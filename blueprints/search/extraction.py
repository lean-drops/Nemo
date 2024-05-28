"""
Dieses Modul enthält Funktionen zum Extrahieren von ZIP-Dateien, zur Analyse der extrahierten Dateien
und zur Korrektur von Tippfehlern in den extrahierten Daten.

Die Hauptfunktion `extract_files_in_directory` extrahiert den Inhalt aller ZIP-Dateien in einem angegebenen Verzeichnis
in ein Zielverzeichnis und liest die Schema-Informationen aus den extrahierten TXT-Dateien.
"""

import zipfile
import os
import json
import pandas as pd
from flask import current_app
from fuzzywuzzy import process
from collections import defaultdict

EXPECTED_SCHEMAS = {
    "Person": ["PIN", "Name", "Vorname", "Geburtsdatum", "Adresse"],
    "PersonHist": ["PIN", "HISTNR", "Name", "Vorname", "Geburtsdatum", "Adresse", "Änderungsdatum"],
    "Ausweis": ["ID", "PIN", "Ausweisnummer", "Ausstellungsdatum", "Gültigkeitsdatum"],
    "Ausweishist": ["ID", "HISTNR", "Ausweisnummer", "Ausstellungsdatum", "Gültigkeitsdatum", "Änderungsdatum"],
    "Ausweiskat": ["ID", "AUSWEISID", "Kategorie"],
    "Ausweiskathist": ["ID", "HISTNR", "Kategorie", "Änderungsdatum"],
    "Fzausweis": ["ID", "STAMM", "PIN", "Fahrzeugausweisnummer", "Ausstellungsdatum", "Gültigkeitsdatum"],
    "Fzausweishist": ["ID", "HISTNR", "Fahrzeugausweisnummer", "Ausstellungsdatum", "Gültigkeitsdatum", "Änderungsdatum"],
    "Fzallgemein": ["STAMM", "Fahrzeugtyp", "Hersteller", "Modell", "Baujahr"],
    "Fzallgemeinhist": ["STAMM", "HISTNR", "Fahrzeugtyp", "Hersteller", "Modell", "Baujahr", "Änderungsdatum"],
    "FZ": ["STAMM", "Kennzeichen", "Farbe", "Motorleistung", "Kilometerstand"],
    "Fzhist": ["STAMM", "HISTNR", "Kennzeichen", "Farbe", "Motorleistung", "Kilometerstand", "Änderungsdatum"],
}

def extract_files_in_directory(directory, extract_to):
    """
    Extrahiert den Inhalt aller ZIP-Dateien in einem angegebenen Verzeichnis in ein Zielverzeichnis
    und liest die Schema-Informationen aus den extrahierten TXT-Dateien.

    Args:
        directory (str): Das Verzeichnis, das die ZIP-Dateien enthält.
        extract_to (str): Das Verzeichnis, in das die Dateien extrahiert werden sollen.

    Returns:
        bool: True, wenn die Extraktion erfolgreich war, False bei einem Fehler.
    """
    try:
        current_app.logger.info(f"Starting extraction of all ZIP files in directory: {directory} to {extract_to}")

        if not os.path.exists(extract_to):
            os.makedirs(extract_to)
            current_app.logger.debug(f"Created extraction directory: {extract_to}")

        for filename in os.listdir(directory):
            if filename.endswith('.zip'):
                file_path = os.path.join(directory, filename)
                extract_path = os.path.join(extract_to, filename.replace('.zip', ''))
                os.makedirs(extract_path, exist_ok=True)
                with zipfile.ZipFile(file_path, 'r') as zip_file:
                    zip_file.extractall(extract_path)
                    current_app.logger.info(f"Successfully extracted ZIP file: {file_path} to {extract_path}")

        # Analysiere die Struktur der extrahierten Dateien und speichere sie
        file_structure = analyze_structure(extract_to)
        structure_file_path = os.path.join(extract_to, 'structure.json')
        with open(structure_file_path, 'w') as f:
            json.dump(file_structure, f)
            current_app.logger.info(f"File structure saved to: {structure_file_path}")

        # Schema-Informationen aus den TXT-Dateien lesen
        schema_info = read_schemas(extract_to)
        schema_info_file_path = os.path.join(extract_to, 'schemas.json')
        with open(schema_info_file_path, 'w') as f:
            json.dump(schema_info, f)
            current_app.logger.info(f"Schema information saved to: {schema_info_file_path}")

        return True
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred while extracting files: {e}")
        return False

def extract_single_zip(file_path, extract_to):
    """
    Extrahiert den Inhalt einer einzelnen ZIP-Datei in ein Zielverzeichnis
    und liest die Schema-Informationen aus den extrahierten TXT-Dateien.

    Args:
        file_path (str): Der Pfad zur ZIP-Datei.
        extract_to (str): Das Verzeichnis, in das die Dateien extrahiert werden sollen.

    Returns:
        bool: True, wenn die Extraktion erfolgreich war, False bei einem Fehler.
    """
    try:
        current_app.logger.info(f"Starting extraction of file: {file_path} to {extract_to}")

        if not os.path.exists(extract_to):
            os.makedirs(extract_to)
            current_app.logger.debug(f"Created extraction directory: {extract_to}")

        with zipfile.ZipFile(file_path, 'r') as zip_file:
            zip_file.extractall(extract_to)
            current_app.logger.info(f"Successfully extracted ZIP file: {file_path} to {extract_to}")

        # Analysiere die Struktur der extrahierten Dateien und speichere sie
        file_structure = analyze_structure(extract_to)
        structure_file_path = os.path.join(extract_to, 'structure.json')
        with open(structure_file_path, 'w') as f:
            json.dump(file_structure, f)
            current_app.logger.info(f"File structure saved to: {structure_file_path}")

        # Schema-Informationen aus den TXT-Dateien lesen
        schema_info = read_schemas(extract_to)
        schema_info_file_path = os.path.join(extract_to, 'schemas.json')
        with open(schema_info_file_path, 'w') as f:
            json.dump(schema_info, f)
            current_app.logger.info(f"Schema information saved to: {schema_info_file_path}")

        return True
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred while extracting file: {e}")
        return False

def analyze_structure(directory):
    """
    Analysiert die Struktur des angegebenen Verzeichnisses und gibt eine Darstellung der Struktur zurück.

    Args:
        directory (str): Das Verzeichnis, dessen Struktur analysiert werden soll.

    Returns:
        dict: Eine Darstellung der Verzeichnisstruktur.
    """
    file_structure = {}
    for root, dirs, files in os.walk(directory):
        relative_path = os.path.relpath(root, directory)
        file_structure[relative_path] = {'dirs': dirs, 'files': files}
    return file_structure

def read_schemas(directory):
    """
    Liest die Schema-Informationen aus den TXT-Dateien im angegebenen Verzeichnis und korrigiert Tippfehler.

    Args:
        directory (str): Das Verzeichnis, in dem die TXT-Dateien durchsucht werden sollen.

    Returns:
        dict: Eine Darstellung der erkannten Schemas mit korrigierten Feldnamen.
    """
    schema_info = defaultdict(list)
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                try:
                    df = pd.read_csv(file_path, sep="\t")
                    columns = df.columns.tolist()
                    corrected_columns = correct_schema(columns)
                    schema_info[file] = corrected_columns
                    current_app.logger.info(f"Read and corrected schema for file: {file_path}")
                except Exception as e:
                    current_app.logger.error(f"Error reading schema from file {file_path}: {e}")

    return schema_info

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
