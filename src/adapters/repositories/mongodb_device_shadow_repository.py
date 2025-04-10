"""
MongoDB implementation of the Device Shadow Repository.

This module contains the MongoDB implementation of the Device Shadow Repository interface,
following Clean Architecture principles by keeping implementation details in the adapter layer.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorCollection

from src.domain.entities.device_shadow import DeviceShadow
from src.gateways.device_shadow_repository import DeviceShadowRepository


class MongoDBDeviceShadowRepository(DeviceShadowRepository):
    """MongoDB implementation of the Device Shadow Repository.

    This class implements the DeviceShadowRepository interface using MongoDB as the
    underlying data store. It respects the Clean Architecture principle of keeping
    implementation details confined to the adapter layer.
    """

    def __init__(self, connection_string: str, database_name: str = "iot_sphere"):
        """Initialize the MongoDB Device Shadow Repository.

        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = "device_shadows"
        self.client = self._init_mongo_client()

    def _init_mongo_client(self) -> motor.motor_asyncio.AsyncIOMotorClient:
        """Initialize the MongoDB client.

        Returns:
            AsyncIOMotorClient: MongoDB client
        """
        return motor.motor_asyncio.AsyncIOMotorClient(self.connection_string)

    def get_collection(self) -> AsyncIOMotorCollection:
        """Get the MongoDB collection for device shadows.

        Returns:
            AsyncIOMotorCollection: MongoDB collection
        """
        return self.client[self.database_name][self.collection_name]

    def _entity_to_dict(self, entity: DeviceShadow) -> Dict[str, Any]:
        """Convert a device shadow entity to a MongoDB document.

        Args:
            entity: Device shadow entity to convert

        Returns:
            Dict: MongoDB document
        """
        return {
            "_id": entity.device_id,
            "reported": entity.reported,
            "desired": entity.desired,
            "version": entity.version,
            "timestamp": entity.timestamp,
        }

    def _dict_to_entity(self, doc: Dict[str, Any]) -> DeviceShadow:
        """Convert a MongoDB document to a device shadow entity.

        Args:
            doc: MongoDB document to convert

        Returns:
            DeviceShadow: Device shadow entity
        """
        return DeviceShadow(
            device_id=doc["_id"],
            reported=doc["reported"],
            desired=doc["desired"],
            version=doc["version"],
            timestamp=doc["timestamp"],
        )

    async def get_device_shadow(self, device_id: str) -> Optional[DeviceShadow]:
        """Get a device shadow by device ID.

        Args:
            device_id: ID of the device whose shadow to retrieve

        Returns:
            DeviceShadow: Device shadow entity if found, None otherwise
        """
        collection = self.get_collection()
        doc = await collection.find_one({"_id": device_id})

        if not doc:
            return None

        return self._dict_to_entity(doc)

    async def create_device_shadow(self, device_shadow: DeviceShadow) -> DeviceShadow:
        """Create a new device shadow.

        Args:
            device_shadow: Device shadow entity to create

        Returns:
            DeviceShadow: Created device shadow entity
        """
        collection = self.get_collection()

        # Convert entity to MongoDB document
        doc = self._entity_to_dict(device_shadow)

        # Insert the document
        await collection.insert_one(doc)

        return device_shadow

    async def update_desired_state(
        self, device_id: str, desired_state: Dict[str, Any]
    ) -> DeviceShadow:
        """Update the desired state of a device shadow.

        Args:
            device_id: ID of the device whose shadow to update
            desired_state: New desired state properties

        Returns:
            DeviceShadow: Updated device shadow entity
        """
        collection = self.get_collection()

        # First get the current shadow to update the version and preserve other fields
        current_shadow = await self.get_device_shadow(device_id)
        if not current_shadow:
            raise ValueError(f"No shadow document exists for device {device_id}")

        # Create update operation
        update_ops = {
            "$set": {},
            "$inc": {"version": 1},
            "$set": {"timestamp": datetime.now().isoformat()},
        }

        # Update desired state (merge with existing)
        for key, value in desired_state.items():
            update_ops["$set"][f"desired.{key}"] = value

        # Perform the update
        await collection.update_one({"_id": device_id}, update_ops)

        # Get updated shadow
        updated_shadow = await self.get_device_shadow(device_id)
        return updated_shadow

    async def update_reported_state(
        self, device_id: str, reported_state: Dict[str, Any]
    ) -> DeviceShadow:
        """Update the reported state of a device shadow.

        Args:
            device_id: ID of the device whose shadow to update
            reported_state: New reported state properties

        Returns:
            DeviceShadow: Updated device shadow entity
        """
        collection = self.get_collection()

        # First get the current shadow to update the version and preserve other fields
        current_shadow = await self.get_device_shadow(device_id)
        if not current_shadow:
            raise ValueError(f"No shadow document exists for device {device_id}")

        # Create update operation
        update_ops = {
            "$set": {},
            "$inc": {"version": 1},
            "$set": {"timestamp": datetime.now().isoformat()},
        }

        # Update reported state (merge with existing)
        for key, value in reported_state.items():
            update_ops["$set"][f"reported.{key}"] = value

        # Perform the update
        await collection.update_one({"_id": device_id}, update_ops)

        # Get updated shadow
        updated_shadow = await self.get_device_shadow(device_id)
        return updated_shadow

    async def get_shadow_delta(self, device_id: str) -> Dict[str, Any]:
        """Get the delta between desired and reported states.

        The delta contains properties that are different between desired and reported
        states, or that exist in desired but not in reported.

        Args:
            device_id: ID of the device whose shadow delta to compute

        Returns:
            Dict: Delta between desired and reported states
        """
        shadow = await self.get_device_shadow(device_id)
        if not shadow:
            raise ValueError(f"No shadow document exists for device {device_id}")

        # Calculate delta
        delta = {}
        desired = shadow.desired or {}
        reported = shadow.reported or {}

        # Add properties that are in desired but not in reported
        # or that have different values
        for key, value in desired.items():
            if key not in reported or reported[key] != value:
                delta[key] = value

        return {"delta": delta}
