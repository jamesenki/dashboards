#!/usr/bin/env python
"""
Debug script to troubleshoot database access and mock data usage in IoTSphere.
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
from pprint import pprint

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set environment variables
os.environ['USE_MOCK_DATA'] = 'False'
os.environ['DEBUG'] = 'True'

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.db.real_database import SQLiteDatabase
from src.db.adapters.sqlite_model_metrics import SQLiteModelMetricsRepository
from src.monitoring.model_metrics_repository import ModelMetricsRepository
from src.monitoring.model_monitoring_service import ModelMonitoringService

async def main():
    """Main debug function."""
    logger.info("Starting database access debug")
    
    # Initialize database
    db = SQLiteDatabase("data/iotsphere.db")
    logger.info(f"Database initialized: {db}")
    
    # Create adapter 
    sqlite_repo = SQLiteModelMetricsRepository(db=db)
    logger.info(f"SQLite repository initialized: {sqlite_repo}")
    
    # Create repository with adapter
    metrics_repo = ModelMetricsRepository(sql_repo=sqlite_repo, test_mode=True)
    logger.info(f"Model metrics repository initialized: {metrics_repo}")
    
    # Create service
    service = ModelMonitoringService(metrics_repository=metrics_repo)
    logger.info(f"Model monitoring service initialized: {service}")
    
    # Check repository settings
    should_use_mock = metrics_repo._should_use_mock_data()
    logger.info(f"Should use mock data? {should_use_mock}")
    
    # Try getting models with error handling
    try:
        logger.info("Getting models from SQL repository directly...")
        sql_models = await sqlite_repo.get_models()
        logger.info(f"Got {len(sql_models)} models from SQL repository")
        for model in sql_models:
            logger.info(f"SQL Model: {model['id']} (data_source: {model.get('data_source', 'Not set')})")
    except Exception as e:
        logger.error(f"Error getting models from SQL repository: {str(e)}")
    
    try:
        logger.info("Getting models from metrics repository...")
        models, is_mock = await metrics_repo.get_models()
        logger.info(f"Got {len(models)} models from metrics repository (is_mock={is_mock})")
        for model in models:
            logger.info(f"Model: {model['id']} (data_source: {model.get('data_source', 'Not set')})")
    except Exception as e:
        logger.error(f"Error getting models from metrics repository: {str(e)}")
    
    try:
        logger.info("Getting models from service...")
        service_models, is_mock = await service.get_monitored_models()
        logger.info(f"Got {len(service_models)} models from service (is_mock={is_mock})")
        for model in service_models:
            logger.info(f"Service Model: {model['id']} (data_source: {model.get('data_source', 'Not set')})")
            
        print("\nSample Model Details:")
        pprint(service_models[0] if service_models else "No models found")
    except Exception as e:
        logger.error(f"Error getting models from service: {str(e)}")
    
    logger.info("Debug complete")

if __name__ == "__main__":
    asyncio.run(main())
