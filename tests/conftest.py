import pytest
from daydream import create_app

@pytest.fixture
def app(mocker):
    """Create and configure a new app instance for each test."""

    # Since we've refactored to use the app context, we don't need to patch
    # the module-level variables. Instead, we can let the app be created
    # and then mock the config values.
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test',
        'BYPASS_EXTERNAL_SERVICES': True, # Ensure services are bypassed
    })
    app.config['SERVER_NAME'] = 'localhost'
    app.config['APPLICATION_ROOT'] = '/'

    # You can still mock if needed, for example, if a function specifically
    # needs to interact with a mock object.
    with app.app_context():
        mocker.patch.dict(app.config, {
            'DB': mocker.MagicMock(),
            'AUTH_CLIENT': mocker.MagicMock(),
            'MODEL': mocker.MagicMock()
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
