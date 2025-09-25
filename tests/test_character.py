import pytest
from flask import session
from unittest.mock import MagicMock

def test_character_template_manager_page_loads_for_instructor(client, mocker):
    """Test that the character template manager page loads for an instructor."""
    # Mock the Firestore call to return an instructor profile with an organization
    mock_profile = MagicMock()
    mock_profile.exists = True
    mock_profile.to_dict.return_value = {'role': 'instructor', 'organization_id': 'test_org'}

    mock_db = MagicMock()
    mock_db.collection.return_value.document.return_value.get.return_value = mock_profile
    mocker.patch('daydream.character.routes.db', mock_db)
    mocker.patch('daydream.utils.db', mock_db)

    with client.session_transaction() as sess:
        sess['user_id'] = 'test_instructor'

    # Mock os.listdir to prevent FileNotFoundError
    mocker.patch('os.listdir', return_value=[])

    response = client.get('/character/templates')
    assert response.status_code == 200
    assert b"Character Template Manager" in response.data

def test_character_template_manager_page_redirects_for_student(client, mocker):
    """Test that the character template manager page redirects for a student."""
    # Mock the Firestore call to return a student profile
    mock_profile = MagicMock()
    mock_profile.exists = True
    mock_profile.to_dict.return_value = {'role': 'student'}

    mock_db = MagicMock()
    mock_db.collection.return_value.document.return_value.get.return_value = mock_profile
    mocker.patch('daydream.utils.db', mock_db)

    with client.session_transaction() as sess:
        sess['user_id'] = 'test_student'

    response = client.get('/character/templates')
    assert response.status_code == 302
    assert b'Redirecting...' in response.data