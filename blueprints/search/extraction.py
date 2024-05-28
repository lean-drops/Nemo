import os
import zipfile
import json
from collections import defaultdict

import pandas as pd
from flask import current_app
from .common import extract_zip_file

def extract_files_in_directory(directory, extract_to):
    """
    Extrahiert alle ZIP-Dateien in einem Verzeichnis und gibt eine Liste aller extrahierten TXT-Dateien zurück.

    Args:
        directory (str): Das Verzeichnis, das die ZIP-Dateien enthält.
        extract_to (str): Das Verzeichnis, in das die Dateien extrahiert werden sollen.

    Returns:
        list: Eine Liste aller extrahierten TXT-Dateien.
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
