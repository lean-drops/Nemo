"""
Dieses Modul enthält Funktionen zur Analyse und Suche in extrahierten Dateien.

Die Hauptfunktion `search_files` durchsucht die Dateien in einem angegebenen Verzeichnis nach einer Abfrage.
"""

import os
from flask import current_app
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

def read_and_search_file(file_path, query, app):
    """
    Liest eine TXT-Datei ein und durchsucht sie nach einer bestimmten Abfrage.

    Args:
        file_path (str): Der Pfad zur Datei, die durchsucht werden soll.
        query (str): Die Suchabfrage.
        app (Flask): Die Flask-Anwendung zur Nutzung des Loggers.

    Returns:
        list: Eine Liste der gefundenen Ergebnisse als Dictionary.
    """
    results = []
    try:
        with open(file_path, 'r') as file:
            app.logger.debug(f"Processing file: {file_path} with query: {query}")

            # Suchabfrage in Kleinbuchstaben konvertieren, um Groß-/Kleinschreibung zu ignorieren
            query_lower = query.lower()

            for line in file:
                if query_lower in line.lower():
                    results.append({'file': file_path, 'line': line.strip()})

        # Wenn Übereinstimmungen gefunden wurden, diese loggen
        if results:
            app.logger.debug(f"Found matches in file: {file_path}\n{results}")

    except Exception as e:
        with app.app_context():
            app.logger.error(f"Error processing file {file_path}: {e}")

    return results

def search_files(query, extract_dir, app, max_workers=2):
    """
    Durchsucht alle TXT-Dateien in einem angegebenen Verzeichnis nach einer bestimmten Abfrage.

    Args:
        query (str): Die Suchabfrage.
        extract_dir (str): Das Verzeichnis, in dem gesucht werden soll.
        app (Flask): Die Flask-Anwendung zur Nutzung des Loggers.
        max_workers (int): Die maximale Anzahl der parallelen Worker.

    Returns:
        list: Eine Liste der gefundenen Ergebnisse als Dictionary.
    """
    results = []
    query = query.lower()

    app.logger.debug(f"Starting search in directory: {extract_dir} with query: {query}")

    try:
        # Pfad zur Strukturdatei ermitteln
        structure_file_path = os.path.join(extract_dir, 'structure.json')
        with open(structure_file_path, 'r') as f:
            file_structure = json.load(f)

        # Alle TXT-Dateipfade im Verzeichnis und Unterverzeichnissen ermitteln
        file_paths = [os.path.join(extract_dir, root, file)
                      for root, details in file_structure.items()
                      for file in details['files'] if file.endswith('.txt')]

        app.logger.debug(f"Found TXT files: {file_paths}")

        # Parallelisierte Suche in den TXT-Dateien
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(read_and_search_file, file_path, query, app): file_path for file_path in file_paths}

            for future in as_completed(futures):
                file_results = future.result()
                if file_results:
                    app.logger.debug(f"Results from file: {futures[future]}\n{file_results}")
                    results.extend(file_results)
    except Exception as e:
        with app.app_context():
            app.logger.error(f"Error searching files: {e}")

    app.logger.debug(f"Total results found: {len(results)}")
    return results
