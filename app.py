"""
Dieses Skript startet eine Flask-Webanwendung und öffnet den Standard-Webbrowser auf der Startseite der Anwendung.
Das Skript konfiguriert das Logging gemäß den Einstellungen in der Konfigurationsdatei und registriert einen Blueprint
für Suchfunktionen. Die Webanwendung wird im Debug-Modus ausgeführt.
"""

from flask import Flask
from blueprints.search.routes import search_bp
import logging
from logging.config import dictConfig
import config
import webbrowser
import threading

def create_app():
    """
    Erstellt und konfiguriert die Flask-Anwendung.

    Lädt die Konfiguration aus dem config.json-Modul, richtet das Logging ein und registriert den Such-Blueprint.

    Returns:
        Flask: Die konfigurierte Flask-Anwendung.
    """
    app = Flask(__name__)
    app.config.from_object(config.Config)

    # Konfiguriere das Logging gemäß den Einstellungen in der Konfigurationsdatei
    dictConfig(app.config['LOGGING'])

    detailed_logger = logging.getLogger('detailed')
    important_logger = logging.getLogger('important')
    error_logger = logging.getLogger('errors')

    detailed_logger.debug('Flask application configuration loaded.')
    detailed_logger.debug(f'Application config.json: {app.config}')

    # Registriere den Blueprint für die Suchfunktionen
    app.register_blueprint(search_bp)
    important_logger.info('Search blueprint registered.')

    return app

def open_browser():
    """
    Öffnet den Standard-Webbrowser und navigiert zur Startseite der Anwendung.
    """
    try:
        webbrowser.open('http://127.0.0.1:5000')
        logging.getLogger('important').info('Web browser opened successfully.')
    except Exception as e:
        logging.getLogger('errors').error(f'Failed to open web browser: {e}')

if __name__ == '__main__':
    detailed_logger = logging.getLogger('detailed')
    important_logger = logging.getLogger('important')
    error_logger = logging.getLogger('errors')

    # Erstelle die Flask-Anwendung
    app = create_app()

    # Log-Informationen zur Anwendung
    important_logger.info('Flask application created.')

    # Starte einen neuen Thread, um den Browser zu öffnen, nachdem die Anwendung gestartet wurde
    try:
        threading.Timer(1, open_browser).start()
        important_logger.info('Browser will be opened shortly...')
    except Exception as e:
        error_logger.error(f'Failed to start browser thread: {e}')

    # Starte die Flask-Anwendung im Debug-Modus
    try:
        app.run(debug=True)
        important_logger.info('Flask application running...')
    except Exception as e:
        error_logger.critical(f'Failed to run Flask application: {e}')
