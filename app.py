from flask import Flask
from blueprints.search.routes import search_bp
import logging
from logging.config import dictConfig
import config
import webbrowser
import threading

def create_app():
    app = Flask(__name__)
    app.config.from_object(config.Config)

    dictConfig(app.config['LOGGING'])
    app.logger.info('Flask application starting...')

    app.register_blueprint(search_bp)

    return app

def open_browser():
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    app = create_app()

    # Starte einen neuen Thread, um den Browser zu öffnen, nachdem die Anwendung gestartet wurde
    threading.Timer(1, open_browser).start()

    app.run(debug=True)
