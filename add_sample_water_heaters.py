"""
Script to add sample water heaters to the database.
"""
import asyncio
import os
from datetime import datetime
import uuid

from src.models.device import DeviceStatus, DeviceType
from src.models.water_heater import WaterHeater, WaterHeaterMode, WaterHeaterStatus
from src.repositories.water_heater_repository import SQLiteWaterHeaterRepository

# Ensure we use the database (not mock data)
os.environ["USE_MOCK_DATA"] = "False"

async def create_sample_water_heaters():
    """Create sample water heaters with varied data."""
    repo = SQLiteWaterHeaterRepository()
    
    # Sample water heaters with varied but realistic data
    water_heaters = [
        WaterHeater(
            id=f"wh-{uuid.uuid4().hex[:8]}",
            name="Residential Water Heater",
            type=DeviceType.WATER_HEATER,
            current_temperature=48.7,
            target_temperature=50.0,
            min_temperature=40.0,
            max_temperature=80.0,
            mode=WaterHeaterMode.ECO,
            status=DeviceStatus.ONLINE,
            heater_status=WaterHeaterStatus.HEATING,
            location="Building A - Apartment 101",
            last_seen=datetime.now()
        ),
        WaterHeater(
            id=f"wh-{uuid.uuid4().hex[:8]}",
            name="Commercial Kitchen Heater",
            type=DeviceType.WATER_HEATER,
            current_temperature=65.2,
            target_temperature=65.0,
            min_temperature=60.0,
            max_temperature=85.0,
            mode=WaterHeaterMode.BOOST,
            status=DeviceStatus.ONLINE,
            heater_status=WaterHeaterStatus.STANDBY,
            location="Building B - Kitchen",
            last_seen=datetime.now()
        ),
        WaterHeater(
            id=f"wh-{uuid.uuid4().hex[:8]}",
            name="Energy Saving Heater",
            type=DeviceType.WATER_HEATER,
            current_temperature=42.5,
            target_temperature=45.0,
            min_temperature=35.0,
            max_temperature=75.0,
            mode=WaterHeaterMode.ECO,
            status=DeviceStatus.ONLINE,
            heater_status=WaterHeaterStatus.HEATING,
            location="Building C - Basement",
            last_seen=datetime.now()
        ),
        WaterHeater(
            id=f"wh-{uuid.uuid4().hex[:8]}",
            name="Maintenance Mode Heater",
            type=DeviceType.WATER_HEATER,
            current_temperature=20.0,
            target_temperature=40.0,
            min_temperature=15.0,
            max_temperature=70.0,
            mode=WaterHeaterMode.OFF,
            status=DeviceStatus.MAINTENANCE,
            heater_status=WaterHeaterStatus.STANDBY,
            location="Building D - Utility Room",
            last_seen=datetime.now()
        )
    ]
    
    # Add to database
    for water_heater in water_heaters:
        print(f"Creating water heater: {water_heater.name}")
        await repo.create_water_heater(water_heater)
    
    print(f"Added {len(water_heaters)} water heaters to the database")
    
    # Also add a health configuration
    health_config = {
        "temperature_high": {
            "threshold": 75.0,
            "status": "RED"
        },
        "temperature_warning": {
            "threshold": 65.0,
            "status": "YELLOW"
        }
    }
    
    print("Setting health configuration")
    await repo.set_health_configuration(health_config)
    
    # Add an alert rule
    alert_rule = {
        "name": "High Temperature Alert",
        "condition": "temperature > 70",
        "severity": "HIGH",
        "message": "Water temperature exceeds safe level",
        "enabled": True
    }
    
    print("Adding alert rule")
    await repo.add_alert_rule(alert_rule)
    
    print("Done!")

if __name__ == "__main__":
    asyncio.run(create_sample_water_heaters())
