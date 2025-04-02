"""
Example script demonstrating the DataAccessLayer with our mock data provider.

This script shows how the DataAccessLayer works with the configuration-driven
mock data system to provide access to mock device and model data.
"""
import os
import sys
import logging
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.config.service import ConfigurationService
from src.config.providers import DefaultProvider, FileProvider, EnvironmentProvider
from src.api.data_access import DataAccessLayer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Run the data access example."""
    # Set up the configuration service
    logger.info("Setting up configuration service...")
    config_service = ConfigurationService()
    
    # Register configuration providers in order of precedence
    # 1. Load default values
    default_config = {
        "testing": {
            "mocks": {
                "enabled": True,  # Enable mock data for this example
                "data_path": "./mocks",
                "response_delay_ms": 100  # Add a small delay to simulate network calls
            }
        }
    }
    config_service.register_provider(DefaultProvider(default_config))
    
    # 2. Load values from configuration files
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
    config_service.register_provider(FileProvider(config_path))
    
    # 3. Load values from environment variables (highest precedence)
    config_service.register_provider(EnvironmentProvider())
    
    # Initialize the data access layer with our configuration
    logger.info("Initializing data access layer...")
    with patch('src.api.data_access.config', config_service):
        data_access = DataAccessLayer()
    
    # Display configuration settings
    logger.info(f"Using mock data: {data_access.is_using_mocks()}")
    
    # Retrieve models data
    logger.info("Retrieving models data...")
    models = data_access.get_models()
    if models:
        logger.info(f"Found {len(models)} models")
        for model in models[:3]:  # Show first three models
            logger.info(f"  - {model.get('name')} (ID: {model.get('id')})")
            # Get alerts for this model
            alerts = data_access.get_model_alerts(model_id=model.get('id'))
            if alerts:
                logger.info(f"    * Has {len(alerts)} alerts")
            
            # Get metrics for this model
            metrics = data_access.get_model_metrics(model_id=model.get('id'))
            if metrics and 'metrics_history' in metrics:
                logger.info(f"    * Has {len(metrics.get('metrics_history', []))} metric records")
    else:
        logger.info("No models found")
    
    # Retrieve water heater devices
    logger.info("Retrieving water heater devices...")
    water_heaters = data_access.get_devices(device_type='water_heater')
    if water_heaters:
        logger.info(f"Found {len(water_heaters)} water heater devices")
        for device in water_heaters[:3]:  # Show first three devices
            logger.info(f"  - {device.get('name')} (ID: {device.get('id')})")
    else:
        logger.info("No water heater devices found")
    
    logger.info("Data access example completed")


if __name__ == "__main__":
    # To run this example, we need to patch the global config with our test configuration
    from unittest.mock import patch
    
    main()
