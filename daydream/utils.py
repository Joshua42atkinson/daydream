import logging
import json
import re
from functools import wraps
import uuid

from flask import session, flash, redirect, url_for, request, current_app
from google.cloud.firestore_v1.base_query import FieldFilter
from .quests import get_quest, get_quest_step, HERO_JOURNEY_STAGES
from .vocabulary import calculate_xp, AWL_WORDS, AWL_DEFINITIONS
from .lore import thetopia_lore

# --- Constants ---
MAX_INPUT_LENGTH = 500
MAX_CONVO_LINES = 100
STARTING_LOCATION = "Thetopia - Town Square"
BASE_FATE_POINTS = 1
EOC_CHECK_START_TURN = 10
EOC_CHECK_INTERVAL = 4
MIN_INPUTS_FOR_EOC = 10
ABILITY_NAME_MAP = {
    "natural armor": "Natural Armor", "cannot wear armor": "Cannot Wear Armor", "fortunate find": "Fortunate Find",
    "integrated systems": "Integrated Systems", "memory limit": "Memory Limit", "pack tactics": "Pack Tactics",
    "fierce loyalty": "Fierce Loyalty", "artistic shell": "Artistic Shell", "second brain": "Second Brain",
    "absorb magic": "Absorb Magic", "shapechange": "Shapechange", "tinker": "Tinker", "arcane affinity": "Arcane Affinity",
    "combat ready": "Combat Ready", "empathic": "Empathic", "quick wits": "Quick Wits",
    "becoming awesome boost": "Becoming Awesome Boost", "law and order gain": "Law and Order Gain",
    "pointlessnesses reroll": "Pointlessnesses Reroll",
}
HERO_JOURNEY_STAGES = [
    "The Ordinary World", "The Call to Adventure", "Refusal of the Call", "Meeting the Mentor", "Crossing the Threshold",
    "Tests, Allies, Enemies", "Approach to the Inmost Cave", "The Ordeal", "Reward (Seizing the Sword)",
    "The Road Back", "Resurrection", "Return with the Elixir"
]
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
FS_CONVERSATION = 'conversation_log'
FS_CHAPTER_INPUTS = 'current_chapter_inputs'
FS_QUEST_FLAGS = 'quest_flags'
FS_INVENTORY = 'inventory'
FS_PLAYER_HAS_SEEN_INTRO = 'has_seen_intro'

def find_terms_in_text(text: str, terms_dict: dict, key_transform=lambda k: k.lower()) -> list:
    found = []
    if not isinstance(terms_dict, dict) or not text: return found
    transformed_map = {key_transform(k): {"original": k, "data": v} for k, v in terms_dict.items() if key_transform(k)}
    sorted_keys = sorted(transformed_map.keys(), key=len, reverse=True)
    processed_indices = set()
    for term_key in sorted_keys:
        term_info = transformed_map[term_key]
        try:
            for match in re.finditer(r'\b' + re.escape(term_key) + r'\b', text, re.IGNORECASE):
                if not any(i in processed_indices for i in range(match.start(), match.end())):
                    found.append((match.start(), match.end(), term_info["original"], term_info["data"]))
                    processed_indices.update(range(match.start(), match.end()))
        except re.error as e: logging.error(f"Regex error: {e}")
    return sorted(found, key=lambda item: item[0])

def process_text_for_highlighting(text: str, terms: list, span_class: str, **kwargs) -> str:
    if not terms or not text: return text
    result_parts, last_end = [], 0
    for start, end, original, data in terms:
        result_parts.append(text[last_end:start])
        attrs = f'class="{span_class}"'
        if (title := kwargs.get('title_formatter', lambda d: '')(data)):
            attrs += f' title="{str(title).replace("\"", "&quot;")}"'
        result_parts.append(f'<span {attrs.strip()}>{text[start:end]}</span>')
        last_end = end
    result_parts.append(text[last_end:])
    return "".join(result_parts)

def get_ai_response(prompt_type: str, context: dict) -> str | dict:
    # ... (full implementation from original app.py)
    return "This is a mock AI response."

def get_user_characters(user_id:str) -> list[dict]:
    """Fetches a list of characters for a given user ID from Firestore."""
    chars = []
    db = current_app.config.get('DB')
    if not db or current_app.config.get('BYPASS_EXTERNAL_SERVICES'):
        logging.info(f"Bypassing character fetch for user {user_id}.")
        return [{"id": "dummy_char_123", "name": "Bypass Charlie", "race": "Human", "class": "Developer"}]

    try:
        docs_query = db.collection('characters').where(filter=FieldFilter('user_id', '==', user_id))
        docs_stream = docs_query.stream()
        for doc in docs_stream:
            d = doc.to_dict()
            chars.append({
                "id": doc.id, "name": d.get("name", "Unnamed Character"),
                "race": d.get("race_name", "Unknown Race"), "class": d.get("class_name", "Unknown Class")
            })
    except Exception as e:
        logging.error(f"Failed to fetch characters for user {user_id}: {e}", exc_info=True)
    return chars

def load_character_data(user_id: str, char_id: str) -> dict | None:
    """Loads a specific character's data from Firestore."""
    db = current_app.config.get('DB')
    if not db or current_app.config.get('BYPASS_EXTERNAL_SERVICES'):
        logging.info(f"Bypassing character load for char_id {char_id}.")
        # Return a dummy character structure for bypass mode
        return {
            "id": char_id, "name": "Bypass Charlie", "user_id": user_id,
            "race_name": "Human", "class_name": "Developer", "xp": 100,
            "level": 5, "inventory": ["Debug Stick"], "quest_flags": {},
            "location": STARTING_LOCATION
        }
    try:
        doc_ref = db.collection('characters').document(char_id)
        doc = doc_ref.get()
        if doc.exists:
            char_data = doc.to_dict()
            if char_data.get('user_id') == user_id:
                return char_data
            else:
                logging.warning(f"User {user_id} attempted to load character {char_id} they do not own.")
    except Exception as e:
        logging.error(f"Failed to load character {char_id} for user {user_id}: {e}", exc_info=True)
    return None

def save_character_data(user_id: str, character_data: dict) -> str | None:
    """Saves character data to Firestore."""
    db = current_app.config.get('DB')
    if not db or current_app.config.get('BYPASS_EXTERNAL_SERVICES'):
        logging.info(f"Bypassing character save for user {user_id}.")
        return character_data.get("id", "dummy_char_123") # Return dummy ID

    char_id = character_data.get('id')
    if not char_id:
        # Create new character if no ID
        char_ref = db.collection('characters').document()
        character_data['id'] = char_ref.id
        character_data['user_id'] = user_id
    else:
        # Update existing character
        char_ref = db.collection('characters').document(char_id)
        # Verify ownership before saving
        if char_ref.get().to_dict().get('user_id') != user_id:
            logging.error(f"User {user_id} attempted to save character {char_id} they do not own.")
            return None

    try:
        char_ref.set(character_data, merge=True)
        return character_data['id']
    except Exception as e:
        logging.error(f"Failed to save character {character_data.get('id')} for user {user_id}: {e}", exc_info=True)
    return None


def check_premium_access(user_id: str) -> bool:
    """Checks if a user has premium access from their Firestore profile."""
    db = current_app.config.get('DB')
    if not db or current_app.config.get('BYPASS_EXTERNAL_SERVICES'):
        logging.warning("Bypassing premium check; defaulting to False.")
        return False
    try:
        profile_ref = db.collection('player_profiles').document(user_id)
        profile = profile_ref.get()
        if profile.exists:
            return profile.to_dict().get('has_premium', False)
    except Exception as e:
        logging.error(f"Error checking premium status for user {user_id}: {e}", exc_info=True)
    return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if SESSION_USER_ID not in session:
            flash("You must be logged in to access this page.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def instructor_required(f):
    """
    Decorator to ensure a user is logged in and has the 'instructor' role.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get(SESSION_USER_ID)
        if not user_id:
            flash("You must be logged in to access this page.", "warning")
            return redirect(url_for('auth.login', next=request.url))

        # In bypass mode, we can grant automatic instructor access for testing.
        if current_app.config.get('BYPASS_EXTERNAL_SERVICES'):
            logging.warning(f"Bypassing instructor check for user {user_id}.")
            return f(*args, **kwargs)

        db = current_app.config.get('DB')
        if not db:
            flash("Database service not available.", "danger")
            return redirect(url_for('profile.profile'))

        try:
            user_profile = db.collection('player_profiles').document(user_id).get()
            if user_profile.exists and user_profile.to_dict().get('role') == 'instructor':
                return f(*args, **kwargs)
            else:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for('profile.profile'))
        except Exception as e:
            logging.error(f"Error checking instructor role for user {user_id}: {e}")
            flash("An error occurred while verifying your permissions.", "danger")
            return redirect(url_for('profile.profile'))
    return decorated_function

def check_step_completion(p_data: dict, step_data: dict) -> tuple[bool, str | None]:
    # ... (full implementation from original app.py)
    return False, None

def apply_reward(p_data: dict, reward_data: dict | None, user_id: str) -> str | None:
    """Applies a quest reward to the character data and saves it."""
    if reward_data is None:
        return None

    feedback_message = "Quest completed! "
    if 'xp' in reward_data:
        p_data['xp'] = p_data.get('xp', 0) + reward_data['xp']
        feedback_message += f"You gained {reward_data['xp']} XP. "
    if 'items' in reward_data:
        p_data['inventory'] = p_data.get('inventory', []) + reward_data['items']
        feedback_message += f"You received: {', '.join(reward_data['items'])}. "
    if 'fate_points' in reward_data:
        p_data['fate_points'] = p_data.get('fate_points', 0) + reward_data['fate_points']
        feedback_message += f"You earned {reward_data['fate_points']} Fate Point(s). "

    # Save the updated character data
    save_character_data(user_id, p_data)
    return feedback_message.strip()

def get_active_vocab_data(user_id: str) -> dict:
    """
    Gets the active vocabulary data for a user, combining default and custom lists
    based on user settings in their Firestore profile.
    """
    db = current_app.config.get('DB')
    # Default to using AWL if in bypass mode or if DB fails
    if not db or current_app.config.get('BYPASS_EXTERNAL_SERVICES'):
        return {"settings": {"use_default_awl": True}, "vocab": AWL_WORDS}

    try:
        profile_ref = db.collection('player_profiles').document(user_id)
        profile = profile_ref.get()

        if profile.exists and profile.to_dict().get('vocab_settings', {}).get('use_default_awl', True):
             # In a real app, you would also fetch and merge custom vocab lists here
            return {"settings": profile.to_dict().get('vocab_settings'), "vocab": AWL_WORDS}
        else:
            # User has disabled the default list and we haven't implemented custom lists yet
            return {"settings": profile.to_dict().get('vocab_settings', {}), "vocab": {}}
    except Exception as e:
        logging.error(f"Failed to get vocab data for user {user_id}: {e}", exc_info=True)
        # Fallback to default AWL list on error
        return {"settings": {"use_default_awl": True}, "vocab": AWL_WORDS}