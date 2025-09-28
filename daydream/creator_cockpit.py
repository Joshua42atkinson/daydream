from flask import Blueprint, render_template, g, redirect, url_for

bp = Blueprint('creator_cockpit', __name__, url_prefix='/cockpit')

@bp.route('/')
def cockpit():
    """Renders the Creator Cockpit view."""
    state_manager = g.state_manager
    if state_manager.get_current_state() != 'CreatorCockpit':
        # If the user is not in the correct state, redirect to the main menu.
        # This prevents accessing pages out of state.
        return redirect(url_for('main_menu.menu'))

    available_tools = state_manager.get_available_tools()
    return render_template('creator_cockpit.html', tools=available_tools)