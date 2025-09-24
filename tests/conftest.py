import pytest
from daydream import create_app

@pytest.fixture
def app(mocker):
    """Create and configure a new app instance for each test."""

    # Mock the external clients before the app is created
    mocker.patch('daydream.db', return_value=mocker.MagicMock())
    mocker.patch('daydream.auth_client', return_value=mocker.MagicMock())
    mocker.patch('daydream.model', return_value=mocker.MagicMock())

    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test',
    })

    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()
