"""
Tests for the Alert Configuration UI components.
"""
import unittest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
import json
import os

class TestAlertConfigurationUI(unittest.TestCase):
    """Tests for the alert configuration UI components."""
    
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
    
    def test_model_selection_ui_exists(self):
        """Test that model selection UI elements exist in the dashboard."""
        # Check if models container exists
        models_container = self.soup.find('div', id='models-list-container')
        self.assertIsNotNone(models_container)
        
        # Check for model list handling in JavaScript
        scripts = self.soup.find_all('script')
        script_content = ' '.join([script.string for script in scripts if script.string])
        
        # Verify model display function exists
        self.assertIn('function displayModels', script_content)
        
        # Verify click event handling for model selection
        self.assertIn('addEventListener(\'click\'', script_content)
        self.assertIn('classList.add(\'active\')', script_content)
    
    def test_alert_modal_exists(self):
        """Test that the alert configuration modal exists in the dashboard HTML."""
        # Check for alert configuration modal
        modal = self.soup.find('div', id='configure-alerts-modal')
        self.assertIsNotNone(modal)
        
        # Check for form elements
        form = modal.find('form', id='alert-rule-form')
        self.assertIsNotNone(form)
        
        # Check for required form fields with updated IDs (rule_name not rule-name)
        self.assertIsNotNone(form.find('input', id='rule_name'))
        self.assertIsNotNone(form.find('select', id='metric_name'))
        self.assertIsNotNone(form.find('select', id='operator'))
        self.assertIsNotNone(form.find('input', id='threshold'))
        self.assertIsNotNone(form.find('select', id='severity'))
        
        # Check for save button
        self.assertIsNotNone(form.find('button', id='save-alert-rule'))
    
    def test_configure_alerts_button_exists(self):
        """Test that the configure alerts button exists in the dashboard."""
        button = self.soup.find('button', id='configure-alerts-btn')
        
        self.assertIsNotNone(button)
        self.assertIn('Configure Alerts', button.text)
    
    def test_load_alert_rules_functionality(self):
        """Test the JavaScript function for loading alert rules."""
        scripts = self.soup.find_all('script')
        script_content = ' '.join([script.string for script in scripts if script.string])
        
        # Verify loadAlertRules function exists
        self.assertIn('function loadAlertRules', script_content)
        
        # Verify it handles API calls properly
        self.assertIn('fetch(`/api/monitoring/models/${modelId}/versions/${modelVersion}/alerts/rules`)', script_content)
        
        # Verify it populates the alert rules list
        self.assertIn('document.getElementById(\'alert-rules-list\').innerHTML', script_content)
    
    def test_create_alert_rule_functionality(self):
        """Test the JavaScript function for creating alert rules."""
        scripts = self.soup.find_all('script')
        script_content = ' '.join([script.string for script in scripts if script.string])
        
        # Verify form submission handling
        self.assertIn('addEventListener(\'submit\'', script_content)
        
        # Check for FormData usage which is what our implementation uses
        self.assertIn('formData.get(\'rule_name\')', script_content)
        
        # Verify it checks for model selection
        self.assertIn('document.querySelector(\'.model-item.active\')', script_content)
        
        # Verify it makes API calls
        self.assertIn('fetch(`/api/monitoring/models/${modelId}/versions/${modelVersion}/alerts/rules`', script_content)
        self.assertIn('method: \'POST\'', script_content)
        
        # Verify modal closes after save
        self.assertIn('modal.style.display = "none"', script_content)
    
    def test_alert_rule_display_after_save(self):
        """Test that new alert rules appear in the list after creation."""
        scripts = self.soup.find_all('script')
        script_content = ' '.join([script.string for script in scripts if script.string])
        
        # Verify the alert rules list is reloaded after creating a new rule
        self.assertIn('loadAlertRules(modelId, modelVersion)', script_content)
        
        # Verify alert rules are rendered to the alert-rules-list element
        self.assertIn('document.getElementById(\'alert-rules-list\').innerHTML', script_content)
        
        # Verify alert rule items include all necessary information
        self.assertIn('alert-rule-item', script_content)
    
    def test_delete_alert_rule_functionality(self):
        """Test the JavaScript function for deleting alert rules."""
        scripts = self.soup.find_all('script')
        script_content = ' '.join([script.string for script in scripts if script.string])
        
        # Verify delete function exists
        self.assertIn('function deleteAlertRule', script_content)
        
        # Verify it confirms before deletion
        self.assertIn('confirm(\'Are you sure', script_content)
        
        # Verify it makes API calls
        self.assertIn('fetch(`/api/monitoring/models/${modelId}/versions/${modelVersion}/alerts/rules/${ruleId}`', script_content)
        self.assertIn('method: \'DELETE\'', script_content)
    
    def test_model_selection_ui_interaction(self):
        """Test the model selection interaction without Selenium."""
        scripts = self.soup.find_all('script')
        script_content = ' '.join([script.string for script in scripts if script.string])
        
        # Verify model selection click event handling
        self.assertIn('item.addEventListener(\'click\'', script_content)
        
        # Verify active class management
        self.assertIn('classList.remove(\'active\')', script_content)
        self.assertIn('classList.add(\'active\')', script_content)
        
        # Verify the first model is set as active by default
        self.assertIn('firstModelElement.classList.add(\'active\')', script_content)
    
    def test_end_to_end_alert_flow(self):
        """Test the end-to-end alert configuration flow."""
        scripts = self.soup.find_all('script')
        script_content = ' '.join([script.string for script in scripts if script.string])
        
        # Check for the complete flow: select model -> open modal -> load rules -> add rule
        self.assertIn('addEventListener(\'click\'', script_content)  # Model selection click
        self.assertIn('configure-alerts-btn', script_content)  # Open modal button
        self.assertIn('loadAlertRules(modelId, modelVersion)', script_content)  # Load rules on model selection
        self.assertIn('alert-rule-form', script_content)  # Form for creating rules
        
        # Verify the flow is properly implemented
        self.assertIn('if (modelId && modelVersion)', script_content)  # Check model selection
    
    def test_alert_display_handles_triggered_at(self):
        """Test that alert display properly handles triggered_at timestamp field."""
        scripts = self.soup.find_all('script')
        script_content = ' '.join([script.string for script in scripts if script.string])
        
        # Verify the code checks for both triggered_at and timestamp fields
        self.assertIn('alert.triggered_at || alert.timestamp', script_content)
        
        # Verify the code has proper date formatting with error handling
        self.assertIn('formattedDate = new Date', script_content)
        self.assertIn('Invalid Date', script_content)

if __name__ == '__main__':
    unittest.main()
