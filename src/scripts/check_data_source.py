"""
Script to check the data source of model data in the running application.

This script prints out models received from the ModelMonitoringService
along with their data source indicators to verify what data source is currently active.
"""
import os
import sys
import asyncio
import logging
from pprint import pprint

# Configure logging to see any errors
logging.basicConfig(level=logging.INFO)

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

from src.monitoring.model_monitoring_service import ModelMonitoringService

async def check_data_sources():
    """Check and display data sources for all models."""
    print("Checking data sources for models in the application...\n")
    
    # Create the service
    service = ModelMonitoringService()
    
    # Get all models
    models = await service.get_models()
    
    # Check current environment settings
    use_mock_data = os.environ.get('USE_MOCK_DATA', 'False').lower() in ('true', '1', 't')
    print(f"Current USE_MOCK_DATA setting: {use_mock_data}")
    
    # Print data source information
    print(f"\nFound {len(models)} models:")
    for model in models:
        data_source = model.get('data_source', 'unknown')
        print(f"- {model['name']} (ID: {model['id']}): Source = {data_source}")
    
    # Count sources
    db_count = sum(1 for m in models if m.get('data_source') == 'database')
    mock_count = sum(1 for m in models if m.get('data_source') == 'mock')
    unknown_count = sum(1 for m in models if 'data_source' not in m)
    
    print(f"\nSummary:")
    print(f"- Models from database: {db_count}")
    print(f"- Models from mock data: {mock_count}")
    print(f"- Models with unknown source: {unknown_count}")
    
    # Recommendations
    if unknown_count > 0:
        print("\nNote: Some models don't have a data_source indicator. Make sure all repository methods add this field.")
    
    if mock_count > 0:
        print("\nAction required: Some models are coming from mock data. To use the database for all models:")
        print("1. Make sure the database is properly initialized")
        print("2. Set USE_MOCK_DATA=False in the environment")
    else:
        print("\nAll models are coming from the database. No action required.")

if __name__ == "__main__":
    asyncio.run(check_data_sources())
