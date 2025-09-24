import json
import os
import logging

def load_lore_from_file(filename="thetopia_lore.json"):
    """
    Loads a lore set from a specified JSON file in the data directory.
    Args:
        filename (str): The name of the lore file to load.
    Returns:
        dict: A dictionary containing the lore data.
              Returns an empty dictionary if loading fails.
    """
    # Correctly construct the path to the data directory relative to this file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'data', filename)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            logging.info(f"Successfully loaded lore from {file_path}")
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Lore file not found at {file_path}. The app may not function correctly.")
        return {}
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {file_path}. Please check the file for syntax errors.")
        return {}
    except Exception as e:
        logging.error(f"An unexpected error occurred while loading {file_path}: {e}")
        return {}

# Load the default lore set on module import.
thetopia_lore = load_lore_from_file()

def get_lore():
    """Returns the currently loaded lore data."""
    return thetopia_lore

if __name__ == "__main__":
    # Example of accessing lore data
    lore = get_lore()
    if lore:
        print("--- Game Premise ---")
        print(lore.get("game_premise", "Premise not found."))
        print("\n--- Great Recycler ---")
        print(lore.get("main_ai_entity", {}).get("description", "AI info not found."))
        print("\n--- Example Race Lore (Android) ---")
        print(lore.get("races", {}).get("Android", {}).get("lore_in_thetopia", "Android lore missing."))
        print("\n--- Example Location (Town Square) ---")
        print(lore.get("locations", {}).get("Thetopia - Town Square", {}).get("description", "Square description missing."))
        print(f"NPCs Here: {lore.get('locations', {}).get('Thetopia - Town Square', {}).get('present_npcs', [])}")
        print("\n--- Example NPC (Widget) ---")
        print(lore.get("npcs", {}).get("Widget", {}).get("description", "Widget info missing."))
        print("\n--- Thetopia Description ---")
        print(lore.get("setting", {}).get("thetopia_description", "Thetopia description missing."))
    else:
        print("Could not load lore data.")
