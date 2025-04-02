"""
Service for water heater devices.

This service follows TDD principles and supports configurable data sources
through dependency injection or environment variables.
"""
import uuid
import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

# Use absolute imports to work both from project root or from src/
from src.models.device import DeviceStatus
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterMode,
    WaterHeaterStatus,
    WaterHeaterReading
)
from src.repositories.water_heater_repository import (
    WaterHeaterRepository,
    MockWaterHeaterRepository,
    SQLiteWaterHeaterRepository
)
from src.utils.dummy_data import dummy_data

# Setup logging
logger = logging.getLogger(__name__)

class WaterHeaterService:
    """Service for water heater operations with database support"""
    
    def __init__(self, repository: Optional[WaterHeaterRepository] = None):
        """
        Initialize the service with a repository.
        
        Args:
            repository: Water heater repository implementation.
                      If None, uses environment variable to determine repository.
        """
        if repository:
            self.repository = repository
        else:
            # Determine repository based on environment variable
            use_mock_data = os.environ.get("USE_MOCK_DATA", "True").lower() in ["true", "1", "yes"]
            
            if use_mock_data:
                logger.info("Using mock data repository for water heaters")
                self.repository = MockWaterHeaterRepository()
            else:
                logger.info("Using SQLite repository for water heaters")
                self.repository = SQLiteWaterHeaterRepository()
    
    async def get_water_heaters(self) -> List[WaterHeater]:
        """Get all water heaters"""
        try:
            return await self.repository.get_water_heaters()
        except Exception as e:
            logger.error(f"Error getting water heaters: {e}")
            # Fallback to dummy data if database fails
            logger.warning("Falling back to dummy data for water heaters")
            return dummy_data.get_water_heaters()
    
    async def get_water_heater(self, device_id: str) -> Optional[WaterHeater]:
        """Get a specific water heater by ID"""
        try:
            water_heater = await self.repository.get_water_heater(device_id)
            if water_heater:
                return water_heater
            
            # If not found in repository, try dummy data
            logger.warning(f"Water heater {device_id} not found in repository, falling back to dummy data")
            return dummy_data.get_water_heater(device_id)
        except Exception as e:
            logger.error(f"Error getting water heater {device_id}: {e}")
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
        try:
            return await self.repository.create_water_heater(water_heater)
        except Exception as e:
            logger.error(f"Error creating water heater: {e}")
            # Fallback to dummy data
            return dummy_data.add_water_heater(water_heater)
    
    async def update_target_temperature(self, device_id: str, temperature: float) -> Optional[WaterHeater]:
        """Update a water heater's target temperature"""
        try:
            # Get water heater from repository
            water_heater = await self.repository.get_water_heater(device_id)
            if not water_heater:
                # Try dummy data as fallback
                water_heater = dummy_data.get_water_heater(device_id)
                if not water_heater:
                    return None
            
            # Validate temperature range
            min_temp = getattr(water_heater, 'min_temperature', 40.0)
            max_temp = getattr(water_heater, 'max_temperature', 80.0)
            if temperature < min_temp or temperature > max_temp:
                raise ValueError(f"Temperature must be between {min_temp} and {max_temp}")
            
            # Update the water heater
            updates = {
                "target_temperature": temperature,
                "last_seen": datetime.now().isoformat()
            }
            
            # If current temperature is much lower than target, set to heating
            if water_heater.current_temperature < temperature - 1.0:
                updates["status"] = WaterHeaterStatus.HEATING.value
            elif getattr(water_heater, 'status', '') == WaterHeaterStatus.HEATING.value and water_heater.current_temperature >= temperature:
                updates["status"] = WaterHeaterStatus.STANDBY.value
            
            # Update in repository
            return await self.repository.update_water_heater(device_id, updates)
        except Exception as e:
            logger.error(f"Error updating water heater temperature: {e}")
            # Fallback to dummy data
            water_heater = dummy_data.get_water_heater(device_id)
            if not water_heater:
                return None
                
            updates = {
                "target_temperature": temperature,
                "last_seen": datetime.now()
            }
            
            if water_heater.current_temperature < temperature - 1.0:
                updates["heater_status"] = WaterHeaterStatus.HEATING
            elif water_heater.heater_status == WaterHeaterStatus.HEATING and water_heater.current_temperature >= temperature:
                updates["heater_status"] = WaterHeaterStatus.STANDBY
            
            return dummy_data.update_water_heater(device_id, updates)
    
    async def update_mode(self, device_id: str, mode: WaterHeaterMode) -> Optional[WaterHeater]:
        """Update a water heater's operational mode"""
        try:
            # Get water heater from repository
            water_heater = await self.repository.get_water_heater(device_id)
            if not water_heater:
                # Try dummy data as fallback
                water_heater = dummy_data.get_water_heater(device_id)
                if not water_heater:
                    return None
            
            # Update the water heater
            updates = {
                "mode": mode.value if hasattr(mode, 'value') else mode,
                "last_seen": datetime.now().isoformat()
            }
            
            # If switching to OFF mode, set status to standby
            if mode == WaterHeaterMode.OFF:
                updates["status"] = WaterHeaterStatus.STANDBY.value
            # If switching to BOOST, set to heating
            elif mode == WaterHeaterMode.BOOST:
                updates["status"] = WaterHeaterStatus.HEATING.value
                
            # Adjust temperature based on mode
            if mode == WaterHeaterMode.ECO and water_heater.target_temperature > 55.0:
                updates["target_temperature"] = 55.0  # Cap at 55°C for eco mode
            elif mode == WaterHeaterMode.BOOST and water_heater.target_temperature < 65.0:
                updates["target_temperature"] = 65.0  # Boost to at least 65°C
            
            # Update in repository
            return await self.repository.update_water_heater(device_id, updates)
        except Exception as e:
            logger.error(f"Error updating water heater mode: {e}")
            # Fallback to dummy data
            water_heater = dummy_data.get_water_heater(device_id)
            if not water_heater:
                return None
                
            updates = {
                "mode": mode,
                "last_seen": datetime.now()
            }
            
            if mode == WaterHeaterMode.OFF:
                updates["heater_status"] = WaterHeaterStatus.STANDBY
            elif mode == WaterHeaterMode.BOOST:
                updates["heater_status"] = WaterHeaterStatus.HEATING
            
            return dummy_data.update_water_heater(device_id, updates)
    
    async def add_temperature_reading(self, device_id: str, temperature: float,
                                     pressure: Optional[float] = None,
                                     energy_usage: Optional[float] = None,
                                     flow_rate: Optional[float] = None) -> Optional[WaterHeater]:
        """Add a new temperature reading to a water heater"""
        try:
            # Get water heater from repository
            water_heater = await self.repository.get_water_heater(device_id)
            if not water_heater:
                # Try dummy data as fallback
                water_heater = dummy_data.get_water_heater(device_id)
                if not water_heater:
                    return None
            
            # Create a new reading
            now = datetime.now()
            reading = WaterHeaterReading(
                id=str(uuid.uuid4()),
                device_id=device_id,
                timestamp=now,
                temperature=temperature,
                pressure=pressure,
                energy_usage=energy_usage,
                flow_rate=flow_rate
            )
            
            # Determine heater status based on temperature
            target_temp = water_heater.target_temperature if hasattr(water_heater, 'target_temperature') else 50.0
            new_status = WaterHeaterStatus.HEATING if temperature < target_temp - 1.0 else WaterHeaterStatus.STANDBY
            
            # Update the water heater
            updates = {
                "current_temperature": temperature,
                "last_seen": now.isoformat(),
                "status": new_status.value
            }
            
            # Add the reading to the database
            try:
                await self.repository.add_reading(reading)
            except Exception as e:
                logger.error(f"Error adding reading to database: {e}")
            
            # Update water heater in repository
            return await self.repository.update_water_heater(device_id, updates)
        except Exception as e:
            logger.error(f"Error adding temperature reading: {e}")
            # Fallback to dummy data
            water_heater = dummy_data.get_water_heater(device_id)
            if not water_heater:
                return None
                
            # Create a new reading for dummy data
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
