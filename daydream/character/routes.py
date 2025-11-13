import logging
import uuid
from flask import render_template, request, redirect, url_for, session, flash
from . import bp
import os
import json
from collections import Counter
from ..utils import (
    login_required,
    save_character_data,
    SESSION_USER_ID,
    SESSION_NEW_CHAR_DETAILS,
    STARTING_LOCATION,
    FS_CONVERSATION,
    FS_CHAPTER_INPUTS,
    FS_QUEST_FLAGS,
    FS_INVENTORY,
    SESSION_EOC_PROMPTED
)

def load_character_template_data(filename):
    """Loads character template data from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'data', filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Could not load character template data from {file_path}: {e}")
        return {}

ARCHETYPE_QUIZ_DATA = load_character_template_data('archetype_quiz.json')
from flask import current_app

@bp.route('/create', methods=['GET','POST'])
@login_required
def character_creation_view():
    user_id = session[SESSION_USER_ID]
    if request.method == 'POST':
        creation_stage = request.form.get('creation_stage')

        if creation_stage == 'submit_quiz':
            answers = {}
            for dilemma in ARCHETYPE_QUIZ_DATA.get('dilemmas', []):
                answer = request.form.get(dilemma['id'])
                if answer:
                    answers[dilemma['id']] = answer

            if len(answers) != len(ARCHETYPE_QUIZ_DATA.get('dilemmas', [])):
                flash("Please answer all the dilemmas.", "warning")
                return redirect(url_for('character.character_creation_view'))

            archetype_counts = Counter(answers.values())
            primary_archetype = archetype_counts.most_common(1)[0][0]

            char_details = {
                'name': request.form.get('name', '').strip(),
                'archetype': primary_archetype
            }
            session[SESSION_NEW_CHAR_DETAILS] = char_details

            archetype_details = ARCHETYPE_QUIZ_DATA.get('archetypes', {}).get(primary_archetype)

            return render_template('character/archetype_reveal.html',
                                   name=char_details['name'],
                                   archetype_name=primary_archetype,
                                   details=archetype_details)

        elif creation_stage == 'restart':
            session.pop(SESSION_NEW_CHAR_DETAILS, None)
            return redirect(url_for('character.character_creation_view'))

        elif creation_stage == 'finalize':
            final_details = session.get(SESSION_NEW_CHAR_DETAILS)
            if not final_details:
                flash("Character details were lost. Please start over.", "error")
                return redirect(url_for('character.character_creation_view'))

            new_char_id = f"{user_id}_custom_{uuid.uuid4().hex[:8]}"
            final_char_data = {
                'id': new_char_id,
                'user_id': user_id,
                'current_location': STARTING_LOCATION,
                'learned_vocab': [],
                'report_summaries': [],
                'turn_count': 0,
                SESSION_EOC_PROMPTED: False,
                FS_CONVERSATION: [],
                FS_CHAPTER_INPUTS: [],
                FS_QUEST_FLAGS: {},
                FS_INVENTORY: []
            }
            final_char_data.update(final_details)

            archetype_name = final_char_data.get('archetype')
            archetype_stats = ARCHETYPE_QUIZ_DATA.get('archetypes', {}).get(archetype_name, {}).get('stats', {})
            final_char_data['stats'] = archetype_stats

            saved_id = save_character_data(user_id, new_char_id, final_char_data)
            if saved_id:
                session.pop(SESSION_NEW_CHAR_DETAILS, None)
                flash(f"Custom character '{final_char_data.get('name', 'Unknown')}' created successfully!", "success")
                return redirect(url_for('profile.profile'))
            else:
                flash("Failed to save the finalized character. Please try again.", "error")
                return redirect(url_for('character.character_creation_view'))
    else:
        return render_template('character/character_creation.html', quiz=ARCHETYPE_QUIZ_DATA)
