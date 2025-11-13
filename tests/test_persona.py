from unittest.mock import MagicMock
from collections import Counter
from flask import session
from daydream.persona.models import PersonaService

def test_quiz_route(client, mocker):
    """
    Tests that the quiz route returns the quiz page.
    """
    # Patch the PersonaService class in the routes module where it is used.
    mock_persona_service_class = mocker.patch('daydream.persona.routes.PersonaService', autospec=True)

    # Configure the instance that will be created when PersonaService() is called in the route.
    mock_instance = mock_persona_service_class.return_value
    mock_instance.get_all_dilemmas.return_value = [
        {
            'id': 'dilemma1',
            'text': 'Dilemma 1',
            'choices': [
                {'id': 'choice1', 'text': 'Choice 1', 'archetype_id': 'archetype1'},
                {'id': 'choice2', 'text': 'Choice 2', 'archetype_id': 'archetype2'},
            ]
        }
    ]

    response = client.get('/persona/quiz')
    assert response.status_code == 200
    assert b'The Persona Quiz' in response.data

def test_reveal_route(client, mocker):
    """
    Tests that the reveal route correctly processes the quiz results.
    """
    # Patch the PersonaService class
    mock_persona_service_class = mocker.patch('daydream.persona.routes.PersonaService', autospec=True)

    # Configure the mock instance
    mock_instance = mock_persona_service_class.return_value
    mock_instance.get_all_archetypes.return_value = [
        {'id': 'archetype1', 'name': 'Hero', 'description': 'Brave warrior', 'stat_buffs': {'Courage': 2}},
        {'id': 'archetype2', 'name': 'Sage', 'description': 'Wise observer', 'stat_buffs': {'Intelligence': 2}},
    ]

    # Simulate a POST request with quiz results
    with client.session_transaction() as sess:
        sess['user_id'] = 'test_user'
    response = client.post('/persona/reveal', data={'dilemma1': 'archetype1'})

    # Check the response
    assert response.status_code == 200
    assert b'Your Archetype is: Hero' in response.data

    # Check that the archetype is stored in the session
    with client.session_transaction() as sess:
        assert sess['archetype']['name'] == 'Hero'

def test_persona_service(app, mocker):
    """
    Tests the PersonaService class within an application context.
    """
    # Use the app context to make current_app available
    with app.app_context():
        # Mock the Firestore client and set it in the app config
        mock_db = MagicMock()
        app.config['DB'] = mock_db

        # Mock the collections and documents
        mock_archetypes_collection = MagicMock()
        mock_dilemmas_collection = MagicMock()

        # Use a side_effect to return the correct mock collection based on the name
        def collection_side_effect(name):
            if name == 'archetypes':
                return mock_archetypes_collection
            elif name == 'dilemmas':
                return mock_dilemmas_collection
            return MagicMock()
        mock_db.collection.side_effect = collection_side_effect

        # Mock the archetype documents
        mock_archetype_doc1 = MagicMock()
        mock_archetype_doc1.id = 'archetype1'
        mock_archetype_doc1.to_dict.return_value = {'name': 'Hero'}
        mock_archetype_doc2 = MagicMock()
        mock_archetype_doc2.id = 'archetype2'
        mock_archetype_doc2.to_dict.return_value = {'name': 'Sage'}
        mock_archetypes_collection.stream.return_value = [mock_archetype_doc1, mock_archetype_doc2]

        # Mock the dilemma documents
        mock_dilemma_doc = MagicMock()
        mock_dilemma_doc.id = 'dilemma1'
        mock_dilemma_doc.to_dict.return_value = {'text': 'Dilemma 1'}
        mock_dilemmas_collection.stream.return_value = [mock_dilemma_doc]

        # Mock the choice documents
        mock_choices_collection = MagicMock()
        mock_dilemma_doc.reference.collection.return_value = mock_choices_collection
        mock_choice_doc1 = MagicMock()
        mock_choice_doc1.id = 'choice1'
        mock_choice_doc1.to_dict.return_value = {'text': 'Choice 1', 'archetype_id': 'archetype1'}
        mock_choice_doc2 = MagicMock()
        mock_choice_doc2.id = 'choice2'
        mock_choice_doc2.to_dict.return_value = {'text': 'Choice 2', 'archetype_id': 'archetype2'}
        mock_choices_collection.stream.return_value = [mock_choice_doc1, mock_choice_doc2]

        # Test the PersonaService - it will now use the mock_db from app.config
        persona_service = PersonaService()
        archetypes = persona_service.get_all_archetypes()
        dilemmas = persona_service.get_all_dilemmas()

        assert len(archetypes) == 2
        assert archetypes[0]['name'] == 'Hero'
        assert len(dilemmas) == 1
        assert dilemmas[0]['text'] == 'Dilemma 1'
        assert len(dilemmas[0]['choices']) == 2
        assert dilemmas[0]['choices'][0]['text'] == 'Choice 1'
