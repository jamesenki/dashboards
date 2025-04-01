"""
Test module to verify that the model metrics are loaded from the database
rather than from mock data.
"""
import os
import sys
import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.monitoring.model_metrics_repository import ModelMetricsRepository
from src.monitoring.model_monitoring_service import ModelMonitoringService
from src.db.adapters.sqlite_model_metrics import SQLiteModelMetricsRepository
from src.db.real_database import SQLiteDatabase
from src.db.initialize_db import initialize_database


class TestDatabaseLoading:
    """Tests to verify data is loaded from database not mocks."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Initialize an in-memory database for testing
        self.db = initialize_database(in_memory=True, populate=True)
        
        # Create a real repository that uses our test database
        self.sqlite_repo = SQLiteModelMetricsRepository(db=self.db)
        
        # Create a spy repository to track method calls for verification
        self.sql_repo_spy = AsyncMock(wraps=self.sqlite_repo)
        
        # Create the repository with our spy and enable test_mode to suppress error messages
        self.metrics_repository = ModelMetricsRepository(sql_repo=self.sql_repo_spy, test_mode=True)
        
        # Create the service with our repository
        self.service = ModelMonitoringService(metrics_repository=self.metrics_repository)
        
        # Ensure USE_MOCK_DATA is set to False for tests
        os.environ['USE_MOCK_DATA'] = 'False'
        
        # Add a unique test model to verify database access
        self.unique_model_id = f"test-model-{str(uuid.uuid4())[:8]}"
        self.db.execute(
            "INSERT INTO models (id, name, description, archived) VALUES (?, ?, ?, ?)",
            (self.unique_model_id, "Unique Test Model", "Created just for this test", 0)
        )
        
        # Add a version for this model
        version_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO model_versions (id, model_id, version, file_path) VALUES (?, ?, ?, ?)",
            (version_id, self.unique_model_id, "1.0", "/test/path.pkl")
        )
        
        # Add some metrics for this model
        metrics_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO model_metrics (id, model_id, model_version, metric_name, metric_value, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (metrics_id, self.unique_model_id, "1.0", "accuracy", 0.987, datetime.now().isoformat())
        )
        
    @pytest.mark.asyncio
    async def test_db_is_primary_data_source(self):
        """Test that the database is the primary data source, not mock data."""
        # Call the service method
        models = await self.service.get_models()
        
        # Verify the SQL repository was called (indicating we're using DB as primary)
        self.sql_repo_spy.get_models.assert_called_once()
        
        # Verify our unique test model was returned - this proves we're loading from DB
        unique_model = next((m for m in models if m['id'] == self.unique_model_id), None)
        assert unique_model is not None, "Unique test model not found - not loading from database"
        assert unique_model['name'] == "Unique Test Model"
        assert unique_model['metrics']['accuracy'] == 0.987
    
    @pytest.mark.asyncio
    async def test_mock_data_is_fallback_only(self):
        """Test that mock data is only used as a fallback, not primary."""
        # Configure the SQL repo to raise an exception to trigger fallback
        self.sql_repo_spy.get_models.side_effect = Exception("Database error")
        
        # Call the service method
        models = await self.service.get_models()
        
        # Verify the SQL repository was called first (indicating we tried DB first)
        self.sql_repo_spy.get_models.assert_called_once()
        
        # Verify we got fallback mock data
        assert len(models) > 0  # Mock data should have some models
        
        # Verify our unique test model is NOT in the results (proving we're using mock data)
        unique_model = next((m for m in models if m['id'] == self.unique_model_id), None)
        assert unique_model is None, "Found unique test model in fallback data - still using database"
        
    @pytest.mark.asyncio
    async def test_toggle_between_db_and_mock(self):
        """Test that setting USE_MOCK_DATA env var toggles between DB and mock."""
        # First with USE_MOCK_DATA=False (should use DB)
        os.environ['USE_MOCK_DATA'] = 'False'
        
        # Reset the spy to clear call history
        self.sql_repo_spy.get_models.reset_mock()
        
        # Get a new repository instance to respect the updated env var
        metrics_repository = ModelMetricsRepository(sql_repo=self.sql_repo_spy, test_mode=True)
        service = ModelMonitoringService(metrics_repository=metrics_repository)
        
        # Call the service method
        models_from_db = await service.get_models()
        
        # Verify SQL repo was called
        assert self.sql_repo_spy.get_models.called
        
        # Verify we can find our unique test model (proving we're using database)
        unique_model = next((m for m in models_from_db if m['id'] == self.unique_model_id), None)
        assert unique_model is not None, "Unique test model not found in DB results"
        
        self.sql_repo_spy.get_models.reset_mock()
        
        # Now with USE_MOCK_DATA=True (should use mock data directly)
        os.environ['USE_MOCK_DATA'] = 'True'
        
        # Get a new repository instance to respect the updated env var
        metrics_repository = ModelMetricsRepository(sql_repo=self.sql_repo_spy, test_mode=True)
        service = ModelMonitoringService(metrics_repository=metrics_repository)
        
        # Call the service method
        models_from_mock = await service.get_models()
        
        # Verify SQL repo was NOT called (went straight to mock data)
        assert not self.sql_repo_spy.get_models.called
        
        # Verify our unique model is NOT in results (proving we're using mock data)
        unique_model = next((m for m in models_from_mock if m['id'] == self.unique_model_id), None)
        assert unique_model is None, "Found unique test model in mock data"
    
    @pytest.mark.asyncio
    async def test_record_and_retrieve_metrics(self):
        """Test that we can record metrics to the database and then retrieve them."""
        # Record new metrics for our test model
        test_metrics = {
            "precision": 0.92,
            "recall": 0.88,
            "f1_score": 0.90,
            "latency_ms": 123.45
        }
        
        # Use the service to record metrics
        await self.service.record_model_metrics(
            model_id=self.unique_model_id,
            model_version="1.0",
            metrics=test_metrics
        )
        
        # Now retrieve the metrics history for one of these metrics
        history = await self.service.get_model_metrics_history(
            model_id=self.unique_model_id,
            model_version="1.0",
            metric_name="precision"
        )
        
        # Verify we got data back from the database
        assert len(history) > 0
        
        # Print the structure for debugging
        print(f"\nHistory structure: {history[0].keys()}")
        
        # Check if the data is formatted with 'value' or 'metric_value' key
        if 'value' in history[0]:
            values = [entry['value'] for entry in history]
        elif 'metric_value' in history[0]:
            values = [entry['metric_value'] for entry in history]
        else:
            # If neither key exists, print all available keys
            available_keys = list(history[0].keys())
            raise KeyError(f"Expected 'value' or 'metric_value' in history entries, found: {available_keys}")
        
        # Verify the value matches what we recorded
        assert 0.92 in values, "Could not find recorded metric value in database result"
