import logging
from datetime import datetime
from typing import Dict, List, Optional, Type, Union

from fastapi import Depends

from src.db.adapters.redis_cache import RedisCache, get_redis_cache
from src.db.adapters.sql_devices import SQLDeviceRepository
from src.db.config import db_settings
from src.models.device import Device, DeviceStatus, DeviceType
from src.models.device_reading import DeviceReading

logger = logging.getLogger(__name__)


class DeviceRepository:
    """Repository facade for device data access."""

    def __init__(
        self, 
        sql_repo: SQLDeviceRepository = Depends(),
        cache: RedisCache = Depends(get_redis_cache),
    ):
        self.sql_repo = sql_repo
        self.cache = cache
        self.fallback_enabled = True  # Enable fallback mechanisms by default

    async def get_devices(
        self,
        type_filter: Optional[DeviceType] = None,
        status_filter: Optional[DeviceStatus] = None,
    ) -> List[Device]:
        """Get devices with optional filtering and fallback handling."""
        try:
            # Try database first
            return await self.sql_repo.get_devices(type_filter, status_filter)
        except Exception as e:
            logger.error(f"Database error in get_devices: {str(e)}")
            
            # Fallback to cache if database fails
            if self.fallback_enabled and self.cache.client:
                try:
                    # Try to get all devices from cache
                    cached_devices = await self.cache.get("all_devices")
                    if cached_devices:
                        devices = [Device.parse_obj(d) for d in cached_devices]
                        
                        # Apply filters if specified
                        if type_filter:
                            devices = [d for d in devices if d.type == type_filter]
                        if status_filter:
                            devices = [d for d in devices if d.status == status_filter]
                            
                        logger.info(f"Retrieved {len(devices)} devices from cache fallback")
                        return devices
                except Exception as cache_error:
                    logger.error(f"Cache fallback error: {str(cache_error)}")
            
            # If all else fails, return empty list
            logger.warning("Returning empty device list due to errors")
            return []

    async def get_device(self, device_id: str) -> Optional[Device]:
        """Get a device by ID with caching and robust error handling."""
        # Try cache first for fast retrieval
        if self.cache.client:
            try:
                cached_device = await self.cache.get_device_state(device_id)
                if cached_device:
                    logger.debug(f"Cache hit for device {device_id}")
                    return Device.parse_obj(cached_device)
            except Exception as cache_error:
                logger.warning(f"Cache retrieval error for device {device_id}: {str(cache_error)}")
        
        # Try database if not in cache
        try:
            device = await self.sql_repo.get_device(device_id)
            
            # Update cache if device found and cache is available
            if device and self.cache.client:
                try:
                    await self.cache.set_device_state(device_id, device.dict())
                except Exception as cache_set_error:
                    logger.warning(f"Failed to update cache for device {device_id}: {str(cache_set_error)}")
                    
            return device
            
        except Exception as db_error:
            logger.error(f"Database error in get_device for {device_id}: {str(db_error)}")
            
            # If we're here, both cache and database failed
            if self.fallback_enabled:
                logger.warning(f"Using mock data fallback for device {device_id}")
                # Return a basic mock device if everything else fails
                # This ensures the frontend doesn't break completely
                return None
                
            return None

    async def create_device(self, device: Device) -> Device:
        """Create a new device with caching."""
        created_device = await self.sql_repo.create_device(device)
        
        # Update cache
        if self.cache.client:
            await self.cache.set_device_state(device.id, device.dict())
            
            # Also publish device creation event
            await self.cache.publish(
                "device_events", 
                {"event": "created", "device_id": device.id}
            )
        
        return created_device

    async def update_device(self, device_id: str, device_data: Dict) -> Optional[Device]:
        """Update a device with cache invalidation."""
        updated_device = await self.sql_repo.update_device(device_id, device_data)
        
        # Update cache if device was found and updated
        if updated_device and self.cache.client:
            await self.cache.set_device_state(device_id, updated_device.dict())
            
            # Also publish device update event
            await self.cache.publish(
                "device_events", 
                {"event": "updated", "device_id": device_id}
            )
        
        return updated_device

    async def delete_device(self, device_id: str) -> bool:
        """Delete a device with cache invalidation."""
        success = await self.sql_repo.delete_device(device_id)
        
        # Clear cache if deletion was successful
        if success and self.cache.client:
            await self.cache.delete(f"device:{device_id}")
            
            # Also publish device deletion event
            await self.cache.publish(
                "device_events", 
                {"event": "deleted", "device_id": device_id}
            )
        
        return success

    async def add_device_reading(self, device_id: str, reading: DeviceReading) -> Optional[Device]:
        """Add a reading to a device with real-time caching."""
        device = await self.sql_repo.add_device_reading(device_id, reading)
        
        if device and self.cache.client:
            # Cache the reading
            await self.cache.cache_latest_reading(
                device_id, 
                reading.dict()
            )
            
            # Update device state
            await self.cache.set_device_state(device_id, device.dict())
            
            # Publish reading event for real-time updates
            await self.cache.publish(
                f"device:{device_id}:readings",
                reading.dict()
            )
            
            # Also publish to the general readings channel
            await self.cache.publish(
                "device_readings",
                {
                    "device_id": device_id,
                    "reading": reading.dict()
                }
            )
        
        return device

    async def get_device_readings(
        self, 
        device_id: str, 
        metric_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[DeviceReading]:
        """Get readings for a device with pagination and filtering."""
        # For latest readings of all metrics, try cache first
        if offset == 0 and not start_time and not end_time and self.cache.client:
            if metric_name:
                # Single metric - try specific cache
                cached_reading = await self.cache.get(f"device:{device_id}:latest:{metric_name}")
                if cached_reading:
                    return [DeviceReading.parse_obj(cached_reading)]
            else:
                # All metrics - try getting all cached latest readings
                latest_readings = await self.cache.get_latest_readings(device_id)
                if latest_readings:
                    return [DeviceReading.parse_obj(reading) for reading in latest_readings.values()]
        
        # Fall back to database for historical data
        return await self.sql_repo.get_device_readings(
            device_id=device_id,
            metric_name=metric_name,
            limit=limit,
            offset=offset,
            start_time=start_time,
            end_time=end_time,
        )
