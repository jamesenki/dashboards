"""
Tests for the DataAccessLayer.

Following TDD principles, these tests define the expected behavior
of the data access layer before implementation.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.api.data_access import DataAccessLayer
from src.config.providers import DefaultProvider
from src.config.service import ConfigurationService
from src.mocks.mock_data_provider import MockDataProvider


class TestDataAccessLayer:
    """Test suite for the DataAccessLayer."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a mock configuration
        self.test_config = {
            "testing": {"mocks": {"enabled": True, "data_path": "./test_mocks"}}
        }

        # Create a test configuration service
        self.config_service = ConfigurationService()
        self.config_service.register_provider(DefaultProvider(self.test_config))

        # Create a temporary directory for mock data
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mock_data_path = Path(self.temp_dir.name)

        # Override the data path in the configuration
        self.test_config["testing"]["mocks"]["data_path"] = str(self.mock_data_path)

        # Create mock data files
        self._create_mock_data_files()

        # Create a mock MockDataProvider
        self.mock_provider = MagicMock()
        self.mock_provider.is_mock_data_available.return_value = True
        self.mock_provider.get_mock_data.side_effect = self._mock_get_data

        # Create the data access layer with our test configuration and mock provider
        with patch("src.api.data_access.config", self.config_service), patch(
            "src.api.data_access.mock_data_provider", self.mock_provider
        ):
            self.data_access = DataAccessLayer()

    def teardown_method(self):
        """Clean up after each test method."""
        # Clean up the temporary directory
        self.temp_dir.cleanup()

    def _create_mock_data_files(self):
        """Create mock data files for testing."""
        # Create directories
        models_dir = self.mock_data_path / "models"
        devices_dir = self.mock_data_path / "devices"
        metrics_dir = self.mock_data_path / "metrics"
        models_dir.mkdir(parents=True)
        devices_dir.mkdir(parents=True)
        metrics_dir.mkdir(parents=True)

        # Create models mock data
        self.models_data = {
            "models": [
                {
                    "id": "model1",
                    "name": "Test Model 1",
                    "version": "1.0.0",
                    "metrics": {"accuracy": 0.92, "drift_score": 0.03},
                },
                {
                    "id": "model2",
                    "name": "Test Model 2",
                    "version": "1.1.0",
                    "metrics": {"accuracy": 0.88, "drift_score": 0.05},
                },
            ]
        }

        with open(models_dir / "models.json", "w") as f:
            json.dump(self.models_data, f)

        # Create devices mock data
        self.devices_data = {
            "devices": [
                {"id": "device1", "name": "Test Device 1", "type": "water_heater"},
                {"id": "device2", "name": "Test Device 2", "type": "vending_machine"},
                {"id": "device3", "name": "Test Device 3", "type": "water_heater"},
            ]
        }

        with open(devices_dir / "devices.json", "w") as f:
            json.dump(self.devices_data, f)

        # Create water heaters mock data
        self.water_heaters_data = {
            "devices": [
                {
                    "id": "wh1",
                    "name": "Water Heater 1",
                    "type": "water_heater",
                    "temperature": 140,
                },
                {
                    "id": "wh2",
                    "name": "Water Heater 2",
                    "type": "water_heater",
                    "temperature": 135,
                },
            ]
        }

        with open(devices_dir / "water_heaters.json", "w") as f:
            json.dump(self.water_heaters_data, f)

        # Create metrics mock data
        self.metrics_data = {
            "metrics": {
                "model1": {
                    "metrics_history": [
                        {
                            "timestamp": "2025-04-01T00:00:00Z",
                            "metrics": {"accuracy": 0.92, "precision": 0.90},
                        }
                    ]
                }
            },
            "alerts": [
                {"id": "alert1", "model_id": "model1", "message": "Test Alert 1"},
                {"id": "alert2", "model_id": "model2", "message": "Test Alert 2"},
            ],
        }

        with open(metrics_dir / "model_metrics.json", "w") as f:
            json.dump(self.metrics_data, f)

    def _mock_get_data(self, category, default=None):
        """Mock implementation of get_mock_data."""
        if category == "models/models":
            return self.models_data
        elif category == "devices/devices":
            return self.devices_data
        elif category == "devices/water_heaters":
            return self.water_heaters_data
        elif category == "metrics/model_metrics":
            return self.metrics_data
        return default

    def test_initialization(self):
        """Test that the data access layer initializes correctly."""
        assert self.data_access.use_mocks is True

    def test_get_models(self):
        """Test getting all models."""
        models = self.data_access.get_models()
        assert len(models) == 2
        assert models[0]["id"] == "model1"
        assert models[1]["id"] == "model2"

        # Verify the mock provider was called correctly
        self.mock_provider.is_mock_data_available.assert_called_with("models/models")
        self.mock_provider.get_mock_data.assert_called_with("models/models")

    def test_get_model_by_id(self):
        """Test getting a model by ID."""
        model = self.data_access.get_model_by_id("model1")
        assert model is not None
        assert model["id"] == "model1"
        assert model["name"] == "Test Model 1"

        # Test getting a nonexistent model
        nonexistent_model = self.data_access.get_model_by_id("nonexistent")
        assert nonexistent_model is None

    def test_get_devices(self):
        """Test getting all devices."""
        devices = self.data_access.get_devices()
        assert len(devices) == 3

        # Test filtering by device type
        water_heaters = self.data_access.get_devices(device_type="water_heater")
        assert len(water_heaters) == 2
        assert all(device["type"] == "water_heater" for device in water_heaters)

    def test_get_devices_with_specific_type(self):
        """Test getting devices with a specific type."""
        # Set up the mock to return water heaters data for water_heaters category
        self.mock_provider.is_mock_data_available.side_effect = (
            lambda x: x == "devices/water_heaters"
        )

        water_heaters = self.data_access.get_devices(device_type="water_heater")
        assert len(water_heaters) == 2
        assert water_heaters[0]["id"] == "wh1"
        assert water_heaters[1]["id"] == "wh2"

        # Verify the mock provider was called correctly
        self.mock_provider.is_mock_data_available.assert_called_with(
            "devices/water_heaters"
        )
        self.mock_provider.get_mock_data.assert_called_with("devices/water_heaters")

    def test_get_device_by_id(self):
        """Test getting a device by ID."""
        device = self.data_access.get_device_by_id("device1")
        assert device is not None
        assert device["id"] == "device1"
        assert device["name"] == "Test Device 1"

        # Test getting a nonexistent device
        nonexistent_device = self.data_access.get_device_by_id("nonexistent")
        assert nonexistent_device is None

    def test_get_model_metrics(self):
        """Test getting metrics for a specific model."""
        metrics = self.data_access.get_model_metrics("model1")
        assert metrics is not None
        assert "metrics_history" in metrics
        assert len(metrics["metrics_history"]) == 1

        # Test getting metrics for a nonexistent model
        nonexistent_metrics = self.data_access.get_model_metrics("nonexistent")
        assert nonexistent_metrics == {}

    def test_get_model_alerts(self):
        """Test getting alerts for models."""
        # Test getting all alerts
        all_alerts = self.data_access.get_model_alerts()
        assert len(all_alerts) == 2

        # Test getting alerts for a specific model
        model1_alerts = self.data_access.get_model_alerts(model_id="model1")
        assert len(model1_alerts) == 1
        assert model1_alerts[0]["id"] == "alert1"

        # Test getting alerts for a model with no alerts
        nonexistent_alerts = self.data_access.get_model_alerts(model_id="nonexistent")
        assert len(nonexistent_alerts) == 0

    def test_without_mocks(self):
        """Test behavior when mocks are disabled."""
        # Create a configuration with mocks disabled
        no_mocks_config = {"testing": {"mocks": {"enabled": False}}}

        # Create a test configuration service
        config_service = ConfigurationService()
        config_service.register_provider(DefaultProvider(no_mocks_config))

        # Create the data access layer with mocks disabled
        with patch("src.api.data_access.config", config_service):
            data_access = DataAccessLayer()

            # Verify mocks are disabled
            assert data_access.use_mocks is False

            # Test that get_models returns an empty list when mocks are disabled
            models = data_access.get_models()
            assert models == []


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
