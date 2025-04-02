"""
Data Access Layer for IoTSphere.

This module provides a data access layer that can use either real data sources
or mock data, based on configuration. This follows our TDD approach by making
data sources configurable rather than hardcoded.
"""
import logging
from typing import Dict, List, Any, Optional, Union

from src.config import config
from src.mocks.mock_data_provider import mock_data_provider

# Configure logging
logger = logging.getLogger(__name__)


class DataAccessLayer:
    """
    Data Access Layer for IoTSphere.
    
    This class provides access to data from various sources (database, API, etc.)
    and can be configured to use mock data for testing and development.
    """
    
    def __init__(self):
        """Initialize the data access layer."""
        self.use_mocks = config.get_bool('testing.mocks.enabled', False)
        logger.info(f"DataAccessLayer initialized with use_mocks={self.use_mocks}")
    
    def get_models(self) -> List[Dict[str, Any]]:
        """
        Get all models.
        
        Returns:
            List of model dictionaries
        """
        if self.use_mocks and mock_data_provider.is_mock_data_available('models/models'):
            # Get mock data for models
            mock_data = mock_data_provider.get_mock_data('models/models')
            return mock_data.get('models', [])
        else:
            # In a real implementation, this would access the database or API
            # For now, we'll just return an empty list
            logger.warning("Real data source for models not implemented yet")
            return []
    
    def get_model_by_id(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a model by ID.
        
        Args:
            model_id: The ID of the model to get
            
        Returns:
            The model dictionary or None if not found
        """
        models = self.get_models()
        for model in models:
            if model.get('id') == model_id:
                return model
        return None
    
    def get_devices(self, device_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all devices, optionally filtered by type.
        
        Args:
            device_type: Optional device type to filter by
            
        Returns:
            List of device dictionaries
        """
        devices = []
        
        if self.use_mocks:
            # Check for different types of device mock data
            if device_type == 'water_heater' and mock_data_provider.is_mock_data_available('devices/water_heaters'):
                mock_data = mock_data_provider.get_mock_data('devices/water_heaters')
                devices = mock_data.get('devices', [])
            elif mock_data_provider.is_mock_data_available('devices/devices'):
                # Fall back to generic devices mock data
                mock_data = mock_data_provider.get_mock_data('devices/devices')
                devices = mock_data.get('devices', [])
        else:
            # In a real implementation, this would access the database or API
            logger.warning("Real data source for devices not implemented yet")
            return []
        
        # Filter by device type if specified
        if device_type and devices:
            return [device for device in devices if device.get('type') == device_type]
        
        return devices
    
    def get_device_by_id(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a device by ID.
        
        Args:
            device_id: The ID of the device to get
            
        Returns:
            The device dictionary or None if not found
        """
        devices = self.get_devices()
        for device in devices:
            if device.get('id') == device_id:
                return device
        return None
    
    def get_model_metrics(self, model_id: str) -> Dict[str, Any]:
        """
        Get metrics for a specific model.
        
        Args:
            model_id: The ID of the model to get metrics for
            
        Returns:
            Dictionary containing model metrics
        """
        if self.use_mocks and mock_data_provider.is_mock_data_available('metrics/model_metrics'):
            # Get mock data for model metrics
            mock_data = mock_data_provider.get_mock_data('metrics/model_metrics')
            metrics = mock_data.get('metrics', {}).get(model_id, {})
            return metrics
        else:
            # In a real implementation, this would access the database or API
            logger.warning("Real data source for model metrics not implemented yet")
            return {}
    
    def get_model_alerts(self, model_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get alerts for a specific model or all models.
        
        Args:
            model_id: Optional ID of the model to get alerts for
            
        Returns:
            List of alert dictionaries
        """
        if self.use_mocks and mock_data_provider.is_mock_data_available('metrics/model_metrics'):
            # Get mock data for model alerts
            mock_data = mock_data_provider.get_mock_data('metrics/model_metrics')
            alerts = mock_data.get('alerts', [])
            
            # Filter by model ID if specified
            if model_id:
                return [alert for alert in alerts if alert.get('model_id') == model_id]
            
            return alerts
        else:
            # In a real implementation, this would access the database or API
            logger.warning("Real data source for model alerts not implemented yet")
            return []
    
    def is_using_mocks(self) -> bool:
        """
        Check if the data access layer is using mock data.
        
        Returns:
            True if using mock data, False otherwise
        """
        return self.use_mocks


# Singleton instance for global access
data_access = DataAccessLayer()
