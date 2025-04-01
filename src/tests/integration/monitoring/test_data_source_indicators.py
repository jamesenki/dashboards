"""
Tests for data source indicators in model metrics.

This test verifies that models returned from the repository correctly include
data source indicators showing if they came from database or mock data.
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


class TestDataSourceIndicators:
    """Tests to verify data source indicators are present in model data."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Initialize an in-memory database for testing
        self.db = initialize_database(in_memory=True, populate=True)
        
        # Create a real repository that uses our test database
        self.sqlite_repo = SQLiteModelMetricsRepository(db=self.db)
        
        # Create the repository with our real DB connection
        self.metrics_repository = ModelMetricsRepository(sql_repo=self.sqlite_repo, test_mode=True)
        
        # Create the service with our repository
        self.service = ModelMonitoringService(metrics_repository=self.metrics_repository)
        
        # Add a unique test model to verify database access
        self.unique_model_id = f"test-model-{str(uuid.uuid4())[:8]}"
        self.db.execute(
            "INSERT INTO models (id, name, description, archived) VALUES (?, ?, ?, ?)",
            (self.unique_model_id, "Data Source Test Model", "Created to test data source indicators", 0)
        )
    
    @pytest.mark.asyncio
    async def test_database_models_have_source_indicator(self):
        """Test that models loaded from database have a database source indicator."""
        # Force using database
        os.environ['USE_MOCK_DATA'] = 'False'
        
        # Get models (should come from database)
        models = await self.service.get_models()
        
        # Verify our unique test model has a data_source indicator
        unique_model = next((m for m in models if m['id'] == self.unique_model_id), None)
        assert unique_model is not None, "Unique test model not found - not loading from database"
        
        # Check that the data source indicator is present and set to 'database'
        assert 'data_source' in unique_model, "Data source indicator missing from model"
        assert unique_model['data_source'] == 'database', "Model from database doesn't have database source indicator"
        
        # Print an example model with its source
        print(f"\nExample database model: {unique_model['name']} (data source: {unique_model['data_source']})")
    
    @pytest.mark.asyncio
    async def test_mock_models_have_source_indicator(self):
        """Test that models loaded from mock data have a mock source indicator."""
        # Force using mock data
        os.environ['USE_MOCK_DATA'] = 'True'
        
        # Create a new repository that will honor the USE_MOCK_DATA environment variable
        mock_metrics_repository = ModelMetricsRepository(test_mode=True)
        mock_service = ModelMonitoringService(metrics_repository=mock_metrics_repository)
        
        # Get models (should come from mock data)
        models = await mock_service.get_models()
        
        # Verify all models have a data_source indicator set to 'mock'
        for model in models:
            assert 'data_source' in model, f"Data source indicator missing from model {model['id']}"
            assert model['data_source'] == 'mock', f"Model {model['id']} doesn't have mock source indicator"
        
        # Print an example model with its source
        if models:
            print(f"\nExample mock model: {models[0]['name']} (data source: {models[0]['data_source']})")
    
    @pytest.mark.asyncio
    async def test_fallback_to_mock_has_indicator(self):
        """Test that models that fall back to mock data have a mock source indicator."""
        # Force database to be primary source
        os.environ['USE_MOCK_DATA'] = 'False'
        
        # Create a mock repo that raises an exception when get_models is called
        failing_repo = AsyncMock(spec=SQLiteModelMetricsRepository)
        failing_repo.get_models.side_effect = Exception("Simulated database error")
        
        # Create repository with the failing mock
        repo_with_fallback = ModelMetricsRepository(sql_repo=failing_repo, test_mode=True)
        service_with_fallback = ModelMonitoringService(metrics_repository=repo_with_fallback)
        
        # Get models (should fall back to mock data due to the exception)
        models = await service_with_fallback.get_models()
        
        # Verify all models have a data_source indicator set to 'mock'
        for model in models:
            assert 'data_source' in model, f"Data source indicator missing from model {model['id']}"
            assert model['data_source'] == 'mock', f"Model {model['id']} doesn't have mock source indicator"
        
        # Print an example model with its source
        if models:
            print(f"\nExample fallback model: {models[0]['name']} (data source: {models[0]['data_source']})")
