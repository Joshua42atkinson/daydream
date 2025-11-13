import pytest
from flask import session

def test_vocabulary_manager_page_loads(client):
    """Test that the vocabulary manager page loads correctly."""
    # To bypass the @login_required decorator, we can set a user_id in the session
    with client.session_transaction() as sess:
        sess['user_id'] = 'test_user'

    response = client.get('/vocabulary/')
    assert response.status_code == 200
    assert b"Vocabulary Manager" in response.data
    assert b"Vocabulary Bank Editor" in response.data
    assert b"AI Vocabulary Brainstormer" in response.data