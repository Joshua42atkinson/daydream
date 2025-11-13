from flask import current_app

class PersonaService:
    """
    A service for interacting with the Persona Engine's Firestore collections.
    If the database is not available (i.e., BYPASS_EXTERNAL_SERVICES is True),
    it returns hardcoded mock data for verification and testing.
    """
    def __init__(self):
        self.db = current_app.config.get('DB')
        if self.db:
            self.archetypes_collection = self.db.collection('archetypes')
            self.dilemmas_collection = self.db.collection('dilemmas')

    def get_all_archetypes(self):
        """Retrieves all archetypes from the database or returns mock data."""
        if not self.db:
            # Return mock data if external services are bypassed
            return [
                {'id': 'archetype1', 'name': 'Hero', 'description': 'You are a brave and courageous warrior, always ready to stand up for what is right.', 'stat_buffs': {'Courage': 2, 'Strength': 1}},
                {'id': 'archetype2', 'name': 'Sage', 'description': 'You are a wise and knowledgeable observer, always seeking to understand the world around you.', 'stat_buffs': {'Intelligence': 2, 'Perception': 1}},
                {'id': 'archetype3', 'name': 'Jester', 'description': 'You are a witty and clever trickster, always finding creative solutions to problems.', 'stat_buffs': {'Eloquence': 2, 'Agility': 1}},
                {'id': 'archetype4', 'name': 'Caregiver', 'description': 'You are a compassionate and empathetic soul, always looking to help others.', 'stat_buffs': {'Empathy': 2, 'Wisdom': 1}},
            ]

        archetypes = []
        for doc in self.archetypes_collection.stream():
            archetype = doc.to_dict()
            archetype['id'] = doc.id
            archetypes.append(archetype)
        return archetypes

    def get_all_dilemmas(self):
        """Retrieves all dilemmas and their choices from the database or returns mock data."""
        if not self.db:
            # Return mock data if external services are bypassed
            return [
                {
                    'id': 'dilemma1', 'text': 'A bully is harassing a merchant in the town square. What do you do?',
                    'choices': [
                        {'id': 'c1', 'text': 'Confront the bully directly.', 'archetype_id': 'archetype1'},
                        {'id': 'c2', 'text': 'Find a clever way to distract the bully.', 'archetype_id': 'archetype3'},
                        {'id': 'c3', 'text': 'Observe to understand why the bully is angry.', 'archetype_id': 'archetype2'},
                        {'id': 'c4', 'text': 'Comfort the merchant after the bully leaves.', 'archetype_id': 'archetype4'},
                    ]
                },
                {
                    'id': 'dilemma2', 'text': 'You find a mysterious, locked chest in a dark forest. What is your approach?',
                    'choices': [
                        {'id': 'c5', 'text': 'Try to force the lock open.', 'archetype_id': 'archetype1'},
                        {'id': 'c6', 'text': 'Look for a hidden key or a clever way to open it without force.', 'archetype_id': 'archetype3'},
                        {'id': 'c7', 'text': 'Examine the chest for clues about its origin and purpose.', 'archetype_id': 'archetype2'},
                        {'id': 'c8', 'text': 'Consider who might have left the chest and why, ensuring it’s safe to open.', 'archetype_id': 'archetype4'},
                    ]
                },
                {
                    'id': 'dilemma3', 'text': 'You are offered a powerful but dangerous artifact. What do you do?',
                    'choices': [
                        {'id': 'c9', 'text': 'Accept the artifact, believing you can control its power for good.', 'archetype_id': 'archetype1'},
                        {'id': 'c10', 'text': 'Accept the artifact, intrigued by its potential for mischief and clever uses.', 'archetype_id': 'archetype3'},
                        {'id': 'c11', 'text': 'Decline the artifact, wary of its potential to corrupt and disrupt.', 'archetype_id': 'archetype2'},
                        {'id': 'c12', 'text': 'Decline the artifact, concerned about the harm it could cause to you and others.', 'archetype_id': 'archetype4'},
                    ]
                },
            ]

        dilemmas = []
        for doc in self.dilemmas_collection.stream():
            dilemma = doc.to_dict()
            dilemma['id'] = doc.id
            choices_collection = doc.reference.collection('choices')
            dilemma['choices'] = []
            for choice_doc in choices_collection.stream():
                choice = choice_doc.to_dict()
                choice['id'] = choice_doc.id
                dilemma['choices'].append(choice)
            dilemmas.append(dilemma)
        return dilemmas

class Archetype:
    """Represents a player archetype (e.g., Sage, Hero)."""
    def __init__(self, name, description, stat_buffs):
        self.name = name
        self.description = description
        self.stat_buffs = stat_buffs

    def to_dict(self):
        return {'name': self.name, 'description': self.description, 'stat_buffs': self.stat_buffs}

class Dilemma:
    """Represents a narrative dilemma in the Persona Quiz."""
    def __init__(self, text):
        self.text = text

    def to_dict(self):
        return {'text': self.text}

class Choice:
    """Represents a choice within a dilemma."""
    def __init__(self, text, archetype_id):
        self.text = text
        self.archetype_id = archetype_id

    def to_dict(self):
        return {'text': self.text, 'archetype_id': self.archetype_id}
