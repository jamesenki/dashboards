from datetime import datetime
from enum import Enum

import pytest

from src.models.device import DeviceStatus, DeviceType
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterMode,
    WaterHeaterReading,
    WaterHeaterStatus,
)


class TestWaterHeaterModel:
    """Test cases for water heater models."""

    def test_water_heater_mode_enum(self):
        """Test the WaterHeaterMode enum has required values."""
        assert WaterHeaterMode.OFF == "OFF"
        assert WaterHeaterMode.ECO == "ECO"
        assert WaterHeaterMode.BOOST == "BOOST"
        assert isinstance(WaterHeaterMode.OFF, str)

    def test_water_heater_status_enum(self):
        """Test the WaterHeaterStatus enum has required values."""
        assert WaterHeaterStatus.STANDBY == "STANDBY"
        assert WaterHeaterStatus.HEATING == "HEATING"
        assert isinstance(WaterHeaterStatus.STANDBY, str)

    def test_water_heater_reading_model(self):
        """Test the WaterHeaterReading model."""
        # Create a water heater reading
        reading = WaterHeaterReading(
            timestamp=datetime.now(),
            temperature=55.5,
            pressure=2.2,
            energy_usage=120.5,
            flow_rate=5.5,
        )

        # Assert properties
        assert reading.temperature == 55.5
        assert reading.pressure == 2.2
        assert reading.energy_usage == 120.5
        assert reading.flow_rate == 5.5

        # Test serialization/deserialization
        reading_dict = reading.model_dump()
        assert "temperature" in reading_dict
        assert "pressure" in reading_dict
        assert "energy_usage" in reading_dict
        assert "flow_rate" in reading_dict

    def test_water_heater_model(self):
        """Test the WaterHeater model."""
        # Create a water heater
        water_heater = WaterHeater(
            id="test-wh-1",
            name="Water Heater 1",
            type=DeviceType.WATER_HEATER,
            status=DeviceStatus.ONLINE,
            location="Building A, Floor 2",
            target_temperature=50.0,
            current_temperature=45.5,
            mode=WaterHeaterMode.ECO,
            heater_status=WaterHeaterStatus.HEATING,
            capacity=150.0,
            efficiency_rating=0.85,
            max_temperature=85.0,
            min_temperature=40.0,
        )

        # Assert base properties
        assert water_heater.name == "Water Heater 1"
        assert water_heater.type == DeviceType.WATER_HEATER
        assert water_heater.status == DeviceStatus.ONLINE
        assert water_heater.location == "Building A, Floor 2"

        # Assert water heater specific properties
        assert water_heater.target_temperature == 50.0
        assert water_heater.current_temperature == 45.5
        assert water_heater.mode == WaterHeaterMode.ECO
        assert water_heater.heater_status == WaterHeaterStatus.HEATING
        assert water_heater.capacity == 150.0
        assert water_heater.efficiency_rating == 0.85
        assert water_heater.max_temperature == 85.0
        assert water_heater.min_temperature == 40.0

        # Test serialization/deserialization
        heater_dict = water_heater.model_dump()
        assert "target_temperature" in heater_dict
        assert "current_temperature" in heater_dict
        assert "mode" in heater_dict
        assert "heater_status" in heater_dict
        assert "capacity" in heater_dict
        assert "efficiency_rating" in heater_dict

    def test_water_heater_add_reading(self):
        """Test adding a reading to a water heater."""
        # Create a water heater
        water_heater = WaterHeater(
            id="test-wh-2",
            name="Water Heater 1",
            type=DeviceType.WATER_HEATER,
            status=DeviceStatus.ONLINE,
            target_temperature=50.0,
            current_temperature=45.5,
            mode=WaterHeaterMode.ECO,
            heater_status=WaterHeaterStatus.HEATING,
        )

        # Create a reading
        reading = WaterHeaterReading(
            timestamp=datetime.now(),
            temperature=48.5,
            pressure=2.2,
            energy_usage=120.5,
            flow_rate=5.5,
        )

        # Add reading to water heater
        water_heater.add_reading(reading)

        # Verify reading was added
        assert len(water_heater.readings) == 1
        assert water_heater.readings[0].temperature == 48.5

        # Verify current temperature was updated
        assert water_heater.current_temperature == 48.5
