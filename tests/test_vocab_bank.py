import pytest
from unittest.mock import patch, mock_open

def test_create_vocab_entry(client):
    """Test creating a new vocabulary entry."""
    with client.session_transaction() as sess:
        sess['user_id'] = 'creator1'

    mock_data = {
        "analyze": {
            "definition": "To examine in detail...",
            "sublist": 1
        }
    }

    m = mock_open(read_data=str(mock_data))
    with patch('builtins.open', m):
        with patch('json.dump') as mock_dump:
            response = client.post('/vocabulary/create', data={
                'word': 'approach',
                'definition': 'To come near...',
                'example_sentence': 'The cat will approach...',
                'genai_image_prompt': 'A cat stalking...',
                'genai_audio_prompt': 'A soft voice...',
                'sublist': '1'
            }, follow_redirects=True)

            assert response.status_code == 200
            mock_dump.assert_called_once()
            # More detailed assertions can be added here to check the content of the dump

def test_edit_vocab_entry(client):
    """Test editing an existing vocabulary entry."""
    with client.session_transaction() as sess:
        sess['user_id'] = 'creator1'

    mock_data = {
        "analyze": {
            "definition": "To examine in detail...",
            "sublist": 1
        }
    }

    m = mock_open(read_data=str(mock_data))
    with patch('builtins.open', m):
        with patch('json.dump') as mock_dump:
            response = client.post('/vocabulary/edit/analyze', data={
                'original_word': 'analyze',
                'word': 'analyze',
                'definition': 'A new definition',
                'example_sentence': 'A new sentence',
                'genai_image_prompt': 'A new image prompt',
                'genai_audio_prompt': 'A new audio prompt',
                'sublist': '2'
            }, follow_redirects=True)

            assert response.status_code == 200
            mock_dump.assert_called_once()
            # More detailed assertions can be added here
