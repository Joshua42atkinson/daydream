import pytest
from flask import session

def test_character_template_manager_page_loads(client):
    """Test that the character template manager page loads correctly."""
    # To bypass the @login_required decorator, we can set a user_id in the session
    with client.session_transaction() as sess:
        sess['user_id'] = 'test_user'

    response = client.get('/character/templates')
    assert response.status_code == 200
    assert b"Character Template Manager" in response.data
    assert b"Race Templates" in response.data
    assert b"Class Templates" in response.data
    assert b"Philosophy Templates" in response.data