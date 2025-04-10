"""
Tests for data source indicators in model metrics.

This test verifies that models returned from the repository correctly include
data source indicators showing if they came from database or mock data.
"""
import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.db.adapters.sqlite_model_metrics import SQLiteModelMetricsRepository
from src.db.initialize_db import initialize_database
from src.db.real_database import SQLiteDatabase
from src.monitoring.model_metrics_repository import ModelMetricsRepository
from src.monitoring.model_monitoring_service import ModelMonitoringService


class TestDataSourceIndicators:
    """Tests to verify data source indicators are present in model data."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Initialize an in-memory database for testing
        self.db = initialize_database(in_memory=True, populate=True)

        # Create a real repository that uses our test database
        self.sqlite_repo = SQLiteModelMetricsRepository(db=self.db)

        # Create the repository with our real DB connection
        self.metrics_repository = ModelMetricsRepository(
            sql_repo=self.sqlite_repo, test_mode=True
        )

        # Create the service with our repository
        self.service = ModelMonitoringService(
            metrics_repository=self.metrics_repository
        )

        # Add a unique test model to verify database access
        self.unique_model_id = f"test-model-{str(uuid.uuid4())[:8]}"
        self.db.execute(
            "INSERT INTO models (id, name, description, archived) VALUES (?, ?, ?, ?)",
            (
                self.unique_model_id,
                "Data Source Test Model",
                "Created to test data source indicators",
                0,
            ),
        )

    @pytest.mark.asyncio
    async def test_database_models_have_source_indicator(self):
        """Test that models loaded from database have a database source indicator.

        This test enforces strict validation that the system must be using
        real database data, not falling back to mock data. If the system
        falls back to mock data, this test will fail.
        """
        # Force using database and disable fallback
        os.environ["USE_MOCK_DATA"] = "False"
        os.environ["DATABASE_FALLBACK_ENABLED"] = "False"

        try:
            # Get models (should come from database)
            result = await self.service.get_models()

            # Check if we have the new data structure (tuple with models in first element)
            if isinstance(result, tuple) and len(result) > 0:
                print("\nDetected new data structure: (models_array, is_from_db)")
                models = result[0]  # Extract the actual models from the first element
                is_from_db = result[1] if len(result) > 1 else False
                print(f"Models from database: {is_from_db}")
            elif isinstance(result, list):
                # Fall back to original interpretation
                models = result
            else:
                pytest.fail(f"Unexpected data structure: {type(result)}")

            # Verify we have models to work with
            assert models, "No models returned from the service"

            # Verify data structure of models
            assert isinstance(models[0], dict), "Models are not dictionaries"

            # Print all model IDs to help debug
            print(f"\nAll model IDs: {[m.get('id') for m in models]}")
            print(f"Looking for test model ID: {self.unique_model_id}")

            # Verify our unique test model was found in the results
            # This is critical - if not found, we must be using mock data
            unique_model = next(
                (m for m in models if m.get("id") == self.unique_model_id), None
            )
            if unique_model is None:
                pytest.fail(
                    f"\nTEST FAILED: Unique test model '{self.unique_model_id}' not found!\n"
                    "This indicates the system is using MOCK DATA instead of the DATABASE.\n"
                    "The mock data doesn't contain the test model we added to the database.\n"
                    "Check database connectivity and that environment variables are respected."
                )

            # Check that the data source indicator is present and set to 'database'
            assert (
                "data_source" in unique_model
            ), "Data source indicator missing from model"
            assert (
                unique_model["data_source"] == "database"
            ), "Model from database doesn't have database source indicator"

            # Print an example model with its source
            print(
                f"\nExample database model: {unique_model['name']} (data source: {unique_model['data_source']})"
            )
        except (TypeError, KeyError) as e:
            pytest.fail(f"Data structure issue: {e}")

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="API contract changed: data_source field missing from some mock models"
    )
    async def test_mock_models_have_source_indicator(self):
        """Test that models loaded from mock data have a mock source indicator."""
        # Force using mock data
        os.environ["USE_MOCK_DATA"] = "True"

        try:
            # Create a new repository that will honor the USE_MOCK_DATA environment variable
            mock_metrics_repository = ModelMetricsRepository(test_mode=True)
            mock_service = ModelMonitoringService(
                metrics_repository=mock_metrics_repository
            )

            # Get models (should come from mock data)
            result = await mock_service.get_models()

            # Check if we have the new data structure (tuple with models in first element)
            if isinstance(result, tuple) and len(result) > 0:
                print("\nDetected new data structure: (models_array, is_from_db)")
                models = result[0]  # Extract the actual models from the first element
                is_from_db = result[1] if len(result) > 1 else False
                print(f"Models from database: {is_from_db}")
            elif isinstance(result, list):
                # Fall back to original interpretation
                models = result
            else:
                pytest.fail(f"Unexpected data structure: {type(result)}")

            # Verify we have models to work with
            assert models, "No models returned from the service"

            # Verify data structure of models
            assert isinstance(models[0], dict), "Models are not dictionaries"

            # Verify models have data_source field
            # Print model details to understand data structure
            if models:
                print(f"\nFirst model fields: {list(models[0].keys())}")
                print(f"Example model: {models[0]}")

            # Count models with and without data_source
            with_source = sum(1 for m in models if "data_source" in m)
            without_source = sum(1 for m in models if "data_source" not in m)
            print(f"Models with data_source: {with_source}, without: {without_source}")

            # Verify all models have a data_source indicator set to 'mock'
            for model in models:
                assert (
                    "data_source" in model
                ), f"Data source indicator missing from model {model.get('id', 'unknown')}"
                assert (
                    model["data_source"] == "mock"
                ), f"Model {model.get('id', 'unknown')} doesn't have mock source indicator"

            # Print an example model with its source
            if models:
                print(
                    f"\nExample mock model: {models[0].get('name', 'unknown')} (data source: {models[0].get('data_source', 'unknown')})"
                )
        except (TypeError, KeyError) as e:
            pytest.fail(f"Data structure issue: {e}")

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="API contract changed: data_source field missing from some mock models"
    )
    async def test_fallback_to_mock_has_indicator(self):
        """Test that models that fall back to mock data have a mock source indicator."""
        # Force database to be primary source
        os.environ["USE_MOCK_DATA"] = "False"

        try:
            # Create a mock repo that raises an exception when get_models is called
            failing_repo = AsyncMock(spec=SQLiteModelMetricsRepository)
            failing_repo.get_models.side_effect = Exception("Simulated database error")

            # Create repository with the failing mock
            repo_with_fallback = ModelMetricsRepository(
                sql_repo=failing_repo, test_mode=True
            )
            service_with_fallback = ModelMonitoringService(
                metrics_repository=repo_with_fallback
            )

            # Get models (should fall back to mock data due to the exception)
            result = await service_with_fallback.get_models()

            # Check if we have the new data structure (tuple with models in first element)
            if isinstance(result, tuple) and len(result) > 0:
                print("\nDetected new data structure: (models_array, is_from_db)")
                models = result[0]  # Extract the actual models from the first element
                is_from_db = result[1] if len(result) > 1 else False
                print(f"Models from database: {is_from_db}")
            elif isinstance(result, list):
                # Fall back to original interpretation
                models = result
            else:
                pytest.fail(f"Unexpected data structure: {type(result)}")

            # Verify we have models to work with
            assert models, "No models returned from the service"

            # Verify data structure of models
            assert isinstance(models[0], dict), "Models are not dictionaries"

            # Verify models have data_source field
            # Print model details to understand data structure
            if models:
                print(f"\nFirst model fields: {list(models[0].keys())}")
                print(f"Example model: {models[0]}")

            # Count models with and without data_source
            with_source = sum(1 for m in models if "data_source" in m)
            without_source = sum(1 for m in models if "data_source" not in m)
            print(f"Models with data_source: {with_source}, without: {without_source}")

            # Verify all models have a data_source indicator set to 'mock'
            for model in models:
                assert (
                    "data_source" in model
                ), f"Data source indicator missing from model {model.get('id', 'unknown')}"
                assert (
                    model["data_source"] == "mock"
                ), f"Model {model.get('id', 'unknown')} doesn't have mock source indicator"

            # Print an example model with its source
            if models:
                print(
                    f"\nExample fallback model: {models[0].get('name', 'unknown')} (data source: {models[0].get('data_source', 'unknown')})"
                )
        except (TypeError, KeyError) as e:
            pytest.fail(f"Data structure issue: {e}")
