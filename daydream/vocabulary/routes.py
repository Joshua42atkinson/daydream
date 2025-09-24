import os
import json
import logging
from flask import render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.utils import secure_filename
from . import bp


# Define the path to the vocabulary data directory
VOCAB_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

@bp.route('/')
def vocabulary_manager():
    from ..utils import login_required
    @login_required
    def _vocabulary_manager():
        """Renders the main vocabulary management page."""
        try:
            # Ensure the data directory exists
            os.makedirs(VOCAB_DATA_PATH, exist_ok=True)
            # List available vocabulary files
            vocab_files = [f for f in os.listdir(VOCAB_DATA_PATH) if f.endswith('.json')]
        except OSError as e:
            logging.error(f"Error accessing vocabulary directory {VOCAB_DATA_PATH}: {e}")
            flash("Could not access vocabulary directory.", "error")
            vocab_files = []

        return render_template('vocabulary_manager.html', vocab_files=vocab_files)
    return _vocabulary_manager()

@bp.route('/upload', methods=['POST'])
def upload_vocab():
    from ..utils import login_required
    @login_required
    def _upload_vocab():
        """Handles uploading of new vocabulary JSON files."""
        if 'vocab_file' not in request.files:
            flash('No file part in the request.', 'error')
            return redirect(url_for('vocabulary.vocabulary_manager'))

        file = request.files['vocab_file']
        if file.filename == '':
            flash('No file selected for uploading.', 'warning')
            return redirect(url_for('vocabulary.vocabulary_manager'))

        if file and file.filename.endswith('.json'):
            filename = secure_filename(file.filename)
            save_path = os.path.join(VOCAB_DATA_PATH, filename)

            try:
                # Validate JSON content before saving
                json_data = json.load(file)
                if not isinstance(json_data, dict):
                    raise ValueError("JSON content must be a dictionary.")

                # Save the validated JSON data
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=4)

                flash(f'Vocabulary file "{filename}" uploaded and validated successfully.', 'success')
            except json.JSONDecodeError:
                flash('Invalid JSON file. Please check the file content and structure.', 'error')
            except ValueError as e:
                flash(str(e), 'error')
            except Exception as e:
                logging.error(f"Error saving uploaded vocab file {filename}: {e}")
                flash('An unexpected error occurred while saving the file.', 'error')

        else:
            flash('Invalid file type. Please upload a .json file.', 'error')

        return redirect(url_for('vocabulary.vocabulary_manager'))
    return _upload_vocab()


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