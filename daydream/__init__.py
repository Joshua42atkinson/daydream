import os
import logging
import json
import re
from functools import wraps
import uuid

from flask import Flask, session, redirect, url_for
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import auth as firebase_auth
import google.generativeai as genai

# Define globals that will be initialized in create_app
db = None
model = None
auth_client = None
firebase_app = None

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
    global db, model, auth_client, firebase_app

    if not app.config.get('TESTING'):
        # --- Firebase Initialization ---
        try:
            SERVICE_ACCOUNT_KEY_PATH = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")
            if not SERVICE_ACCOUNT_KEY_PATH:
                logging.critical("FATAL: FIREBASE_SERVICE_ACCOUNT_KEY environment variable not set.")
                exit(1)
            if not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
                logging.critical(f"Firebase key file not found at path: {os.path.abspath(SERVICE_ACCOUNT_KEY_PATH)}")
                exit(1)

            cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
            try:
                firebase_app = firebase_admin.get_app(name=app.config['FIREBASE_APP_NAME'])
            except ValueError:
                firebase_app = firebase_admin.initialize_app(cred, name=app.config['FIREBASE_APP_NAME'])

            db = firestore.client(app=firebase_app)
            auth_client = firebase_auth.Client(app=firebase_app)
            logging.info("Firebase Admin SDK initialized.")
        except Exception as e:
            logging.critical(f"FATAL ERROR: Could not initialize Firebase: {e}")
            exit(1)

        # --- Google AI (Gemini) Initialization ---
        try:
            GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
            if not GEMINI_API_KEY or GEMINI_API_KEY == "PASTE_YOUR_NEW_API_KEY_HERE":
                logging.critical("FATAL: GEMINI_API_KEY environment variable not set or is still the placeholder.")
                exit(1)

            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash-latest")
            logging.info("Google AI Model 'gemini-1.5-flash-latest' initialized.")
        except Exception as e:
            logging.critical(f"FATAL ERROR: Could not initialize Google AI: {e}")
            exit(1)

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

    # A simple root route to redirect
    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('profile.profile'))
        return redirect(url_for('auth.login'))

    return app
