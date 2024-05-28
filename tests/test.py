"""
Dieses Skript erstellt ein Verzeichnis mit 17 ZIP-Dateien, um die Extraktions- und Suchfunktionen zu testen.

Jede ZIP-Datei enthält Daten im Format der Viacar-Tabellen, wie in der Beschreibung angegeben.
"""

import zipfile
import os
import pandas as pd
from faker import Faker
import logging

# Logging-Konfiguration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

fake = Faker()

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

def create_txt_file(file_path, schema, num_rows=100):
    """
    Erstellt eine TXT-Datei mit zufälligen Daten gemäß dem angegebenen Schema.

    Args:
        file_path (str): Der Pfad zur zu erstellenden Datei.
        schema (list): Eine Liste der Spaltennamen.
        num_rows (int): Die Anzahl der Zeilen, die erstellt werden sollen.
    """
    logger.debug(f"Creating TXT file at: {file_path} with schema: {schema}")
    data = []
    for _ in range(num_rows):
        row = []
        for col in schema:
            if col in ["PIN", "ID", "STAMM"]:
                row.append(fake.uuid4())
            elif col in ["Name", "Vorname", "Hersteller", "Modell", "Kategorie", "Fahrzeugtyp", "Kennzeichen", "Farbe"]:
                row.append(fake.word())
            elif col in ["Geburtsdatum", "Ausstellungsdatum", "Gültigkeitsdatum", "Änderungsdatum", "Baujahr"]:
                row.append(fake.date())
            elif col == "Adresse":
                row.append(fake.address())
            elif col in ["Ausweisnummer", "Fahrzeugausweisnummer"]:
                row.append(fake.bothify(text='??######'))
            elif col in ["Motorleistung", "Kilometerstand"]:
                row.append(fake.random_int(min=0, max=100000))
            else:
                row.append(fake.word())
        data.append(row)

    df = pd.DataFrame(data, columns=schema)
    df.to_csv(file_path, sep="\t", index=False)
    logger.debug(f"Finished creating TXT file at: {file_path}")

def create_large_zip(zip_path, num_files=5, num_rows=100):
    """
    Erstellt eine große ZIP-Datei mit mehreren TXT-Dateien.

    Args:
        zip_path (str): Der Pfad zur zu erstellenden ZIP-Datei.
        num_files (int): Die Anzahl der TXT-Dateien, die erstellt werden sollen.
        num_rows (int): Die Anzahl der Zeilen pro Datei.
    """
    logger.debug(f"Creating ZIP file at: {zip_path} with {num_files} TXT files, each with {num_rows} rows")
    schemas = list(EXPECTED_SCHEMAS.values())
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for i in range(num_files):
            schema = schemas[i % len(schemas)]
            file_name = f"{fake.word()}_{i+1}.txt"
            file_path = os.path.join("/tmp", file_name)
            logger.debug(f"Creating TXT file {file_name} for ZIP {zip_path}")
            create_txt_file(file_path, schema, num_rows)
            zipf.write(file_path, file_name)
            os.remove(file_path)
            logger.debug(f"Added TXT file {file_name} to ZIP {zip_path}")
    logger.debug(f"Finished creating ZIP file at: {zip_path}")

def create_zip_directory(directory, num_zips=17, num_files_per_zip=5, num_rows_per_file=100):
    """
    Erstellt ein Verzeichnis mit mehreren ZIP-Dateien.

    Args:
        directory (str): Das Verzeichnis, das die ZIP-Dateien enthalten soll.
        num_zips (int): Die Anzahl der zu erstellenden ZIP-Dateien.
        num_files_per_zip (int): Die Anzahl der Dateien pro ZIP-Datei.
        num_rows_per_file (int): Die Anzahl der Zeilen pro Datei.
    """
    logger.debug(f"Creating directory {directory} with {num_zips} ZIP files")
    os.makedirs(directory, exist_ok=True)

    for i in range(num_zips):
        zip_path = os.path.join(directory, f"zipfile_{i+1}.zip")
        logger.debug(f"Creating ZIP file {zip_path}")
        create_large_zip(zip_path, num_files=num_files_per_zip, num_rows=num_rows_per_file)
        logger.debug(f"Finished creating ZIP file {zip_path}")
    logger.debug(f"Finished creating all ZIP files in directory {directory}")

if __name__ == "__main__":
    directory_path = "/Users/python/Documents/Tests/Test_Siard_Zips"
    logger.debug(f"Starting creation of test ZIP directory at {directory_path}")
    create_zip_directory(directory_path, num_zips=17, num_files_per_zip=5, num_rows_per_file=100)
    logger.debug(f"Created test ZIP directory at {directory_path}")
    print(f"Created test ZIP directory at {directory_path}")
