from flask import Blueprint, render_template, g, redirect, url_for
from .vocabulary.core import load_vocabulary_from_file

bp = Blueprint('creator_cockpit', __name__, url_prefix='/cockpit')

@bp.route('/')
def cockpit():
    """Renders the Creator Cockpit view."""
    state_manager = g.state_manager
    if state_manager.get_current_state() != 'CreatorCockpit':
        return redirect(url_for('main_menu.menu'))

    available_tools = state_manager.get_available_tools()

    # Load vocabulary for the contextual tagger
    try:
        vocab_data = load_vocabulary_from_file()
        vocab_words = list(vocab_data.keys())
    except Exception:
        vocab_words = []

    return render_template('creator_cockpit.html',
                           tools=available_tools,
                           vocab_words=vocab_words)
