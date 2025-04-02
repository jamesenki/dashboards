import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.api.water_heater.router as water_heater_router

# Import the router and models from the correct locations
from src.api.water_heater import router
from src.models.device import DeviceStatus, DeviceType
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterMode,
    WaterHeaterReading,
    WaterHeaterStatus,
)
from src.services.water_heater import WaterHeaterService


@pytest.fixture
def app():
    """Create a FastAPI test application."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return TestClient(app)


@pytest.fixture
def sample_water_heater():
    """Create a sample water heater for testing."""
    return WaterHeater(
        id="test-water-heater-1",
        name="Test Water Heater",
        type=DeviceType.WATER_HEATER,
        status=DeviceStatus.ONLINE,
        target_temperature=50.0,
        current_temperature=45.5,
        mode=WaterHeaterMode.ECO,
        heater_status=WaterHeaterStatus.HEATING,
    )


@pytest.fixture
def sample_reading():
    """Create a sample water heater reading for testing."""
    return WaterHeaterReading(
        timestamp=datetime.now(),
        temperature=48.5,
        pressure=2.2,
        energy_usage=120.5,
        flow_rate=5.5,
    )


class TestWaterHeaterAPIExpanded:
    """Expanded test cases for water heater API endpoints."""

    @patch("src.api.water_heater.router.service")
    def test_update_mode(self, mock_service, client, sample_water_heater):
        """Test updating a water heater's operational mode."""
        # Mock the service methods
        mock_service.get_water_heater = AsyncMock(return_value=sample_water_heater)
        updated_heater = sample_water_heater.model_copy(
            update={"mode": WaterHeaterMode.BOOST}
        )
        mock_service.update_mode = AsyncMock(return_value=updated_heater)

        # Make the request
        payload = {"mode": WaterHeaterMode.BOOST}
        response = client.patch(
            "/api/water-heaters/test-water-heater-1/mode", json=payload
        )

        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == WaterHeaterMode.BOOST

        # Verify the service was called correctly
        mock_service.update_mode.assert_called_once_with(
            "test-water-heater-1", WaterHeaterMode.BOOST
        )

    @patch("src.api.water_heater.router.service")
    def test_add_temperature_reading(
        self, mock_service, client, sample_water_heater, sample_reading
    ):
        """Test adding a temperature reading to a water heater."""
        # Mock the service methods
        mock_service.get_water_heater = AsyncMock(return_value=sample_water_heater)
        updated_heater = sample_water_heater.model_copy(
            update={"current_temperature": 48.5, "readings": [sample_reading]}
        )
        mock_service.add_temperature_reading = AsyncMock(return_value=updated_heater)

        # Make the request
        payload = {
            "temperature": 48.5,
            "pressure": 2.2,
            "energy_usage": 120.5,
            "flow_rate": 5.5,
        }
        response = client.post(
            "/api/water-heaters/test-water-heater-1/readings", json=payload
        )

        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["current_temperature"] == 48.5

        # Verify the service was called correctly
        mock_service.add_temperature_reading.assert_called_once()
        # Verify parameters were passed correctly - they are positional, not keyword arguments
        call_args = mock_service.add_temperature_reading.call_args[0]
        assert len(call_args) >= 2  # At least device_id and temperature
        assert call_args[0] == "test-water-heater-1"  # First arg is device_id
        assert call_args[1] == 48.5  # Second arg is temperature

    @patch("src.api.water_heater.router.service")
    def test_get_water_heater_with_readings(
        self, mock_service, client, sample_water_heater, sample_reading
    ):
        """Test getting a water heater that has readings."""
        # Create a water heater with readings
        water_heater_with_readings = sample_water_heater.model_copy()
        water_heater_with_readings.readings = [sample_reading]

        # Mock the service method
        mock_service.get_water_heater = AsyncMock(
            return_value=water_heater_with_readings
        )

        # Make the request to get the water heater
        response = client.get("/api/water-heaters/test-water-heater-1")

        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-water-heater-1"
        assert "readings" in data
        assert len(data["readings"]) == 1
        assert data["readings"][0]["temperature"] == 48.5

    @patch("src.api.water_heater.router.service")
    def test_error_handling_invalid_input(self, mock_service, client):
        """Test API error handling with invalid input data."""
        # Try to create a water heater with invalid data
        payload = {
            "name": "Invalid Heater",
            "target_temperature": "not-a-number",  # Should be a float
            "mode": "invalid-mode",  # Not a valid enum value
        }

        # Make the request
        response = client.post("/api/water-heaters", json=payload)

        # Verify the response is an error
        assert response.status_code == 422  # Unprocessable Entity

        # Check that the error details are informative
        error_data = response.json()
        assert "detail" in error_data
        # The error should mention the validation issues
        errors = error_data["detail"]
        assert isinstance(errors, list)

        # Verify service was not called due to validation failure
        mock_service.create_water_heater.assert_not_called()

    # This test is skipped because the delete endpoint doesn't exist in the current router
    # Let's create a test for another aspect of the water heater API instead
    @patch("src.api.water_heater.router.service")
    def test_invalid_temperature_update(
        self, mock_service, client, sample_water_heater
    ):
        """Test updating a water heater with an invalid temperature."""
        # Mock the service to raise an error
        mock_service.get_water_heater = AsyncMock(return_value=sample_water_heater)
        mock_service.update_target_temperature = AsyncMock(
            side_effect=ValueError("Temperature out of range")
        )

        # Make the request with an invalid temperature
        payload = {"temperature": 1000.0}  # Clearly out of range
        response = client.patch(
            "/api/water-heaters/test-water-heater-1/temperature", json=payload
        )

        # Verify the response indicates an error
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Temperature out of range" in data["detail"]

        # Verify the service was called
        mock_service.update_target_temperature.assert_called_once()
