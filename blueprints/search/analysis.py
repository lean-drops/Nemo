import os
import pandas as pd
from flask import current_app
from concurrent.futures import ThreadPoolExecutor, as_completed

def read_and_search_file(file_path, query, app):
    """
    Liest eine CSV-Datei ein und durchsucht sie nach einer bestimmten Abfrage.

    Args:
        file_path (str): Der Pfad zur Datei.
        query (str): Die Suchabfrage.
        app (Flask): Die Flask-Anwendung für Logging.

    Returns:
        list: Eine Liste der gefundenen Ergebnisse.
    """
    try:
        df = pd.read_csv(file_path, sep="\t")
        app.logger.debug(f"Processing file: {file_path} with query: {query}")

        # Convert query to lowercase for case-insensitive search
        query_lower = query.lower()

        # Log the first few rows of the dataframe for debugging
        app.logger.debug(f"First few rows of the dataframe:\n{df.head()}")

        # Search for matches in the DataFrame
        matches = df[df.apply(lambda row: row.astype(str).str.lower().str.contains(query_lower).any(), axis=1)]

        if not matches.empty:
            app.logger.debug(f"Found matches in file: {file_path}\n{matches}")

        return [row.to_dict() for _, row in matches.iterrows()]
    except Exception as e:
        with app.app_context():
            app.logger.error(f"Error processing file {file_path}: {e}")
        return []

def search_files(query, extract_dir, app, max_workers=4):
    """
    Durchsucht alle CSV-Dateien in einem angegebenen Verzeichnis nach einer bestimmten Abfrage.

    Args:
        query (str): Die Suchabfrage.
        extract_dir (str): Das Verzeichnis, in dem die Dateien durchsucht werden sollen.
        app (Flask): Die Flask-Anwendung für Logging.
        max_workers (int): Die maximale Anzahl der Worker-Threads.

    Returns:
        list: Eine Liste der gefundenen Ergebnisse.
    """
    results = []
    query = query.lower()

    app.logger.debug(f"Starting search in directory: {extract_dir} with query: {query}")

    try:
        file_paths = [os.path.join(root, file)
                      for root, _, files in os.walk(extract_dir)
                      for file in files if file.endswith('.txt')]

        app.logger.debug(f"Found TXT files: {file_paths}")

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
