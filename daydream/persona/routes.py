from collections import Counter
from flask import render_template, request, redirect, url_for, session
from . import bp
from .models import PersonaService

@bp.route('/quiz')
def quiz():
    """Displays the Persona Quiz."""
    persona_service = PersonaService()
    dilemmas = persona_service.get_all_dilemmas()
    return render_template('persona/quiz.html', dilemmas=dilemmas)

@bp.route('/reveal', methods=['POST'])
def reveal():
    """Processes the Persona Quiz results and reveals the user's archetype."""
    # Tally the archetype choices
    archetype_counts = Counter(request.form.values())
    # Determine the primary archetype
    primary_archetype_id = archetype_counts.most_common(1)[0][0]

    # Get the archetype details
    persona_service = PersonaService()
    archetypes = {archetype['id']: archetype for archetype in persona_service.get_all_archetypes()}
    primary_archetype = archetypes.get(primary_archetype_id)

    # Store the user's archetype in the session
    session['archetype'] = primary_archetype

    return render_template('persona/reveal.html', archetype=primary_archetype)
