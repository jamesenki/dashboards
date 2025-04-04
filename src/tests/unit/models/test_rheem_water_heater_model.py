"""
Test cases for updated Rheem water heater models.
"""
from datetime import datetime

import pytest

from src.models.device import DeviceType
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterMode,
    WaterHeaterReading,
    WaterHeaterStatus,
    WaterHeaterType,
)


class TestRheemWaterHeaterModel:
    """Test cases for water heater models updated to match Rheem specifications."""

    def test_water_heater_mode_enum_rheem_modes(self):
        """Test the WaterHeaterMode enum has Rheem-specific modes."""
        assert hasattr(WaterHeaterMode, "ENERGY_SAVER")
        assert hasattr(WaterHeaterMode, "HEAT_PUMP")
        assert hasattr(WaterHeaterMode, "ELECTRIC")
        assert hasattr(WaterHeaterMode, "VACATION")
        assert hasattr(WaterHeaterMode, "HIGH_DEMAND")

        # Test that values are correctly mapped
        assert WaterHeaterMode.ENERGY_SAVER == "ENERGY_SAVER"
        assert WaterHeaterMode.HEAT_PUMP == "HEAT_PUMP"
        assert WaterHeaterMode.ELECTRIC == "ELECTRIC"
        assert WaterHeaterMode.VACATION == "VACATION"
        assert WaterHeaterMode.HIGH_DEMAND == "HIGH_DEMAND"

        # Test the enum still has original modes for backward compatibility
        assert hasattr(WaterHeaterMode, "ECO")
        assert hasattr(WaterHeaterMode, "BOOST")
        assert hasattr(WaterHeaterMode, "OFF")

    def test_water_heater_model_rheem_attributes(self):
        """Test water heater model with Rheem-specific attributes."""
        # Create a water heater with Rheem attributes
        water_heater = WaterHeater(
            id="rheem-123",
            name="ProTerra Hybrid Water Heater",
            location="Basement",
            manufacturer="Rheem",
            model="ProTerra",
            firmware_version="2.1.5",
            status="ONLINE",
            target_temperature=50.0,
            current_temperature=48.0,
            min_temperature=35.0,
            max_temperature=85.0,
            mode=WaterHeaterMode.ENERGY_SAVER,
            heater_status=WaterHeaterStatus.STANDBY,
            heater_type=WaterHeaterType.HYBRID,
            # Rheem-specific attributes
            series="ProTerra",
            energy_efficiency_rating=4.0,  # UEF rating
            capacity=50.0,  # in gallons
            smart_enabled=True,  # EcoNet enabled
            leak_detection=True,
            wifi_status="CONNECTED",
            warranty_info="10 year limited warranty",
            installation_date=datetime(2023, 1, 15),
            last_maintenance_date=datetime(2024, 2, 20),
        )

        # Verify Rheem-specific attributes
        assert water_heater.series == "ProTerra"
        assert water_heater.energy_efficiency_rating == 4.0
        assert water_heater.capacity == 50.0
        assert water_heater.smart_enabled is True
        assert water_heater.leak_detection is True
        assert water_heater.wifi_status == "CONNECTED"
        assert water_heater.warranty_info == "10 year limited warranty"
        assert water_heater.installation_date == datetime(2023, 1, 15)
        assert water_heater.last_maintenance_date == datetime(2024, 2, 20)

        # Verify standard attributes still work
        assert water_heater.id == "rheem-123"
        assert water_heater.name == "ProTerra Hybrid Water Heater"
        assert water_heater.target_temperature == 50.0
        assert water_heater.mode == WaterHeaterMode.ENERGY_SAVER
        assert water_heater.heater_type == WaterHeaterType.HYBRID

    def test_water_heater_telemetry_rheem_attributes(self):
        """Test water heater telemetry with Rheem-specific attributes."""
        # Create telemetry with Rheem-specific readings
        reading = WaterHeaterReading(
            timestamp=datetime.now(),
            temperature=50.5,
            pressure=2.5,
            energy_usage=250.0,
            flow_rate=6.5,
            # Rheem-specific readings
            inlet_temperature=18.5,
            outlet_temperature=49.5,
            ambient_temperature=22.0,
            humidity=40.5,
            heating_element_status="ON",
            compressor_status="OFF",  # For hybrid models
            power_source="HEAT_PUMP",  # Current power source being used
            wifi_signal_strength=85,  # Signal strength percentage
            total_energy_used=1250.5,  # Cumulative energy consumption
        )

        # Verify Rheem-specific attributes
        assert reading.inlet_temperature == 18.5
        assert reading.outlet_temperature == 49.5
        assert reading.ambient_temperature == 22.0
        assert reading.humidity == 40.5
        assert reading.heating_element_status == "ON"
        assert reading.compressor_status == "OFF"
        assert reading.power_source == "HEAT_PUMP"
        assert reading.wifi_signal_strength == 85
        assert reading.total_energy_used == 1250.5

        # Verify standard attributes still work
        assert reading.temperature == 50.5
        assert reading.pressure == 2.5
        assert reading.energy_usage == 250.0
        assert reading.flow_rate == 6.5
