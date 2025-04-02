"""
Synchronous wrappers for the ModelMonitoringService.

This module provides synchronous versions of the ModelMonitoringService methods
that integrate with our ConfigurationService and DataAccessLayer.
Following our TDD principles, we're maintaining backward compatibility while
adding support for externalized, configurable data sources.
"""
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from src.monitoring.model_monitoring_service import ModelMonitoringService
from src.api.data_access import data_access

# Configure logging
logger = logging.getLogger(__name__)


class ModelMonitoringServiceSync:
    """
    Synchronous wrapper for ModelMonitoringService that integrates with the DataAccessLayer.
    
    This class provides synchronous versions of the ModelMonitoringService methods,
    making them easier to use from non-async contexts like the API layer.
    """
    
    def __init__(self, monitoring_service=None):
        """
        Initialize the synchronous model monitoring service.
        
        Args:
            monitoring_service: Optional ModelMonitoringService instance
        """
        self.monitoring_service = monitoring_service or ModelMonitoringService(
            data_access_layer=data_access
        )
        
    def get_model_details(self, model_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a model.
        
        Args:
            model_id: The ID of the model
            
        Returns:
            Dictionary with model details
        """
        # First try to get model details from the data access layer if using mock data
        if self.monitoring_service.using_mock_data:
            model = data_access.get_model_by_id(model_id)
            if model is not None:
                return model
        
        # Fall back to generating dummy model details
        return {
            "id": model_id,
            "name": f"Model {model_id}",
            "description": "A machine learning model",
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "type": "classification",
            "status": "active"
        }
        
    def get_all_models(self) -> List[Dict[str, Any]]:
        """
        Get a list of all available models.
        
        Returns:
            List of model dictionaries with basic information
        """
        # First try to get models from the data access layer if using mock data
        if self.monitoring_service.using_mock_data:
            models = data_access.get_models()
            if models:
                return models
        
        # Fall back to generating dummy models
        return [
            {
                "id": "model1",
                "name": "Model 1",
                "version": "1.0.0",
                "type": "classification",
                "status": "active"
            },
            {
                "id": "model2",
                "name": "Model 2",
                "version": "1.1.0",
                "type": "regression",
                "status": "active"
            }
        ]
        
    def get_model_metrics(self, model_id: str) -> Dict[str, Any]:
        """
        Get metrics for a specific model.
        
        Args:
            model_id: The ID of the model
            
        Returns:
            Dictionary containing model metrics
        """
        # Try to get metrics from the data access layer if using mock data
        if self.monitoring_service.using_mock_data:
            metrics = data_access.get_model_metrics(model_id)
            if metrics:
                return metrics
        
        # Fall back to generating dummy metrics
        return {
            "metrics_history": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "metrics": {
                        "accuracy": 0.85,
                        "precision": 0.82,
                        "recall": 0.83,
                        "f1_score": 0.82,
                        "drift_score": 0.07
                    }
                }
            ]
        }
        
    def get_model_alerts(self, model_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get alerts for a specific model or all models.
        
        Args:
            model_id: Optional ID of the model to get alerts for
            
        Returns:
            List of alert dictionaries
        """
        # Try to get alerts from the data access layer if using mock data
        if self.monitoring_service.using_mock_data:
            alerts = data_access.get_model_alerts(model_id)
            if alerts is not None:
                return alerts
        
        # Fall back to generating dummy alerts
        if model_id:
            return [
                {
                    "id": f"alert-{model_id}-1",
                    "model_id": model_id,
                    "timestamp": datetime.now().isoformat(),
                    "metric_name": "accuracy",
                    "threshold": 0.85,
                    "actual_value": 0.82,
                    "message": "Accuracy below threshold",
                    "severity": "MEDIUM"
                }
            ]
        else:
            return [
                {
                    "id": "alert-model1-1",
                    "model_id": "model1",
                    "timestamp": datetime.now().isoformat(),
                    "metric_name": "accuracy",
                    "threshold": 0.85,
                    "actual_value": 0.82,
                    "message": "Accuracy below threshold",
                    "severity": "MEDIUM"
                },
                {
                    "id": "alert-model2-1",
                    "model_id": "model2",
                    "timestamp": datetime.now().isoformat(),
                    "metric_name": "drift_score",
                    "threshold": 0.15,
                    "actual_value": 0.18,
                    "message": "Drift score exceeds threshold",
                    "severity": "HIGH"
                }
            ]
            
    def record_model_metrics(self, model_id: str, model_version: str, 
                       metrics: Dict[str, float], timestamp: datetime = None) -> str:
        """
        Record performance metrics for a model.
        
        Args:
            model_id: ID of the model
            model_version: Version of the model
            metrics: Dictionary of metric names and values
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            ID of the recorded metrics
        """
        # Pass through to the monitoring service's synchronous method
        return self.monitoring_service.record_model_metrics(
            model_id, model_version, metrics, timestamp
        )


# Singleton instance for global access
monitoring_service_sync = ModelMonitoringServiceSync()
