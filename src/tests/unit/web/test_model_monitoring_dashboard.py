"""
Tests for the Model Monitoring Dashboard UI component.
"""
import unittest
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.web.routes import router
from src.web.templates.model_monitoring_dashboard import ModelMonitoringDashboard


class TestModelMonitoringDashboard(unittest.TestCase):
    """Tests for the Model Monitoring Dashboard UI component."""

    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

    def test_dashboard_init(self):
        """Test initialization of the dashboard."""
        dashboard = ModelMonitoringDashboard()
        self.assertIsNotNone(dashboard)
        self.assertEqual(dashboard.title, "Model Monitoring Dashboard")

    def test_dashboard_render(self):
        """Test rendering of the dashboard."""
        dashboard = ModelMonitoringDashboard()
        html = dashboard.render()
        self.assertIsInstance(html, str)
        self.assertIn("Model Monitoring Dashboard", html)

    @patch("src.monitoring.model_monitoring_service.ModelMonitoringService")
    def test_dashboard_with_metrics(self, mock_service):
        """Test dashboard with metrics data."""
        # Setup mock data
        mock_service.get_monitored_models.return_value = [
            {
                "id": "model1",
                "name": "Water Heater Prediction Model",
                "versions": ["1.0", "1.1"],
            }
        ]
        mock_service.get_latest_metrics.return_value = {
            "accuracy": 0.95,
            "precision": 0.92,
            "recall": 0.91,
        }

        dashboard = ModelMonitoringDashboard(monitoring_service=mock_service)
        html = dashboard.render()
        self.assertIn("Water Heater Prediction Model", html)
        self.assertIn("0.95", html)  # Check accuracy is displayed


class TestModelMonitoringRoutes(unittest.TestCase):
    """Tests for the model monitoring routes."""

    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

    def test_monitoring_dashboard_route(self):
        """Test the monitoring dashboard route."""
        with patch("src.web.routes.templates.TemplateResponse") as mock_template:
            mock_template.return_value = MagicMock()
            response = self.client.get("/model-monitoring")
            self.assertEqual(response.status_code, 200)
            # Check that the template was rendered with the correct template
            mock_template.assert_called_once()
            args, kwargs = mock_template.call_args
            self.assertEqual(args[0], "model-monitoring/dashboard.html")
