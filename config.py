import os
from logging.config import dictConfig

class Config:
    # Geheime Schlüssel für Sicherheitsfunktionen
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    # Log-Verzeichnis erstellen, falls es nicht existiert
    LOG_DIR = 'logs'
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # Logging-Konfiguration
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,  # Vorhandene Logger nicht deaktivieren
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',  # Format der Log-Nachrichten
            },
            'detailed': {
                'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] in %(module)s: %(message)s',
                # Detailliertes Format der Log-Nachrichten
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',  # Ausgabe in die Konsole
                'formatter': 'default',
                'level': 'INFO',  # Log-Level für die Konsole
            },
            'detailed_file': {
                'class': 'logging.handlers.RotatingFileHandler',  # Rotierende Datei-Logs
                'formatter': 'detailed',
                'level': 'DEBUG',  # Log-Level für die detaillierte Datei
                'filename': os.path.join(LOG_DIR, 'detailed.log'),  # Detaillierte Log-Datei
                'maxBytes': 1024 * 1024 * 10,  # Maximal 10MB pro Log-Datei
                'backupCount': 5,  # Bis zu 5 Backup-Dateien behalten
            },
            'important_file': {
                'class': 'logging.handlers.RotatingFileHandler',  # Rotierende Datei-Logs
                'formatter': 'default',
                'level': 'INFO',  # Log-Level für wichtige Ereignisse
                'filename': os.path.join(LOG_DIR, 'important.log'),  # Log-Datei für wichtige Ereignisse
                'maxBytes': 1024 * 1024 * 10,  # Maximal 10MB pro Log-Datei
                'backupCount': 5,  # Bis zu 5 Backup-Dateien behalten
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',  # Rotierende Datei-Logs
                'formatter': 'default',
                'level': 'ERROR',  # Log-Level für Fehler
                'filename': os.path.join(LOG_DIR, 'errors.log'),  # Fehler-Log-Datei
                'maxBytes': 1024 * 1024 * 10,  # Maximal 10MB pro Log-Datei
                'backupCount': 5,  # Bis zu 5 Backup-Dateien behalten
            },
        },
        'loggers': {
            'detailed': {
                'handlers': ['detailed_file'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'important': {
                'handlers': ['important_file', 'console'],
                'level': 'INFO',
                'propagate': False,
            },
            'errors': {
                'handlers': ['error_file', 'console'],
                'level': 'ERROR',
                'propagate': False,
            },
        }
    }

# Logging-Konfiguration anwenden
dictConfig(Config.LOGGING)
