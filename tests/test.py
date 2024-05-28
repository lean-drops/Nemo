import os
import zipfile
import pandas as pd
import dask.dataframe as dd
from concurrent.futures import ThreadPoolExecutor
from faker import Faker
import webbrowser
import subprocess
import logging

fake = Faker()

# Logging-Konfiguration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_large_csv_files(output_dir, num_records=10000):
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f'Erstelle Verzeichnis: {output_dir}')

    def generate_data(file_path, num_records):
        logging.info(f'Starte Daten-Generierung für {file_path}')
        data = {
            'ID': list(range(1, num_records + 1)),
            'Name': [fake.name() for _ in range(num_records)],
            'Birthdate': [fake.date_of_birth(minimum_age=18, maximum_age=90) for _ in range(num_records)]
        }
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        logging.info(f'Daten-Generierung abgeschlossen für {file_path}')

    futures = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures.append(executor.submit(generate_data, os.path.join(output_dir, 'person.csv'), num_records))
        futures.append(executor.submit(generate_data, os.path.join(output_dir, 'address.csv'), num_records))

    for future in futures:
        future.result()
    logging.info('Alle CSV-Dateien wurden erfolgreich erstellt.')

def create_siard_file(siard_filename, input_dir):
    logging.info(f'Starte Erstellung der SIARD-Datei: {siard_filename}')
    with zipfile.ZipFile(siard_filename, 'w', zipfile.ZIP_DEFLATED) as siard_zip:
        for root, _, files in os.walk(input_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, input_dir)
                siard_zip.write(file_path, arcname)
    logging.info(f'SIARD-Datei "{siard_filename}" wurde erfolgreich erstellt.')

def start_flask_app():
    # Flask-Anwendung in einem separaten Prozess starten
    logging.info('Starte Flask-Anwendung...')
    subprocess.Popen(['python', 'app.py'])

def main():
    output_dir = 'test_siard_data'
    siard_filename = 'test_siard.siard'

    # CSV-Dateien erstellen
    create_large_csv_files(output_dir, num_records=10000)

    # SIARD-Datei erstellen
    create_siard_file(siard_filename, output_dir)

    print(f'Test-SIARD-Datei "{siard_filename}" wurde erstellt.')

    # Flask-Anwendung starten
    start_flask_app()

    # Browser öffnen
    webbrowser.open('http://127.0.0.1:5000')
    logging.info('Webbrowser geöffnet auf http://127.0.0.1:5000')

if __name__ == "__main__":
    main()
