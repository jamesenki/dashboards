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
        "manufacturer": "Rheem",
        "model": "Professional Tankless X7",
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
        "manufacturer": "Rheem",
        "model": "Performance Tankless X5",
        "status": "ONLINE",
        "heater_status": "HEATING",
        "mode": "HIGH_DEMAND",
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
        "manufacturer": "Rheem",
        "model": "Professional Tank 80",
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
        "manufacturer": "Rheem",
        "model": "Performance Tank 50",
        "status": "ONLINE",
        "heater_status": "HEATING",
        "mode": "ENERGY_SAVER",
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
        "manufacturer": "Rheem",
        "model": "Classic Tank 30",
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
        "manufacturer": "Rheem",
        "model": "HybridPro 65",
        "status": "ONLINE",
        "heater_status": "STANDBY",
        "mode": "BOOST",
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
        "manufacturer": "Rheem",
        "model": "HybridPro 80",
        "status": "ONLINE",
        "heater_status": "HEATING",
        "mode": "HIGH_DEMAND",
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
    {
        "id": "aqua-wh-tank-004",
        "name": "Rheem Commercial Tank",
        "manufacturer": "Rheem",
        "model": "Professional Tank 100",
        "status": "ONLINE",
        "heater_status": "HEATING",
        "mode": "HIGH_DEMAND",
        "current_temperature": 55,
        "target_temperature": 65,
        "min_temperature": 40,
        "max_temperature": 85,
        "properties": {
            "heater_type": "TANK",
            "tank_capacity": "100 gallons",
            "energy_efficiency": "A",
        },
    },
    {
        "id": "aqua-wh-tank-005",
        "name": "Rheem Professional Plus",
        "manufacturer": "Rheem",
        "model": "Professional Plus 75",
        "status": "ONLINE",
        "heater_status": "STANDBY",
        "mode": "ECO",
        "current_temperature": 50,
        "target_temperature": 52,
        "min_temperature": 40,
        "max_temperature": 80,
        "properties": {
            "heater_type": "TANK",
            "tank_capacity": "75 gallons",
            "energy_efficiency": "A+",
        },
    },
    {
        "id": "aqua-wh-hybrid-003",
        "name": "Rheem Hybrid Heater 3",
        "manufacturer": "Rheem",
        "model": "Professional Hybrid 50",
        "status": "ONLINE",
        "heater_status": "HEATING",
        "mode": "BOOST",
        "current_temperature": 48,
        "target_temperature": 55,
        "min_temperature": 40,
        "max_temperature": 80,
        "properties": {
            "heater_type": "HYBRID",
            "tank_capacity": "50 gallons",
            "energy_efficiency": "A+++",
        },
    },
    {
        "id": "aqua-wh-hybrid-004",
        "name": "Rheem Hybrid Heater 4",
        "manufacturer": "Rheem",
        "model": "Performance Hybrid 65",
        "status": "ONLINE",
        "heater_status": "STANDBY",
        "mode": "ECO",
        "current_temperature": 52,
        "target_temperature": 52,
        "min_temperature": 40,
        "max_temperature": 80,
        "properties": {
            "heater_type": "HYBRID",
            "tank_capacity": "65 gallons",
            "energy_efficiency": "A++",
        },
    },
    {
        "id": "aqua-wh-hybrid-005",
        "name": "Rheem ProTerra Hybrid",
        "manufacturer": "Rheem",
        "model": "ProTerra Hybrid 80",
        "status": "ONLINE",
        "heater_status": "HEATING",
        "mode": "BOOST",
        "current_temperature": 49,
        "target_temperature": 60,
        "min_temperature": 40,
        "max_temperature": 85,
        "properties": {
            "heater_type": "HYBRID",
            "tank_capacity": "80 gallons",
            "energy_efficiency": "A+++",
        },
    },
    {
        "id": "aqua-wh-tankless-003",
        "name": "Rheem Tankless Prestige",
        "manufacturer": "Rheem",
        "model": "Prestige Tankless X9",
        "status": "ONLINE",
        "heater_status": "STANDBY",
        "mode": "ECO",
        "current_temperature": 54,
        "target_temperature": 54,
        "min_temperature": 40,
        "max_temperature": 85,
        "properties": {
            "heater_type": "TANKLESS",
            "energy_efficiency": "A+++",
            "flow_rate": "15 GPM",
        },
    },
    {
        "id": "aqua-wh-tankless-004",
        "name": "Rheem Tankless Compact",
        "manufacturer": "Rheem",
        "model": "Classic Tankless X3",
        "status": "ONLINE",
        "heater_status": "HEATING",
        "mode": "ENERGY_SAVER",
        "current_temperature": 50,
        "target_temperature": 60,
        "min_temperature": 40,
        "max_temperature": 80,
        "properties": {
            "heater_type": "TANKLESS",
            "energy_efficiency": "A",
            "flow_rate": "7 GPM",
        },
    },
    {
        "id": "aqua-wh-tank-006",
        "name": "Rheem Classic Plus",
        "manufacturer": "Rheem",
        "model": "Classic Plus 40",
        "status": "ONLINE",
        "heater_status": "STANDBY",
        "mode": "ECO",
        "current_temperature": 45,
        "target_temperature": 50,
        "min_temperature": 40,
        "max_temperature": 75,
        "properties": {
            "heater_type": "TANK",
            "tank_capacity": "40 gallons",
            "energy_efficiency": "B+",
        },
    },
]


def get_aquatherm_water_heaters() -> List[Dict[str, Any]]:
    """
    Return a list of AquaTherm (Rheem) water heaters to ensure they exist in the database.
    Each heater has test data with timestamps and all have Rheem as manufacturer.
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
