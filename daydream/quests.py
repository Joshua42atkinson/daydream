# quests.py - Defines quest structures and content for Daydream
# Version 4.4 - Corrected syntax error in __main__ test block.
# ==============================================================================
# ==============================================================================
# Hero's Journey Framework
# ==============================================================================
# This structure defines the 12 stages of the Hero's Journey, providing a narrative
# and psychological backbone for quest generation. Each stage includes a title,
# a brief description of its psychological purpose, and keywords for the AI.

HERO_JOURNEY_STAGES = [
    {
        "stage": 1,
        "title": "The Ordinary World",
        "description": "Introduces the hero in their normal life, establishing their identity, environment, and the status quo. It's a baseline from which they will grow.",
        "keywords": ["normalcy", "routine", "home", "status quo", "unfulfilled"]
    },
    {
        "stage": 2,
        "title": "The Call to Adventure",
        "description": "An event or discovery disrupts the hero's ordinary life and presents a challenge or quest. This is the catalyst for their journey.",
        "keywords": ["disruption", "invitation", "challenge", "new information", "catalyst"]
    },
    {
        "stage": 3,
        "title": "Refusal of the Call",
        "description": "The hero feels fear and hesitates to answer the call. This highlights the risks and stakes of the journey, making their eventual acceptance more meaningful.",
        "keywords": ["fear", "hesitation", "doubt", "insecurity", "avoidance"]
    },
    {
        "stage": 4,
        "title": "Meeting the Mentor",
        "description": "The hero encounters a mentor figure who provides guidance, training, or a special tool. This prepares them for the challenges ahead.",
        "keywords": ["guidance", "wisdom", "training", "mentor", "supernatural aid"]
    },
    {
        "stage": 5,
        "title": "Crossing the Threshold",
        "description": "The hero commits to the adventure and enters the special world of the story. This marks their true departure from the ordinary world.",
        "keywords": ["commitment", "departure", "new world", "point of no return", "first test"]
    },
    {
        "stage": 6,
        "title": "Tests, Allies, and Enemies",
        "description": "The hero faces a series of tests and challenges, learning the rules of the new world. They form alliances and identify their enemies.",
        "keywords": ["challenges", "alliances", "enemies", "learning", "adaptation"]
    },
    {
        "stage": 7,
        "title": "Approach to the Inmost Cave",
        "description": "The hero and their allies prepare for the major challenge in the special world. This often involves planning and facing their greatest fears.",
        "keywords": ["preparation", "planning", "greatest fear", "confrontation", "the ordeal"]
    },
    {
        "stage": 8,
        "title": "The Ordeal",
        "description": "The central crisis of the story, where the hero faces their greatest fear or a life-and-death moment. This is the 'dark night of the soul.'",
        "keywords": ["crisis", "death and rebirth", "greatest challenge", "rock bottom", "transformation"]
    },
    {
        "stage": 9,
        "title": "Reward (Seizing the Sword)",
        "description": "Having survived the ordeal, the hero gains a reward, such as an object of great importance, new knowledge, or reconciliation.",
        "keywords": ["reward", "knowledge", "power", "reconciliation", "treasure"]
    },
    {
        "stage": 10,
        "title": "The Road Back",
        "description": "The hero begins their journey back to the ordinary world, but the consequences of the ordeal and reward may still be unfolding.",
        "keywords": ["return", "consequences", "chase", "escape", "resurrection"]
    },
    {
        "stage": 11,
        "title": "The Resurrection",
        "description": "The hero faces a final, climactic test on their return journey. This test purifies, redeems, and transforms them into a new being.",
        "keywords": ["climax", "final test", "purification", "redemption", "new self"]
    },
    {
        "stage": 12,
        "title": "Return with the Elixir",
        "description": "The hero returns to their ordinary world with the reward or knowledge they have gained, which they can now use to benefit their community.",
        "keywords": ["homecoming", "sharing knowledge", "benefit to community", "master of two worlds", "resolution"]
    }
]


# ==============================================================================
# Quest Data Structure Explanation (Enhanced)
# ==============================================================================
# QUEST_DATA = {
#     "QUEST_ID": { # Unique identifier for the quest
#         "title": "Quest Title", # User-facing title
#         "chapter_theme": "Associated Hero's Journey Stage", # Optional theme alignment
#         "description": "Overall goal of the quest/chapter.", # High-level overview
#         "starting_step": "STEP_ID_01", # The first step ID for this quest
#         "completion_reward": { # Reward upon completing the *entire* quest (final step)
#                "type": "fate_points | item | boon | info | relationship",
#                # Examples:
#                # "value": 1, # For fate_points
#                # "name": "Polished Widget", # For item
#                # "set_flag": {"widget_quest_done": True}, # For info type to set a flag
#                # "details": "You've earned the trust of the Repair Guild.", # For info/relationship announcement
#                # "target": "Repair Guild", "change": 1 # For relationship points
#         },
#         "steps": {
#             "STEP_ID_XX": { # Unique identifier for the step within this quest
#                 "description": "Player-facing goal for this specific step.",
#                 "trigger_condition": "state_var:flag_name == True | ai_check:condition_to_evaluate | inventory_has:item_name", # How app.py knows step is done.
#                 # Examples:
#                 #   "state_var:fountain_analyzed == True" -> Check p_data['quest_flags']['fountain_analyzed']
#                 #   "ai_check:repair_successful" -> Requires specific AI call in app.py (EVALUATE_STEP_COMPLETION)
#                 #   "inventory_has:Cogwheel and Hydro-Spanner" -> Check if items are in player's inventory (FS_INVENTORY)
#                 "step_reward": { # Optional reward upon completing *this specific* step
#                     "type": "fate_points | item | info | relationship",
#                     # ... same structure as completion_reward ...
#                     "set_flag": {"fountain_analyzed": True}, # Example: Set flag via step reward
#                     "silent": True / False # Optional: If true, don't explicitly announce reward in system message
#                 },
#                 "next_step": "STEP_ID_YY or None", # ID of the next step, or None if this is the last step.
#                 "is_major_plot_point": True / False # Does completing this step trigger the EOC sequence? (Use sparingly)
#             },
#             # ... more steps
#         }
#     },
#     # ... more quests
# }

# ==============================================================================
# Quest Data Definition
# ==============================================================================

QUEST_DATA = {
   # --- Bolt (Android Inventor) Starter Quest ---
   # Matches ID used in starter_quest_map in app.py
   "Q_B1_FAULTY_FOUNTAIN": {
       "title": "The Faulty Fountain",
       "chapter_theme": "The Ordinary World / Call to Adventure",
       "description": "As an Inventor new to Thetopia, you observe the Town Square, noting inefficiencies. The central data fountain sputters erratically – a clear system flaw. Analyzing and repairing this disorder could be a logical first step towards establishing purpose.",
       "starting_step": "STEP_01_ANALYZE_FOUNTAIN",
       "completion_reward": {
           "type": "relationship",
           "target": "Thetopia Populace", # Fictional target for reputation
           "change": 1,
           "details": "Fixing the fountain seems to have improved the general mood slightly. You notice fewer annoyed glances directed your way."
       },
       "steps": {
           "STEP_01_ANALYZE_FOUNTAIN": {
               "description": "Approach the sputtering data fountain in the Town Square. Describe how you perceive its malfunction and use your analytical skills (perhaps related to your 'Integrated Systems' ability?) to diagnose the problem.",
               # Trigger: AI confirms analysis was attempted/described
               "trigger_condition": "ai_check:fountain_analysis_described",
               # Reward: Set a flag indicating analysis is done
               "step_reward": {
                   "type": "info",
                   "set_flag": {"fountain_analyzed": True},
                   "silent": True # No need to announce this internal flag
                },
               "next_step": "STEP_02_IDENTIFY_PARTS",
               "is_major_plot_point": False
           },
           "STEP_02_IDENTIFY_PARTS": {
               "description": "Based on your analysis (now that `fountain_analyzed` flag is True), determine the specific component(s) needed for the repair. Perhaps consult your internal schematics or observe the fountain's mechanism closely.",
               # Trigger: AI confirms specific parts were identified
               "trigger_condition": "ai_check:fountain_parts_identified",
               # Reward: Set flag, maybe give info detail if needed elsewhere
               "step_reward": {
                   "type": "info",
                   "details": "You determine a 'Hydro-Spanner' and a 'Type-3 Cogwheel' seem necessary.", # Info for player
                   "set_flag": {"fountain_parts_identified": True},
                   "silent": False # Announce the required parts
               },
               "next_step": "STEP_03_ACQUIRE_PARTS",
               "is_major_plot_point": False
           },
           "STEP_03_ACQUIRE_PARTS": {
               "description": "Acquire the needed Hydro-Spanner and Type-3 Cogwheel. Perhaps Maker's Alley has parts, or maybe ask the Info-Broker?",
               # Trigger: Check inventory list in p_data[FS_INVENTORY]
               "trigger_condition": "inventory_has:Hydro-Spanner and Type-3 Cogwheel",
               "step_reward": None, # Reward is having the parts
               "next_step": "STEP_04_ATTEMPT_REPAIR",
               "is_major_plot_point": False
           },
           "STEP_04_ATTEMPT_REPAIR": {
               "description": "With the necessary parts in hand, attempt to repair the data fountain using your 'Tinker' ability and the acquired components. Describe your repair process.",
               # Trigger: AI confirms repair action was attempted
               "trigger_condition": "ai_check:repair_attempt_made",
               # Reward: Set flag based on AI evaluation? Or handle in next step trigger. Let's set flag here.
               "step_reward": {
                    "type": "info",
                    # This flag might be set based on AI outcome, complex. Let's use simple check first.
                    "set_flag": {"repair_attempted": True}, # Simpler flag
                    "silent": True
               },
               "next_step": "STEP_05_CHECK_RESULTS",
               "is_major_plot_point": False
           },
           "STEP_05_CHECK_RESULTS": {
               "description": "Observe the data fountain. Did the repair work? Is the data flowing smoothly now?",
               # Trigger: AI evaluates if the outcome described by player/previous AI indicates success
               "trigger_condition": "ai_check:fountain_repair_successful",
               # Reward: Minor reward for success & set final flag
               "step_reward": {
                   "type": "fate_points",
                   "value": 1,
                   "silent": True # Overall quest reward is announced later
               },
               "next_step": None, # End of this quest chain
               "is_major_plot_point": True # Completing the repair IS a major plot point now
           }
       }
   },

   # --- Totem (Sasquatch Soldier) Starter Quest ---
   # Matches ID used in premade_characters.json & starter_quest_map in app.py
   "Q_T1_FIRST_IMPRESSIONS": {
       "title": "First Impressions",
       "chapter_theme": "The Ordinary World / Call to Adventure",
       "description": "You arrive in the bustling, chaotic Thetopia Town Square, a stark contrast to the quiet forests you barely remember. Your companion porcupine trembles slightly. Take a moment to get your bearings and describe your initial reaction to this strange new place.",
       "starting_step": "STEP_01_OBSERVE_SQUARE",
       "completion_reward": { # Small reward for grounding
            "type": "fate_points",
            "value": 1
       },
       "steps": {
           "STEP_01_OBSERVE_SQUARE": {
               "description": "Look around the Town Square. Describe what catches your eye first – the shimmering pavement, the murmuring fountain, the diverse inhabitants. How does your large, natural Sasquatch form feel in this artificial place? How does your porcupine companion react?",
               # Trigger: AI confirms player provided the requested description
               "trigger_condition": "ai_check:initial_description_provided",
               "step_reward": None,
               "next_step": "STEP_02_FIND_ANCHOR",
               "is_major_plot_point": False
           },
           "STEP_02_FIND_ANCHOR": {
               "description": "Amidst the strangeness, find one element that feels somewhat familiar or grounding. Is it a patch of synthesized moss, the sight of Guard Captain Elena's disciplined presence, or something else? Describe what you focus on.",
               # Trigger: AI confirms player described focusing on something specific
               "trigger_condition": "ai_check:anchor_point_described",
               "step_reward": None,
               "next_step": "STEP_03_FOCUS_SENSES",
               "is_major_plot_point": False
           },
           "STEP_03_FOCUS_SENSES": {
               "description": "Focus your senses, particularly smell and hearing. What distinct sound or scent cuts through the general background noise? Perhaps the synthesized bread from Bakery Street, or the metallic tang from Maker's Alley? Describe the specific sensation.",
               # Trigger: AI confirms player identified a specific sensory detail
               "trigger_condition": "ai_check:specific_sensation_identified",
               "step_reward": {
                   "type": "info",
                   "details": "You've managed to isolate a specific sensory detail amidst the chaos.",
                   "silent": True
                },
               "next_step": "STEP_04_CONSIDER_ACTION",
               "is_major_plot_point": False
           },
           "STEP_04_CONSIDER_ACTION": {
                "description": "Based on your observations and focused sense, what is your first instinctual action as a Soldier? Secure your position, investigate the scent/sound, or perhaps just continue observing warily? Describe your intended first move.",
                # Trigger: AI confirms player described their intended action
                "trigger_condition": "ai_check:first_action_described",
                "step_reward": None,
                "next_step": None, # End intro chapter quest
                "is_major_plot_point": True # End Chapter 1 after deciding the first action
           }
       }
   },

    # --- Pip Quickwit (Leprechaun Rascal) Starter Quest ---
    # Ensure this ID matches your premade_characters.json / starter_quest_map
    # Using "Q_P1_SIZING_UP_THE_MARK" based on previous example
    "Q_P1_SIZING_UP_THE_MARK": {
       "title": "Sizing Up the Mark",
       "chapter_theme": "The Ordinary World / Call to Adventure",
       "description": "You arrive in Thetopia's Town Square, a whirlwind of potential opportunities. The 'lucky' coin feels warm in your pocket. Take stock of the situation – who looks important, who looks distracted, what looks valuable or interestingly 'lost'?",
       "starting_step": "STEP_01_SCAN_THE_CROWD",
        "completion_reward": { # Reward for successful casing
            "type": "fate_points",
            "value": 1
       },
       "steps": {
           "STEP_01_SCAN_THE_CROWD": {
               "description": "Scan the crowd in the Town Square. Describe your initial assessment from your Leprechaun perspective – focus on movement, exchanges, unattended items. How does your small stature affect your view or allow you to go unnoticed?",
               "trigger_condition": "ai_check:initial_scan_described",
               "step_reward": None,
               "next_step": "STEP_02_ASSESS_VALUE",
               "is_major_plot_point": False
           },
           "STEP_02_ASSESS_VALUE": {
               "description": "What seems most 'valuable' right now? Not just monetary value, but potential value for information (like Info-Broker Pip might have), amusement, or leverage. Describe the most tempting target.",
               "trigger_condition": "ai_check:value_assessed_described",
               "step_reward": None,
               "next_step": "STEP_03_IDENTIFY_OPPORTUNITY",
               "is_major_plot_point": False
           },
           "STEP_03_IDENTIFY_OPPORTUNITY": {
               "description": "Focus on one specific person (like the Info-Broker or Guard Captain), item (maybe something near the fountain?), or conversation that seems like the most promising 'opportunity' for your Rascal talents. What makes it stand out?",
               "trigger_condition": "ai_check:opportunity_identified",
               "step_reward": {
                   "type": "info",
                   "details": "You've zeroed in on a potentially interesting situation.",
                   "silent": True
                },
               "next_step": "STEP_04_PLAN_APPROACH",
               "is_major_plot_point": False
           },
            "STEP_04_PLAN_APPROACH": {
                "description": "How would you approach this opportunity? Use your 'Quick Wits'? Try a 'Fortunate Find'? Or perhaps just a charming distraction? Describe your initial plan.",
                "trigger_condition": "ai_check:approach_planned_described",
                "step_reward": None,
                "next_step": None, # End intro chapter quest
                "is_major_plot_point": True # End Chapter 1 after planning the first move
           }
       }
   },

   # --- Mama Willow (Opossuman Counselor) Starter Quest ---
   # Ensure this ID matches your premade_characters.json / starter_quest_map
   # Using "Q_W1_FEELING_THE_ROOM" based on previous example
   "Q_W1_FEELING_THE_ROOM": {
       "title": "Feeling the Room",
       "chapter_theme": "The Ordinary World / Call to Adventure",
       "description": "You arrive in Thetopia Square, a place buzzing with chaotic energy but also hidden anxieties. As a Counselor focused on 'Becoming Awesome', take a moment to sense the emotional atmosphere and present yourself.",
       "starting_step": "STEP_01_OBSERVE_EMOTIONS",
        "completion_reward": { # Reward for connection
            "type": "fate_points",
            "value": 1
       },
       "steps": {
           "STEP_01_OBSERVE_EMOTIONS": {
               "description": "Observe the inhabitants of the Town Square. Describe the general emotional 'vibe' you pick up using your empathic senses. How does your own warm, perhaps slightly unusual, Opossuman appearance and demeanor project into this scene?",
               "trigger_condition": "ai_check:emotions_described",
               "step_reward": None,
               "next_step": "STEP_02_PROJECT_CALM",
               "is_major_plot_point": False
           },
           "STEP_02_PROJECT_CALM": {
                "description": "Subtly project a sense of calm or welcome using your Counselor's presence. Describe how you carry yourself, maybe offering a gentle nod or smile to passersby. Do any individuals react noticeably?",
                "trigger_condition": "ai_check:calm_projected_described",
                "step_reward": None,
                "next_step": "STEP_03_FIND_FOCUS",
                "is_major_plot_point": False
            },
           "STEP_03_FIND_FOCUS": {
               "description": "Identify one individual who seems particularly troubled, lost, or perhaps receptive to your calming presence amidst the crowd. What draws your attention to them specifically?",
               "trigger_condition": "ai_check:focus_individual_identified",
               "step_reward": {
                   "type": "info",
                   "details": "You've found someone who might benefit from your guidance.",
                   "silent": True
                },
               "next_step": "STEP_04_CONSIDER_OPENING",
               "is_major_plot_point": False
           },
           "STEP_04_CONSIDER_OPENING": {
               "description": "How would you initiate contact? A direct approach? Offer a small token (like seeds from your boon)? Or simply make eye contact and offer a warm greeting? Describe your intended opening move to help them on their path to 'Becoming Awesome'.",
               "trigger_condition": "ai_check:opening_move_described",
               "step_reward": None,
               "next_step": None, # End intro chapter quest
               "is_major_plot_point": True # End Chapter 1 after deciding how to approach
           }
       }
   },

   # --- Klex (Slime Archanist) Starter Quest ---
   # Ensure this ID matches your premade_characters.json / starter_quest_map
   # Using "Q_K1_TASTING_THE_AETHER" based on previous example
   "Q_K1_TASTING_THE_AETHER": {
       "title": "Tasting the Aether",
       "chapter_theme": "The Ordinary World / Call to Adventure",
       "description": "You flow into Thetopia's Town Square, a nexus of strange energies from discarded ideas. As an Archanist attuned to magical flows, your first task is to understand the ambient 'flavor' of this place.",
       "starting_step": "STEP_01_SENSE_AMBIENCE",
        "completion_reward": { # Reward for attunement
            "type": "fate_points",
            "value": 1
       },
       "steps": {
           "STEP_01_SENSE_AMBIENCE": {
               "description": "Extend your senses (or pseudopods?). Describe the overall magical or energetic 'feel' of the Town Square. Is it buzzing, stagnant, sharp, chaotic? How does your amorphous Slime nature interact with the environment?",
               "trigger_condition": "ai_check:ambience_described",
               "step_reward": None,
               "next_step": "STEP_02_DIFFERENTIATE_SOURCES",
               "is_major_plot_point": False
           },
           "STEP_02_DIFFERENTIATE_SOURCES": {
                "description": "Try to differentiate the various energy signatures. Can you distinguish the data fountain's murmur from the whispers of the nearby Willow Plaza, or the crackle from Maker's Alley? Describe the different 'flavors' you detect.",
                "trigger_condition": "ai_check:sources_differentiated_described",
                "step_reward": None,
                "next_step": "STEP_03_PINPOINT_FOCUS",
                "is_major_plot_point": False
            },
           "STEP_03_PINPOINT_FOCUS": {
               "description": "Identify the single strongest, most unusual, or most appealing source of energy you can detect nearby. What does it feel like (e.g., sharp, humming, erratic, warm)? Describe the specific signature.",
               "trigger_condition": "ai_check:energy_source_identified",
               "step_reward": {
                   "type": "info",
                   "details": "You've locked onto a significant energy signature.",
                   "silent": True
                },
               "next_step": "STEP_04_CONSIDER_INTERACTION",
               "is_major_plot_point": False
           },
            "STEP_04_CONSIDER_INTERACTION": {
                "description": "How might you interact with this energy signature? Attempt to 'Absorb Magic'? Use your 'Arcane Affinity'? Or simply observe it more closely? Describe your intended next step.",
                "trigger_condition": "ai_check:interaction_intent_described",
                "step_reward": None,
                "next_step": None, # End intro chapter quest
                "is_major_plot_point": True # End Chapter 1 after deciding how to interact
            }
       }
   },

   # --- Shelldon (Tortisian Counselor) Starter Quest ---
   # Ensure this ID matches your premade_characters.json / starter_quest_map
   # Using "Q_S1_ESTABLISHING_PRESENCE" based on previous example
   "Q_S1_ESTABLISHING_PRESENCE": {
       "title": "Establishing Presence",
       "chapter_theme": "The Ordinary World / Call to Adventure",
       "description": "You arrive methodically in Thetopia's Town Square. As a proponent of Law and Order, understanding the environment requires careful observation and establishing a stable position.",
       "starting_step": "STEP_01_FIND_POSITION",
       "completion_reward": { # Reward for methodical start
            "type": "fate_points",
            "value": 1
       },
       "steps": {
           "STEP_01_FIND_POSITION": {
               "description": "Find a suitable, stable location within the Town Square from which to observe. Describe the spot you choose and why it appeals to your Tortisian sense of order. Describe your posture and appearance as you settle in.",
               "trigger_condition": "ai_check:position_described",
               "step_reward": None,
               "next_step": "STEP_02_INITIAL_OBSERVATION",
               "is_major_plot_point": False
           },
           "STEP_02_INITIAL_OBSERVATION": {
                "description": "From your chosen position, make one specific observation about the flow of traffic or interaction patterns. Is there a discernible pattern, or pure chaos? Describe what you see.",
                "trigger_condition": "ai_check:initial_observation_made",
                "step_reward": None,
                "next_step": "STEP_03_IDENTIFY_RULE",
                "is_major_plot_point": False
            },
           "STEP_03_IDENTIFY_RULE": {
               "description": "Based on your observation, try to deduce one apparent 'rule' (spoken or unspoken) governing behavior in the square. It might relate to interacting with Guards, using the fountain, or bartering. What rule do you hypothesize?",
               "trigger_condition": "ai_check:rule_hypothesized",
               "step_reward": {
                   "type": "info",
                   "details": "You've begun your systematic analysis of Thetopia's social dynamics.",
                   "silent": True
                },
               "next_step": "STEP_04_PLAN_VERIFICATION",
               "is_major_plot_point": False
           },
           "STEP_04_PLAN_VERIFICATION": {
                "description": "How might you verify this hypothesized rule? Further observation? Asking someone (like Guard Captain Elena or Professor Quill)? Or perhaps a small, controlled test? Describe your next logical step according to Law and Order.",
                "trigger_condition": "ai_check:verification_planned_described",
                "step_reward": None,
                "next_step": None, # End intro chapter quest
                "is_major_plot_point": True # End Chapter 1 after planning verification
           }
       }
   }
   # --- Add quests for Chapter 2 and beyond here ---
   # --- Example: Could be generated by AI using GENERATE_NEXT_QUEST ---
   # "Q_CH2_BOLT_1A4F": { ... }
}

# ==============================================================================
# Helper Functions (Unchanged)
# ==============================================================================

def get_quest(quest_id):
   """Retrieves data for a specific quest from QUEST_DATA."""
   return QUEST_DATA.get(quest_id)

def get_quest_step(quest_id, step_id):
   """Retrieves data for a specific step within a quest."""
   quest = get_quest(quest_id)
   # Check if quest exists and step_id is valid before accessing steps
   if quest and step_id and isinstance(quest.get("steps"), dict):
       return quest["steps"].get(step_id) # Use .get for safety in case step_id is wrong
   return None # Return None if quest or step not found

# ==============================================================================
# Example Usage (for testing when run directly - CORRECTED SYNTAX)
# ==============================================================================
if __name__ == "__main__":
   print("--- Testing Quest Data Access ---")

   # Test one of the starter quests (e.g., Totem)
   test_quest_id = "Q_T1_FIRST_IMPRESSIONS"
   print(f"\n--- Testing Quest: {test_quest_id} ---")
   test_quest = get_quest(test_quest_id)
   if test_quest:
       print(f"\nFound Quest: {test_quest.get('title')}")
       start_step_id = test_quest.get('starting_step')
       current_step_id = start_step_id
       step_num = 1
       while current_step_id:
            current_step = get_quest_step(test_quest_id, current_step_id)
            if current_step:
                print(f"\n--- Step {step_num} ({current_step_id}) ---")
                desc = current_step.get('description', 'NO DESCRIPTION FOUND')
                # Simple print to avoid f-string issues with potential quotes in desc
                print("Description:", desc)
                print(f"Trigger Condition Example: {current_step.get('trigger_condition')}")
                print(f"Step Reward Example: {current_step.get('step_reward')}")
                print(f"Is Major Plot Point: {current_step.get('is_major_plot_point')}")
                current_step_id = current_step.get('next_step')
                step_num += 1
            else:
                print(f"ERROR: Could not find step data for '{current_step_id}'")
                break
       print(f"\n--- Quest Completion Reward Example ---")
       print(f"{test_quest.get('completion_reward')}")
   else:
       print(f"ERROR: Could not find quest '{test_quest_id}'")


   print("\n--- Testing Invalid Access ---")
   invalid_quest = get_quest("INVALID_ID")
   print(f"Result for get_quest('INVALID_ID'): {invalid_quest}")
   invalid_step = get_quest_step("Q_T1_FIRST_IMPRESSIONS", "INVALID_STEP")
   print(f"Result for get_quest_step('Q_T1...', 'INVALID_STEP'): {invalid_step}")

   print("\n--- Checking All Quest IDs Match Starter Map ---")
   # This list should match the keys used in the starter_quest_map in app.py
   starter_quest_map_keys_from_app = [
       "Q_B1_FAULTY_FOUNTAIN", "Q_T1_FIRST_IMPRESSIONS", "Q_P1_SIZING_UP_THE_MARK",
       "Q_W1_FEELING_THE_ROOM", "Q_K1_TASTING_THE_AETHER", "Q_S1_ESTABLISHING_PRESENCE"
   ]
   missing_quests = []
   all_quest_ids_in_file = QUEST_DATA.keys()
   for q_id in starter_quest_map_keys_from_app:
       if q_id not in all_quest_ids_in_file:
           missing_quests.append(q_id)

   if not missing_quests:
       print("OK: All starter quest IDs referenced in app.py exist as keys in this quests.py file.")
   else:
       print(f"ERROR: The following quest IDs are used in app.py's starter_quest_map but are MISSING as keys in this quests.py file: {missing_quests}")