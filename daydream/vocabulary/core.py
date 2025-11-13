# vocabulary.py - Handles SAT/AWL vocabulary checking and XP calculation for Daydream

import re

import json
import logging
import os

# --- Vocabulary Loading ---
def load_vocabulary_from_file(filename="academic_word_list.json"):
    """
    Loads a vocabulary set from a specified JSON file in the data directory.
    Args:
        filename (str): The name of the vocabulary file to load.
    Returns:
        dict: A dictionary of words mapped to their sublist/difficulty level.
              Returns an empty dictionary if loading fails.
    """
    # Correctly construct the path to the data directory relative to this file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'data', filename)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            logging.info(f"Successfully loaded vocabulary from {file_path}")
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Vocabulary file not found at {file_path}. The app may not function correctly.")
        return {}
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {file_path}. Please check the file for syntax errors.")
        return {}
    except Exception as e:
        logging.error(f"An unexpected error occurred while loading {file_path}: {e}")
        return {}

# Load the default vocabulary set on module import.
# This can be dynamically replaced later if needed.
AWL_WORDS = load_vocabulary_from_file()

# --- XP and Category Configuration ---
XP_TIERS = {
    'common': 3,      # XP for common AWL words
    'medium': 5,      # XP for medium AWL words
    'challenging': 10 # XP for challenging AWL words
}

# Map AWL sublists to our categories
# Adjust mapping as needed based on desired difficulty spread
SUBLIST_TO_CATEGORY = {
    1: 'common', 2: 'common', 3: 'common',
    4: 'medium', 5: 'medium', 6: 'medium', 7: 'medium',
    8: 'challenging', 9: 'challenging', 10: 'challenging'
}

# Pre-calculate category for each word for faster lookup
AWL_CATEGORIZED = {word: SUBLIST_TO_CATEGORY.get(details.get('sublist'), 'medium') for word, details in AWL_WORDS.items()}

import json
import logging

# --- Load AWL Definitions ---
AWL_DEFINITIONS = {}
try:
    with open('awl_definitions.json', 'r', encoding='utf-8') as f:
        AWL_DEFINITIONS = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    logging.warning(f"Could not load awl_definitions.json: {e}")


# --- Main XP Calculation Function ---

def calculate_xp(player_input_text: str, learned_vocab_set: set) -> tuple[int, set]:
    """
    Calculates XP based on finding NEW AWL words in player input, using tiered XP.

    Args:
        player_input_text: The raw text input from the player.
        learned_vocab_set: A set of words the player has already learned (and received XP for).

    Returns:
        A tuple containing:
        - total_xp_gain (int): The amount of XP earned from this input.
        - found_new_awl_words (set): A set of the new AWL words found in this input.
    """
    if not player_input_text:
        return 0, set()

    total_xp_gain = 0
    found_new_awl_words = set()

    # 1. Clean and tokenize the input text
    # Convert to lowercase, remove basic punctuation, split into words
    text_lower = player_input_text.lower()
    # Remove punctuation that might interfere with word matching
    text_cleaned = re.sub(r'[^\w\s-]', '', text_lower) # Keep hyphens within words
    words = text_cleaned.split()

    # Use a set for efficient checking of unique words within this input
    unique_words_in_input = set(words)

    # 2. Check each unique word against the categorized AWL
    for word in unique_words_in_input:
        # Check if the word is in our categorized AWL list
        if word in AWL_CATEGORIZED:
            # Check if the player has *already learned* this word
            if word not in learned_vocab_set:
                # It's a new AWL word for this player! Award XP based on category.
                category = AWL_CATEGORIZED[word]
                xp_award = XP_TIERS.get(category, 0) # Get XP for the category, default 0 if somehow missing

                if xp_award > 0:
                    total_xp_gain += xp_award
                    found_new_awl_words.add(word)
                    # Optional: Print debug message
                    # print(f"[DEBUG Vocab] Found new AWL word: '{word}' (Category: {category}, XP: +{xp_award})")

    # 3. Return total XP gain and the set of new words found
    return total_xp_gain, found_new_awl_words

# --- Example Usage (for testing) ---
if __name__ == '__main__':
    # Simulate player input and learned words
    test_input_1 = "I need to analyse the data and evaluate the subsequent impact."
    test_input_2 = "The contrast was obvious, despite the ambiguous visual presentation."
    test_input_3 = "Let's COMMENCE the project and allocate resources." # Test case insensitivity
    test_input_4 = "Look around." # No AWL words expected
    test_input_5 = "approach evaluate" # Test finding already learned words

    learned_words = set()
    print(f"Input: \"{test_input_1}\"")
    xp1, new1 = calculate_xp(test_input_1, learned_words)
    print(f"XP Gained: {xp1}, New Words: {new1}")
    learned_words.update(new1)
    print(f"Learned List: {learned_words}\n")

    print(f"Input: \"{test_input_2}\"")
    xp2, new2 = calculate_xp(test_input_2, learned_words)
    print(f"XP Gained: {xp2}, New Words: {new2}")
    learned_words.update(new2)
    print(f"Learned List: {learned_words}\n")

    print(f"Input: \"{test_input_3}\"")
    xp3, new3 = calculate_xp(test_input_3, learned_words)
    print(f"XP Gained: {xp3}, New Words: {new3}")
    learned_words.update(new3)
    print(f"Learned List: {learned_words}\n")

    print(f"Input: \"{test_input_4}\"")
    xp4, new4 = calculate_xp(test_input_4, learned_words)
    print(f"XP Gained: {xp4}, New Words: {new4}")
    learned_words.update(new4)
    print(f"Learned List: {learned_words}\n")

    print(f"Input: \"{test_input_5}\"")
    xp5, new5 = calculate_xp(test_input_5, learned_words)
    print(f"XP Gained: {xp5}, New Words: {new5}")
    learned_words.update(new5)
    print(f"Learned List: {learned_words}\n")