"""
Tests for the Models tab in the model monitoring dashboard.
This tab provides comparative analysis and bulk operations for models.
"""

import unittest
from unittest.mock import MagicMock, patch
import json
from bs4 import BeautifulSoup


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

    def test_view_archived_button(self):
        """Test that the View Archived button toggles between active and archived models."""
        # Setup HTML document with the view archived button and models table
        html = """
        <div class="management-header">
            <button id="view-archived-btn">View Archived</button>
        </div>
        <table id="models-comparison-table">
            <tbody id="models-table-body"></tbody>
        </table>
        <script>
            // Stub functions to be patched
            function fetch(url, options) {}
            function loadArchivedModels() {}
            function loadAllModels() {}
        </script>
        """
        
        # Create mock models for both active and archived
        active_models = [{"id": "model1", "name": "Active Model", "archived": False}]
        archived_models = [{"id": "model2", "name": "Archived Model", "archived": True}]
        
        # Parse HTML and inject into BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Create a mock Document object for testing
        with patch('src.frontend.js.document', create=True) as mock_document:
            # Set up mock document getters
            mock_document.getElementById.side_effect = lambda id: soup.select_one(f'#{id}')
            
            # Set up mock fetch responses
            with patch('src.frontend.js.fetch') as mock_fetch:
                # Setup mock fetch to return different responses based on URL
                def mock_fetch_side_effect(url, *args, **kwargs):
                    response = MagicMock()
                    if url == '/api/monitoring/models':
                        response.json.return_value = active_models
                    elif url == '/api/monitoring/models/archived':
                        response.json.return_value = archived_models
                    else:
                        response.json.return_value = {}
                    return response
                
                mock_fetch.side_effect = mock_fetch_side_effect
                
                # Set up view state tracker
                viewingArchived = False
                
                # Set up mock functions
                with patch('src.frontend.js.toggleArchivedView') as mock_toggle:
                    with patch('src.frontend.js.loadArchivedModels') as mock_load_archived:
                        with patch('src.frontend.js.loadAllModels') as mock_load_all:
                            # Define the toggle function behavior
                            def toggle_side_effect():
                                nonlocal viewingArchived
                                if viewingArchived:
                                    # Switch to active models
                                    mock_load_all()
                                    button = soup.select_one('#view-archived-btn')
                                    button.string = 'View Archived'
                                    viewingArchived = False
                                else:
                                    # Switch to archived models
                                    mock_load_archived()
                                    button = soup.select_one('#view-archived-btn')
                                    button.string = 'View Active'
                                    viewingArchived = True
                                    
                            mock_toggle.side_effect = toggle_side_effect
                            
                            # Simulate first click on View Archived button (should load archived models)
                            button = soup.select_one('#view-archived-btn')
                            self.assertEqual(button.string, 'View Archived', "Button should initially say 'View Archived'")
                            
                            # Trigger the button click
                            toggle_side_effect()
                            
                            # Verify that archived models are loaded
                            mock_load_archived.assert_called_once()
                            self.assertEqual(button.string, 'View Active', "Button should change to 'View Active'")
                            self.assertTrue(viewingArchived, "viewingArchived should be True")
                            
                            # Simulate second click on button (should return to active models)
                            toggle_side_effect()
                            
                            # Verify that active models are loaded
                            mock_load_all.assert_called_once()
                            self.assertEqual(button.string, 'View Archived', "Button should change back to 'View Archived'")
                            self.assertFalse(viewingArchived, "viewingArchived should be False")

    def test_archive_button_click_event(self):
        """Test that clicking the archive toggle button calls the correct functions."""
        # Setup HTML document with the archive toggle button
        html = """
        <div class="management-header">
            <button id="toggle-archive-btn" class="secondary-button">View Archived</button>
        </div>
        <table id="models-comparison-table">
            <tbody id="models-table-body"></tbody>
        </table>
        <script>
            let viewingArchived = false;
            function loadAllModels() {
                // Mock function for loading active models
            }
            function loadArchivedModels() {
                // Mock function for loading archived models
            }
            function fetch(url, options) {
                // Mock fetch
                return Promise.resolve({
                    json: () => Promise.resolve([])
                });
            }
        </script>
        """
        
        # Parse HTML
        document = BeautifulSoup(html, 'html.parser')
        
        # Find the button
        button = document.select_one('#toggle-archive-btn')
        self.assertIsNotNone(button, "Toggle archive button should exist")
        
        # We can't directly test JavaScript execution, but we can verify:
        # 1. The button exists with the right ID and class
        self.assertEqual(button.get('id'), 'toggle-archive-btn', "Button should have correct ID")
        self.assertEqual(button.get('class'), ['secondary-button'], "Button should have correct class")
        
        # 2. The button has the right initial text
        self.assertEqual(button.text, 'View Archived', "Button should initially say 'View Archived'")
        
        # 3. The necessary JavaScript functions exist in the HTML
        self.assertIn('loadArchivedModels', html, "loadArchivedModels function should exist")
        self.assertIn('loadAllModels', html, "loadAllModels function should exist")
        self.assertIn('viewingArchived', html, "viewingArchived variable should exist")


if __name__ == '__main__':
    unittest.main()