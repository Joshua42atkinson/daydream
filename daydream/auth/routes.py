import logging
from flask import render_template, request, redirect, url_for, session, flash, current_app
from . import bp
from ..utils import login_required, SESSION_USER_ID, SESSION_USER_EMAIL, FS_PLAYER_HAS_SEEN_INTRO

@bp.route('/login', methods=['GET','POST'])
def login():
    """Handles user login."""
    if SESSION_USER_ID in session:
        return redirect(url_for('profile.profile'))

    # If bypassing external services, create a dummy session for development.
    if current_app.config.get('BYPASS_EXTERNAL_SERVICES'):
        if request.method == 'POST':
            dummy_email = request.form.get('email', 'dev@daydream.ai')
            dummy_uid = "dummy_user_id_12345"
            session[SESSION_USER_ID] = dummy_uid
            session[SESSION_USER_EMAIL] = dummy_email
            session.permanent = True
            flash(f"Logged in as {dummy_email} (Bypass Mode)", "success")
            logging.info(f"Bypass login successful for {dummy_email}")
            next_url = request.args.get('next')
            return redirect(next_url or url_for('profile.profile'))
        return render_template('auth/login.html')

    # --- Standard Firebase Login ---
    if request.method == 'POST':
        auth_client = current_app.config.get('AUTH_CLIENT')
        if not auth_client:
            flash("Authentication service is not available. Please check server configuration.", "error")
            return render_template('auth/login.html')

        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template('auth/login.html')

        try:
            user = auth_client.get_user_by_email(email)
            # SECURITY NOTE: This is a placeholder and does NOT actually verify the password.
            # In a real application, you would use a method like `sign_in_with_email_and_password`.
            logging.info(f"User {email} found, proceeding with login for UID: {user.uid}")
            logging.warning(f"SECURITY-NOTE: Password for {email} is NOT verified by this backend logic.")

            session[SESSION_USER_ID] = user.uid
            session[SESSION_USER_EMAIL] = user.email
            session.permanent = True
            flash(f"Welcome back, {user.email}!", "success")

            next_url = request.args.get('next')
            return redirect(next_url or url_for('profile.profile'))
        except Exception as e:
            # Using a generic error message for security.
            flash("Login failed: The email address was not found or an error occurred.", "error")
            logging.error(f"Login attempt failed for {email}: {e}")

    return render_template('auth/login.html')


@bp.route('/signup', methods=['GET','POST'])
def signup():
    """Handles user signup."""
    if SESSION_USER_ID in session:
        return redirect(url_for('profile.profile'))

    if current_app.config.get('BYPASS_EXTERNAL_SERVICES'):
        flash("Signup is disabled in Bypass Mode.", "info")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        auth_client = current_app.config.get('AUTH_CLIENT')
        db = current_app.config.get('DB')
        if not auth_client or not db:
            flash("Authentication service is not available. Please check server configuration.", "error")
            return render_template('auth/signup.html')

        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password or len(password) < 6:
            flash("Please provide a valid email and a password (at least 6 characters).", "error")
            return render_template('auth/signup.html')

        try:
            # Create user in Firebase Authentication
            user = auth_client.create_user(email=email, password=password)
            logging.info(f"New Firebase Auth user created: {user.uid} ({email})")

            # Create corresponding user profile in Firestore
            profile_data = {
                'email': email,
                'player_level': 1,
                'total_player_xp': 0,
                'created_at': db.SERVER_TIMESTAMP,
                'has_premium': False,
                'vocab_settings': {
                    'use_default_awl': True
                },
                FS_PLAYER_HAS_SEEN_INTRO: False,
                'role': 'student' # Default role for new signups
            }
            db.collection('player_profiles').document(user.uid).set(profile_data)
            logging.info(f"Firestore player profile created for {user.uid}")

            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for('auth.login'))
        except Exception as e:
            # It's good practice to catch specific exceptions, e.g., email already exists.
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