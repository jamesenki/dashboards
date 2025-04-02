"""
Test module for enhanced water heater model with type and diagnostic codes.
"""
from datetime import datetime
from typing import List, Optional

import pytest

from src.models.device import DeviceStatus, DeviceType
from src.models.water_heater import (
    WaterHeaterDiagnosticCode,  # This will be added to the model
)
from src.models.water_heater import WaterHeaterType  # This will be added to the model
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterMode,
    WaterHeaterReading,
    WaterHeaterStatus,
)


@pytest.mark.tdd_red
def test_water_heater_type():
    """Test that water heater can be created with a specific type (Commercial/Residential)."""
    # Create a commercial water heater
    commercial_heater = WaterHeater(
        id="wh-comm-001",
        name="Building A Boiler Room - ThermoGuard Industrial-1500",
        type=DeviceType.WATER_HEATER,
        status=DeviceStatus.ONLINE,
        location="Building A - Boiler Room",
        target_temperature=65.0,
        current_temperature=63.5,
        mode=WaterHeaterMode.ECO,
        heater_status=WaterHeaterStatus.HEATING,
        heater_type=WaterHeaterType.COMMERCIAL,  # New field
        capacity=1500.0,
        efficiency_rating=0.95,
        max_temperature=85.0,
    )

    # Create a residential water heater
    residential_heater = WaterHeater(
        id="wh-res-001",
        name="Apartment 101 - EcoHeat Family-80",
        type=DeviceType.WATER_HEATER,
        status=DeviceStatus.ONLINE,
        location="Apartment 101 - Bathroom",
        target_temperature=55.0,
        current_temperature=54.0,
        mode=WaterHeaterMode.ECO,
        heater_status=WaterHeaterStatus.HEATING,
        heater_type=WaterHeaterType.RESIDENTIAL,  # New field
        capacity=80.0,
        efficiency_rating=0.90,
        max_temperature=75.0,
    )

    # Verify types are correctly set
    assert commercial_heater.heater_type == WaterHeaterType.COMMERCIAL
    assert residential_heater.heater_type == WaterHeaterType.RESIDENTIAL

    # Verify other properties specific to each type
    assert commercial_heater.max_temperature == 85.0
    assert residential_heater.max_temperature == 75.0


@pytest.mark.tdd_red
def test_water_heater_diagnostic_codes():
    """Test that water heaters can track diagnostic codes."""
    # Create a water heater
    heater = WaterHeater(
        id="wh-test-001",
        name="Test Water Heater",
        type=DeviceType.WATER_HEATER,
        status=DeviceStatus.ONLINE,
        location="Test Location",
        target_temperature=60.0,
        current_temperature=58.5,
        mode=WaterHeaterMode.ECO,
        heater_status=WaterHeaterStatus.HEATING,
        heater_type=WaterHeaterType.COMMERCIAL,
        diagnostic_codes=[],  # New field for tracking active diagnostic codes
    )

    # Add diagnostic codes
    heater.add_diagnostic_code(
        WaterHeaterDiagnosticCode(
            code="C001",
            description="High temperature warning",
            severity="Warning",
            timestamp=datetime.now(),
            active=True,
        )
    )

    heater.add_diagnostic_code(
        WaterHeaterDiagnosticCode(
            code="C006",
            description="Control board communication error",
            severity="Warning",
            timestamp=datetime.now(),
            active=True,
        )
    )

    # Check that diagnostic codes were added
    assert len(heater.diagnostic_codes) == 2
    assert heater.diagnostic_codes[0].code == "C001"
    assert heater.diagnostic_codes[1].code == "C006"

    # Resolve a diagnostic code
    heater.resolve_diagnostic_code("C001")

    # Check that code is marked as inactive but still in history
    assert len(heater.diagnostic_codes) == 2
    assert not heater.diagnostic_codes[0].active
    assert heater.diagnostic_codes[1].active

    # Check active diagnostic codes method
    active_codes = heater.get_active_diagnostic_codes()
    assert len(active_codes) == 1
    assert active_codes[0].code == "C006"


@pytest.mark.tdd_red
def test_water_heater_specification_link():
    """Test that water heaters can be linked to their specifications."""
    # Create a commercial water heater
    commercial_heater = WaterHeater(
        id="wh-comm-001",
        name="Building A Boiler Room - ThermoGuard Industrial-1500",
        type=DeviceType.WATER_HEATER,
        status=DeviceStatus.ONLINE,
        location="Building A - Boiler Room",
        target_temperature=65.0,
        current_temperature=63.5,
        mode=WaterHeaterMode.ECO,
        heater_status=WaterHeaterStatus.HEATING,
        heater_type=WaterHeaterType.COMMERCIAL,
        specification_link="/docs/specifications/water_heaters/commercial.md",  # New field
    )

    # Create a residential water heater
    residential_heater = WaterHeater(
        id="wh-res-001",
        name="Apartment 101 - EcoHeat Family-80",
        type=DeviceType.WATER_HEATER,
        status=DeviceStatus.ONLINE,
        location="Apartment 101 - Bathroom",
        target_temperature=55.0,
        current_temperature=54.0,
        mode=WaterHeaterMode.ECO,
        heater_status=WaterHeaterStatus.HEATING,
        heater_type=WaterHeaterType.RESIDENTIAL,
        specification_link="/docs/specifications/water_heaters/residential.md",  # New field
    )

    # Verify specification links are correctly set
    assert (
        commercial_heater.specification_link
        == "/docs/specifications/water_heaters/commercial.md"
    )
    assert (
        residential_heater.specification_link
        == "/docs/specifications/water_heaters/residential.md"
    )
