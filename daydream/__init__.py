import os
import logging
import json
import re
from functools import wraps
import uuid

from flask import Flask, session, redirect, url_for, g, request
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import auth as firebase_auth
import google.generativeai as genai

from .state_manager import StateManager

# Define globals that will be initialized in create_app
# Refactor: We will move service objects (db, model, etc.) into the app config
# to avoid globals and potential circular imports.
state_manager = None

# --- Application Data Loading ---
# These are loaded once when the module is imported.
# In a larger app, these might be managed by a dedicated asset loading system.

# --- Application Data Loading ---
# These are loaded once when the module is imported.
# In a larger app, these might be managed by a dedicated asset loading system.

# AWL_WORDS is now loaded directly in the vocabulary module.
# We can import it after it has been initialized.
try:
    from .vocabulary import AWL_WORDS
except (ImportError, FileNotFoundError, json.JSONDecodeError) as e:
    logging.warning(f"Could not load vocabulary data: {e}")
    AWL_WORDS = {}

QUEST_DATA = {}
try:
    from .quests import QUEST_DATA as imported_quest_data
    QUEST_DATA = imported_quest_data
except ImportError as e:
    logging.warning(f"Could not load quest data: {e}")

thetopia_lore = {}
world_map = {}
lore_vocabulary = {}
try:
    from .lore import thetopia_lore as imported_thetopia_lore
    thetopia_lore = imported_thetopia_lore
    world_map = thetopia_lore.get('locations', {})
    with open('lore_vocabulary.json', 'r', encoding='utf-8') as f:
        lore_vocabulary = json.load(f)
except (ImportError, FileNotFoundError, json.JSONDecodeError) as e:
    logging.warning(f"Could not load lore data: {e}")

premade_character_templates = []
try:
    with open('premade_characters.json', 'r', encoding='utf-8') as f:
        raw_templates = json.load(f)
    premade_character_templates = [{k: v for k, v in t.items() if k != 'base_attributes'} for t in raw_templates]
except (FileNotFoundError, json.JSONDecodeError) as e:
    logging.warning(f"Could not load pre-made characters: {e}")


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)

    # --- Configuration ---
    # Load default config and override with instance config if it exists
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('FLASK_SECRET_KEY', 'dev'),
        FIREBASE_APP_NAME='daydream-firebase-app',
        MAX_INPUT_LENGTH=500,
        MAX_CONVO_LINES=100,
        STARTING_LOCATION="Thetopia - Town Square",
        BASE_FATE_POINTS=1,
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # --- Initialize Logging ---
    if not app.debug and not app.testing:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    logging.info("Flask application created.")

    # Use 'global' to modify the global variables defined outside the function
    global state_manager

    # --- Initialize State Manager ---
    # The StateManager is a singleton, so this will either create a new
    # instance or return the existing one.
    state_manager = StateManager()

    @app.before_request
    def manage_app_state():
        """
        Manages the application state for each request.
        - Makes the state manager available in the request context `g`.
        - Ensures a logged-in user has a state, defaulting to the entry point.
        """
        # Make the state manager accessible for the duration of the request.
        g.state_manager = state_manager

        # Skip state management for static files and authentication routes
        # to prevent errors or redirection loops.
        # The 'auth' blueprint handles login/logout and should not be state-dependent.
        if request.path.startswith('/static/') or (hasattr(request, 'blueprint') and request.blueprint == 'auth'):
            return

        # If a user is logged in but has no application state in their session,
        # set it to the default entry point. This happens on the first request
        # after logging in.
        if 'user_id' in session and 'app_state' not in session:
            state_manager.set_state(state_manager.entry_point)
            logging.info(f"Initialized state for user {session['user_id']} to '{session['app_state']}'")


    # Conditionally initialize external services.
    # This can be bypassed for local UI/state testing by setting the env var.
    BYPASS_EXTERNAL_SERVICES = os.environ.get('BYPASS_EXTERNAL_SERVICES', 'False').lower() in ['true', '1', 't']
    app.config['BYPASS_EXTERNAL_SERVICES'] = BYPASS_EXTERNAL_SERVICES

    # Initialize service placeholders in config
    app.config['FIREBASE_APP'] = None
    app.config['DB'] = None
    app.config['AUTH_CLIENT'] = None
    app.config['MODEL'] = None

    if not app.config.get('TESTING') and not BYPASS_EXTERNAL_SERVICES:
        # --- Firebase Initialization ---
        try:
            SERVICE_ACCOUNT_KEY_PATH = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")
            if not SERVICE_ACCOUNT_KEY_PATH:
                raise ValueError("FIREBASE_SERVICE_ACCOUNT_KEY environment variable not set.")
            if not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
                 raise FileNotFoundError(f"Firebase key file not found at path: {os.path.abspath(SERVICE_ACCOUNT_KEY_PATH)}")

            cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
            firebase_app_instance = None
            try:
                firebase_app_instance = firebase_admin.get_app(name=app.config['FIREBASE_APP_NAME'])
            except ValueError:
                firebase_app_instance = firebase_admin.initialize_app(cred, name=app.config['FIREBASE_APP_NAME'])

            # Store service objects in the app config
            app.config['FIREBASE_APP'] = firebase_app_instance
            app.config['DB'] = firestore.client(app=firebase_app_instance)
            app.config['AUTH_CLIENT'] = firebase_auth.Client(app=firebase_app_instance)
            logging.info("Firebase Admin SDK initialized.")

        except Exception as e:
            logging.critical(f"FATAL ERROR: Could not initialize Firebase: {e}")
            # We don't exit here anymore, the diagnostics will show the error.
            # exit(1) # This would stop the app from running, which we don't want.

        # --- Google AI (Gemini) Initialization ---
        try:
            GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
            if not GEMINI_API_KEY or GEMINI_API_KEY == "PASTE_YOUR_NEW_API_KEY_HERE":
                raise ValueError("GEMINI_API_KEY environment variable not set or is still the placeholder.")

            genai.configure(api_key=GEMINI_API_KEY)
            # Store the model in the app config
            app.config['MODEL'] = genai.GenerativeModel("gemini-1.5-flash-latest")
            logging.info("Google AI Model 'gemini-1.5-flash-latest' initialized.")
        except Exception as e:
            logging.critical(f"FATAL ERROR: Could not initialize Google AI: {e}")
            # We don't exit here anymore, the diagnostics will show the error.
            # exit(1)

    # --- Register Blueprints ---
    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from .game import bp as game_bp
    app.register_blueprint(game_bp)

    from .character import bp as char_bp
    app.register_blueprint(char_bp, url_prefix='/character')

    from .journal import bp as journal_bp
    app.register_blueprint(journal_bp)

    from .profile import bp as profile_bp
    app.register_blueprint(profile_bp)

    from .eoc import bp as eoc_bp
    app.register_blueprint(eoc_bp)

    from .vocabulary import bp as vocab_bp
    app.register_blueprint(vocab_bp, url_prefix='/vocabulary')

    from .api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from .main_menu import bp as main_menu_bp
    app.register_blueprint(main_menu_bp)

    from .tool_handlers import bp as tool_handlers_bp
    app.register_blueprint(tool_handlers_bp)

    from .creator_cockpit import bp as creator_cockpit_bp
    app.register_blueprint(creator_cockpit_bp)

    from .settings import bp as settings_bp
    app.register_blueprint(settings_bp)

    from .system_diagnostics import bp as system_diagnostics_bp
    app.register_blueprint(system_diagnostics_bp)

    # A simple root route to redirect
    @app.route('/')
    def index():
        if 'user_id' in session:
            # If the user is logged in, redirect to the main menu,
            # which will then be handled by the state manager.
            return redirect(url_for('main_menu.menu'))
        # If not logged in, send to the login page.
        return redirect(url_for('auth.login'))

    return app
