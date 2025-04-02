"""
Tests for the ModelMonitoringService with the new configuration system.

Following TDD principles, these tests define the expected behavior
of the model monitoring service when using configuration.
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

# Import the service and configuration
from src.monitoring.model_monitoring_service import ModelMonitoringService
from src.monitoring.metrics import ModelMetric, MetricType
from src.monitoring.alerts import AlertRule, AlertSeverity
from src.config import config
from src.config.service import ConfigurationService
from src.config.providers import DefaultProvider


class TestModelMonitoringServiceWithConfig:
    """Test suite for the ModelMonitoringService using the configuration system."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Configure test configuration
        test_config = {
            "services": {
                "monitoring": {
                    "enabled": True,
                    "metrics_retention_days": 14,
                    "model_health": {
                        "drift_threshold": 0.2,
                        "accuracy_threshold": 0.8
                    },
                    "alerts": {
                        "check_interval": 300,
                        "notification_channels": {
                            "email": True,
                            "slack": False
                        }
                    },
                    "tags": [
                        {"id": "tag1", "name": "production", "color": "green"},
                        {"id": "tag2", "name": "development", "color": "blue"},
                        {"id": "tag3", "name": "testing", "color": "orange"},
                        {"id": "tag4", "name": "deprecated", "color": "red"}
                    ]
                }
            }
        }
        
        # Set up test configuration
        test_config_provider = DefaultProvider(test_config)
        self.config_service = ConfigurationService()
        self.config_service.register_provider(test_config_provider)
        
        # Mock the global config to use our test instance
        self.original_config = config
        import src.config
        src.config.config = self.config_service
        
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
    
    def teardown_method(self):
        """Clean up after each test method."""
        # Restore the original config
        import src.config
        src.config.config = self.original_config
    
    def test_init_with_config(self):
        """Test service initialization with configuration."""
        # A properly configured service should use configuration values
        assert self.service.metrics_retention_days == 14
        assert hasattr(self.service, "tags")
        assert len(self.service.tags) == 4
        assert self.service.tags["tag1"]["name"] == "production"
    
    def test_alert_thresholds_from_config(self):
        """Test that alert thresholds are loaded from configuration."""
        # Create an accuracy alert rule to test the threshold
        rule = self.service.create_alert_rule(
            rule_name="Low accuracy",
            metric_name="accuracy",
            operator="<",
            # We don't specify a threshold, it should use the config value
            severity=AlertSeverity.HIGH,
            description="Alert when accuracy drops too low"
        )
        
        # Verify that the threshold is set from configuration
        assert rule.threshold == 0.8
    
    def test_drift_threshold_from_config(self):
        """Test that drift threshold is loaded from configuration."""
        # Create a drift alert rule to test the threshold
        rule = self.service.create_alert_rule(
            rule_name="High drift",
            metric_name="drift_score",
            operator=">",
            # We don't specify a threshold, it should use the config value
            severity=AlertSeverity.MEDIUM,
            description="Alert when drift is too high"
        )
        
        # Verify that the threshold is set from configuration
        assert rule.threshold == 0.2
    
    def test_notification_channels_from_config(self):
        """Test that notification channels are loaded from configuration."""
        # Trigger an alert to test notification channels
        self.service.create_alert_rule(
            rule_name="Test rule",
            metric_name="accuracy",
            operator="<",
            threshold=0.95,
            severity=AlertSeverity.LOW
        )
        
        # Record metrics that should trigger the alert
        self.service.record_model_metrics(
            model_id=self.model_id,
            model_version=self.model_version,
            metrics={"accuracy": 0.94}
        )
        
        # Verify notification channels used
        notification_calls = self.notification_service_mock.send_notification.call_args_list
        for call in notification_calls:
            args, kwargs = call
            # Email channel should be used (true in config)
            if "email" in kwargs["channels"]:
                assert kwargs["channels"]["email"] is True
            # Slack channel should not be used (false in config)
            if "slack" in kwargs["channels"]:
                assert kwargs["channels"]["slack"] is False
