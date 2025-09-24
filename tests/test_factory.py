def test_config(app):
    """Test create_app with test config."""
    assert app.testing

def test_hello(client):
    # This test is a placeholder. In a real app, you might test a health check endpoint.
    response = client.get('/')
    assert response.status_code == 302 # Should redirect

def test_index_redirect(client):
    """Test that the index route redirects to the login page."""
    response = client.get('/')
    # Check that the response is a redirect
    assert response.status_code == 302
    # Check that the redirect location is the login page
    assert 'auth/login' in response.headers['Location']
