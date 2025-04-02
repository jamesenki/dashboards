from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.device import DeviceStatus, DeviceType
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterMode,
    WaterHeaterReading,
    WaterHeaterStatus,
)
from src.services.water_heater import WaterHeaterService


class TestWaterHeaterService:
    """Test cases for water heater service."""

    @pytest.fixture
    def mock_dummy_data(self, monkeypatch):
        """Create a mock for the dummy_data module."""
        mock_data = MagicMock()
        mock_data.get_water_heaters = MagicMock()
        mock_data.get_water_heater = MagicMock()
        mock_data.add_water_heater = MagicMock()
        mock_data.update_water_heater = MagicMock()
        mock_data.delete_water_heater = MagicMock()

        # Monkeypatch the dummy_data in the service module
        from src.services.water_heater import dummy_data as original_dummy_data

        monkeypatch.setattr("src.services.water_heater.dummy_data", mock_data)
        return mock_data

    @pytest.fixture
    def water_heater_service(self):
        """Create a water heater service without repository."""
        return WaterHeaterService()

    @pytest.fixture
    def sample_water_heater(self):
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

    @pytest.mark.asyncio
    async def test_get_water_heaters(
        self, water_heater_service, mock_dummy_data, sample_water_heater
    ):
        """Test getting all water heaters."""
        # Setup mock return value
        mock_dummy_data.get_water_heaters.return_value = [sample_water_heater]

        # Call the service method
        heaters = await water_heater_service.get_water_heaters()

        # Verify the result
        assert len(heaters) == 1
        assert heaters[0].id == "test-water-heater-1"
        assert heaters[0].type == DeviceType.WATER_HEATER

        # Verify dummy_data was called correctly
        mock_dummy_data.get_water_heaters.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_water_heater(
        self, water_heater_service, mock_dummy_data, sample_water_heater
    ):
        """Test getting a specific water heater by ID."""
        # Setup mock return value
        mock_dummy_data.get_water_heater.return_value = sample_water_heater

        # Call the service method
        heater = await water_heater_service.get_water_heater("test-water-heater-1")

        # Verify the result
        assert heater is not None
        assert heater.id == "test-water-heater-1"
        assert heater.current_temperature == 45.5

        # Verify dummy_data was called correctly
        mock_dummy_data.get_water_heater.assert_called_once_with("test-water-heater-1")

    @pytest.mark.asyncio
    async def test_get_water_heater_not_found(
        self, water_heater_service, mock_dummy_data
    ):
        """Test getting a non-existent water heater."""
        # Setup mock return value
        mock_dummy_data.get_water_heater.return_value = None

        # Call the service method
        heater = await water_heater_service.get_water_heater("nonexistent-id")

        # Verify the result
        assert heater is None

        # Verify dummy_data was called correctly
        mock_dummy_data.get_water_heater.assert_called_once_with("nonexistent-id")

    @pytest.mark.asyncio
    async def test_create_water_heater(
        self, water_heater_service, mock_dummy_data, sample_water_heater
    ):
        """Test creating a new water heater."""
        # Setup mock return value
        mock_dummy_data.add_water_heater.return_value = sample_water_heater

        # Call the service method
        heater = await water_heater_service.create_water_heater(sample_water_heater)

        # Verify the result
        assert heater is not None
        assert heater.id == "test-water-heater-1"
        assert heater.type == DeviceType.WATER_HEATER

        # Verify dummy_data was called correctly
        mock_dummy_data.add_water_heater.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_target_temperature(
        self, water_heater_service, mock_dummy_data, sample_water_heater
    ):
        """Test updating a water heater's target temperature."""
        # Setup mock behavior
        mock_dummy_data.get_water_heater.return_value = sample_water_heater
        updated_heater = sample_water_heater.model_copy(
            update={"target_temperature": 55.0}
        )
        mock_dummy_data.update_water_heater.return_value = updated_heater

        # Call the service method
        updated = await water_heater_service.update_target_temperature(
            "test-water-heater-1", 55.0
        )

        # Verify the result
        assert updated is not None
        assert updated.target_temperature == 55.0

        # Verify dummy_data was called correctly
        mock_dummy_data.get_water_heater.assert_called_once_with("test-water-heater-1")
        mock_dummy_data.update_water_heater.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_mode(
        self, water_heater_service, mock_dummy_data, sample_water_heater
    ):
        """Test updating a water heater's operational mode."""
        # Setup mock behavior
        mock_dummy_data.get_water_heater.return_value = sample_water_heater
        updated_heater = sample_water_heater.model_copy(
            update={"mode": WaterHeaterMode.BOOST}
        )
        mock_dummy_data.update_water_heater.return_value = updated_heater

        # Call the service method
        updated = await water_heater_service.update_mode(
            "test-water-heater-1", WaterHeaterMode.BOOST
        )

        # Verify the result
        assert updated is not None
        assert updated.mode == WaterHeaterMode.BOOST

        # Verify dummy_data was called correctly
        mock_dummy_data.get_water_heater.assert_called_once_with("test-water-heater-1")
        mock_dummy_data.update_water_heater.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_temperature_reading(
        self, water_heater_service, mock_dummy_data, sample_water_heater
    ):
        """Test adding a temperature reading to a water heater."""
        # Setup mock behavior
        mock_dummy_data.get_water_heater.return_value = sample_water_heater

        updated_heater = sample_water_heater.model_copy(
            update={"current_temperature": 52.0}
        )
        mock_dummy_data.update_water_heater.return_value = updated_heater

        # Call the service method
        result = await water_heater_service.add_temperature_reading(
            "test-water-heater-1", temperature=52.0, pressure=3.5, energy_usage=110.5
        )

        # Verify the result
        assert result is not None
        assert result.current_temperature == 52.0

        # Verify dummy_data was called correctly
        mock_dummy_data.get_water_heater.assert_called_once_with("test-water-heater-1")
        mock_dummy_data.update_water_heater.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_heater_status_based_on_reading(
        self, water_heater_service, mock_dummy_data, sample_water_heater
    ):
        """Test heater status is updated when temperature reading exceeds target."""
        # Setup: Heater is currently heating
        sample_water_heater.heater_status = WaterHeaterStatus.HEATING
        sample_water_heater.target_temperature = 50.0
        sample_water_heater.current_temperature = 48.0

        mock_dummy_data.get_water_heater.return_value = sample_water_heater

        # Create updated heater with temp above target and status changed to standby
        updated_heater = sample_water_heater.model_copy(
            update={
                "current_temperature": 51.5,
                "heater_status": WaterHeaterStatus.STANDBY,
            }
        )
        mock_dummy_data.update_water_heater.return_value = updated_heater

        # Call the service method with temp above target
        result = await water_heater_service.add_temperature_reading(
            "test-water-heater-1", temperature=51.5
        )

        # Verify the result shows heater switched to standby
        assert result is not None
        assert result.heater_status == WaterHeaterStatus.STANDBY
        assert result.current_temperature == 51.5

        # Verify dummy_data was called correctly
        mock_dummy_data.get_water_heater.assert_called_once_with("test-water-heater-1")
        mock_dummy_data.update_water_heater.assert_called_once()
