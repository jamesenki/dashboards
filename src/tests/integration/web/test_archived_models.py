"""
Integration tests for archived models API endpoints and UI functionality.
These tests verify that the archived models functionality works correctly.
"""

import unittest
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup

# Import the main application
from src.main import app

class TestArchivedModels(unittest.TestCase):
    """Test archived models endpoints and UI."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test client."""
        cls.client = TestClient(app)
    
    def test_get_active_models(self):
        """Test that active models can be retrieved."""
        response = self.client.get("/api/monitoring/models")
        
        # Check response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check response is a list
        models = response.json()
        self.assertIsInstance(models, list)
        
        # Check all returned models are active (not archived)
        for model in models:
            self.assertIn("archived", model)
            self.assertFalse(model["archived"])
    
    def test_get_archived_models(self):
        """Test that archived models can be retrieved."""
        response = self.client.get("/api/monitoring/models/archived")
        
        # Check response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check response is a list
        models = response.json()
        self.assertIsInstance(models, list)
        
        # Check all returned models are archived
        for model in models:
            self.assertIn("archived", model)
            self.assertTrue(model["archived"])
    
    def test_active_view_ui(self):
        """Test that the active models view contains the correct toggle link."""
        # Request the models page (active view is default)
        response = self.client.get("/model-monitoring/models")
        self.assertEqual(response.status_code, 200)
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the toggle link
        toggle_link = soup.select_one('.header-controls a.primary-button')
        self.assertIsNotNone(toggle_link, "Toggle link should exist")
        
        # Check the link text and URL
        self.assertEqual(toggle_link.text.strip(), "View Archived",
                         "Toggle link should say 'View Archived' in active view")
        self.assertTrue(toggle_link['href'].endswith('?view=archived'),
                        "Toggle link should point to archived view URL")
    
    def test_archived_view_ui(self):
        """Test that the archived models view contains the correct toggle link."""
        # Request the models page with archived view parameter
        response = self.client.get("/model-monitoring/models?view=archived")
        self.assertEqual(response.status_code, 200)
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the toggle link
        toggle_link = soup.select_one('.header-controls a.primary-button')
        self.assertIsNotNone(toggle_link, "Toggle link should exist")
        
        # Check the link text and URL
        self.assertEqual(toggle_link.text.strip(), "View Active",
                         "Toggle link should say 'View Active' in archived view")
        self.assertEqual(toggle_link['href'], "/model-monitoring/models",
                         "Toggle link should point to active view URL")
    
    def test_archived_api_endpoints_in_javascript(self):
        """Test that the JavaScript code references the correct API endpoints."""
        # Request the models page
        response = self.client.get("/model-monitoring/models")
        self.assertEqual(response.status_code, 200)
        
        # Check if the API endpoints are correctly referenced in the JavaScript
        self.assertIn('/api/monitoring/models', response.text,
                      "Active models API endpoint should be referenced")
        self.assertIn('/api/monitoring/models/archived', response.text,
                      "Archived models API endpoint should be referenced")

if __name__ == '__main__':
    unittest.main()