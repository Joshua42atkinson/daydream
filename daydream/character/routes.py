import logging
import uuid
from flask import render_template, request, redirect, url_for, session, flash
from . import bp
from ..utils import (
    login_required, get_ai_response, save_character_data,
    RACE_DATA, CLASS_DATA, PHILOSOPHY_DATA,
    SESSION_USER_ID, SESSION_NEW_CHAR_DETAILS, SESSION_AI_RECOMMENDATIONS,
    STARTING_LOCATION, BASE_FATE_POINTS, FS_CONVERSATION, FS_CHAPTER_INPUTS,
    FS_QUEST_FLAGS, FS_INVENTORY, SESSION_EOC_PROMPTED
)
from .. import db
from ..quests import get_quest, get_quest_step

@bp.route('/create', methods=['GET','POST'])
@login_required
def character_creation_view():
    user_id = session[SESSION_USER_ID]
    if request.method == 'POST':
        creation_stage = request.form.get('creation_stage')
        if creation_stage == 'submit_details':
            char_details = {
                k: request.form.get(k, '').strip()
                for k in ['name', 'race_name', 'class_name', 'philosophy_name', 'boon', 'backstory', 'starting_quest']
            }
            missing = [field for field in char_details if not char_details.get(field)]
            if missing:
                flash(f"Please fill out all character detail fields ({', '.join(missing)} missing).", "warning")
                return render_template('character/character_creation.html', race_options=list(RACE_DATA.keys()), class_options=list(CLASS_DATA.keys()), philosophy_options=list(PHILOSOPHY_DATA.keys()), char_details=char_details, ai_recommendations=None, reviewing=False)
            session[SESSION_NEW_CHAR_DETAILS] = char_details
            review_context = {"character_sheet_data": char_details}
            ai_response = get_ai_response("REVIEW_CHARACTER_SHEET", review_context)
            recommendations = []
            if isinstance(ai_response, dict) and 'error' not in ai_response:
                recommendations = ai_response.get('recommendations', [])
                flash("AI has reviewed your character concept. See suggestions below.", "info")
            else:
                error_reason = ai_response.get('reason', 'Unknown error') if isinstance(ai_response, dict) else 'AI communication failure'
                flash(f"AI couldn't review your concept ({error_reason}). You can finalize, edit, or start over.", "error")
                recommendations = None
            session[SESSION_AI_RECOMMENDATIONS] = recommendations
            return render_template('character/character_creation.html', race_options=list(RACE_DATA.keys()), class_options=list(CLASS_DATA.keys()), philosophy_options=list(PHILOSOPHY_DATA.keys()), char_details=char_details, ai_recommendations=recommendations, reviewing=True)
        elif creation_stage == 'restart':
            session.pop(SESSION_NEW_CHAR_DETAILS, None)
            session.pop(SESSION_AI_RECOMMENDATIONS, None)
            return redirect(url_for('character.character_creation_view'))
        elif creation_stage == 'edit':
            session.pop(SESSION_AI_RECOMMENDATIONS, None)
            return redirect(url_for('character.character_creation_view'))
        elif creation_stage == 'finalize':
            final_details = session.get(SESSION_NEW_CHAR_DETAILS)
            if not final_details:
                flash("Character details were lost. Please start over.", "error")
                session.pop(SESSION_AI_RECOMMENDATIONS, None)
                return redirect(url_for('character.character_creation_view'))
            new_char_id = f"{user_id}_custom_{uuid.uuid4().hex[:8]}"
            final_char_data = {
                'id': new_char_id, 'user_id': user_id, 'current_location': STARTING_LOCATION,
                'learned_vocab': set(), 'report_summaries': [], 'turn_count': 0,
                SESSION_EOC_PROMPTED: False, FS_CONVERSATION: [], FS_CHAPTER_INPUTS: [],
                FS_QUEST_FLAGS: {}, FS_INVENTORY: []
            }
            final_char_data.update(final_details)
            race_name = final_char_data.get('race_name')
            class_name = final_char_data.get('class_name')
            philosophy_name = final_char_data.get('philosophy_name')
            start_goal = final_char_data.get('starting_quest', 'Find purpose')
            if not all([race_name, class_name, philosophy_name]):
                flash(f"Missing required character detail (Race/Class/Philosophy). Please start over.", "error")
                session.pop(SESSION_NEW_CHAR_DETAILS, None)
                session.pop(SESSION_AI_RECOMMENDATIONS, None)
                return redirect(url_for('character.character_creation_view'))
            try:
                race_abilities = set(RACE_DATA.get(race_name, {}).get('abilities', []))
                class_ability = CLASS_DATA.get(class_name, {}).get('ability')
                phil_ability = PHILOSOPHY_DATA.get(philosophy_name, {}).get('ability')
                all_abilities = race_abilities
                if class_ability: all_abilities.add(class_ability)
                if phil_ability: all_abilities.add(phil_ability)
                final_char_data['abilities'] = sorted(list(all_abilities))
                class_focus = CLASS_DATA.get(class_name, {}).get('focus')
                aspects = [class_focus] if class_focus else []
                if "Artistic Shell" in final_char_data['abilities']: aspects.append("Shell Design: Undefined")
                final_char_data['aspects'] = aspects
                race_mod = RACE_DATA.get(race_name, {}).get('fate_point_mod', 0)
                final_char_data['fate_points'] = BASE_FATE_POINTS + race_mod
                final_char_data['current_quest_id'] = f"Q_CH1_{new_char_id[-4:]}"
                final_char_data['current_quest_title'] = f"Chapter 1: {start_goal}"[:80]
                final_char_data['current_step_id'] = "STEP_01"
                final_char_data['current_step_description'] = start_goal
            except KeyError as e:
                flash(f"Internal data error finding details for {e}. Please check selections.", "error")
                session.pop(SESSION_NEW_CHAR_DETAILS, None)
                session.pop(SESSION_AI_RECOMMENDATIONS, None)
                return redirect(url_for('character.character_creation_view'))
            saved_id = save_character_data(user_id, final_char_data)
            if saved_id:
                session.pop(SESSION_NEW_CHAR_DETAILS, None)
                session.pop(SESSION_AI_RECOMMENDATIONS, None)
                flash(f"Custom character '{final_char_data.get('name', 'Unknown')}' created successfully!", "success")
                return redirect(url_for('profile.profile'))
            else:
                flash("Failed to save the finalized character. Please try again.", "error")
                return redirect(url_for('character.character_creation_view'))
    else:
        char_details_from_session = session.get(SESSION_NEW_CHAR_DETAILS)
        recommendations_from_session = session.get(SESSION_AI_RECOMMENDATIONS)
        is_reviewing_stage = bool(char_details_from_session and recommendations_from_session is not None)
        return render_template('character/character_creation.html', race_options=list(RACE_DATA.keys()), class_options=list(CLASS_DATA.keys()), philosophy_options=list(PHILOSOPHY_DATA.keys()), char_details=char_details_from_session or {}, ai_recommendations=recommendations_from_session, reviewing=is_reviewing_stage)

@bp.route('/delete/<char_id>', methods=['POST'])
@login_required
def delete_character(char_id):
    user_id = session[SESSION_USER_ID]
    if not char_id:
        flash("Invalid request: Missing character ID.", "error")
        return redirect(url_for('profile.profile'))
    try:
        char_ref = db.collection('characters').document(char_id)
        char_doc = char_ref.get(['user_id', 'name'])
        if not char_doc.exists:
            flash("Character not found.", "warning")
            return redirect(url_for('profile.profile'))
        if char_doc.to_dict().get('user_id') != user_id:
            flash("Permission denied to delete this character.", "error")
            return redirect(url_for('profile.profile'))
        char_name = char_doc.to_dict().get('name', 'Unknown Character')
        char_ref.delete()
        flash(f"Character '{char_name}' deleted successfully.", "success")
        if session.get('character_id') == char_id:
            session.clear()
    except Exception as e:
        logging.error(f"Error deleting character {char_id}: {e}")
        flash("An error occurred while trying to delete the character.", "error")
    return redirect(url_for('profile.profile'))