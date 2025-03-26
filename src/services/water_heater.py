"""
Service for water heater devices
"""
import uuid
from datetime import datetime
from typing import List, Optional

# Use absolute imports to work both from project root or from src/
from src.models.device import DeviceStatus
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterMode,
    WaterHeaterStatus,
    WaterHeaterReading
)
from src.utils.dummy_data import dummy_data

class WaterHeaterService:
    """Service for water heater operations"""
    
    async def get_water_heaters(self) -> List[WaterHeater]:
        """Get all water heaters"""
        return dummy_data.get_water_heaters()
    
    async def get_water_heater(self, device_id: str) -> Optional[WaterHeater]:
        """Get a specific water heater by ID"""
        return dummy_data.get_water_heater(device_id)
    
    async def create_water_heater(self, water_heater: WaterHeater) -> WaterHeater:
        """Create a new water heater"""
        # Generate ID if not provided
        if not water_heater.id:
            water_heater.id = f"wh-{str(uuid.uuid4())[:8]}"
        
        # Set creation timestamp
        if not water_heater.last_seen:
            water_heater.last_seen = datetime.now()
        
        # Initialize readings if not provided
        if not water_heater.readings:
            water_heater.readings = []
        
        # Add to repository
        return dummy_data.add_water_heater(water_heater)
    
    async def update_target_temperature(self, device_id: str, temperature: float) -> Optional[WaterHeater]:
        """Update a water heater's target temperature"""
        water_heater = dummy_data.get_water_heater(device_id)
        if not water_heater:
            return None
        
        # Validate temperature range
        if temperature < water_heater.min_temperature or temperature > water_heater.max_temperature:
            raise ValueError(f"Temperature must be between {water_heater.min_temperature} and {water_heater.max_temperature}")
        
        # Update the water heater
        updates = {
            "target_temperature": temperature,
            "last_seen": datetime.now()
        }
        
        # If current temperature is much lower than target, set to heating
        if water_heater.current_temperature < temperature - 1.0:
            updates["heater_status"] = WaterHeaterStatus.HEATING
        elif water_heater.heater_status == WaterHeaterStatus.HEATING and water_heater.current_temperature >= temperature:
            updates["heater_status"] = WaterHeaterStatus.STANDBY
        
        return dummy_data.update_water_heater(device_id, updates)
    
    async def update_mode(self, device_id: str, mode: WaterHeaterMode) -> Optional[WaterHeater]:
        """Update a water heater's operational mode"""
        water_heater = dummy_data.get_water_heater(device_id)
        if not water_heater:
            return None
        
        # Update the water heater
        updates = {
            "mode": mode,
            "last_seen": datetime.now()
        }
        
        # If switching to OFF mode, set status to standby
        if mode == WaterHeaterMode.OFF:
            updates["heater_status"] = WaterHeaterStatus.STANDBY
        # If switching to BOOST, set to heating
        elif mode == WaterHeaterMode.BOOST:
            updates["heater_status"] = WaterHeaterStatus.HEATING
        
        return dummy_data.update_water_heater(device_id, updates)
    
    async def add_temperature_reading(self, device_id: str, temperature: float,
                                     pressure: Optional[float] = None,
                                     energy_usage: Optional[float] = None,
                                     flow_rate: Optional[float] = None) -> Optional[WaterHeater]:
        """Add a new temperature reading to a water heater"""
        water_heater = dummy_data.get_water_heater(device_id)
        if not water_heater:
            return None
        
        # Create a new reading
        now = datetime.now()
        reading = WaterHeaterReading(
            timestamp=now,
            temperature=temperature,
            pressure=pressure,
            energy_usage=energy_usage,
            flow_rate=flow_rate
        )
        
        # Add the reading and update the current temperature
        readings = water_heater.readings.copy() if water_heater.readings else []
        readings.append(reading)
        
        # Keep only the last 100 readings
        if len(readings) > 100:
            readings = readings[-100:]
        
        # Update the water heater
        updates = {
            "current_temperature": temperature,
            "readings": readings,
            "last_seen": now
        }
        
        # Update heater status based on temperature
        if temperature < water_heater.target_temperature - 1.0:
            updates["heater_status"] = WaterHeaterStatus.HEATING
        elif water_heater.heater_status == WaterHeaterStatus.HEATING and temperature >= water_heater.target_temperature:
            updates["heater_status"] = WaterHeaterStatus.STANDBY
        
        return dummy_data.update_water_heater(device_id, updates)
