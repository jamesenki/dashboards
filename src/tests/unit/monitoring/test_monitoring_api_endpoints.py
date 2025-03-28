"""
Tests for the Model Monitoring Dashboard API endpoints.
"""
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.monitoring.dashboard_api import create_dashboard_api
from src.monitoring.model_monitoring_service import ModelMonitoringService


class TestMonitoringAPIEndpoints(unittest.TestCase):
    """Tests for the model monitoring API endpoints."""

    def setUp(self):
        self.mock_service = MagicMock(spec=ModelMonitoringService)
        self.app = create_dashboard_api(self.mock_service)
        self.client = TestClient(self.app)

    def test_get_models_endpoint(self):
        """Test that the models endpoint returns a list of models in the correct format."""
        # Setup test data
        expected_models = [
            {"id": "model1", "name": "Predictive Maintenance Model", "versions": ["1.0", "1.1"]}
        ]
        self.mock_service.get_monitored_models.return_value = expected_models
        
        # Execute test
        response = self.client.get("/models")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_models)
        
    def test_get_metrics_endpoint(self):
        """Test that the metrics endpoint returns metrics in the correct format."""
        # Setup test data
        expected_metrics = {
            "accuracy": 0.95,
            "precision": 0.92,
            "recall": 0.91,
            "f1_score": 0.93
        }
        self.mock_service.get_latest_metrics.return_value = expected_metrics
        
        # Execute test
        response = self.client.get("/models/model1/versions/1.0/metrics")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_metrics)
        
    def test_get_alerts_endpoint(self):
        """Test that the alerts endpoint returns alerts in the correct format."""
        # Setup test data
        expected_alerts = [
            {
                "id": "alert1",
                "rule_name": "Low Accuracy Alert",
                "metric_name": "accuracy",
                "threshold": 0.9,
                "operator": "<",
                "severity": "HIGH"
            }
        ]
        self.mock_service.get_triggered_alerts.return_value = expected_alerts
        
        # Execute test
        response = self.client.get("/models/model1/versions/1.0/alerts")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_alerts)