"""
Tests for the MLOps Feature Store.
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.mlops.feature_store import FeatureStore


class TestFeatureStore:
    """Test suite for the feature store implementation."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.db_mock = MagicMock()
        self.feature_store = FeatureStore(self.db_mock)

        # Sample mock data
        self.mock_raw_data = [
            {
                "device_id": "wh-123",
                "temperature": 142,
                "pressure": 55,
                "age_days": 732,
                "timestamp": datetime(2025, 1, 1),
            },
            {
                "device_id": "wh-123",
                "temperature": 145,
                "pressure": 57,
                "age_days": 733,
                "timestamp": datetime(2025, 1, 2),
            },
            {
                "device_id": "wh-456",
                "temperature": 138,
                "pressure": 50,
                "age_days": 365,
                "timestamp": datetime(2025, 1, 3),
            },
            {
                "device_id": "wh-456",
                "temperature": 139,
                "pressure": 51,
                "age_days": 366,
                "timestamp": datetime(2025, 1, 4),
            },
        ]

    def test_init(self):
        """Test that the feature store initializes correctly."""
        assert self.feature_store.db == self.db_mock
        assert hasattr(self.feature_store, "feature_transformers")

    def test_get_training_dataset_simple(self):
        """Test retrieving a simple training dataset with basic features."""
        # Arrange
        feature_names = ["temperature", "pressure", "age_days"]
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 5)

        # Mock the database response
        self.db_mock.execute.return_value = self.mock_raw_data

        # Act
        result = self.feature_store.get_training_dataset(
            feature_names=feature_names, start_date=start_date, end_date=end_date
        )

        # Assert
        assert len(result) == 4
        assert all(feature in result[0] for feature in feature_names)
        self.db_mock.execute.assert_called_once()

    def test_get_training_dataset_with_filtering(self):
        """Test retrieving training data with date filtering."""
        # Arrange
        feature_names = ["temperature", "pressure"]
        start_date = datetime(2025, 1, 2)  # Should exclude first record
        end_date = datetime(2025, 1, 3)  # Should exclude last record

        # Mock the database response with pre-filtered data
        filtered_data = [
            rec
            for rec in self.mock_raw_data
            if start_date <= rec["timestamp"] <= end_date
        ]
        self.db_mock.execute.return_value = filtered_data

        # Act
        result = self.feature_store.get_training_dataset(
            feature_names=feature_names, start_date=start_date, end_date=end_date
        )

        # Assert
        assert len(result) == 2
        assert all(feature in result[0] for feature in feature_names)

    def test_get_training_dataset_with_derived_features(self):
        """Test retrieving training data with derived features."""
        # Arrange
        feature_names = ["temperature", "pressure", "temperature_pressure_ratio"]
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 5)

        # Mock the database response
        self.db_mock.execute.return_value = self.mock_raw_data

        # Act
        result = self.feature_store.get_training_dataset(
            feature_names=feature_names,
            start_date=start_date,
            end_date=end_date,
            derive_features=True,
        )

        # Assert
        assert len(result) == 4
        assert all(feature in result[0] for feature in feature_names)
        assert (
            abs(
                result[0]["temperature_pressure_ratio"]
                - (result[0]["temperature"] / result[0]["pressure"])
            )
            < 0.001
        )
