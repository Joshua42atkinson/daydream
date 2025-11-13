import pytest
from unittest.mock import MagicMock

def test_connect_request(client, app):
    """Test sending a connection request to a mentor."""
    with client.session_transaction() as sess:
        sess['user_id'] = 'learner1'

    app.config['BYPASS_EXTERNAL_SERVICES'] = False
    mock_db = app.config['DB']

    # Mock finding the mentor
    mock_mentor = MagicMock()
    mock_mentor.id = 'mentor1'
    mock_db.collection.return_value.where.return_value.limit.return_value.stream.return_value = [mock_mentor]

    # Mock checking for existing connection
    mock_db.collection.return_value.where.return_value.where.return_value.stream.return_value = []

    response = client.post('/api/mentor/connect', json={'mentor_username': 'mentor@example.com'})
    assert response.status_code == 201
    assert response.json['status'] == 'pending'

def test_accept_connection(client, app):
    """Test a mentor accepting a connection request."""
    with client.session_transaction() as sess:
        sess['user_id'] = 'mentor1'

    app.config['BYPASS_EXTERNAL_SERVICES'] = False
    mock_db = app.config['DB']

    mock_doc = MagicMock()
    mock_doc.reference.update = MagicMock()

    mock_db.collection.return_value.where.return_value.where.return_value.where.return_value.limit.return_value.stream.return_value = [mock_doc]

    response = client.put('/api/mentor/accept/learner1')
    assert response.status_code == 200
    assert response.json['status'] == 'accepted'

def test_share_reflection(client, app):
    """Test sharing a reflection with a mentor."""
    with client.session_transaction() as sess:
        sess['user_id'] = 'learner1'

    app.config['BYPASS_EXTERNAL_SERVICES'] = False
    mock_db = app.config['DB']

    # Simulate an accepted connection
    mock_db.collection.return_value.where.return_value.where.return_value.where.return_value.limit.return_value.stream.return_value = [MagicMock()]

    response = client.post('/api/reflection/share/reflection1', json={'mentor_id': 'mentor1'})
    assert response.status_code == 200
    assert response.json['status'] == 'shared'

def test_mentor_inbox(client, app):
    """Test fetching the mentor's inbox."""
    with client.session_transaction() as sess:
        sess['user_id'] = 'mentor1'

    app.config['BYPASS_EXTERNAL_SERVICES'] = False
    mock_db = app.config['DB']

    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = {'reflection_id': 'reflection1', 'learner_id': 'learner1'}

    mock_db.collection.return_value.where.return_value.order_by.return_value.stream.return_value = [mock_doc]

    response = client.get('/api/mentor/inbox')
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['reflection_id'] == 'reflection1'
