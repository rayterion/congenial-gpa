from unittest import TestCase
from services import InternalDatabaseService
import requests

class TestDatabaseAPI(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_api = InternalDatabaseService(port=1919)
        cls.db_api.start()
        cls.base_url = cls.db_api.base_url
    
    @classmethod
    def tearDownClass(cls):
        cls.db_api.stop()

    def setUp(self):
        # Clean up the database before each test
        self.db_api.clear_database()

    def test_api_up(self):
        """ Tests that the API is up and running. """
        response = requests.get(self.base_url + "/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("healthy", response.text.lower())

    def test_post_cell(self):
        """ Tests posting a cell to the database. """
        action = "post_cell"
        column = "hijab"
        row = 0
        value = 1028
        full_url = self.base_url + f"?action={action}&column={column}&row={row}&value={value}"
        response = requests.post(full_url)
        self.assertEqual(response.status_code, 200)
    
    def test_get_cell(self):
        """ Tests getting a cell from the database. """
        # First, post a cell to ensure it exists
        action_post = "post_cell"
        column = "kodwi"
        row = 0
        value = 2415
        full_url_post = self.base_url + f"/operation?action={action_post}&column={column}&row={row}&value={value}"
        requests.post(full_url_post)

        # Now, get the cell value
        action_get = "get_cell"
        full_url_get = self.base_url + f"/operation?action={action_get}&column={column}&row={row}"
        response = requests.get(full_url_get)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, str(value))