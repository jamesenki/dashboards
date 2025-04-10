"""
Integration tests for the Model Metrics Repository gateway to external systems.

These tests validate the integration between the Model Metrics Repository gateway
and the external database system following Clean Architecture principles.

Tests are tagged with their TDD phase:
- @red: Tests that define expected behavior but will fail (not yet implemented)
- @green: Tests that pass with minimal implementation
- @refactor: Tests that continue to pass after code improvements
"""
import asyncio
import os
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.db.adapters.sqlite_model_metrics import SQLiteModelMetricsRepository
from src.db.initialize_db import initialize_database
from src.db.real_database import SQLiteDatabase
from src.domain.entities.model_metrics import ModelMetrics
from src.domain.value_objects.metric_value import MetricValue
from src.domain.value_objects.model_identifier import ModelIdentifier
from src.domain.value_objects.timestamp import Timestamp


@pytest.fixture
def in_memory_database():
    """Create an in-memory SQLite database for testing.

    This fixture follows Clean Architecture by providing a real
    but isolated external system for integration testing.
    """
    db = initialize_database(in_memory=True, populate=False)
    return db


@pytest.fixture
def sample_model_metrics():
    """Generate sample model metrics for testing.

    This follows Clean Architecture by creating domain entities
    directly rather than relying on repository-specific structures.
    """
    test_id = uuid.uuid4().hex[:8]

    return ModelMetrics(
        model_id=ModelIdentifier(f"test-model-{test_id}"),
        accuracy=MetricValue(0.92),
        precision=MetricValue(0.88),
        recall=MetricValue(0.90),
        f1_score=MetricValue(0.89),
        latency_ms=MetricValue(150.5),
        timestamp=Timestamp(datetime.now()),
        version="1.0.0",
    )


class TestModelMetricsRepositoryIntegration:
    """Integration tests for the Model Metrics Repository gateway to external database.

    These tests validate that:
    1. The repository correctly persists domain entities to the database
    2. The repository correctly retrieves and reconstructs domain entities
    3. The repository properly handles database errors

    Following Clean Architecture principles, this tests the boundary between
    the gateway interface and the external system (database).
    """

    @pytest.mark.green
    async def test_save_model_metrics(self, in_memory_database, sample_model_metrics):
        """Test saving model metrics to the database.

        RED phase: This test defines the expected behavior for persisting metrics.

        Business value: Ensures AI models' performance metrics can be reliably stored
        for later analysis and model health monitoring.
        """
        # Setup - Create the repository with a real database connection
        repository = SQLiteModelMetricsRepository(db=in_memory_database)

        # Execute - Save metrics to the database
        saved_id = await repository.save_metrics(sample_model_metrics)

        # Verify - ID was returned
        assert saved_id is not None
        assert isinstance(saved_id, str)

        # Verify - Metrics can be retrieved from the database
        retrieved_metrics = await repository.get_metrics_by_id(saved_id)
        assert retrieved_metrics is not None
        assert retrieved_metrics.model_id.value == sample_model_metrics.model_id.value
        assert retrieved_metrics.accuracy.value == sample_model_metrics.accuracy.value
        assert retrieved_metrics.precision.value == sample_model_metrics.precision.value
        assert (
            retrieved_metrics.timestamp.value.date()
            == sample_model_metrics.timestamp.value.date()
        )

    @pytest.mark.green
    async def test_get_metrics_by_model_id(
        self, in_memory_database, sample_model_metrics
    ):
        """Test retrieving metrics by model ID.

        RED phase: This test defines the expected behavior for retrieving metrics by model ID.

        Business value: Enables tracking of specific AI model performance over time
        for monitoring and improvement.
        """
        # Setup - Create the repository and save sample metrics
        repository = SQLiteModelMetricsRepository(db=in_memory_database)
        await repository.save_metrics(sample_model_metrics)

        # Execute - Retrieve metrics by model ID
        metrics_list = await repository.get_metrics_by_model_id(
            sample_model_metrics.model_id.value
        )

        # Verify - Metrics were retrieved
        assert metrics_list is not None
        assert len(metrics_list) > 0

        # Verify - Retrieved data matches what was saved
        retrieved_metrics = metrics_list[0]
        assert retrieved_metrics.model_id.value == sample_model_metrics.model_id.value
        assert retrieved_metrics.accuracy.value == sample_model_metrics.accuracy.value
        assert retrieved_metrics.precision.value == sample_model_metrics.precision.value

    @pytest.mark.green
    async def test_get_metrics_by_time_range(
        self, in_memory_database, sample_model_metrics
    ):
        """Test retrieving metrics within a time range.

        RED phase: This test defines the expected behavior for time-based queries.

        Business value: Enables analysis of AI model drift and performance degradation
        over specific time periods.
        """
        # Setup - Create the repository and save sample metrics
        repository = SQLiteModelMetricsRepository(db=in_memory_database)
        await repository.save_metrics(sample_model_metrics)

        # Define time range for query - include the current time
        end_time = datetime.now() + timedelta(hours=1)
        start_time = datetime.now() - timedelta(hours=1)

        # Execute - Retrieve metrics within time range
        metrics_list = await repository.get_metrics_by_time_range(
            start_time=start_time, end_time=end_time
        )

        # Verify - Metrics within range were retrieved
        assert metrics_list is not None
        assert len(metrics_list) > 0

        # Verify - Retrieved metrics match what was saved
        found_match = False
        for metrics in metrics_list:
            if metrics.model_id.value == sample_model_metrics.model_id.value:
                found_match = True
                assert metrics.accuracy.value == sample_model_metrics.accuracy.value
                break

        assert (
            found_match
        ), "The saved metrics were not found in the time range query results"

    @pytest.mark.green
    async def test_update_metrics(self, in_memory_database, sample_model_metrics):
        """Test updating existing model metrics.

        RED phase: This test defines the expected behavior for updating metrics.

        Business value: Allows correction of erroneous metrics or updating
        calculated metrics after additional data analysis.
        """
        # Setup - Create the repository and save sample metrics
        repository = SQLiteModelMetricsRepository(db=in_memory_database)
        metrics_id = await repository.save_metrics(sample_model_metrics)

        # Create updated metrics with the same ID but different values
        updated_metrics = ModelMetrics(
            id=metrics_id,
            model_id=sample_model_metrics.model_id,
            accuracy=MetricValue(0.95),  # Improved accuracy
            precision=MetricValue(0.90),  # Improved precision
            recall=MetricValue(0.91),  # Improved recall
            f1_score=MetricValue(0.93),  # Improved F1 score
            latency_ms=MetricValue(140.0),  # Reduced latency
            timestamp=Timestamp(datetime.now()),
            version=sample_model_metrics.version,
        )

        # Execute - Update the metrics
        success = await repository.update_metrics(updated_metrics)

        # Verify - Update was successful
        assert success is True

        # Verify - Retrieved metrics match the updated values
        retrieved_metrics = await repository.get_metrics_by_id(metrics_id)
        assert retrieved_metrics is not None
        assert retrieved_metrics.accuracy.value == 0.95
        assert retrieved_metrics.precision.value == 0.90
        assert retrieved_metrics.latency_ms.value == 140.0

    @pytest.mark.green
    async def test_delete_metrics(self, in_memory_database, sample_model_metrics):
        """Test deleting model metrics.

        RED phase: This test defines the expected behavior for metrics deletion.

        Business value: Supports data retention policies and removal of
        invalid or outdated metrics.
        """
        # Setup - Create the repository and save sample metrics
        repository = SQLiteModelMetricsRepository(db=in_memory_database)
        metrics_id = await repository.save_metrics(sample_model_metrics)

        # Verify metrics exists
        retrieved_before_delete = await repository.get_metrics_by_id(metrics_id)
        assert retrieved_before_delete is not None

        # Execute - Delete the metrics
        success = await repository.delete_metrics(metrics_id)

        # Verify - Deletion was successful
        assert success is True

        # Verify - Metrics no longer exists
        retrieved_after_delete = await repository.get_metrics_by_id(metrics_id)
        assert retrieved_after_delete is None

    @pytest.mark.green
    async def test_get_latest_metrics_by_model(self, in_memory_database):
        """Test retrieving the latest metrics for multiple models.

        RED phase: This test defines the expected behavior for getting
        the most recent metrics.

        Business value: Enables dashboard displays of current model performance
        without requiring time range filtering.
        """
        # Setup - Create the repository and multiple metrics for same model
        repository = SQLiteModelMetricsRepository(db=in_memory_database)
        model_id = f"test-model-{uuid.uuid4().hex[:8]}"

        # Create metrics from 3 days ago
        old_metrics = ModelMetrics(
            model_id=ModelIdentifier(model_id),
            accuracy=MetricValue(0.85),
            precision=MetricValue(0.80),
            recall=MetricValue(0.82),
            f1_score=MetricValue(0.81),
            latency_ms=MetricValue(200.0),
            timestamp=Timestamp(datetime.now() - timedelta(days=3)),
            version="1.0.0",
        )

        # Create metrics from today (newest)
        new_metrics = ModelMetrics(
            model_id=ModelIdentifier(model_id),
            accuracy=MetricValue(0.92),
            precision=MetricValue(0.88),
            recall=MetricValue(0.90),
            f1_score=MetricValue(0.89),
            latency_ms=MetricValue(150.5),
            timestamp=Timestamp(datetime.now()),
            version="1.0.1",
        )

        # Save both sets of metrics
        await repository.save_metrics(old_metrics)
        await repository.save_metrics(new_metrics)

        # Execute - Get latest metrics
        latest_metrics = await repository.get_latest_metrics_by_model(model_id)

        # Verify - Retrieved the newest metrics
        assert latest_metrics is not None
        assert latest_metrics.model_id.value == model_id
        assert latest_metrics.accuracy.value == 0.92  # Should match newest metrics
        assert latest_metrics.version == "1.0.1"  # Should match newest version

    # GREEN phase tests would be added here after implementation
    # They would have the @pytest.mark.green decorator

    # REFACTOR phase tests would be added after code improvements
    # They would have the @pytest.mark.refactor decorator
