"""
Dieses Modul definiert die Routen für die Such-Blueprints der Flask-Anwendung.

Es enthält Endpunkte für:
- Die Hauptseite
- Hochladen und Speichern von ZIP-Dateien
- Extrahieren von ZIP-Dateien aus einem Verzeichnis
- Durchführen von Suchanfragen in extrahierten Dateien

Logging wird verwendet, um den Verlauf und eventuelle Fehler zu verfolgen.
"""

from flask import Blueprint, render_template, request, jsonify, current_app
import os
from .common import save_uploaded_file, extract_zip_file
from .extraction import extract_files_in_directory, analyze_structure, read_schemas
from .analysis import search_files
from concurrent.futures import ThreadPoolExecutor

search_bp = Blueprint('search_bp', __name__)
executor = ThreadPoolExecutor(max_workers=4)  # Anpassung der Anzahl der Worker je nach Systemressourcen

def extract_file_async(file_path, extract_dir):
    """
    Führt die asynchrone Extraktion der Datei durch.

    Args:
        file_path (str): Der Pfad zur Datei (ZIP).
        extract_dir (str): Das Verzeichnis, in das extrahiert werden soll.

    Returns:
        list: Eine Liste der extrahierten TXT-Dateien.
    """
    with current_app.app_context():
        try:
            txt_files = extract_zip_file(file_path, extract_dir)
            current_app.logger.info(f'Successfully extracted file: {file_path}')
            analyze_and_log_structure(extract_dir)
            return txt_files
        except Exception as e:
            current_app.logger.error(f'Exception during file extraction: {e}')
            return []

def extract_directory_async(directory, extract_to):
    """
    Führt die asynchrone Extraktion eines Verzeichnisses mit ZIP-Dateien durch.

    Args:
        directory (str): Das Verzeichnis, das die ZIP-Dateien enthält.
        extract_to (str): Das Verzeichnis, in das extrahiert werden soll.

    Returns:
        list: Eine Liste der extrahierten TXT-Dateien.
    """
    with current_app.app_context():
        try:
            txt_files = extract_files_in_directory(directory, extract_to)
            current_app.logger.info(f'Successfully extracted directory: {directory}')
            analyze_and_log_structure(extract_to)
            return txt_files
        except Exception as e:
            current_app.logger.error(f'Exception during directory extraction: {e}')
            return []

def analyze_and_log_structure(extract_dir):
    """
    Analysiert die Struktur der extrahierten Dateien und protokolliert die Schema-Informationen.

    Args:
        extract_dir (str): Das Verzeichnis mit den extrahierten Dateien.
    """
    try:
        file_structure = analyze_structure(extract_dir)
        structure_file_path = os.path.join(extract_dir, 'structure.json')
        with open(structure_file_path, 'w') as f:
            json.dump(file_structure, f)
            current_app.logger.info(f"File structure saved to: {structure_file_path}")

        schema_info = read_schemas(extract_dir)
        schema_info_file_path = os.path.join(extract_dir, 'schemas.json')
        with open(schema_info_file_path, 'w') as f:
            json.dump(schema_info, f)
            current_app.logger.info(f"Schema information saved to: {schema_info_file_path}")

        current_app.logger.debug(f"Extracted directory structure: {file_structure}")
        current_app.logger.debug(f"Extracted schemas: {schema_info}")
    except Exception as e:
        current_app.logger.error(f"Error analyzing and logging structure: {e}")

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
    files = request.files.getlist('file')
    all_txt_files = []
    if files:
        file_paths = []
        for file in files:
            current_app.logger.info(f'Received file: {file.filename}')
            current_app.logger.info(f'File content type: {file.content_type}')
            if file.filename.endswith('.zip'):
                try:
                    file_path = save_uploaded_file(file)
                    file_paths.append(file_path)
                except Exception as e:
                    current_app.logger.error(f'Exception during file upload: {e}')
                    return jsonify({"message": "Internal server error."}), 500
            else:
                current_app.logger.warning('Invalid file format received.')
                return jsonify({"message": "Invalid file format."}), 400

        extract_dir = 'temp_extracted'
        os.makedirs(extract_dir, exist_ok=True)

        # Asynchrone Extraktion aller hochgeladenen ZIP-Dateien und Sammeln aller TXT-Dateien
        futures = [executor.submit(extract_file_async, file_path, extract_dir) for file_path in file_paths]
        for future in futures:
            all_txt_files.extend(future.result())

        return jsonify({"message": "Files uploaded and extraction started.", "txt_files": all_txt_files}), 200
    else:
        current_app.logger.warning('No file part in the request.')
        return jsonify({"message": "No file part in the request."}), 400

@search_bp.route('/upload_directory', methods=['POST'])
def upload_directory():
    """
    Endpunkt zum Hochladen und Extrahieren eines Verzeichnisses mit ZIP-Dateien.

    Returns:
        werkzeug.wrappers.Response: Eine JSON-Antwort mit dem Ergebnis des Extrahierens.
    """
    directory = request.form.get('directory')
    if directory:
        current_app.logger.info(f'Received directory path: {directory}')
        extract_to = os.path.join('temp_extracted', os.path.basename(directory))
        os.makedirs(extract_to, exist_ok=True)

        # Asynchrone Extraktion starten
        future = executor.submit(extract_directory_async, directory, extract_to)
        txt_files_list = future.result()
        return jsonify({"message": "Directory extraction started.", "txt_files": txt_files_list}), 200
    else:
        current_app.logger.warning('No directory path in the request.')
        return jsonify({"message": "No directory path in the request."}), 400

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
    extract_dir = 'temp_extracted'
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
    address = request.form.get('address', '').strip()
    email = request.form.get('email', '').strip()
    phone_number = request.form.get('phone_number', '').strip()
    license_plate = request.form.get('license_plate', '').strip()
    inspection_date = request.form.get('inspection_date', '').strip()
    car_model = request.form.get('car_model', '').strip()
    birth_date = request.form.get('birth_date', '').strip()

    query = ' '.join(filter(None, [first_name, last_name, address, email, phone_number, license_plate, inspection_date, car_model, birth_date]))
    if not query:
        current_app.logger.warning('Empty detailed search query received.')
        return jsonify({"message": "Search query cannot be empty."}), 400

    current_app.logger.info(f'Detailed search for query: {query}')
    extract_dir = 'temp_extracted'
    app = current_app._get_current_object()
    try:
        results = search_files(query, extract_dir, app, max_workers=4)
        current_app.logger.info(f'Detailed search completed for query: {query}')
        return jsonify({"results": results}), 200
    except Exception as e:
        current_app.logger.error(f'Exception during detailed search: {e}')
        return jsonify({"message": "Internal server error during detailed search."}), 500
