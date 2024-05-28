"""
Dieses Modul definiert die Routen für die Such-Blueprints der Flask-Anwendung.

Es enthält Endpunkte für:
- Die Hauptseite
- Hochladen und Speichern von ZIP-Dateien
- Extrahieren von ZIP-Dateien
- Durchführen von Suchanfragen in extrahierten Dateien

Logging wird verwendet, um den Verlauf und eventuelle Fehler zu verfolgen.
"""

from flask import Blueprint, render_template, request, jsonify, current_app
import os
from werkzeug.utils import secure_filename
from .extraction import extract_file
from .analysis import search_files
from concurrent.futures import ThreadPoolExecutor

search_bp = Blueprint('search_bp', __name__)
executor = ThreadPoolExecutor(max_workers=4)  # Anpassung der Anzahl der Worker je nach Systemressourcen

def save_uploaded_file(file):
    """
    Speichert die hochgeladene Datei im Verzeichnis 'uploads'.

    Args:
        file (werkzeug.datastructures.FileStorage): Die hochgeladene Datei.

    Returns:
        str: Der Pfad zur gespeicherten Datei.
    """
    filename = secure_filename(file.filename)
    upload_path = os.path.join('uploads', filename)
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    file.save(upload_path)
    current_app.logger.debug(f"File saved to: {upload_path}")
    return upload_path

def extract_file_async(file_path, extract_dir):
    """
    Führt die asynchrone Extraktion der Datei durch.

    Args:
        file_path (str): Der Pfad zur Datei (ZIP).
        extract_dir (str): Das Verzeichnis, in das extrahiert werden soll.
    """
    try:
        if extract_file(file_path, extract_dir):
            current_app.logger.info(f'Successfully extracted file: {file_path}')
        else:
            current_app.logger.error(f'Error extracting the file: {file_path}')
    except Exception as e:
        current_app.logger.error(f'Exception during file extraction: {e}')

@search_bp.route('/')
def index():
    """
    Rendert die Startseite der Anwendung.

    Returns:
        werkzeug.wrappers.Response: Die gerenderte HTML-Seite.
    """
    current_app.logger.info('Rendering index page.')
    return render_template('index.html')

@search_bp.route('/upload', methods=['POST'])
def upload():
    """
    Endpunkt zum Hochladen und Extrahieren von Dateien (ZIP).

    Returns:
        werkzeug.wrappers.Response: Eine JSON-Antwort mit dem Ergebnis des Hochladens und Extrahierens.
    """
    file = request.files.get('file')
    if file:
        current_app.logger.info(f'Received file: {file.filename}')
        current_app.logger.info(f'File content type: {file.content_type}')

        if file.filename.endswith('.zip'):
            try:
                file_path = save_uploaded_file(file)
                extract_dir = os.path.join('temp_extracted', os.path.basename(file_path).replace('.zip', ''))
                os.makedirs(extract_dir, exist_ok=True)
                # Asynchrone Extraktion starten
                executor.submit(extract_file_async, file_path, extract_dir)
                return jsonify({"message": "File uploaded and extraction started."}), 200
            except Exception as e:
                current_app.logger.error(f'Exception during file upload and extraction: {e}')
                return jsonify({"message": "Internal server error."}), 500
        else:
            current_app.logger.warning('Invalid file format received.')
            return jsonify({"message": "Invalid file format."}), 400
    else:
        current_app.logger.warning('No file part in the request.')
        return jsonify({"message": "No file part in the request."}), 400

@search_bp.route('/search', methods=['POST'])
def search():
    """
    Endpunkt für die Suche in den extrahierten Dateien.

    Returns:
        werkzeug.wrappers.Response: Eine JSON-Antwort mit den Suchergebnissen.
    """
    query = request.form.get('search_query', '').strip()
    if not query:
        current_app.logger.warning('Empty search query received.')
        return jsonify({"message": "Search query cannot be empty."}), 400

    current_app.logger.info(f'Searching for query: {query}')
    extract_dir = os.path.join('temp_extracted', os.path.basename('uploads/test_file.zip').replace('.zip', ''))
    app = current_app._get_current_object()
    try:
        results = search_files(query, extract_dir, app, max_workers=4)
        current_app.logger.info(f'Search completed for query: {query}')
        return jsonify({"results": results}), 200
    except Exception as e:
        current_app.logger.error(f'Exception during search: {e}')
        return jsonify({"message": "Internal server error during search."}), 500

@search_bp.route('/detailed_search', methods=['POST'])
def detailed_search():
    """
    Endpunkt für die detaillierte Suche in den extrahierten Dateien.

    Returns:
        werkzeug.wrappers.Response: Eine JSON-Antwort mit den detaillierten Suchergebnissen.
    """
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    age = request.form.get('age', '').strip()

    query = ' '.join(filter(None, [first_name, last_name, age]))
    if not query:
        current_app.logger.warning('Empty detailed search query received.')
        return jsonify({"message": "Search query cannot be empty."}), 400

    current_app.logger.info(f'Detailed search for query: {query}')
    extract_dir = os.path.join('temp_extracted', os.path.basename('uploads/test_file.zip').replace('.zip', ''))
    app = current_app._get_current_object()
    try:
        results = search_files(query, extract_dir, app, max_workers=4)
        current_app.logger.info(f'Detailed search completed for query: {query}')
        return jsonify({"results": results}), 200
    except Exception as e:
        current_app.logger.error(f'Exception during detailed search: {e}')
        return jsonify({"message": "Internal server error during detailed search."}), 500
