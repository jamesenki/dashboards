"""
Integration tests for archived models API endpoints.
These tests verify that the archived models functionality works correctly.
"""

import unittest
from fastapi.testclient import TestClient

# Import the main application
from src.main import app

class TestArchivedModels(unittest.TestCase):
    """Test archived models endpoints."""
    
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

if __name__ == '__main__':
    unittest.main()