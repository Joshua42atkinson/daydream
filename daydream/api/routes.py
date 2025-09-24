from flask import jsonify, request, session
from . import bp
from ..utils import get_ai_response, login_required
from ..ethics.gateway import analyze_content

@bp.route('/hello')
def hello():
    """A simple test endpoint for the API."""
    return jsonify({'message': 'Hello, API!'})

@bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """
    Handles chat interactions from a UI like Open WebUI.
    This endpoint is the bridge between the frontend and the game's AI.
    """
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Invalid request format. "message" field is required.'}), 400

    user_message = data['message']

    # 1. Analyze user's input with the Ethical Gateway
    safety_check = analyze_content(user_message)
    if not safety_check.get('safe'):
        return jsonify({
            'reply': f"I cannot process this request. Reason: {safety_check.get('reason', 'Content policy violation.')}"
        }), 200 # Return 200 so the UI displays the message

    # 2. Prepare context and get AI response
    # In a real implementation, we'd pull character/game state from the db
    context = {'user_input': user_message}
    ai_response_data = get_ai_response("GENERAL_CHAT", context)

    # 3. Process and analyze the AI's output
    if isinstance(ai_response_data, dict) and 'error' not in ai_response_data:
        ai_message = ai_response_data.get('response_text', "I don't have a response for that.")

        # Analyze AI output with the Ethical Gateway
        ai_safety_check = analyze_content(ai_message)
        if not ai_safety_check.get('safe'):
            return jsonify({'reply': "The generated response was blocked for safety reasons."}), 200

        # 4. Send successful response back to the UI
        return jsonify({'reply': ai_message})
    else:
        # Handle errors from the AI service
        error_reason = ai_response_data.get('reason', 'Unknown AI error') if isinstance(ai_response_data, dict) else 'AI communication failure'
        return jsonify({'reply': f"Sorry, I encountered an error: {error_reason}"}), 200