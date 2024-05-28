import os
import zipfile
from werkzeug.utils import secure_filename
from flask import current_app
from fuzzywuzzy import process

from tests.test import EXPECTED_SCHEMAS

UPLOAD_FOLDER = 'uploads'

def save_uploaded_file(file):
    """
    Speichert die hochgeladene Datei im Verzeichnis 'uploads'.

    Args:
        file (werkzeug.datastructures.FileStorage): Die hochgeladene Datei.

    Returns:
        str: Der Pfad zur gespeicherten Datei.
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

    Args:
        zip_path (str): Der Pfad zur ZIP-Datei.
        extract_dir (str): Das Verzeichnis, in das die Dateien extrahiert werden sollen.

    Returns:
        list: Eine Liste der extrahierten TXT-Dateien.
    """
    txt_files = []
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        zip_file.extractall(extract_dir)
        for file in zip_file.namelist():
            if file.endswith('.txt'):
                txt_files.append(os.path.join(extract_dir, file))
    return txt_files


def correct_schema(columns):
    """
    Korrigiert die Spaltennamen einer Tabelle basierend auf den erwarteten Schemas.

    Args:
        columns (list): Die Liste der Spaltennamen, die korrigiert werden sollen.

    Returns:
        list: Die Liste der korrigierten Spaltennamen.
    """
    corrected_columns = []
    for col in columns:
        best_match, score = process.extractOne(col, [col for schema in EXPECTED_SCHEMAS.values() for col in schema])
        if score > 80:  # Wenn die Übereinstimmung hoch genug ist, als korrekt betrachten
            corrected_columns.append(best_match)
        else:
            corrected_columns.append(col)  # Wenn keine gute Übereinstimmung gefunden wird, den ursprünglichen Namen beibehalten
    return corrected_columns