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
from .. import premade_character_templates
from ..quests import get_quest, get_quest_step
from flask import current_app

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
            # ... (Full logic from original profile route)
            pass
        elif action == 'save_settings':
            # ... (Full logic from original profile route)
            pass
        else:
            flash(f"Unknown profile action requested: {action}", "warning")
        return redirect(url_for('profile.profile'))

    # --- GET Request Handling ---
    profile_data = {'email': user_email, 'player_level': 1, 'total_player_xp': 0, 'has_premium': False, 'vocab_settings': {'use_default_awl': True, 'awl_color_bg': '#FFE6EB', 'ai_color_bg': '#E1F0FF'}}
    db = current_app.config.get('DB')
    if db and not current_app.config.get('BYPASS_EXTERNAL_SERVICES'):
        try:
            profile_doc_ref = db.collection('player_profiles').document(user_id)
            p_doc = profile_doc_ref.get(['player_level', 'total_player_xp', 'has_premium', 'email', 'vocab_settings'])
            if p_doc.exists:
                fs_data = p_doc.to_dict()
                profile_data.update(fs_data)
        except Exception as e:
            logging.error(f"Failed to fetch player profile for user {user_id}: {e}", exc_info=True)
            flash("An error occurred loading your profile data.", "error")

    return render_template('profile/profile.html',
                           profile=profile_data,
                           characters=characters,
                           premade_characters=premade_character_templates,
                           has_premium=profile_data.get('has_premium', False))

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

@bp.route('/grant-mentor-role')
@login_required
def grant_mentor_role():
    """A temporary route to grant mentor role to the current user."""
    user_id = session.get(SESSION_USER_ID)
    db = current_app.config.get('DB')

    if not user_id:
        flash("User not found in session.", "error")
        return redirect(url_for('profile.profile'))

    if current_app.config.get('BYPASS_EXTERNAL_SERVICES') or not db:
        flash("Cannot grant roles in Bypass Mode.", "warning")
        return redirect(url_for('profile.profile'))

    try:
        user_profile_ref = db.collection('player_profiles').document(user_id)
        user_profile_ref.update({'role': 'mentor'})
        flash('You have been granted mentor privileges!', 'success')
        logging.info(f"User {user_id} granted mentor role.")
    except Exception as e:
        logging.error(f"Error granting mentor role to user {user_id}: {e}")
        flash('An error occurred while granting mentor privileges.', 'error')

    return redirect(url_for('profile.profile'))
