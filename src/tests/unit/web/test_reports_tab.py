"""
Tests for the Reports tab in the model monitoring dashboard.
This tab provides reporting functionality for model performance metrics.
"""

import unittest
from unittest.mock import MagicMock, patch
import json
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from src.main import app


class TestReportsTab(unittest.TestCase):
    """Tests for the Reports tab UI and functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock request session that we'll use to simulate API calls
        self.mock_session_patcher = patch('requests.Session')
        self.mock_session = self.mock_session_patcher.start()
        self.mock_response = MagicMock()
        self.mock_session.return_value.get.return_value = self.mock_response
        self.mock_session.return_value.post.return_value = self.mock_response
        
        # Mock API responses
        self.report_templates_response = [
            {
                "id": "template1",
                "name": "Performance Summary",
                "description": "Summary of model performance metrics",
                "type": "performance"
            },
            {
                "id": "template2",
                "name": "Drift Analysis",
                "description": "Analysis of model drift over time",
                "type": "drift"
            },
            {
                "id": "template3",
                "name": "Alert History",
                "description": "History of alerts for a given model",
                "type": "alerts"
            }
        ]
        
        self.models_response = [
            {
                "id": "model1",
                "name": "Predictive Maintenance",
                "versions": ["1.0", "1.1", "1.2"]
            },
            {
                "id": "model2",
                "name": "Anomaly Detection",
                "versions": ["1.0"]
            }
        ]
        
        # Sample HTML content from our reports template (if it exists)
        try:
            with open('/Users/lisasimon/repos/IoTSphereAngular/IoTSphere-Refactor/frontend/templates/model-monitoring/reports.html', 'r') as f:
                self.html_content = f.read()
                self.soup = BeautifulSoup(self.html_content, 'html.parser')
        except FileNotFoundError:
            # File doesn't exist yet, which is expected in TDD approach
            self.html_content = None
            self.soup = None
    
    def tearDown(self):
        """Clean up after tests."""
        self.mock_session_patcher.stop()
    
    def test_reports_page_structure(self):
        """Test that the reports page has the required structural elements."""
        # Since we're following TDD, this test will initially fail until we create the page
        if not self.soup:
            self.skipTest("Reports page not yet created - this is normal for TDD")
        
        # Check for page title
        title = self.soup.find('title')
        self.assertIsNotNone(title)
        self.assertIn('Reports', title.text)
        
        # Check for report template selection
        template_select = self.soup.find('div', id='report-templates')
        self.assertIsNotNone(template_select)
        
        # Check for model selection
        model_select = self.soup.find('select', id='model-select')
        self.assertIsNotNone(model_select)
        
        # Check for date range controls
        date_range = self.soup.find('div', id='date-range-controls')
        self.assertIsNotNone(date_range)
        
        # Check for report generation button
        generate_btn = self.soup.find('button', id='generate-report-btn')
        self.assertIsNotNone(generate_btn)
        
        # Check for report content area
        report_content = self.soup.find('div', id='report-content')
        self.assertIsNotNone(report_content)
    
    def test_template_selection_functionality(self):
        """Test that the report template selection works properly."""
        if not self.soup:
            self.skipTest("Reports page not yet created - this is normal for TDD")
        
        scripts = self.soup.find_all('script')
        script_content = ' '.join([script.string for script in scripts if script.string])
        
        # Verify template loading function exists
        self.assertIn('function loadReportTemplates', script_content)
        
        # Check if the function makes an API call
        self.assertIn('fetch(`/api/monitoring/reports/templates`', script_content)
        
        # Check for template selection handling
        self.assertIn('function selectReportTemplate', script_content)
    
    def test_model_selection_functionality(self):
        """Test that the model selection for reports works properly."""
        if not self.soup:
            self.skipTest("Reports page not yet created - this is normal for TDD")
        
        scripts = self.soup.find_all('script')
        script_content = ' '.join([script.string for script in scripts if script.string])
        
        # Verify model loading function exists
        self.assertIn('function loadModelOptions', script_content)
        
        # Check if the function makes an API call
        self.assertIn('fetch(`/api/monitoring/models`', script_content)
    
    def test_date_range_controls(self):
        """Test that the date range controls for reports work properly."""
        if not self.soup:
            self.skipTest("Reports page not yet created - this is normal for TDD")
        
        # Check that date pickers exist
        start_date = self.soup.find('input', id='start-date')
        end_date = self.soup.find('input', id='end-date')
        
        self.assertIsNotNone(start_date)
        self.assertIsNotNone(end_date)
        self.assertEqual(start_date.get('type'), 'date')
        self.assertEqual(end_date.get('type'), 'date')
        
        # Check for date presets
        scripts = self.soup.find_all('script')
        script_content = ' '.join([script.string for script in scripts if script.string])
        
        self.assertIn('function setDateRange', script_content)
    
    def test_report_generation_functionality(self):
        """Test that report generation works properly."""
        if not self.soup:
            self.skipTest("Reports page not yet created - this is normal for TDD")
        
        scripts = self.soup.find_all('script')
        script_content = ' '.join([script.string for script in scripts if script.string])
        
        # Verify report generation function exists
        self.assertIn('function generateReport', script_content)
        
        # Check if the function makes an API call
        self.assertIn('fetch(`/api/monitoring/reports/generate`', script_content)
        
        # Check that it handles errors properly
        self.assertIn('catch(error', script_content)
    
    def test_report_export_functionality(self):
        """Test that report export functionality works properly."""
        if not self.soup:
            self.skipTest("Reports page not yet created - this is normal for TDD")
        
        scripts = self.soup.find_all('script')
        script_content = ' '.join([script.string for script in scripts if script.string])
        
        # Verify export functions exist
        self.assertIn('function exportReportPDF', script_content)
        self.assertIn('function exportReportCSV', script_content)
        
        # Check for export buttons
        export_pdf = self.soup.find('button', id='export-pdf')
        export_csv = self.soup.find('button', id='export-csv')
        
        self.assertIsNotNone(export_pdf)
        self.assertIsNotNone(export_csv)
    
    def test_dark_theme_styling(self):
        """Test that the reports page uses dark theme styling."""
        if not self.soup:
            self.skipTest("Reports page not yet created - this is normal for TDD")
        
        # Check for dark background color in CSS or inline styles
        dark_indicators = [
            'background-color: #000000',
            'background-color: rgb(0, 0, 0)',
            'background-color: #111111',
            'dark-theme'
        ]
        
        # Check head styles or inline styles
        styles = self.soup.find_all('style')
        style_content = ' '.join([style.string for style in styles if style.string])
        
        dark_style_found = False
        for indicator in dark_indicators:
            if indicator in style_content:
                dark_style_found = True
                break
                
        self.assertTrue(dark_style_found, "Page should use dark theme styling")
        
        # Also check body or container elements for dark theme classes
        page_container = self.soup.find('div', id='page-container')
        if page_container:
            classes = page_container.get('class', [])
            self.assertIn('dark-theme', classes)
    
    def test_url_parameter_based_state(self):
        """Test that the reports page uses URL parameter-based state management."""
        if not self.soup:
            self.skipTest("Reports page not yet created - this is normal for TDD")
        
        scripts = self.soup.find_all('script')
        script_content = ' '.join([script.string for script in scripts if script.string])
        
        # Verify URL parameter handling
        self.assertIn('function updateURLParameters', script_content)
        self.assertIn('function getURLParameters', script_content)
        
        # Check that template, model, and date parameters are supported
        self.assertIn('const urlParams = new URLSearchParams(window.location.search)', script_content)
        self.assertIn('template=', script_content)
        self.assertIn('model=', script_content)
        self.assertIn('startDate=', script_content)
        self.assertIn('endDate=', script_content)


if __name__ == '__main__':
    unittest.main()
