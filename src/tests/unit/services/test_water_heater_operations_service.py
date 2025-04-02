from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.models.water_heater import (
    WaterHeater,
    WaterHeaterMode,
    WaterHeaterReading,
    WaterHeaterStatus,
)
from src.services.water_heater_operations_service import WaterHeaterOperationsService


class TestWaterHeaterOperationsService:
    """Test cases for water heater operations service."""

    def setup_method(self):
        """Setup for each test method."""
        self.service = WaterHeaterOperationsService()

    @pytest.mark.asyncio
    async def test_get_operations_dashboard(self):
        """Test retrieving operations dashboard data."""
        # Arrange
        heater_id = "test-heater-123"
        mock_readings = [
            WaterHeaterReading(
                timestamp=datetime.now() - timedelta(hours=3),
                temperature=65.5,
                pressure=2.5,
                energy_usage=1200,
                flow_rate=3.2,
            ),
            WaterHeaterReading(
                timestamp=datetime.now() - timedelta(hours=1),
                temperature=68.0,
                pressure=2.6,
                energy_usage=1350,
                flow_rate=3.5,
            ),
        ]

        mock_heater = WaterHeater(
            id=heater_id,
            name="Test Water Heater",
            target_temperature=70.0,
            current_temperature=68.0,
            mode=WaterHeaterMode.ECO,
            heater_status=WaterHeaterStatus.HEATING,
            readings=mock_readings,
        )

        with patch(
            "src.services.water_heater.WaterHeaterService.get_water_heater"
        ) as mock_get_heater:
            mock_get_heater.return_value = mock_heater

            # Act
            result = await self.service.get_operations_dashboard(heater_id)

            # Assert
            assert result is not None
            # Check for expected dashboard components
            assert "machine_status" in result
            assert "heater_status" in result
            assert "current_temperature" in result
            assert "target_temperature" in result
            assert "gauges" in result

            # Check gauge data
            gauges = result["gauges"]
            assert "temperature" in gauges
            assert "pressure" in gauges
            assert "energy_usage" in gauges
            assert "flow_rate" in gauges

            # Check that the service called the right dependencies
            mock_get_heater.assert_called_once_with(heater_id)

    def test_transform_temperature_gauge_data(self):
        """Test transformation of temperature data for gauge display."""
        # Arrange
        current_temp = 68.0
        target_temp = 70.0
        min_temp = 40.0
        max_temp = 85.0

        # Act
        result = self.service._transform_temperature_gauge_data(
            current_temp, target_temp, min_temp, max_temp
        )

        # Assert
        assert "value" in result
        assert "min" in result
        assert "max" in result
        assert "unit" in result
        assert "percentage" in result

        # Verify calculation: (68-40)/(85-40) ≈ 0.622 or 62.2%
        assert result["value"] == 68.0
        assert result["min"] == 40.0
        assert result["max"] == 85.0
        assert result["unit"] == "°C"
        assert result["percentage"] == pytest.approx(62.2, 0.1)

    def test_transform_pressure_gauge_data(self):
        """Test transformation of pressure data for gauge display."""
        # Arrange
        current_pressure = 2.6

        # Act
        result = self.service._transform_pressure_gauge_data(current_pressure)

        # Assert
        assert "value" in result
        assert "min" in result
        assert "max" in result
        assert "unit" in result
        assert "percentage" in result

        # Expected values based on specification
        assert result["value"] == 2.6
        assert result["min"] == 0.0
        assert result["max"] == 5.0
        assert result["unit"] == "bar"
        assert result["percentage"] == pytest.approx(52.0, 0.1)

    def test_transform_energy_usage_gauge_data(self):
        """Test transformation of energy usage data for gauge display."""
        # Arrange
        current_energy = 1350

        # Act
        result = self.service._transform_energy_usage_gauge_data(current_energy)

        # Assert
        assert "value" in result
        assert "min" in result
        assert "max" in result
        assert "unit" in result
        assert "percentage" in result

        # Expected values based on specification
        assert result["value"] == 1350
        assert result["min"] == 0
        assert result["max"] == 3000
        assert result["unit"] == "W"
        assert result["percentage"] == pytest.approx(45.0, 0.1)

    def test_transform_flow_rate_gauge_data(self):
        """Test transformation of flow rate data for gauge display."""
        # Arrange
        current_flow_rate = 3.5

        # Act
        result = self.service._transform_flow_rate_gauge_data(current_flow_rate)

        # Assert
        assert "value" in result
        assert "min" in result
        assert "max" in result
        assert "unit" in result
        assert "percentage" in result

        # Expected values based on specification
        assert result["value"] == 3.5
        assert result["min"] == 0.0
        assert result["max"] == 10.0
        assert result["unit"] == "L/min"
        assert result["percentage"] == pytest.approx(35.0, 0.1)

    def test_calculate_asset_health(self):
        """Test calculation of overall asset health score."""
        # Arrange
        temperature = 68.0
        target_temperature = 70.0
        pressure = 2.6
        energy_usage = 1350
        flow_rate = 3.5

        # Act
        result = self.service._calculate_asset_health(
            temperature, target_temperature, pressure, energy_usage, flow_rate
        )

        # Assert
        assert 0 <= result <= 100
        # We expect a good health score since all values are within normal ranges
        assert result > 70
