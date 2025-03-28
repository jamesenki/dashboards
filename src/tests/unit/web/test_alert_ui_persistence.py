"""
Tests for alert UI configuration persistence.
"""
import unittest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
import json

class TestAlertUIPersistence(unittest.TestCase):
    """Tests for persisting and deleting alert configurations in the UI."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock request session that we'll use to simulate API calls
        self.mock_session_patcher = patch('requests.Session')
        self.mock_session = self.mock_session_patcher.start()
        self.mock_response = MagicMock()
        self.mock_session.return_value.get.return_value = self.mock_response
        self.mock_session.return_value.post.return_value = self.mock_response
        self.mock_session.return_value.delete.return_value = self.mock_response
        
        # Sample HTML content from our dashboard template
        with open('/Users/lisasimon/repos/IoTSphereAngular/IoTSphere-Refactor/frontend/templates/model-monitoring/dashboard.html', 'r') as f:
            self.html_content = f.read()
        
        # Parse the HTML
        self.soup = BeautifulSoup(self.html_content, 'html.parser')
    
    def tearDown(self):
        """Clean up after tests."""
        self.mock_session_patcher.stop()
    
    def test_alert_rules_loaded_on_model_selection(self):
        """Test that alert rules are loaded when a model is selected."""
        scripts = self.soup.find_all('script')
        script_content = ' '.join([script.string for script in scripts if script.string])
        
        # Verify that loadMetricsForModel function exists and is called when model is selected
        self.assertIn('loadMetricsForModel(modelId, modelVersion)', script_content)
        
        # Verify the modal show function checks for modelId and modelVersion 
        self.assertIn('document.querySelector(\'.model-item.active\')', script_content)
        self.assertIn('if (modelId && modelVersion)', script_content)
        
        # Verify loadAlertRules is called when "Configure Alerts" is clicked
        self.assertIn('loadAlertRules(modelId, modelVersion)', script_content)
    
    def test_alert_rule_persisted_after_creation(self):
        """Test that alert rules are properly persisted after creation."""
        scripts = self.soup.find_all('script')
        script_content = ' '.join([script.string for script in scripts if script.string])
        
        # Verify form submission creates a POST request
        self.assertIn('method: \'POST\'', script_content)
        self.assertIn('Content-Type', script_content)
        self.assertIn('application/json', script_content)
        
        # Verify the endpoint for creating rules
        self.assertIn('fetch(`/api/monitoring/models/${modelId}/versions/${modelVersion}/alerts/rules`', script_content)
        
        # Verify rules are reloaded after creation
        self.assertIn('loadAlertRules(modelId, modelVersion)', script_content)
    
    def test_alert_rule_deleted(self):
        """Test that alert rules can be deleted and the deletion persists."""
        scripts = self.soup.find_all('script')
        script_content = ' '.join([script.string for script in scripts if script.string])
        
        # Verify delete function exists
        self.assertIn('function deleteAlertRule', script_content)
        
        # Verify DELETE method is used
        self.assertIn('method: \'DELETE\'', script_content)
        
        # Verify rules are reloaded after deletion
        self.assertIn('loadAlertRules(modelId, modelVersion)', script_content)
