import logging
import re
import uuid
from flask import render_template, request, redirect, url_for, session, flash, jsonify
from . import bp
from ..utils import (
    login_required, get_user_characters, load_character_data,
    save_character_data, check_premium_access, get_ai_response,
    SESSION_USER_ID, SESSION_USER_EMAIL, SESSION_CHARACTER_ID,
    SESSION_LAST_AI_OUTPUT, SESSION_EOC_STATE, SESSION_EOC_QUESTIONS,
    SESSION_EOC_SUMMARY, SESSION_EOC_PROMPTED, SESSION_NEW_CHAR_DETAILS,
    SESSION_AI_RECOMMENDATIONS, SESSION_SIDE_QUEST_ACTIVE, SESSION_SIDE_QUEST_DESC,
    SESSION_SIDE_QUEST_TURNS, STARTING_LOCATION, FS_CONVERSATION, FS_CHAPTER_INPUTS,
    BASE_FATE_POINTS
)
from .. import db, premade_character_templates
from ..quests import get_quest, get_quest_step
from ..character.routes import load_character_template_data

@bp.route('/', methods=['GET','POST'])
@login_required
def profile():
    user_id = session[SESSION_USER_ID]
    user_email = session.get(SESSION_USER_EMAIL, '?')
    characters = get_user_characters(user_id)

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'load_char':
            # ... (Full logic from original profile route)
            pass
        elif action == 'create_char':
            # ... (Full logic from original profile route)
            pass
        elif action == 'load_premade':
            premade_id = request.form.get('premade_char_id')
            if not premade_id:
                flash("Please select a pre-made character.", "warning")
                return redirect(url_for('profile.profile'))

            template = next((p for p in premade_character_templates if p['id'] == premade_id), None)
            if not template:
                flash("Invalid pre-made character selected.", "error")
                return redirect(url_for('profile.profile'))

            RACE_DATA = load_character_template_data('default', 'races')
            CLASS_DATA = load_character_template_data('default', 'classes')
            PHILOSOPHY_DATA = load_character_template_data('default', 'philosophies')

            new_char_id = f"{user_id}_premade_{uuid.uuid4().hex[:8]}"
            final_char_data = {
                'id': new_char_id, 'user_id': user_id, 'current_location': STARTING_LOCATION,
                'learned_vocab': set(), 'report_summaries': [], 'turn_count': 0,
                SESSION_EOC_PROMPTED: False, FS_CONVERSATION: [], FS_CHAPTER_INPUTS: [],
                FS_QUEST_FLAGS: {}, FS_INVENTORY: [],
                **template
            }

            try:
                race_abilities = set(RACE_DATA.get(template['race_name'], {}).get('abilities', []))
                class_ability = CLASS_DATA.get(template['class_name'], {}).get('ability')
                phil_ability = PHILOSOPHY_DATA.get(template['philosophy_name'], {}).get('ability')
                all_abilities = race_abilities
                if class_ability: all_abilities.add(class_ability)
                if phil_ability: all_abilities.add(phil_ability)
                final_char_data['abilities'] = sorted(list(all_abilities))
                class_focus = CLASS_DATA.get(template['class_name'], {}).get('focus')
                aspects = [class_focus] if class_focus else []
                if "Artistic Shell" in final_char_data['abilities']: aspects.append("Shell Design: Undefined")
                final_char_data['aspects'] = aspects
                race_mod = RACE_DATA.get(template['race_name'], {}).get('fate_point_mod', 0)
                final_char_data['fate_points'] = BASE_FATE_POINTS + race_mod
                final_char_data['current_quest_id'] = f"Q_CH1_{new_char_id[-4:]}"
                final_char_data['current_quest_title'] = f"Chapter 1: {template['starting_quest']}"[:80]
                final_char_data['current_step_id'] = "STEP_01"
                final_char_data['current_step_description'] = template['starting_quest']
                saved_id = save_character_data(user_id, final_char_data)
                if saved_id:
                    flash(f"Pre-made character '{template['name']}' loaded successfully!", "success")
                else:
                    flash("Failed to save the pre-made character.", "error")
            except KeyError as e:
                flash(f"Internal data error for pre-made character: {e}", "error")
        elif action == 'save_settings':
            # ... (Full logic from original profile route)
            pass
        else:
            flash(f"Unknown profile action requested: {action}", "warning")
        return redirect(url_for('profile.profile'))

    # --- GET Request Handling ---
    profile_data = {'email': user_email, 'player_level': 1, 'total_player_xp': 0, 'has_premium': False, 'vocab_settings': {'use_default_awl': True, 'awl_color_bg': '#FFE6EB', 'ai_color_bg': '#E1F0FF'}}
    organization_name = None
    if db:
        try:
            profile_doc_ref = db.collection('player_profiles').document(user_id)
            p_doc = profile_doc_ref.get()
            if p_doc.exists:
                fs_data = p_doc.to_dict()
                profile_data.update(fs_data)

                org_id = fs_data.get('organization_id')
                if org_id:
                    org_doc = db.collection('organizations').document(org_id).get()
                    if org_doc.exists:
                        organization_name = org_doc.to_dict().get('name')

        except Exception as e:
            logging.error(f"Failed to fetch player profile for user {user_id}: {e}", exc_info=True)
            flash("An error occurred loading your profile data.", "error")

    return render_template('profile/profile.html',
                           profile=profile_data,
                           characters=characters,
                           premade_characters=premade_character_templates,
                           has_premium=profile_data.get('has_premium', False),
                           organization_name=organization_name)

@bp.route('/generate_vocab', methods=['POST'])
@login_required
def generate_vocab_list():
    # ... (Full logic from original generate_vocab_list)
    return jsonify({"success": True, "message": "Placeholder response."})

@bp.route('/toggle_vocab/<list_id>', methods=['POST'])
@login_required
def toggle_vocab_list(list_id):
    # ... (Full logic from original toggle_vocab_list)
    return jsonify({"success": True, "new_status": False})

@bp.route('/delete_vocab/<list_id>', methods=['POST'])
@login_required
def delete_vocab_list(list_id):
    # ... (Full logic from original delete_vocab_list)
    return jsonify({"success": True, "message": "List deleted."})