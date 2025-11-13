import os
from daydream import create_app

# Create the Flask app instance using the factory
app = create_app()

if __name__ == '__main__':
    # Configuration for running the Flask app
    # These are now the primary way to configure the run command,
    # overriding any defaults inside create_app if necessary.
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_RUN_PORT', 8080))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']

    # The reloader should be managed by the `flask run` command,
    # but we can enable it here for direct `python run.py` execution.
    use_reloader = debug_mode

    print("--- Starting Daydream Server (Refactored) ---")
    print(f" Mode: {'Debug' if debug_mode else 'Production'}")
    print(f" Host: {host}")
    print(f" Port: {port}")
    print(f"-----------------------------------")

    # Use app.run() for direct execution.
    # For production, Gunicorn should be used and pointed to this `app` object.
    # Example: gunicorn --bind 0.0.0.0:8080 "run:app"
    try:
        app.run(debug=debug_mode, host=host, port=port, use_reloader=use_reloader)
    except Exception as e:
        print(f"Error starting server: {e}")
