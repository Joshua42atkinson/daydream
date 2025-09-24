import logging
import json
import re
from functools import wraps
import uuid

from flask import session, flash, redirect, url_for, request
from google.cloud.firestore_v1.base_query import FieldFilter
from . import db, model, auth_client, firebase_app
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
    chars = []
    if not db:
        return chars
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

def load_character_data(user_id:str, char_id:str) -> dict | None:
    # ... (full implementation from original app.py)
    return None

def save_character_data(user_id:str, character_data:dict|None) -> str|None:
    # ... (full implementation from original app.py)
    return None

def check_premium_access(user_id:str) -> bool:
    # ... (full implementation from original app.py)
    return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if SESSION_USER_ID not in session:
            flash("You must be logged in to access this page.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def check_step_completion(p_data: dict, step_data: dict) -> tuple[bool, str | None]:
    # ... (full implementation from original app.py)
    return False, None

def apply_reward(p_data: dict, reward_data: dict | None, user_id: str) -> str | None:
    # ... (full implementation from original app.py)
    return None

def get_active_vocab_data(user_id: str) -> dict:
    # ... (full implementation from original app.py)
    return {"settings": {}, "vocab": {}}