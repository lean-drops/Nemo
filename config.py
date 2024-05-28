import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': 'logs/app.log',
            },
        },
        'loggers': {
            'root': {
                'handlers': ['file'],
                'level': 'DEBUG',
            },
        },
    }
