"""
Asset Registry Service for IoTSphere platform.

This service manages the static metadata for all IoT devices in the system,
serving as the source of truth for device identification and specifications.
"""
import json
import logging
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

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
        self.event_bus = event_bus
        self.metadata_subscribers = []

        # Determine which storage to use
        self.storage_type = os.environ.get("ASSET_REGISTRY_STORAGE", "").lower()

        # Initialize storage
        if db_connection is not None:
            self.db_connection = db_connection
            self.in_memory_storage = None
            logger.info("Using provided database connection for Asset Registry")
        elif self.storage_type == "mongodb":
            try:
                # Use the same MongoDB connection as shadow service
                from pymongo import MongoClient

                mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
                db_name = os.environ.get("MONGODB_DB_NAME", "iotsphere")
                self.mongo_client = MongoClient(mongo_uri)
                self.mongo_db = self.mongo_client[db_name]
                self.assets_collection = self.mongo_db["assets"]
                self.db_connection = self.mongo_client
                self.in_memory_storage = None
                logger.info(f"Asset Registry using MongoDB at {mongo_uri}")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB for Asset Registry: {e}")
                logger.warning("Falling back to in-memory storage for Asset Registry")
                self.db_connection = None
                self.in_memory_storage = {}
        else:
            # Use in-memory storage for testing/development
            logger.warning(
                "Using in-memory storage for Asset Registry - DEVICE DATA WILL NOT PERSIST BETWEEN RESTARTS"
            )
            self.db_connection = None
            self.in_memory_storage = {}

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
            await self.event_bus.publish(
                "asset.device.registered",
                {
                    "device_id": device_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": device_metadata,
                },
            )

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

    async def update_device_location(
        self, device_id: str, location: Dict[str, Any]
    ) -> Dict[str, Any]:
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
            new_value=location,
        )

        # Emit event if event bus is configured
        if self.event_bus:
            await self.event_bus.publish(
                "asset.device.location_updated",
                {
                    "device_id": device_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "old_location": old_location,
                    "new_location": location,
                },
            )

        return metadata

    async def update_device_firmware(
        self, device_id: str, new_version: str
    ) -> Dict[str, Any]:
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
            new_value=new_version,
        )

        # Emit event if event bus is configured
        if self.event_bus:
            await self.event_bus.publish(
                "asset.device.firmware_updated",
                {
                    "device_id": device_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "old_version": old_version,
                    "new_version": new_version,
                },
            )

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

    def _notify_metadata_change(
        self, device_id: str, change_type: str, old_value: Any, new_value: Any
    ) -> None:
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
            "timestamp": datetime.utcnow().timestamp(),
        }

        for subscriber in self.metadata_subscribers:
            try:
                subscriber(notification)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")

    # Database access methods (using in-memory storage for testing)

    async def _device_exists(self, device_id: str) -> bool:
        """Check if a device exists in the registry."""
        if self.db_connection and hasattr(self, "assets_collection"):
            # MongoDB implementation
            result = await self._run_mongo_query(
                lambda: self.assets_collection.find_one({"device_id": device_id})
            )
            return result is not None
        else:
            return device_id in self.in_memory_storage

    async def _get_device_metadata(self, device_id: str) -> Dict[str, Any]:
        """Get device metadata from storage."""
        if self.db_connection and hasattr(self, "assets_collection"):
            # MongoDB implementation
            result = await self._run_mongo_query(
                lambda: self.assets_collection.find_one({"device_id": device_id})
            )
            if not result:
                raise ValueError(f"Device with ID {device_id} not found")
            return result
        else:
            if device_id not in self.in_memory_storage:
                raise ValueError(f"Device with ID {device_id} not found")
            return self.in_memory_storage[device_id]

    async def _store_device_metadata(
        self, device_id: str, metadata: Dict[str, Any]
    ) -> None:
        """Store device metadata."""
        if self.db_connection and hasattr(self, "assets_collection"):
            # MongoDB implementation
            await self._run_mongo_query(
                lambda: self.assets_collection.update_one(
                    {"device_id": device_id}, {"$set": metadata}, upsert=True
                )
            )
            logger.info(f"Device metadata for {device_id} stored in MongoDB")
        else:
            self.in_memory_storage[device_id] = metadata
            logger.info(f"Device metadata for {device_id} stored in memory")

    async def _run_mongo_query(self, query_func):
        """Helper method to run MongoDB queries safely."""
        try:
            # MongoDB operations are synchronous, we should make them async in production
            return query_func()
        except Exception as e:
            logger.error(f"MongoDB operation failed: {e}")
            raise
