from flask import Blueprint, render_template, request, current_app
import os
from werkzeug.utils import secure_filename
from .extraction import extract_siard_file
from .analysis import search_siard_files

search_bp = Blueprint('search_bp', __name__)

def save_uploaded_file(file):
    filename = secure_filename(file.filename)
    upload_path = os.path.join('uploads', filename)
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    file.save(upload_path)
    current_app.logger.debug(f"File saved to: {upload_path}")
    return upload_path

@search_bp.route('/', methods=['GET', 'POST'])
def search():
    results = None
    feedback = ''

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        age = request.form.get('age', '').strip()

        query = ' '.join(filter(None, [first_name, last_name, age]))
        use_default = 'use_default' in request.form

        current_app.logger.info(f'Search query received: {query}')

        if use_default:
            siard_path = 'tests/test_siard.siard'
            current_app.logger.info(f'Using default SIARD file at {siard_path}')
        else:
            file = request.files.get('siard_file')
            if file and file.filename.endswith('.siard'):
                siard_path = save_uploaded_file(file)
                current_app.logger.info(f'User uploaded file: {siard_path}')
            else:
                feedback = 'No valid SIARD file uploaded.'
                current_app.logger.error('No valid SIARD file uploaded.')
                return render_template('index.html', results=results, feedback=feedback)

        extract_dir = os.path.join('temp_extracted', os.path.basename(siard_path).replace('.siard', ''))
        os.makedirs(extract_dir, exist_ok=True)
        current_app.logger.debug(f'Extraction directory created: {extract_dir}')

        with current_app.app_context():
            if extract_siard_file(siard_path, extract_dir):
                current_app.logger.info(f'Successfully extracted SIARD file: {siard_path}')
                app = current_app._get_current_object()
                results = search_siard_files(query, extract_dir, app, max_workers=2)
                if results:
                    feedback = f'{len(results)} matches found for "{query}".'
                    current_app.logger.info(f'Search results: {results}')
                else:
                    feedback = f'No matches found for "{query}".'
                    current_app.logger.info(f'No matches found for "{query}".')
            else:
                feedback = 'Error extracting the SIARD file.'
                current_app.logger.error('Error extracting the SIARD file.')

    current_app.logger.info('Rendering template with results and feedback')
    return render_template('index.html', results=results, feedback=feedback)
