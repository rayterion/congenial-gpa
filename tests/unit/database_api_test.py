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
        res = requests.post(self.base_url + "/clear")
        self.assertEqual(res.status_code, 200)

    def test_api_up(self):
        """ Tests that the API is up and running. """
        response = requests.get(self.base_url + "/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("healthy", response.text.lower())
    
    def test_api_cant_up_again(self):
        """ Tests that starting the API again raises an error. """
        with self.assertRaises(RuntimeError):
            self.db_api.start()

    def test_invalid_action(self):
        """ Tests that an invalid action returns a 400 error. """
        full_url = self.base_url + "/operation?action=invalid_action"
        response = requests.get(full_url)
        self.assertEqual(response.status_code, 400)

    def test_missing_action(self):
        """ Tests that missing action returns a 400 error. """
        full_url = self.base_url + "/operation"
        response = requests.get(full_url)
        self.assertEqual(response.status_code, 400)
    
    def test_post_missing_row(self):
        """ Tests that missing row returns a 400 error. """
        action = "post_cell"
        full_url = self.base_url + f"/operation?action={action}&column=abc&value=123"
        response = requests.post(full_url)
        self.assertEqual(response.status_code, 400)
    
    def test_get_missing_row(self):
        """ Tests that missing row returns a 400 error. For get cell """
        action = "get_cell"
        full_url = self.base_url + f"/operation?action={action}&column=abc"
        response = requests.get(full_url)
        self.assertEqual(response.status_code, 400)

    def test_post_missing_column(self):
        """ Tests that missing column returns a 400 error. """
        action = "post_cell"
        full_url = self.base_url + f"/operation?action={action}&row=0&value=123"
        response = requests.post(full_url)
        self.assertEqual(response.status_code, 400)
    
    def test_get_missing_column(self):
        """ Tests that missing column returns a 400 error. For get cell """
        action = "get_cell"
        full_url = self.base_url + f"/operation?action={action}&row=0"
        response = requests.get(full_url)
        self.assertEqual(response.status_code, 400)

    def test_post_missing_value(self):
        """ Tests that missing value returns a 400 error. """
        action = "post_cell"
        full_url = self.base_url + f"/operation?action={action}&column=abc&row=0"
        response = requests.post(full_url)
        self.assertEqual(response.status_code, 400)
    
    def test_get_nonexistent_cell(self):
        """ Tests that getting a non-existent cell returns a 404 error. """
        action = "get_cell"
        full_url = self.base_url + f"/operation?action={action}&column=nonexistent&row=999"
        response = requests.get(full_url)
        self.assertEqual(response.status_code, 404)

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
        res = requests.post(full_url_post)
        self.assertEqual(res.status_code, 200)

        # Now, get the cell value
        action_get = "get_cell"
        full_url_get = self.base_url + f"/operation?action={action_get}&column={column}&row={row}"
        response = requests.get(full_url_get)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, str(value))