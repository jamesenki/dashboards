"""
Example script demonstrating the MockDataProvider with our configuration system.

This script shows how to use the configuration-driven mock data provider
to load mock data from external files rather than hardcoding it.
"""
import os
import sys
import logging
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.config.service import ConfigurationService
from src.config.providers import DefaultProvider, FileProvider, EnvironmentProvider
from src.mocks.mock_data_provider import MockDataProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run the mock data example."""
    # Set up the configuration service
    logger.info("Setting up configuration service...")
    config_service = ConfigurationService()
    
    # Register configuration providers in order of precedence
    # 1. Load default values
    default_config = {
        "testing": {
            "mocks": {
                "enabled": True,  # Enable mock data by default for this example
                "data_path": "./mocks",
                "response_delay_ms": 200  # Add a small delay to simulate network calls
            }
        }
    }
    config_service.register_provider(DefaultProvider(default_config))
    
    # 2. Load values from configuration files
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
    config_service.register_provider(FileProvider(config_path))
    
    # 3. Load values from environment variables (highest precedence)
    config_service.register_provider(EnvironmentProvider())
    
    # Initialize the mock data provider with our configuration
    logger.info("Initializing mock data provider...")
    with patch('src.mocks.mock_data_provider.config', config_service):
        provider = MockDataProvider()
    
    # Display configuration settings
    logger.info(f"Mock data enabled: {provider.is_enabled()}")
    logger.info(f"Mock data path: {provider.data_path}")
    logger.info(f"Mock response delay: {provider.response_delay_ms}ms")
    
    # Retrieve some mock data
    logger.info("Retrieving mock models data...")
    models_data = provider.get_mock_data("models/models")
    if models_data:
        logger.info(f"Found {len(models_data.get('models', []))} models in mock data")
        for model in models_data.get('models', [])[:2]:  # Show first two models
            logger.info(f"  - {model.get('name')} (ID: {model.get('id')})")
    else:
        logger.info("No models data found")
    
    # Retrieve water heater mock data
    logger.info("Retrieving mock water heater devices data...")
    devices_data = provider.get_mock_data("devices/water_heaters")
    if devices_data:
        logger.info(f"Found {len(devices_data.get('devices', []))} water heater devices in mock data")
        for device in devices_data.get('devices', [])[:2]:  # Show first two devices
            logger.info(f"  - {device.get('name')} (ID: {device.get('id')})")
    else:
        logger.info("No water heater device data found")
    
    # Example of registering runtime mock data
    logger.info("Registering runtime mock data...")
    runtime_data = {
        "timestamp": "2025-04-02T12:00:00Z",
        "metrics": {
            "active_devices": 328,
            "alerts_triggered": 12,
            "api_requests": 5423
        }
    }
    provider.register_mock_data("runtime/metrics", runtime_data)
    
    # Verify runtime data was registered
    metrics_data = provider.get_mock_data("runtime/metrics")
    if metrics_data:
        logger.info(f"Retrieved runtime metrics data:")
        logger.info(f"  - Timestamp: {metrics_data.get('timestamp')}")
        logger.info(f"  - Active devices: {metrics_data.get('metrics', {}).get('active_devices')}")
        logger.info(f"  - Alerts triggered: {metrics_data.get('metrics', {}).get('alerts_triggered')}")
    
    logger.info("Mock data example completed")


if __name__ == "__main__":
    # To run this example, we need to patch the global config with our test configuration
    from unittest.mock import patch
    
    main()
