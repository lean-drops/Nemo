import os
import zipfile
import json
from flask import Blueprint, render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor
from .extraction import extract_files_in_directory, analyze_structure, read_schemas
from .analysis import search_files

search_bp = Blueprint('search_bp', __name__)
executor = ThreadPoolExecutor(max_workers=4)  # Anpassung der Anzahl der Worker je nach Systemressourcen

UPLOAD_FOLDER = 'uploads'

def save_uploaded_file(file):
    """
    Speichert die hochgeladene Datei im Verzeichnis 'uploads'.
    """
    filename = secure_filename(file.filename)
    upload_path = os.path.join(UPLOAD_FOLDER, filename)
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    file.save(upload_path)
    current_app.logger.debug(f"File saved to: {upload_path}")
    return upload_path

def extract_zip_file(zip_path, extract_dir):
    """
    Extrahiert eine ZIP-Datei in ein angegebenes Verzeichnis und gibt eine Liste der extrahierten TXT-Dateien zurück.
    """
    txt_files = []
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        zip_file.extractall(extract_dir)
        for file in zip_file.namelist():
            if file.endswith('.txt'):
                txt_files.append(os.path.join(extract_dir, file))
    return txt_files

def extract_files_in_directory(directory, extract_to):
    """
    Extrahiert alle ZIP-Dateien in einem Verzeichnis und gibt eine Liste aller extrahierten TXT-Dateien zurück.
    """
    all_txt_files = []
    for filename in os.listdir(directory):
        if filename.endswith('.zip'):
            file_path = os.path.join(directory, filename)
            extract_path = os.path.join(extract_to, os.path.splitext(filename)[0])
            os.makedirs(extract_path, exist_ok=True)
            txt_files = extract_zip_file(file_path, extract_path)
            all_txt_files.extend(txt_files)
    return all_txt_files

def extract_file_async(app, file_path, extract_dir):
    """
    Führt die asynchrone Extraktion der Datei durch.
    """
    with app.app_context():
        try:
            txt_files = extract_zip_file(file_path, extract_dir)
            current_app.logger.info(f'Successfully extracted file: {file_path}')
            analyze_and_log_structure(extract_dir)
            return txt_files
        except Exception as e:
            current_app.logger.error(f'Exception during file extraction: {e}')
            return []

def extract_directory_async(app, directory, extract_to):
    """
    Führt die asynchrone Extraktion eines Verzeichnisses mit ZIP-Dateien durch.
    """
    with app.app_context():
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
    """
    current_app.logger.info('Rendering index page.')
    return render_template('index.html')

@search_bp.route('/upload', methods=['POST'])
def upload():
    """
    Endpunkt zum Hochladen und Extrahieren von Dateien (ZIP).
    Dieser Endpunkt erkennt automatisch, ob es sich um eine einzelne ZIP-Datei oder ein Verzeichnis handelt.
    """
    files = request.files.getlist('file')
    if not files:
        current_app.logger.warning('No file part in the request.')
        return jsonify({"message": "No file part in the request."}), 400

    file_paths = []
    for file in files:
        current_app.logger.info(f'Received file: {file.filename}')
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
    all_txt_files = []
    futures = [executor.submit(extract_file_async, current_app._get_current_object(), file_path, extract_dir) for file_path in file_paths]
    for future in futures:
        all_txt_files.extend(future.result())

    return jsonify({"message": "Files uploaded and extraction started.", "txt_files": all_txt_files}), 200

@search_bp.route('/upload_directory', methods=['POST'])
def upload_directory():
    """
    Endpunkt zum Hochladen und Extrahieren eines Verzeichnisses mit ZIP-Dateien.
    """
    files = request.files.getlist('file')
    if not files:
        current_app.logger.warning('No files part in the request.')
        return jsonify({"message": "No files part in the request."}), 400

    extract_to = 'temp_extracted'
    os.makedirs(extract_to, exist_ok=True)

    # Asynchrone Extraktion aller hochgeladenen ZIP-Dateien und Sammeln aller TXT-Dateien
    all_txt_files = []
    futures = [executor.submit(extract_file_async, current_app._get_current_object(), save_uploaded_file(file), extract_to) for file in files]
    for future in futures:
        all_txt_files.extend(future.result())

    return jsonify({"message": "Files uploaded and extraction started.", "txt_files": all_txt_files}), 200

@search_bp.route('/search', methods=['POST'])
def search():
    """
    Endpunkt für die Suche in den extrahierten Dateien.
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
