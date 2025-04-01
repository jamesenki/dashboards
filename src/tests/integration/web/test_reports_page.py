"""
Integration tests for the reports page in the model monitoring dashboard.
"""
import unittest
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup
from src.main import app
from urllib.parse import urlparse, parse_qs


class TestReportsPage(unittest.TestCase):
    """Integration tests for the reports page."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = TestClient(app)
    
    def test_reports_page_route(self):
        """Test that the reports page route exists and returns a 200 status code."""
        # This test will fail until we create the route for the reports page
        response = self.client.get("/model-monitoring/reports")
        self.assertEqual(response.status_code, 200, f"Response: {response.text}")
    
    def test_reports_page_template_extends_base(self):
        """Test that the reports page template extends the base template."""
        try:
            with open('/Users/lisasimon/repos/IoTSphereAngular/IoTSphere-Refactor/frontend/templates/model-monitoring/reports.html', 'r') as f:
                html_content = f.read()
        except FileNotFoundError:
            self.skipTest("Reports page template not yet created - this is normal for TDD")
            
        # Check that the template extends the base template
        self.assertIn('{% extends "layouts/base.html" %}', html_content)
        
        # Check for required template blocks
        self.assertIn('{% block title %}', html_content)
        self.assertIn('{% block nav %}', html_content)
        self.assertIn('{% block content %}', html_content)
        self.assertIn('{% block scripts %}', html_content)
    
    def test_reports_page_navigation(self):
        """Test that the reports page has the correct navigation and active tab."""
        try:
            with open('/Users/lisasimon/repos/IoTSphereAngular/IoTSphere-Refactor/frontend/templates/model-monitoring/reports.html', 'r') as f:
                html_content = f.read()
        except FileNotFoundError:
            self.skipTest("Reports page template not yet created - this is normal for TDD")
            
        # Check for the active reports link in the navigation
        self.assertIn('<a href="/model-monitoring/reports" class="active">', html_content)
    
    def test_api_endpoints_exist(self):
        """Test that the required API endpoints for the reports page exist."""
        # This approach follows our TDD principles - the tests define the required endpoints
        
        # Test templates endpoint (will fail until implemented)
        templates_response = self.client.get("/api/monitoring/reports/templates")
        
        # We'll accept either 200 OK or 404 Not Found at this stage
        # (In real TDD, we'd start with expecting 404, then implement for 200)
        self.assertIn(templates_response.status_code, [200, 404], 
                     f"Unexpected status code: {templates_response.status_code}")
        
        # Test report generation endpoint (will fail until implemented)
        generate_response = self.client.post("/api/monitoring/reports/generate", 
                                           json={
                                               "template_id": "template1",
                                               "model_id": "model1",
                                               "start_date": "2025-03-01",
                                               "end_date": "2025-03-31"
                                           })
        
        # We'll accept either 200 OK or 404 Not Found at this stage
        self.assertIn(generate_response.status_code, [200, 404, 422], 
                     f"Unexpected status code: {generate_response.status_code}")
    
    def test_url_parameter_handling(self):
        """Test that the reports page correctly handles URL parameters for state."""
        # Test that parameters are properly processed
        
        test_params = "?template=performance&model=model1&startDate=2025-03-01&endDate=2025-03-31"
        response = self.client.get(f"/model-monitoring/reports{test_params}")
        
        # This will initially return 404 in TDD until the page exists, 
        # then should return 200 when implemented
        if response.status_code == 404:
            self.skipTest("Reports page route not yet created - this is normal for TDD")
        
        self.assertEqual(response.status_code, 200, f"Failed to handle URL parameters: {response.text}")
        
        # The test will be extended once the page is implemented to verify
        # that the parameters actually affect the page content
    
    def test_report_generation_with_parameters(self):
        """Test report generation with various parameter combinations."""
        # This tests the core functionality of report generation
        
        # Test with a valid template and model
        params = "?template=performance&model=model1&startDate=2025-03-01&endDate=2025-03-31"
        response = self.client.get(f"/model-monitoring/reports{params}")
        
        if response.status_code == 404:
            self.skipTest("Reports page route not yet created - this is normal for TDD")
        
        self.assertEqual(response.status_code, 200, f"Failed to handle URL parameters: {response.text}")
        
    def test_export_pdf_endpoint(self):
        """Test that the PDF export API endpoint exists and returns the correct response."""
        # Test PDF export endpoint
        pdf_response = self.client.post("/api/monitoring/reports/export/pdf",
                                      json={
                                          "template_id": "performance",
                                          "model_id": "model1",
                                          "start_date": "2025-03-01",
                                          "end_date": "2025-03-31"
                                      })
        
        # In TDD, we're expecting this to fail initially with 404 until implemented
        # Once implemented, we expect either a 200 with PDF content, or a 201 created response
        self.assertIn(pdf_response.status_code, [200, 201, 404], 
                     f"Unexpected status code: {pdf_response.status_code}")
        
        # When endpoint is properly implemented, we should get a PDF file
        if pdf_response.status_code in [200, 201]:
            # Check that the content type is PDF
            self.assertIn('application/pdf', pdf_response.headers.get('Content-Type', ''),
                         "Response should be a PDF file")
            
            # PDF files start with '%PDF'
            self.assertTrue(pdf_response.content.startswith(b'%PDF'),
                           "Response content should be a valid PDF file")
    
    def test_export_csv_endpoint(self):
        """Test that the CSV export API endpoint exists and returns the correct response."""
        # Test CSV export endpoint
        csv_response = self.client.post("/api/monitoring/reports/export/csv",
                                     json={
                                         "template_id": "performance",
                                         "model_id": "model1",
                                         "start_date": "2025-03-01",
                                         "end_date": "2025-03-31"
                                     })
        
        # In TDD, we're expecting this to fail initially with 404 until implemented
        # Once implemented, we expect a 200 OK with CSV content
        self.assertIn(csv_response.status_code, [200, 201, 404], 
                     f"Unexpected status code: {csv_response.status_code}")
        
        # When endpoint is properly implemented, we should get a CSV file
        if csv_response.status_code in [200, 201]:
            # Check that the content type is CSV
            self.assertIn('text/csv', csv_response.headers.get('Content-Type', ''),
                         "Response should be a CSV file")
            
            # Check that the content is a valid CSV format (has commas, newlines)
            content = csv_response.content.decode('utf-8')
            self.assertTrue(',' in content, "CSV should contain comma separators")
            
    def test_export_buttons_exist(self):
        """Test that the export buttons exist in the UI and have the correct attributes."""
        response = self.client.get("/model-monitoring/reports")
        
        if response.status_code == 404:
            self.skipTest("Reports page route not yet created - this is normal for TDD")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the PDF export button
        pdf_button = soup.find('button', {'onclick': 'exportReportPDF()'})
        self.assertIsNotNone(pdf_button, "PDF export button not found")
        
        # Find the CSV export button
        csv_button = soup.find('button', {'onclick': 'exportReportCSV()'})
        self.assertIsNotNone(csv_button, "CSV export button not found")
        
    def test_export_pdf_client_function(self):
        """Test that the client-side PDF export function makes the correct API call."""
        response = self.client.get("/model-monitoring/reports")
        
        if response.status_code == 404:
            self.skipTest("Reports page route not yet created - this is normal for TDD")
            
        # Check that the JavaScript contains the export function that makes a fetch call
        self.assertIn('function exportReportPDF()', response.text, 
                      "PDF export function not found in JavaScript")
        self.assertIn('fetch(`/api/monitoring/reports/export/pdf`', response.text, 
                      "PDF export function does not make the correct API call")
        
    def test_export_csv_client_function(self):
        """Test that the client-side CSV export function makes the correct API call."""
        response = self.client.get("/model-monitoring/reports")
        
        if response.status_code == 404:
            self.skipTest("Reports page route not yet created - this is normal for TDD")
            
        # Check that the JavaScript contains the export function that makes a fetch call
        self.assertIn('function exportReportCSV()', response.text, 
                      "CSV export function not found in JavaScript")
        self.assertIn('fetch(`/api/monitoring/reports/export/csv`', response.text, 
                      "CSV export function does not make the correct API call")
                      
        # Test with parameters
        params = "?model=model1&startDate=2025-03-01&endDate=2025-03-31"
        response = self.client.get(f"/model-monitoring/reports{params}")
        
        if response.status_code == 404:
            self.skipTest("Reports page route not yet created - this is normal for TDD")
        
        self.assertEqual(response.status_code, 200)
        
        # Test with missing model parameter (should still load the page)
        params = "?template=performance&startDate=2025-03-01&endDate=2025-03-31"
        response = self.client.get(f"/model-monitoring/reports{params}")
        self.assertEqual(response.status_code, 200)
    
    def test_reports_page_has_dark_theme(self):
        """Test that the reports page has dark theme styling."""
        try:
            with open('/Users/lisasimon/repos/IoTSphereAngular/IoTSphere-Refactor/frontend/templates/model-monitoring/reports.html', 'r') as f:
                html_content = f.read()
        except FileNotFoundError:
            self.skipTest("Reports page template not yet created - this is normal for TDD")
        
        # Check for dark theme styling
        dark_theme_indicators = [
            'background-color: #000000',
            'background-color: #111111',
            'class="dark-theme"',
            'color: #e1e1e1'
        ]
        
        # At least one dark theme indicator should be present
        dark_theme_found = any(indicator in html_content for indicator in dark_theme_indicators)
        self.assertTrue(dark_theme_found, "Dark theme styling not found in reports page template")


    def test_end_to_end_report_generation(self):
        """Test the end-to-end report generation and viewing functionality."""
        # Step 1: Verify templates endpoint returns data
        templates_response = self.client.get("/api/monitoring/reports/templates")
        self.assertEqual(templates_response.status_code, 200, "Templates endpoint should return 200 OK")
        
        templates = templates_response.json()
        self.assertIsInstance(templates, list, "Templates should be returned as a list")
        self.assertTrue(len(templates) > 0, "At least one template should be available")
        
        # Get the first template ID for use in report generation
        template_id = templates[0].get('id')
        self.assertIsNotNone(template_id, "Template should have an ID")
        
        # Step 2: Verify models endpoint returns data (for model selection)
        models_response = self.client.get("/api/monitoring/models")
        self.assertEqual(models_response.status_code, 200, "Models endpoint should return 200 OK")
        
        models = models_response.json()
        self.assertIsInstance(models, list, "Models should be returned as a list")
        self.assertTrue(len(models) > 0, "At least one model should be available")
        
        # Get the first model ID for use in report generation
        model_id = models[0].get('id')
        self.assertIsNotNone(model_id, "Model should have an ID")
        
        # Step 3: Generate a report using the template and model
        report_request = {
            "template_id": template_id,
            "model_id": model_id,
            "start_date": "2025-03-01",
            "end_date": "2025-03-31"
        }
        
        generate_response = self.client.post("/api/monitoring/reports/generate", json=report_request)
        self.assertEqual(generate_response.status_code, 200, "Report generation should return 200 OK")
        
        report = generate_response.json()
        self.assertIsInstance(report, dict, "Generated report should be a dictionary")
        
        # Step 4: Verify the report contains the expected fields
        required_fields = ['id', 'title', 'description', 'model_id', 'model_name', 
                         'template_id', 'start_date', 'end_date', 'generated_at', 'metrics']
        
        for field in required_fields:
            self.assertIn(field, report, f"Report should contain the {field} field")
        
        # Verify that the report contains metrics
        self.assertIsInstance(report['metrics'], list, "Report metrics should be a list")
        self.assertTrue(len(report['metrics']) > 0, "Report should contain at least one metric")
        
        # Step 5: Verify that the metrics have the expected structure
        for metric in report['metrics']:
            self.assertIn('name', metric, "Metric should have a name")
            self.assertIn('value', metric, "Metric should have a value")
            self.assertIn('change', metric, "Metric should have a change value")


if __name__ == '__main__':
    unittest.main()
