"""
Tests for the synchronous ModelMonitoringService wrapper.

Following TDD principles, these tests define the expected behavior of
the ModelMonitoringServiceSync class when integrated with our DataAccessLayer.
"""
import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Mock the dependencies before importing the tested module
sys.modules['src.monitoring.model_metrics_repository'] = MagicMock()
sys.modules['src.db.adapters.sqlite_model_metrics'] = MagicMock()
sys.modules['src.monitoring.alerts'] = MagicMock()

from src.api.data_access import DataAccessLayer


class TestModelMonitoringServiceSync:
    """Test suite for the ModelMonitoringServiceSync."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create mock data access layer
        self.mock_data_access = MagicMock(spec=DataAccessLayer)
        self.mock_data_access.is_using_mocks.return_value = True
        
        # Create mock monitoring service
        self.mock_monitoring_service = MagicMock()
        self.mock_monitoring_service.using_mock_data = True
        
        # Import ModelMonitoringServiceSync inside the method to avoid initialization issues
        with patch('src.api.data_access.data_access', self.mock_data_access):
            from src.monitoring.model_monitoring_service_sync import ModelMonitoringServiceSync
            self.ModelMonitoringServiceSync = ModelMonitoringServiceSync
            
            # Create the service with our mocks
            self.service = self.ModelMonitoringServiceSync(monitoring_service=self.mock_monitoring_service)
    
    def test_get_model_details_with_mock_data(self):
        """Test getting model details when mock data is available."""
        # Set up the mock to return a model
        model_id = "test-model-1"
        mock_model = {
            "id": model_id,
            "name": "Test Model 1",
            "version": "1.0.0",
            "type": "classification"
        }
        self.mock_data_access.get_model_by_id.return_value = mock_model
        
        # Call the method
        result = self.service.get_model_details(model_id)
        
        # Verify the result
        assert result == mock_model
        self.mock_data_access.get_model_by_id.assert_called_once_with(model_id)
    
    def test_get_model_details_fallback(self):
        """Test getting model details when mock data is not available."""
        # Set up the mock to return None (no model found)
        model_id = "test-model-1"
        self.mock_data_access.get_model_by_id.return_value = None
        
        # Call the method
        result = self.service.get_model_details(model_id)
        
        # Verify the result is a fallback model
        assert result["id"] == model_id
        assert "name" in result
        assert "version" in result
        assert "type" in result
        self.mock_data_access.get_model_by_id.assert_called_once_with(model_id)
    
    def test_get_all_models_with_mock_data(self):
        """Test getting all models when mock data is available."""
        # Set up the mock to return models
        mock_models = [
            {
                "id": "model-1",
                "name": "Model 1",
                "version": "1.0.0"
            },
            {
                "id": "model-2",
                "name": "Model 2",
                "version": "1.1.0"
            }
        ]
        self.mock_data_access.get_models.return_value = mock_models
        
        # Call the method
        result = self.service.get_all_models()
        
        # Verify the result
        assert result == mock_models
        self.mock_data_access.get_models.assert_called_once()
    
    def test_get_all_models_fallback(self):
        """Test getting all models when mock data is not available."""
        # Set up the mock to return an empty list (no models found)
        self.mock_data_access.get_models.return_value = []
        
        # Call the method
        result = self.service.get_all_models()
        
        # Verify the result is a fallback list
        assert len(result) > 0
        assert "id" in result[0]
        assert "name" in result[0]
        assert "version" in result[0]
        self.mock_data_access.get_models.assert_called_once()
    
    def test_get_model_metrics_with_mock_data(self):
        """Test getting model metrics when mock data is available."""
        # Set up the mock to return metrics
        model_id = "test-model-1"
        mock_metrics = {
            "metrics_history": [
                {
                    "timestamp": "2025-04-01T00:00:00Z",
                    "metrics": {
                        "accuracy": 0.92,
                        "precision": 0.90
                    }
                }
            ]
        }
        self.mock_data_access.get_model_metrics.return_value = mock_metrics
        
        # Call the method
        result = self.service.get_model_metrics(model_id)
        
        # Verify the result
        assert result == mock_metrics
        self.mock_data_access.get_model_metrics.assert_called_once_with(model_id)
    
    def test_get_model_metrics_fallback(self):
        """Test getting model metrics when mock data is not available."""
        # Set up the mock to return None (no metrics found)
        model_id = "test-model-1"
        self.mock_data_access.get_model_metrics.return_value = None
        
        # Call the method
        result = self.service.get_model_metrics(model_id)
        
        # Verify the result is a fallback metrics object
        assert "metrics_history" in result
        assert len(result["metrics_history"]) > 0
        assert "timestamp" in result["metrics_history"][0]
        assert "metrics" in result["metrics_history"][0]
        self.mock_data_access.get_model_metrics.assert_called_once_with(model_id)
    
    def test_get_model_alerts_with_mock_data(self):
        """Test getting model alerts when mock data is available."""
        # Set up the mock to return alerts
        model_id = "test-model-1"
        mock_alerts = [
            {
                "id": "alert-1",
                "model_id": model_id,
                "message": "Test Alert 1"
            }
        ]
        self.mock_data_access.get_model_alerts.return_value = mock_alerts
        
        # Call the method
        result = self.service.get_model_alerts(model_id)
        
        # Verify the result
        assert result == mock_alerts
        self.mock_data_access.get_model_alerts.assert_called_once_with(model_id)
    
    def test_get_model_alerts_fallback(self):
        """Test getting model alerts when mock data is not available."""
        # Set up the mock to return None (no alerts found)
        model_id = "test-model-1"
        self.mock_data_access.get_model_alerts.return_value = None
        
        # Call the method
        result = self.service.get_model_alerts(model_id)
        
        # Verify the result is a fallback alert list
        assert len(result) > 0
        assert "id" in result[0]
        assert "model_id" in result[0]
        assert result[0]["model_id"] == model_id
        self.mock_data_access.get_model_alerts.assert_called_once_with(model_id)
    
    def test_record_model_metrics(self):
        """Test recording model metrics."""
        # Set up the mock to return a record ID
        model_id = "test-model-1"
        model_version = "1.0.0"
        metrics = {"accuracy": 0.92, "precision": 0.90}
        record_id = "record-1"
        self.mock_monitoring_service.record_model_metrics.return_value = record_id
        
        # Call the method
        result = self.service.record_model_metrics(model_id, model_version, metrics)
        
        # Verify the result
        assert result == record_id
        self.mock_monitoring_service.record_model_metrics.assert_called_once_with(
            model_id, model_version, metrics, None
        )


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
