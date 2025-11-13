import os
import json
import logging
from flask import render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.utils import secure_filename
from . import bp
from .core import load_vocabulary_from_file

# Define the path to the vocabulary data directory
VOCAB_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
ACTIVE_VOCAB_FILE = "academic_word_list.json" # Make this configurable later

@bp.route('/')
def vocabulary_manager():
    from ..utils import login_required
    @login_required
    def _vocabulary_manager():
        """Renders the main vocabulary management page."""
        try:
            vocab_data = load_vocabulary_from_file(ACTIVE_VOCAB_FILE)
        except Exception as e:
            logging.error(f"Error loading vocabulary file {ACTIVE_VOCAB_FILE}: {e}")
            flash("Could not load the active vocabulary file.", "error")
            vocab_data = {}

        return render_template('vocabulary_manager.html',
                               vocab_data=vocab_data,
                               active_file=ACTIVE_VOCAB_FILE)
    return _vocabulary_manager()

@bp.route('/create', methods=['POST'])
def create_vocab_entry():
    from ..utils import login_required
    @login_required
    def _create_vocab_entry():
        """Creates a new vocabulary entry in the active vocabulary file."""
        try:
            vocab_data = load_vocabulary_from_file(ACTIVE_VOCAB_FILE)

            new_word = request.form.get('word', '').strip()
            if not new_word:
                flash('Word cannot be empty.', 'error')
                return redirect(url_for('vocabulary.vocabulary_manager'))

            if new_word in vocab_data:
                flash(f'Word "{new_word}" already exists.', 'error')
                return redirect(url_for('vocabulary.vocabulary_manager'))

            entry_details = {
                "definition": request.form.get('definition', ''),
                "example_sentence": request.form.get('example_sentence', ''),
                "genai_image_prompt": request.form.get('genai_image_prompt', ''),
                "genai_audio_prompt": request.form.get('genai_audio_prompt', ''),
                "sublist": int(request.form.get('sublist', 5))
            }

            vocab_data[new_word] = entry_details

            # Save the updated data back to the file
            save_path = os.path.join(VOCAB_DATA_PATH, ACTIVE_VOCAB_FILE)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(vocab_data, f, indent=4)

            flash(f'Successfully created new word: "{new_word}".', 'success')

        except Exception as e:
            logging.error(f"Error creating vocabulary entry: {e}")
            flash('An unexpected error occurred while creating the entry.', 'error')

        return redirect(url_for('vocabulary.vocabulary_manager'))
    return _create_vocab_entry()

@bp.route('/edit/<word>', methods=['POST'])
def edit_vocab_entry(word):
    from ..utils import login_required
    @login_required
    def _edit_vocab_entry(word):
        """Updates an existing vocabulary entry."""
        try:
            vocab_data = load_vocabulary_from_file(ACTIVE_VOCAB_FILE)

            original_word = request.form.get('original_word', word)
            new_word = request.form.get('word', '').strip()

            if not new_word:
                flash('Word cannot be empty.', 'error')
                return redirect(url_for('vocabulary.vocabulary_manager'))

            # If the word is being renamed, check if the new name conflicts with an existing entry.
            if new_word != original_word and new_word in vocab_data:
                flash(f'Word "{new_word}" already exists.', 'error')
                return redirect(url_for('vocabulary.vocabulary_manager'))

            # Remove the old entry if the word was renamed
            if new_word != original_word and original_word in vocab_data:
                vocab_data.pop(original_word)

            entry_details = {
                "definition": request.form.get('definition', ''),
                "example_sentence": request.form.get('example_sentence', ''),
                "genai_image_prompt": request.form.get('genai_image_prompt', ''),
                "genai_audio_prompt": request.form.get('genai_audio_prompt', ''),
                "sublist": int(request.form.get('sublist', 5))
            }

            vocab_data[new_word] = entry_details

            # Save the updated data back to the file
            save_path = os.path.join(VOCAB_DATA_PATH, ACTIVE_VOCAB_FILE)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(vocab_data, f, indent=4)

            flash(f'Successfully updated word: "{new_word}".', 'success')

        except Exception as e:
            logging.error(f"Error updating vocabulary entry for word '{word}': {e}")
            flash('An unexpected error occurred while updating the entry.', 'error')

        return redirect(url_for('vocabulary.vocabulary_manager'))
    return _edit_vocab_entry(word)

@bp.route('/brainstorm', methods=['POST'])
def brainstorm_vocab():
    from ..utils import login_required, get_ai_response
    @login_required
    def _brainstorm_vocab():
        """Handles the AI vocabulary brainstorming feature."""
        subject = request.form.get('subject')
        if not subject:
            flash("Please enter a subject to brainstorm.", "warning")
            return redirect(url_for('vocabulary.vocabulary_manager'))

        # Prepare the context for the AI prompt
        context = {"subject": subject}
        ai_response = get_ai_response("BRAINSTORM_VOCABULARY", context)

        brainstorm_results = None
        if isinstance(ai_response, dict) and 'vocabulary' in ai_response:
            # The AI should return a list of objects, each with 'word' and 'definition'
            # We need to convert this into the format our app uses (word: difficulty)
            # For now, we'll just assign a default difficulty.
            brainstorm_results = {item.get('word', 'unknown'): 5 for item in ai_response['vocabulary']}
            flash("AI brainstorming complete! Review and save the results below.", "info")
        else:
            error_reason = ai_response.get('reason', 'Unknown error') if isinstance(ai_response, dict) else 'AI communication failure'
            flash(f"AI brainstorming failed: {error_reason}", "error")

        # Re-render the manager page with the results
        try:
            vocab_files = [f for f in os.listdir(VOCAB_DATA_PATH) if f.endswith('.json')]
        except OSError:
            vocab_files = []

        return render_template('vocabulary_manager.html',
                               vocab_files=vocab_files,
                               brainstorm_results=brainstorm_results,
                               subject=subject)
    return _brainstorm_vocab()


@bp.route('/save_brainstorm', methods=['POST'])
def save_brainstormed_vocab():
    from ..utils import login_required
    @login_required
    def _save_brainstormed_vocab():
        """Saves the brainstormed vocabulary list to a new JSON file."""
        filename = request.form.get('filename')
        vocab_data_str = request.form.get('vocab_data')

        if not filename or not vocab_data_str:
            flash("Missing filename or vocabulary data to save.", "error")
            return redirect(url_for('vocabulary.vocabulary_manager'))

        # Secure the filename
        filename = secure_filename(filename)
        if not filename.endswith('.json'):
            filename += '.json'

        save_path = os.path.join(VOCAB_DATA_PATH, filename)

        try:
            # Validate that the data is valid JSON
            vocab_data = json.loads(vocab_data_str)
            if not isinstance(vocab_data, dict):
                raise ValueError("Data is not a valid dictionary.")

            # Save the file
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(vocab_data, f, indent=4)

            flash(f'Successfully saved new vocabulary set as "{filename}".', 'success')

        except json.JSONDecodeError:
            flash("The provided text is not valid JSON. Please correct it before saving.", "error")
            # To allow the user to fix it, we need to re-render the page with their data
            try:
                vocab_files = [f for f in os.listdir(VOCAB_DATA_PATH) if f.endswith('.json')]
            except OSError:
                vocab_files = []
            subject = request.form.get('subject', 'Unknown Subject')
            # This is tricky; we can't easily reinject the broken JSON.
            # For now, we'll just redirect. A better UX would use client-side validation.
            return redirect(url_for('vocabulary.vocabulary_manager'))
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            logging.error(f"Error saving brainstormed vocab file {filename}: {e}")
            flash('An unexpected error occurred while saving the file.', 'error')

        return redirect(url_for('vocabulary.vocabulary_manager'))
    return _save_brainstormed_vocab()
