"""
Tests for the Model Monitoring Dashboard UI rendering.
"""
import unittest
from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup

from src.web.templates.model_monitoring_dashboard import ModelMonitoringDashboard


class TestModelMonitoringUI(unittest.TestCase):
    """Tests for the Model Monitoring Dashboard UI rendering."""

    def test_dashboard_styling(self):
        """Test that the dashboard uses the correct styling and background colors."""
        dashboard = ModelMonitoringDashboard()
        html = dashboard.render()

        # Parse HTML to check styling
        soup = BeautifulSoup(html, "html.parser")

        # Check for dark background class
        dashboard_div = soup.find("div", class_="monitoring-dashboard")
        self.assertIsNotNone(dashboard_div)
        self.assertIn("dark-theme", dashboard_div.get("class", []))

    def test_models_rendering(self):
        """Test that models render correctly in the dashboard."""
        # Setup mock monitoring service with test data
        mock_service = MagicMock()
        mock_service.get_monitored_models.return_value = [
            {"id": "model1", "name": "Test Model", "versions": ["1.0", "1.1"]}
        ]

        dashboard = ModelMonitoringDashboard(monitoring_service=mock_service)
        html = dashboard.render()

        # Parse HTML to check model list rendering
        soup = BeautifulSoup(html, "html.parser")
        model_items = soup.find_all("li", class_="model-item")

        self.assertGreaterEqual(len(model_items), 1)
        self.assertIn("Test Model", model_items[0].text)

    def test_javascript_data_handling(self):
        """Test that the dashboard's JavaScript properly handles data."""
        dashboard = ModelMonitoringDashboard()
        html = dashboard.render()

        # Check for proper array handling in JavaScript
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.find_all("script")

        script_content = " ".join(
            [script.string for script in scripts if script.string]
        )

        # Verify the JavaScript handles both array and non-array responses
        self.assertIn("Array.isArray(models)", script_content)
        self.assertIn("models = []", script_content)
