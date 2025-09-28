from flask import Blueprint, g, redirect, url_for, flash, session

bp = Blueprint('tool_handlers', __name__, url_prefix='/handle_tool')

@bp.route('/<tool_id>')
def handle_tool(tool_id):
    """
    Handles a tool action triggered from the UI.

    This route looks up the tool by its ID in the current state's available
    tools, performs the specified state transition, and redirects the user
    to the new state's corresponding view.
    """
    state_manager = g.state_manager
    current_state = state_manager.get_current_state()
    available_tools = state_manager.get_available_tools(current_state)

    # Find the tool definition that matches the provided tool_id
    tool_def = next((tool for tool in available_tools if tool['id'] == tool_id), None)

    if not tool_def:
        flash(f"Invalid action: Tool '{tool_id}' not available in state '{current_state}'.")
        # Redirect back to the view for the current state.
        # This requires a mapping from state name to view function.
        # For now, we'll redirect to the main menu as a fallback.
        return redirect(url_for('main_menu.menu'))

    # Get the target state for a successful action
    next_state = tool_def.get('on_success_transition_to')

    if not next_state:
        flash(f"Configuration error: Tool '{tool_id}' has no defined transition state.")
        return redirect(url_for('main_menu.menu'))

    # Perform the state transition
    state_manager.set_state(next_state)

    # Redirect to the appropriate view based on the new state
    if next_state == 'CreatorCockpit':
        return redirect(url_for('creator_cockpit.cockpit'))
    elif next_state == 'Settings':
        return redirect(url_for('settings.settings_view'))
    elif next_state == 'SystemDiagnostics':
        return redirect(url_for('system_diagnostics.diagnostics_view'))
    elif next_state == 'TERMINATE':
        session.clear()
        flash("You have been logged out.")
        return redirect(url_for('auth.login'))
    else:
        # Fallback for any other states that might be added
        flash(f"Transitioned to '{next_state}', but no view is configured.")
        return redirect(url_for('main_menu.menu'))