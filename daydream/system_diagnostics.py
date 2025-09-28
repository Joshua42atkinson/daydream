from flask import Blueprint, render_template, g, redirect, url_for

bp = Blueprint('system_diagnostics', __name__, url_prefix='/diagnostics')

@bp.route('/')
def diagnostics_view():
    """Renders the System Diagnostics view."""
    state_manager = g.state_manager
    if state_manager.get_current_state() != 'SystemDiagnostics':
        return redirect(url_for('main_menu.menu'))

    available_tools = state_manager.get_available_tools()
    return render_template('system_diagnostics.html', tools=available_tools)