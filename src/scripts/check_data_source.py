"""
Script to check the data source of model data in the running application.

This script prints out models received from the ModelMonitoringService
along with their data source indicators to verify what data source is currently active.
"""
import asyncio
import logging
import os
import sys
from pprint import pprint

# Configure logging to see any errors
logging.basicConfig(level=logging.INFO)

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.append(project_root)

from src.monitoring.model_monitoring_service import ModelMonitoringService


async def check_data_sources():
    """Check and display data sources for all models."""
    print("Checking data sources for models in the application...\n")

    # Create the service
    service = ModelMonitoringService()

    # Get all models
    result = await service.get_models()

    # Extract models from the new data structure if needed
    is_from_db = False
    if isinstance(result, tuple) and len(result) > 0:
        print("API Response Format: (models_array, is_from_db)")
        models = result[0]  # Extract the actual models from the first element
        is_from_db = result[1] if len(result) > 1 else False
    elif isinstance(result, list):
        models = result
        print("API Response Format: direct models list")
    else:
        print(f"API Response Format: unexpected type {type(result)}")
        models = result

    # Check current environment settings
    use_mock_data = os.environ.get("USE_MOCK_DATA", "False").lower() in (
        "true",
        "1",
        "t",
    )
    print(f"Current USE_MOCK_DATA setting: {use_mock_data}")
    print(f"Is data from database (based on API response): {is_from_db}")

    # Print data source information
    print(f"\nFound {len(models)} models:")

    # Check the data structure
    if not models:
        print("No models returned from the service.")
        return

    if not isinstance(models, list):
        print(f"ERROR: Expected models to be a list, got {type(models)}")
        print(f"Data sample: {models}")
        return

    if isinstance(models[0], list):
        print("NOTE: Models are returned as nested lists, not dictionaries.")
        print("Data structure has changed from what was expected.")
        for i, model in enumerate(models):
            print(f"- Model #{i+1}: {model}")
        return

    # Original logic for dictionary models
    try:
        for model in models:
            if not isinstance(model, dict):
                print(f"WARNING: Expected model to be a dictionary, got {type(model)}")
                continue

            data_source = model.get("data_source", "unknown")
            print(
                f"- {model.get('name', 'unknown')} (ID: {model.get('id', 'unknown')}): Source = {data_source}"
            )

        # Count sources
        db_count = sum(
            1
            for m in models
            if isinstance(m, dict) and m.get("data_source") == "database"
        )
        mock_count = sum(
            1 for m in models if isinstance(m, dict) and m.get("data_source") == "mock"
        )
        unknown_count = sum(
            1 for m in models if isinstance(m, dict) and "data_source" not in m
        )
    except (AttributeError, TypeError) as e:
        print(f"ERROR: Unexpected data structure: {e}")
        print(f"Data type: {type(models)}")
        print(f"First model type: {type(models[0]) if models else 'N/A'}")
        print(f"Data sample: {models[:2] if models else 'N/A'}")
        return

    print(f"\nSummary:")
    print(f"- Models from database: {db_count}")
    print(f"- Models from mock data: {mock_count}")
    print(f"- Models with unknown source: {unknown_count}")

    # Recommendations
    if unknown_count > 0:
        print(
            "\nNote: Some models don't have a data_source indicator. Make sure all repository methods add this field."
        )

    if mock_count > 0:
        print(
            "\nAction required: Some models are coming from mock data. To use the database for all models:"
        )
        print("1. Make sure the database is properly initialized")
        print("2. Set USE_MOCK_DATA=False in the environment")
    else:
        print("\nAll models are coming from the database. No action required.")


if __name__ == "__main__":
    asyncio.run(check_data_sources())
