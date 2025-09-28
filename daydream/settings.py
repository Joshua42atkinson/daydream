from flask import Blueprint, render_template, g, redirect, url_for

bp = Blueprint('settings', __name__, url_prefix='/settings')

@bp.route('/')
def settings_view():
    """Renders the Settings view."""
    state_manager = g.state_manager
    if state_manager.get_current_state() != 'Settings':
        return redirect(url_for('main_menu.menu'))

    available_tools = state_manager.get_available_tools()
    return render_template('settings.html', tools=available_tools)