from unittest import TestCase
from src.services.database_api import DatabaseAPI
from scripts.dev_db import get_db_url
import requests
import time

class TestDatabaseAPI(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_api = DatabaseAPI(database_url=get_db_url(), port=4039)
        cls.db_api.start()
        time.sleep(2)  # Wait for the API to start
        cls.base_url = cls.db_api.base_url

    def test_api_up(self):
        """ Tests that the API is up and running. """
        response = requests.get(self.base_url)
        self.assertEqual(response.status_code, 200)  # Expecting 404 since root endpoint is not defined
        self.assertIn("healthy", response.text.lower())  # Confirming that the API is responding

    def test_post_cell(self):
        """ Tests posting a cell to the database. """
        full_url = self.base_url + "/my_table/my_row/my_column"
        response = requests.post(full_url, json={"data": "test_value"})
        self.assertEqual(response.status_code, 200)