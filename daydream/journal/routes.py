from flask import render_template, session, flash, redirect, url_for
from . import bp
from ..utils import (
    login_required, load_character_data, get_active_vocab_data, check_premium_access,
    SESSION_USER_ID, SESSION_CHARACTER_ID, FS_CONVERSATION, FS_CHAPTER_INPUTS,
    FS_QUEST_FLAGS, FS_INVENTORY
)
from ..quests import get_quest
from flask import current_app

@bp.route('/vocab', methods=['GET'])
@login_required
def journal_vocab_report():
    user_id = session[SESSION_USER_ID]
    char_id = session.get(SESSION_CHARACTER_ID)
    if not char_id:
        flash("No character loaded.", "warning")
        return redirect(url_for('profile.profile'))

    p_data = load_character_data(user_id, char_id)
    if not p_data:
        return redirect(url_for('profile.profile'))

    active_vocab_data = get_active_vocab_data(user_id)
    combined_vocab = active_vocab_data.get("vocab", {})
    awl_words = []
    ai_words_by_list = {}
    for word, data in sorted(combined_vocab.items()):
        source = data.get("source", "Unknown")
        entry = {"word": word, "definition": data.get("definition", "?")}
        if source == "AWL":
            awl_words.append(entry)
        else:
            if source not in ai_words_by_list:
                ai_words_by_list[source] = []
            ai_words_by_list[source].append(entry)

    ai_lists_metadata = []
    db = current_app.config.get('DB')
    if db and not current_app.config.get('BYPASS_EXTERNAL_SERVICES'):
        try:
            profile_ref = db.collection('player_profiles').document(user_id)
            ai_lists_query = profile_ref.collection('custom_vocab_lists').where('is_ai_generated', '==', True).stream()
            for list_doc in ai_lists_query:
                list_data = list_doc.to_dict()
                ai_lists_metadata.append({
                    "id": list_doc.id,
                    "name": list_data.get("name", "Unnamed AI List"),
                    "is_active": list_data.get("is_active", False),
                    "word_count": len(list_data.get("words", [])),
                    "created_at": list_data.get("created_at")
                })
            ai_lists_metadata.sort(key=lambda x: x.get('created_at', 0), reverse=True)
        except Exception as e:
            flash("Error loading vocabulary list details.", "warning")

    report_summaries = p_data.get('report_summaries', [])
    report_summaries.sort(key=lambda x: x.get('chapter', 0))

    return render_template('journal/journal_vocab_report.html',
                           awl_words=awl_words,
                           ai_word_lists=ai_words_by_list,
                           ai_lists_metadata=ai_lists_metadata,
                           report_summaries=report_summaries,
                           premium_active=check_premium_access(user_id))

@bp.route('/character', methods=['GET'])
@login_required
def journal_char_quest():
    user_id = session[SESSION_USER_ID]
    char_id = session.get(SESSION_CHARACTER_ID)
    if not char_id:
        flash("No character loaded.", "warning")
        return redirect(url_for('profile.profile'))

    p_data = load_character_data(user_id, char_id)
    if not p_data:
        return redirect(url_for('profile.profile'))

    sheet_data = p_data.copy()
    fields_to_pop = [FS_CONVERSATION, FS_CHAPTER_INPUTS, FS_QUEST_FLAGS]
    for field in fields_to_pop:
        sheet_data.pop(field, None)
    if isinstance(sheet_data.get('learned_vocab'), set):
         sheet_data['learned_vocab'] = sorted(list(sheet_data['learned_vocab']))

    quest_log = {
        "title": p_data.get('current_quest_title', 'No active quest'),
        "step_desc": p_data.get('current_step_description', '')
    }
    if quest_log['title'] == 'No active quest' and p_data.get('current_quest_id'):
        qd = get_quest(p_data['current_quest_id'])
        quest_log['title'] = qd.get('title', 'Unknown Quest') if qd else 'Unknown Quest'

    inventory_list = p_data.get(FS_INVENTORY, [])

    return render_template('journal/journal_char_quest.html',
                           character_sheet=sheet_data,
                           quest_log=quest_log,
                           inventory=inventory_list)