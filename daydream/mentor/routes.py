import logging
from flask import jsonify, request, current_app, session
from . import bp
from ..utils import login_required, SESSION_USER_ID

@bp.route('/connect', methods=['POST'])
@login_required
def connect():
    """Learner requests a connection with a mentor."""
    db = current_app.config.get('DB')
    if not db or current_app.config.get('BYPASS_EXTERNAL_SERVICES'):
        return jsonify({"error": "Database service is not available."}), 500

    mentor_username = request.json.get('mentor_username')
    if not mentor_username:
        return jsonify({"error": "Mentor username is required."}), 400

    learner_id = session[SESSION_USER_ID]

    try:
        # Find mentor by email (assuming username is email for now)
        users_ref = db.collection('player_profiles')
        query = users_ref.where('email', '==', mentor_username).limit(1)
        mentors = list(query.stream())

        if not mentors:
            return jsonify({"error": "Mentor not found."}), 404

        mentor = mentors[0]
        mentor_id = mentor.id

        if learner_id == mentor_id:
            return jsonify({"error": "You cannot connect with yourself."}), 400

        # Check if a connection already exists
        connections_ref = db.collection('mentor_connections')
        existing_query = connections_ref.where('learner_id', '==', learner_id).where('mentor_id', '==', mentor_id)
        if len(list(existing_query.stream())) > 0:
             return jsonify({"error": "Connection request already sent or exists."}), 409

        # Create a new connection request
        connection_data = {
            'learner_id': learner_id,
            'mentor_id': mentor_id,
            'status': 'pending',
            'requested_at': db.SERVER_TIMESTAMP
        }
        connections_ref.add(connection_data)

        return jsonify({"status": "pending"}), 201

    except Exception as e:
        logging.error(f"Error creating mentor connection: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

@bp.route('/inbox', methods=['GET'])
@login_required
def inbox():
    """Fetches all reflections shared with the current mentor."""
    db = current_app.config.get('DB')
    if not db or current_app.config.get('BYPASS_EXTERNAL_SERVICES'):
        return jsonify({"error": "Database service is not available."}), 500

    mentor_id = session[SESSION_USER_ID]

    try:
        shared_reflections_ref = db.collection('shared_reflections')
        query = shared_reflections_ref.where('mentor_id', '==', mentor_id).order_by('shared_at', direction='DESCENDING')

        reflections = []
        for doc in query.stream():
            reflection_data = doc.to_dict()
            # Convert timestamp to ISO 8601 format string
            if 'shared_at' in reflection_data and hasattr(reflection_data['shared_at'], 'isoformat'):
                reflection_data['shared_at'] = reflection_data['shared_at'].isoformat()
            reflections.append(reflection_data)

        return jsonify(reflections), 200

    except Exception as e:
        logging.error(f"Error fetching mentor inbox: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500

@bp.route('/accept/<learner_id>', methods=['PUT'])
@login_required
def accept_connection(learner_id):
    """Mentor accepts a connection request from a learner."""
    db = current_app.config.get('DB')
    if not db or current_app.config.get('BYPASS_EXTERNAL_SERVICES'):
        return jsonify({"error": "Database service is not available."}), 500

    mentor_id = session[SESSION_USER_ID]

    try:
        # Find the connection request
        connections_ref = db.collection('mentor_connections')
        query = connections_ref.where('learner_id', '==', learner_id).where('mentor_id', '==', mentor_id).where('status', '==', 'pending').limit(1)
        requests = list(query.stream())

        if not requests:
            return jsonify({"error": "Connection request not found or already accepted."}), 404

        request_doc = requests[0]
        request_doc.reference.update({
            'status': 'accepted',
            'accepted_at': db.SERVER_TIMESTAMP
        })

        return jsonify({"status": "accepted"}), 200

    except Exception as e:
        logging.error(f"Error accepting mentor connection: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred."}), 500
