"""
Unit tests for Water Heater Service with MongoDB Repository.

This module contains tests for the Water Heater Service that uses a MongoDB repository,
following the TDD approach (red-green-refactor) and Clean Architecture principles.
"""
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.water_heater import WaterHeater
from src.domain.value_objects.device_status import DeviceStatus
from src.domain.value_objects.maintenance_status import MaintenanceStatus
from src.domain.value_objects.temperature import Temperature
from src.domain.value_objects.water_heater_mode import WaterHeaterMode


@pytest.mark.unit
class TestWaterHeaterServiceWithMongoDB:
    """Unit tests for Water Heater Service with MongoDB repository."""

    @pytest.fixture
    def mock_mongodb_repository(self):
        """Create a mock MongoDB water heater repository."""
        mock_repo = AsyncMock()
        return mock_repo

    @pytest.fixture
    def sample_water_heater(self):
        """Create a sample water heater entity for testing."""
        return WaterHeater(
            id="test-heater-001",
            name="Test Heater",
            manufacturer="TestCo",
            model="TestModel100",
            location="Building A",
            is_simulated=False,
            current_temperature=Temperature(value=50.0, unit="C"),
            target_temperature=Temperature(value=55.0, unit="C"),
            min_temperature=Temperature(value=40.0, unit="C"),
            max_temperature=Temperature(value=85.0, unit="C"),
            status=DeviceStatus(value="ONLINE"),
            mode=WaterHeaterMode(value="ECO"),
            health_status=MaintenanceStatus(value="NORMAL"),
            heater_status="OFF",
            last_updated=datetime.now(),
        )

    @pytest.fixture
    def water_heater_service(self, mock_mongodb_repository):
        """Create a water heater service instance with mocked repository."""
        from src.use_cases.water_heater_service import WaterHeaterService

        return WaterHeaterService(repository=mock_mongodb_repository)

    @pytest.mark.tdd_red
    @pytest.mark.asyncio
    async def test_get_water_heater_by_id(
        self, water_heater_service, mock_mongodb_repository, sample_water_heater
    ):
        """Test retrieving a water heater by ID using the MongoDB repository.

        This test verifies that the service correctly delegates to the MongoDB repository
        and returns the water heater entity.
        """
        # Arrange
        mock_mongodb_repository.get_by_id.return_value = sample_water_heater

        # Act
        result = await water_heater_service.get_water_heater_by_id(
            sample_water_heater.id
        )

        # Assert
        assert result == sample_water_heater
        mock_mongodb_repository.get_by_id.assert_called_once_with(
            sample_water_heater.id
        )

    @pytest.mark.tdd_red
    @pytest.mark.asyncio
    async def test_get_water_heater_not_found(
        self, water_heater_service, mock_mongodb_repository
    ):
        """Test retrieving a non-existent water heater.

        This test verifies that the service correctly handles the case where the MongoDB
        repository returns None for a non-existent water heater.
        """
        # Arrange
        mock_mongodb_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(
            ValueError, match="Water heater with ID non-existent-id not found"
        ):
            await water_heater_service.get_water_heater_by_id("non-existent-id")

        mock_mongodb_repository.get_by_id.assert_called_once_with("non-existent-id")

    @pytest.mark.tdd_red
    @pytest.mark.asyncio
    async def test_get_all_water_heaters(
        self, water_heater_service, mock_mongodb_repository, sample_water_heater
    ):
        """Test retrieving all water heaters using the MongoDB repository.

        This test verifies that the service correctly delegates to the MongoDB repository
        and returns a list of water heater entities.
        """
        # Arrange
        second_heater = WaterHeater(
            id="test-heater-002",
            name="Second Test Heater",
            manufacturer="TestCo",
            model="TestModel200",
            location="Building B",
            is_simulated=True,
            current_temperature=Temperature(value=45.0, unit="C"),
            target_temperature=Temperature(value=50.0, unit="C"),
            min_temperature=Temperature(value=40.0, unit="C"),
            max_temperature=Temperature(value=85.0, unit="C"),
            status=DeviceStatus(value="ONLINE"),
            mode=WaterHeaterMode(value="PERFORMANCE"),
            health_status=MaintenanceStatus(value="NORMAL"),
            heater_status="ON",
            last_updated=datetime.now(),
        )

        mock_mongodb_repository.get_all.return_value = [
            sample_water_heater,
            second_heater,
        ]

        # Act
        result = await water_heater_service.get_all_water_heaters()

        # Assert
        assert len(result) == 2
        assert result[0] == sample_water_heater
        assert result[1] == second_heater
        mock_mongodb_repository.get_all.assert_called_once()

    @pytest.mark.tdd_red
    @pytest.mark.asyncio
    async def test_create_water_heater(
        self, water_heater_service, mock_mongodb_repository, sample_water_heater
    ):
        """Test creating a water heater using the MongoDB repository.

        This test verifies that the service correctly delegates to the MongoDB repository
        to create a new water heater entity.
        """
        # Arrange
        mock_mongodb_repository.save.return_value = sample_water_heater.id
        mock_mongodb_repository.get_by_id.return_value = sample_water_heater

        heater_data = {
            "name": sample_water_heater.name,
            "manufacturer": sample_water_heater.manufacturer,
            "model": sample_water_heater.model,
            "location": sample_water_heater.location,
            "is_simulated": sample_water_heater.is_simulated,
            "current_temperature": sample_water_heater.current_temperature.value,
            "current_temperature_unit": sample_water_heater.current_temperature.unit,
            "target_temperature": sample_water_heater.target_temperature.value,
            "target_temperature_unit": sample_water_heater.target_temperature.unit,
            "min_temperature": sample_water_heater.min_temperature.value,
            "max_temperature": sample_water_heater.max_temperature.value,
            "status": sample_water_heater.status.value,
            "mode": sample_water_heater.mode.value,
        }

        # Act
        result = await water_heater_service.create_water_heater(heater_data)

        # Assert
        assert result == sample_water_heater
        mock_mongodb_repository.save.assert_called_once()
        # Verify that get_by_id was called with the ID returned by save
        mock_mongodb_repository.get_by_id.assert_called_once_with(
            sample_water_heater.id
        )

    @pytest.mark.tdd_red
    @pytest.mark.asyncio
    async def test_update_target_temperature(
        self, water_heater_service, mock_mongodb_repository, sample_water_heater
    ):
        """Test updating a water heater's target temperature using the MongoDB repository.

        This test verifies that the service correctly delegates to the MongoDB repository
        to update the target temperature of a water heater.
        """
        # Arrange
        mock_mongodb_repository.get_by_id.return_value = sample_water_heater
        mock_mongodb_repository.update.return_value = True

        # Create a clone of the heater with updated temperature for the second get_by_id call
        updated_heater = WaterHeater(
            id=sample_water_heater.id,
            name=sample_water_heater.name,
            manufacturer=sample_water_heater.manufacturer,
            model=sample_water_heater.model,
            location=sample_water_heater.location,
            is_simulated=sample_water_heater.is_simulated,
            current_temperature=sample_water_heater.current_temperature,
            target_temperature=Temperature(value=60.0, unit="C"),  # Updated value
            min_temperature=sample_water_heater.min_temperature,
            max_temperature=sample_water_heater.max_temperature,
            status=sample_water_heater.status,
            mode=sample_water_heater.mode,
            health_status=sample_water_heater.health_status,
            heater_status=sample_water_heater.heater_status,
            last_updated=datetime.now(),
        )

        # Make get_by_id return the original heater first, then the updated heater
        mock_mongodb_repository.get_by_id.side_effect = [
            sample_water_heater,
            updated_heater,
        ]

        # New temperature to set
        new_temperature = Temperature(value=60.0, unit="C")

        # Act
        result = await water_heater_service.update_target_temperature(
            sample_water_heater.id, new_temperature
        )

        # Assert
        assert result == updated_heater
        assert result.target_temperature.value == 60.0
        # Verify get_by_id was called twice (before and after update)
        assert mock_mongodb_repository.get_by_id.call_count == 2
        # Verify update was called once with the correct entity
        mock_mongodb_repository.update.assert_called_once()
        # Get the entity that was passed to update
        updated_entity = mock_mongodb_repository.update.call_args[0][0]
        assert updated_entity.target_temperature.value == 60.0

    @pytest.mark.tdd_red
    @pytest.mark.asyncio
    async def test_update_target_temperature_beyond_safe_range(
        self, water_heater_service, mock_mongodb_repository, sample_water_heater
    ):
        """Test updating a water heater's target temperature beyond the safe range.

        This test verifies that the service correctly validates the target temperature
        and raises an error if it's outside the safe range.
        """
        # Arrange
        mock_mongodb_repository.get_by_id.return_value = sample_water_heater

        # Try to set temperature beyond maximum
        unsafe_temperature = Temperature(value=90.0, unit="C")

        # Act & Assert
        with pytest.raises(
            ValueError,
            match="Target temperature 90.0°C exceeds maximum safe temperature",
        ):
            await water_heater_service.update_target_temperature(
                sample_water_heater.id, unsafe_temperature
            )

        # Verify get_by_id was called but update was not
        mock_mongodb_repository.get_by_id.assert_called_once_with(
            sample_water_heater.id
        )
        mock_mongodb_repository.update.assert_not_called()

    @pytest.mark.tdd_red
    @pytest.mark.asyncio
    async def test_update_operating_mode(
        self, water_heater_service, mock_mongodb_repository, sample_water_heater
    ):
        """Test updating a water heater's operating mode using the MongoDB repository.

        This test verifies that the service correctly delegates to the MongoDB repository
        to update the operating mode of a water heater.
        """
        # Arrange
        mock_mongodb_repository.get_by_id.return_value = sample_water_heater
        mock_mongodb_repository.update.return_value = True

        # Create a clone of the heater with updated mode for the second get_by_id call
        updated_heater = WaterHeater(
            id=sample_water_heater.id,
            name=sample_water_heater.name,
            manufacturer=sample_water_heater.manufacturer,
            model=sample_water_heater.model,
            location=sample_water_heater.location,
            is_simulated=sample_water_heater.is_simulated,
            current_temperature=sample_water_heater.current_temperature,
            target_temperature=sample_water_heater.target_temperature,
            min_temperature=sample_water_heater.min_temperature,
            max_temperature=sample_water_heater.max_temperature,
            status=sample_water_heater.status,
            mode=WaterHeaterMode(value="PERFORMANCE"),  # Updated value
            health_status=sample_water_heater.health_status,
            heater_status=sample_water_heater.heater_status,
            last_updated=datetime.now(),
        )

        # Make get_by_id return the original heater first, then the updated heater
        mock_mongodb_repository.get_by_id.side_effect = [
            sample_water_heater,
            updated_heater,
        ]

        # New mode to set
        new_mode = WaterHeaterMode(value="PERFORMANCE")

        # Act
        result = await water_heater_service.update_operating_mode(
            sample_water_heater.id, new_mode
        )

        # Assert
        assert result == updated_heater
        assert result.mode.value == "PERFORMANCE"
        # Verify get_by_id was called twice (before and after update)
        assert mock_mongodb_repository.get_by_id.call_count == 2
        # Verify update was called once with the correct entity
        mock_mongodb_repository.update.assert_called_once()
        # Get the entity that was passed to update
        updated_entity = mock_mongodb_repository.update.call_args[0][0]
        assert updated_entity.mode.value == "PERFORMANCE"

    @pytest.mark.tdd_red
    @pytest.mark.asyncio
    async def test_delete_water_heater(
        self, water_heater_service, mock_mongodb_repository, sample_water_heater
    ):
        """Test deleting a water heater using the MongoDB repository.

        This test verifies that the service correctly delegates to the MongoDB repository
        to delete a water heater entity.
        """
        # Arrange
        mock_mongodb_repository.get_by_id.return_value = sample_water_heater
        mock_mongodb_repository.delete.return_value = True

        # Act
        result = await water_heater_service.delete_water_heater(sample_water_heater.id)

        # Assert
        assert result is True
        mock_mongodb_repository.get_by_id.assert_called_once_with(
            sample_water_heater.id
        )
        mock_mongodb_repository.delete.assert_called_once_with(sample_water_heater.id)

    @pytest.mark.tdd_red
    @pytest.mark.asyncio
    async def test_delete_non_existent_water_heater(
        self, water_heater_service, mock_mongodb_repository
    ):
        """Test deleting a non-existent water heater.

        This test verifies that the service correctly handles the case where the MongoDB
        repository returns None for a non-existent water heater during deletion.
        """
        # Arrange
        mock_mongodb_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(
            ValueError, match="Water heater with ID non-existent-id not found"
        ):
            await water_heater_service.delete_water_heater("non-existent-id")

        mock_mongodb_repository.get_by_id.assert_called_once_with("non-existent-id")
        mock_mongodb_repository.delete.assert_not_called()
