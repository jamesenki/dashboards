"""
Integration tests for the Water Heater API to Use Case layer.

These tests validate the integration between the Water Heater API controllers and
the Use Case layer following Clean Architecture principles. Tests are tagged with
their TDD phase to clearly indicate their purpose in the development cycle.
"""
import os
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.domain.entities.water_heater import WaterHeater
from src.domain.value_objects.temperature import Temperature
from src.main import app
from src.models.device import DeviceStatus, DeviceType
from src.models.water_heater import WaterHeaterMode, WaterHeaterStatus
from src.use_cases.water_heater_service import WaterHeaterService

# Create a test client
client = TestClient(app)


@pytest.fixture
def test_water_heater_data():
    """Generate test data for a water heater.

    This follows Clean Architecture by creating data that matches our domain model,
    not just the API payload structure.
    """
    # Generate a unique identifier for this test run
    test_id = uuid.uuid4().hex[:8]

    return {
        # Required Device base class fields
        "id": f"wh-test-{test_id}",
        "name": f"Test Water Heater {test_id}",
        "model": "Test-WH-1000",
        "manufacturer": "TestCorp",
        "type": DeviceType.WATER_HEATER.value,
        "status": DeviceStatus.ONLINE.value,
        # Required WaterHeater-specific fields
        "target_temperature": 55.0,
        "current_temperature": 52.0,
        "min_temperature": 40.0,
        "max_temperature": 85.0,
        "heater_status": WaterHeaterStatus.STANDBY.value,
        "mode": WaterHeaterMode.ECO.value,
        "health_status": "GREEN",
        # Additional metadata
        "location": "Test Location",
        "description": f"Test water heater created for API testing {test_id}",
    }


@pytest.fixture
def mock_water_heater_service():
    """Create a mock water heater service for testing.

    This follows Clean Architecture by properly mocking the Use Case layer
    to isolate the API layer for testing.
    """
    mock = MagicMock(spec=WaterHeaterService)

    # We'll configure specific method returns in each test
    return mock


@pytest.fixture
def mock_get_service(mock_water_heater_service):
    """Patch the service factory to return our mock.

    This ensures the API layer uses our test double instead of
    creating a real service instance.
    """
    with patch(
        "src.api.water_heater.get_water_heater_service",
        return_value=mock_water_heater_service,
    ):
        yield


class TestWaterHeaterAPIToUseCase:
    """Integration tests for the Water Heater API to Use Case boundary.

    These tests validate that:
    1. The API correctly translates HTTP requests to use case method calls
    2. The API properly handles responses from the use case layer
    3. The API correctly enforces input validation before calling use cases

    Following Clean Architecture principles, we isolate the API layer from
    the actual use case implementation.
    """

    @pytest.mark.green
    def test_get_water_heaters(
        self,
        client,
        mock_get_service,
        mock_water_heater_service,
        test_water_heater_data,
    ):
        """Test getting all water heaters through the API.

        RED phase: This test defines the expected behavior for retrieving the water heater list.

        Business value: Enables facility managers to view all water heaters in the system.
        """
        # Setup - configure mock to return test data
        test_heater = WaterHeater(
            id=test_water_heater_data["id"],
            name=test_water_heater_data["name"],
            manufacturer=test_water_heater_data["manufacturer"],
            model=test_water_heater_data["model"],
            current_temperature=Temperature(
                value=test_water_heater_data["current_temperature"], unit="C"
            ),
            target_temperature=Temperature(
                value=test_water_heater_data["target_temperature"], unit="C"
            ),
            status=DeviceStatus(test_water_heater_data["status"]),
            is_simulated=False,
            last_updated=datetime.now(),
        )
        mock_water_heater_service.get_all_water_heaters.return_value = [test_heater]

        # Execute - API call to controller
        response = client.get("/api/water-heaters")

        # Verify - Response format and status code
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Verify first water heater has expected structure
        first_heater = data[0]
        assert "id" in first_heater
        assert "name" in first_heater
        assert "manufacturer" in first_heater
        assert "current_temperature" in first_heater
        assert "target_temperature" in first_heater

        # Verify - Use case method was called correctly
        mock_water_heater_service.get_all_water_heaters.assert_called_once()

    @pytest.mark.green
    def test_get_water_heater_by_id(
        self,
        client,
        mock_get_service,
        mock_water_heater_service,
        test_water_heater_data,
    ):
        """Test getting a specific water heater by ID.

        RED phase: This test defines the expected behavior for retrieving a specific water heater.

        Business value: Enables facility managers to view detailed information about a specific device.
        """
        # Setup - configure mock to return test data
        heater_id = test_water_heater_data["id"]
        test_heater = WaterHeater(
            id=heater_id,
            name=test_water_heater_data["name"],
            manufacturer=test_water_heater_data["manufacturer"],
            model=test_water_heater_data["model"],
            current_temperature=Temperature(
                value=test_water_heater_data["current_temperature"], unit="C"
            ),
            target_temperature=Temperature(
                value=test_water_heater_data["target_temperature"], unit="C"
            ),
            status=DeviceStatus(test_water_heater_data["status"]),
            is_simulated=False,
            last_updated=datetime.now(),
        )
        mock_water_heater_service.get_water_heater_by_id.return_value = test_heater

        # Execute - API call to controller
        response = client.get(f"/api/water-heaters/{heater_id}")

        # Verify - Response format and status code
        assert response.status_code == 200
        heater = response.json()
        assert heater["id"] == heater_id
        assert heater["name"] == test_water_heater_data["name"]
        assert heater["manufacturer"] == test_water_heater_data["manufacturer"]

        # Verify - Use case method was called correctly
        mock_water_heater_service.get_water_heater_by_id.assert_called_once_with(
            heater_id
        )

    @pytest.mark.green
    def test_get_non_existent_water_heater(
        self, client, mock_get_service, mock_water_heater_service
    ):
        """Test getting a water heater with a non-existent ID.

        RED phase: This test defines the expected error handling behavior.

        Business value: Provides clear error messages when accessing non-existent resources.
        """
        # Setup - configure mock to raise exception
        non_existent_id = "non-existent-id"
        mock_water_heater_service.get_water_heater_by_id.side_effect = ValueError(
            f"Water heater with ID {non_existent_id} not found"
        )

        # Execute - API call to controller
        response = client.get(f"/api/water-heaters/{non_existent_id}")

        # Verify - Error response and status code
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

        # Verify - Use case method was called correctly
        mock_water_heater_service.get_water_heater_by_id.assert_called_once_with(
            non_existent_id
        )

    @pytest.mark.green
    def test_create_water_heater(
        self,
        client,
        mock_get_service,
        mock_water_heater_service,
        test_water_heater_data,
    ):
        """Test creating a new water heater.

        RED phase: This test defines the expected behavior for creating a water heater.

        Business value: Allows facility managers to add new devices to the system.
        """
        # Setup - configure mock to return the created water heater
        heater_id = test_water_heater_data["id"]
        test_heater = WaterHeater(
            id=heater_id,
            name=test_water_heater_data["name"],
            manufacturer=test_water_heater_data["manufacturer"],
            model=test_water_heater_data["model"],
            current_temperature=Temperature(
                value=test_water_heater_data["current_temperature"], unit="C"
            ),
            target_temperature=Temperature(
                value=test_water_heater_data["target_temperature"], unit="C"
            ),
            status=DeviceStatus(test_water_heater_data["status"]),
            is_simulated=False,
            last_updated=datetime.now(),
        )
        mock_water_heater_service.create_water_heater.return_value = test_heater

        # Execute - API call to controller
        response = client.post("/api/water-heaters", json=test_water_heater_data)

        # Verify - Response format and status code
        assert response.status_code == 201
        created_heater = response.json()
        assert created_heater["id"] == heater_id
        assert created_heater["name"] == test_water_heater_data["name"]

        # Verify - Use case method was called correctly
        mock_water_heater_service.create_water_heater.assert_called_once()

    @pytest.mark.green
    def test_update_water_heater_temperature(
        self,
        client,
        mock_get_service,
        mock_water_heater_service,
        test_water_heater_data,
    ):
        """Test updating a water heater's target temperature.

        RED phase: This test defines the expected behavior for updating the temperature.

        Business value: Enables facility managers to control water temperature remotely.
        """
        # Setup - prepare test data and mock response
        heater_id = test_water_heater_data["id"]
        new_temperature = 60.0
        update_data = {"target_temperature": new_temperature}

        test_heater = WaterHeater(
            id=heater_id,
            name=test_water_heater_data["name"],
            manufacturer=test_water_heater_data["manufacturer"],
            model=test_water_heater_data["model"],
            current_temperature=Temperature(
                value=test_water_heater_data["current_temperature"], unit="C"
            ),
            target_temperature=Temperature(
                value=new_temperature, unit="C"
            ),  # Updated temperature
            status=DeviceStatus(test_water_heater_data["status"]),
            is_simulated=False,
            last_updated=datetime.now(),
        )
        mock_water_heater_service.update_target_temperature.return_value = test_heater

        # Execute - API call to controller
        response = client.patch(
            f"/api/water-heaters/{heater_id}/temperature", json=update_data
        )

        # Verify - Response format and status code
        assert response.status_code == 200
        updated_heater = response.json()
        assert updated_heater["id"] == heater_id
        assert updated_heater["target_temperature"] == new_temperature

        # Verify - Use case method was called correctly
        mock_water_heater_service.update_target_temperature.assert_called_once_with(
            heater_id, Temperature(value=new_temperature, unit="C")
        )

    @pytest.mark.green
    def test_update_water_heater_mode(
        self,
        client,
        mock_get_service,
        mock_water_heater_service,
        test_water_heater_data,
    ):
        """Test updating a water heater's operating mode.

        RED phase: This test defines the expected behavior for changing operating modes.

        Business value: Enables facility managers to switch between energy-saving and
        performance modes based on needs.
        """
        # Setup - prepare test data and mock response
        heater_id = test_water_heater_data["id"]
        new_mode = WaterHeaterMode.PERFORMANCE.value
        update_data = {"mode": new_mode}

        test_heater = WaterHeater(
            id=heater_id,
            name=test_water_heater_data["name"],
            manufacturer=test_water_heater_data["manufacturer"],
            model=test_water_heater_data["model"],
            current_temperature=Temperature(
                value=test_water_heater_data["current_temperature"], unit="C"
            ),
            target_temperature=Temperature(
                value=test_water_heater_data["target_temperature"], unit="C"
            ),
            status=DeviceStatus(test_water_heater_data["status"]),
            is_simulated=False,
            last_updated=datetime.now(),
            mode=WaterHeaterMode(new_mode),  # Updated mode
        )
        mock_water_heater_service.update_operating_mode.return_value = test_heater

        # Execute - API call to controller
        response = client.patch(
            f"/api/water-heaters/{heater_id}/mode", json=update_data
        )

        # Verify - Response format and status code
        assert response.status_code == 200
        updated_heater = response.json()
        assert updated_heater["id"] == heater_id
        assert updated_heater["mode"] == new_mode

        # Verify - Use case method was called correctly
        mock_water_heater_service.update_operating_mode.assert_called_once_with(
            heater_id, WaterHeaterMode(new_mode)
        )

    # Additional tests would be added for other API endpoints
    # Each test would follow the same pattern of:
    # 1. Setting up mock responses from the use case layer
    # 2. Making API calls to controllers
    # 3. Verifying response format and status codes
    # 4. Verifying the use case methods were called correctly with proper parameters

    # GREEN phase tests would be added here after implementation
    # They would have the @pytest.mark.green decorator

    # REFACTOR phase tests would be added after code improvements
    # They would have the @pytest.mark.refactor decorator
