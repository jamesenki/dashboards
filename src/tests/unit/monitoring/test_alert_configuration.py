"""
Tests for the Model Monitoring Alert Configuration functionality.
"""
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.monitoring.dashboard_api import create_dashboard_api
from src.monitoring.model_monitoring_service import ModelMonitoringService
from src.monitoring.alerts import AlertRule, AlertSeverity


class TestAlertConfiguration(unittest.TestCase):
    """Tests for configuring model monitoring alerts."""

    def setUp(self):
        self.mock_service = MagicMock(spec=ModelMonitoringService)
        self.app = create_dashboard_api(self.mock_service)
        self.client = TestClient(self.app)

    def test_get_alert_rules(self):
        """Test retrieving existing alert rules for a model."""
        # Mock data setup
        model_id = "water-heater-model-1"
        version = "1.0"
        mock_rules = [
            {
                "id": "rule-1",
                "rule_name": "Low Accuracy Alert",
                "metric_name": "accuracy",
                "threshold": 0.9,
                "operator": "<",
                "severity": "HIGH",
                "created_at": "2025-03-28T10:00:00Z"
            }
        ]
        self.mock_service.get_alert_rules.return_value = mock_rules
        
        # Execute test
        response = self.client.get(f"/models/{model_id}/versions/{version}/alerts/rules")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), mock_rules)
        self.mock_service.get_alert_rules.assert_called_once_with(model_id, version)

    def test_create_alert_rule(self):
        """Test creating a new alert rule."""
        # Mock data setup
        model_id = "water-heater-model-1"
        version = "1.0"
        new_rule = {
            "rule_name": "Precision Drop Alert",
            "metric_name": "precision",
            "threshold": 0.85,
            "operator": "<",
            "severity": "MEDIUM",
            "description": "Alert when precision drops below 0.85"
        }
        self.mock_service.create_alert_rule.return_value = "new-rule-123"
        
        # Execute test
        response = self.client.post(
            f"/models/{model_id}/versions/{version}/alerts/rules",
            json=new_rule
        )
        
        # Verify response
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"id": "new-rule-123", "status": "success"})
        self.mock_service.create_alert_rule.assert_called_once()
    
    def test_delete_alert_rule(self):
        """Test deleting an existing alert rule."""
        # Mock data setup
        model_id = "water-heater-model-1"
        version = "1.0"
        rule_id = "rule-1"
        
        # Execute test
        response = self.client.delete(
            f"/models/{model_id}/versions/{version}/alerts/rules/{rule_id}"
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "message": "Alert rule deleted"})
        self.mock_service.delete_alert_rule.assert_called_once_with(rule_id)
