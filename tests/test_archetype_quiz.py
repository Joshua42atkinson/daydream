import pytest
from unittest.mock import patch

def test_archetype_quiz_loads(client):
    """Test that the archetype quiz page loads correctly."""
    with client.session_transaction() as sess:
        sess['user_id'] = 'test_user'
    response = client.get('/character/create')
    assert response.status_code == 200
    assert b"Choose Your Path" in response.data

def test_archetype_quiz_submission(client):
    """Test submitting the archetype quiz and revealing the archetype."""
    with client.session_transaction() as sess:
        sess['user_id'] = 'test_user'

    with patch('daydream.character.routes.ARCHETYPE_QUIZ_DATA', {
        "dilemmas": [
            {"id": "dilemma_1", "text": "Dilemma 1", "choices": [{"text": "A", "archetype": "Hero"}, {"text": "B", "archetype": "Sage"}]},
            {"id": "dilemma_2", "text": "Dilemma 2", "choices": [{"text": "A", "archetype": "Hero"}, {"text": "B", "archetype": "Jester"}]}
        ],
        "archetypes": {
            "Hero": {"description": "Heroic", "stats": {"Courage": 2}},
            "Sage": {"description": "Wise", "stats": {"Intelligence": 2}},
            "Jester": {"description": "Witty", "stats": {"Eloquence": 2}}
        }
    }):
        response = client.post('/character/create', data={
            'creation_stage': 'submit_quiz',
            'name': 'Test Hero',
            'dilemma_1': 'Hero',
            'dilemma_2': 'Hero'
        })
        assert response.status_code == 200
        assert b"Your Archetype is the Hero" in response.data
        assert b"Courage: +2" in response.data

def test_character_finalization(client):
    """Test finalizing a character after the archetype quiz."""
    with client.session_transaction() as sess:
        sess['user_id'] = 'test_user'
        sess['new_char_details'] = {'name': 'Test Sage', 'archetype': 'Sage'}

    with patch('daydream.character.routes.save_character_data') as mock_save:
        mock_save.return_value = 'new_char_id'
        with patch('daydream.character.routes.ARCHETYPE_QUIZ_DATA', {
            "archetypes": {
                "Sage": {"description": "Wise", "stats": {"Intelligence": 2}}
            }
        }):
            response = client.post('/character/create', data={'creation_stage': 'finalize'})
            assert response.status_code == 302
            mock_save.assert_called_once()
