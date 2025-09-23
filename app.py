# /home/user/daydream_project/app.py
# ==============================================================================
# app.py - Flask Web Application for Daydream
# Version: 5.3 (Added Introduction Logic) # <<< VERSION UPDATE >>>
# Description: Main Flask application handling routing, game logic,
#              AI interaction, database operations, and session management.
# ==============================================================================

# --- Standard Library Imports ---
import os
import time
import re # Ensure re is imported
import random
import json # Ensure json is imported
import math
from functools import wraps
import logging
import uuid

# --- Third-Party Imports ---
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    flash
)
import firebase_admin
from firebase_admin import credentials, firestore, auth

# Import FieldFilter for fixing warnings
from google.cloud.firestore_v1.base_query import FieldFilter


# --- Application-Specific Imports ---

# Initialize fallbacks outside try block
AWL_WORDS = {}
AWL_DEFINITIONS = {}
def _fallback_calculate_xp(text_input, learned_set): # Removed unused custom_vocab arg
    """Fallback calculate_xp function."""
    return 0, set()
calculate_xp = _fallback_calculate_xp # Assign fallback initially

try:
    # Step 1: Import only what's actually IN vocabulary.py
    from vocabulary import AWL_WORDS as imported_awl_words, calculate_xp as imported_calculate_xp
    AWL_WORDS = imported_awl_words # Overwrite fallback if import succeeds
    calculate_xp = imported_calculate_xp # Overwrite fallback if import succeeds
    logging.info("Imported AWL_WORDS and calculate_xp from vocabulary.py.")

    # Step 2: Try to load definitions from the JSON file
    try:
        AWL_DEFINITIONS_PATH = 'awl_definitions.json' # The specific filename
        if os.path.exists(AWL_DEFINITIONS_PATH):
            with open(AWL_DEFINITIONS_PATH, 'r', encoding='utf-8') as f: # Added encoding
                AWL_DEFINITIONS = json.load(f)
            if isinstance(AWL_DEFINITIONS, dict):
                logging.info(f"Successfully loaded AWL definitions from {AWL_DEFINITIONS_PATH}")
            else:
                logging.warning(f"{AWL_DEFINITIONS_PATH} did not contain a valid JSON dictionary. Using empty definitions.")
                AWL_DEFINITIONS = {}
        else:
            logging.warning(f"{AWL_DEFINITIONS_PATH} not found. Word definitions will be unavailable.")
            AWL_DEFINITIONS = {}
    except json.JSONDecodeError as json_err:
        logging.error(f"Error decoding JSON from {AWL_DEFINITIONS_PATH}: {json_err}. Word definitions unavailable.")
        AWL_DEFINITIONS = {}
    except Exception as file_err:
        logging.error(f"Error reading {AWL_DEFINITIONS_PATH}: {file_err}. Word definitions unavailable.", exc_info=True)
        AWL_DEFINITIONS = {}

except ImportError as e:
    logging.warning(f"Could not import from vocabulary.py: {e}. Using fallbacks for AWL_WORDS and calculate_xp. Word definitions may also be unavailable.")
    pass # Keep fallbacks if import fails


# --- Import quests ---
QUEST_DATA = {}
def _fallback_get_quest(quest_id):
    logging.warning(f"Using fallback get_quest for quest_id: {quest_id}")
    return None
def _fallback_get_quest_step(quest_id, step_id):
    logging.warning(f"Using fallback get_quest_step for quest_id: {quest_id}, step_id: {step_id}")
    return None
get_quest = _fallback_get_quest
get_quest_step = _fallback_get_quest_step

try:
    # Assuming quests.py v4.2 or later is used now
    from quests import QUEST_DATA as imported_quest_data, get_quest as imported_get_quest, get_quest_step as imported_get_quest_step
    QUEST_DATA = imported_quest_data
    get_quest = imported_get_quest
    get_quest_step = imported_get_quest_step
    logging.info("Quest data loaded from quests.py.")
except Exception as e:
    logging.warning(f"quests.py not found or error during import: {e}. Using fallbacks.")
    pass

# --- Import lore ---
thetopia_lore = {}
world_map = {}
ABILITY_NAME_MAP = {}
try:
    # Assuming lore.py is available
    from lore import thetopia_lore as imported_thetopia_lore
    thetopia_lore = imported_thetopia_lore
    world_map = thetopia_lore.get('locations', {}) # Use locations as the world map source
    ABILITY_NAME_MAP = {
        # Map lowercase input to proper name for consistency
        "natural armor": "Natural Armor", "cannot wear armor": "Cannot Wear Armor",
        "fortunate find": "Fortunate Find",
        "integrated systems": "Integrated Systems", "memory limit": "Memory Limit",
        "pack tactics": "Pack Tactics", "fierce loyalty": "Fierce Loyalty",
        "artistic shell": "Artistic Shell", "second brain": "Second Brain",
        "absorb magic": "Absorb Magic", "shapechange": "Shapechange",
        "tinker": "Tinker",
        "arcane affinity": "Arcane Affinity",
        "combat ready": "Combat Ready",
        "empathic": "Empathic",
        "quick wits": "Quick Wits",
        "becoming awesome boost": "Becoming Awesome Boost",
        "law and order gain": "Law and Order Gain",
        "pointlessnesses reroll": "Pointlessnesses Reroll",
    }
    logging.info("Lore data loaded from lore.py.")
except ImportError:
    logging.warning("lore.py not found. Using fallback data.")
    pass # Keep fallbacks

# --- Load Lore Vocabulary ---
lore_vocabulary = {}
try:
    LORE_VOCAB_PATH = 'lore_vocabulary.json'
    if os.path.exists(LORE_VOCAB_PATH):
        with open(LORE_VOCAB_PATH, 'r', encoding='utf-8') as f:
             lore_vocabulary = json.load(f)
        logging.info(f"Lore vocabulary loaded from {LORE_VOCAB_PATH}")
    else:
        logging.warning(f"{LORE_VOCAB_PATH} not found.")
except Exception as e:
    logging.error(f"Error loading {LORE_VOCAB_PATH}: {e}")

# --- Load Pre-made Character Templates ---
premade_character_templates = []
PREMADE_CHARS_PATH = 'premade_characters.json' # Define path outside try block
try:
    if os.path.exists(PREMADE_CHARS_PATH):
        try:
            with open(PREMADE_CHARS_PATH, 'r', encoding='utf-8') as f:
                raw_templates = json.load(f)
            # Remove base_attributes during loading
            premade_character_templates = [{k: v for k, v in t.items() if k != 'base_attributes'} for t in raw_templates]
            if not isinstance(premade_character_templates, list):
                logging.error("premade_chars.json contained data, but it was not in the expected list format after cleaning.")
                premade_character_templates = [] # Reset to empty list
            else:
                logging.info(f"Pre-made characters loaded and cleaned from {PREMADE_CHARS_PATH}")
        except json.JSONDecodeError as json_err:
            logging.error(f"Error decoding JSON from {PREMADE_CHARS_PATH}: {json_err}", exc_info=True)
            premade_character_templates = []
        except Exception as read_err:
            logging.error(f"Error reading or processing {PREMADE_CHARS_PATH}: {read_err}", exc_info=True)
            premade_character_templates = []
    else:
        # This is the path that logs the warning we've been seeing
        logging.warning(f"{PREMADE_CHARS_PATH} not found.")
except Exception as outer_e:
    # Catch any other unexpected errors during the check/load process
    logging.error(f"Unexpected error during pre-made character loading setup for {PREMADE_CHARS_PATH}: {outer_e}", exc_info=True)
    premade_character_templates = [] # Ensure it's empty on any error


# --- Merged Character Data Definitions ---
RACE_DATA = {
    "Sasquatch": {"abilities": ["Natural Armor", "Cannot Wear Armor"], "fate_point_mod": 0},
    "Leprechaun": {"abilities": ["Fortunate Find"], "fate_point_mod": 0},
    "Android": {"abilities": ["Integrated Systems", "Memory Limit"], "fate_point_mod": -1},
    "Opossuman": {"abilities": ["Pack Tactics", "Fierce Loyalty"], "fate_point_mod": 0},
    "Tortisian": {"abilities": ["Artistic Shell", "Second Brain"], "fate_point_mod": 0},
    "Slime": {"abilities": ["Absorb Magic", "Shapechange"], "fate_point_mod": 0},
}
CLASS_DATA = {
    "Inventor": {"focus": "My First Gadget", "ability": "Tinker"},
    "Archanist": {"focus": "Favorite Incantation", "ability": "Arcane Affinity"},
    "Soldier": {"focus": "Weapon of Choice", "ability": "Combat Ready"},
    "Counselor": {"focus": "Trusted Confidante", "ability": "Empathic"},
    "Rascal": {"focus": "Useful Acquaintance", "ability": "Quick Wits"},
}
PHILOSOPHY_DATA = {
    "Becoming Awesome": {"ability": "Becoming Awesome Boost"},
    "Law and Order": {"ability": "Law and Order Gain"},
    "Pointlessnesses": {"ability": "Pointlessnesses Reroll"},
}
# --- End Merged Character Data ---


# --- Constants and Configuration ---
MAX_INPUT_LENGTH = 500
MAX_CONVO_LINES = 100 # Max lines of conversation log saved to Firestore
STARTING_LOCATION = "Thetopia - Town Square"
BASE_FATE_POINTS = 1
FIREBASE_APP_NAME = 'daydream-firebase-app'
DEFAULT_SERVICE_ACCOUNT_KEY_FILE = "daydream-455317-e701a4533dc0.json" # !! REPLACE !!
DEFAULT_VOCAB_LIST_COLOR = "#ADD8E6" # Example color
DEFAULT_AWL_COLOR = "#FFC0CB" # Example color

# Session Keys
SESSION_USER_ID = 'user_id'
SESSION_USER_EMAIL = 'user_email'
SESSION_CHARACTER_ID = 'character_id'
SESSION_CONVERSATION = 'conversation'
SESSION_LOCATION = 'location'
SESSION_LAST_AI_OUTPUT = 'last_ai_output'
SESSION_CHAPTER_INPUTS = 'chapter_player_inputs'
SESSION_EOC_STATE = 'eoc_state'
SESSION_EOC_QUESTIONS = 'eoc_comp_questions'
SESSION_EOC_SUMMARY = 'eoc_report_summary'
SESSION_EOC_PROMPTED = 'eoc_prompted_this_turn'
SESSION_NEW_CHAR_DETAILS = 'new_char_details'
SESSION_AI_RECOMMENDATIONS = 'ai_recommendations'
SESSION_SIDE_QUEST_ACTIVE = 'side_quest_active'
SESSION_SIDE_QUEST_DESC = 'side_quest_description'
SESSION_SIDE_QUEST_TURNS = 'side_quest_turns'

# Firestore Field Names
FS_CONVERSATION = 'conversation_log'
FS_CHAPTER_INPUTS = 'current_chapter_inputs'
FS_QUEST_FLAGS = 'quest_flags' # Dictionary to store flags like {'fountain_analyzed': True}
FS_INVENTORY = 'inventory' # List to store item names like ['Cogwheel', 'Hydro-Spanner']
FS_PLAYER_HAS_SEEN_INTRO = 'has_seen_intro' # <<< NEW >>> Firestore field name constant

# Game Logic Constants
EOC_CHECK_START_TURN = 10
EOC_CHECK_INTERVAL = 4
MIN_INPUTS_FOR_EOC = 10 # Example minimum inputs before EOC can trigger
HERO_JOURNEY_STAGES = [ # Simple stage progression based on chapter number
    "The Ordinary World", "The Call to Adventure", "Refusal of the Call",
    "Meeting the Mentor", "Crossing the Threshold", "Tests, Allies, Enemies",
    "Approach to the Inmost Cave", "The Ordeal", "Reward (Seizing the Sword)",
    "The Road Back", "Resurrection", "Return with the Elixir"
]

# ==============================================================================
# Flask App Initialization & Logging Setup
# ==============================================================================
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # Changed default level to INFO
    logging.info("Flask application initialized and logging configured.")

# ==============================================================================
# Firebase Initialization
# ==============================================================================
firebase_app = None
db = None
try:
    SERVICE_ACCOUNT_KEY_PATH = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY", DEFAULT_SERVICE_ACCOUNT_KEY_FILE)
    if not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
        logging.critical(f"Firebase key not found: {os.path.abspath(SERVICE_ACCOUNT_KEY_PATH)}")
        exit(1)
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
    try:
        firebase_app = firebase_admin.get_app(name=FIREBASE_APP_NAME)
        logging.info(f"Using existing Firebase app: '{FIREBASE_APP_NAME}'")
    except ValueError:
        logging.info(f"Initializing Firebase app: '{FIREBASE_APP_NAME}'")
        firebase_app = firebase_admin.initialize_app(cred, name=FIREBASE_APP_NAME)
    db = firestore.client(app=firebase_app)
    logging.info("Firebase Admin SDK initialized.")
    try:
        # Test connection with a short timeout
        db.collection('_test_connection').document('_doc').get(timeout=5)
        logging.info("Firestore connection test successful.")
    except Exception as db_test_err:
        logging.warning(f"Firestore connection test failed: {db_test_err}")
except Exception as e:
    logging.critical(f"FATAL ERROR: Could not initialize Firebase: {e}")
    exit(1)

# ==============================================================================
# Google AI (Gemini) Initialization
# ==============================================================================
model = None
safety_settings = {}
try:
    # --- Get the API key from environment variables for security ---
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

    if not GEMINI_API_KEY or GEMINI_API_KEY == "PASTE_YOUR_NEW_API_KEY_HERE":
        # Added a check for the placeholder value as well
        logging.critical("FATAL: GEMINI_API_KEY environment variable not set or is still the placeholder.")
        logging.critical("Please set the GEMINI_API_KEY environment variable to your actual Google AI API key.")
        exit(1) # Exit if the key is not configured

    # --- Configure the new library with your key ---
    import google.generativeai as genai # <<< NEW IMPORT
    from google.generativeai.types import HarmCategory, HarmBlockThreshold # <<< ADDED IMPORT
    genai.configure(api_key=GEMINI_API_KEY)
    logging.info("Google AI SDK configured.")

    # --- Initialize the generative model ---
    # The model name is slightly different in this new library
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    logging.info(f"Google AI Model 'gemini-1.5-flash-latest' initialized.")

    # Configure safety settings (the names are the same)
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }
    logging.info("Google AI safety settings configured.")

except Exception as e:
    logging.critical(f"FATAL ERROR: Could not initialize Google AI: {e}")
    exit(1)

# ==============================================================================
# Application Helper Functions
# ==============================================================================

# --- Text Processing for Highlighting ---
def find_terms_in_text(text: str, terms_dict: dict, key_transform=lambda k: k.lower()) -> list[tuple[int, int, str, dict]]:
    """Generic function to find terms in text based on a dictionary."""
    found = []
    if not isinstance(terms_dict, dict) or not text:
        return found

    # Build a map where keys are transformed (e.g., lowercased)
    transformed_map = {}
    for keyword, data in terms_dict.items():
        transformed_key = key_transform(keyword)
        if transformed_key: # Avoid empty keys
            transformed_map[transformed_key] = {"original": keyword, "data": data}

    # Sort keys by length (longest first) to prioritize longer matches
    sorted_keys = sorted(transformed_map.keys(), key=len, reverse=True)

    processed_indices = set() # Track indices already part of a found term

    for term_key in sorted_keys:
        term_info = transformed_map[term_key]
        try:
            # Match whole words only, case-insensitive
            # Use word boundaries (\b) to avoid matching parts of words
            escaped_key = re.escape(term_key)
            for match in re.finditer(r'\b' + escaped_key + r'\b', text, re.IGNORECASE):
                start_index, end_index = match.span()

                # Check for overlap with already processed indices
                is_overlap = any(i in processed_indices for i in range(start_index, end_index))

                if not is_overlap:
                    # Store the start, end, original keyword (for display), and associated data
                    found.append((start_index, end_index, term_info["original"], term_info["data"]))
                    # Mark indices as processed to prevent nested/overlapping highlights
                    processed_indices.update(range(start_index, end_index))

        except re.error as regex_err:
            logging.error(f"Regex error processing term '{term_key}': {regex_err}")
            continue # Skip problematic terms

    # Sort findings by their starting position in the text
    found.sort(key=lambda item: item[0])
    return found

def process_text_for_highlighting(text: str, terms: list[tuple[int, int, str, dict]], span_class: str, data_attribute_name: str = None, data_formatter=lambda d: json.dumps(d).replace("'", "&#39;"), title_formatter=lambda d: d.get('definition', ''), display_formatter=lambda original_keyword, matched_text, term_data: matched_text) -> str:
    """Applies highlighting spans to text based on pre-found terms."""
    if not terms or not text:
        return text # Return original text if no terms found or text is empty

    result_parts = []
    last_end_index = 0

    for start, end, original_keyword, term_data in terms:
        # Append text segment before the current term
        result_parts.append(text[last_end_index:start])

        # Prepare attributes for the span
        current_class = span_class
        attributes = f'class="{current_class}"' if current_class else ''

        # Add title attribute (for hover tooltips)
        title = title_formatter(term_data)
        if title:
            # Ensure title attribute is properly escaped for HTML
            attributes += f' title="{str(title).replace("\"", "&quot;")}"'

        # Add custom data attribute if specified
        if data_attribute_name:
            data_value = data_formatter(term_data)
            # Use single quotes for data attribute to avoid issues if data contains quotes
            attributes += f' {data_attribute_name}=\'{data_value}\''

        # Get the matched text and format display text (usually just the matched text)
        matched_text = text[start:end]
        display_text = display_formatter(original_keyword, matched_text, term_data)

        # Construct the span tag
        span = f'<span {attributes.strip()}>{display_text}</span>'
        result_parts.append(span)

        last_end_index = end # Update position for next iteration

    # Append the remaining text after the last term
    result_parts.append(text[last_end_index:])

    return "".join(result_parts)


# --- Vocabulary Highlighting ---
def apply_vocab_highlighting_python(text: str, vocab_data: dict, color_prefs: dict) -> str:
    """
    Applies highlighting spans for vocabulary terms using user color preferences.
    Applies colors via inline styles, fetched from color_prefs dictionary.
    """
    # Define default fallback colors directly matching CSS variables initially
    DEFAULT_AWL_BG = '#FFE6EB'
    DEFAULT_AWL_TEXT = '#6b0016'
    DEFAULT_AI_BG = '#E1F0FF'
    DEFAULT_AI_TEXT = '#003b4f'

    # Ensure color_prefs is a dict, even if empty
    if not isinstance(color_prefs, dict):
        logging.warning("apply_vocab_highlighting_python received invalid color_prefs, using defaults.")
        color_prefs = {} # Use empty dict to allow .get() with defaults

    if not vocab_data or not text:
        # Return text if no vocab data or text provided
        return text

    # Get user colors from prefs, falling back to defaults if missing/invalid
    awl_bg_color = color_prefs.get('awl_color_bg', DEFAULT_AWL_BG)
    ai_bg_color = color_prefs.get('ai_color_bg', DEFAULT_AI_BG)
    # Basic validation for fetched colors (hex format)
    if not re.match(r'^#[0-9a-fA-F]{6}$', awl_bg_color):
        awl_bg_color = DEFAULT_AWL_BG
    if not re.match(r'^#[0-9a-fA-F]{6}$', ai_bg_color):
        ai_bg_color = DEFAULT_AI_BG

    # Using default text colors defined above for now
    awl_text_color = DEFAULT_AWL_TEXT
    ai_text_color = DEFAULT_AI_TEXT

    # Find terms in text (reusing the generic helper)
    # Lowercase keys in vocab_data for case-insensitive matching
    found_terms = find_terms_in_text(text, vocab_data, key_transform=lambda k: k.lower())

    # Helper to format the title attribute (tooltip)
    def format_vocab_title(data):
        return f"{data.get('definition', '?')} (Source: {data.get('source', '?')})"

    # Build the highlighted string part by part
    result_parts = []
    last_end_index = 0
    for start, end, original_keyword, term_data in found_terms:
        # Append text segment before the current term
        result_parts.append(text[last_end_index:start])

        # Determine if it's AWL or AI based on source
        is_ai_list = term_data.get("source", "AWL") != "AWL"

        # Select the appropriate background and text colors
        bg_color = ai_bg_color if is_ai_list else awl_bg_color
        text_color = ai_text_color if is_ai_list else awl_text_color
        source_class = 'vocab-ai' if is_ai_list else 'vocab-awl'
        css_class = f"highlighted-vocab {source_class}" # Keep class for potential generic styles

        # Construct the inline style attribute
        style_attr = f'background-color: {bg_color}; color: {text_color};'

        # Construct the title attribute
        title_attr = ""
        title = format_vocab_title(term_data)
        if title:
            safe_title = str(title).replace("\"", "&quot;") # Escape quotes for HTML attribute
            title_attr = f' title="{safe_title}"'

        # Build the full span tag
        attributes = f'class="{css_class}" style="{style_attr}"{title_attr}'
        matched_text = text[start:end] # Get the exact text matched
        span = f'<span {attributes}>{matched_text}</span>'
        result_parts.append(span)

        last_end_index = end # Update position for next iteration

    # Append the remaining text after the last term
    result_parts.append(text[last_end_index:])

    return "".join(result_parts)

# --- Lore Highlighting ---
def apply_lore_highlighting_python(text: str, lore_vocab: dict) -> str:
     """Applies highlighting spans for lore terms in Python."""
     if not lore_vocab or not text:
         return text

     # Pre-process lore terms to include display data needed by the formatter
     processed_lore_terms = {}
     for keyword, data in lore_vocab.items():
         processed_lore_terms[keyword] = {
             "display_term": data.get("display_term", keyword.capitalize()), # How the term should look
             "lore_path": data.get("lore_path", []) # Path for JS lookup
         }

     # Find terms using the original key case for lore terms (can be proper nouns)
     found_terms = find_terms_in_text(text, processed_lore_terms, key_transform=lambda k: k)

     # Define formatters specific to lore
     def format_lore_data(data):
         # Format the lore path as a JSON string for the data attribute
         path = data.get("lore_path", [])
         return json.dumps(path).replace("'", "&#39;") # Use HTML entity for single quote

     def format_lore_title(data):
         # Simple title using the display term
         return f"Lore: {data.get('display_term', '?')}"

     def format_lore_display(original_keyword, matched_text, term_data):
         # Display the term using its proper capitalization from lore data
         return term_data.get("display_term", matched_text)

     # Use the generic highlighting function
     highlighted_text = process_text_for_highlighting(
         text,
         found_terms,
         span_class="lore-term", # CSS class for styling
         data_attribute_name="data-lore-path", # Attribute JS will use for lookups
         data_formatter=format_lore_data,
         title_formatter=format_lore_title,
         display_formatter=format_lore_display
     )
     return highlighted_text


# --- AI Interaction ---
def get_ai_response(prompt_type: str, context: dict) -> str | dict:
    """Sends a constructed prompt to Vertex AI and returns the response."""
    if not model:
        logging.error("AI model unavailable during get_ai_response.")
        is_json_output = prompt_type in [
            "ANALYZE_PLAYER_WRITING", "EVALUATE_CHAPTER_COMPREHENSION",
            "GENERATE_NEXT_QUEST", "REVIEW_CHARACTER_SHEET",
            "GENERATE_CONTEXTUAL_VOCAB", "PROCESS_PLAYER_SIDEQUEST_IDEA",
            "EVALUATE_STEP_COMPLETION", # Used by ai_check trigger
            "EVALUATE_SIDEQUEST_COMPLETION"
        ]
        # Return error in expected format (dict for JSON, str for text)
        return {"error": "AI Error", "reason":"AI model not initialized"} if is_json_output else "Error: The Storyteller AI is currently unavailable."

    # --- Build Base Context String ---
    p_name = context.get('player_name', 'Player')
    loc_name = context.get('location', 'The Void')
    q_id = context.get('current_quest_id')
    s_id = context.get('current_step_id')
    p_race = context.get('player_race', '?')
    p_class = context.get('player_class', '?')
    p_philosophy = context.get('player_philosophy', '?')

    # Construct Quest Context String
    q_ctx = "Currently exploring freely."
    if q_id and s_id:
        q_t = context.get('current_quest_title', '')
        s_d = context.get('current_step_description', '')
        # Attempt to fetch title/desc if not provided in context (should usually be there)
        if not q_t:
            q_data = get_quest(q_id)
            q_t = q_data.get('title', '?') if q_data else '?'
        if not s_d:
            s_data = get_quest_step(q_id, s_id)
            s_d = s_data.get('description', '?') if s_data else '?'
        q_ctx = f"Current Quest: '{q_t}'. Objective: '{s_d}'."

    # --- Enhanced Base Instruction ---
    char_profile = f"P={p_name}({p_race}/{p_class}/{p_philosophy})"
    fate_pts = context.get('player_fate_points', 0)
    base_instruct = (
        f"Act as the AI Storyteller for 'Daydream'. Setting: Dumpster Planet (a chaotic realm of discarded ideas). Current Location: {loc_name}. Player Character: {char_profile}. Fate Points: {fate_pts}. "
        f"Your goal is to create an engaging, descriptive narrative experience. Use sensory details (sight, sound, smell, feel) based on the location's lore. "
        f"Interpret player actions creatively, considering their character profile. Narrate outcomes by *showing* the results and consequences. "
        f"Encourage thoughtful player input. Keep responses concise but evocative, suitable for Grades 8-12. "
        f"Current Situation: {q_ctx}"
    )

    prompt = ""
    output_format = "text" # Default output format

    # --- Prompt Construction based on Type (Keep existing prompts from v5.2) ---
    # (No changes to individual prompt structures needed for intro logic)
    if prompt_type == "INITIAL_SETUP":
        loc_lore = thetopia_lore.get('locations', {}).get(loc_name, {})
        npcs_here = loc_lore.get('present_npcs', [])
        lore_desc = loc_lore.get('description', 'A place beyond description.')
        mood = loc_lore.get('mood', 'chaotic but functional')
        prompt = (
             f"{base_instruct}\n\nTask: Welcome {p_name} ({p_race}) to {loc_name}. "
             f"Describe the scene vividly using sensory details (sight, sound, smell). Convey the location's mood ('{mood}'). Mention present NPCs: {npcs_here}. "
             f"Consider {p_name}'s perspective as a {p_race}/{p_class}. End with an open-ended question inviting description or reflection. "
             f"Example ending: 'What aspect of this scene captures your attention first?' or 'How does your {p_race} nature react to this environment?'"
             f"\nRelevant Lore: {lore_desc}"
         )
    elif prompt_type == "GET_DESCRIPTION":
        loc_lore = thetopia_lore.get('locations', {}).get(loc_name, {})
        npcs_here = loc_lore.get('present_npcs', [])
        exits = list(context.get('location_data', {}).get('exits', {}).keys())
        lore_desc = loc_lore.get('description', 'A place beyond description.')
        mood = loc_lore.get('mood', 'chaotic but functional')
        prompt = (
            f"{base_instruct}\n\nTask: Describe {loc_name} in response to 'look around'. Use rich sensory details (sight, sound, smell, feel) and evoke the mood ('{mood}'). "
            f"Describe key features and NPCs ({npcs_here}) based on the lore ({lore_desc}). Mention available exits ({exits}). "
            f"Frame the description from {p_name}'s perspective ({p_race}/{p_class}). Ask what specific detail draws their focus or what they intend to investigate next."
        )
    elif prompt_type == "PROCESS_ABILITY_USE":
        ability = context.get('ability', 'Unknown Ability')
        current_npcs = context.get('thetopia_location_lore',{}).get('present_npcs',[])
        prompt = (
            f"{base_instruct}\n\nTask: Narrate {p_name} using the ability '{ability}'. "
            f"Describe the *process* and *sensory effects* of the ability activating, using flavorful language appropriate for '{ability}'. "
            f"Show the outcome through narrative description (success, partial success, failure, unexpected consequence) based *only* on the ability concept, current situation (location={loc_name}, NPCs={current_npcs}), player's goal ({q_ctx}), and Fate Points ({fate_pts}). "
            f"Describe plausible narrative consequences. NO DICE ROLLS."
         )
    elif prompt_type == "INVALID_DIRECTION":
        direction = context.get('direction', 'that way')
        exits = list(context.get('location_data', {}).get('exits', {}).keys())
        prompt = f"{base_instruct}\n\nTask: Explain *narratively* why {p_name} cannot 'go {direction}' from {loc_name}. Describe the obstacle or reason vividly. Mention available exits: {exits}."
    elif prompt_type == "INVALID_ABILITY":
        ability = context.get('ability', 'that ability')
        reason = context.get('reason', 'it cannot be used now')
        prompt = f"{base_instruct}\n\nTask: Explain *narratively* why {p_name} couldn't use '{ability}'. Reason provided: {reason}. Gently clarify the situation or ability's limitations through description."
    elif prompt_type == "INTERPRET_COMMAND":
        cmd = context.get('command', '')
        loc_lore = thetopia_lore.get('locations', {}).get(loc_name, {})
        npcs_here = loc_lore.get('present_npcs', [])
        abilities = context.get('player_abilities', [])
        lore_desc = loc_lore.get('description','A place beyond description.')
        player_input = context.get('command', '') # Use variable name consistently

        # Base prompt for interpretation
        prompt = (
            f"{base_instruct}\n\nTask: Interpret player command '{player_input}' and narrate the outcome. This command is NOT a move, look, or explicit ability use.\n"
            f"Context: {char_profile} in {loc_name} with {fate_pts} Fate Points. Player Abilities: {abilities}.\n"
            f"Location Details: {lore_desc}. Present NPCs: {npcs_here}.\n"
            f"Response Guidance: Determine player's intent. Consider how a {p_race} {p_class} ({p_philosophy}) would perform this action. "
            f"*Show* the action unfolding and its immediate consequences through sensory details. Narrate a plausible outcome based on context. "
            f"If the command is very simple (e.g., 'open door'), briefly ask for *how* they do it (e.g., 'How do you try the door? Cautiously? Forcefully?'). "
            f"If the command is vague, ask for clarification. If relevant, gently guide towards the quest: {q_ctx}."
        )

        # Add specific NPC interaction context
        interaction_verbs = ["talk", "ask", "speak", "say", "greet", "tell", "question"]
        if any(player_input.lower().startswith(verb + " ") for verb in interaction_verbs):
            target_npc_input = player_input.split(" ", 1)[1] # Get text after the verb
            target_npc_found = None
            npc_detail = "NPC not clearly specified or not present."
            best_match_score = 0

            for npc_name in npcs_here:
                score = 0
                if npc_name.lower() in target_npc_input.lower():
                    score = len(npc_name)
                if score > best_match_score:
                    best_match_score = score
                    target_npc_found = npc_name

            if target_npc_found:
                npc_data = thetopia_lore.get('npcs',{}).get(target_npc_found,{})
                npc_desc = npc_data.get('description','An individual.')
                npc_pers = npc_data.get('personality',[])
                npc_hooks = npc_data.get('dialogue_hooks', {})
                npc_knowledge = npc_data.get('knowledge', [])
                npc_detail = (
                    f"Target NPC ({target_npc_found}): {npc_desc} Personality: {npc_pers}. "
                    f"Knowledge Areas: {npc_knowledge}. Typical Greetings: {npc_hooks.get('greeting', [])}"
                 )
                prompt += (
                    f"\n\nInteraction Guidance: Respond as {target_npc_found}, reflecting their personality ({npc_pers}) and knowledge. "
                    f"Consider how they might react to a {p_race} asking about the topic derived from '{player_input}'. Use their voice."
                 )
            else:
                 prompt += f"\nInteraction Note: {npc_detail}. Ask player to clarify who they are talking to if ambiguous."

    elif prompt_type == "ANALYZE_PLAYER_WRITING":
         output_format = "json"
         text_to_analyze = context.get('chapter_player_text', '')
         prompt = (
             f"Analyze the following player text responses from a single chapter. Evaluate on these metrics:\n"
             f"1. Relevance/Coherence (Combined score, scale 1-5).\n"
             f"2. List of AWL words used (Extract words from the standard Academic Word List).\n"
             f"3. General Style (Low/Medium/High effort/complexity).\n"
             f"4. Critical Thinking evident (Low/Medium/High ability to strategize, infer, or make choices).\n"
             f"5. Average Response Length Category (Short/Medium/Long).\n"
             f"6. Descriptive Language Use (Low/Medium/High use of sensory details and evocative language).\n"
             f"Respond ONLY with a JSON object matching this structure: {{"
             f"\"relevance_coherence_score\":int, \"awl_words_used\":[str], \"style_rating\":\"L|M|H\", "
             f"\"thinking_rating\":\"L|M|H\", \"avg_length_category\":\"S|M|L\", "
             f"\"descriptive_language_rating\":\"L|M|H\""
             f"}}\n\nPlayer Responses:\n{text_to_analyze}"
         )
    elif prompt_type == "EVALUATE_CHAPTER_COMPREHENSION":
         output_format = "json"
         questions = context.get('questions', [])
         answers = context.get('answers', [])
         prompt = f"Evaluate the player's answers based on their understanding of the chapter events, relevance to the questions, and evidence of reasoning (scale 1-10 for each answer).\n" + "\n".join([f"Q{i+1}: {q}\nA{i+1}: {(answers[i] if i < len(answers) else '(No Answer)')}" for i,q in enumerate(questions)]) + f"\n\nProvide an overall average comprehension score (float, 1-10).\nRespond ONLY with JSON: {{\"overall_comprehension_score\": float}}."

    elif prompt_type == "REVIEW_CHARACTER_SHEET":
        output_format = "json"
        sheet_data = context.get('character_sheet_data', {})
        # Only include narrative fields for review
        sheet_data_narrative = {k: v for k, v in sheet_data.items() if k in ['name', 'race_name', 'class_name', 'philosophy_name', 'boon', 'backstory', 'starting_quest']}
        prompt = (
            f"Review the following player-created character sheet for narrative potential in the 'Daydream' game (Dumpster Planet setting: chaotic realm of discarded ideas, hub: Thetopia).\n"
            f"Check for clarity, interesting hooks based on lore (Races: {list(thetopia_lore.get('races',{}).keys())}, Classes: {list(thetopia_lore.get('classes',{}).keys())}, Philosophies: {list(thetopia_lore.get('philosophies',{}).keys())}), internal consistency, and playability. Focus on narrative aspects only.\n"
            f"Character Sheet:\n{json.dumps(sheet_data_narrative, indent=2)}\n\n"
            f"Respond ONLY with a JSON object containing specific, constructive recommendations focused on enhancing narrative depth or clarity. "
            f"Structure: {{ \"recommendations\": [ {{ \"field\": \"field_name\", \"type\": \"clarify|enhance|issue|interesting\", \"suggestion\": \"text describing the suggestion...\" }} ] }} or {{ \"recommendations\": [] }} if it looks good."
        )

    elif prompt_type == "GENERATE_NEXT_QUEST":
        output_format = "json"
        char_data = context.get('character_data', {})
        summaries = context.get('chapter_summaries', [])
        stage = context.get('next_hero_journey_stage', 'Unknown Stage')
        char_data_narrative = {k:v for k,v in char_data.items() if k in ['name', 'race_name', 'class_name', 'philosophy_name', 'boon', 'backstory', 'abilities', 'aspects']}
        chapter_num = len(summaries) + 1
        last_summary_text = summaries[-1].get('summary','(No previous summary)') if summaries else '(First Chapter)'
        prompt = (
            f"Generate the *next* quest (Chapter {chapter_num}) for the Daydream game.\nCharacter Profile:\n{json.dumps(char_data_narrative, indent=2)}\n"
            f"Most Recent Chapter Summary:\n{last_summary_text}\nTarget Hero's Journey Stage: {stage}\n"
            f"Requirements:\n1. Create a conflict/goal that *directly follows from or reacts to* the character details and the MOST RECENT chapter summary.\n"
            f"2. Ensure strong narrative continuity. The quest should feel like a consequence or next step.\n"
            f"3. Align theme with the target journey stage ({stage}).\n"
            f"4. Provide an actionable starting step description that clearly guides the player.\n"
            f"5. Use unique IDs based on chapter and character.\n"
            f"Respond ONLY with JSON: {{\"quest_id\":\"Q_CH{chapter_num}_{char_data.get('id', 'char')[-4:]}\", \"title\":\"Chapter {chapter_num}: [Concise Title]\", \"description\":\"[Brief overall quest description building on previous chapter]\", \"starting_step_id\":\"STEP_01\", \"starting_step_description\":\"[Clear, actionable first step description]\"}}"
         )

    elif prompt_type == "GENERATE_CONTEXTUAL_VOCAB":
        output_format = "json"
        target_word = context.get('target_word', '')
        if not target_word:
            return {"error":"Missing Input", "reason": "Target word for vocabulary generation is missing"}
        prompt = f"Task: Generate a contextual vocabulary list related to the word '{target_word}'.\n1. Provide a clear definition for '{target_word}' suitable for grades 8-12.\n2. List exactly 25 related words (synonyms, antonyms, conceptually linked terms).\n3. Provide a clear definition for each of the 25 related words, suitable for grades 8-12.\nFormat ONLY JSON: {{\"target_word_info\":{{\"word\":\"{target_word}\",\"definition\":\"...\"}},\"related_words\":[{{\"word\":\"word1\",\"definition\":\"...\"}},...,{{\"word\":\"word25\",\"definition\":\"...\"}}]}}"

    elif prompt_type == "CHECK_CHAPTER_PROGRESS":
        output_format = "text" # Expecting YES / NO / SUGGEST_TASK
        char_info = f"P={p_name}({p_race}/{p_class}/{p_philosophy})"
        quest_info = f"Quest:'{context.get('current_quest_title','?')}' Step:'{context.get('current_step_description','?')}'"
        conversation_summary = context.get('conversation_summary', '(no recent conversation)')
        turn_count = context.get('turn_count', 0)
        inputs_count = context.get('inputs_count', 0)
        prompt = (
            f"Analyze the current game state. Turn Count: {turn_count}. Inputs this Chapter: {inputs_count}. Character: {char_info}. Current Objective: {quest_info}. Recent Conversation Summary:\n{conversation_summary}\n\n"
            f"Task: Evaluate if the chapter has had sufficient narrative development and player interaction for a meaningful end-of-chapter evaluation (consider turns > {EOC_CHECK_START_TURN} and inputs > {MIN_INPUTS_FOR_EOC}).\n"
            f"1. If significant progress on the objective OR substantial exploration/interaction has occurred, AND the chapter feels sufficiently developed for evaluation, respond ONLY with 'YES'.\n"
            f"2. If a natural pause point seems reached (e.g., objective part met) BUT the chapter feels short or lacks interaction depth for a good evaluation, respond ONLY with 'SUGGEST_TASK'.\n"
            f"3. Otherwise, respond ONLY with 'NO'."
         )

    elif prompt_type == "INITIATE_PLAYER_SIDEQUEST":
         prompt = (
             f"{base_instruct}\n\nTask: Inform the player they've reached a natural pause point, but the current chapter could use a bit more activity for a full reflection. Offer them a chance to define a brief, personal side task for writing practice.\n"
             f"Ask them clearly: 'What small, immediate goal or observation would your character like to focus on right now before we conclude this chapter?'"
             f"\nKeep the tone encouraging and focused on creative practice."
         )
    elif prompt_type == "PROCESS_PLAYER_SIDEQUEST_IDEA":
         output_format = "json" # Expecting JSON objective back
         player_idea = context.get('player_sidequest_idea', '')
         prompt = (
              f"{base_instruct}\n\nPlayer proposed side task: '{player_idea}'\n\n"
              f"Task: Interpret the player's idea. Formulate a concise, actionable mini-objective (1-2 steps max) based on their input. If the idea is too complex or vague, generate a simpler, related objective suitable for a short detour (approx 3-5 turns).\n"
              f"Respond ONLY with JSON: {{\"side_quest_objective\": \"[Generated concise objective description]\"}}"
          )
    elif prompt_type == "EVALUATE_SIDEQUEST_COMPLETION":
         output_format = "text" # Expecting YES/NO
         side_quest_obj = context.get('side_quest_objective', '')
         recent_conv = context.get('conversation_summary', '')
         prompt = (
              f"{base_instruct}\n\nSide Quest Objective Was: '{side_quest_obj}'\nRecent Conversation:\n{recent_conv}\n\n"
              f"Task: Briefly assess if the player seems to have reasonably addressed or completed their self-defined side quest objective based ONLY on the recent conversation provided. Focus on effort/engagement rather than strict success.\n"
              f"Respond ONLY with 'YES' or 'NO'."
          )

    elif prompt_type == "EVALUATE_STEP_COMPLETION":
        output_format = "text" # Expecting YES/NO
        step_desc = context.get('step_description', '')
        player_action = context.get('player_action', '') # Last player input
        ai_outcome = context.get('ai_outcome', '') # Last AI response narrating outcome
        check_criteria = context.get('ai_check_criteria', 'if the player performed the action')

        prompt = (
            f"Evaluate if the player's action likely completed the step based on the outcome and the specific criteria.\n"
            f"Step Objective Hint: '{step_desc}'\n"
            f"Player's Action This Turn: '{player_action}'\n"
            f"Narrated Outcome This Turn: '{ai_outcome}'\n\n"
            f"Criteria: Based *only* on the Player's Action and Narrated Outcome text provided above, determine {check_criteria}. "
            f"Focus on whether the described action or intent occurred this turn.\n"
            f"Respond ONLY with 'YES' or 'NO'."
        )

    else:
        logging.warning(f"Unknown prompt type requested: '{prompt_type}'. Using fallback.")
        prompt = base_instruct + "\n\nMy Task: Respond gracefully to an unclear request."


    # --- AI Call and Response Handling ---
    try:
        logging.info(f"Sending prompt type '{prompt_type}' to Vertex AI...")
        # logging.debug(f"Full Prompt for {prompt_type}: {prompt}") # Uncomment for deep debugging
        response = model.generate_content(prompt, safety_settings=safety_settings)
        ai_text = None

        # Check if response blocked
        if not response.candidates:
             feedback = getattr(response, 'prompt_feedback', None)
             block_reason = getattr(feedback, 'block_reason', 'Unknown') if feedback else 'Unknown'
             error_msg = f"Blocked: {block_reason}"
             logging.warning(f"AI response blocked for prompt type '{prompt_type}'. Reason: {block_reason}")
             is_json = output_format == "json"
             return {"error": "AI Error", "reason": error_msg} if is_json else f"Error: AI response blocked ({block_reason})."

        # Check finish reason
        candidate = response.candidates[0]
        finish_reason_name = candidate.finish_reason.name
        if finish_reason_name != 'STOP' and finish_reason_name != 'MAX_TOKENS':
            is_safety = (finish_reason_name == 'SAFETY')
            logging.warning(f"AI generation finished unexpectedly for '{prompt_type}'. Reason: {finish_reason_name}")
            error_msg = "Blocked: Safety" if is_safety else f"AI stopped: {finish_reason_name}"
            safety_ratings_str = ""
            if candidate.safety_ratings:
                 ratings_str_list = [f"{r.category.name}: {r.probability.name}" for r in candidate.safety_ratings if r.blocked]
                 if ratings_str_list:
                     safety_ratings_str = f" [{', '.join(ratings_str_list)}]"
            error_msg += safety_ratings_str
            logging.warning(f"Safety Ratings Details: {safety_ratings_str}")
            is_json = output_format == "json"
            return {"error": "AI Error", "reason": error_msg} if is_json else f"Error: AI generation stopped ({error_msg})."

        # Extract text content
        if candidate.content and candidate.content.parts:
            ai_text = candidate.content.parts[0].text
        else:
             logging.warning(f"AI response content is empty for prompt type '{prompt_type}'.")
             ai_text = "" # Use empty string if no text

        # Ensure text is string
        if not isinstance(ai_text, str):
            logging.warning(f"AI response was not a string for '{prompt_type}' (Type: {type(ai_text)}). Attempting conversion.")
            try:
                ai_text = str(ai_text)
            except Exception:
                ai_text = "" # Fallback to empty string on conversion failure

        # Process JSON or Text response
        if output_format == "json":
            if not ai_text.strip():
                 logging.error(f"AI returned an empty string when JSON was expected for prompt type '{prompt_type}'.")
                 return {"error": "AI Error", "reason": "Empty JSON response"}
            try:
                # Remove markdown code block fences if present
                clean_json_str = re.sub(r'^```json\s*|\s*```$', '', ai_text.strip(), flags=re.M|re.S)
                return json.loads(clean_json_str)
            except json.JSONDecodeError as json_err:
                logging.error(f"Failed to decode AI JSON response for '{prompt_type}'. Error: {json_err}. Raw text: >>>{ai_text}<<<")
                # Attempt recovery if possible
                match = re.search(r'\{.*\}', ai_text, re.S) # Find first JSON-like object
                if match:
                    try:
                        recovered_json = json.loads(match.group(0))
                        logging.warning(f"Successfully recovered JSON object from malformed response for '{prompt_type}'.")
                        return recovered_json
                    except Exception as recovery_err:
                        logging.error(f"Attempted JSON recovery failed for '{prompt_type}'. Recovery error: {recovery_err}")
                # Return error if decode/recovery fails
                return {"error": "JSON Parse Fail", "reason": str(json_err), "raw": ai_text}
            except Exception as e:
                # Catch other potential errors during JSON processing
                logging.error(f"Unexpected error processing JSON response for '{prompt_type}': {e}")
                return {"error": "JSON Processing Error", "reason": str(e), "raw": ai_text}
        else: # Text output
            # Clean up potential AI prefixes and strip whitespace
            cleaned = ai_text.strip()
            cleaned = re.sub(r'^(AI|Storyteller|Assistant|Guide):\s*', '', cleaned, count=1, flags=re.IGNORECASE)
            # Return cleaned text or a fallback message
            return cleaned if cleaned else "(The Storyteller seems lost in thought...)"

    except Exception as api_err:
         # Catch errors during the API call itself
         logging.error(f"Vertex AI API call failed for prompt type '{prompt_type}': {api_err}", exc_info=True)
         is_json = output_format == "json"
         # Return error in the expected format
         return {"error": "AI Error", "reason": f"API Call Failed: {str(api_err)}"} if is_json else "Error: Could not communicate with the Storyteller AI."


# --- Custom Vocabulary Helper ---
def get_active_vocab_data(user_id: str) -> dict:
    """
    Fetches user's vocabulary settings (including custom colors) and
    compiles active AWL/AI words. Returns a dictionary:
    { "settings": { "use_default_awl": bool, "awl_color_bg": str, "ai_color_bg": str },
      "vocab": { "word": {"definition": str, "source": str} } }
    """
    # Define robust defaults, including colors
    default_settings = {
        "use_default_awl": True,
        'awl_color_bg': '#FFE6EB', # Default pinkish bg
        'ai_color_bg': '#E1F0FF'   # Default blueish bg
    }
    fallback_return = {"settings": default_settings.copy(), "vocab": {}} # Use copy

    if not user_id or not db:
        logging.error("get_active_vocab_data called without user_id or DB connection.")
        return fallback_return

    consolidated_vocab = {}
    user_settings = default_settings.copy() # Start with defaults

    try:
        profile_ref = db.collection('player_profiles').document(user_id)
        # Fetch the entire vocab_settings field
        profile_doc = profile_ref.get(['vocab_settings']) # Only fetch the settings field

        if profile_doc.exists:
            settings_data = profile_doc.to_dict().get('vocab_settings', {})
            if isinstance(settings_data, dict): # Ensure it's a dictionary
                # Update settings from Firestore, keeping defaults if keys are missing
                user_settings['use_default_awl'] = settings_data.get('use_default_awl', user_settings['use_default_awl'])
                user_settings['awl_color_bg'] = settings_data.get('awl_color_bg', user_settings['awl_color_bg'])
                user_settings['ai_color_bg'] = settings_data.get('ai_color_bg', user_settings['ai_color_bg'])
            else:
                logging.warning(f"Firestore 'vocab_settings' for user {user_id} is not a dictionary ({type(settings_data)}). Using defaults.")
        else:
            logging.info(f"No profile document or vocab_settings found for user {user_id}. Using default settings.")


        # --- Compile Vocabulary Words ---
        # Add default AWL words if enabled in settings
        if user_settings['use_default_awl']:
            if AWL_WORDS and AWL_DEFINITIONS:
                # We only need word, definition, and source here. Color applied later.
                for word in AWL_WORDS:
                    lower_word = word.lower()
                    definition = AWL_DEFINITIONS.get(lower_word, "Definition not found.")
                    if lower_word not in consolidated_vocab: # Avoid overwriting AI list words if same
                        consolidated_vocab[lower_word] = {
                            "definition": definition,
                            "source": "AWL" # Mark source clearly
                        }
            else:
                logging.warning(f"AWL vocabulary enabled for user {user_id}, but AWL_WORDS or AWL_DEFINITIONS data is missing.")

        # Add words from user's active, AI-generated lists
        custom_lists_ref = profile_ref.collection('custom_vocab_lists')
        # Query for lists that are both active and AI-generated
        # Using FieldFilter for clarity and compatibility
        active_ai_lists_query = custom_lists_ref.where(filter=FieldFilter('is_active', '==', True)).where(filter=FieldFilter('is_ai_generated', '==', True)).stream()

        for list_doc in active_ai_lists_query:
            list_data = list_doc.to_dict()
            list_name = list_data.get('name', 'AI List') # Use list name as source
            words_array = list_data.get('words', [])
            # Iterate through words in the list
            for word_entry in words_array:
                word = word_entry.get('word')
                definition = word_entry.get('definition')
                if word and definition:
                    # Add word to consolidated list, overwriting AWL if same word
                    consolidated_vocab[word.lower()] = {
                        "definition": definition,
                        "source": list_name # Use the AI list name as the source
                    }
                else:
                    logging.warning(f"Skipping invalid word entry in list {list_doc.id} for user {user_id}: {word_entry}")

    except Exception as e:
        logging.error(f"Error fetching vocabulary data for user {user_id}: {e}", exc_info=True)
        # Return default settings on error
        return fallback_return

    logging.info(f"Compiled {len(consolidated_vocab)} active vocab words for user {user_id}. Settings: {user_settings}")
    # Return the full settings dict (including colors) and the vocab data
    return { "settings": user_settings, "vocab": consolidated_vocab }

# --- Data Management Helpers ---
def get_user_characters(user_id:str) -> list[dict]:
    """Retrieves a list of character summaries for a given user."""
    chars = []
    if not db:
        logging.error("Database unavailable: cannot execute get_user_characters.")
        return chars
    if not user_id:
         logging.error("User ID not provided to get_user_characters.")
         return chars
    try:
        # Query characters collection for documents matching the user_id
        # Using FieldFilter for clarity and compatibility
        docs_query = db.collection('characters').where(filter=FieldFilter('user_id', '==', user_id))
        docs_stream = docs_query.stream()
        # Iterate through found documents and extract summary data
        for doc in docs_stream:
            d = doc.to_dict()
            chars.append({
                "id": doc.id,
                "name": d.get("name", "Unnamed Character"),
                "race": d.get("race_name", "Unknown Race"),
                "class": d.get("class_name", "Unknown Class")
            })
    except Exception as e:
        logging.error(f"Failed to fetch characters for user {user_id}: {e}", exc_info=True)
    # Log how many characters were found
    logging.info(f"Found {len(chars)} characters for user {user_id}")
    return chars

def load_character_data(user_id:str, char_id:str) -> dict | None:
    """Loads full character data from Firestore, ensuring user ownership and initializing fields."""
    if not user_id or not char_id or not db:
        logging.error(f"load_character_data missing arguments or DB connection. User: {user_id}, Char: {char_id}")
        return None
    try:
        doc_ref = db.collection('characters').document(char_id)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            # --- Security Check ---
            if data.get('user_id') != user_id:
                flash("Permission denied to load this character.", "error")
                logging.warning(f"SECURITY ALERT: User {user_id} attempted to load character {char_id} owned by {data.get('user_id')}.")
                return None

            # --- Initialize Core Fields with Defaults ---
            data['id'] = char_id # Add doc ID for reference
            data.setdefault('name', 'Unnamed Character')
            data.setdefault('race_name', 'Unknown')
            data.setdefault('class_name', 'Unknown')
            data.setdefault('philosophy_name', 'Unknown')
            data.setdefault('boon', 'None')
            data.setdefault('backstory', 'A mystery.')
            data.setdefault('abilities', [])
            data.setdefault('aspects', [])
            data.setdefault('current_location', STARTING_LOCATION)
            data.setdefault('current_quest_id', None)
            data.setdefault('current_step_id', None)
            data.setdefault('current_quest_title', '')
            data.setdefault('current_step_description', '')
            data.setdefault('report_summaries', [])
            data.setdefault('turn_count', 0)
            data.setdefault(SESSION_EOC_PROMPTED, False) # Use constant if defined, else string
            data.setdefault(FS_CONVERSATION, [])
            data.setdefault(FS_CHAPTER_INPUTS, [])
            data.setdefault(FS_QUEST_FLAGS, {}) # Initialize as empty dict if missing
            data.setdefault(FS_INVENTORY, []) # Initialize as empty list if missing

            # Ensure learned_vocab is a set
            loaded_vocab = data.get('learned_vocab', [])
            if isinstance(loaded_vocab, list):
                data['learned_vocab'] = set(loaded_vocab)
            elif isinstance(loaded_vocab, set):
                data['learned_vocab'] = loaded_vocab # Already a set
            else:
                data['learned_vocab'] = set() # Fallback for unexpected types

            # Initialize fate points if missing
            if 'fate_points' not in data:
                race_mod = RACE_DATA.get(data.get('race_name','?'), {}).get('fate_point_mod', 0)
                data['fate_points'] = BASE_FATE_POINTS + race_mod

            # Remove deprecated fields if they exist (optional cleanup)
            deprecated_keys = ['attributes', 'level', 'xp', 'xp_next_level', 'attribute_points_to_spend']
            for key in deprecated_keys:
                data.pop(key, None)

            logging.info(f"Successfully loaded character {char_id} ('{data.get('name','?')}') for user {user_id}")
            return data
        else:
            logging.warning(f"Character document {char_id} not found for user {user_id}.")
            flash("Character not found.", "error")
            return None
    except Exception as e:
        logging.error(f"Failed to load character {char_id} for user {user_id}: {e}", exc_info=True)
        flash("An error occurred while loading the character.", "error")
        return None

def save_character_data(user_id:str, character_data:dict|None) -> str|None:
    """Saves character data to Firestore, ensuring necessary fields exist and formatting lists."""
    if not user_id or not character_data or not db:
        logging.error(f"save_character_data missing arguments or DB connection. User: {user_id}")
        return None
    doc_id = character_data.get('id')
    if not doc_id:
        logging.error("save_character_data called without 'id' in character_data.")
        return None

    try:
        # Create a copy to avoid modifying the original dict in memory
        save_data = character_data.copy()
        save_data['user_id'] = user_id # Ensure user_id is set

        # Convert learned_vocab set back to sorted list for Firestore
        if 'learned_vocab' in save_data and isinstance(save_data['learned_vocab'], set):
            save_data['learned_vocab'] = sorted(list(save_data['learned_vocab']))
        else:
            save_data['learned_vocab'] = [] # Ensure it's always a list

        # Ensure conversation log is a list and trim if necessary
        save_data[FS_CONVERSATION] = list(save_data.get(FS_CONVERSATION, []))[-MAX_CONVO_LINES:]
        # Ensure chapter inputs is a list
        save_data[FS_CHAPTER_INPUTS] = list(save_data.get(FS_CHAPTER_INPUTS, []))
        # Ensure quest flags and inventory are correct types
        save_data[FS_QUEST_FLAGS] = dict(save_data.get(FS_QUEST_FLAGS, {})) # Ensure it's a dict
        save_data[FS_INVENTORY] = list(save_data.get(FS_INVENTORY, [])) # Ensure it's a list

        # Remove temporary session-related keys before saving
        save_data.pop('id', None) # Don't save the ID within the document data itself
        session_keys_to_remove = [
             SESSION_CONVERSATION, SESSION_CHAPTER_INPUTS, SESSION_SIDE_QUEST_ACTIVE,
             SESSION_SIDE_QUEST_DESC, SESSION_SIDE_QUEST_TURNS,
             SESSION_LAST_AI_OUTPUT, SESSION_EOC_STATE, SESSION_EOC_QUESTIONS,
             SESSION_EOC_SUMMARY, SESSION_AI_RECOMMENDATIONS, SESSION_NEW_CHAR_DETAILS
         ]
        for key in session_keys_to_remove:
            save_data.pop(key, None)

        # Remove deprecated fields explicitly (optional cleanup)
        deprecated_keys = ['attributes', 'level', 'xp', 'xp_next_level', 'attribute_points_to_spend']
        for key in deprecated_keys:
            save_data.pop(key, None)

        # Ensure core fields always exist before saving to prevent errors on load
        core_fields = {
            'name': 'Unnamed Character', 'race_name': 'Unknown', 'class_name': 'Unknown',
            'philosophy_name': 'Unknown', 'boon': 'None', 'backstory': 'A mystery.',
            'abilities': [], 'aspects': [], 'current_location': STARTING_LOCATION,
            'current_quest_id': None, 'current_step_id': None, 'current_quest_title': '',
            'current_step_description': '', 'turn_count': 0, SESSION_EOC_PROMPTED: False,
            'report_summaries': [], 'learned_vocab': [], FS_CONVERSATION: [],
            FS_CHAPTER_INPUTS: [], FS_QUEST_FLAGS: {}, FS_INVENTORY: []
        }
        for field, default in core_fields.items():
            save_data.setdefault(field, default) # Set default only if key is missing

        # Recalculate default fate points if missing (should have been set by load_character_data)
        if 'fate_points' not in save_data:
            race_mod = RACE_DATA.get(save_data.get('race_name','?'), {}).get('fate_point_mod', 0)
            save_data['fate_points'] = BASE_FATE_POINTS + race_mod

        # Save the cleaned data using merge=True for safety
        db.collection('characters').document(doc_id).set(save_data, merge=True)
        logging.info(f"Successfully saved character document {doc_id} for user {user_id}")
        return doc_id
    except Exception as e:
        logging.error(f"Failed to save character {doc_id} for user {user_id}: {e}", exc_info=True)
        flash("A critical error occurred while saving your progress.", "error")
        return None

# --- Premium Access Check ---
def check_premium_access(user_id:str) -> bool:
    """Checks if the user has premium access via their profile."""
    if not user_id or not db:
        return False
    try:
        profile_ref = db.collection('player_profiles').document(user_id)
        profile_doc = profile_ref.get(['has_premium']) # Only fetch necessary field
        if profile_doc.exists:
            return profile_doc.to_dict().get('has_premium', False)
        else:
            return False # Default to False if profile doesn't exist or lacks field
    except Exception as e:
        # Log error but default to False to prevent accidental premium access
        logging.error(f"Error during premium access check for user {user_id}: {e}", exc_info=True)
        return False

# --- Login Decorator ---
def login_required(f):
    """Decorator to ensure user is logged in before accessing a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if SESSION_USER_ID not in session:
            flash("You must be logged in to access this page.", "warning")
            # Store the intended URL to redirect after login
            return redirect(url_for('login', next=request.url))
        # User is logged in, proceed with the original function
        return f(*args, **kwargs)
    return decorated_function


# ==============================================================================
# Quest Step Completion Logic Helper
# ==============================================================================
def check_step_completion(p_data: dict, step_data: dict) -> tuple[bool, str | None]:
    """
    Checks if the conditions for completing the current quest step are met based
    on player data (quest flags, inventory) or signals if an AI check is required.

    Returns a tuple: (completion_status: bool, ai_check_criteria: str | None)
    ai_check_criteria is populated ONLY if the trigger is 'ai_check'.
    """
    if not step_data or not p_data:
        logging.warning("check_step_completion called with missing step_data or p_data.")
        return False, None

    trigger = step_data.get('trigger_condition')
    if not trigger or not isinstance(trigger, str):
        logging.warning(f"Step {p_data.get('current_step_id', '?')} is missing a valid trigger condition string.")
        return False, None

    # Use regex for more robust parsing, allowing optional spaces
    match = re.match(r'^\s*(\w+)\s*:\s*(.*)$', trigger)
    if not match:
        logging.error(f"Invalid trigger format: '{trigger}'. Expected 'type:condition'.")
        return False, None

    trigger_type = match.group(1).strip().lower()
    condition = match.group(2).strip()

    logging.info(f"Checking trigger: type='{trigger_type}', condition='{condition}' for step {p_data.get('current_step_id', '?')}")

    # --- State Variable Check ---
    if trigger_type == "state_var":
        # Expects format "flag_name == True" or "flag_name == False" (case-insensitive for True/False)
        state_match = re.match(r'^\s*([\w_]+)\s*==\s*(True|False)\s*$', condition, re.IGNORECASE)
        if state_match:
            flag_name = state_match.group(1).strip()
            expected_value_str = state_match.group(2).strip().lower()
            expected_value = (expected_value_str == 'true')

            quest_flags = p_data.get(FS_QUEST_FLAGS, {})
            actual_value = quest_flags.get(flag_name, False) # Default to False if flag not set

            logging.debug(f"State var check: Flag '{flag_name}', Expected: {expected_value}, Actual: {actual_value}")
            is_complete = (actual_value == expected_value)
            return is_complete, None # No AI check needed
        else:
            logging.error(f"Invalid state_var trigger format: '{condition}'. Expected 'flag_name == True' or 'flag_name == False'.")
            return False, None

    # --- Inventory Check ---
    elif trigger_type == "inventory_has":
        # Expects format "item1 and item2 and ..." (case-sensitive item names)
        required_items = [item.strip() for item in condition.split(' and ') if item.strip()]
        if not required_items:
            logging.error(f"Invalid inventory_has trigger: No items specified in '{condition}'.")
            return False, None

        # Ensure inventory is a list (or set for efficiency if large)
        inventory = p_data.get(FS_INVENTORY, [])
        inventory_set = set(inventory) if isinstance(inventory, (list, set)) else set()

        all_items_present = True
        missing_items = []
        for item in required_items:
            if item not in inventory_set:
                all_items_present = False
                missing_items.append(item)

        if not all_items_present:
            logging.debug(f"Inventory check failed: Missing item(s) {missing_items}. Required: {required_items}, Has: {list(inventory_set)}")

        return all_items_present, None # No AI check needed

    # --- AI Check Preparation ---
    elif trigger_type == "ai_check":
        # Return False for completion status *for now*, but provide the criteria string
        # The game loop will perform the check based on the player's action this turn.
        ai_check_criteria = condition
        if not ai_check_criteria:
             logging.warning(f"AI Check trigger found for step {p_data.get('current_step_id', '?')} but condition is empty.")
             return False, None # Treat as invalid trigger

        logging.info(f"AI Check trigger identified. Criteria: '{ai_check_criteria}'. Evaluation required in game loop.")
        return False, ai_check_criteria

    # --- Unknown Trigger Type ---
    else:
        logging.warning(f"Unknown trigger condition type: '{trigger_type}' in trigger '{trigger}'")
        return False, None


# ==============================================================================
# Reward Handling Helper
# ==============================================================================
def apply_reward(p_data: dict, reward_data: dict | None, user_id: str) -> str | None:
    """
    Applies a step or quest reward to the player data (p_data dictionary).
    Handles rewards like: fate_points, info/set_flag, item, relationship.
    Returns announcement text (str) or None if silent/invalid. Modifies p_data directly.
    """
    if not reward_data or not isinstance(reward_data, dict) or not p_data:
        return None # No reward data or player data provided

    reward_type = reward_data.get("type")
    value = reward_data.get("value") # Used by fate_points
    details = reward_data.get("details") # Used by info/relationship
    name = reward_data.get("name") # Used by item
    target = reward_data.get("target") # Used by relationship
    change = reward_data.get("change") # Used by relationship
    flag_to_set_data = reward_data.get("set_flag") # Used by info
    silent = reward_data.get("silent", False) # Check if reward announcement should be suppressed

    announcement = None
    char_id_log = p_data.get('id', '?') # For logging

    logging.info(f"Applying reward: {reward_data} for user {user_id}, char {char_id_log}")

    try:
        if reward_type == "fate_points":
            try:
                fp_change = int(value)
                if fp_change != 0:
                    current_fp = p_data.get("fate_points", BASE_FATE_POINTS)
                    # Ensure current value is numeric before adding
                    if not isinstance(current_fp, (int, float)):
                         logging.warning(f"Character {char_id_log} fate_points field is not numeric ({type(current_fp)}). Resetting to base before applying change.")
                         current_fp = BASE_FATE_POINTS
                    p_data["fate_points"] = current_fp + fp_change
                    if not silent:
                        announcement = f"You gain {fp_change} Fate Point(s)." if fp_change > 0 else f"You lose {abs(fp_change)} Fate Point(s)."
                    logging.info(f"  Applied {fp_change} Fate Points reward. New total: {p_data['fate_points']}")
            except (ValueError, TypeError):
                logging.warning(f"  Invalid 'value' for fate_points reward: {value}")

        elif reward_type == "info":
            # Primarily used for setting flags, but can have announcement text
            if details and not silent:
                announcement = f"Info: {details}" # Use details as the announcement

            # Handle setting quest flags via 'set_flag' sub-dictionary
            if isinstance(flag_to_set_data, dict):
                # Ensure quest_flags dictionary exists
                quest_flags = p_data.setdefault(FS_QUEST_FLAGS, {})
                for flag_name, flag_value in flag_to_set_data.items():
                    if isinstance(flag_name, str) and isinstance(flag_value, bool):
                         quest_flags[flag_name] = flag_value # Set the flag
                         logging.info(f"  Set quest flag '{flag_name}' to '{flag_value}' via info reward.")
                    else:
                         logging.warning(f"  Invalid flag name ('{flag_name}') or value ('{flag_value}') in 'set_flag' for info reward. Flag name must be string, value must be boolean.")
            elif flag_to_set_data: # Log warning if format is wrong but it exists
                 logging.warning(f"  Invalid 'set_flag' format in info reward: {flag_to_set_data}. Expected a dictionary {{'flag_name': True/False}}.")

        elif reward_type == "item":
            # Adds item name to inventory list
            if name and isinstance(name, str):
                 # Ensure inventory list exists and append item
                 inventory_list = p_data.setdefault(FS_INVENTORY, [])
                 if isinstance(inventory_list, list):
                     inventory_list.append(name)
                     if not silent:
                         announcement = f"You obtained: {name}."
                     logging.info(f"  Added item '{name}' to inventory.")
                 else:
                     logging.error(f"  Character {char_id_log} inventory field is not a list. Cannot add item '{name}'.")
            else:
                logging.warning(f"  Item reward specified but 'name' is missing or not a string: {name}")

        elif reward_type == "relationship":
             # Example: Store relationship points in FS_QUEST_FLAGS
             if target and isinstance(target, str):
                try:
                    rel_change = int(change)
                    if rel_change != 0:
                        flag_name = f"relationship_{target.replace(' ','_').lower()}" # Create a unique, clean flag name
                        quest_flags = p_data.setdefault(FS_QUEST_FLAGS, {})
                        current_value = quest_flags.get(flag_name, 0) # Default to 0
                        if not isinstance(current_value, (int, float)):
                            logging.warning(f"  Relationship flag '{flag_name}' has non-numeric value ({type(current_value)}). Resetting to 0 before applying change.")
                            current_value = 0
                        new_value = current_value + rel_change
                        quest_flags[flag_name] = new_value
                        if not silent:
                            announcement = details if details else f"Your relationship with {target} changed ({rel_change:+})."
                        logging.info(f"  Applied relationship change for '{target}' by {rel_change}. New value: {new_value} (Flag: {flag_name})")
                except (ValueError, TypeError):
                    logging.warning(f"  Invalid 'change' value for relationship reward: {change}")
             else:
                logging.warning(f"  Relationship reward specified but 'target' is missing or not a string: {target}")

        else:
            logging.warning(f"Unknown or invalid reward type '{reward_type}'")

    except Exception as e:
        logging.error(f"Error applying reward {reward_data} for char {char_id_log}: {e}", exc_info=True)
        announcement = "An error occurred while processing a reward." # Generic error for user

    return announcement


# ==============================================================================
# Flask Routes
# ==============================================================================

# --- Auth Routes ---
@app.route('/login', methods=['GET','POST'])
def login():
    # Redirect if user is already logged in
    if SESSION_USER_ID in session:
        return redirect(url_for('profile'))

    # Handle POST request (form submission)
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # Basic validation
        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template('login.html')
        try:
            # --- IMPORTANT SECURITY WARNING ---
            # The following code block is for DEVELOPMENT and TESTING ONLY.
            # It finds a user by email but DOES NOT VERIFY THE PASSWORD.
            # For a production application, this MUST be replaced with a secure
            # client-side authentication flow that sends a verified ID token
            # to the backend, as demonstrated in the previous version of this function.
            user = auth.get_user_by_email(email, app=firebase_app)
            logging.warning(f"INSECURE LOGIN: Bypassing password verification for user {email} ({user.uid}) for development purposes.")

            # Store user info in session
            session[SESSION_USER_ID] = user.uid
            session[SESSION_USER_EMAIL] = user.email
            session.permanent = True # Make session persistent

            flash(f"Welcome back, {user.email}!", "success")
            next_url = request.args.get('next')
            return redirect(next_url or url_for('profile'))
        except auth.UserNotFoundError:
            flash("Login failed: The email address was not found.", "error")
            logging.warning(f"Login attempt failed for non-existent user: {email}")
        except Exception as e:
            # This will catch other Firebase-related errors during user lookup
            flash("An unexpected error occurred during login. Please try again.", "error")
            logging.error(f"An unexpected error occurred during login for {email}: {e}", exc_info=True)

    # Handle GET request (display login page)
    return render_template('login.html')


# --- <<< REVISED >>> Auth Routes (Signup - Adds has_seen_intro) ---
@app.route('/signup', methods=['GET','POST'])
def signup():
    # Redirect if user is already logged in
    if SESSION_USER_ID in session:
        return redirect(url_for('profile'))

    # Handle POST request (form submission)
    if request.method=='POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # Basic validation
        if not email or not password or len(password) < 6:
            flash("Please provide a valid email and a password (at least 6 characters).", "error")
            return render_template('signup.html')
        try:
            # Create user in Firebase Authentication
            user = auth.create_user(email=email, password=password, app=firebase_app)
            logging.info(f"New Firebase Auth user created: {user.uid} ({email})")

            # --- Create corresponding profile in Firestore ---
            try:
                profile_data = {
                    'email': email, # Store email for reference
                    'player_level': 1, # Initial player level
                    'total_player_xp': 0, # Initial player XP
                    'created_at': firestore.SERVER_TIMESTAMP, # Record creation time
                    'has_premium': False, # Default to non-premium
                    'vocab_settings': {'use_default_awl': True}, # Default vocab setting
                    FS_PLAYER_HAS_SEEN_INTRO: False  # <<< REVISED: Set intro flag to False >>>
                }
                db.collection('player_profiles').document(user.uid).set(profile_data)
                logging.info(f"Firestore player profile created for {user.uid} (with {FS_PLAYER_HAS_SEEN_INTRO}=False)")
                flash(f"Account created successfully! Please log in.", "success")
                return redirect(url_for('login'))
            except Exception as db_err:
                # Log error but allow user to proceed to login
                logging.error(f"Failed to create Firestore profile for new user {user.uid}: {db_err}", exc_info=True)
                flash("Account created, but profile initialization failed. Please contact support if issues persist.", "warning")
                return redirect(url_for('login'))

        except auth.EmailAlreadyExistsError:
            flash("Signup failed: This email address is already registered.", "error")
        except Exception as e:
            flash("An unexpected error occurred during signup.", "error")
            logging.error(f"Signup Error for {email}: {e}", exc_info=True)

    # Handle GET request (display signup page)
    return render_template('signup.html')


@app.route('/logout')
@login_required # Ensure user must be logged in to log out
def logout():
    user_email = session.get(SESSION_USER_EMAIL,'Unknown User')
    user_id = session.get(SESSION_USER_ID)
    logging.info(f"Logging out user {user_email} ({user_id})")
    # Clear all relevant session keys
    keys_to_clear = [
        SESSION_USER_ID, SESSION_USER_EMAIL, SESSION_CHARACTER_ID,
        SESSION_CONVERSATION, SESSION_LOCATION, SESSION_LAST_AI_OUTPUT,
        SESSION_CHAPTER_INPUTS, SESSION_EOC_STATE, SESSION_EOC_QUESTIONS,
        SESSION_EOC_SUMMARY, SESSION_EOC_PROMPTED, SESSION_NEW_CHAR_DETAILS,
        SESSION_AI_RECOMMENDATIONS, SESSION_SIDE_QUEST_ACTIVE,
        SESSION_SIDE_QUEST_DESC, SESSION_SIDE_QUEST_TURNS
    ]
    for key in keys_to_clear:
        session.pop(key, None) # Use pop with default None to avoid errors if key missing
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('login'))


# --- Profile Route ---
@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    user_id = session[SESSION_USER_ID]
    user_email = session.get(SESSION_USER_EMAIL, '?')
    characters = get_user_characters(user_id) # Fetch user's characters

    # --- POST Request Handling (Actions from profile page) ---
    if request.method == 'POST':
        action = request.form.get('action')

        # --- Load Character Action ---
        if action == 'load_char':
            char_id_to_load = request.form.get('char_id')
            if not char_id_to_load:
                flash("No character selected to load.", "warning")
                return redirect(url_for('profile'))

            logging.info(f"User {user_id} attempting to load character: {char_id_to_load}")
            p_data = load_character_data(user_id, char_id_to_load)

            if p_data: # Successfully loaded
                # Clear previous character's temporary session data
                keys_to_clear = [
                    SESSION_LAST_AI_OUTPUT, SESSION_EOC_STATE, SESSION_EOC_QUESTIONS,
                    SESSION_EOC_SUMMARY, SESSION_EOC_PROMPTED, SESSION_NEW_CHAR_DETAILS,
                    SESSION_AI_RECOMMENDATIONS, SESSION_SIDE_QUEST_ACTIVE,
                    SESSION_SIDE_QUEST_DESC, SESSION_SIDE_QUEST_TURNS
                ]
                for k in keys_to_clear:
                    session.pop(k, None)

                # Load new character data into session
                session[SESSION_CHARACTER_ID] = char_id_to_load
                session[SESSION_LOCATION] = p_data.get('current_location', STARTING_LOCATION)
                session[SESSION_CONVERSATION] = p_data.get(FS_CONVERSATION, []) # Load convo log
                session[SESSION_CHAPTER_INPUTS] = p_data.get(FS_CHAPTER_INPUTS, []) # Load chapter inputs
                session.modified = True

                flash(f"Character '{p_data.get('name','?')}' loaded successfully.", "success")
                return redirect(url_for('game_view'))
            else: # Load failed (error flashed in load_character_data)
                return redirect(url_for('profile'))

        # --- Custom Character Creation Initiation ---
        elif action == 'create_char':
            logging.info(f"User {user_id} initiating custom character creation.")
            # Clear any leftover creation data from session
            session.pop(SESSION_NEW_CHAR_DETAILS, None)
            session.pop(SESSION_AI_RECOMMENDATIONS, None)
            session.modified = True
            return redirect(url_for('character_creation_view'))

        # --- Load Pre-made Character Action ---
        elif action == 'load_premade':
            premade_id = request.form.get('premade_char_id')
            if not premade_id:
                flash("No pre-made character template selected.", "warning")
                return redirect(url_for('profile'))

            template = next((t for t in premade_character_templates if t.get('id') == premade_id), None)
            if not template:
                logging.error(f"User {user_id} selected invalid pre-made template ID: {premade_id}")
                flash("Invalid pre-made character selection.", "error")
                return redirect(url_for('profile'))

            logging.info(f"User {user_id} creating character from pre-made template: {premade_id} ('{template.get('name', '?')}')")

            # Create new character data structure
            new_char_id = f"{user_id}_{premade_id}_{uuid.uuid4().hex[:8]}"
            # Start with template data and add default fields
            new_char_data = {
                'id': new_char_id,
                'user_id': user_id,
                **template, # Unpack template data
                'current_location': STARTING_LOCATION,
                'learned_vocab': set(), # Initialize as set
                'report_summaries': [],
                'turn_count': 0,
                SESSION_EOC_PROMPTED: False,
                FS_CONVERSATION: [],
                FS_CHAPTER_INPUTS: [],
                FS_QUEST_FLAGS: {},
                FS_INVENTORY: []
            }

            # Ensure required fields are present after merging template
            if not all(k in new_char_data for k in ['race_name', 'class_name', 'philosophy_name']):
                logging.error(f"Pre-made template '{premade_id}' is missing required Race/Class/Philosophy name.")
                flash("Selected pre-made character template is incomplete. Please contact support.", "error")
                return redirect(url_for('profile'))

            # Calculate derived fields (abilities, aspects, fate points)
            race_abilities = set(RACE_DATA.get(new_char_data['race_name'], {}).get('abilities', []))
            class_ability = CLASS_DATA.get(new_char_data['class_name'], {}).get('ability')
            phil_ability = PHILOSOPHY_DATA.get(new_char_data['philosophy_name'], {}).get('ability')
            all_abilities = race_abilities
            if class_ability: all_abilities.add(class_ability)
            if phil_ability: all_abilities.add(phil_ability)
            new_char_data['abilities'] = sorted(list(all_abilities))

            class_focus = CLASS_DATA.get(new_char_data['class_name'], {}).get('focus')
            aspects = [class_focus] if class_focus else []
            if "Artistic Shell" in new_char_data['abilities']: aspects.append("Shell Design: Undefined") # Example aspect
            new_char_data['aspects'] = aspects

            race_mod = RACE_DATA.get(new_char_data['race_name'], {}).get('fate_point_mod', 0)
            new_char_data['fate_points'] = BASE_FATE_POINTS + race_mod

            # Assign starting quest from template or default
            start_q_id = template.get('starting_quest_id')
            start_s_id, start_s_desc, start_q_title = None, "Begin your journey.", "Starting Quest"
            if start_q_id:
                start_q_data = get_quest(start_q_id)
                if start_q_data:
                    start_q_title = start_q_data.get('title', 'Starting Quest')
                    start_s_id = start_q_data.get('starting_step')
                    if start_s_id:
                        start_s_info = get_quest_step(start_q_id, start_s_id)
                        if start_s_info:
                             start_s_desc = start_s_info.get('description', 'Begin your journey.')
            new_char_data.update({
                'current_quest_id': start_q_id,
                'current_step_id': start_s_id,
                'current_quest_title': start_q_title,
                'current_step_description': start_s_desc
            })

            # Save the new character
            saved_id = save_character_data(user_id, new_char_data)
            if saved_id:
                # Load the newly saved character into session
                p_data = load_character_data(user_id, saved_id)
                if p_data:
                    # Clear any previous temp session data
                    keys_to_clear = [ SESSION_LAST_AI_OUTPUT, SESSION_EOC_STATE, SESSION_EOC_QUESTIONS, SESSION_EOC_SUMMARY, SESSION_EOC_PROMPTED, SESSION_NEW_CHAR_DETAILS, SESSION_AI_RECOMMENDATIONS, SESSION_SIDE_QUEST_ACTIVE, SESSION_SIDE_QUEST_DESC, SESSION_SIDE_QUEST_TURNS ]
                    for k in keys_to_clear: session.pop(k, None)
                    # Load essential data into session
                    session[SESSION_CHARACTER_ID] = saved_id
                    session[SESSION_LOCATION] = p_data.get('current_location', STARTING_LOCATION)
                    session[SESSION_CONVERSATION] = p_data.get(FS_CONVERSATION, [])
                    session[SESSION_CHAPTER_INPUTS] = p_data.get(FS_CHAPTER_INPUTS, [])
                    session.modified = True
                    flash(f"Pre-made character '{p_data.get('name','?')}' created and loaded!", "success")
                    return redirect(url_for('game_view'))
                else:
                    flash("Character created but failed to load. Please try loading from profile.", "error")
                    return redirect(url_for('profile'))
            else: # Save failed
                # Error should be flashed by save_character_data
                return redirect(url_for('profile'))

        # --- Save Vocabulary Color Settings Action ---
        elif action == 'save_settings':
            logging.info(f"User {user_id} attempting to save vocabulary color settings.")
            awl_color = request.form.get('awl_color_bg', '#FFE6EB').strip()
            ai_color = request.form.get('ai_color_bg', '#E1F0FF').strip()

            # Validate color format
            if not re.match(r'^#[0-9a-fA-F]{6}$', awl_color) or not re.match(r'^#[0-9a-fA-F]{6}$', ai_color):
                flash("Invalid color format submitted. Please use the color picker.", "error")
                return redirect(url_for('profile'))

            try:
                profile_ref = db.collection('player_profiles').document(user_id)
                # Use set with merge=True to update or add the vocab_settings field
                # This preserves other settings if they exist
                profile_ref.set({
                    'vocab_settings': {
                        'awl_color_bg': awl_color,
                        'ai_color_bg': ai_color
                        # Note: This currently OVERWRITES use_default_awl.
                        # If you add a toggle for that, fetch existing settings first.
                    }
                }, merge=True)
                logging.info(f"Saved vocab color settings for user {user_id}: AWL={awl_color}, AI={ai_color}")
                flash("Vocabulary color settings saved!", "success")
            except Exception as e:
                logging.error(f"Failed to save vocab color settings for user {user_id}: {e}", exc_info=True)
                flash("An error occurred while saving color settings.", "error")

            return redirect(url_for('profile')) # Redirect back to profile

        # --- Placeholder Action ---
        elif action == 'request_report':
            flash("Detailed reports feature is not yet available.", "info")
            return redirect(url_for('profile'))

        # --- Unknown Action ---
        else:
            flash(f"Unknown profile action requested: {action}", "warning")
            return redirect(url_for('profile'))

    # --- GET Request Handling (Display Profile Page) ---
    else: # request.method == 'GET'
        # Fetch profile data including vocab settings
        profile_data = {
            'email': user_email,
            'player_level': 1,
            'total_player_xp': 0,
            'has_premium': False,
            'vocab_settings': { # Initialize with ALL defaults
                'use_default_awl': True,
                'awl_color_bg': '#FFE6EB', # Default pinkish
                'ai_color_bg': '#E1F0FF'   # Default blueish
             }
        }
        if db:
            try:
                profile_doc_ref = db.collection('player_profiles').document(user_id)
                # Fetch all relevant fields
                p_doc = profile_doc_ref.get(['player_level', 'total_player_xp', 'has_premium', 'email', 'vocab_settings'])
                if p_doc.exists:
                    fs_data = p_doc.to_dict()
                    # Update basic fields safely
                    profile_data['player_level'] = fs_data.get('player_level', profile_data['player_level'])
                    profile_data['total_player_xp'] = fs_data.get('total_player_xp', profile_data['total_player_xp'])
                    profile_data['has_premium'] = fs_data.get('has_premium', profile_data['has_premium'])
                    profile_data['email'] = fs_data.get('email', profile_data['email'])

                    # Carefully update vocab_settings, preserving existing keys and adding defaults
                    saved_settings = fs_data.get('vocab_settings', {})
                    if isinstance(saved_settings, dict): # Check if it's a dict
                        profile_data['vocab_settings']['use_default_awl'] = saved_settings.get('use_default_awl', profile_data['vocab_settings']['use_default_awl'])
                        profile_data['vocab_settings']['awl_color_bg'] = saved_settings.get('awl_color_bg', profile_data['vocab_settings']['awl_color_bg'])
                        profile_data['vocab_settings']['ai_color_bg'] = saved_settings.get('ai_color_bg', profile_data['vocab_settings']['ai_color_bg'])
                    else:
                        logging.warning(f"Vocab settings for user {user_id} in Firestore is not a dict ({type(saved_settings)}). Using defaults.")
                else:
                    logging.warning(f"Player profile document not found for logged-in user: {user_id}")
                    flash("Could not load your player profile details.", "warning")
            except Exception as e:
                logging.error(f"Failed to fetch player profile for user {user_id}: {e}", exc_info=True)
                flash("An error occurred loading your profile data.", "error")

        # Render the profile template
        return render_template(
            'profile.html',
            profile=profile_data, # Pass the full profile data, including vocab_settings
            characters=characters,
            premade_characters=premade_character_templates,
            has_premium=profile_data.get('has_premium', False)
        )

# --- Character Creation Route ---
@app.route('/create_character', methods=['GET','POST'])
@login_required
def character_creation_view():
    user_id = session[SESSION_USER_ID]
    logging.debug(f"Entering character_creation_view. Method: {request.method}")

    # --- POST Request Handling ---
    if request.method == 'POST':
        creation_stage = request.form.get('creation_stage')
        logging.debug(f"POST request received. creation_stage = {creation_stage}")

        # --- Stage 1: Submit Details for AI Review ---
        if creation_stage == 'submit_details':
            logging.info(f"User {user_id} submitting custom character details for AI review.")
            # Retrieve all fields from the form
            char_details = {
                k: request.form.get(k, '').strip()
                for k in ['name', 'race_name', 'class_name', 'philosophy_name', 'boon', 'backstory', 'starting_quest']
            }

            # Validate required fields
            required_fields = ['name', 'race_name', 'class_name', 'philosophy_name', 'boon', 'backstory', 'starting_quest']
            missing = [field for field in required_fields if not char_details.get(field)]
            if missing:
                flash(f"Please fill out all character detail fields ({', '.join(missing)} missing).", "warning")
                logging.debug("Validation failed, re-rendering template with errors.")
                # Render as if initial stage (reviewing=False, no recommendations)
                return render_template(
                    'character_creation.html',
                    race_options=list(RACE_DATA.keys()),
                    class_options=list(CLASS_DATA.keys()),
                    philosophy_options=list(PHILOSOPHY_DATA.keys()),
                    char_details=char_details, # Pass back entered details
                    ai_recommendations=None,
                    reviewing=False # Ensure fields are editable
                )

            # Store details and get AI review
            session[SESSION_NEW_CHAR_DETAILS] = char_details
            session.modified = True
            logging.debug(f"Stored char_details in session: {session.get(SESSION_NEW_CHAR_DETAILS)}")
            review_context = {"character_sheet_data": char_details}
            ai_response = get_ai_response("REVIEW_CHARACTER_SHEET", review_context)

            recommendations = []
            if isinstance(ai_response, dict) and 'error' not in ai_response:
                recommendations = ai_response.get('recommendations', [])
                logging.info(f"AI review returned {len(recommendations)} recommendations.")
                flash("AI has reviewed your character concept. See suggestions below.", "info")
            else:
                error_reason = ai_response.get('reason', 'Unknown error') if isinstance(ai_response, dict) else 'AI communication failure'
                logging.error(f"AI character review failed. Reason: {error_reason}")
                flash(f"AI couldn't review your concept ({error_reason}). You can finalize, edit, or start over.", "error")
                recommendations = None # Indicate review failure

            session[SESSION_AI_RECOMMENDATIONS] = recommendations
            session.modified = True
            logging.debug(f"Stored ai_recommendations in session: {session.get(SESSION_AI_RECOMMENDATIONS)}")

            # Render page in review mode (reviewing=True)
            logging.debug("Rendering template for review stage.")
            return render_template(
                'character_creation.html',
                race_options=list(RACE_DATA.keys()),
                class_options=list(CLASS_DATA.keys()),
                philosophy_options=list(PHILOSOPHY_DATA.keys()),
                char_details=char_details,
                ai_recommendations=recommendations,
                reviewing=True # Now in review mode
            )

        # --- Stage 0: Handle Restart Request ---
        elif creation_stage == 'restart':
            logging.info(f"User {user_id} restarting character creation.")
            logging.debug("Clearing session data for restart.")
            session.pop(SESSION_NEW_CHAR_DETAILS, None)
            session.pop(SESSION_AI_RECOMMENDATIONS, None)
            session.modified = True
            logging.debug(f"Session after clearing: details={session.get(SESSION_NEW_CHAR_DETAILS)}, recs={session.get(SESSION_AI_RECOMMENDATIONS)}")
            return redirect(url_for('character_creation_view'))

        # --- Stage 1.5: Handle Edit Request ---
        elif creation_stage == 'edit':
            logging.info(f"User {user_id} editing character after review.")
            # Keep char_details in session, but clear recommendations
            session.pop(SESSION_AI_RECOMMENDATIONS, None)
            session.modified = True
            logging.debug(f"Session after clearing recs for edit: details={session.get(SESSION_NEW_CHAR_DETAILS)}, recs={session.get(SESSION_AI_RECOMMENDATIONS)}")
            # Redirect back to the GET handler, which will now render editable fields
            return redirect(url_for('character_creation_view'))

        # --- Stage 2: Finalize Character Creation ---
        elif creation_stage == 'finalize':
            logging.info(f"User {user_id} attempting to finalize custom character.")
            final_details = session.get(SESSION_NEW_CHAR_DETAILS)
            logging.debug(f"Retrieved final_details from session: {final_details}")
            if not final_details:
                flash("Character details were lost. Please start over.", "error")
                logging.error(f"Finalization error: Session data missing.")
                session.pop(SESSION_AI_RECOMMENDATIONS, None)
                session.modified = True
                return redirect(url_for('character_creation_view'))

            # --- Create new character data structure ---
            new_char_id = f"{user_id}_custom_{uuid.uuid4().hex[:8]}"
            final_char_data = {
                'id': new_char_id,
                'user_id': user_id,
                'current_location': STARTING_LOCATION,
                'learned_vocab': set(), # Initialize as set
                'report_summaries': [],
                'turn_count': 0,
                SESSION_EOC_PROMPTED: False,
                FS_CONVERSATION: [],
                FS_CHAPTER_INPUTS: [],
                FS_QUEST_FLAGS: {},
                FS_INVENTORY: []
            }
            final_char_data.update(final_details) # Add the form details

            # --- Validate required fields ---
            race_name = final_char_data.get('race_name')
            class_name = final_char_data.get('class_name')
            philosophy_name = final_char_data.get('philosophy_name')
            start_goal = final_char_data.get('starting_quest', 'Find purpose') # Use form input

            if not race_name or not class_name or not philosophy_name:
                 flash(f"Missing required character detail (Race/Class/Philosophy). Please start over.", "error")
                 logging.error(f"Missing essential name(s) finalizing character for {user_id}: R={race_name}, C={class_name}, P={philosophy_name}")
                 session.pop(SESSION_NEW_CHAR_DETAILS, None)
                 session.pop(SESSION_AI_RECOMMENDATIONS, None)
                 session.modified = True
                 return redirect(url_for('character_creation_view'))

            # --- Calculate derived fields ---
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
                if "Artistic Shell" in final_char_data['abilities']: aspects.append("Shell Design: Undefined") # Example
                final_char_data['aspects'] = aspects

                race_mod = RACE_DATA.get(race_name, {}).get('fate_point_mod', 0)
                final_char_data['fate_points'] = BASE_FATE_POINTS + race_mod

                # Create simple starting quest based on user input
                final_char_data['current_quest_id'] = f"Q_CH1_{new_char_id[-4:]}" # Unique ID
                final_char_data['current_quest_title'] = f"Chapter 1: {start_goal}"[:80] # Title from goal
                final_char_data['current_step_id'] = "STEP_01"
                final_char_data['current_step_description'] = start_goal # Step desc from goal

            except KeyError as e:
                 flash(f"Internal data error finding details for {e}. Please check selections.", "error")
                 logging.error(f"KeyError finalizing character for {user_id}: {e}", exc_info=True)
                 session.pop(SESSION_NEW_CHAR_DETAILS, None)
                 session.pop(SESSION_AI_RECOMMENDATIONS, None)
                 session.modified = True
                 return redirect(url_for('character_creation_view'))
            except Exception as e:
                 flash(f"An error occurred calculating character stats: {e}. Please start over.", "error")
                 logging.error(f"Error calculating derived fields for {user_id}: {e}", exc_info=True)
                 session.pop(SESSION_NEW_CHAR_DETAILS, None)
                 session.pop(SESSION_AI_RECOMMENDATIONS, None)
                 session.modified = True
                 return redirect(url_for('character_creation_view'))

            # --- Save the new character ---
            logging.debug("Attempting to save finalized character data.")
            saved_id = save_character_data(user_id, final_char_data)
            if saved_id:
                logging.debug(f"Character saved successfully with ID: {saved_id}. Clearing session.")
                # Clear creation data from session
                session.pop(SESSION_NEW_CHAR_DETAILS, None)
                session.pop(SESSION_AI_RECOMMENDATIONS, None)
                session.modified = True
                flash(f"Custom character '{final_char_data.get('name', 'Unknown')}' created successfully!", "success")
                return redirect(url_for('profile')) # Go back to profile after creation
            else:
                flash("Failed to save the finalized character. Please try again.", "error")
                logging.error("save_character_data returned None during finalization.")
                # Stay on creation page with current details
                return redirect(url_for('character_creation_view'))

        # --- Invalid Stage ---
        else:
            flash("Invalid character creation request.", "error")
            logging.warning(f"Invalid creation_stage '{creation_stage}' received.")
            session.pop(SESSION_NEW_CHAR_DETAILS, None)
            session.pop(SESSION_AI_RECOMMENDATIONS, None)
            session.modified = True
            return redirect(url_for('character_creation_view'))

    # --- GET Request Handling ---
    else: # request.method == 'GET'
        logging.debug("GET request: Checking session for existing data.")
        char_details_from_session = session.get(SESSION_NEW_CHAR_DETAILS)
        recommendations_from_session = session.get(SESSION_AI_RECOMMENDATIONS)
        logging.debug(f"  Session values: details={char_details_from_session}, recs={recommendations_from_session}")

        # Determine if we are in the 'review' stage (locked fields)
        is_reviewing_stage = bool(char_details_from_session and recommendations_from_session is not None)

        if char_details_from_session:
            # We have details, could be review stage or edit stage
            logging.info(f"Rendering creation page. Reviewing={is_reviewing_stage}")
            return render_template(
                'character_creation.html',
                race_options=list(RACE_DATA.keys()),
                class_options=list(CLASS_DATA.keys()),
                philosophy_options=list(PHILOSOPHY_DATA.keys()),
                char_details=char_details_from_session,
                ai_recommendations=recommendations_from_session, # Pass recommendations if they exist
                reviewing=is_reviewing_stage # Pass the flag to template
            )
        else:
            # No details in session, must be the initial empty form
            logging.info(f"Displaying initial character creation form.")
            # Ensure session is clear just in case
            session.pop(SESSION_NEW_CHAR_DETAILS, None)
            session.pop(SESSION_AI_RECOMMENDATIONS, None)
            session.modified = True
            return render_template(
                'character_creation.html',
                race_options=list(RACE_DATA.keys()),
                class_options=list(CLASS_DATA.keys()),
                philosophy_options=list(PHILOSOPHY_DATA.keys()),
                char_details={}, # Empty initial details
                ai_recommendations=None, # No recommendations
                reviewing=False # Not reviewing
            )

# --- AI Vocab Generation Route ---
@app.route('/generate_vocab_list', methods=['POST'])
@login_required
def generate_vocab_list():
    user_id = session[SESSION_USER_ID]
    # --- Premium Access Check ---
    if not check_premium_access(user_id):
        logging.warning(f"Non-premium user {user_id} attempted AI vocabulary generation.")
        return jsonify({"success": False, "error": "AI vocabulary generation is a premium feature."}), 403

    target_word = request.form.get('target_word','').strip()
    if not target_word:
        return jsonify({"success": False, "error": "Please provide a target word."}), 400

    logging.info(f"User {user_id} requesting AI vocabulary list generation for target word: '{target_word}'")
    ai_context = {"target_word": target_word}
    ai_response = get_ai_response("GENERATE_CONTEXTUAL_VOCAB", ai_context)

    # --- Process AI Response ---
    if isinstance(ai_response, dict) and 'error' not in ai_response:
        target_info = ai_response.get('target_word_info')
        related_words = ai_response.get('related_words')
        # --- Validate response structure ---
        is_valid_format = (
            target_info and isinstance(target_info, dict) and target_info.get('word') and target_info.get('definition') and
            related_words and isinstance(related_words, list) and len(related_words) == 25 and
            all(isinstance(w, dict) and w.get('word') and w.get('definition') for w in related_words)
        )
        if not is_valid_format:
            logging.error(f"AI vocabulary generation for '{target_word}' returned incomplete or invalid data structure for user {user_id}. Response: {ai_response}")
            return jsonify({"success": False, "error": "AI failed to generate the vocabulary list in the expected format."}), 500

        # --- Save the generated list to Firestore ---
        word_list_data = [{"word": target_info['word'],"definition": target_info['definition']}] + related_words
        list_id = f"ai_{target_word.lower().replace(' ','_')}_{int(time.time())}"
        list_name = f"'{target_word}' Context" # Create a descriptive name
        list_color = DEFAULT_VOCAB_LIST_COLOR # Use default color
        firestore_data = {
            "name": list_name, "color": list_color, "words": word_list_data,
            "is_ai_generated": True, "created_at": firestore.SERVER_TIMESTAMP, "is_active": True # Activate by default
        }
        try:
            profile_ref = db.collection('player_profiles').document(user_id)
            vocab_lists_ref = profile_ref.collection('custom_vocab_lists')
            vocab_lists_ref.document(list_id).set(firestore_data)
            logging.info(f"Successfully saved AI generated vocabulary list {list_id} for user {user_id}")
            flash(f"AI vocabulary list based on '{target_word}' created successfully!", "success")
            return jsonify({ "success": True, "message": f"Vocabulary list for '{target_word}' created!", "list_id": list_id, "list_name": list_name }), 200
        except Exception as e:
            logging.error(f"Failed to save generated AI vocabulary list {list_id} for user {user_id}: {e}", exc_info=True)
            return jsonify({"success": False, "error": "Failed to save the generated vocabulary list to your profile."}), 500
    else:
        # Handle AI error during generation
        error_reason = ai_response.get('reason','Unknown AI error') if isinstance(ai_response, dict) else 'AI communication failure'
        logging.error(f"AI vocabulary generation failed for user {user_id}, target word '{target_word}'. Reason: {error_reason}")
        return jsonify({"success": False, "error": f"AI Storyteller could not generate the list: {error_reason}"}), 500


# --- Vocab List Management Routes ---
@app.route('/toggle_vocab_list/<list_id>', methods=['POST'])
@login_required
def toggle_vocab_list(list_id):
    user_id = session[SESSION_USER_ID]
    if not list_id:
        return jsonify({"success": False, "error": "List ID missing."}), 400
    try:
        list_ref = db.collection('player_profiles').document(user_id).collection('custom_vocab_lists').document(list_id)
        list_doc = list_ref.get(['is_active']) # Only fetch the field we need
        if not list_doc.exists:
            logging.warning(f"Attempt to toggle non-existent vocab list {list_id} for user {user_id}.")
            return jsonify({"success": False, "error": "Vocabulary list not found."}), 404
        current_status = list_doc.to_dict().get('is_active', False)
        new_status = not current_status
        list_ref.update({'is_active': new_status})
        logging.info(f"Toggled vocab list {list_id} for user {user_id} to {'active' if new_status else 'inactive'}.")
        flash(f"Vocabulary list status updated.", "success") # User feedback
        return jsonify({"success": True, "new_status": new_status}), 200
    except Exception as e:
        logging.error(f"Error toggling vocabulary list {list_id} for user {user_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Failed to update vocabulary list status."}), 500

@app.route('/delete_vocab_list/<list_id>', methods=['POST'])
@login_required
def delete_vocab_list(list_id):
    user_id = session[SESSION_USER_ID]
    if not list_id:
        return jsonify({"success": False, "error": "List ID missing."}), 400
    try:
        list_ref = db.collection('player_profiles').document(user_id).collection('custom_vocab_lists').document(list_id)
        list_doc = list_ref.get(['name']) # Get name for logging/feedback
        if not list_doc.exists:
            logging.warning(f"Attempt to delete non-existent vocab list {list_id} for user {user_id}.")
            return jsonify({"success": False, "error": "Vocabulary list not found."}), 404
        list_name = list_doc.to_dict().get('name', 'Unknown List')
        list_ref.delete()
        logging.info(f"Deleted vocabulary list {list_id} ('{list_name}') for user {user_id}.")
        flash(f"Vocabulary list '{list_name}' deleted.", "success") # User feedback
        return jsonify({"success": True, "message": f"List '{list_name}' deleted."}), 200
    except Exception as e:
        logging.error(f"Error deleting vocabulary list {list_id} for user {user_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Failed to delete vocabulary list."}), 500


# --- <<< REVISED >>> Main Game View Route ---
@app.route('/game', methods=['GET', 'POST'])
@login_required
def game_view():
    user_id = session[SESSION_USER_ID]
    char_id = session.get(SESSION_CHARACTER_ID)

    if not char_id:
        flash("No character is currently loaded. Please select one from your profile.", "warning")
        return redirect(url_for('profile'))

    # Load character data fresh on each interaction for consistency
    p_data = load_character_data(user_id, char_id)
    if not p_data: # Handle case where character fails to load
        session.pop(SESSION_CHARACTER_ID, None) # Clear invalid character ID from session
        session.modified = True
        # load_character_data should have flashed an error
        return redirect(url_for('profile'))

    # --- Sync Session State with Loaded Character Data ---
    # Ensure session reflects persistent data, especially logs
    session[SESSION_CONVERSATION] = p_data.get(FS_CONVERSATION, [])
    session[SESSION_CHAPTER_INPUTS] = p_data.get(FS_CHAPTER_INPUTS, [])
    session[SESSION_LOCATION] = p_data.get('current_location', STARTING_LOCATION)
    # Ensure temporary session states are also loaded or defaulted
    session[SESSION_EOC_PROMPTED] = p_data.get(SESSION_EOC_PROMPTED, False)
    session[SESSION_SIDE_QUEST_ACTIVE] = session.get(SESSION_SIDE_QUEST_ACTIVE, False)
    session[SESSION_SIDE_QUEST_DESC] = session.get(SESSION_SIDE_QUEST_DESC, None)
    session[SESSION_SIDE_QUEST_TURNS] = session.get(SESSION_SIDE_QUEST_TURNS, 0)
    session.modified = True # Mark session as modified after sync
    curr_loc = session[SESSION_LOCATION] # Use local variable for current location

    # --- POST Request Handling (Player Action) ---
    if request.method == 'POST':
        p_input = request.form.get('player_input', '').strip()
        conv_log = session.get(SESSION_CONVERSATION, [])
        chapter_inputs_log = session.get(SESSION_CHAPTER_INPUTS, [])
        eoc_prompted = session.get(SESSION_EOC_PROMPTED, False)
        side_quest_active = session.get(SESSION_SIDE_QUEST_ACTIVE, False)

        # --- Input Validation ---
        if not p_input:
            return redirect(url_for('game_view')) # Ignore empty input silently
        if len(p_input) > MAX_INPUT_LENGTH:
            conv_log.append({"speaker":"System", "text":f"Input too long (Max {MAX_INPUT_LENGTH}). Be concise."})
            session[SESSION_CONVERSATION] = conv_log
            session.modified = True
            # Update persistent log too
            p_data[FS_CONVERSATION] = conv_log[-MAX_CONVO_LINES:]
            save_character_data(user_id, p_data) # Save after adding system message
            return redirect(url_for('game_view'))

        # --- Handle EOC Prompt Response ---
        if eoc_prompted:
            clean_input = p_input.strip().lower()
            p_data[SESSION_EOC_PROMPTED] = False # Reset flag regardless of answer
            session[SESSION_EOC_PROMPTED] = False # Reset session flag too
            session.modified = True

            if clean_input == 'yes':
                logging.info(f"Player {user_id} accepted AI-suggested EOC for char {char_id}.")
                p_data['turn_count'] = 0 # Reset turn count for EOC
                session[SESSION_EOC_STATE] = 'START' # Set session state to start EOC
                save_character_data(user_id, p_data) # Save reset flag/turn count
                return redirect(url_for('end_of_chapter'))
            elif clean_input == 'no':
                logging.info(f"Player {user_id} declined AI-suggested EOC for char {char_id}.")
                conv_log.append({"speaker": "System", "text": "Okay, continuing the adventure!"})
                session[SESSION_CONVERSATION] = conv_log # Update session log
                p_data[FS_CONVERSATION] = conv_log[-MAX_CONVO_LINES:] # Update persistent log
                save_character_data(user_id, p_data) # Save reset flag & message
                return redirect(url_for('game_view'))
            else: # Ambiguous response
                conv_log.append({"speaker": "Player", "text": p_input}) # Log their input
                conv_log.append({"speaker": "System", "text": "Please respond with 'yes' or 'no'."})
                session[SESSION_CONVERSATION] = conv_log
                p_data[FS_CONVERSATION] = conv_log[-MAX_CONVO_LINES:]
                p_data[SESSION_EOC_PROMPTED] = True # Re-prompt by setting flag back
                session[SESSION_EOC_PROMPTED] = True # Re-prompt by setting flag back
                save_character_data(user_id, p_data)
                return redirect(url_for('game_view'))

        # --- Handle Player Side Quest Input ---
        if side_quest_active:
            side_quest_desc = session.get(SESSION_SIDE_QUEST_DESC)
            side_quest_turns = session.get(SESSION_SIDE_QUEST_TURNS, 0)
            conv_log.append({"speaker":"Player", "text": p_input})

            if side_quest_desc is None: # Player defining task
                logging.info(f"Player {user_id} proposing side quest: {p_input}")
                ai_context_sideq = {'player_sidequest_idea': p_input}
                ai_context_sideq.update({ k: p_data.get(k) for k in ['name', 'race_name', 'class_name', 'philosophy_name', 'current_location']})
                ai_resp_json = get_ai_response("PROCESS_PLAYER_SIDEQUEST_IDEA", ai_context_sideq)

                if isinstance(ai_resp_json, dict) and 'side_quest_objective' in ai_resp_json:
                    new_desc = ai_resp_json['side_quest_objective']
                    session[SESSION_SIDE_QUEST_DESC] = new_desc
                    session[SESSION_SIDE_QUEST_TURNS] = 0 # Start turn count
                    conv_log.append({"speaker":"System", "text": f"Task: {new_desc}"})
                    logging.info(f"Player {user_id} starting side quest: {new_desc}")
                else: # Failed processing
                    conv_log.append({"speaker":"System", "text": "Let's try simpler. What would you like to observe or interact with briefly?"}) # Ask again
                    logging.warning(f"Failed to process side quest idea for {user_id}. Response: {ai_resp_json}")

            else: # Player performing task
                session[SESSION_SIDE_QUEST_TURNS] = side_quest_turns + 1
                logging.info(f"Player {user_id} side quest '{side_quest_desc}' (Turn {side_quest_turns + 1})")
                # Use INTERPRET_COMMAND for side quest actions
                ai_context_action = {
                    'player_name': p_data.get('name','?'), 'player_race': p_data.get('race_name','?'),
                    'player_class': p_data.get('class_name','?'), 'player_philosophy': p_data.get('philosophy_name','?'),
                    'player_abilities': p_data.get('abilities',[]), 'player_fate_points': p_data.get('fate_points', 0),
                    'location': curr_loc, 'location_data': world_map.get(curr_loc,{}),
                    'thetopia_location_lore': thetopia_lore.get('locations',{}).get(curr_loc,{}),
                    'command': p_input,
                    'current_quest_title': '(Side Quest)', 'current_step_description': side_quest_desc
                }
                ai_resp = get_ai_response("INTERPRET_COMMAND", ai_context_action)
                if ai_resp:
                    conv_log.append({"speaker":"AI", "text": ai_resp})

                # Check if side quest should end (e.g., after 3 turns)
                # Consider adding an AI check EVALUATE_SIDEQUEST_COMPLETION later if needed
                side_quest_done = (session[SESSION_SIDE_QUEST_TURNS] >= 3)
                if side_quest_done:
                     conv_log.append({"speaker":"System", "text": "Finished with that detour. Now, let's reflect on the main chapter..."})
                     logging.info(f"Player {user_id} completed side quest: {side_quest_desc}")
                     # Clear side quest state from session
                     session[SESSION_SIDE_QUEST_ACTIVE] = False
                     session.pop(SESSION_SIDE_QUEST_DESC, None)
                     session.pop(SESSION_SIDE_QUEST_TURNS, None)
                     # Start EOC flow
                     session[SESSION_EOC_STATE] = 'START'
                     p_data['turn_count'] = 0 # Reset main turn count for EOC
                     p_data[FS_CONVERSATION] = conv_log[-MAX_CONVO_LINES:] # Save log
                     save_character_data(user_id, p_data)
                     session.modified = True
                     return redirect(url_for('end_of_chapter')) # Go straight to EOC

            # Save and redirect if side quest not finished
            session[SESSION_CONVERSATION] = conv_log[-MAX_CONVO_LINES:]
            p_data[FS_CONVERSATION] = session[SESSION_CONVERSATION]
            save_character_data(user_id, p_data)
            session.modified = True
            return redirect(url_for('game_view'))

        # --- Process Normal Game Command ---
        # Log player input
        conv_log.append({"speaker":"Player", "text": p_input})
        chapter_inputs_log.append(p_input)
        session[SESSION_CHAPTER_INPUTS] = chapter_inputs_log # Update session log
        p_data['turn_count'] = p_data.get('turn_count', 0) + 1
        turn_num = p_data['turn_count']

        # --- Vocabulary XP Calculation ---
        try:
            # Ensure learned_vocab exists and is a set
            if 'learned_vocab' not in p_data or not isinstance(p_data['learned_vocab'], set):
                p_data['learned_vocab'] = set()
            # Calculate XP and update learned words
            player_xp_gain, new_awl_words = calculate_xp(p_input, p_data['learned_vocab'])
            if new_awl_words:
                p_data['learned_vocab'].update(new_awl_words)
                logging.info(f"User {user_id} learned new AWL words: {new_awl_words}")
            # Update player profile XP in Firestore if gain > 0
            if player_xp_gain > 0:
                 logging.info(f"User {user_id} gained {player_xp_gain} Player XP this turn.")
                 try:
                     db.collection('player_profiles').document(user_id).update({
                         'total_player_xp': firestore.Increment(player_xp_gain)
                     })
                 except Exception as xp_err:
                     logging.error(f"Failed to update Player XP in Firestore for {user_id}: {xp_err}")
        except Exception as vocab_err:
            logging.error(f"Error during vocabulary XP calculation: {vocab_err}", exc_info=True)

        # --- Build AI Context ---
        # Combine relevant player, location, and quest data
        ai_context = {
            'player_name': p_data.get('name','?'),
            'player_race': p_data.get('race_name','?'),
            'player_class': p_data.get('class_name','?'),
            'player_philosophy': p_data.get('philosophy_name','?'),
            'player_abilities': p_data.get('abilities',[]),
            'player_aspects': p_data.get('aspects',[]), # Include aspects
            'player_fate_points': p_data.get('fate_points', 0),
            'location': curr_loc,
            'location_data': world_map.get(curr_loc,{}), # Exits, etc.
            'thetopia_location_lore': thetopia_lore.get('locations',{}).get(curr_loc,{}), # Desc, NPCs
            'thetopia_general_lore': thetopia_lore.get('setting',{}), # World context
            'command': p_input,
            'current_quest_id': p_data.get('current_quest_id'),
            'current_step_id': p_data.get('current_step_id'),
            'current_quest_title': p_data.get('current_quest_title',''),
            'current_step_description': p_data.get('current_step_description','')
        }

        # --- Command Processing ---
        parts = p_input.lower().split(maxsplit=1)
        verb = parts[0] if parts else ""
        target = parts[1] if len(parts) > 1 else ""
        ai_resp = ""
        needs_desc_after_move = False
        chapter_ended = False
        step_completed_this_turn = False

        # Movement
        if verb in ["go","move","n","s","e","w","u","d","north","south","east","west","up","down"]:
            direction = target if verb in ["go","move"] else verb
            if not direction:
                ai_resp = "Which direction would you like to go?"
            else:
                exits = world_map.get(curr_loc,{}).get("exits",{})
                # Normalize direction
                norm_d = direction.lower().split()[0] # Take first word
                d_map = {'n':'north','s':'south','e':'east','w':'west','u':'up','d':'down'}
                final_d = d_map.get(norm_d, norm_d) # Map abbreviations
                # Check if exit exists
                if final_d in exits:
                    new_loc = exits[final_d]
                    p_data['current_location'] = new_loc # Update character data
                    session[SESSION_LOCATION] = new_loc # Update session
                    curr_loc = new_loc # Update local variable for this request
                    ai_resp = f"You move {final_d}..." # Simple confirmation
                    needs_desc_after_move = True # Flag to get description later
                else:
                    # Invalid direction, ask AI to explain
                    ctx_move = ai_context.copy()
                    ctx_move["direction"] = final_d
                    ai_resp = get_ai_response("INVALID_DIRECTION", ctx_move)

        # Ability Use
        elif verb == "use":
            if not target:
                ai_resp = "Use what ability?"
            else:
                abil_input = target.lower()
                # Normalize ability name (handle case variations)
                norm_abil = ABILITY_NAME_MAP.get(abil_input) or \
                            next((v for k,v in ABILITY_NAME_MAP.items() if abil_input == k.lower()), None) or \
                            abil_input.capitalize() # Fallback to capitalized input
                # Check if player has the ability
                if norm_abil not in p_data.get('abilities', []):
                    reason = f"Your character does not have the ability '{norm_abil}'."
                    ctx_abil = ai_context.copy()
                    ctx_abil.update({"ability": norm_abil, "reason": reason})
                    ai_resp = get_ai_response("INVALID_ABILITY", ctx_abil)
                else:
                    # Valid ability, ask AI to process
                    ctx_abil = ai_context.copy()
                    ctx_abil.update({"ability": norm_abil})
                    ai_resp = get_ai_response("PROCESS_ABILITY_USE", ctx_abil)

        # Look
        elif verb in ["look","l", "examine"]:
            ai_resp = get_ai_response("GET_DESCRIPTION", ai_context)

        # Journal Shortcuts
        elif verb in ["sheet","char","status", "inventory", "inv"]:
            return redirect(url_for('journal_char_quest'))
        elif verb in ["journal","quest","log","vocab","words","report","reports"]:
            return redirect(url_for('journal_vocab_report'))

        # Default Interpretation (any other input)
        else:
            ai_resp = get_ai_response("INTERPRET_COMMAND", ai_context)

        # Log AI response if generated
        if ai_resp:
            conv_log.append({"speaker":"AI", "text": ai_resp})
            session[SESSION_LAST_AI_OUTPUT] = ai_resp # Store last output for potential AI check

        # --- Quest Step Completion Check ---
        q_id = p_data.get('current_quest_id')
        s_id = p_data.get('current_step_id')
        step_done = False
        if q_id and s_id: # Only check if on a quest step
            current_step_data = get_quest_step(q_id, s_id)
            if current_step_data:
                # Check simple state/inventory triggers first
                is_complete_without_ai, ai_check_criteria = check_step_completion(p_data, current_step_data)
                if is_complete_without_ai:
                    step_done = True
                    logging.info(f"Step {s_id} of quest {q_id} completed via state/inventory check.")
                elif ai_check_criteria:
                    # If simple checks fail but AI check is needed, call AI
                    logging.info(f"Performing AI Check for step {s_id}. Criteria: '{ai_check_criteria}'")
                    ai_eval_context = {
                        'step_description': current_step_data.get('description', ''),
                        'player_action': p_input,
                        'ai_outcome': ai_resp or "(No AI response this turn)", # Use last AI response
                        'ai_check_criteria': f"if the action fulfilled: '{ai_check_criteria}'", # Add context for AI
                        # Pass basic player/location info for context
                        'player_name': p_data.get('name','?'),
                        'location': curr_loc
                    }
                    ai_eval_resp = get_ai_response("EVALUATE_STEP_COMPLETION", ai_eval_context)
                    # Check if AI responded YES
                    if isinstance(ai_eval_resp, str) and ai_eval_resp.strip().upper() == 'YES':
                        step_done = True
                        logging.info(f"Step {s_id} of quest {q_id} completed via AI Check evaluating TRUE.")
                    else:
                        logging.info(f"AI Check for step {s_id} evaluated FALSE or Error. AI Response: '{ai_eval_resp}'")
            else:
                logging.error(f"Could not find step data for current step: {q_id}/{s_id}")

        # --- Process Step Completion ---
        if step_done:
            step_completed_this_turn = True
            logging.info(f"Processing step completion for: {q_id}/{s_id}")
            step_data = get_quest_step(q_id, s_id) # Re-fetch step data
            if step_data:
                # Add system message for completion
                conv_log.append({
                    "speaker":"System",
                    "text":f"Objective Complete: '{p_data.get('current_step_description','Objective Details Missing')}'!"
                })
                # Apply step reward
                reward_msg = apply_reward(p_data, step_data.get("step_reward"), user_id)
                if reward_msg:
                    conv_log.append({"speaker":"System", "text": reward_msg})

                # Determine next step or chapter end
                next_s_id = step_data.get("next_step")
                step_was_major = step_data.get("is_major_plot_point", False)
                step_was_final = (next_s_id is None) # It's final if no next_step defined
                inputs_count = len(chapter_inputs_log)

                # Check if this step triggers End-of-Chapter
                trigger_eoc_condition = (step_was_major or step_was_final) and inputs_count >= MIN_INPUTS_FOR_EOC

                if trigger_eoc_condition:
                    if step_was_major:
                        conv_log.append({"speaker":"System", "text": "A significant moment in your journey..."})
                    if step_was_final:
                        # Apply final quest reward if this was the last step
                        quest_data = get_quest(q_id)
                        if quest_data:
                            final_reward_msg = apply_reward(p_data, quest_data.get("completion_reward"), user_id)
                            if final_reward_msg:
                                conv_log.append({"speaker":"System", "text": final_reward_msg})
                        # Mark quest completed in flags
                        p_data.setdefault(FS_QUEST_FLAGS, {})[f"quest_{q_id}_completed"] = True
                        logging.info(f"Quest {q_id} marked as completed.")

                    # Clear current quest info and reset turn count for EOC flow
                    p_data['current_quest_id'] = None
                    p_data['current_step_id'] = None
                    p_data['current_quest_title'] = ''
                    p_data['current_step_description'] = ''
                    p_data['turn_count'] = 0 # Reset turns for EOC
                    chapter_ended = True
                    logging.info(f"Chapter end triggered by completing step {s_id} of quest {q_id}.")

                elif next_s_id:
                    # Advance to the next step in the quest
                    next_step_info = get_quest_step(q_id, next_s_id)
                    if next_step_info:
                        next_desc = next_step_info.get('description', 'Continue your quest.')
                        p_data['current_step_id'] = next_s_id
                        p_data['current_step_description'] = next_desc
                        conv_log.append({"speaker":"System", "text":f"New Objective: {next_desc}"})
                        logging.info(f"Advanced to step {next_s_id} in quest {q_id}")
                    else:
                        # Error: Next step defined but not found
                        logging.error(f"Cannot find data for next step {next_s_id} in quest {q_id}. Ending quest.")
                        p_data['current_quest_id'] = None; p_data['current_step_id'] = None # End quest

                elif step_was_final:
                    # Final step completed, but didn't trigger EOC (e.g., too few inputs)
                    quest_data = get_quest(q_id)
                    if quest_data:
                        final_reward_msg = apply_reward(p_data, quest_data.get("completion_reward"), user_id)
                        if final_reward_msg:
                            conv_log.append({"speaker":"System", "text": final_reward_msg})
                    p_data.setdefault(FS_QUEST_FLAGS, {})[f"quest_{q_id}_completed"] = True
                    logging.warning(f"Final step {s_id} completed for quest {q_id}, but EOC not triggered (Inputs: {inputs_count}). Quest ended.")
                    # Clear quest info as it's finished
                    p_data['current_quest_id'] = None
                    p_data['current_step_id'] = None
                    p_data['current_quest_title'] = ''
                    p_data['current_step_description'] = ''
            else:
                # Should not happen if step_done is True
                logging.error(f"CRITICAL: Cannot find step data for completed step {s_id} in quest {q_id}")

        # --- Get New Location Description (if moved and chapter didn't end) ---
        if needs_desc_after_move and not chapter_ended:
            # Build context specifically for GET_DESCRIPTION
            desc_ctx = {
                'player_name': p_data.get('name','?'),
                'location': curr_loc, # Use the updated location
                'location_data': world_map.get(curr_loc, {}),
                'thetopia_location_lore': thetopia_lore.get('locations', {}).get(curr_loc, {}),
                'player_race': p_data.get('race_name','?'),
                'player_class': p_data.get('class_name','?'),
                'player_philosophy': p_data.get('philosophy_name','?'),
                'player_fate_points': p_data.get('fate_points', 0),
                 # Pass current quest info even after moving
                'current_quest_id': p_data.get('current_quest_id'),
                'current_step_id': p_data.get('current_step_id'),
                'current_quest_title': p_data.get('current_quest_title',''),
                'current_step_description': p_data.get('current_step_description','')
            }
            desc_txt = get_ai_response("GET_DESCRIPTION", desc_ctx)
            if desc_txt:
                conv_log.append({"speaker":"AI", "text": desc_txt})
                session[SESSION_LAST_AI_OUTPUT] = desc_txt # Update last AI output

        # --- AI Check for EOC Suggestion (if conditions met) ---
        should_check_eoc = (
            not chapter_ended and
            turn_num >= EOC_CHECK_START_TURN and
            turn_num % EOC_CHECK_INTERVAL == (EOC_CHECK_START_TURN % EOC_CHECK_INTERVAL) and
            not step_completed_this_turn # Don't suggest EOC on the same turn a step was completed
        )
        if should_check_eoc:
            eoc_check_context = ai_context.copy() # Use the main context from this turn
            eoc_check_context['turn_count'] = turn_num
            eoc_check_context['inputs_count'] = len(chapter_inputs_log)
            # Build conversation summary from recent messages (including this turn)
            recent_conv_log = session.get(SESSION_CONVERSATION, [])[:] # Copy log before this turn
            recent_conv_log.append({"speaker":"Player", "text":p_input}) # Add player input
            if ai_resp: recent_conv_log.append({"speaker":"AI", "text":ai_resp}) # Add AI output
            # Add any system messages added *this turn* (step complete, rewards)
            system_msgs_this_turn = [msg for msg in conv_log if msg not in session.get(SESSION_CONVERSATION, []) and msg.get('speaker') == 'System']
            recent_conv_log.extend(system_msgs_this_turn)
            # Create summary string (last ~6 messages)
            eoc_check_context['conversation_summary'] = "\n".join([
                f"{msg['speaker']}: {msg['text'][:100]}" # Truncate long messages
                for msg in recent_conv_log[-6:] # Take last 6 entries
            ])

            logging.info(f"Checking AI EOC suggestion for char {char_id} turn {turn_num}.")
            eoc_suggestion = get_ai_response("CHECK_CHAPTER_PROGRESS", eoc_check_context)
            suggestion = eoc_suggestion.strip().upper() if isinstance(eoc_suggestion, str) else ""

            if suggestion == 'YES':
                 # Prompt player to confirm EOC
                 conv_log.append({"speaker":"System", "text":"This feels like a good place to pause and reflect on this chapter. Shall we conclude it? (yes/no)"})
                 p_data[SESSION_EOC_PROMPTED] = True # Set persistent flag
                 session[SESSION_EOC_PROMPTED] = True # Set session flag
                 logging.info(f"AI suggested EOC for {char_id}. Player prompted.")
            elif suggestion == 'SUGGEST_TASK':
                 # Initiate side quest flow
                 logging.info(f"AI suggested player side quest for {char_id}.")
                 side_quest_init_ctx = { k: p_data.get(k) for k in ['name', 'race_name', 'class_name', 'philosophy_name', 'current_location']}
                 init_resp = get_ai_response("INITIATE_PLAYER_SIDEQUEST", side_quest_init_ctx)
                 conv_log.append({"speaker":"AI", "text": init_resp})
                 # Set side quest state in session
                 session[SESSION_SIDE_QUEST_ACTIVE] = True
                 session[SESSION_SIDE_QUEST_DESC] = None # Desc will be set by player response
                 session[SESSION_SIDE_QUEST_TURNS] = 0
                 p_data[SESSION_EOC_PROMPTED] = False # Ensure EOC prompt is off
                 session[SESSION_EOC_PROMPTED] = False
            else:
                 # No suggestion or explicit NO
                 logging.info(f"AI EOC check result: '{suggestion}' for {char_id}. Continuing chapter.")
                 p_data[SESSION_EOC_PROMPTED] = False # Ensure EOC prompt is off
                 session[SESSION_EOC_PROMPTED] = False


        # --- Save Final State for this Turn ---
        session[SESSION_CONVERSATION] = conv_log[-MAX_CONVO_LINES:] # Update session log
        p_data[FS_CONVERSATION] = session[SESSION_CONVERSATION] # Update data to be saved
        p_data[FS_CHAPTER_INPUTS] = session[SESSION_CHAPTER_INPUTS] # Update data to be saved
        p_data[SESSION_EOC_PROMPTED] = session.get(SESSION_EOC_PROMPTED, False) # Sync EOC prompt status
        # Ensure flags and inventory are updated in p_data before save
        p_data[FS_QUEST_FLAGS] = p_data.get(FS_QUEST_FLAGS, {})
        p_data[FS_INVENTORY] = p_data.get(FS_INVENTORY, [])
        session.modified = True # Mark session as modified

        # Save character data
        saved_id = save_character_data(user_id, p_data)
        if not saved_id:
            # Critical save error, redirect to profile
            flash("CRITICAL ERROR: Failed to save your progress! Please reload your character.", "critical")
            session.pop(SESSION_CHARACTER_ID, None)
            return redirect(url_for('profile'))

        # --- Redirect ---
        if chapter_ended:
            session[SESSION_EOC_STATE] = 'START' # Set state for EOC route
            session.modified = True
            return redirect(url_for('end_of_chapter'))
        else:
            return redirect(url_for('game_view')) # Continue in game view

    # --- <<< REVISED >>> GET Request Handling (Display Game View) ---
    else: # request.method == 'GET'
        # --- <<< NEW: Introduction Logic >>> ---
        player_has_seen_intro = False
        show_intro_this_time = False # Flag to indicate if intro is displayed *this* time

        # Heuristic: Is this the character's first turn ever? (0 turns, empty log)
        first_character_turn = (p_data.get('turn_count', 0) == 0 and not p_data.get(FS_CONVERSATION))

        # Check the PLAYER'S intro status in Firestore
        try:
            profile_ref = db.collection('player_profiles').document(user_id)
            # Only fetch the intro flag field
            profile_doc = profile_ref.get([FS_PLAYER_HAS_SEEN_INTRO])
            if profile_doc.exists:
                player_has_seen_intro = profile_doc.to_dict().get(FS_PLAYER_HAS_SEEN_INTRO, False)
            else:
                # Profile doc missing for logged-in user? Should not happen after signup.
                # Assume intro needed if profile somehow missing.
                logging.warning(f"Player profile document not found for user {user_id} when checking intro status. Assuming intro needed.")
                player_has_seen_intro = False
        except Exception as e:
            logging.error(f"Failed to fetch {FS_PLAYER_HAS_SEEN_INTRO} for user {user_id}: {e}", exc_info=True)
            # If DB read fails, assume they HAVE seen intro to avoid repeated display on error
            player_has_seen_intro = True

        # Determine if intro should be shown this time
        if not player_has_seen_intro:
            show_intro_this_time = True # Mark that we are showing it now
            logging.info(f"Displaying introduction for user {user_id} (char {char_id}).")

            # <<< REVISED Intro Script Text >>>
            intro_text = """
Welcome to your Daydream! You are a new player located on Dumpster Planet, responsible for containing all of the wasted ideas from human daydreams. The game’s governing AI is named The Great Recycler and is responsible for “cleaning up” Daydream by elevating ideas from trash to treasure. 

Your journey begins in Thetopia, a pocket of stability amidst the chaotic Dumpster Planet – a realm made from forgotten ideas and lost dreams.

Here, your greatest tool is your imagination! The more descriptive and detailed you are in your actions and narration, the richer your adventure will become, and the more the story will evolve based on *your* writing. Don't be afraid to write detailed descriptions and express your character's thoughts and feelings. This helps me understand your intent and bring the world to life around you.

Our adventure is structured around quests, which form chapters in your story. Each chapter is inspired by a stage of the classic Hero's Journey, giving our quest a unique theme. As you complete chapters, we'll pause to reflect. I'll help analyze your writing and comprehension, not for a grade, but to help you grow stronger in your storytelling skills. The goal is to improve through play!

Do you have any questions before we begin, or are you ready to dive into your first quest in Thetopia?
"""
            # Get current session log
            conv_log_for_session = session.get(SESSION_CONVERSATION, [])

            # Prepend intro text *only if* it's not already the first message
            # (This prevents duplication if user refreshes the page immediately after intro)
            if not conv_log_for_session or conv_log_for_session[0].get('text') != intro_text:
                 conv_log_for_session.insert(0, {"speaker": "Storyteller", "text": intro_text})
                 session[SESSION_CONVERSATION] = conv_log_for_session
                 session.modified = True
                 # Also update the persistent log in p_data immediately
                 p_data[FS_CONVERSATION] = conv_log_for_session[-MAX_CONVO_LINES:]

            # Update Firestore flag for the USER asynchronously
            try:
                # Use set with merge=True to safely update or add the field
                profile_ref.set({FS_PLAYER_HAS_SEEN_INTRO: True}, merge=True)
                logging.info(f"Updated {FS_PLAYER_HAS_SEEN_INTRO} to True for user {user_id}.")
                # Save p_data if we added the intro text to its log
                if not conv_log_for_session or conv_log_for_session[0].get('text') == intro_text:
                     save_character_data(user_id, p_data)
            except Exception as e:
                logging.error(f"Failed to update {FS_PLAYER_HAS_SEEN_INTRO} for user {user_id}: {e}")
                # Log error, but continue; intro was shown in session anyway

        # --- <<< END Introduction Logic >>> ---

        # --- Fetch Data for Display ---
        conv_log_from_session = session.get(SESSION_CONVERSATION, []) # Get potentially updated log
        vocab_info = get_active_vocab_data(user_id) # Gets settings (inc. colors) and vocab
        active_vocab = vocab_info.get("vocab", {})
        vocab_settings = vocab_info.get("settings", {}) # Extract settings dict

        # --- Determine if Initial AI Setup Call is Needed ---
        # Needs setup ONLY if it's the first turn AND intro wasn't shown this time
        needs_initial_setup = first_character_turn and not show_intro_this_time

        if needs_initial_setup:
             logging.info(f"Running INITIAL_SETUP AI for new character {char_id} (Turn 0, Intro not shown this load).")
             # Build context for INITIAL_SETUP
             ai_context = {
                 'player_name': p_data.get('name','?'),
                 'player_race': p_data.get('race_name','?'),
                 'player_class': p_data.get('class_name','?'),
                 'player_philosophy': p_data.get('philosophy_name','?'),
                 'location': curr_loc,
                 'thetopia_location_lore': thetopia_lore.get('locations',{}).get(curr_loc,{}),
                 'current_quest_id': p_data.get('current_quest_id'),
                 'current_step_id': p_data.get('current_step_id'),
                 'current_quest_title': p_data.get('current_quest_title',''),
                 'current_step_description': p_data.get('current_step_description','')
             }
             initial_ai_response = get_ai_response("INITIAL_SETUP", ai_context)

             if initial_ai_response and isinstance(initial_ai_response, str):
                 # Check if this exact message is already the last one (avoid double add on reload)
                 if not conv_log_from_session or conv_log_from_session[-1].get('text') != initial_ai_response:
                      conv_log_from_session.append({"speaker": "AI", "text": initial_ai_response})
                      session[SESSION_CONVERSATION] = conv_log_from_session # Update session log
                      session.modified = True
                      # Also update the persistent log in p_data
                      p_data[FS_CONVERSATION] = conv_log_from_session[-MAX_CONVO_LINES:]
                      # Save character data immediately after adding initial setup message
                      save_character_data(user_id, p_data)
             else:
                  logging.warning(f"INITIAL_SETUP failed or returned non-string for char {char_id}. Response: {initial_ai_response}")

        # --- Process Conversation Log for Display (Apply Highlighting) ---
        display_log = []
        for message in conv_log_from_session:
            processed_message = message.copy()
            text_to_process = message.get('text', '')
            speaker = message.get('speaker')
            # Apply highlighting to AI and Storyteller messages
            if speaker in ['AI', 'Storyteller']: # <<< REVISED: Include Storyteller >>>
                 text_with_vocab = apply_vocab_highlighting_python(text_to_process, active_vocab, vocab_settings)
                 text_with_all_highlights = apply_lore_highlighting_python(text_with_vocab, lore_vocabulary)
                 processed_message['text'] = text_with_all_highlights # Use safe HTML
            elif speaker == 'System':
                 # Allow basic HTML like line breaks in system messages if needed
                 processed_message['text'] = text_to_process.replace('\n', '<br>')
            # Player messages remain plain text (no |safe filter needed)
            display_log.append(processed_message)

        # --- Prepare Character Data for Template ---
        template_data = p_data.copy()
        template_data['current_location_name'] = curr_loc # Add location name
        # Remove large/internal fields not needed directly in template display
        fields_to_pop = [FS_CONVERSATION, FS_CHAPTER_INPUTS, 'learned_vocab', FS_QUEST_FLAGS, FS_INVENTORY]
        for field in fields_to_pop:
            template_data.pop(field, None)

        # --- Prepare Lore Data for JavaScript Highlighting ---
        lore_data_for_json = {} # Initialize empty dict
        try:
            current_lore = globals().get('thetopia_lore', {}) # Safely access global
            if isinstance(current_lore, dict):
                # Include relevant top-level keys for JS lookups
                keys_to_include = ['locations', 'npcs', 'races', 'classes', 'philosophies', 'concepts', 'setting']
                for key in keys_to_include:
                    lore_data_for_json[key] = current_lore.get(key, {}) # Get each section safely
            else:
                logging.error(f"Global 'thetopia_lore' variable is not a dictionary (Type: {type(current_lore)}). Sending empty lore data.")
            # Convert to JSON string for embedding in HTML
            thetopia_lore_json = json.dumps(lore_data_for_json)
        except NameError:
             logging.error(f"NameError accessing 'thetopia_lore' globally. Sending empty lore data.")
             thetopia_lore_json = "{}" # Fallback empty JSON
        except Exception as json_err:
             logging.error(f"Failed to serialize lore data to JSON: {json_err}", exc_info=True)
             thetopia_lore_json = "{}" # Fallback empty JSON

        # --- Render Template ---
        try:
            return render_template(
                 'game_view.html',
                 conversation=display_log,
                 character_data=template_data,
                 thetopia_lore_data=thetopia_lore_json # Pass JSON string
             )
        except Exception as render_err:
             # Handle potential template rendering errors
             logging.critical(f"Template rendering error in game_view GET: {render_err}", exc_info=True)
             flash("Critical error displaying game. Please reload your character.", "critical")
             session.pop(SESSION_CHARACTER_ID, None)
             session.modified = True
             return redirect(url_for('profile'))

# --- Vocab/Report Journal ---
@app.route('/journal/vocab', methods=['GET'])
@login_required
def journal_vocab_report():
    user_id = session[SESSION_USER_ID]
    char_id = session.get(SESSION_CHARACTER_ID)
    if not char_id:
        flash("No character loaded.", "warning")
        return redirect(url_for('profile'))

    p_data = load_character_data(user_id, char_id)
    if not p_data:
        return redirect(url_for('profile')) # Redirect if char load fails

    # --- Prepare Vocabulary Data ---
    active_vocab_data = get_active_vocab_data(user_id)
    combined_vocab = active_vocab_data.get("vocab", {})
    awl_words = []
    ai_words_by_list = {}
    # Sort vocab by word for display
    for word, data in sorted(combined_vocab.items()):
        source = data.get("source", "Unknown")
        entry = {"word": word, "definition": data.get("definition", "?"), "color": data.get("color", "#FFFFFF")} # Placeholder color
        if source == "AWL":
            awl_words.append(entry)
        else: # Group AI words by their list name (source)
            if source not in ai_words_by_list:
                ai_words_by_list[source] = []
            ai_words_by_list[source].append(entry)

    # --- Fetch Metadata for AI Lists (for management UI) ---
    ai_lists_metadata = []
    try:
        profile_ref = db.collection('player_profiles').document(user_id)
        # Query only AI-generated lists
        ai_lists_query = profile_ref.collection('custom_vocab_lists').where(filter=FieldFilter('is_ai_generated', '==', True)).stream()
        for list_doc in ai_lists_query:
            list_data = list_doc.to_dict()
            ai_lists_metadata.append({
                "id": list_doc.id,
                "name": list_data.get("name", "Unnamed AI List"),
                "color": list_data.get("color", DEFAULT_VOCAB_LIST_COLOR),
                "is_active": list_data.get("is_active", False),
                "word_count": len(list_data.get("words", [])),
                "created_at": list_data.get("created_at") # For sorting
            })
        # Sort lists by creation date, newest first (handle missing timestamp)
        ai_lists_metadata.sort(key=lambda x: x.get('created_at', 0), reverse=True) # Use 0 as fallback for sort
    except Exception as e:
        logging.error(f"Failed to fetch AI vocabulary list metadata for user {user_id}: {e}", exc_info=True)
        flash("Error loading vocabulary list details.", "warning")

    # --- Prepare Report Summaries ---
    report_summaries = p_data.get('report_summaries', [])
    # Sort reports by chapter number
    report_summaries.sort(key=lambda x: x.get('chapter', 0))

    # Render the template
    return render_template(
        'journal_vocab_report.html',
        awl_words=awl_words,
        ai_word_lists=ai_words_by_list, # Pass dict grouped by list name
        ai_lists_metadata=ai_lists_metadata, # Pass list metadata for management
        report_summaries=report_summaries,
        premium_active=check_premium_access(user_id) # Pass premium status for UI elements
    )

# --- Character/Quest Journal ---
@app.route('/journal/character', methods=['GET'])
@login_required
def journal_char_quest():
    user_id = session[SESSION_USER_ID]
    char_id = session.get(SESSION_CHARACTER_ID)
    if not char_id:
        flash("No character loaded.", "warning")
        return redirect(url_for('profile'))

    p_data = load_character_data(user_id, char_id)
    if not p_data:
        return redirect(url_for('profile')) # Redirect if char load fails

    # --- Prepare Character Sheet Data ---
    sheet_data = p_data.copy() # Work with a copy
    # Remove large/internal fields not needed for direct display
    fields_to_pop = [FS_CONVERSATION, FS_CHAPTER_INPUTS, FS_QUEST_FLAGS] # Keep FS_INVENTORY now!
    for field in fields_to_pop:
        sheet_data.pop(field, None)
    # Convert learned vocab set back to list for display
    if isinstance(sheet_data.get('learned_vocab'), set):
         sheet_data['learned_vocab'] = sorted(list(sheet_data['learned_vocab']))

    # --- Prepare Quest Log Data ---
    quest_log = {
        "title": p_data.get('current_quest_title', 'No active quest'),
        "step_desc": p_data.get('current_step_description', '')
    }
    # Handle cases where title might be missing but ID exists (should be rare)
    if quest_log['title'] == 'No active quest' and p_data.get('current_quest_id'):
        qd = get_quest(p_data['current_quest_id'])
        quest_log['title'] = qd.get('title', 'Unknown Quest') if qd else 'Unknown Quest'

    # --- Prepare Inventory Data ---
    inventory_list = p_data.get(FS_INVENTORY, []) # Get inventory list

    # Render the template, passing character sheet, quest log, and inventory
    return render_template(
        'journal_char_quest.html',
        character_sheet=sheet_data,
        quest_log=quest_log,
        inventory=inventory_list # Pass the inventory list
    )


# --- End-of-Chapter Route ---
@app.route('/end_of_chapter', methods=['GET', 'POST'])
@login_required
def end_of_chapter():
    user_id = session[SESSION_USER_ID]
    char_id = session.get(SESSION_CHARACTER_ID)
    if not char_id:
        flash("No character loaded to process end of chapter.", "error")
        return redirect(url_for('profile'))

    p_data = load_character_data(user_id, char_id)
    if not p_data:
        # If character fails to load during EOC, clear session and redirect
        flash("Failed to load character data for end of chapter.", "error")
        session.pop(SESSION_CHARACTER_ID, None)
        session.pop(SESSION_EOC_STATE, None) # Clear EOC state too
        session.modified = True
        return redirect(url_for('profile'))

    eoc_state = session.get(SESSION_EOC_STATE, 'START') # Get current EOC state from session

    # --- POST Request Handling ---
    if request.method == 'POST':
        # --- State: Submitted Comprehension Answers ---
        if eoc_state == 'AWAIT_COMP_ANSWERS':
            questions = session.get(SESSION_EOC_QUESTIONS, [])
            if not questions:
                 flash("Error: Comprehension questions missing from session.", "error")
                 logging.error(f"EOC state AWAIT_COMP_ANSWERS but no questions in session for user {user_id}, char {char_id}.")
                 session[SESSION_EOC_STATE] = 'START'; session.modified = True # Reset state
                 return redirect(url_for('end_of_chapter'))

            # Collect answers from form
            answers = [request.form.get(f'comp_answer_{i+1}', '').strip() for i in range(len(questions))]
            # Basic validation: ensure all questions were answered
            if not all(answers):
                flash("Please answer all comprehension questions.", "warning")
                # Re-render comprehension check page with existing questions
                return render_template('comprehension_check.html', questions=questions)

            # --- AI Comprehension Evaluation ---
            eval_ctx = {'questions': questions, 'answers': answers}
            comp_res = get_ai_response("EVALUATE_CHAPTER_COMPREHENSION", eval_ctx)
            comp_score = 0.0 # Default score
            if isinstance(comp_res, dict) and 'overall_comprehension_score' in comp_res:
                try:
                    comp_score = float(comp_res['overall_comprehension_score'])
                    comp_score = max(0.0, min(10.0, comp_score)) # Clamp score
                except (ValueError, TypeError):
                    logging.warning(f"Invalid comprehension score format from AI: {comp_res['overall_comprehension_score']} for user {user_id}, char {char_id}.")
            else:
                flash("The AI storyteller had trouble evaluating your comprehension.", "warning")
                logging.warning(f"Comprehension evaluation failed for user {user_id}, char {char_id}. Response: {comp_res}")

            # --- AI Writing Analysis ---
            chapter_text = "\n---\n".join(p_data.get(FS_CHAPTER_INPUTS,[]))
            if not chapter_text:
                chapter_text = "(No player inputs recorded for this chapter)" # Handle empty
            anal_ctx = {'chapter_player_text': chapter_text}
            anal_res = get_ai_response("ANALYZE_PLAYER_WRITING", anal_ctx)
            # Use empty dict if analysis fails, prevents errors later
            if not isinstance(anal_res, dict) or 'error' in anal_res:
                flash("The AI storyteller couldn't analyze your writing style for this chapter.", "warning")
                logging.warning(f"Writing analysis failed for user {user_id}, char {char_id}. Response: {anal_res}")
                anal_res = {}

            # --- Calculate Player XP ---
            xp_gained = (
                5 # Base completion XP
                + {'S':1, 'M':3, 'L':5}.get(anal_res.get('avg_length_category'), 0)
                + len(anal_res.get('awl_words_used', [])) * 2
                + int(anal_res.get('relevance_coherence_score', 0))
                + {'L':1, 'M':3, 'H':5}.get(anal_res.get('style_rating'), 0)
                + {'L':1, 'M':3, 'H':5}.get(anal_res.get('thinking_rating'), 0)
                + {'L':1, 'M':3, 'H':5}.get(anal_res.get('descriptive_language_rating'), 0)
                + max(0, int(comp_score) - 5) # Bonus for comprehension > 5
            )
            xp_gained = max(0, xp_gained) # Ensure XP is not negative
            flash(f"Chapter Complete! You earned {xp_gained} Player XP!", "success")

            # --- Update Player Profile XP/Level ---
            try:
                profile_ref = db.collection('player_profiles').document(user_id)
                profile_ref.update({'total_player_xp': firestore.Increment(xp_gained)})
                logging.info(f"Player XP +{xp_gained} updated in Firestore for user: {user_id}")
                # Check for level up
                profile_doc = profile_ref.get(['total_player_xp', 'player_level'])
                if profile_doc.exists:
                    profile_data = profile_doc.to_dict()
                    current_xp = profile_data.get('total_player_xp', 0)
                    current_level = profile_data.get('player_level', 1)
                    xp_for_next = (current_level * 100) # Example XP threshold
                    if current_xp >= xp_for_next:
                        new_level = current_level + 1
                        profile_ref.update({'player_level': new_level})
                        flash(f"Congratulations! You've reached Player Level {new_level}!", "success")
                        logging.info(f"Player {user_id} leveled up to {new_level}")
                else:
                     logging.warning(f"Could not retrieve profile data after XP update for level check. User: {user_id}")
            except Exception as e:
                logging.error(f"Failed to update player XP/Level in Firestore for user {user_id}: {e}", exc_info=True)
                flash("Could not update your Player XP due to a server error.", "warning")

            # --- Generate Report Summary ---
            summary_text = f"**Chapter Complete!**\n\n"
            summary_text += f"* **Comprehension Score:** {comp_score:.1f} / 10\n"
            summary_text += f"* **Player XP Gained:** +{xp_gained}\n\n"
            summary_text += f"* **Writing Analysis:**\n"
            awl_used = anal_res.get('awl_words_used', [])
            summary_text += f"    * AWL Words Used ({len(awl_used)}): {', '.join(awl_used) if awl_used else 'None'}\n"
            summary_text += f"    * Relevance & Coherence: {anal_res.get('relevance_coherence_score','?')} / 5\n"
            summary_text += f"    * Style Complexity: {anal_res.get('style_rating','?')}\n"
            summary_text += f"    * Critical Thinking: {anal_res.get('thinking_rating','?')}\n"
            summary_text += f"    * Average Length: {anal_res.get('avg_length_category','?')}\n"
            summary_text += f"    * Descriptive Language: {anal_res.get('descriptive_language_rating','?')}\n"

            # --- Update Character Data (Save summary, clear inputs) ---
            summaries = p_data.get('report_summaries', [])
            current_chapter_num = len(summaries) + 1
            summaries.append({
                "chapter": current_chapter_num, "summary": summary_text,
                "comprehension_score": comp_score, "player_xp_gained": xp_gained,
                "analysis_raw": anal_res # Store raw analysis
            })
            p_data['report_summaries'] = summaries
            p_data[FS_CHAPTER_INPUTS] = [] # Clear chapter inputs

            # --- Update Session and Save ---
            session[SESSION_EOC_SUMMARY] = summary_text # Store summary for display
            session[SESSION_EOC_STATE] = 'AWAIT_REPORT_ACK' # Move to next state
            session.pop(SESSION_CHAPTER_INPUTS, None) # Clear chapter inputs from session
            session.pop(SESSION_EOC_QUESTIONS, None) # Clear questions from session
            session.modified = True
            save_character_data(user_id, p_data) # Save updated character data
            return redirect(url_for('end_of_chapter')) # Redirect to show report

        # --- State: Acknowledged Report, Generate Next Quest ---
        elif eoc_state == 'AWAIT_REPORT_ACK':
            current_chapter_num = len(p_data.get('report_summaries', []))
            logging.info(f"User {user_id} acknowledged EOC report for character {char_id}, chapter {current_chapter_num}. Generating next quest.")

            # --- Determine Next Hero's Journey Stage ---
            stage_index = (current_chapter_num) % len(HERO_JOURNEY_STAGES)
            next_stage = HERO_JOURNEY_STAGES[stage_index]
            logging.info(f"Using Hero's Journey Stage '{next_stage}' for Chapter {current_chapter_num+1} quest generation.")

            # --- AI Quest Generation ---
            next_q_id, next_q_title, next_s_id, next_s_desc = None, None, None, None
            q_gen_ctx = {
                 "character_data": p_data,
                 "chapter_summaries": p_data.get('report_summaries', []),
                 "next_hero_journey_stage": next_stage
            }
            q_gen_res = get_ai_response("GENERATE_NEXT_QUEST", q_gen_ctx)

            if isinstance(q_gen_res, dict) and 'error' not in q_gen_res:
                next_q_id = q_gen_res.get('quest_id')
                next_q_title = q_gen_res.get('title')
                next_s_id = q_gen_res.get('starting_step_id')
                next_s_desc = q_gen_res.get('starting_step_description')
                # Validate generated parts
                if not (next_q_id and next_s_id and next_q_title and next_s_desc):
                     logging.warning(f"AI quest generation returned incomplete data for char {char_id}: {q_gen_res}")
                     flash("The AI storyteller couldn't generate a specific new quest objective. Feel free to explore!", "info")
                     next_q_id, next_q_title, next_s_id, next_s_desc = None, "Explore Thetopia", None, "Forge your own path or seek rumors."
                else:
                     logging.info(f"AI generated next quest for char {char_id}: {next_q_id} - '{next_q_title}'")
                     flash(f"New objective received: {next_q_title}", "info") # Inform player
            else: # Handle AI error
                error_reason = q_gen_res.get('reason','Unknown AI error') if isinstance(q_gen_res, dict) else 'AI communication failure'
                logging.error(f"AI quest generation failed for char {char_id}. Reason: {error_reason}")
                flash(f"The AI storyteller had trouble determining your next quest ({error_reason}). Time to explore!", "warning")
                next_q_id, next_q_title, next_s_id, next_s_desc = None, "Explore Thetopia", None, "Forge your own path or seek rumors."

            # --- Update Character Data with New Quest ---
            p_data['current_quest_id'] = next_q_id
            p_data['current_step_id'] = next_s_id
            p_data['current_quest_title'] = next_q_title or ''
            p_data['current_step_description'] = next_s_desc or ''
            p_data[FS_CHAPTER_INPUTS] = [] # Ensure clear for new chapter start
            p_data['turn_count'] = 0 # Reset turn count for new chapter

            # --- Clear EOC Session State ---
            for key in [SESSION_EOC_STATE, SESSION_EOC_QUESTIONS, SESSION_EOC_SUMMARY]:
                session.pop(key, None)
            session.modified = True

            save_character_data(user_id, p_data) # Save final character state
            return redirect(url_for('game_view')) # Redirect back to the game

        # --- Invalid EOC state in POST ---
        else:
            flash("An unexpected error occurred during chapter conclusion.", "error")
            logging.error(f"Unexpected EOC state '{eoc_state}' encountered in POST for user {user_id}, char {char_id}. Resetting EOC.")
            session.pop(SESSION_EOC_STATE, None); session.pop(SESSION_EOC_QUESTIONS, None); session.pop(SESSION_EOC_SUMMARY, None)
            session.modified = True
            return redirect(url_for('profile'))

    # --- GET Request Handling ---
    else: # request.method == 'GET'
        # --- State: Start EOC Flow -> Show Comprehension Check ---
        if eoc_state == 'START':
            questions = [ # Example questions
                 "What was your main objective or focus in this chapter?",
                 "Describe a key interaction or challenge you faced.",
                 "How did your character approach the situations encountered?"
            ]
            session[SESSION_EOC_QUESTIONS] = questions # Store questions in session
            session[SESSION_EOC_STATE] = 'AWAIT_COMP_ANSWERS' # Update state
            session.modified = True
            logging.info(f"Initiating EOC comprehension check for user {user_id}, char {char_id}.")
            return render_template('comprehension_check.html', questions=questions)

        # --- State: Awaiting Answers -> Re-display Comprehension Check ---
        elif eoc_state == 'AWAIT_COMP_ANSWERS':
            questions = session.get(SESSION_EOC_QUESTIONS)
            if questions:
                logging.info(f"Re-displaying EOC comprehension check for user {user_id}, char {char_id}.")
                return render_template('comprehension_check.html', questions=questions)
            else:
                flash("Error: Comprehension questions lost. Restarting chapter conclusion.", "error")
                logging.error(f"EOC state AWAIT_COMP_ANSWERS but no questions in session (GET). User: {user_id}, char {char_id}.")
                session[SESSION_EOC_STATE] = 'START'; session.modified = True
                return redirect(url_for('end_of_chapter'))

        # --- State: Awaiting Report Ack -> Display Report Summary ---
        elif eoc_state == 'AWAIT_REPORT_ACK':
            summary = session.get(SESSION_EOC_SUMMARY, "Report summary is currently unavailable.")
            logging.info(f"Displaying EOC report summary for user {user_id}, char {char_id}.")
            return render_template('report_summary.html', report_summary=summary)

        # --- State: Complete (Should not be reachable via GET) ---
        elif eoc_state == 'COMPLETE':
            logging.info(f"EOC state was 'COMPLETE' on GET request for user {user_id}, redirecting to game.")
            return redirect(url_for('game_view'))

        # --- Invalid EOC state in GET ---
        else:
             flash("An unexpected state was encountered during chapter conclusion.", "error")
             logging.error(f"Unexpected EOC state '{eoc_state}' encountered in GET for user {user_id}, char {char_id}. Resetting.")
             session.pop(SESSION_EOC_STATE, None); session.pop(SESSION_EOC_QUESTIONS, None); session.pop(SESSION_EOC_SUMMARY, None)
             session.modified = True
             return redirect(url_for('profile'))


# --- Root Route ---
@app.route('/')
def root():
    # Redirect logged-in users to profile, others to login
    if SESSION_USER_ID in session:
        return redirect(url_for('profile'))
    else:
        return redirect(url_for('login'))


# --- Delete Character Route ---
@app.route('/delete_character/<char_id>', methods=['POST'])
@login_required
def delete_character(char_id):
    user_id = session[SESSION_USER_ID]
    if not char_id:
        flash("Invalid request: Missing character ID.", "error")
        return redirect(url_for('profile'))

    logging.info(f"User {user_id} attempting to delete character {char_id}")
    try:
        char_ref = db.collection('characters').document(char_id)
        char_doc = char_ref.get(['user_id', 'name']) # Fetch only needed fields
        if not char_doc.exists:
            flash("Character not found.", "warning")
            logging.warning(f"Attempt to delete non-existent character {char_id} by user {user_id}.")
            return redirect(url_for('profile'))

        # --- Ownership Check ---
        if char_doc.to_dict().get('user_id') != user_id:
            flash("Permission denied to delete this character.", "error")
            logging.warning(f"SECURITY ALERT: User {user_id} denied deletion of character {char_id} (owner mismatch).")
            return redirect(url_for('profile'))

        # Proceed with deletion
        char_name = char_doc.to_dict().get('name', 'Unknown Character')
        char_ref.delete()
        logging.info(f"Successfully deleted character {char_id} ('{char_name}') for user {user_id}.")
        flash(f"Character '{char_name}' deleted successfully.", "success")

        # --- Clear Deleted Character from Session if Active ---
        if session.get(SESSION_CHARACTER_ID) == char_id:
            keys_to_clear = [
                 SESSION_CHARACTER_ID, SESSION_CONVERSATION, SESSION_CHAPTER_INPUTS,
                 SESSION_LOCATION, SESSION_LAST_AI_OUTPUT, SESSION_EOC_STATE,
                 SESSION_SIDE_QUEST_ACTIVE, SESSION_SIDE_QUEST_DESC, SESSION_SIDE_QUEST_TURNS
            ]
            for key in keys_to_clear:
                session.pop(key, None)
            session.modified = True
            logging.info(f"Cleared deleted character {char_id} from active session.")

    except Exception as e:
        logging.error(f"Error deleting character {char_id} for user {user_id}: {e}", exc_info=True)
        flash("An error occurred while trying to delete the character.", "error")

    return redirect(url_for('profile')) # Redirect back to profile page


# --- Run App ---
if __name__ == '__main__':
    # Configuration for running the Flask app
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0') # Default host
    port = int(os.environ.get('FLASK_RUN_PORT', 8080)) # Default port
    # Enable debug mode based on environment variable
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']

    # Print server start information
    print(f"--- Starting Daydream Server V5.3 ---") # <<< Updated version number >>>
    print(f" Mode: {'Debug (with reloader)' if debug_mode else 'Production'}")
    print(f" Host: {host}")
    print(f" Port: {port}")
    print(f" Firebase Project: {os.environ.get('GOOGLE_CLOUD_PROJECT', 'daydream-455317')}")
    print(f" Vertex AI Location: {os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')}")
    print(f"-----------------------------------")

    # Run the Flask development server
    app.run(debug=debug_mode, host=host, port=port, use_reloader=debug_mode)