"""
Integration tests for the AI Agent's water heater tools following TDD principles.

These tests validate the integration between the AI Agent tools (use cases) and
the gateway interfaces following Clean Architecture principles. Tests are tagged
with their TDD phase to clearly indicate their purpose in the development cycle.

Business Value: These tests ensure that AI agent tools correctly interact with
water heater services, enabling reliable automated assistance for facility managers.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from src.ai.agent.tools.water_heater_tools import (
    get_water_heater_info,
    get_water_heater_list,
    get_water_heater_maintenance_info,
    get_water_heater_telemetry,
    set_water_heater_mode,
    set_water_heater_temperature,
)
from src.domain.entities.water_heater import WaterHeater
from src.domain.value_objects.device_status import DeviceStatus
from src.domain.value_objects.maintenance_status import MaintenanceStatus
from src.domain.value_objects.temperature import Temperature
from src.domain.value_objects.water_heater_mode import WaterHeaterMode
from src.use_cases.maintenance_service import MaintenanceService
from src.use_cases.telemetry_service import TelemetryService
from src.use_cases.water_heater_service import WaterHeaterService


@pytest.fixture
def mock_water_heater_service():
    """Create a mock water heater service for testing.

    This follows Clean Architecture by properly mocking the service layer
    that the AI agent tools depend on.
    """
    mock = MagicMock(spec=WaterHeaterService)
    return mock


@pytest.fixture
def mock_maintenance_service():
    """Create a mock maintenance service for testing."""
    mock = MagicMock(spec=MaintenanceService)
    return mock


@pytest.fixture
def mock_telemetry_service():
    """Create a mock telemetry service for testing."""
    mock = MagicMock(spec=TelemetryService)
    return mock


@pytest.fixture
def sample_water_heater():
    """Generate sample water heater data for testing."""
    return WaterHeater(
        id="wh-test-123",
        name="Test Water Heater",
        manufacturer="TestCorp",
        model="WH-1000",
        current_temperature=Temperature(value=52.0, unit="C"),
        target_temperature=Temperature(value=55.0, unit="C"),
        min_temperature=Temperature(value=40.0, unit="C"),
        max_temperature=Temperature(value=85.0, unit="C"),
        status=DeviceStatus("ONLINE"),
        mode=WaterHeaterMode("ECO"),
        health_status=MaintenanceStatus("GREEN"),
        location="Building A, Floor 2",
        is_simulated=False,
    )


@pytest.fixture
def sample_telemetry_data():
    """Generate sample telemetry data for testing."""
    return [
        {
            "timestamp": "2025-04-08T14:30:00Z",
            "temperature": 52.0,
            "power_consumption": 1.2,
            "water_flow_rate": 0.0,
        },
        {
            "timestamp": "2025-04-08T14:35:00Z",
            "temperature": 53.5,
            "power_consumption": 2.5,
            "water_flow_rate": 0.2,
        },
        {
            "timestamp": "2025-04-08T14:40:00Z",
            "temperature": 54.8,
            "power_consumption": 1.8,
            "water_flow_rate": 0.0,
        },
    ]


class TestWaterHeaterToolsToGateway:
    """Integration tests for the Water Heater AI Agent tools to repository gateway boundary.

    These tests validate that:
    1. AI tools correctly call the appropriate service methods
    2. AI tools properly format the data returned from services
    3. AI tools handle errors from services appropriately

    Following Clean Architecture principles, we test the boundary between
    the AI tools (use cases) and the gateway interfaces they depend on.
    """

    @pytest.mark.green
    def test_get_water_heater_list(
        self, mock_water_heater_service, sample_water_heater
    ):
        """Test getting a list of water heaters through the AI tool.

        RED phase: This test defines the expected behavior for the water heater listing tool.

        Business value: Enables the AI assistant to provide facility managers
        with a list of available devices.
        """
        # Setup - Configure mock service to return sample data
        mock_water_heater_service.get_all_water_heaters.return_value = [
            sample_water_heater
        ]

        # Execute - Call the AI tool with the mocked service
        with patch(
            "src.ai.agent.tools.water_heater_tools.get_water_heater_service",
            return_value=mock_water_heater_service,
        ):
            result = get_water_heater_list()

        # Verify - Result format and content
        parsed_result = json.loads(result)
        assert isinstance(parsed_result, list)
        assert len(parsed_result) > 0

        # Verify first water heater has expected structure
        first_heater = parsed_result[0]
        assert "id" in first_heater
        assert "name" in first_heater
        assert "manufacturer" in first_heater
        assert "current_temperature" in first_heater

        # Verify - Service method was called correctly
        mock_water_heater_service.get_all_water_heaters.assert_called_once()

    @pytest.mark.green
    def test_get_water_heater_info(
        self, mock_water_heater_service, sample_water_heater
    ):
        """Test getting detailed information about a water heater through the AI tool.

        RED phase: This test defines the expected behavior for the water heater info tool.

        Business value: Enables the AI assistant to provide facility managers with
        detailed information about specific devices.
        """
        # Setup - Configure mock service to return sample data
        heater_id = sample_water_heater.id
        mock_water_heater_service.get_water_heater_by_id.return_value = (
            sample_water_heater
        )

        # Execute - Call the AI tool with the mocked service
        with patch(
            "src.ai.agent.tools.water_heater_tools.get_water_heater_service",
            return_value=mock_water_heater_service,
        ):
            result = get_water_heater_info(heater_id)

        # Verify - Result format and content
        parsed_result = json.loads(result)
        assert parsed_result["id"] == heater_id
        assert parsed_result["name"] == sample_water_heater.name
        assert (
            parsed_result["current_temperature"]
            == sample_water_heater.current_temperature.value
        )
        assert (
            parsed_result["target_temperature"]
            == sample_water_heater.target_temperature.value
        )
        assert parsed_result["mode"] == sample_water_heater.mode.value

        # Verify - Service method was called correctly
        mock_water_heater_service.get_water_heater_by_id.assert_called_once_with(
            heater_id
        )

    @pytest.mark.green
    def test_get_water_heater_info_not_found(self, mock_water_heater_service):
        """Test getting information for a non-existent water heater.

        RED phase: This test defines the expected error handling behavior.

        Business value: Ensures the AI assistant provides clear error messages
        when asked about non-existent devices.
        """
        # Setup - Configure mock service to raise exception
        non_existent_id = "non-existent-id"
        mock_water_heater_service.get_water_heater_by_id.side_effect = ValueError(
            f"Water heater with ID {non_existent_id} not found"
        )

        # Execute - Call the AI tool with the mocked service
        with patch(
            "src.ai.agent.tools.water_heater_tools.get_water_heater_service",
            return_value=mock_water_heater_service,
        ):
            result = get_water_heater_info(non_existent_id)

        # Verify - Result contains error information
        parsed_result = json.loads(result)
        assert "error" in parsed_result
        assert "not found" in parsed_result["error"].lower()

        # Verify - Service method was called correctly
        mock_water_heater_service.get_water_heater_by_id.assert_called_once_with(
            non_existent_id
        )

    @pytest.mark.green
    def test_set_water_heater_temperature(
        self, mock_water_heater_service, sample_water_heater
    ):
        """Test setting a water heater's temperature through the AI tool.

        RED phase: This test defines the expected behavior for the temperature setting tool.

        Business value: Enables the AI assistant to help facility managers
        remotely control water heater temperatures.
        """
        # Setup - Configure mock service
        heater_id = sample_water_heater.id
        new_temp = 58.0

        # Clone the sample heater but with updated temperature
        updated_heater = WaterHeater(
            id=sample_water_heater.id,
            name=sample_water_heater.name,
            manufacturer=sample_water_heater.manufacturer,
            model=sample_water_heater.model,
            current_temperature=sample_water_heater.current_temperature,
            target_temperature=Temperature(value=new_temp, unit="C"),  # Updated
            min_temperature=sample_water_heater.min_temperature,
            max_temperature=sample_water_heater.max_temperature,
            status=sample_water_heater.status,
            mode=sample_water_heater.mode,
            health_status=sample_water_heater.health_status,
            location=sample_water_heater.location,
            is_simulated=sample_water_heater.is_simulated,
        )

        mock_water_heater_service.get_water_heater_by_id.return_value = (
            sample_water_heater
        )
        mock_water_heater_service.update_target_temperature.return_value = (
            updated_heater
        )

        # Execute - Call the AI tool with the mocked service
        with patch(
            "src.ai.agent.tools.water_heater_tools.get_water_heater_service",
            return_value=mock_water_heater_service,
        ):
            result = set_water_heater_temperature(heater_id, new_temp)

        # Verify - Result format and content
        parsed_result = json.loads(result)
        assert parsed_result["id"] == heater_id
        assert parsed_result["target_temperature"] == new_temp
        assert "success" in parsed_result
        assert parsed_result["success"] is True

        # Verify - Service methods were called correctly
        mock_water_heater_service.get_water_heater_by_id.assert_called_once_with(
            heater_id
        )
        mock_water_heater_service.update_target_temperature.assert_called_once()

    @pytest.mark.green
    def test_set_water_heater_mode(
        self, mock_water_heater_service, sample_water_heater
    ):
        """Test setting a water heater's operating mode through the AI tool.

        RED phase: This test defines the expected behavior for the mode setting tool.

        Business value: Enables the AI assistant to help facility managers
        switch between energy-saving and performance modes.
        """
        # Setup - Configure mock service
        heater_id = sample_water_heater.id
        new_mode = "PERFORMANCE"

        # Clone the sample heater but with updated mode
        updated_heater = WaterHeater(
            id=sample_water_heater.id,
            name=sample_water_heater.name,
            manufacturer=sample_water_heater.manufacturer,
            model=sample_water_heater.model,
            current_temperature=sample_water_heater.current_temperature,
            target_temperature=sample_water_heater.target_temperature,
            min_temperature=sample_water_heater.min_temperature,
            max_temperature=sample_water_heater.max_temperature,
            status=sample_water_heater.status,
            mode=WaterHeaterMode(new_mode),  # Updated
            health_status=sample_water_heater.health_status,
            location=sample_water_heater.location,
            is_simulated=sample_water_heater.is_simulated,
        )

        mock_water_heater_service.get_water_heater_by_id.return_value = (
            sample_water_heater
        )
        mock_water_heater_service.update_operating_mode.return_value = updated_heater

        # Execute - Call the AI tool with the mocked service
        with patch(
            "src.ai.agent.tools.water_heater_tools.get_water_heater_service",
            return_value=mock_water_heater_service,
        ):
            result = set_water_heater_mode(heater_id, new_mode)

        # Verify - Result format and content
        parsed_result = json.loads(result)
        assert parsed_result["id"] == heater_id
        assert parsed_result["mode"] == new_mode
        assert "success" in parsed_result
        assert parsed_result["success"] is True

        # Verify - Service methods were called correctly
        mock_water_heater_service.get_water_heater_by_id.assert_called_once_with(
            heater_id
        )
        mock_water_heater_service.update_operating_mode.assert_called_once()

    @pytest.mark.green
    def test_get_water_heater_telemetry(
        self, mock_telemetry_service, sample_water_heater, sample_telemetry_data
    ):
        """Test retrieving water heater telemetry through the AI tool.

        RED phase: This test defines the expected behavior for the telemetry tool.

        Business value: Enables the AI assistant to provide facility managers with
        historical performance data for analysis and troubleshooting.
        """
        # Setup - Configure mock service to return sample data
        heater_id = sample_water_heater.id
        hours = 24
        mock_telemetry_service.get_device_telemetry.return_value = sample_telemetry_data

        # Execute - Call the AI tool with the mocked service
        with patch(
            "src.ai.agent.tools.water_heater_tools.get_telemetry_service",
            return_value=mock_telemetry_service,
        ):
            result = get_water_heater_telemetry(heater_id, hours)

        # Verify - Result format and content
        parsed_result = json.loads(result)
        assert isinstance(parsed_result, list)
        assert len(parsed_result) == len(sample_telemetry_data)

        # Check first telemetry entry
        first_entry = parsed_result[0]
        assert "timestamp" in first_entry
        assert "temperature" in first_entry
        assert "power_consumption" in first_entry

        # Verify - Service method was called correctly
        mock_telemetry_service.get_device_telemetry.assert_called_once_with(
            device_id=heater_id, hours=hours
        )

    @pytest.mark.green
    def test_get_water_heater_maintenance_info(
        self, mock_maintenance_service, sample_water_heater
    ):
        """Test retrieving water heater maintenance information through the AI tool.

        RED phase: This test defines the expected behavior for the maintenance info tool.

        Business value: Enables the AI assistant to provide facility managers with
        maintenance recommendations and status information.
        """
        # Setup - Configure mock service to return sample data
        heater_id = sample_water_heater.id
        maintenance_info = {
            "device_id": heater_id,
            "last_maintenance": "2025-01-15T09:30:00Z",
            "next_maintenance_due": "2025-07-15T09:30:00Z",
            "maintenance_status": "GREEN",
            "recommendations": [
                "Regular inspection recommended in 3 months",
                "Water filter replacement due in 5 months",
            ],
            "issues": [],
        }
        mock_maintenance_service.get_maintenance_info.return_value = maintenance_info

        # Execute - Call the AI tool with the mocked service
        with patch(
            "src.ai.agent.tools.water_heater_tools.get_maintenance_service",
            return_value=mock_maintenance_service,
        ):
            result = get_water_heater_maintenance_info(heater_id)

        # Verify - Result format and content
        parsed_result = json.loads(result)
        assert parsed_result["device_id"] == heater_id
        assert "last_maintenance" in parsed_result
        assert "next_maintenance_due" in parsed_result
        assert "maintenance_status" in parsed_result
        assert "recommendations" in parsed_result
        assert isinstance(parsed_result["recommendations"], list)

        # Verify - Service method was called correctly
        mock_maintenance_service.get_maintenance_info.assert_called_once_with(heater_id)

    # GREEN phase tests would be added here after implementation
    # They would have the @pytest.mark.green decorator

    # REFACTOR phase tests would be added after code improvements
    # They would have the @pytest.mark.refactor decorator
