"""
Tests for the model monitoring UI functionality.
These tests ensure that key UI elements function correctly.
"""

import unittest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from src.main import app
from src.monitoring.model_monitoring_service import ModelMonitoringService


class TestMonitoringUI(unittest.TestCase):
    """Test the model monitoring UI functionality."""
    
    def setUp(self):
        """Set up test client and common resources."""
        self.client = TestClient(app)
        
        # Mock data for models
        self.mock_models = [
            {
                "id": "model1",
                "name": "Test Model 1",
                "versions": ["1.0", "2.0"],
                "metrics": {
                    "accuracy": 0.95,
                    "drift_score": 0.05,
                    "health_status": "GREEN"
                },
                "alert_count": 0,
                "tags": ["production", "important"]
            },
            {
                "id": "model2",
                "name": "Test Model 2",
                "versions": ["1.0"],
                "metrics": {
                    "accuracy": 0.85,
                    "drift_score": 0.15,
                    "health_status": "YELLOW"
                },
                "alert_count": 2,
                "tags": ["development"]
            }
        ]
        
        # Mock data for archived models
        self.mock_archived_models = [
            {
                "id": "model3",
                "name": "Archived Model 1",
                "versions": ["1.0"],
                "metrics": {
                    "accuracy": 0.75,
                    "drift_score": 0.25,
                    "health_status": "RED"
                },
                "alert_count": 5,
                "tags": ["archived"],
                "archived": True
            }
        ]
    
    @patch('src.monitoring.model_monitoring_service.ModelMonitoringService.get_monitored_models')
    def test_enable_monitoring_ui_element(self, mock_get_all_models):
        """Test that enabling monitoring shows the monitoring status section."""
        # Set up mock
        mock_get_all_models.return_value = self.mock_models
        
        # Get the page
        response = self.client.get("/model-monitoring/models")
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check that monitoring status container exists but is hidden by default
        monitoring_status = soup.find(id='monitoring-status')
        self.assertIsNotNone(monitoring_status, "Monitoring status container should exist")
        
        # It should have a style attribute containing 'display: none'
        self.assertIn('display: none', monitoring_status.get('style', ''),
                      "Monitoring status should be hidden by default")
        
        # Ensure enable monitoring button exists
        enable_btn = soup.find(id='enable-monitoring')
        self.assertIsNotNone(enable_btn, "Enable monitoring button should exist")
        
        # Check if the JavaScript contains the required function to show the monitoring status
        self.assertIn('monitoring-status', response.text,
                     "Page should include JavaScript to handle monitoring status display")
        
        # Specifically check for the code that would set display to block
        monitoring_visibility_code = ".style.display = 'block'"
        self.assertIn(monitoring_visibility_code, response.text,
                     "JavaScript should contain code to show monitoring status")
    
    @patch('src.monitoring.model_monitoring_service.ModelMonitoringService.get_monitored_models')
    def test_manage_tags_ui_element(self, mock_get_all_models):
        """Test that manage tags button and modal exist and are properly configured."""
        # Set up mock
        mock_get_all_models.return_value = self.mock_models
        
        # Get the page
        response = self.client.get("/model-monitoring/models")
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check that manage tags button exists
        manage_tags_btn = soup.find(id='manage-tags-btn')
        self.assertIsNotNone(manage_tags_btn, "Manage tags button should exist")
        
        # Check that tags modal exists
        tags_modal = soup.find(id='tags-modal')
        self.assertIsNotNone(tags_modal, "Tags modal should exist")
        
        # It should have a style attribute containing 'display: none'
        self.assertIn('display: none', tags_modal.get('style', ''),
                     "Tags modal should be hidden by default")
        
        # Check that tags modal has a close button
        close_btn = tags_modal.select_one('.close-button')
        self.assertIsNotNone(close_btn, "Tags modal should have a close button")
        
        # Check for the JavaScript function to show the modal
        self.assertIn('showTagsManagementModal', response.text,
                     "Page should include JavaScript function to show tags modal")
        
        # Check for the code that would set the modal display to block
        modal_visibility_code = "tagsModal.style.display = 'block'"
        self.assertIn(modal_visibility_code, response.text,
                    "JavaScript should contain code to show tags modal")
    
    @patch('src.monitoring.model_monitoring_service.ModelMonitoringService.get_monitored_models')
    def test_view_edit_model_functionality(self, mock_get_all_models):
        """Test that view and edit buttons for models are properly configured."""
        # Set up mock with sample model data
        mock_get_all_models.return_value = [
            {
                "id": "test-model-1",
                "name": "Test Model 1",
                "versions": ["1.0"],
                "metrics": {
                    "accuracy": 0.95,
                    "drift_score": 0.05,
                    "health_status": "GREEN"
                },
                "alert_count": 0,
                "tags": ["production"]
            }
        ]
        
        # Get the page
        response = self.client.get("/model-monitoring/models")
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check that view buttons exist with proper data attributes
        view_buttons = soup.select('.action-btn.view-btn')
        self.assertTrue(len(view_buttons) > 0, "Page should have view buttons")
        
        for button in view_buttons:
            self.assertIsNotNone(button.get('data-model-id'),
                               "View button should have model ID data attribute")
        
        # Check that edit buttons exist with proper data attributes
        edit_buttons = soup.select('.action-btn.edit-btn')
        self.assertTrue(len(edit_buttons) > 0, "Page should have edit buttons")
        
        for button in edit_buttons:
            self.assertIsNotNone(button.get('data-model-id'),
                               "Edit button should have model ID data attribute")
        
        # Check for the JavaScript functions to handle view and edit
        self.assertIn('viewModel', response.text,
                    "Page should include JavaScript function to view model details")
        
        self.assertIn('editModel', response.text,
                    "Page should include JavaScript function to edit model")
        
        # Check that we avoid 404 errors by having inline handling
        # The function should NOT redirect to another page
        self.assertIn('model-detail-view', response.text,
                     "View function should create an inline detail view")
        
        self.assertIn('model-edit-view', response.text,
                     "Edit function should create an inline edit view")
    
    @patch('src.monitoring.model_monitoring_service.ModelMonitoringService.get_monitored_models')
    @patch('src.monitoring.model_monitoring_service.ModelMonitoringService.get_archived_models')
    def test_batch_operations_ui(self, mock_get_archived_models, mock_get_all_models):
        """Test batch operations UI elements and functionality."""
        # Set up mocks
        mock_get_all_models.return_value = self.mock_models
        mock_get_archived_models.return_value = self.mock_archived_models
        
        # Get the page
        response = self.client.get("/model-monitoring/models")
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check batch operation buttons exist
        batch_buttons = {
            'enable-monitoring': soup.find(id='enable-monitoring'),
            'disable-monitoring': soup.find(id='disable-monitoring'),
            'archive-selected': soup.find(id='archive-selected'),
            'apply-tag': soup.find(id='apply-tag')
        }
        
        for button_id, button in batch_buttons.items():
            self.assertIsNotNone(button, f"Button {button_id} should exist")
        
        # Check for "Select All" checkbox
        select_all = soup.find(id='select-all-models')
        self.assertIsNotNone(select_all, "Select All checkbox should exist")
        
        # Check if necessary JavaScript functions exist
        self.assertIn('applyBatchOperation', response.text,
                    "Page should include function to apply batch operations")
        
        self.assertIn('updateBatchActionsAvailability', response.text,
                    "Page should include function to update batch action availability")
    
    @patch('src.monitoring.model_monitoring_service.ModelMonitoringService.get_monitored_models')
    def test_css_styling_for_monitoring(self, mock_get_all_models):
        """Test that proper CSS styling for monitoring elements exists."""
        # Set up mock
        mock_get_all_models.return_value = self.mock_models
        
        # Get the page
        response = self.client.get("/model-monitoring/models")
        
        # Check for critical CSS classes
        css_classes = [
            # Monitoring status styling
            ".monitoring-status-container",
            ".status-details",
            
            # Modal styling
            ".modal",
            ".modal-content",
            
            # Model detail and edit views
            ".model-detail-modal",
            ".model-edit-modal",
            
            # Monitored model row styling
            ".monitoring-enabled"
        ]
        
        for css_class in css_classes:
            self.assertIn(css_class, response.text,
                         f"CSS class {css_class} should exist in the page")


if __name__ == '__main__':
    unittest.main()
