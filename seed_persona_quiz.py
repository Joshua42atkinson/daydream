import os
import firebase_admin
from firebase_admin import credentials, firestore

def seed_database():
    """
    Seeds the Firestore database with the Persona Quiz content.
    """
    # Initialize Firebase
    SERVICE_ACCOUNT_KEY_PATH = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")
    if not SERVICE_ACCOUNT_KEY_PATH:
        raise ValueError("FIREBASE_SERVICE_ACCOUNT_KEY environment variable not set.")
    if not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
        raise FileNotFoundError(f"Firebase key file not found at path: {os.path.abspath(SERVICE_ACCOUNT_KEY_PATH)}")

    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    # Create Archetypes
    archetypes_data = [
        {'name': 'Sage', 'description': 'You are a wise and knowledgeable observer, always seeking to understand the world around you.', 'stat_buffs': {'Intelligence': 2, 'Perception': 1}},
        {'name': 'Hero', 'description': 'You are a brave and courageous warrior, always ready to stand up for what is right.', 'stat_buffs': {'Courage': 2, 'Strength': 1}},
        {'name': 'Jester', 'description': 'You are a witty and clever trickster, always finding creative solutions to problems.', 'stat_buffs': {'Eloquence': 2, 'Agility': 1}},
        {'name': 'Caregiver', 'description': 'You are a compassionate and empathetic soul, always looking to help others.', 'stat_buffs': {'Empathy': 2, 'Wisdom': 1}},
    ]

    archetype_refs = {}
    for archetype_data in archetypes_data:
        archetype_ref = db.collection('archetypes').document()
        archetype_ref.set(archetype_data)
        archetype_refs[archetype_data['name']] = archetype_ref.id

    # Create Dilemmas
    dilemmas_data = [
        {
            'text': 'A bully is harassing a merchant in the town square. What do you do?',
            'choices': [
                {'text': 'Confront the bully directly.', 'archetype_name': 'Hero'},
                {'text': 'Find a clever way to distract the bully.', 'archetype_name': 'Jester'},
                {'text': 'Observe to understand why the bully is angry.', 'archetype_name': 'Sage'},
                {'text': 'Comfort the merchant after the bully leaves.', 'archetype_name': 'Caregiver'},
            ]
        },
        {
            'text': 'You find a mysterious, locked chest in a dark forest. What is your approach?',
            'choices': [
                {'text': 'Try to force the lock open.', 'archetype_name': 'Hero'},
                {'text': 'Look for a hidden key or a clever way to open it without force.', 'archetype_name': 'Jester'},
                {'text': 'Examine the chest for clues about its origin and purpose.', 'archetype_name': 'Sage'},
                {'text': 'Consider who might have left the chest and why, ensuring it’s safe to open.', 'archetype_name': 'Caregiver'},
            ]
        },
        {
            'text': 'You are offered a powerful but dangerous artifact. What do you do?',
            'choices': [
                {'text': 'Accept the artifact, believing you can control its power for good.', 'archetype_name': 'Hero'},
                {'text': 'Accept the artifact, intrigued by its potential for mischief and clever uses.', 'archetype_name': 'Jester'},
                {'text': 'Decline the artifact, wary of its potential to corrupt and disrupt.', 'archetype_name': 'Sage'},
                {'text': 'Decline the artifact, concerned about the harm it could cause to you and others.', 'archetype_name': 'Caregiver'},
            ]
        },
    ]

    for dilemma_data in dilemmas_data:
        dilemma_ref = db.collection('dilemmas').document()
        dilemma_ref.set({'text': dilemma_data['text']})
        for choice_data in dilemma_data['choices']:
            archetype_id = archetype_refs[choice_data['archetype_name']]
            choice_ref = dilemma_ref.collection('choices').document()
            choice_ref.set({
                'text': choice_data['text'],
                'archetype_id': archetype_id,
            })

    print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()
