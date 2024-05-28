import unittest
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
