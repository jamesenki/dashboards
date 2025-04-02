"""
Tests for the water heater history service
"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.models.water_heater import (
    WaterHeater,
    WaterHeaterMode,
    WaterHeaterReading,
    WaterHeaterStatus,
)
from src.services.water_heater_history import WaterHeaterHistoryService


class TestWaterHeaterHistoryService:
    """Test cases for the water heater history service"""

    def setup_method(self):
        """Setup for each test method."""
        self.service = WaterHeaterHistoryService()

    @pytest.mark.asyncio
    async def test_get_temperature_history(self):
        """Test retrieving temperature history data."""
        # Arrange
        heater_id = "test-heater-123"
        days = 7
        now = datetime.now()

        # Create mock readings spanning the last week
        mock_readings = [
            WaterHeaterReading(
                timestamp=now - timedelta(days=7, hours=1),
                temperature=65.0,
                pressure=2.5,
                energy_usage=1200,
                flow_rate=3.2,
            ),
            WaterHeaterReading(
                timestamp=now - timedelta(days=6),
                temperature=66.5,
                pressure=2.6,
                energy_usage=1250,
                flow_rate=3.3,
            ),
            WaterHeaterReading(
                timestamp=now - timedelta(days=4),
                temperature=68.0,
                pressure=2.7,
                energy_usage=1300,
                flow_rate=3.4,
            ),
            WaterHeaterReading(
                timestamp=now - timedelta(days=2),
                temperature=67.0,
                pressure=2.6,
                energy_usage=1280,
                flow_rate=3.3,
            ),
            WaterHeaterReading(
                timestamp=now - timedelta(hours=12),
                temperature=69.0,
                pressure=2.8,
                energy_usage=1350,
                flow_rate=3.5,
            ),
        ]

        mock_heater = WaterHeater(
            id=heater_id,
            name="Test Water Heater",
            target_temperature=70.0,
            current_temperature=69.0,
            mode=WaterHeaterMode.ECO,
            heater_status=WaterHeaterStatus.HEATING,
            readings=mock_readings,
        )

        with patch(
            "src.services.water_heater.WaterHeaterService.get_water_heater"
        ) as mock_get_heater:
            mock_get_heater.return_value = mock_heater

            # Act
            result = await self.service.get_temperature_history(heater_id, days)

            # Assert
            assert result is not None
            assert "labels" in result
            assert "datasets" in result
            assert len(result["labels"]) > 0
            assert len(result["datasets"]) == 2  # Temperature and target temperature

            # Check temperature dataset
            temp_dataset = result["datasets"][0]
            assert "label" in temp_dataset
            assert "data" in temp_dataset
            assert len(temp_dataset["data"]) == len(result["labels"])

            # Ensure we only get readings from the specified time period
            assert len(temp_dataset["data"]) <= days + 1  # +1 for current day

            # Check the service called the right dependencies
            mock_get_heater.assert_called_once_with(heater_id)

    @pytest.mark.asyncio
    async def test_get_energy_usage_history(self):
        """Test retrieving energy usage history data."""
        # Arrange
        heater_id = "test-heater-123"
        days = 7
        now = datetime.now()

        # Create mock readings spanning the last week
        mock_readings = [
            WaterHeaterReading(
                timestamp=now - timedelta(days=7, hours=1),
                temperature=65.0,
                pressure=2.5,
                energy_usage=1200,
                flow_rate=3.2,
            ),
            WaterHeaterReading(
                timestamp=now - timedelta(days=6),
                temperature=66.5,
                pressure=2.6,
                energy_usage=1250,
                flow_rate=3.3,
            ),
            WaterHeaterReading(
                timestamp=now - timedelta(days=4),
                temperature=68.0,
                pressure=2.7,
                energy_usage=1300,
                flow_rate=3.4,
            ),
            WaterHeaterReading(
                timestamp=now - timedelta(days=2),
                temperature=67.0,
                pressure=2.6,
                energy_usage=1280,
                flow_rate=3.3,
            ),
            WaterHeaterReading(
                timestamp=now - timedelta(hours=12),
                temperature=69.0,
                pressure=2.8,
                energy_usage=1350,
                flow_rate=3.5,
            ),
        ]

        mock_heater = WaterHeater(
            id=heater_id,
            name="Test Water Heater",
            target_temperature=70.0,
            current_temperature=69.0,
            mode=WaterHeaterMode.ECO,
            heater_status=WaterHeaterStatus.HEATING,
            readings=mock_readings,
        )

        with patch(
            "src.services.water_heater.WaterHeaterService.get_water_heater"
        ) as mock_get_heater:
            mock_get_heater.return_value = mock_heater

            # Act
            result = await self.service.get_energy_usage_history(heater_id, days)

            # Assert
            assert result is not None
            assert "labels" in result
            assert "datasets" in result
            assert len(result["labels"]) > 0
            assert len(result["datasets"]) == 1  # Energy usage

            # Check energy usage dataset
            energy_dataset = result["datasets"][0]
            assert "label" in energy_dataset
            assert "data" in energy_dataset
            assert len(energy_dataset["data"]) == len(result["labels"])

            # Ensure we only get readings from the specified time period
            assert len(energy_dataset["data"]) <= days + 1  # +1 for current day

            # Check the service called the right dependencies
            mock_get_heater.assert_called_once_with(heater_id)

    @pytest.mark.asyncio
    async def test_get_pressure_flow_history(self):
        """Test retrieving pressure and flow rate history data."""
        # Arrange
        heater_id = "test-heater-123"
        days = 7
        now = datetime.now()

        # Create mock readings spanning the last week
        mock_readings = [
            WaterHeaterReading(
                timestamp=now - timedelta(days=7, hours=1),
                temperature=65.0,
                pressure=2.5,
                energy_usage=1200,
                flow_rate=3.2,
            ),
            WaterHeaterReading(
                timestamp=now - timedelta(days=6),
                temperature=66.5,
                pressure=2.6,
                energy_usage=1250,
                flow_rate=3.3,
            ),
            WaterHeaterReading(
                timestamp=now - timedelta(days=4),
                temperature=68.0,
                pressure=2.7,
                energy_usage=1300,
                flow_rate=3.4,
            ),
            WaterHeaterReading(
                timestamp=now - timedelta(days=2),
                temperature=67.0,
                pressure=2.6,
                energy_usage=1280,
                flow_rate=3.3,
            ),
            WaterHeaterReading(
                timestamp=now - timedelta(hours=12),
                temperature=69.0,
                pressure=2.8,
                energy_usage=1350,
                flow_rate=3.5,
            ),
        ]

        mock_heater = WaterHeater(
            id=heater_id,
            name="Test Water Heater",
            target_temperature=70.0,
            current_temperature=69.0,
            mode=WaterHeaterMode.ECO,
            heater_status=WaterHeaterStatus.HEATING,
            readings=mock_readings,
        )

        with patch(
            "src.services.water_heater.WaterHeaterService.get_water_heater"
        ) as mock_get_heater:
            mock_get_heater.return_value = mock_heater

            # Act
            result = await self.service.get_pressure_flow_history(heater_id, days)

            # Assert
            assert result is not None
            assert "labels" in result
            assert "datasets" in result
            assert len(result["labels"]) > 0
            assert len(result["datasets"]) == 2  # Pressure and flow rate

            # Check pressure dataset
            pressure_dataset = result["datasets"][0]
            assert "label" in pressure_dataset
            assert "data" in pressure_dataset
            assert len(pressure_dataset["data"]) == len(result["labels"])

            # Check flow rate dataset
            flow_dataset = result["datasets"][1]
            assert "label" in flow_dataset
            assert "data" in flow_dataset
            assert len(flow_dataset["data"]) == len(result["labels"])

            # Ensure we only get readings from the specified time period
            assert len(pressure_dataset["data"]) <= days + 1  # +1 for current day

            # Check the service called the right dependencies
            mock_get_heater.assert_called_once_with(heater_id)

    @pytest.mark.asyncio
    async def test_get_history_dashboard(self):
        """Test retrieving the complete history dashboard data."""
        # Arrange
        heater_id = "test-heater-123"
        days = 7

        # Mock the individual history methods
        temperature_history = {
            "labels": ["Day 1", "Day 2"],
            "datasets": [{"label": "Temperature", "data": [65, 68]}],
        }

        energy_usage_history = {
            "labels": ["Day 1", "Day 2"],
            "datasets": [{"label": "Energy Usage", "data": [1200, 1300]}],
        }

        pressure_flow_history = {
            "labels": ["Day 1", "Day 2"],
            "datasets": [
                {"label": "Pressure", "data": [2.5, 2.7]},
                {"label": "Flow Rate", "data": [3.2, 3.4]},
            ],
        }

        with patch(
            "src.services.water_heater_history.WaterHeaterHistoryService.get_temperature_history"
        ) as mock_temp, patch(
            "src.services.water_heater_history.WaterHeaterHistoryService.get_energy_usage_history"
        ) as mock_energy, patch(
            "src.services.water_heater_history.WaterHeaterHistoryService.get_pressure_flow_history"
        ) as mock_pressure:
            mock_temp.return_value = temperature_history
            mock_energy.return_value = energy_usage_history
            mock_pressure.return_value = pressure_flow_history

            # Act
            result = await self.service.get_history_dashboard(heater_id, days)

            # Assert
            assert result is not None
            assert "temperature" in result
            assert "energy_usage" in result
            assert "pressure_flow" in result

            assert result["temperature"] == temperature_history
            assert result["energy_usage"] == energy_usage_history
            assert result["pressure_flow"] == pressure_flow_history

            # Check that all methods were called with correct parameters
            mock_temp.assert_called_once_with(heater_id, days)
            mock_energy.assert_called_once_with(heater_id, days)
            mock_pressure.assert_called_once_with(heater_id, days)
