import logging
from flask import jsonify, request, current_app, session
from . import bp
from ..utils import login_required, SESSION_USER_ID

@bp.route('/share/<reflection_id>', methods=['POST'])
@login_required
def share(reflection_id):
    """Learner shares a reflection with a mentor."""
    db = current_app.config.get('DB')
    if not db or current_app.config.get('BYPASS_EXTERNAL_SERVICES'):
        return jsonify({"error": "Database service is not available."}), 500

    mentor_id = request.json.get('mentor_id')
    if not mentor_id:
        return jsonify({"error": "Mentor ID is required."}), 400

    learner_id = session[SESSION_USER_ID]

    try:
        # Verify that the learner and mentor are connected
        connections_ref = db.collection('mentor_connections')
        query = connections_ref.where('learner_id', '==', learner_id).where('mentor_id', '==', mentor_id).where('status', '==', 'accepted').limit(1)
        if not list(query.stream()):
            return jsonify({"error": "You are not connected with this mentor."}), 403

        # For now, we'll just create a record that the reflection was shared.
        # In a real implementation, we would also copy or reference the reflection data.
        shared_reflection_data = {
            'reflection_id': reflection_id,
            'learner_id': learner_id,
            'mentor_id': mentor_id,
            'shared_at': db.SERVER_TIMESTAMP,
            'viewed': False
        }
        db.collection('shared_reflections').add(shared_reflection_data)

        return jsonify({"status": "shared"}), 200

    except Exception as e:
        logging.error(f"Error sharing reflection: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500
