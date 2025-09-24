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
