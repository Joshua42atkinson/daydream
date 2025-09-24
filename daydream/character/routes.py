import logging
import uuid
from flask import render_template, request, redirect, url_for, session, flash
from . import bp
import os
import json
import logging
from ..utils import (
    login_required, get_ai_response, save_character_data,
    SESSION_USER_ID, SESSION_NEW_CHAR_DETAILS, SESSION_AI_RECOMMENDATIONS,
    STARTING_LOCATION, BASE_FATE_POINTS, FS_CONVERSATION, FS_CHAPTER_INPUTS,
    FS_QUEST_FLAGS, FS_INVENTORY, SESSION_EOC_PROMPTED
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

RACE_DATA = load_character_template_data('races.json')
CLASS_DATA = load_character_template_data('classes.json')
PHILOSOPHY_DATA = load_character_template_data('philosophies.json')
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

from werkzeug.utils import secure_filename

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

@bp.route('/templates')
@login_required
def template_manager():
    """Renders the character template management page."""
    os.makedirs(DATA_PATH, exist_ok=True)

    try:
        all_files = os.listdir(DATA_PATH)
        race_files = [f for f in all_files if f.startswith('races') and f.endswith('.json')]
        class_files = [f for f in all_files if f.startswith('classes') and f.endswith('.json')]
        philosophy_files = [f for f in all_files if f.startswith('philosophies') and f.endswith('.json')]
    except OSError as e:
        logging.error(f"Error accessing character template directory {DATA_PATH}: {e}")
        flash("Could not access character template directory.", "error")
        race_files, class_files, philosophy_files = [], [], []

    return render_template('character_template_manager.html',
                           race_files=race_files,
                           class_files=class_files,
                           philosophy_files=philosophy_files)

@bp.route('/templates/upload/<string:template_type>', methods=['POST'])
@login_required
def upload_template(template_type):
    """Handles uploading of new character template JSON files."""
    if template_type not in ['races', 'classes', 'philosophies']:
        flash("Invalid template type specified.", "error")
        return redirect(url_for('character.template_manager'))

    if 'template_file' not in request.files:
        flash('No file part in the request.', 'error')
        return redirect(url_for('character.template_manager'))

    file = request.files['template_file']
    if file.filename == '':
        flash('No file selected for uploading.', 'warning')
        return redirect(url_for('character.template_manager'))

    if file and file.filename.endswith('.json'):
        filename = secure_filename(file.filename)
        # To prevent overwriting the default, we might want to rename if it matches.
        # For now, we'll allow it.
        save_path = os.path.join(DATA_PATH, filename)

        try:
            # Validate JSON content
            json_data = json.load(file)
            if not isinstance(json_data, dict):
                raise ValueError("JSON content must be a dictionary.")

            # Save the validated JSON data
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=4)

            flash(f'Template file "{filename}" for {template_type} uploaded successfully.', 'success')

        except json.JSONDecodeError:
            flash('Invalid JSON file. Please check the file content and structure.', 'error')
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            logging.error(f"Error saving uploaded template file {filename}: {e}")
            flash('An unexpected error occurred while saving the file.', 'error')
    else:
        flash('Invalid file type. Please upload a .json file.', 'error')

    return redirect(url_for('character.template_manager'))

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