import zipfile
import os
from flask import current_app

def extract_siard_file(siard_path, extract_to):
    try:
        with zipfile.ZipFile(siard_path, 'r') as siard_zip:
            siard_zip.extractall(extract_to)
        return True
    except Exception as e:
        with current_app.app_context():
            current_app.logger.error(f"Error extracting SIARD file: {e}")
        return False
