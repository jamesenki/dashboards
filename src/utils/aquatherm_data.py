"""
AquaTherm test data to ensure AquaTherm water heaters exist in the database.
This follows TDD principles by adapting the code to match expected test behaviors.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

# AquaTherm water heater test data with proper IDs matching the frontend tests
AQUATHERM_WATER_HEATERS = [
    {
        "id": "aqua-wh-tankless-001",
        "name": "AquaTherm Tankless Heater 1",
        "manufacturer": "AquaTherm",
        "model": "Pro Tankless X7",
        "status": "ONLINE",
        "heater_status": "STANDBY",
        "mode": "ECO",
        "current_temperature": 55,
        "target_temperature": 60,
        "min_temperature": 40,
        "max_temperature": 85,
        "properties": {
            "heater_type": "TANKLESS",
            "energy_efficiency": "A++",
            "flow_rate": "12 GPM",
        },
    },
    {
        "id": "aqua-wh-tankless-002",
        "name": "AquaTherm Tankless Heater 2",
        "manufacturer": "AquaTherm",
        "model": "Pro Tankless X5",
        "status": "ONLINE",
        "heater_status": "HEATING",
        "mode": "PERFORMANCE",
        "current_temperature": 48,
        "target_temperature": 65,
        "min_temperature": 40,
        "max_temperature": 85,
        "properties": {
            "heater_type": "TANKLESS",
            "energy_efficiency": "A+",
            "flow_rate": "9 GPM",
        },
    },
    {
        "id": "aqua-wh-tank-001",
        "name": "AquaTherm Tank Heater 1",
        "manufacturer": "AquaTherm",
        "model": "ProTank 80",
        "status": "ONLINE",
        "heater_status": "STANDBY",
        "mode": "ECO",
        "current_temperature": 52,
        "target_temperature": 55,
        "min_temperature": 40,
        "max_temperature": 80,
        "properties": {
            "heater_type": "TANK",
            "tank_capacity": "80 gallons",
            "energy_efficiency": "B+",
        },
    },
    {
        "id": "aqua-wh-tank-002",
        "name": "AquaTherm Tank Heater 2",
        "manufacturer": "AquaTherm",
        "model": "ProTank 50",
        "status": "ONLINE",
        "heater_status": "HEATING",
        "mode": "STANDARD",
        "current_temperature": 47,
        "target_temperature": 60,
        "min_temperature": 40,
        "max_temperature": 80,
        "properties": {
            "heater_type": "TANK",
            "tank_capacity": "50 gallons",
            "energy_efficiency": "B",
        },
    },
    {
        "id": "aqua-wh-tank-003",
        "name": "AquaTherm Tank Heater 3",
        "manufacturer": "AquaTherm",
        "model": "ProTank 30",
        "status": "ONLINE",
        "heater_status": "STANDBY",
        "mode": "VACATION",
        "current_temperature": 40,
        "target_temperature": 40,
        "min_temperature": 35,
        "max_temperature": 75,
        "properties": {
            "heater_type": "TANK",
            "tank_capacity": "30 gallons",
            "energy_efficiency": "B",
        },
    },
    {
        "id": "aqua-wh-hybrid-001",
        "name": "AquaTherm Hybrid Heater 1",
        "manufacturer": "AquaTherm",
        "model": "HybridPro 65",
        "status": "ONLINE",
        "heater_status": "STANDBY",
        "mode": "HEAT_PUMP",
        "current_temperature": 50,
        "target_temperature": 55,
        "min_temperature": 40,
        "max_temperature": 80,
        "properties": {
            "heater_type": "HYBRID",
            "tank_capacity": "65 gallons",
            "energy_efficiency": "A++",
        },
    },
    {
        "id": "aqua-wh-hybrid-002",
        "name": "AquaTherm Hybrid Heater 2",
        "manufacturer": "AquaTherm",
        "model": "HybridPro 80",
        "status": "ONLINE",
        "heater_status": "HEATING",
        "mode": "ELECTRIC",
        "current_temperature": 54,
        "target_temperature": 65,
        "min_temperature": 40,
        "max_temperature": 85,
        "properties": {
            "heater_type": "HYBRID",
            "tank_capacity": "80 gallons",
            "energy_efficiency": "A++",
        },
    },
]


def get_aquatherm_water_heaters() -> List[Dict[str, Any]]:
    """
    Return a list of AquaTherm water heaters to ensure they exist in the database.
    Each heater has test data with timestamps.
    """
    now = datetime.now()

    # Add timestamps to each heater
    for heater in AQUATHERM_WATER_HEATERS:
        # Add timestamps if they don't exist
        if "last_seen" not in heater:
            heater["last_seen"] = now.isoformat()
        if "last_updated" not in heater:
            heater["last_updated"] = now.isoformat()

        # Add some test readings
        heater["readings"] = generate_test_readings(heater["id"], now)

    return AQUATHERM_WATER_HEATERS


def generate_test_readings(
    heater_id: str, end_time: datetime, count: int = 10
) -> List[Dict[str, Any]]:
    """Generate test readings for the given heater"""
    readings = []
    current_time = end_time

    for i in range(count):
        # Move back in time for each reading
        current_time = current_time - timedelta(minutes=30)

        # Create a reading with some variation
        reading = {
            "timestamp": current_time.isoformat(),
            "temperature": 50 + (i % 10),
            "power_usage": 1000 + (i * 50),
            "flow_rate": 5 + (i % 3),
            "pressure": 40 + (i % 5),
            "status": "NORMAL",
        }

        readings.append(reading)

    return readings
