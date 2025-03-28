"""
Tests for the ModelMonitoringService.

Following TDD principles, these tests define the expected behavior
of the model monitoring service before implementation.
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

# Import the service (to be implemented)
from src.monitoring.model_monitoring_service import ModelMonitoringService
from src.monitoring.metrics import ModelMetric, MetricType
from src.monitoring.alerts import AlertRule, AlertSeverity


class TestModelMonitoringService:
    """Test suite for the ModelMonitoringService."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Mock dependencies
        self.db_mock = MagicMock()
        self.notification_service_mock = MagicMock()
        
        # Create service instance with mocked dependencies
        self.service = ModelMonitoringService(
            db=self.db_mock,
            notification_service=self.notification_service_mock
        )
        
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
        
    def test_init(self):
        """Test service initialization."""
        assert self.service.db == self.db_mock
        assert self.service.notification_service == self.notification_service_mock
    
    def test_record_model_metrics(self):
        """Test recording metrics for a model."""
        # Arrange
        timestamp = datetime.now()
        
        # Act
        result = self.service.record_model_metrics(
            model_id=self.model_id,
            model_version=self.model_version,
            metrics=self.metric_data,
            timestamp=timestamp
        )
        
        # Assert
        assert result is not None
        self.db_mock.execute.assert_called_once()
        # Check that SQL parameters contain all the metric data
        call_args = self.db_mock.execute.call_args[0][1]
        assert self.model_id in call_args
        assert self.model_version in call_args
        
    def test_get_model_metrics_history(self):
        """Test retrieving metric history for a model."""
        # Arrange
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        expected_metrics = [
            {"model_id": self.model_id, "model_version": self.model_version, 
             "metric_name": "accuracy", "metric_value": 0.92, 
             "timestamp": (end_date - timedelta(days=1)).isoformat()},
            {"model_id": self.model_id, "model_version": self.model_version, 
             "metric_name": "accuracy", "metric_value": 0.90, 
             "timestamp": (end_date - timedelta(days=2)).isoformat()}
        ]
        self.db_mock.fetch_all.return_value = expected_metrics
        
        # Act
        metrics = self.service.get_model_metrics_history(
            model_id=self.model_id,
            model_version=self.model_version,
            metric_name="accuracy",
            start_date=start_date,
            end_date=end_date
        )
        
        # Assert
        assert metrics == expected_metrics
        self.db_mock.fetch_all.assert_called_once()
        
    def test_create_alert_rule(self):
        """Test creating an alert rule for metric thresholds."""
        # Arrange
        rule_name = "Accuracy Drop Alert"
        metric_name = "accuracy"
        threshold = 0.85
        operator = "<"  # Alert when accuracy falls below threshold
        severity = AlertSeverity.HIGH
        
        # Act
        rule_id = self.service.create_alert_rule(
            model_id=self.model_id,
            model_version=self.model_version,
            rule_name=rule_name,
            metric_name=metric_name,
            threshold=threshold,
            operator=operator,
            severity=severity
        )
        
        # Assert
        assert rule_id is not None
        self.db_mock.execute.assert_called_once()
        
    def test_check_for_alerts(self):
        """Test checking metrics against alert rules."""
        # Arrange
        alert_rule = AlertRule(
            id=str(uuid.uuid4()),
            model_id=self.model_id,
            model_version=self.model_version,
            rule_name="Accuracy Drop Alert",
            metric_name="accuracy",
            threshold=0.95,
            operator="<",
            severity=AlertSeverity.HIGH
        )
        
        # Mock that we have one alert rule
        self.db_mock.fetch_all.return_value = [alert_rule.__dict__]
        
        # The metric we're recording is below the threshold
        metrics = {"accuracy": 0.92}
        
        # Act
        triggered_alerts = self.service.check_for_alerts(
            model_id=self.model_id,
            model_version=self.model_version,
            metrics=metrics
        )
        
        # Assert
        assert len(triggered_alerts) == 1
        assert triggered_alerts[0].rule_id == alert_rule.id
        assert triggered_alerts[0].model_id == self.model_id
        assert triggered_alerts[0].metric_name == "accuracy"
        self.notification_service_mock.send_alert.assert_called_once()
    
    def test_calculate_drift(self):
        """Test calculating drift between model versions."""
        # Arrange
        baseline_version = "1.0.0"
        current_version = "1.1.0"
        
        # Mock metrics data
        baseline_metrics = [
            {"metric_name": "accuracy", "metric_value": 0.90},
            {"metric_name": "precision", "metric_value": 0.85}
        ]
        current_metrics = [
            {"metric_name": "accuracy", "metric_value": 0.85},
            {"metric_name": "precision", "metric_value": 0.82}
        ]
        
        self.db_mock.fetch_all.side_effect = [baseline_metrics, current_metrics]
        
        # Act
        drift_results = self.service.calculate_drift(
            model_id=self.model_id,
            baseline_version=baseline_version,
            current_version=current_version
        )
        
        # Assert
        assert drift_results is not None
        assert "accuracy" in drift_results
        assert "precision" in drift_results
        assert isinstance(drift_results["accuracy"], float)
        assert isinstance(drift_results["precision"], float)
        
    def test_get_model_performance_summary(self):
        """Test getting a performance summary for a model version."""
        # Arrange
        latest_metrics = {
            "accuracy": 0.92,
            "precision": 0.88,
            "recall": 0.85,
            "f1_score": 0.86
        }
        historical_average = {
            "accuracy": 0.90,
            "precision": 0.87,
            "recall": 0.83,
            "f1_score": 0.85
        }
        
        self.db_mock.fetch_one.return_value = latest_metrics
        self.db_mock.fetch_all.return_value = [historical_average]
        
        # Act
        summary = self.service.get_model_performance_summary(
            model_id=self.model_id,
            model_version=self.model_version
        )
        
        # Assert
        assert summary is not None
        assert "latest_metrics" in summary
        assert "historical_average" in summary
        assert "trend" in summary
        assert summary["latest_metrics"] == latest_metrics

    def test_export_metrics_report(self):
        """Test exporting metrics as a report."""
        # Arrange
        report_format = "json"
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        metrics = [
            {"model_id": self.model_id, "model_version": self.model_version, 
             "metric_name": "accuracy", "metric_value": 0.92, 
             "timestamp": (end_date - timedelta(days=1)).isoformat()},
            {"model_id": self.model_id, "model_version": self.model_version, 
             "metric_name": "precision", "metric_value": 0.88, 
             "timestamp": (end_date - timedelta(days=1)).isoformat()}
        ]
        
        self.db_mock.fetch_all.return_value = metrics
        
        # Act
        report = self.service.export_metrics_report(
            model_id=self.model_id,
            model_version=self.model_version,
            start_date=start_date,
            end_date=end_date,
            format=report_format
        )
        
        # Assert
        assert report is not None
        assert isinstance(report, str)
        # Should be valid JSON
        loaded_report = json.loads(report)
        assert len(loaded_report) == len(metrics)