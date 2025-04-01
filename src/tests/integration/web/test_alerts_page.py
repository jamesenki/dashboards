"""
Integration tests for the alerts page in the model monitoring dashboard.
"""
import unittest
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup
from src.main import app


class TestAlertsPage(unittest.TestCase):
    """Integration tests for the alerts page."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = TestClient(app)
    
    def test_alerts_page_loads(self):
        """Test that the alerts page loads successfully."""
        response = self.client.get("/model-monitoring/alerts")
        
        # This will fail with a 500 error
        self.assertEqual(response.status_code, 200, f"Response: {response.text}")
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for the presence of key elements
        self.assertIsNotNone(soup.find('table', id='alerts-table'))
        self.assertIsNotNone(soup.find('div', id='filter-controls'))
    
    def test_alerts_page_template_structure(self):
        """Test that the alerts page template has the correct structure."""
        with open('/Users/lisasimon/repos/IoTSphereAngular/IoTSphere-Refactor/frontend/templates/model-monitoring/alerts.html', 'r') as f:
            html_content = f.read()
        
        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Basic template structure checks
        # Verify the table exists in the template
        self.assertIn('alerts-table', html_content)
        
        # Check for navigation block
        self.assertIn('{% block nav %}', html_content)
        
        # Verify that active class is used for the alerts navigation link
        self.assertIn('/model-monitoring/alerts" class="active"', html_content)


if __name__ == '__main__':
    unittest.main()
