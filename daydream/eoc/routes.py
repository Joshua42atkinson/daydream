import logging
from flask import render_template, request, redirect, url_for, session, flash
from . import bp
from ..utils import (
    login_required, load_character_data, save_character_data, get_ai_response,
    SESSION_USER_ID, SESSION_CHARACTER_ID, SESSION_EOC_STATE,
    FS_CHAPTER_INPUTS, HERO_JOURNEY_STAGES, SESSION_EOC_QUESTIONS,
    SESSION_EOC_SUMMARY
)
from flask import current_app

@bp.route('/', methods=['GET', 'POST'])
@login_required
def end_of_chapter():
    user_id = session[SESSION_USER_ID]
    char_id = session.get(SESSION_CHARACTER_ID)
    if not char_id:
        flash("No character loaded.", "error")
        return redirect(url_for('profile.profile'))

    p_data = load_character_data(user_id, char_id)
    if not p_data:
        return redirect(url_for('profile.profile'))

    eoc_state = session.get(SESSION_EOC_STATE, 'START')

    if request.method == 'POST':
        if eoc_state == 'AWAIT_COMP_ANSWERS':
            questions = session.get(SESSION_EOC_QUESTIONS, [])
            if not questions:
                flash("Error: Comprehension questions missing from session.", "error")
                session[SESSION_EOC_STATE] = 'START'
                return redirect(url_for('eoc.end_of_chapter'))
            answers = [request.form.get(f'comp_answer_{i+1}', '').strip() for i in range(len(questions))]
            if not all(answers):
                flash("Please answer all comprehension questions.", "warning")
                return render_template('eoc/comprehension_check.html', questions=questions)
            eval_ctx = {'questions': questions, 'answers': answers}
            comp_res = get_ai_response("EVALUATE_CHAPTER_COMPREHENSION", eval_ctx)
            comp_score = 0.0
            if isinstance(comp_res, dict) and 'overall_comprehension_score' in comp_res:
                try:
                    comp_score = float(comp_res['overall_comprehension_score'])
                    comp_score = max(0.0, min(10.0, comp_score))
                except (ValueError, TypeError):
                    logging.warning(f"Invalid comprehension score format from AI: {comp_res['overall_comprehension_score']}")
            else:
                flash("The AI storyteller had trouble evaluating your comprehension.", "warning")
            chapter_text = "\n---\n".join(p_data.get(FS_CHAPTER_INPUTS,[])) or "(No player inputs recorded for this chapter)"
            anal_ctx = {'chapter_player_text': chapter_text}
            anal_res = get_ai_response("ANALYZE_PLAYER_WRITING", anal_ctx)
            if not isinstance(anal_res, dict) or 'error' in anal_res:
                anal_res = {}
            xp_gained = (5 + {'S':1, 'M':3, 'L':5}.get(anal_res.get('avg_length_category'), 0) + len(anal_res.get('awl_words_used', [])) * 2 + int(anal_res.get('relevance_coherence_score', 0)) + {'L':1, 'M':3, 'H':5}.get(anal_res.get('style_rating'), 0) + {'L':1, 'M':3, 'H':5}.get(anal_res.get('thinking_rating'), 0) + {'L':1, 'M':3, 'H':5}.get(anal_res.get('descriptive_language_rating'), 0) + max(0, int(comp_score) - 5))
            xp_gained = max(0, xp_gained)
            flash(f"Chapter Complete! You earned {xp_gained} Player XP!", "success")
            db = current_app.config.get('DB')
            if db and not current_app.config.get('BYPASS_EXTERNAL_SERVICES'):
                try:
                    profile_ref = db.collection('player_profiles').document(user_id)
                    profile_ref.update({'total_player_xp': db.firestore.Increment(xp_gained)})
                    profile_doc = profile_ref.get(['total_player_xp', 'player_level'])
                    if profile_doc.exists:
                        profile_data = profile_doc.to_dict()
                        if profile_data.get('total_player_xp', 0) >= (profile_data.get('player_level', 1) * 100):
                            new_level = profile_data.get('player_level', 1) + 1
                            profile_ref.update({'player_level': new_level})
                            flash(f"Congratulations! You've reached Player Level {new_level}!", "success")
                except Exception as e:
                    logging.error(f"Failed to update player XP/Level in Firestore for user {user_id}: {e}", exc_info=True)
            summary_text = f"**Chapter Complete!**\n\n* **Comprehension Score:** {comp_score:.1f} / 10\n* **Player XP Gained:** +{xp_gained}\n\n* **Writing Analysis:**\n"
            summary_text += f"    * AWL Words Used ({len(anal_res.get('awl_words_used', []))}): {', '.join(anal_res.get('awl_words_used', [])) if anal_res.get('awl_words_used') else 'None'}\n"
            summary_text += f"    * Relevance & Coherence: {anal_res.get('relevance_coherence_score','?')} / 5\n"
            summary_text += f"    * Style Complexity: {anal_res.get('style_rating','?')}\n"
            summary_text += f"    * Critical Thinking: {anal_res.get('thinking_rating','?')}\n"
            summary_text += f"    * Average Length: {anal_res.get('avg_length_category','?')}\n"
            summary_text += f"    * Descriptive Language: {anal_res.get('descriptive_language_rating','?')}\n"
            summaries = p_data.get('report_summaries', [])
            current_chapter_num = len(summaries) + 1
            summaries.append({"chapter": current_chapter_num, "summary": summary_text, "comprehension_score": comp_score, "player_xp_gained": xp_gained, "analysis_raw": anal_res})
            p_data['report_summaries'] = summaries
            p_data[FS_CHAPTER_INPUTS] = []
            session[SESSION_EOC_SUMMARY] = summary_text
            session[SESSION_EOC_STATE] = 'AWAIT_REPORT_ACK'
            session.pop(SESSION_CHAPTER_INPUTS, None)
            session.pop(SESSION_EOC_QUESTIONS, None)
            save_character_data(user_id, p_data)
            return redirect(url_for('eoc.end_of_chapter'))
        elif eoc_state == 'AWAIT_REPORT_ACK':
            summaries = p_data.get('report_summaries', [])
            current_chapter_num = len(summaries)

            # Check if the full 12-stage journey is complete
            if current_chapter_num > 0 and current_chapter_num % 12 == 0:
                session[SESSION_EOC_STATE] = 'AWAIT_FINAL_REVIEW_ACK'
                # Trigger the final review process
                final_review_ctx = {
                    "character_data": p_data,
                    "all_chapter_summaries": summaries
                }
                final_review_res = get_ai_response("GENERATE_FINAL_REVIEW", final_review_ctx)

                if isinstance(final_review_res, dict) and 'final_narrative' in final_review_res:
                    session[SESSION_EOC_SUMMARY] = final_review_res['final_narrative']
                    flash("You have completed a full Hero's Journey! A final review is available.", "success")
                else:
                    session[SESSION_EOC_SUMMARY] = "The AI storyteller is gathering its thoughts for your final review. Please check back shortly."
                    flash("You've completed a full cycle! The final review is being prepared.", "info")

                # Optionally, reset summaries for the next journey
                # p_data['report_summaries'] = []

                save_character_data(user_id, p_data)
                return redirect(url_for('eoc.end_of_chapter'))

            # Standard next chapter generation
            stage_index = current_chapter_num % len(HERO_JOURNEY_STAGES)
            next_stage_data = HERO_JOURNEY_STAGES[stage_index]

            q_gen_ctx = {
                "character_data": p_data,
                "chapter_summaries": summaries,
                "next_hero_journey_stage": next_stage_data['title'],
                "next_stage_description": next_stage_data['description'],
                "next_stage_keywords": next_stage_data['keywords']
            }
            q_gen_res = get_ai_response("GENERATE_NEXT_QUEST", q_gen_ctx)

            if isinstance(q_gen_res, dict) and 'error' not in q_gen_res:
                p_data['current_quest_id'] = q_gen_res.get('quest_id')
                p_data['current_quest_title'] = q_gen_res.get('title')
                p_data['current_step_id'] = q_gen_res.get('starting_step_id')
                p_data['current_step_description'] = q_gen_res.get('starting_step_description')
                flash(f"New objective received: {p_data['current_quest_title']}", "info")
            else:
                flash(f"The AI storyteller had trouble determining your next quest. Time to explore!", "warning")

            p_data[FS_CHAPTER_INPUTS] = []
            p_data['turn_count'] = 0
            for key in [SESSION_EOC_STATE, SESSION_EOC_QUESTIONS, SESSION_EOC_SUMMARY]:
                session.pop(key, None)
            save_character_data(user_id, p_data)
            return redirect(url_for('game.game_view'))
    else:
        if eoc_state == 'START':
            questions = [
                "What was your main objective or focus in this chapter?",
                "Describe a key interaction or challenge you faced.",
                "How did your character approach the situations encountered?"
            ]
            session[SESSION_EOC_QUESTIONS] = questions
            session[SESSION_EOC_STATE] = 'AWAIT_COMP_ANSWERS'
            return render_template('eoc/comprehension_check.html', questions=questions)
        elif eoc_state == 'AWAIT_FINAL_REVIEW_ACK':
            final_review_html = session.get(SESSION_EOC_SUMMARY, "<p>Your final review is not available at this moment.</p>")
            return render_template('eoc/final_review.html', final_review_html=final_review_html)
        elif eoc_state == 'AWAIT_REPORT_ACK':
            summary = session.get(SESSION_EOC_SUMMARY, "Report summary is currently unavailable.")
            return render_template('eoc/report_summary.html', report_summary=summary)
        return redirect(url_for('game.game_view'))

@bp.route('/new_journey', methods=['POST'])
@login_required
def start_new_journey():
    """Resets the necessary character data to begin a new 12-stage journey."""
    user_id = session[SESSION_USER_ID]
    char_id = session.get(SESSION_CHARACTER_ID)
    if not char_id:
        flash("No character loaded.", "error")
        return redirect(url_for('profile.profile'))

    p_data = load_character_data(user_id, char_id)
    if not p_data:
        return redirect(url_for('profile.profile'))

    # Reset the journey-specific data
    p_data['report_summaries'] = []

    # Clear all session data related to the end-of-chapter process
    for key in [SESSION_EOC_STATE, SESSION_EOC_QUESTIONS, SESSION_EOC_SUMMARY]:
        session.pop(key, None)

    save_character_data(user_id, p_data)

    flash("A new journey begins! Your previous accomplishments have been archived.", "success")
    return redirect(url_for('game.game_view'))