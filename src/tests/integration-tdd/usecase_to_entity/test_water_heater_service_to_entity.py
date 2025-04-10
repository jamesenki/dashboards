"""
Integration tests for the Water Heater Service to Entity boundary.

These tests validate the interaction between the Water Heater Service (use case)
and the Water Heater domain entities, following Clean Architecture principles.
Tests are tagged with their TDD phase to identify their purpose in the TDD cycle.
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.domain.entities.water_heater import WaterHeater
from src.domain.value_objects.device_status import DeviceStatus
from src.domain.value_objects.maintenance_status import MaintenanceStatus
from src.domain.value_objects.temperature import Temperature
from src.domain.value_objects.water_heater_mode import WaterHeaterMode
from src.gateways.water_heater_repository import WaterHeaterRepository
from src.use_cases.water_heater_service import WaterHeaterService


@pytest.fixture
def mock_water_heater_repository():
    """Create a mock water heater repository for testing."""
    return MagicMock(spec=WaterHeaterRepository)


@pytest.fixture
def sample_water_heater():
    """Create a sample water heater entity for testing."""
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


class TestWaterHeaterServiceToEntity:
    """Integration tests for the Water Heater Service to Entity boundary.

    These tests validate that:
    1. The service correctly applies business rules to entity operations
    2. The service preserves entity invariants during operations
    3. The service correctly handles domain exceptions from entities

    Following Clean Architecture principles, these tests focus on the interaction
    between use cases and domain entities, without involving external dependencies.
    """

    @pytest.mark.green
    def test_update_temperature_within_safe_range(
        self, mock_water_heater_repository, sample_water_heater
    ):
        """Test updating water heater temperature within the safe temperature range.

        RED phase: This test defines the expected behavior for temperature updates
        that are within the allowed range defined by the entity.

        Business value: Ensures that facility managers can adjust temperature
        while the system enforces safety limits defined by the manufacturer.
        """
        # Setup - Create service with mocked repository
        service = WaterHeaterService(repository=mock_water_heater_repository)

        # Configure mock to return our sample entity
        heater_id = sample_water_heater.id
        mock_water_heater_repository.get_by_id.return_value = sample_water_heater
        mock_water_heater_repository.update.return_value = True

        # Execute - Update temperature to a valid value
        new_temp = 60.0  # Within min-max range
        updated_heater = service.update_target_temperature(
            heater_id=heater_id, temperature=Temperature(value=new_temp, unit="C")
        )

        # Verify - Entity was updated correctly
        assert updated_heater.id == heater_id
        assert updated_heater.target_temperature.value == new_temp

        # Verify - Repository methods were called correctly
        mock_water_heater_repository.get_by_id.assert_called_once_with(heater_id)
        mock_water_heater_repository.update.assert_called_once()

    @pytest.mark.green
    def test_update_temperature_beyond_safe_range(
        self, mock_water_heater_repository, sample_water_heater
    ):
        """Test updating water heater temperature beyond the safe temperature range.

        RED phase: This test defines the expected behavior when a temperature update
        violates the safety limits defined by the entity.

        Business value: Prevents dangerous temperature settings that could damage
        equipment or cause safety hazards.
        """
        # Setup - Create service with mocked repository
        service = WaterHeaterService(repository=mock_water_heater_repository)

        # Configure mock to return our sample entity
        heater_id = sample_water_heater.id
        mock_water_heater_repository.get_by_id.return_value = sample_water_heater

        # Execute & Verify - Update temperature to an invalid value (beyond max)
        unsafe_temp = 90.0  # Beyond max_temperature of 85.0
        with pytest.raises(ValueError) as excinfo:
            service.update_target_temperature(
                heater_id=heater_id,
                temperature=Temperature(value=unsafe_temp, unit="C"),
            )

        # Verify exception message mentions temperature limits
        assert "temperature" in str(excinfo.value).lower()
        assert "range" in str(excinfo.value).lower()

        # Verify - Repository methods were called correctly
        mock_water_heater_repository.get_by_id.assert_called_once_with(heater_id)
        # Update should not be called for invalid temperature
        mock_water_heater_repository.update.assert_not_called()

    @pytest.mark.green
    def test_change_operating_mode(
        self, mock_water_heater_repository, sample_water_heater
    ):
        """Test changing water heater operating mode.

        RED phase: This test defines the expected behavior for mode changes.

        Business value: Allows facility managers to optimize energy usage by
        switching between performance and economy modes.
        """
        # Setup - Create service with mocked repository
        service = WaterHeaterService(repository=mock_water_heater_repository)

        # Configure mock to return our sample entity (currently in ECO mode)
        heater_id = sample_water_heater.id
        mock_water_heater_repository.get_by_id.return_value = sample_water_heater
        mock_water_heater_repository.update.return_value = True

        # Execute - Change mode to PERFORMANCE
        new_mode = WaterHeaterMode("PERFORMANCE")
        updated_heater = service.update_operating_mode(
            heater_id=heater_id, mode=new_mode
        )

        # Verify - Entity was updated correctly
        assert updated_heater.id == heater_id
        assert updated_heater.mode.value == "PERFORMANCE"

        # Verify - Repository methods were called correctly
        mock_water_heater_repository.get_by_id.assert_called_once_with(heater_id)
        mock_water_heater_repository.update.assert_called_once()

    @pytest.mark.green
    def test_water_heater_not_found(self, mock_water_heater_repository):
        """Test handling of non-existent water heater.

        RED phase: This test defines the expected behavior when a water heater
        doesn't exist.

        Business value: Provides clear error messages to facility managers when
        they attempt to operate on non-existent devices.
        """
        # Setup - Create service with mocked repository
        service = WaterHeaterService(repository=mock_water_heater_repository)

        # Configure mock to simulate water heater not found
        non_existent_id = "non-existent-id"
        mock_water_heater_repository.get_by_id.return_value = None

        # Execute & Verify - Attempt to get non-existent heater should raise exception
        with pytest.raises(ValueError) as excinfo:
            service.get_water_heater_by_id(non_existent_id)

        # Verify exception contains helpful information
        assert non_existent_id in str(excinfo.value)
        assert "not found" in str(excinfo.value).lower()

        # Verify - Repository method was called correctly
        mock_water_heater_repository.get_by_id.assert_called_once_with(non_existent_id)

    @pytest.mark.green
    def test_handle_temperature_state_transition(
        self, mock_water_heater_repository, sample_water_heater
    ):
        """Test handling of temperature state transitions in the water heater.

        RED phase: This test defines the expected behavior when temperature changes
        trigger internal state changes in the entity.

        Business value: Ensures the system correctly models physical behavior of
        water heaters and provides accurate status information.
        """
        # Setup - Create service with mocked repository
        service = WaterHeaterService(repository=mock_water_heater_repository)

        # Clone sample heater but with current temp below target
        cold_heater = WaterHeater(
            id=sample_water_heater.id,
            name=sample_water_heater.name,
            manufacturer=sample_water_heater.manufacturer,
            model=sample_water_heater.model,
            current_temperature=Temperature(value=45.0, unit="C"),  # Below target
            target_temperature=Temperature(value=55.0, unit="C"),
            min_temperature=sample_water_heater.min_temperature,
            max_temperature=sample_water_heater.max_temperature,
            status=sample_water_heater.status,
            mode=sample_water_heater.mode,
            health_status=sample_water_heater.health_status,
            location=sample_water_heater.location,
            is_simulated=sample_water_heater.is_simulated,
        )

        # Configure mock to return our cold heater
        heater_id = cold_heater.id
        mock_water_heater_repository.get_by_id.return_value = cold_heater
        mock_water_heater_repository.update.return_value = True

        # Execute - Process temperature update
        updated_heater = service.process_temperature_update(
            heater_id=heater_id, current_temperature=cold_heater.current_temperature
        )

        # Verify - Entity state should reflect heating activity
        assert updated_heater.id == heater_id
        assert updated_heater.heater_status.value == "HEATING"  # Should be heating

        # Verify - Repository methods were called correctly
        mock_water_heater_repository.get_by_id.assert_called_once_with(heater_id)
        mock_water_heater_repository.update.assert_called_once()

    # GREEN phase tests would be added here after implementation
    # They would have the @pytest.mark.green decorator

    # REFACTOR phase tests would be added after code improvements
    # They would have the @pytest.mark.refactor decorator
