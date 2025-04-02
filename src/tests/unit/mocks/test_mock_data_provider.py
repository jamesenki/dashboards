"""
Tests for the MockDataProvider.

Following TDD principles, these tests define the expected behavior
of the mock data provider before implementation.
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

from src.config.providers import DefaultProvider
from src.config.service import ConfigurationService
from src.mocks.mock_data_provider import MockDataProvider


class TestMockDataProvider:
    """Test suite for the MockDataProvider."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a mock configuration
        self.test_config = {
            "testing": {
                "mocks": {
                    "enabled": True,
                    "data_path": "./test_mocks",
                    "response_delay_ms": 0,
                }
            }
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

        # Create the provider with our test configuration
        with patch("src.mocks.mock_data_provider.config", self.config_service):
            self.provider = MockDataProvider()

    def teardown_method(self):
        """Clean up after each test method."""
        # Clean up the temporary directory
        self.temp_dir.cleanup()

    def _create_mock_data_files(self):
        """Create mock data files for testing."""
        # Create directories
        models_dir = self.mock_data_path / "models"
        devices_dir = self.mock_data_path / "devices"
        models_dir.mkdir(parents=True)
        devices_dir.mkdir(parents=True)

        # Create JSON mock data
        models_data = {
            "models": [
                {"id": "model1", "name": "Test Model 1", "version": "1.0.0"},
                {"id": "model2", "name": "Test Model 2", "version": "1.0.0"},
            ]
        }

        with open(models_dir / "models.json", "w") as f:
            json.dump(models_data, f)

        # Create YAML mock data
        devices_data = """
devices:
  - id: device1
    name: Test Device 1
    type: water_heater
  - id: device2
    name: Test Device 2
    type: vending_machine
"""

        with open(devices_dir / "devices.yaml", "w") as f:
            f.write(devices_data)

    def test_initialization(self):
        """Test that the provider initializes correctly."""
        assert self.provider.enabled is True
        assert self.provider.data_path == str(self.mock_data_path)
        assert self.provider.response_delay_ms == 0

    def test_load_json_data(self):
        """Test loading data from JSON files."""
        models_data = self.provider.get_mock_data("models/models")
        assert models_data is not None
        assert "models" in models_data
        assert len(models_data["models"]) == 2
        assert models_data["models"][0]["id"] == "model1"

    def test_load_yaml_data(self):
        """Test loading data from YAML files."""
        devices_data = self.provider.get_mock_data("devices/devices")
        assert devices_data is not None
        assert "devices" in devices_data
        assert len(devices_data["devices"]) == 2
        assert devices_data["devices"][0]["id"] == "device1"

    def test_get_nonexistent_data(self):
        """Test getting data for a nonexistent category."""
        data = self.provider.get_mock_data("nonexistent")
        assert data is None

        # Test with default value
        data = self.provider.get_mock_data("nonexistent", {"default": True})
        assert data == {"default": True}

    def test_register_mock_data(self):
        """Test registering mock data at runtime."""
        # Register new mock data
        test_data = {"test": True, "value": 42}
        self.provider.register_mock_data("runtime/test", test_data)

        # Retrieve the registered data
        retrieved_data = self.provider.get_mock_data("runtime/test")
        assert retrieved_data == test_data

    def test_clear_mock_data(self):
        """Test clearing mock data."""
        # Register some mock data
        self.provider.register_mock_data("test1", {"test": 1})
        self.provider.register_mock_data("test2", {"test": 2})

        # Clear specific category
        self.provider.clear_mock_data("test1")
        assert self.provider.get_mock_data("test1") is None
        assert self.provider.get_mock_data("test2") is not None

        # Clear all data
        self.provider.clear_mock_data()
        assert self.provider.get_mock_data("test2") is None

    def test_is_mock_data_available(self):
        """Test checking if mock data is available."""
        assert self.provider.is_mock_data_available("models/models") is True
        assert self.provider.is_mock_data_available("nonexistent") is False

    def test_is_enabled(self):
        """Test checking if mock data is enabled."""
        assert self.provider.is_enabled() is True

        # Test with mock data disabled
        disabled_config = {"testing": {"mocks": {"enabled": False}}}

        config_service = ConfigurationService()
        config_service.register_provider(DefaultProvider(disabled_config))

        with patch("src.mocks.mock_data_provider.config", config_service):
            provider = MockDataProvider()
            assert provider.is_enabled() is False

    def test_reload(self):
        """Test reloading mock data."""
        # Get initial data
        models_data = self.provider.get_mock_data("models/models")
        assert len(models_data["models"]) == 2

        # Modify the mock data file
        new_models_data = {
            "models": [
                {"id": "model1", "name": "Test Model 1", "version": "1.0.0"},
                {"id": "model2", "name": "Test Model 2", "version": "1.0.0"},
                {"id": "model3", "name": "Test Model 3", "version": "1.0.0"},
            ]
        }

        with open(self.mock_data_path / "models" / "models.json", "w") as f:
            json.dump(new_models_data, f)

        # Reload the data
        self.provider.reload()

        # Verify the reloaded data
        reloaded_data = self.provider.get_mock_data("models/models")
        assert len(reloaded_data["models"]) == 3
        assert reloaded_data["models"][2]["id"] == "model3"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
