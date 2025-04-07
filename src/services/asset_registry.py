"""
Asset Registry Service for IoTSphere platform.

This service manages the static metadata for all IoT devices in the system,
serving as the source of truth for device identification and specifications.
"""
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

logger = logging.getLogger(__name__)

class AssetRegistryService:
    """
    Manages the device registry and asset information for all IoT devices.
    
    The Asset Registry is the source of truth for static device metadata such as:
    1. Device identification (manufacturer, model, serial number)
    2. Installation information (location, installation date)
    3. Device specifications (capacity, voltage, etc.)
    4. Maintenance records
    
    This separation from the Device Shadow allows for efficient state management
    while keeping metadata in a structured database designed for queries and reporting.
    """
    
    def __init__(self, db_connection=None, event_bus=None):
        """
        Initialize the Asset Registry Service.
        
        Args:
            db_connection: Database connection for the asset registry
            event_bus: Event system for broadcasting metadata changes
        """
        self.db_connection = db_connection
        self.event_bus = event_bus
        self.metadata_subscribers = []
        
        # For testing/development, use in-memory storage if no DB connection
        self.in_memory_storage = {} if db_connection is None else None
        
        logger.info("Asset Registry Service initialized")
    
    async def register_device(self, device_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new device in the asset database.
        
        Args:
            device_metadata: Device metadata including ID, type, manufacturer, etc.
            
        Returns:
            Dict containing the registered device metadata
        """
        device_id = device_metadata.get("device_id")
        if not device_id:
            raise ValueError("Device ID is required")
            
        # Check if device already exists
        if await self._device_exists(device_id):
            raise ValueError(f"Device with ID {device_id} already exists")
        
        # Add registration timestamp if not provided
        if "registration_date" not in device_metadata:
            device_metadata["registration_date"] = datetime.utcnow().isoformat()
        
        # Store device metadata
        await self._store_device_metadata(device_id, device_metadata)
        
        # Emit event if event bus is configured
        if self.event_bus:
            await self.event_bus.publish("asset.device.registered", {
                "device_id": device_id,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": device_metadata
            })
            
        return device_metadata
    
    async def get_device_info(self, device_id: str) -> Dict[str, Any]:
        """
        Get device information from the asset registry.
        
        Args:
            device_id: Unique identifier for the device
            
        Returns:
            Dict containing device metadata
        """
        # Check if device exists
        if not await self._device_exists(device_id):
            raise ValueError(f"Device with ID {device_id} not found")
            
        # Retrieve device metadata
        return await self._get_device_metadata(device_id)
    
    async def update_device_location(self, device_id: str, 
                                   location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the location of a device.
        
        Args:
            device_id: Unique identifier for the device
            location: New location information
            
        Returns:
            Dict containing the updated device metadata
        """
        # Check if device exists
        if not await self._device_exists(device_id):
            raise ValueError(f"Device with ID {device_id} not found")
            
        # Get current metadata
        metadata = await self._get_device_metadata(device_id)
        
        # Store old location for event notification
        old_location = metadata.get("location", {})
        
        # Update location
        metadata["location"] = location
        
        # Update last modified timestamp
        metadata["last_modified"] = datetime.utcnow().isoformat()
        
        # Store updated metadata
        await self._store_device_metadata(device_id, metadata)
        
        # Notify subscribers
        self._notify_metadata_change(
            device_id=device_id,
            change_type="location_update",
            old_value=old_location,
            new_value=location
        )
        
        # Emit event if event bus is configured
        if self.event_bus:
            await self.event_bus.publish("asset.device.location_updated", {
                "device_id": device_id,
                "timestamp": datetime.utcnow().isoformat(),
                "old_location": old_location,
                "new_location": location
            })
            
        return metadata
    
    async def update_device_firmware(self, device_id: str, 
                                   new_version: str) -> Dict[str, Any]:
        """
        Update firmware version of a device.
        
        Args:
            device_id: Unique identifier for the device
            new_version: New firmware version
            
        Returns:
            Dict containing the updated device metadata
        """
        # Check if device exists
        if not await self._device_exists(device_id):
            raise ValueError(f"Device with ID {device_id} not found")
            
        # Get current metadata
        metadata = await self._get_device_metadata(device_id)
        
        # Store old version for event notification
        old_version = metadata.get("firmware_version", "")
        
        # Update firmware version
        metadata["firmware_version"] = new_version
        
        # Update last modified timestamp
        metadata["last_modified"] = datetime.utcnow().isoformat()
        
        # Store updated metadata
        await self._store_device_metadata(device_id, metadata)
        
        # Notify subscribers
        self._notify_metadata_change(
            device_id=device_id,
            change_type="firmware_update",
            old_value=old_version,
            new_value=new_version
        )
        
        # Emit event if event bus is configured
        if self.event_bus:
            await self.event_bus.publish("asset.device.firmware_updated", {
                "device_id": device_id,
                "timestamp": datetime.utcnow().isoformat(),
                "old_version": old_version,
                "new_version": new_version
            })
            
        return metadata
    
    async def get_unified_device_view(self, device_id: str) -> Dict[str, Any]:
        """
        Get a unified view of device information combining metadata and state.
        
        Args:
            device_id: Unique identifier for the device
            
        Returns:
            Dict containing combined device metadata and state information
        """
        from src.services.device_shadow import DeviceShadowService
        
        # Get device metadata from the asset registry
        metadata = await self.get_device_info(device_id)
        
        # Get device state from the shadow service
        try:
            # Access the DeviceShadowService (should be injected in production)
            shadow_service = DeviceShadowService()
            shadow = await shadow_service.get_device_shadow(device_id)
            
            # Combine metadata and state
            unified_view = {**metadata}
            unified_view["state"] = shadow.get("reported", {})
            
            return unified_view
            
        except Exception as e:
            logger.warning(f"Failed to get device shadow for {device_id}: {e}")
            # Return metadata only if shadow is not available
            return {**metadata, "state": {}}
    
    def subscribe_to_metadata_changes(self, callback: Callable) -> None:
        """
        Subscribe to device metadata changes.
        
        Args:
            callback: Function to call when metadata changes
        """
        if callback not in self.metadata_subscribers:
            self.metadata_subscribers.append(callback)
    
    def unsubscribe_from_metadata_changes(self, callback: Callable) -> None:
        """
        Unsubscribe from device metadata changes.
        
        Args:
            callback: Function to remove from subscribers
        """
        if callback in self.metadata_subscribers:
            self.metadata_subscribers.remove(callback)
    
    def _notify_metadata_change(self, device_id: str, change_type: str, 
                               old_value: Any, new_value: Any) -> None:
        """
        Notify subscribers of metadata changes.
        
        Args:
            device_id: ID of the device that changed
            change_type: Type of change that occurred
            old_value: Previous value
            new_value: New value
        """
        notification = {
            "device_id": device_id,
            "change_type": change_type,
            "old_value": old_value,
            "new_value": new_value,
            "timestamp": datetime.utcnow().timestamp()
        }
        
        for subscriber in self.metadata_subscribers:
            try:
                subscriber(notification)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    # Database access methods (using in-memory storage for testing)
    
    async def _device_exists(self, device_id: str) -> bool:
        """Check if a device exists in the registry."""
        if self.db_connection:
            # Database implementation would go here
            pass
        else:
            return device_id in self.in_memory_storage
    
    async def _get_device_metadata(self, device_id: str) -> Dict[str, Any]:
        """Get device metadata from storage."""
        if self.db_connection:
            # Database implementation would go here
            pass
        else:
            if device_id not in self.in_memory_storage:
                raise ValueError(f"Device with ID {device_id} not found")
            return self.in_memory_storage[device_id]
    
    async def _store_device_metadata(self, device_id: str, 
                                   metadata: Dict[str, Any]) -> None:
        """Store device metadata."""
        if self.db_connection:
            # Database implementation would go here
            pass
        else:
            self.in_memory_storage[device_id] = metadata
