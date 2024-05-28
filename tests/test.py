import zipfile
import os
import pandas as pd
from faker import Faker
import logging
import uuid

fake = Faker()

# Erwartete Schemas für die verschiedenen Datentypen
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

# Konfigurationsdatei
CONFIG = {
    "base_directory": "/Users/python/Documents/Tests/Test_Siard_Zips",
    "num_rows_per_file": 100,
    "num_txt_files_per_zip": 5,
    "log_file": "/Users/python/Documents/Tests/Test_Siard_Zips/logfile.log",
    "schema_file": "/Users/python/Documents/Tests/Test_Siard_Zips/schemas.txt"
}

def create_txt_file(file_path, schema, num_rows=100):
    data = []
    used_pins = set()
    for _ in range(num_rows):
        row = []
        for col in schema:
            if col == "PIN":
                pin = fake.unique.random_int(min=1, max=num_rows*100)
                while pin in used_pins:
                    pin = fake.unique.random_int(min=1, max=num_rows*100)
                used_pins.add(pin)
                row.append(pin)
            elif col == "HISTNR":
                row.append(fake.random_int(min=1, max=100))
            elif col in ["ID", "STAMM"]:
                row.append(fake.uuid4())
            elif col == "Name":
                row.append(fake.last_name())
            elif col == "Vorname":
                row.append(fake.first_name())
            elif col in ["Hersteller", "Modell", "Kategorie", "Fahrzeugtyp"]:
                row.append(fake.word())
            elif col == "Kennzeichen":
                row.append(fake.bothify(text='?? ### ??'))
            elif col == "Farbe":
                row.append(fake.safe_color_name())
            elif col == "Geburtsdatum":
                row.append(fake.date_of_birth(minimum_age=18, maximum_age=90))
            elif col in ["Ausstellungsdatum", "Gültigkeitsdatum", "Änderungsdatum", "Baujahr"]:
                row.append(fake.date_between(start_date='-30y', end_date='today'))
            elif col == "Adresse":
                row.append(fake.address().replace("\n", ", "))
            elif col == "Ausweisnummer":
                row.append(fake.bothify(text='??? ######'))
            elif col == "Fahrzeugausweisnummer":
                row.append(fake.bothify(text='?? ######'))
            elif col == "Motorleistung":
                row.append(fake.random_int(min=50, max=400))  # Motorleistung in PS
            elif col == "Kilometerstand":
                row.append(fake.random_int(min=0, max=300000))  # Kilometerstand
            else:
                row.append(fake.word())
        data.append(row)
    df = pd.DataFrame(data, columns=schema)
    df.to_csv(file_path, sep="\t", index=False)

def create_large_zip(zip_path, schema, num_rows=100, num_txt_files=5):
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for i in range(num_txt_files):
            file_name = f"{os.path.basename(zip_path).replace('.zip', '')}_{i+1}.txt"
            file_path = os.path.join("/tmp", file_name)
            create_txt_file(file_path, schema, num_rows)
            zipf.write(file_path, file_name)
            os.remove(file_path)
    return {
        "zip_name": os.path.basename(zip_path),
        "schema": schema
    }

def create_zip_files(directory, schemas, num_rows_per_file=100, num_txt_files_per_zip=5):
    unique_dir = os.path.join(directory, str(uuid.uuid4()))
    os.makedirs(unique_dir, exist_ok=True)
    all_schema_entries = []
    for name, schema in schemas.items():
        zip_path = os.path.join(unique_dir, f"{name}.zip")
        logging.debug(f"Creating ZIP file at: {zip_path}")
        schema_entry = create_large_zip(zip_path, schema, num_rows=num_rows_per_file, num_txt_files=num_txt_files_per_zip)
        all_schema_entries.append(schema_entry)
        logging.debug(f"Created ZIP file: {zip_path}")
    return all_schema_entries

def save_schemas_to_file(schema_entries, schema_file_path):
    with open(schema_file_path, 'w') as schema_file:
        for entry in schema_entries:
            schema_file.write(f"ZIP File: {entry['zip_name']}\nSchema: {', '.join(entry['schema'])}\n\n")

def initialize_logging(log_file):
    logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')

def main():
    initialize_logging(CONFIG["log_file"])
    logging.debug(f"Starting to create ZIP files at: {CONFIG['base_directory']}")
    schema_entries = create_zip_files(CONFIG["base_directory"], EXPECTED_SCHEMAS, num_rows_per_file=CONFIG["num_rows_per_file"], num_txt_files_per_zip=CONFIG["num_txt_files_per_zip"])
    save_schemas_to_file(schema_entries, CONFIG["schema_file"])
    logging.debug(f"Created test ZIP files at {CONFIG['base_directory']}")
    print(f"Created test ZIP files at {CONFIG['base_directory']}")

if __name__ == "__main__":
    main()
