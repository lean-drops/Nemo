import os
import logging


def create_flask_project():
    # Direkt im aktuellen Verzeichnis arbeiten
    dirs = [
        'static',
        'static/css',
        'templates',
        'blueprints',
        'blueprints/search',
        'tests',
        'logs'
    ]

    files = {
        'app.py': app_py_content(),
        'static/css/style.css': style_css_content(),
        'templates/index.html': index_html_content(),
        'blueprints/search/__init__.py': blueprint_init_py_content(),
        'blueprints/search/routes.py': routes_py_content(),
        'tests/test_routes.py': test_routes_py_content(),
        'config.py': config_py_content(),
        'logs/app.log': ''
    }

    for directory in dirs:
        os.makedirs(directory, exist_ok=True)

    for file_path, content in files.items():
        with open(file_path, 'w') as file:
            file.write(content)

    print("Flask-Projekt erfolgreich erstellt.")


def app_py_content():
    return """from flask import Flask
from blueprints.search.routes import search_bp
import logging
from logging.config import dictConfig
import config

def create_app():
    app = Flask(__name__)
    app.config.from_object(config.Config)

    dictConfig(app.config['LOGGING'])
    app.logger.info('Flask application starting...')

    app.register_blueprint(search_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
"""


def style_css_content():
    return """body {
    font-family: Arial, sans-serif;
    background-color: #f0f0f0;
    margin: 0;
    padding: 0;
}

.container {
    width: 80%;
    margin: 0 auto;
    padding: 20px;
    background-color: #fff;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
    margin-top: 50px;
}

h1 {
    text-align: center;
    color: #333;
}

form {
    margin-bottom: 20px;
}

input[type="text"] {
    width: 100%;
    padding: 10px;
    margin: 10px 0;
    box-sizing: border-box;
}

input[type="submit"] {
    width: 100%;
    padding: 10px;
    background-color: #333;
    color: #fff;
    border: none;
    cursor: pointer;
}

input[type="submit"]:hover {
    background-color: #555;
}

.results {
    margin-top: 20px;
}
"""


def index_html_content():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SIARD Search</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="container">
        <h1>Search in SIARD File</h1>
        <form method="post" action="/search">
            <input type="text" name="query" placeholder="Enter your name...">
            <input type="submit" value="Search">
        </form>
        {% if results %}
        <div class="results">
            <h2>Results:</h2>
            <ul>
                {% for result in results %}
                <li>{{ result }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""


def blueprint_init_py_content():
    return ""


def routes_py_content():
    return """from flask import Blueprint, render_template, request, current_app

search_bp = Blueprint('search_bp', __name__)

@search_bp.route('/', methods=['GET', 'POST'])
def search():
    results = None
    if request.method == 'POST':
        query = request.form['query']
        current_app.logger.info(f'Search query received: {query}')
        # Hier können Sie die Suchlogik hinzufügen, um die SIARD-Datei zu durchsuchen
        # Zum Beispiel:
        # results = search_siard_file(query)
        results = ["Example result 1", "Example result 2"]  # Dummy-Daten
        current_app.logger.info(f'Search results: {results}')
    return render_template('index.html', results=results)
"""


def test_routes_py_content():
    return """import unittest
from app import create_app

class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True

    def test_search_page_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Search in SIARD File', response.data)

    def test_search_functionality(self):
        response = self.client.post('/search', data=dict(query='Test Name'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Example result 1', response.data)

if __name__ == '__main__':
    unittest.main()
"""


def config_py_content():
    return """import os

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
"""


if __name__ == '__main__':
    create_flask_project()
