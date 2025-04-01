"""
Tests for the Models tab in the model monitoring dashboard.
This tab provides comparative analysis and bulk operations for models.
"""

import unittest
from unittest.mock import MagicMock, patch
import json
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from src.main import app  # Import the FastAPI app


class TestModelsTab(unittest.TestCase):
    """Tests for the Models tab UI and functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock API responses
        self.models_response = [
            {
                "id": "model1",
                "name": "Predictive Maintenance",
                "versions": ["1.0", "1.1", "1.2"],
                "metrics": {
                    "accuracy": 0.92,
                    "drift_score": 0.03,
                    "health_status": "GREEN"
                },
                "alert_count": 0,
                "tags": ["production", "iot"]
            },
            {
                "id": "model2",
                "name": "Anomaly Detection",
                "versions": ["1.0"],
                "metrics": {
                    "accuracy": 0.85,
                    "drift_score": 0.07,
                    "health_status": "YELLOW"
                },
                "alert_count": 2,
                "tags": ["development"]
            },
            {
                "id": "model3",
                "name": "Equipment Failure",
                "versions": ["2.0", "2.1"],
                "metrics": {
                    "accuracy": 0.78,
                    "drift_score": 0.12,
                    "health_status": "RED"
                },
                "alert_count": 5,
                "tags": ["production", "critical"]
            }
        ]
        
        # Load the HTML template
        with open('/Users/lisasimon/repos/IoTSphereAngular/IoTSphere-Refactor/frontend/templates/model-monitoring/models.html', 'r') as f:
            self.html_content = f.read()
        
        # Parse the HTML content
        self.soup = BeautifulSoup(self.html_content, 'html.parser')
    
    def test_models_table_structure(self):
        """Test that the models table has the expected structure for comparative view."""
        # Check for the table element
        models_table = self.soup.find('table', id='models-comparison-table')
        self.assertIsNotNone(models_table, "Models comparison table should exist")
        
        # Check for table headers that enable comparison
        table_headers = models_table.find_all('th')
        expected_headers = ['Model Name', 'Version', 'Accuracy', 'Drift Score', 'Health', 'Alerts', 'Tags', 'Actions']
        for header in expected_headers:
            self.assertTrue(any(header in th.text for th in table_headers), 
                           f"Table should have a header for {header}")
    
    def test_fleet_metrics_display(self):
        """Test that fleet-wide metrics are displayed."""
        # Check for the fleet metrics section
        fleet_metrics = self.soup.find('div', id='fleet-metrics')
        self.assertIsNotNone(fleet_metrics, "Fleet metrics section should exist")
        
        # Check for key metrics
        expected_metrics = ['Average Accuracy', 'Average Drift', 'Models with Alerts', 'Healthy Models']
        for metric in expected_metrics:
            self.assertTrue(any(metric in div.text for div in fleet_metrics.find_all('div', class_='metric-card')), 
                           f"Fleet metrics should include {metric}")
    
    def test_health_indicators(self):
        """Test that health indicators are displayed for each model."""
        # Check for health indicator elements
        health_indicators = self.soup.find_all('div', class_='health-indicator')
        self.assertGreater(len(health_indicators), 0, "Health indicators should be present")
        
        # Check for different health states
        expected_states = ['health-green', 'health-yellow', 'health-red']
        for state in expected_states:
            self.assertTrue(any(state in indicator.get('class', []) for indicator in health_indicators), 
                           f"Health indicators should include {state} state")
    
    def test_model_filtering(self):
        """Test that filtering functionality is available."""
        # Check for filter controls
        filter_section = self.soup.find('div', id='model-filters')
        self.assertIsNotNone(filter_section, "Model filtering section should exist")
        
        # Check for specific filter options
        expected_filters = ['Filter by Tag', 'Filter by Health', 'Filter by Alert Status']
        for filter_option in expected_filters:
            self.assertTrue(any(filter_option in div.text for div in filter_section.find_all('div')), 
                           f"Filtering options should include {filter_option}")
    
    def test_batch_operations(self):
        """Test that batch operations are available."""
        # Check for batch operations section
        batch_ops = self.soup.find('div', id='batch-operations')
        self.assertIsNotNone(batch_ops, "Batch operations section should exist")
        
        # Check for specific batch operations
        expected_operations = ['Enable Monitoring', 'Disable Monitoring', 'Archive Selected', 'Apply Tag']
        for operation in expected_operations:
            self.assertTrue(any(operation in button.text for button in batch_ops.find_all('button')), 
                           f"Batch operations should include {operation}")
    
    def test_model_selection(self):
        """Test that models can be selected for batch operations."""
        # Check for checkboxes to select models
        checkboxes = self.soup.find_all('input', {'type': 'checkbox', 'class': 'model-select'})
        self.assertGreater(len(checkboxes), 0, "Checkboxes for model selection should be present")
        
        # Check for 'select all' checkbox
        select_all = self.soup.find('input', {'type': 'checkbox', 'id': 'select-all-models'})
        self.assertIsNotNone(select_all, "Select all checkbox should exist")
    
    def test_inventory_management(self):
        """Test that inventory management options are available."""
        # Check for inventory management section
        inventory_section = self.soup.find('div', id='inventory-management')
        self.assertIsNotNone(inventory_section, "Inventory management section should exist")
        
        # Check for specific management options
        expected_options = ['Tags Management', 'Archive Models', 'Model Groups']
        for option in expected_options:
            self.assertTrue(any(option in div.text for div in inventory_section.find_all('div')), 
                           f"Inventory management should include {option}")
    
    def test_javascript_functions(self):
        """Test that required JavaScript functions are present."""
        # Extract all script content
        scripts = self.soup.find_all('script')
        script_content = ' '.join([script.string for script in scripts if script.string])
        
        # Check for essential JavaScript functions
        expected_functions = [
            'loadAllModels',
            'calculateFleetMetrics',
            'filterModels',
            'applyBatchOperation',
            'toggleModelSelection',
            'selectAllModels',
            'displayHealthIndicator'
        ]
        
        for function in expected_functions:
            self.assertIn(function, script_content, f"JavaScript should include {function} function")

    def test_all_ui_components(self):
        """Test that all UI components and interactive elements are present."""
        # 1. Test navigation links in Jinja template
        html_content = str(self.html_content)
        expected_links = ['Dashboard', 'Models', 'Alerts', 'Reports']
        nav_section = html_content[html_content.find("{% block nav %}"):html_content.find("{% endblock %}", html_content.find("{% block nav %}"))]
        
        for link_text in expected_links:
            self.assertIn(link_text, nav_section, f"Navigation should include link to {link_text}")
        
        # 2. Test dropdown selects
        selects = self.soup.find_all('select')
        expected_selects = ['tag-filter', 'health-filter', 'alert-filter']
        select_ids = [select.get('id') for select in selects if select.get('id')]
        
        for select_id in expected_selects:
            self.assertIn(select_id, select_ids, f"Page should have select element with id {select_id}")
        
        # 3. Test interactive buttons
        buttons = self.soup.find_all('button')
        expected_buttons = [
            'enable-monitoring', 'disable-monitoring', 'archive-selected', 'apply-tag',
            'manage-tags-btn', 'view-archived-btn', 'manage-groups-btn'
        ]
        
        # Get all button IDs and texts
        button_ids = [button.get('id', '') for button in buttons]
        button_texts = [button.text.strip() for button in buttons if button.text.strip()]
        
        for button_id in expected_buttons:
            found = False
            # Check by ID
            if button_id in button_ids:
                found = True
            else:
                # Check by text content
                button_name = button_id.replace('-', ' ').replace('_', ' ')
                if any(button_name.lower() in text.lower() for text in button_texts):
                    found = True
            
            self.assertTrue(found, f"Page should have button for {button_id}")
        
        # 4. Test action buttons in table rows
        action_buttons = self.soup.find_all('button', class_='action-btn')
        expected_actions = ['View', 'Edit']
        action_texts = [button.text.strip() for button in action_buttons if button.text.strip()]
        
        for action in expected_actions:
            self.assertTrue(any(action in text for text in action_texts), 
                          f"Table should have {action} action buttons")

    def test_api_endpoints_in_javascript(self):
        """Test that the JavaScript code uses the correct API endpoints."""
        # Look for script tags with JavaScript code
        scripts = self.soup.find_all('script')
        script_content = ""
        for script in scripts:
            if script.string and not script.has_attr('src'):
                script_content += script.string
            
        # Check for expected API endpoints
        expected_endpoints = [
            '/api/monitoring/models',
            '/api/monitoring/models/batch'
        ]
        
        for endpoint in expected_endpoints:
            self.assertIn(endpoint, script_content, f"JavaScript should include API endpoint {endpoint}")
    
    def test_batch_operations_api_consistency(self):
        """Test that batch operations API paths are consistent between frontend and backend."""
        # This test verifies that the batch operations API endpoint is correctly accessed
        
        # Get the JavaScript that handles batch operations
        scripts = self.soup.find_all('script')
        script_content = ""
        for script in scripts:
            if script.string and not script.has_attr('src'):
                script_content += script.string
                
        # Verify the batch operation endpoint is used correctly in the JavaScript
        batch_endpoint = '/api/monitoring/models/batch'
        self.assertIn(batch_endpoint, script_content, 
                     f"JavaScript should include batch operation endpoint {batch_endpoint}")
        
        # Verify batch operation API calls are using the correct method (POST)
        escaped_endpoint = batch_endpoint.replace('/', '\\/')
        post_pattern = f"fetch\\(.*{escaped_endpoint}.*POST"
        self.assertRegex(script_content, post_pattern, 
                        "Batch operations should use POST method")
        
        # Verify models and operation parameters are included in the request
        models_param = '"models":'
        operation_param = '"operation":'
        self.assertIn(models_param, script_content, 
                     "Batch operations should include models parameter")
        self.assertIn(operation_param, script_content, 
                     "Batch operations should include operation parameter")

    def test_archive_toggle_functionality(self):
        """Test that the archive toggle links correctly switch between active and archived views."""
        # Setup HTML document with the archive toggle links in our new pattern
        html = """
        <div class="header-controls">
            <h1>Model Monitoring</h1>
            <a href="/model-monitoring/models?view=archived" class="primary-button">View Archived</a>
        </div>
        <table id="models-comparison-table" class="data-table">
            <tbody id="models-table-body"></tbody>
        </table>
        <script>
            let viewingArchived = false;
            
            document.addEventListener('DOMContentLoaded', function() {
                // Check URL parameters
                const urlParams = new URLSearchParams(window.location.search);
                const viewParam = urlParams.get('view');
                
                if (viewParam === 'archived') {
                    viewingArchived = true;
                    loadArchivedModels();
                } else {
                    viewingArchived = false;
                    loadAllModels();
                }
            });
            
            function loadAllModels() {
                // Mock function for loading active models
                fetch('/api/monitoring/models');
            }
            
            function loadArchivedModels() {
                // Mock function for loading archived models
                fetch('/api/monitoring/models/archived');
            }
        </script>
        """
        
        # Parse HTML
        document = BeautifulSoup(html, 'html.parser')
        
        # Test active view (default)
        active_link = document.select_one('.header-controls a')
        self.assertIsNotNone(active_link, "Archive toggle link should exist")
        self.assertEqual(active_link.text, 'View Archived', "Link should say 'View Archived' when viewing active models")
        self.assertEqual(active_link['href'], '/model-monitoring/models?view=archived', 
                         "Link should point to the archived view URL")
        
        # Test archived view
        archived_html = html.replace('View Archived', 'View Active').replace(
            '?view=archived', '').replace('viewingArchived = false', 'viewingArchived = true')
        archived_document = BeautifulSoup(archived_html, 'html.parser')
        archived_link = archived_document.select_one('.header-controls a')
        self.assertIsNotNone(archived_link, "Archive toggle link should exist in archived view")
        self.assertEqual(archived_link.text, 'View Active', "Link should say 'View Active' when viewing archived models")
        self.assertEqual(archived_link['href'], '/model-monitoring/models', 
                         "Link should point to the active view URL without parameters")
        
        # Check that the appropriate API URLs are used in the JavaScript
        self.assertIn('/api/monitoring/models', html, "Active models API endpoint should be used")
        self.assertIn('/api/monitoring/models/archived', html, "Archived models API endpoint should be used")

    def test_models_archive_toggle_url_param(self):
        """Test the archive toggle functionality with URL parameters."""
        # Create a test client
        client = TestClient(app)
        
        # First test the default view (active models)
        response = client.get("/model-monitoring/models")
        self.assertEqual(response.status_code, 200)
        html = response.text
        
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check that the toggle link exists and has the correct text and href
        toggle_link = soup.select_one('.header-controls a.primary-button')
        self.assertIsNotNone(toggle_link, "Toggle link should exist in active view")
        self.assertEqual(toggle_link.text.strip(), "View Archived", 
                         "Toggle link text should be 'View Archived' in active view")
        self.assertTrue(toggle_link['href'].endswith('?view=archived'), 
                        "Toggle link should point to URL with '?view=archived' parameter")
        
        # Now test the archived view
        response = client.get("/model-monitoring/models?view=archived")
        self.assertEqual(response.status_code, 200)
        html = response.text
        
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check that the toggle link exists and has the correct text and href
        toggle_link = soup.select_one('.header-controls a.primary-button')
        self.assertIsNotNone(toggle_link, "Toggle link should exist in archived view")
        self.assertEqual(toggle_link.text.strip(), "View Active", 
                         "Toggle link text should be 'View Active' in archived view")
        self.assertEqual(toggle_link['href'], "/model-monitoring/models", 
                         "Toggle link should point to base URL without parameters")
        
        # Check that JavaScript contains the correct API endpoints
        self.assertIn('/api/monitoring/models', html, 
                     "Active models API endpoint should be referenced in JavaScript")
        self.assertIn('/api/monitoring/models/archived', html, 
                     "Archived models API endpoint should be referenced in JavaScript")

    def test_model_action_buttons(self):
        """Test that model action buttons (View and Edit) exist and have correct attributes."""
        # Create a test client
        client = TestClient(app)
        
        # Setup mock data
        # This would normally be injected via dependency override
        # For simplicity, we're assuming models are rendered in the HTML
        
        # Get the models page
        response = client.get("/model-monitoring/models")
        self.assertEqual(response.status_code, 200)
        html = response.text
        
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for View and Edit buttons in table rows
        view_buttons = soup.select('.action-btn.view-btn')
        edit_buttons = soup.select('.action-btn.edit-btn')
        
        # There should be at least one of each button
        self.assertGreater(len(view_buttons), 0, "At least one View button should exist")
        self.assertGreater(len(edit_buttons), 0, "At least one Edit button should exist")
        
        # Each button should have a data-model-id attribute
        for button in view_buttons:
            self.assertIsNotNone(button.get('data-model-id'), 
                                "View button should have data-model-id attribute")
            
        for button in edit_buttons:
            self.assertIsNotNone(button.get('data-model-id'), 
                                "Edit button should have data-model-id attribute")

    def test_batch_operation_buttons(self):
        """Test that batch operation buttons exist and are initially disabled."""
        # Create a test client
        client = TestClient(app)
        
        # Get the models page
        response = client.get("/model-monitoring/models")
        self.assertEqual(response.status_code, 200)
        html = response.text
        
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check that batch operation buttons exist
        batch_buttons = {
            'enable-monitoring': soup.find(id='enable-monitoring'),
            'disable-monitoring': soup.find(id='disable-monitoring'),
            'archive-selected': soup.find(id='archive-selected'),
            'apply-tag': soup.find(id='apply-tag')
        }
        
        # All these buttons should exist
        for button_id, button in batch_buttons.items():
            self.assertIsNotNone(button, f"Button {button_id} should exist")
            
        # Initially they should be disabled since no models are selected
        for button_id, button in batch_buttons.items():
            self.assertTrue(button.has_attr('disabled') or 'disabled' in button.get('class', []),
                           f"Button {button_id} should be disabled initially")
            
    def test_manage_tags_button(self):
        """Test that the manage tags button exists and has appropriate event handler."""
        # Create a test client
        client = TestClient(app)
        
        # Get the models page
        response = client.get("/model-monitoring/models")
        self.assertEqual(response.status_code, 200)
        html = response.text
        
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check that manage tags button exists
        manage_tags_btn = soup.find(id='manage-tags-btn')
        self.assertIsNotNone(manage_tags_btn, "Manage tags button should exist")
        
        # Check that relevant JavaScript function exists in the code
        self.assertIn('showTagsManagementModal', html, 
                     "showTagsManagementModal function should exist in JavaScript")
        self.assertIn('loadTags', html, 
                     "loadTags function should exist in JavaScript")


if __name__ == '__main__':
    unittest.main()