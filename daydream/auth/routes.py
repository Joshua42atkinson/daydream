import logging
from flask import render_template, request, redirect, url_for, session, flash
from . import bp
from .. import auth_client, db
from ..utils import login_required, SESSION_USER_ID, SESSION_USER_EMAIL, FS_PLAYER_HAS_SEEN_INTRO

@bp.route('/login', methods=['GET','POST'])
def login():
    if SESSION_USER_ID in session:
        return redirect(url_for('profile.profile'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template('auth/login.html')
        try:
            user = auth_client.get_user_by_email(email)
            logging.info(f"User {email} found, proceeding with login for UID: {user.uid}")
            logging.warning(f"SECURITY-NOTE: Password for {email} is NOT verified by this backend logic.")
            session[SESSION_USER_ID] = user.uid
            session[SESSION_USER_EMAIL] = user.email
            session.permanent = True
            flash(f"Welcome back, {user.email}!", "success")
            next_url = request.args.get('next')
            return redirect(next_url or url_for('profile.profile'))
        except Exception as e:
            flash("Login failed: The email address was not found or an error occurred.", "error")
            logging.error(f"Login attempt failed for {email}: {e}")
    return render_template('auth/login.html')

@bp.route('/signup', methods=['GET','POST'])
def signup():
    if SESSION_USER_ID in session:
        return redirect(url_for('profile.profile'))
    if request.method=='POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password or len(password) < 6:
            flash("Please provide a valid email and a password (at least 6 characters).", "error")
            return render_template('auth/signup.html')
        try:
            user = auth_client.create_user(email=email, password=password)
            logging.info(f"New Firebase Auth user created: {user.uid} ({email})")
            profile_data = {
                'email': email, 'player_level': 1, 'total_player_xp': 0,
                'created_at': db.SERVER_TIMESTAMP, 'has_premium': False,
                'vocab_settings': {'use_default_awl': True},
                FS_PLAYER_HAS_SEEN_INTRO: False
            }
            db.collection('player_profiles').document(user.uid).set(profile_data)
            logging.info(f"Firestore player profile created for {user.uid}")
            flash(f"Account created successfully! Please log in.", "success")
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash("An unexpected error occurred during signup.", "error")
            logging.error(f"Signup Error for {email}: {e}", exc_info=True)
    return render_template('auth/signup.html')

@bp.route('/logout')
@login_required
def logout():
    user_email = session.get(SESSION_USER_EMAIL,'Unknown User')
    logging.info(f"Logging out user {user_email} ({session.get(SESSION_USER_ID)})")
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('auth.login'))