"""
Device Shadow Service for IoTSphere platform.

This service implements the device shadow/digital twin functionality, maintaining 
a synchronized representation of device state that can be accessed and updated
both by the device and by applications.
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DeviceShadowService:
    """
    Manages device shadows/digital twins for all IoT devices in the system.
    
    A device shadow is a JSON document that stores the current state and 
    desired future state of a device. It enables applications to:
    
    1. Get the last reported state of a device even when the device is offline
    2. Update the desired state of a device, which the device can retrieve when online 
    3. Compare reported state vs desired state to detect drift or needed actions
    
    NOTE: Device shadows ONLY store state information, not device metadata.
    Device metadata (manufacturer, model, location, etc.) is stored in the AssetRegistry.
    """
    
    def __init__(self, storage_provider=None, event_bus=None):
        """
        Initialize the Device Shadow Service.
        
        Args:
            storage_provider: Provider for persisting shadow documents
            event_bus: Event system for broadcasting shadow changes
        """
        # In a real implementation, these would be actual dependencies
        # For now, we'll use in-memory storage for testing
        self.storage_provider = storage_provider or InMemoryShadowStorage()
        self.event_bus = event_bus
        logger.info("Device Shadow Service initialized")
    
    async def create_device_shadow(self, device_id: str, 
                                  reported_state: Dict[str, Any] = None, 
                                  desired_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new device shadow document.
        
        Args:
            device_id: Unique identifier for the device
            reported_state: Current reported state of the device
            desired_state: Desired state for the device
            
        Returns:
            Dict containing the created shadow document metadata
        """
        if await self.storage_provider.shadow_exists(device_id):
            raise ValueError(f"Shadow document already exists for device {device_id}")
        
        # Create timestamp
        now = datetime.utcnow().isoformat() + "Z"
        
        # Create the shadow document with ONLY state data, not device metadata
        shadow = {
            "device_id": device_id,  # Device ID is the only identifying information needed
            "reported": reported_state or {},
            "desired": desired_state or {},
            "version": 1,
            "metadata": {
                "created_at": now,
                "last_updated": now
            }
        }
        
        # Save the shadow document
        await self.storage_provider.save_shadow(device_id, shadow)
        
        # Emit event if event bus is configured
        if self.event_bus:
            await self.event_bus.publish("shadow.created", {
                "device_id": device_id,
                "timestamp": now,
                "version": 1
            })
        
        # Return metadata
        return {
            "device_id": device_id,
            "version": 1
        }
    
    async def get_device_shadow(self, device_id: str) -> Dict[str, Any]:
        """
        Retrieve the current device shadow.
        
        Args:
            device_id: Unique identifier for the device
            
        Returns:
            Dict containing the complete shadow document
            
        Raises:
            ValueError: If shadow document doesn't exist
        """
        if not await self.storage_provider.shadow_exists(device_id):
            raise ValueError(f"No shadow document exists for device {device_id}")
        
        return await self.storage_provider.get_shadow(device_id)
    
    async def update_device_shadow(self, device_id: str, 
                                  reported_state: Dict[str, Any] = None,
                                  desired_state: Dict[str, Any] = None,
                                  version: int = None) -> Dict[str, Any]:
        """
        Update the device shadow with new state information.
        
        Args:
            device_id: Unique identifier for the device
            reported_state: Updated reported state (device-driven)
            desired_state: Updated desired state (app-driven)
            version: Current version for optimistic locking
            
        Returns:
            Dict containing the updated shadow metadata
            
        Raises:
            ValueError: If shadow doesn't exist or version conflict
        """
        if not await self.storage_provider.shadow_exists(device_id):
            raise ValueError(f"No shadow document exists for device {device_id}")
        
        # Get current shadow
        current_shadow = await self.storage_provider.get_shadow(device_id)
        
        # Check version if provided
        if version is not None and current_shadow["version"] != version:
            raise ValueError(f"Version conflict: Document has been modified. Current version: {current_shadow['version']}, provided version: {version}")
        
        # Create new version with updates
        new_version = current_shadow["version"] + 1
        now = datetime.utcnow().isoformat() + "Z"
        
        # Update reported state if provided
        if reported_state:
            current_shadow["reported"].update(reported_state)
        
        # Update desired state if provided
        if desired_state:
            current_shadow["desired"].update(desired_state)
        
        # Update metadata
        current_shadow["version"] = new_version
        current_shadow["metadata"]["last_updated"] = now
        
        # Save history if configured (not implemented yet)
        
        # Save updated shadow
        await self.storage_provider.save_shadow(device_id, current_shadow)
        
        # Emit event if event bus is configured
        if self.event_bus:
            event_data = {
                "device_id": device_id,
                "timestamp": now,
                "version": new_version
            }
            if reported_state:
                event_data["state"] = {"reported": reported_state}
            if desired_state:
                event_data["state"] = event_data.get("state", {})
                event_data["state"]["desired"] = desired_state
                
            await self.event_bus.publish("shadow.updated", event_data)
        
        # Return result
        result = {
            "device_id": device_id,
            "version": new_version,
            "state": {}
        }
        
        if reported_state:
            result["state"]["reported"] = reported_state
        if desired_state:
            result["state"]["desired"] = desired_state
            
        return result
    
    async def delete_device_shadow(self, device_id: str) -> bool:
        """
        Delete a device shadow document.
        
        Args:
            device_id: Unique identifier for the device
            
        Returns:
            bool indicating success
            
        Raises:
            ValueError: If shadow doesn't exist
        """
        if not await self.storage_provider.shadow_exists(device_id):
            raise ValueError(f"No shadow document exists for device {device_id}")
        
        # Delete the shadow
        success = await self.storage_provider.delete_shadow(device_id)
        
        # Emit event if event bus is configured
        if success and self.event_bus:
            now = datetime.utcnow().isoformat() + "Z"
            await self.event_bus.publish("shadow.deleted", {
                "device_id": device_id,
                "timestamp": now
            })
        
        return success
    
    async def get_shadow_delta(self, device_id: str) -> Dict[str, Any]:
        """
        Get the delta between reported and desired state.
        
        Args:
            device_id: Unique identifier for the device
            
        Returns:
            Dict containing differences between reported and desired state
            
        Raises:
            ValueError: If shadow doesn't exist
        """
        shadow = await self.get_device_shadow(device_id)
        reported = shadow.get("reported", {})
        desired = shadow.get("desired", {})
        
        # Find all keys in either reported or desired
        all_keys = set(reported.keys()) | set(desired.keys())
        delta = {}
        
        # Compare values for each key
        for key in all_keys:
            reported_val = reported.get(key)
            desired_val = desired.get(key)
            
            # Only include in delta if values differ
            if reported_val != desired_val:
                delta[key] = {
                    "reported": reported_val,
                    "desired": desired_val
                }
        
        return delta
    
    async def get_shadow_history(self, device_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get historical versions of the shadow document.
        
        Args:
            device_id: Unique identifier for the device
            limit: Maximum number of history entries to return
            
        Returns:
            List of historical shadow versions
            
        Raises:
            ValueError: If shadow doesn't exist
        """
        if not await self.storage_provider.shadow_exists(device_id):
            raise ValueError(f"No shadow document exists for device {device_id}")
        
        # This would normally fetch from a real history store
        # For now, return a mock history
        history = await self.storage_provider.get_shadow_history(device_id, limit)
        return history


class InMemoryShadowStorage:
    """
    In-memory implementation of shadow storage for testing and development.
    
    In production, this would be replaced with a proper database or storage service.
    """
    
    def __init__(self):
        """Initialize in-memory storage."""
        self.shadows = {}
        self.shadow_history = {}
    
    async def shadow_exists(self, device_id: str) -> bool:
        """Check if a shadow exists for the device."""
        return device_id in self.shadows
    
    async def get_shadow(self, device_id: str) -> Dict[str, Any]:
        """Get the current shadow document."""
        if device_id not in self.shadows:
            raise ValueError(f"No shadow found for device {device_id}")
        return self.shadows[device_id]
    
    async def save_shadow(self, device_id: str, shadow: Dict[str, Any]) -> None:
        """Save the shadow document."""
        # Keep a copy of current shadow in history if it exists
        if device_id in self.shadows:
            if device_id not in self.shadow_history:
                self.shadow_history[device_id] = []
            # Add to history with timestamp
            history_entry = self.shadows[device_id].copy()
            self.shadow_history[device_id].append(history_entry)
            # Limit history size
            if len(self.shadow_history[device_id]) > 100:
                self.shadow_history[device_id].pop(0)
        
        # Save the new shadow
        self.shadows[device_id] = shadow.copy()
    
    async def delete_shadow(self, device_id: str) -> bool:
        """Delete the shadow document."""
        if device_id not in self.shadows:
            return False
        del self.shadows[device_id]
        return True
    
    async def get_shadow_history(self, device_id: str, limit: int) -> List[Dict[str, Any]]:
        """Get shadow history."""
        if device_id not in self.shadow_history:
            return []
        return self.shadow_history[device_id][-limit:]
