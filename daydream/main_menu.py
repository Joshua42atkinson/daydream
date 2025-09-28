import functools
from flask import (
    Blueprint, g, redirect, render_template, session, url_for
)

bp = Blueprint('main_menu', __name__, url_prefix='/main_menu')

@bp.route('/')
def menu():
    """
    Renders the main menu for the application.

    This view acts as the central hub when the application is in the
    'MainMenu' state. It retrieves the available tools for this state
    from the StateManager and passes them to the template for rendering.
    """
    # The state manager is attached to the 'g' object in the before_request hook.
    state_manager = g.state_manager

    # Ensure the user is in the correct state to view this page.
    # While the entry point logic should handle this, it's good practice
    # to check.
    current_state = state_manager.get_current_state()
    if current_state != 'MainMenu':
        # If the user is somehow in the wrong state, redirect them to the
        # appropriate view or a generic handler. For now, we'll redirect
        # back to the main menu, which will enforce the correct state.
        # A more sophisticated app might have a central routing function.
        return redirect(url_for('main_menu.menu'))

    # Get the tools available in the MainMenu state.
    available_tools = state_manager.get_available_tools('MainMenu')

    return render_template('main_menu.html', tools=available_tools)