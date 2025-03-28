"""
Integration tests for API endpoints to ensure they're properly configured and accessible.
This test suite verifies that all API endpoints referenced in the frontend
actually exist and return proper responses, not 404 or 500 errors.
"""

import unittest
import re
import os
import json
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
import pytest
from pathlib import Path

# Import the main application
from src.main import app

class TestAPIEndpoints(unittest.TestCase):
    """Test all API endpoints used in the frontend to prevent 404 and 500 errors."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test client and parse all frontend files to extract API endpoints."""
        cls.client = TestClient(app)
        cls.frontend_dir = Path(__file__).parent.parent.parent.parent / "frontend"
        cls.api_endpoints = cls._extract_api_endpoints_from_frontend()
        cls.link_elements = cls._extract_link_elements_from_templates()
        cls.button_endpoints = cls._extract_button_endpoints_from_templates()
    
    @classmethod
    def _extract_api_endpoints_from_frontend(cls):
        """Extract all API endpoints referenced in JavaScript files."""
        api_endpoints = []
        js_files = []
        
        # Find all JS files in the frontend directory
        for root, _, files in os.walk(cls.frontend_dir / "static" / "js"):
            for file in files:
                if file.endswith('.js'):
                    js_files.append(os.path.join(root, file))
        
        # Regular expressions to identify API endpoints in JavaScript
        endpoint_patterns = [
            r"fetch\(['\"](?P<url>/api/[^'\"]+)['\"]",
            r"url:\s*['\"](?P<url>/api/[^'\"]+)['\"]",
            r"axios\.(?:get|post|put|delete)\(['\"](?P<url>/api/[^'\"]+)['\"]"
        ]
        
        # Extract endpoints from each JS file
        for js_file in js_files:
            with open(js_file, 'r') as f:
                content = f.read()
                for pattern in endpoint_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        url = match.group('url')
                        # Handle dynamic parameters in URLs
                        if url and '{' in url:
                            # Transform URLs like /api/models/{model_id} to /api/models/test-model
                            url = re.sub(r'\{([^}]+)\}', lambda m: f"test-{m.group(1)}", url)
                        if url:
                            # Extract HTTP method
                            if 'axios.get' in match.group(0) or ('fetch' in match.group(0) and 'GET' in content[match.start():match.start()+100]):
                                method = 'GET'
                            elif 'axios.post' in match.group(0) or ('fetch' in match.group(0) and 'POST' in content[match.start():match.start()+100]):
                                method = 'POST'
                            elif 'axios.put' in match.group(0) or ('fetch' in match.group(0) and 'PUT' in content[match.start():match.start()+100]):
                                method = 'PUT'
                            elif 'axios.delete' in match.group(0) or ('fetch' in match.group(0) and 'DELETE' in content[match.start():match.start()+100]):
                                method = 'DELETE'
                            else:
                                method = 'GET'  # Default to GET if can't determine
                            
                            api_endpoints.append({
                                'url': url, 
                                'method': method,
                                'source': os.path.basename(js_file)
                            })
        
        return api_endpoints
    
    @classmethod
    def _extract_link_elements_from_templates(cls):
        """Extract all link elements from HTML templates."""
        links = []
        template_files = []
        
        # Find all HTML files in the frontend templates directory
        for root, _, files in os.walk(cls.frontend_dir / "templates"):
            for file in files:
                if file.endswith('.html'):
                    template_files.append(os.path.join(root, file))
        
        # Extract links from each template file
        for template_file in template_files:
            with open(template_file, 'r') as f:
                try:
                    content = f.read()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Find all <a> tags with href
                    for a_tag in soup.find_all('a', href=True):
                        href = a_tag.get('href')
                        if href.startswith('/'):
                            links.append({
                                'url': href,
                                'text': a_tag.text.strip(),
                                'source': os.path.basename(template_file)
                            })
                except Exception as e:
                    print(f"Error parsing {template_file}: {str(e)}")
        
        return links
    
    @classmethod
    def _extract_button_endpoints_from_templates(cls):
        """Extract all button click handlers from HTML templates that might trigger API calls."""
        button_endpoints = []
        template_files = []
        
        # Find all HTML files in the frontend templates directory
        for root, _, files in os.walk(cls.frontend_dir / "templates"):
            for file in files:
                if file.endswith('.html'):
                    template_files.append(os.path.join(root, file))
        
        # Extract button handlers from each template file
        for template_file in template_files:
            with open(template_file, 'r') as f:
                try:
                    content = f.read()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Find all buttons with onclick handlers
                    for button in soup.find_all(['button', 'input'], type=['button', 'submit']):
                        onclick = button.get('onclick', '')
                        button_id = button.get('id', '')
                        button_text = button.text.strip()
                        
                        button_endpoints.append({
                            'id': button_id,
                            'text': button_text,
                            'handler': onclick,
                            'source': os.path.basename(template_file)
                        })
                        
                    # Find buttons via data attributes
                    for elem in soup.find_all(attrs={"data-action": True}):
                        action = elem.get('data-action', '')
                        elem_id = elem.get('id', '')
                        
                        button_endpoints.append({
                            'id': elem_id,
                            'text': elem.text.strip(),
                            'handler': action,
                            'source': os.path.basename(template_file)
                        })
                        
                except Exception as e:
                    print(f"Error parsing {template_file}: {str(e)}")
        
        return button_endpoints

    def test_all_api_endpoints_accessible(self):
        """Test that all API endpoints extracted from JS files are accessible."""
        for endpoint in self.api_endpoints:
            url = endpoint['url']
            method = endpoint['method']
            source = endpoint['source']
            
            with self.subTest(url=url, method=method, source=source):
                # Create a test payload for POST/PUT requests
                test_payload = {}
                if '/batch' in url:
                    test_payload = {
                        "models": ["test-model-1"],
                        "operation": "enable-monitoring"
                    }
                elif '/metrics' in url and method == 'POST':
                    test_payload = {
                        "metrics": {
                            "accuracy": 0.95,
                            "precision": 0.92
                        }
                    }
                
                # Make the request
                if method == 'GET':
                    response = self.client.get(url)
                elif method == 'POST':
                    response = self.client.post(url, json=test_payload)
                elif method == 'PUT':
                    response = self.client.put(url, json=test_payload)
                elif method == 'DELETE':
                    response = self.client.delete(url)
                
                # Check that we don't get 404 or 500 errors
                self.assertNotEqual(response.status_code, 404, 
                                   f"API endpoint {url} from {source} returned 404 Not Found")
                self.assertNotEqual(response.status_code, 500, 
                                   f"API endpoint {url} from {source} returned 500 Server Error")
                
                # Response code should be in the range 200-399
                self.assertTrue(200 <= response.status_code < 400,
                               f"API endpoint {url} from {source} returned status code {response.status_code}")
    
    def test_navigation_links_accessible(self):
        """Test that all navigation links in templates are accessible."""
        for link in self.link_elements:
            url = link['url']
            text = link['text']
            source = link['source']
            
            # Skip external links or anchor links
            if url.startswith('http') or url.startswith('#'):
                continue
                
            with self.subTest(url=url, text=text, source=source):
                response = self.client.get(url)
                
                # Check that we don't get 404 or 500 errors
                self.assertNotEqual(response.status_code, 404, 
                                   f"Navigation link {url} ({text}) from {source} returned 404 Not Found")
                self.assertNotEqual(response.status_code, 500, 
                                   f"Navigation link {url} ({text}) from {source} returned 500 Server Error")
    
    def test_critical_model_batch_operation_endpoint(self):
        """Specific test for the model batch operations endpoint that powers Enable/Disable buttons."""
        batch_endpoint = '/api/monitoring/models/batch'
        test_payload = {
            "models": ["test-model-1", "test-model-2"],
            "operation": "enable-monitoring"
        }
        
        response = self.client.post(batch_endpoint, json=test_payload)
        
        # This is the endpoint that was causing 404 errors with buttons
        self.assertNotEqual(response.status_code, 404, 
                           f"Critical batch operations endpoint {batch_endpoint} returned 404 Not Found")
        self.assertNotEqual(response.status_code, 500, 
                           f"Critical batch operations endpoint {batch_endpoint} returned 500 Server Error")
    
    def test_model_specific_endpoints(self):
        """Test model-specific endpoints with valid test IDs."""
        # Test the most important model-specific endpoints
        critical_endpoints = [
            {
                'url': '/api/monitoring/models/test-model/versions',
                'method': 'GET'
            },
            {
                'url': '/api/monitoring/models/test-model/versions/1.0/metrics',
                'method': 'GET'
            },
            {
                'url': '/api/monitoring/models/test-model/versions/1.0/summary',
                'method': 'GET'
            }
        ]
        
        for endpoint in critical_endpoints:
            url = endpoint['url']
            method = endpoint['method']
            
            with self.subTest(url=url, method=method):
                if method == 'GET':
                    response = self.client.get(url)
                else:
                    response = self.client.post(url, json={})
                
                # Check that we don't get 404 or 500 errors
                self.assertNotEqual(response.status_code, 404, 
                                   f"Critical model endpoint {url} returned 404 Not Found")
                self.assertNotEqual(response.status_code, 500, 
                                   f"Critical model endpoint {url} returned 500 Server Error")

if __name__ == '__main__':
    unittest.main()
