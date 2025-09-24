import pytest
from flask import g, session

def test_login_page_loads(client):
    """Test that the login page loads correctly."""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b"Login" in response.data
    assert b"Email" in response.data
    assert b"Password" in response.data

def test_signup_page_loads(client):
    """Test that the signup page loads correctly."""
    response = client.get('/auth/signup')
    assert response.status_code == 200
    assert b"Sign Up" in response.data
    assert b"Email" in response.data
    assert b"Password" in response.data

def test_successful_login(client, mocker):
    """Test a successful login with a mocked password verification."""
    # Mock the environment variable for the API key
    mocker.patch.dict('os.environ', {'FIREBASE_WEB_API_KEY': 'test_api_key'})

    # Mock the requests.post call
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        'localId': 'test_user_id',
        'email': 'test@example.com'
    }

    response = client.post('/auth/login', data={'email': 'test@example.com', 'password': 'password'})

    assert response.status_code == 302
    # The redirect should go to the profile page, which is at the root of the profile blueprint
    assert response.location == '/profile/'

    with client.session_transaction() as sess:
        assert sess['user_id'] == 'test_user_id'
