import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.models.device import DeviceType, DeviceStatus
from src.models.water_heater import (
    WaterHeaterMode, 
    WaterHeaterStatus,
    WaterHeaterReading,
    WaterHeater
)


# Import the router and models from the correct locations
from src.api.water_heater import router
from src.models.water_heater import WaterHeater, WaterHeaterReading
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
        heater_status=WaterHeaterStatus.HEATING
    )


class TestWaterHeaterAPI:
    """Test cases for water heater API endpoints."""
    
    @patch('src.api.water_heater.router.service')
    def test_get_water_heaters(self, mock_service, client, sample_water_heater):
        """Test getting all water heaters."""
        # Mock the service method
        heaters = [
            sample_water_heater,
            WaterHeater(
                id="test-water-heater-2",
                name="Test Water Heater 2",
                type=DeviceType.WATER_HEATER,
                status=DeviceStatus.OFFLINE,
                target_temperature=55.0,
                current_temperature=38.0,
                mode=WaterHeaterMode.BOOST,
                heater_status=WaterHeaterStatus.STANDBY
            )
        ]
        mock_service.get_water_heaters = AsyncMock(return_value=heaters)
        
        # Make the request
        response = client.get("/api/water-heaters")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "test-water-heater-1"
        assert data[1]["id"] == "test-water-heater-2"
    
    @patch('src.api.water_heater.router.service')
    def test_get_water_heater(self, mock_service, client, sample_water_heater):
        """Test getting a specific water heater."""
        # Mock the service method
        mock_service.get_water_heater = AsyncMock(return_value=sample_water_heater)
        
        # Make the request
        response = client.get("/api/water-heaters/test-water-heater-1")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-water-heater-1"
        assert data["current_temperature"] == 45.5
        
        # Verify the service was called correctly
        mock_service.get_water_heater.assert_called_once_with("test-water-heater-1")
    
    @patch('src.api.water_heater.router.service')
    def test_get_water_heater_not_found(self, mock_service, client):
        """Test getting a non-existent water heater."""
        # Mock the service method
        mock_service.get_water_heater = AsyncMock(return_value=None)
        
        # Make the request
        response = client.get("/api/water-heaters/nonexistent-id")
        
        # Verify the response
        assert response.status_code == 404
        
        # Verify the service was called correctly
        mock_service.get_water_heater.assert_called_once_with("nonexistent-id")
    
    @patch('src.api.water_heater.router.service')
    def test_create_water_heater(self, mock_service, client, sample_water_heater):
        """Test creating a new water heater."""
        # Mock the service method to return the sample heater with an ID
        created_heater = sample_water_heater.model_copy(update={"id": str(uuid.uuid4())})
        mock_service.create_water_heater = AsyncMock(return_value=created_heater)
        
        # Create a payload for a new water heater
        # Generate a random ID for testing
        test_id = str(uuid.uuid4())
        payload = {
            "id": test_id,
            "name": "New Water Heater",
            "type": DeviceType.WATER_HEATER,
            "status": DeviceStatus.ONLINE,
            "target_temperature": 52.0,
            "current_temperature": 45.0,
            "mode": WaterHeaterMode.ECO,
            "heater_status": WaterHeaterStatus.STANDBY
        }
        
        # Make the request with valid data
        response = client.post("/api/water-heaters", json=payload)
        
        # If it fails, print the response for debugging
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        
        # Verify the service was called (we don't check exact parameters due to id generation)
        mock_service.create_water_heater.assert_called_once()
    
    @patch('src.api.water_heater.router.service')
    def test_update_target_temperature(self, mock_service, client, sample_water_heater):
        """Test updating a water heater's target temperature."""
        # Mock the service methods - only need to mock update_target_temperature since that's what's called directly
        updated_heater = sample_water_heater.model_copy(update={"target_temperature": 53.5})
        mock_service.update_target_temperature = AsyncMock(return_value=updated_heater)
        
        # Make the request
        payload = {"temperature": 53.5}
        response = client.patch("/api/water-heaters/test-water-heater-1/temperature", json=payload)
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["target_temperature"] == 53.5
        
        # Verify the service was called correctly
        mock_service.update_target_temperature.assert_called_once_with("test-water-heater-1", 53.5)
