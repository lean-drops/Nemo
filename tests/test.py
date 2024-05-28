"""
Dieses Skript erstellt umfangreiche SIARD- und ZIP-Dateien zu Testzwecken.
Die Dateien werden im Verzeichnis '/Users/python/Documents/Tests/Test Siard' gespeichert und der Erstellungsprozess wird im Verzeichnis 'logs' protokolliert.
"""

import os
import zipfile
import logging
import random
import string
from logging.handlers import RotatingFileHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
from faker import Faker
import shutil

# Verzeichnisse
LOG_DIR = 'logs'
UPLOAD_DIR = '/Users/python/Documents/Tests/Test Siard'
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Logging-Konfiguration
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler(os.path.join(LOG_DIR, 'creation.log'), maxBytes=1024*1024*10, backupCount=5)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger('creation')
logger.addHandler(handler)

fake = Faker()

# Beispiel-Automarken und -modelle
car_brands = [
    "Toyota Corolla", "Ford Fiesta", "Honda Civic", "Chevrolet Malibu", "BMW 3 Series",
    "Audi A4", "Mercedes-Benz C-Class", "Volkswagen Golf", "Hyundai Elantra", "Nissan Altima"
]

def random_string(length=8):
    """Erzeugt einen zufälligen String aus Buchstaben und Zahlen."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_random_driver_info():
    """Erzeugt zufällige Autofahrerinformationen."""
    car = random.choice(car_brands)
    return {
        "Vorname": fake.first_name(),
        "Nachname": fake.last_name(),
        "Adresse": fake.address().replace("\n", ", "),
        "Email": fake.email(),
        "Nummer": fake.phone_number(),
        "Kennzeichen": random_string(7),
        "Datum der Prüfung": fake.date(),
        "Auto Marke und Modell": car,
        "Geburtstag": fake.date_of_birth().strftime("%Y-%m-%d")
    }

def create_dummy_file(file_path):
    """
    Erstellt eine Dummy-Datei mit zufälligen Autofahrerinformationen.

    Args:
        file_path (str): Der Pfad zur zu erstellenden Datei.
    """
    logger.info(f"Creating dummy file: {file_path}")
    driver_info = create_random_driver_info()
    with open(file_path, 'w') as f:
        for key, value in driver_info.items():
            f.write(f"{key}: {value}\n")
    return file_path

def create_siard_file_chunked(siard_path, num_files, temp_dir):
    """
    Erstellt eine SIARD-Datei mit einer bestimmten Anzahl an Dummy-Dateien.

    Args:
        siard_path (str): Der Pfad zur zu erstellenden SIARD-Datei.
        num_files (int): Die Anzahl der Dummy-Dateien.
        temp_dir (str): Das temporäre Verzeichnis zur Speicherung der Dummy-Dateien.
    """
    logger.info(f"Creating SIARD file: {siard_path} with {num_files} files")
    with zipfile.ZipFile(siard_path, 'w') as siard_zip:
        with ThreadPoolExecutor() as executor:
            futures = []
            for i in range(num_files):
                dummy_file_path = os.path.join(temp_dir, f'dummy_file_{random_string()}.txt')
                futures.append(executor.submit(create_dummy_file, dummy_file_path))
            for future in as_completed(futures):
                dummy_file_path = future.result()
                siard_zip.write(dummy_file_path, os.path.basename(dummy_file_path))
                os.remove(dummy_file_path)

def create_zip_file_chunked(zip_path, num_files, temp_dir):
    """
    Erstellt eine ZIP-Datei mit einer bestimmten Anzahl an Dummy-Dateien.

    Args:
        zip_path (str): Der Pfad zur zu erstellenden ZIP-Datei.
        num_files (int): Die Anzahl der Dummy-Dateien.
        temp_dir (str): Das temporäre Verzeichnis zur Speicherung der Dummy-Dateien.
    """
    logger.info(f"Creating ZIP file: {zip_path} with {num_files} files")
    with zipfile.ZipFile(zip_path, 'w') as zip_file:
        with ThreadPoolExecutor() as executor:
            futures = []
            for i in range(num_files):
                dummy_file_path = os.path.join(temp_dir, f'dummy_file_{random_string()}.txt')
                futures.append(executor.submit(create_dummy_file, dummy_file_path))
            for future in as_completed(futures):
                dummy_file_path = future.result()
                zip_file.write(dummy_file_path, os.path.basename(dummy_file_path))
                os.remove(dummy_file_path)

def main():
    """
    Hauptfunktion zum Erstellen von SIARD- und ZIP-Dateien.
    """
    siard_path = os.path.join(UPLOAD_DIR, f'test_siard_{random_string()}.siard')
    zip_path = os.path.join(UPLOAD_DIR, f'test_zip_{random_string()}.zip')
    num_files = 10000  # Anzahl der Dummy-Dateien
    temp_dir = os.path.join('temp', random_string())

    # Sicherstellen, dass das temporäre Verzeichnis existiert
    os.makedirs(temp_dir, exist_ok=True)

    # Erstellung der SIARD- und ZIP-Dateien
    create_siard_file_chunked(siard_path, num_files, temp_dir)
    create_zip_file_chunked(zip_path, num_files, temp_dir)

    # Bereinigen des temporären Verzeichnisses
    shutil.rmtree(temp_dir)
    logger.info("SIARD and ZIP file creation completed.")

if __name__ == '__main__':
    main()
