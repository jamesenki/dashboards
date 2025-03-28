"""
Tests for the Model Monitoring Dashboard API.

Following TDD principles, these tests define the expected behavior
of the monitoring dashboard API before implementation.
"""
import os
import sys
import pytest
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Import the API (to be implemented)
from src.monitoring.dashboard_api import create_dashboard_api
from src.monitoring.model_monitoring_service import ModelMonitoringService


@pytest.fixture
def app():
    """Create a test FastAPI application with mocked services."""
    # Mock the monitoring service
    monitoring_service_mock = MagicMock(spec=ModelMonitoringService)
    
    # Create a test FastAPI app with the mocked service
    app = create_dashboard_api(monitoring_service=monitoring_service_mock)
    
    # Add the mock to the app for test access
    app.state.monitoring_service = monitoring_service_mock
    
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestMonitoringDashboardAPI:
    """Test suite for the Monitoring Dashboard API."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Test data
        self.model_id = str(uuid.uuid4())
        self.model_version = "1.0.0"
        self.metric_data = {
            "accuracy": 0.92,
            "precision": 0.88,
            "recall": 0.85,
            "f1_score": 0.86,
            "roc_auc": 0.91
        }
    
    def test_get_models_endpoint(self, client, app):
        """Test the endpoint that returns all monitored models."""
        # Arrange
        models = [
            {"id": str(uuid.uuid4()), "name": "water_heater_failure", "latest_version": "1.0.0"},
            {"id": str(uuid.uuid4()), "name": "energy_consumption", "latest_version": "2.1.0"}
        ]
        app.state.monitoring_service.get_monitored_models.return_value = models
        
        # Act
        response = client.get("/api/monitoring/models")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == models
        app.state.monitoring_service.get_monitored_models.assert_called_once()
    
    def test_get_model_versions_endpoint(self, client, app):
        """Test the endpoint that returns all versions of a model."""
        # Arrange
        versions = [
            {"version": "1.0.0", "created_at": "2025-02-15T10:00:00Z"},
            {"version": "1.1.0", "created_at": "2025-03-01T14:30:00Z"}
        ]
        app.state.monitoring_service.get_model_versions.return_value = versions
        
        # Act
        response = client.get(f"/api/monitoring/models/{self.model_id}/versions")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == versions
        app.state.monitoring_service.get_model_versions.assert_called_once_with(self.model_id)
    
    def test_get_model_metrics_endpoint(self, client, app):
        """Test the endpoint that returns metrics for a model version."""
        # Arrange
        metrics = [
            {"name": "accuracy", "value": 0.92, "timestamp": "2025-03-27T10:00:00Z"},
            {"name": "precision", "value": 0.88, "timestamp": "2025-03-27T10:00:00Z"}
        ]
        app.state.monitoring_service.get_latest_metrics.return_value = metrics
        
        # Act
        response = client.get(
            f"/api/monitoring/models/{self.model_id}/versions/{self.model_version}/metrics"
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json() == metrics
        app.state.monitoring_service.get_latest_metrics.assert_called_once_with(
            self.model_id, self.model_version
        )
    
    def test_get_metric_history_endpoint(self, client, app):
        """Test the endpoint that returns the history of a specific metric."""
        # Arrange
        metric_name = "accuracy"
        history = [
            {"value": 0.92, "timestamp": "2025-03-27T10:00:00Z"},
            {"value": 0.91, "timestamp": "2025-03-26T10:00:00Z"},
            {"value": 0.90, "timestamp": "2025-03-25T10:00:00Z"}
        ]
        app.state.monitoring_service.get_model_metrics_history.return_value = history
        
        # Act
        response = client.get(
            f"/api/monitoring/models/{self.model_id}/versions/{self.model_version}/metrics/{metric_name}/history",
            params={"days": 30}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json() == history
        app.state.monitoring_service.get_model_metrics_history.assert_called_once()
    
    def test_record_metrics_endpoint(self, client, app):
        """Test the endpoint for recording new metrics."""
        # Arrange
        app.state.monitoring_service.record_model_metrics.return_value = "success"
        
        # Act
        response = client.post(
            f"/api/monitoring/models/{self.model_id}/versions/{self.model_version}/metrics",
            json=self.metric_data
        )
        
        # Assert
        assert response.status_code == 201
        app.state.monitoring_service.record_model_metrics.assert_called_once()
        
    def test_get_performance_summary_endpoint(self, client, app):
        """Test the endpoint that returns a performance summary."""
        # Arrange
        summary = {
            "latest_metrics": {
                "accuracy": 0.92,
                "precision": 0.88
            },
            "historical_average": {
                "accuracy": 0.90,
                "precision": 0.86
            },
            "trend": {
                "accuracy": "improving",
                "precision": "stable"
            }
        }
        app.state.monitoring_service.get_model_performance_summary.return_value = summary
        
        # Act
        response = client.get(
            f"/api/monitoring/models/{self.model_id}/versions/{self.model_version}/summary"
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json() == summary
        app.state.monitoring_service.get_model_performance_summary.assert_called_once_with(
            self.model_id, self.model_version
        )
    
    def test_calculate_drift_endpoint(self, client, app):
        """Test the endpoint for calculating drift between model versions."""
        # Arrange
        baseline_version = "1.0.0"
        current_version = "1.1.0"
        drift_results = {
            "accuracy": -0.05,
            "precision": -0.03
        }
        app.state.monitoring_service.calculate_drift.return_value = drift_results
        
        # Act
        response = client.get(
            f"/api/monitoring/models/{self.model_id}/drift",
            params={"baseline_version": baseline_version, "current_version": current_version}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json() == drift_results
        app.state.monitoring_service.calculate_drift.assert_called_once_with(
            self.model_id, baseline_version, current_version
        )
    
    def test_create_alert_rule_endpoint(self, client, app):
        """Test the endpoint for creating an alert rule."""
        # Arrange
        rule_data = {
            "rule_name": "Accuracy Drop Alert",
            "metric_name": "accuracy",
            "threshold": 0.85,
            "operator": "<",
            "severity": "HIGH"
        }
        rule_id = str(uuid.uuid4())
        app.state.monitoring_service.create_alert_rule.return_value = rule_id
        
        # Act
        response = client.post(
            f"/api/monitoring/models/{self.model_id}/versions/{self.model_version}/alerts/rules",
            json=rule_data
        )
        
        # Assert
        assert response.status_code == 201
        assert response.json()["id"] == rule_id
        app.state.monitoring_service.create_alert_rule.assert_called_once()
    
    def test_get_alert_rules_endpoint(self, client, app):
        """Test the endpoint that returns alert rules for a model."""
        # Arrange
        rules = [
            {
                "id": str(uuid.uuid4()),
                "model_id": self.model_id,
                "model_version": self.model_version,
                "rule_name": "Accuracy Drop Alert",
                "metric_name": "accuracy",
                "threshold": 0.85,
                "operator": "<",
                "severity": "HIGH"
            }
        ]
        app.state.monitoring_service.get_alert_rules.return_value = rules
        
        # Act
        response = client.get(
            f"/api/monitoring/models/{self.model_id}/versions/{self.model_version}/alerts/rules"
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json() == rules
        app.state.monitoring_service.get_alert_rules.assert_called_once_with(
            self.model_id, self.model_version
        )
    
    def test_get_triggered_alerts_endpoint(self, client, app):
        """Test the endpoint that returns triggered alerts."""
        # Arrange
        alerts = [
            {
                "id": str(uuid.uuid4()),
                "rule_id": str(uuid.uuid4()),
                "model_id": self.model_id,
                "model_version": self.model_version,
                "metric_name": "accuracy",
                "threshold": 0.85,
                "actual_value": 0.82,
                "triggered_at": "2025-03-27T10:00:00Z",
                "severity": "HIGH"
            }
        ]
        app.state.monitoring_service.get_triggered_alerts.return_value = alerts
        
        # Act
        response = client.get(
            f"/api/monitoring/models/{self.model_id}/versions/{self.model_version}/alerts"
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json() == alerts
        app.state.monitoring_service.get_triggered_alerts.assert_called_once_with(
            self.model_id, self.model_version
        )
        
    def test_export_metrics_report_endpoint(self, client, app):
        """Test the endpoint for exporting a metrics report."""
        # Arrange
        report_content = json.dumps([
            {"model_id": self.model_id, "model_version": self.model_version, 
             "metric_name": "accuracy", "metric_value": 0.92, 
             "timestamp": "2025-03-27T10:00:00Z"}
        ])
        app.state.monitoring_service.export_metrics_report.return_value = report_content
        
        # Act
        response = client.get(
            f"/api/monitoring/models/{self.model_id}/versions/{self.model_version}/report",
            params={"format": "json", "days": 30}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json() == json.loads(report_content)
        app.state.monitoring_service.export_metrics_report.assert_called_once()