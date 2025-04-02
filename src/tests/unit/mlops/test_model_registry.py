"""
Tests for the MLOps Model Registry.
"""
import json
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.mlops.model_registry import ModelRegistry


class TestModelRegistry:
    """Test suite for the model registry implementation."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.db_mock = MagicMock()
        self.storage_path = "/tmp/model_registry_test"
        self.model_registry = ModelRegistry(self.db_mock, self.storage_path)

        # Sample model metadata
        self.sample_metadata = {
            "accuracy": 0.92,
            "precision": 0.88,
            "recall": 0.95,
            "f1_score": 0.91,
            "training_date": "2025-03-01",
            "training_duration_minutes": 45,
            "feature_importance": {
                "temperature": 0.4,
                "pressure": 0.3,
                "age_days": 0.2,
                "daily_cycles": 0.1,
            },
        }

    def test_init(self):
        """Test that the model registry initializes correctly."""
        assert self.model_registry.db == self.db_mock
        assert self.model_registry.storage_path == self.storage_path

    def test_register_model(self):
        """Test registering a new model."""
        # Arrange
        model_name = "component_failure"
        model_version = "2025.03.27.001"
        model_path = "/tmp/models/component_failure_model.pkl"

        # Act
        model_id = self.model_registry.register_model(
            model_name=model_name,
            model_version=model_version,
            model_path=model_path,
            metadata=self.sample_metadata,
        )

        # Assert
        assert model_id is not None and isinstance(model_id, str)
        self.db_mock.execute.assert_called_once()

    def test_get_model_info(self):
        """Test retrieving model information."""
        # Arrange
        model_name = "component_failure"
        model_version = "2025.03.27.001"
        expected_model_info = {
            "model_id": "model-123",
            "model_name": model_name,
            "model_version": model_version,
            "status": "active",
            "created_at": datetime(2025, 3, 27),
            "metadata": json.dumps(self.sample_metadata),
        }

        # Mock the database response
        self.db_mock.execute.return_value = [expected_model_info]

        # Act
        model_info = self.model_registry.get_model_info(
            model_name=model_name, model_version=model_version
        )

        # Assert
        assert model_info is not None
        assert model_info["model_name"] == model_name
        assert model_info["model_version"] == model_version
        self.db_mock.execute.assert_called_once()

    def test_get_model_info_not_found(self):
        """Test retrieving model information when model doesn't exist."""
        # Arrange
        model_name = "nonexistent_model"
        model_version = "2025.03.27.001"

        # Mock empty database response
        self.db_mock.execute.return_value = []

        # Act
        model_info = self.model_registry.get_model_info(
            model_name=model_name, model_version=model_version
        )

        # Assert
        assert model_info is None
        self.db_mock.execute.assert_called_once()

    def test_get_model_versions(self):
        """Test retrieving all versions of a model."""
        # Arrange
        model_name = "component_failure"
        expected_versions = [
            {
                "model_id": "model-123",
                "model_name": model_name,
                "model_version": "2025.03.27.001",
                "status": "active",
                "created_at": datetime(2025, 3, 27),
            },
            {
                "model_id": "model-456",
                "model_name": model_name,
                "model_version": "2025.03.26.001",
                "status": "archived",
                "created_at": datetime(2025, 3, 26),
            },
        ]

        # Mock the database response
        self.db_mock.execute.return_value = expected_versions

        # Act
        versions = self.model_registry.get_model_versions(model_name=model_name)

        # Assert
        assert len(versions) == 2
        assert all(version["model_name"] == model_name for version in versions)
        self.db_mock.execute.assert_called_once()

    def test_activate_model(self):
        """Test activating a model version."""
        # Arrange
        model_name = "component_failure"
        model_version = "2025.03.27.001"

        # Act
        success = self.model_registry.activate_model(
            model_name=model_name, model_version=model_version
        )

        # Assert
        assert success is True
        # Should call execute at least twice (once to deactivate old versions, once to activate new)
        assert self.db_mock.execute.call_count >= 2

    def test_archive_model(self):
        """Test archiving a model version."""
        # Arrange
        model_name = "component_failure"
        model_version = "2025.03.27.001"

        # Act
        success = self.model_registry.archive_model(
            model_name=model_name, model_version=model_version
        )

        # Assert
        assert success is True
        self.db_mock.execute.assert_called_once()

    def test_get_active_model(self):
        """Test retrieving the active model for a given model type."""
        # Arrange
        model_name = "component_failure"
        expected_model_info = {
            "model_id": "model-123",
            "model_name": model_name,
            "model_version": "2025.03.27.001",
            "status": "active",
            "created_at": datetime(2025, 3, 27),
            "metadata": json.dumps(self.sample_metadata),
        }

        # Mock the database response
        self.db_mock.execute.return_value = [expected_model_info]

        # Act
        active_model = self.model_registry.get_active_model(model_name=model_name)

        # Assert
        assert active_model is not None
        assert active_model["model_name"] == model_name
        assert active_model["status"] == "active"
        self.db_mock.execute.assert_called_once()

    def test_get_model_path(self):
        """Test retrieving the file path for a model."""
        # Arrange
        model_name = "component_failure"
        model_version = "2025.03.27.001"
        expected_model_info = {
            "model_id": "model-123",
            "model_name": model_name,
            "model_version": model_version,
            "model_path": "/tmp/models/component_failure_2025.03.27.001.pkl",
            "status": "active",
        }

        # Mock the database response
        self.db_mock.execute.return_value = [expected_model_info]

        # Act
        model_path = self.model_registry.get_model_path(
            model_name=model_name, model_version=model_version
        )

        # Assert
        assert model_path == expected_model_info["model_path"]
        self.db_mock.execute.assert_called_once()

    def test_get_active_models(self):
        """Test retrieving all active models."""
        # Arrange
        expected_models = [
            {
                "model_id": "model-123",
                "model_name": "component_failure",
                "model_version": "2025.03.27.001",
                "status": "active",
                "created_at": datetime(2025, 3, 27),
            },
            {
                "model_id": "model-456",
                "model_name": "lifespan_estimation",
                "model_version": "2025.03.26.001",
                "status": "active",
                "created_at": datetime(2025, 3, 26),
            },
        ]

        # Mock the database response
        self.db_mock.execute.return_value = expected_models

        # Act
        active_models = self.model_registry.get_active_models()

        # Assert
        assert len(active_models) == 2
        assert all(model["status"] == "active" for model in active_models)
        self.db_mock.execute.assert_called_once()

    def test_compare_models(self):
        """Test comparing two model versions."""
        # Arrange
        model_name = "component_failure"
        version_a = "2025.03.27.001"
        version_b = "2025.03.26.001"

        model_a_info = {
            "model_id": "model-123",
            "model_name": model_name,
            "model_version": version_a,
            "metadata": json.dumps(
                {"accuracy": 0.92, "precision": 0.88, "recall": 0.95}
            ),
        }

        model_b_info = {
            "model_id": "model-456",
            "model_name": model_name,
            "model_version": version_b,
            "metadata": json.dumps(
                {"accuracy": 0.89, "precision": 0.85, "recall": 0.92}
            ),
        }

        # Configure the mock to return different results for different calls
        self.db_mock.execute.side_effect = [[model_a_info], [model_b_info]]

        # Act
        comparison = self.model_registry.compare_models(
            model_name=model_name, version_a=version_a, version_b=version_b
        )

        # Assert
        assert comparison is not None
        assert "metrics_diff" in comparison
        assert comparison["metrics_diff"]["accuracy"] > 0  # Version A is better
        assert comparison["winner"] == version_a
