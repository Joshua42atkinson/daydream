import os
from flask import Blueprint, render_template, g, redirect, url_for, current_app

bp = Blueprint('system_diagnostics', __name__, url_prefix='/diagnostics')

def get_external_services_status():
    """
    Checks the status of external services by reading from the app context.
    """
    # These services are initialized in create_app and stored in the app config.
    bypassed = current_app.config.get('BYPASS_EXTERNAL_SERVICES', False)
    firebase_app_instance = current_app.config.get('FIREBASE_APP')
    model_instance = current_app.config.get('MODEL')

    status = {'bypassed': bypassed}

    # Check Firebase status
    if firebase_app_instance:
        status['firebase'] = {
            'status': 'Connected',
            'project_id': firebase_app_instance.project_id
        }
    elif bypassed:
        status['firebase'] = {'status': 'Bypassed'}
    else:
        status['firebase'] = {'status': 'Error', 'reason': 'Firebase app object not found or failed to initialize.'}

    # Check Google AI status
    if model_instance:
        # The model object itself doesn't have a public name property, so we hardcode it.
        status['google_ai'] = {'status': 'Connected', 'model': 'gemini-1.5-flash-latest'}
    elif bypassed:
        status['google_ai'] = {'status': 'Bypassed'}
    else:
        status['google_ai'] = {'status': 'Error', 'reason': 'Google AI model not initialized.'}

    return status

def get_vision_alignment():
    """Compares the current implementation with the long-term project vision."""
    return [
        {
            'component': 'Core Language',
            'current': 'Python',
            'vision': 'Rust',
            'aligned': False
        },
        {
            'component': 'Application Framework',
            'current': 'Flask (Web App)',
            'vision': 'Tauri (Desktop App)',
            'aligned': False
        },
        {
            'component': 'AI/ML Inference',
            'current': 'Cloud (Google Gemini)',
            'vision': 'Local (Candle)',
            'aligned': False
        },
        {
            'component': 'Database & Auth',
            'current': 'Cloud (Firebase)',
            'vision': 'Local',
            'aligned': False
        },
        {
            'component': 'State Management',
            'current': 'In-Memory Python',
            'vision': 'Bevy ECS (Rust)',
            'aligned': False
        }
    ]

@bp.route('/')
def diagnostics_view():
    """Renders the System Diagnostics view with detailed status information."""
    state_manager = g.state_manager
    if state_manager.get_current_state() != 'SystemDiagnostics':
        return redirect(url_for('main_menu.menu'))

    # Gather all diagnostic information
    diagnostics_data = {
        'app_mode': 'Debug' if current_app.debug else 'Production',
        'services': get_external_services_status(),
        'vision_alignment': get_vision_alignment()
    }

    # The old implementation passed 'tools', which the new template won't use.
    # We pass the new, structured 'diagnostics' dictionary instead.
    return render_template('system_diagnostics.html', diagnostics=diagnostics_data)