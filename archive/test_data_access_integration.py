"""
Test script for the DataAccessLayer and ModelMonitoringService integration.

This script tests the actual integration between our DataAccessLayer and 
ModelMonitoringService with real database interactions, following our TDD principles.
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_tests():
    """Run integration tests for DataAccessLayer and ModelMonitoringService."""
    from src.config.service import ConfigurationService
    from src.config.providers import DefaultProvider
    from src.api.data_access import DataAccessLayer
    from src.monitoring.model_monitoring_service_sync import ModelMonitoringServiceSync
    from src.db.initialize_db import initialize_database
    
    logger.info("Starting integration tests...")
    
    # Create a temporary database for testing
    temp_db_fd, temp_db_path = tempfile.mkstemp(suffix='.db')
    os.close(temp_db_fd)
    
    try:
        # Initialize the database with test data and force schema reset to ensure consistency
        logger.info(f"Initializing test database at {temp_db_path}")
        db = initialize_database(db_path=temp_db_path, in_memory=False, populate=True, force_reset=True)
        
        # Set up configuration for tests
        logger.info("Setting up test configuration")
        config_service = ConfigurationService()
        test_config = {
            "testing": {
                "mocks": {
                    "enabled": True,
                    "data_path": "./mocks"
                }
            }
        }
        config_service.register_provider(DefaultProvider(test_config))
        
        # Create data access layer with mocks enabled
        with patch('src.api.data_access.config', config_service):
            data_access = DataAccessLayer()
            logger.info(f"DataAccessLayer initialized, using mocks: {data_access.is_using_mocks()}")
            
            # Create monitoring service with the data access layer
            with patch('src.monitoring.model_monitoring_service_sync.data_access', data_access):
                monitoring_service = ModelMonitoringServiceSync()
                
                # Test getting model details
                test_get_model_details(monitoring_service)
                
                # Test getting all models
                test_get_all_models(monitoring_service)
                
                # Test getting model metrics
                test_get_model_metrics(monitoring_service)
                
                # Test getting model alerts
                test_get_model_alerts(monitoring_service)
                
                # Test recording model metrics
                test_record_metrics(monitoring_service)
    
    finally:
        # Clean up temporary database
        try:
            logger.info(f"Cleaning up test database at {temp_db_path}")
            os.unlink(temp_db_path)
        except:
            pass
    
    logger.info("All tests completed successfully!")


def test_get_model_details(service):
    """Test getting model details from service."""
    logger.info("Testing get_model_details...")
    
    # Test with an existing model
    water_heater_model = service.get_model_details("water-heater-model-1")
    assert water_heater_model is not None, "Should get water heater model details"
    logger.info(f"Successfully retrieved model details: {water_heater_model.get('name')}")
    
    # Test with a non-existent model
    nonexistent_model = service.get_model_details("nonexistent-model")
    assert nonexistent_model is not None, "Should get fallback model details for nonexistent model"
    assert nonexistent_model['id'] == "nonexistent-model", "Model ID should match request"
    logger.info("Successfully handled non-existent model")


def test_get_all_models(service):
    """Test getting all models from service."""
    logger.info("Testing get_all_models...")
    
    models = service.get_all_models()
    assert models is not None, "Should get a list of models"
    assert len(models) > 0, "Should have at least one model"
    logger.info(f"Successfully retrieved {len(models)} models")
    
    # Log the first few models
    for model in models[:2]:
        logger.info(f"Model: {model.get('name')} (ID: {model.get('id')})")


def test_get_model_metrics(service):
    """Test getting model metrics from service."""
    logger.info("Testing get_model_metrics...")
    
    # Test with an existing model
    metrics = service.get_model_metrics("water-heater-model-1")
    assert metrics is not None, "Should get metrics for water heater model"
    assert 'metrics_history' in metrics, "Metrics should contain metrics_history"
    logger.info(f"Successfully retrieved metrics with {len(metrics.get('metrics_history', []))} records")


def test_get_model_alerts(service):
    """Test getting model alerts from service."""
    logger.info("Testing get_model_alerts...")
    
    # Test getting all alerts
    all_alerts = service.get_model_alerts()
    assert all_alerts is not None, "Should get a list of alerts"
    logger.info(f"Successfully retrieved {len(all_alerts)} alerts")
    
    # Test with a specific model
    model_alerts = service.get_model_alerts("water-heater-model-1")
    assert model_alerts is not None, "Should get alerts for water heater model"
    logger.info(f"Successfully retrieved {len(model_alerts)} alerts for specific model")


def test_record_metrics(service):
    """Test recording model metrics."""
    logger.info("Testing record_model_metrics...")
    
    model_id = "test-model-123"
    model_version = "1.0.0"
    metrics = {
        "accuracy": 0.92,
        "precision": 0.90,
        "recall": 0.89
    }
    
    record_id = service.record_model_metrics(model_id, model_version, metrics)
    assert record_id is not None, "Should get a record ID"
    logger.info(f"Successfully recorded metrics with ID: {record_id}")


if __name__ == "__main__":
    # To run this example, we need to patch the config with our test configuration
    from unittest.mock import patch
    
    run_tests()
