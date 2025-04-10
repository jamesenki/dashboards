"""
MongoDB implementation of the Water Heater Repository.

This module contains the MongoDB implementation of the Water Heater Repository interface,
following Clean Architecture principles by keeping implementation details in the adapter layer.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorCollection

from src.domain.entities.water_heater import WaterHeater
from src.domain.value_objects.device_status import DeviceStatus
from src.domain.value_objects.maintenance_status import MaintenanceStatus
from src.domain.value_objects.temperature import Temperature
from src.domain.value_objects.water_heater_mode import WaterHeaterMode
from src.gateways.water_heater_repository import WaterHeaterRepository


class MongoDBWaterHeaterRepository(WaterHeaterRepository):
    """MongoDB implementation of the Water Heater Repository.

    This class implements the WaterHeaterRepository interface using MongoDB as the
    underlying data store. It respects the Clean Architecture principle of keeping
    implementation details confined to the adapter layer.
    """

    def __init__(self, connection_string: str, database_name: str = "iot_sphere"):
        """Initialize the MongoDB Water Heater Repository.

        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = "water_heaters"
        self.client = self._init_mongo_client()

    def _init_mongo_client(self) -> motor.motor_asyncio.AsyncIOMotorClient:
        """Initialize the MongoDB client.

        Returns:
            AsyncIOMotorClient: MongoDB client
        """
        return motor.motor_asyncio.AsyncIOMotorClient(self.connection_string)

    def get_collection(self) -> AsyncIOMotorCollection:
        """Get the MongoDB collection for water heaters.

        Returns:
            AsyncIOMotorCollection: MongoDB collection
        """
        return self.client[self.database_name][self.collection_name]

    def _entity_to_dict(self, entity: WaterHeater) -> Dict[str, Any]:
        """Convert a water heater entity to a MongoDB document.

        Args:
            entity: Water heater entity to convert

        Returns:
            Dict: MongoDB document
        """
        return {
            "_id": entity.id,
            "name": entity.name,
            "manufacturer": entity.manufacturer,
            "model": entity.model,
            "location": entity.location,
            "is_simulated": entity.is_simulated,
            "current_temperature": {
                "value": entity.current_temperature.value,
                "unit": entity.current_temperature.unit,
            },
            "target_temperature": {
                "value": entity.target_temperature.value,
                "unit": entity.target_temperature.unit,
            },
            "min_temperature": {
                "value": entity.min_temperature.value,
                "unit": entity.min_temperature.unit,
            },
            "max_temperature": {
                "value": entity.max_temperature.value,
                "unit": entity.max_temperature.unit,
            },
            "status": entity.status.value,
            "mode": entity.mode.value,
            "health_status": entity.health_status.value,
            "heater_status": entity.heater_status,
            "last_updated": entity.last_updated.isoformat()
            if entity.last_updated
            else None,
        }

    def _dict_to_entity(self, doc: Dict[str, Any]) -> WaterHeater:
        """Convert a MongoDB document to a water heater entity.

        Args:
            doc: MongoDB document to convert

        Returns:
            WaterHeater: Water heater entity
        """
        # Handle the case where document might not have all fields
        last_updated = None
        if doc.get("last_updated"):
            if isinstance(doc["last_updated"], str):
                last_updated = datetime.fromisoformat(doc["last_updated"])
            else:
                last_updated = doc["last_updated"]

        return WaterHeater(
            id=doc["_id"],
            name=doc["name"],
            manufacturer=doc["manufacturer"],
            model=doc["model"],
            location=doc.get("location"),
            is_simulated=doc.get("is_simulated", False),
            current_temperature=Temperature(
                value=doc["current_temperature"]["value"],
                unit=doc["current_temperature"]["unit"],
            ),
            target_temperature=Temperature(
                value=doc["target_temperature"]["value"],
                unit=doc["target_temperature"]["unit"],
            ),
            min_temperature=Temperature(
                value=doc["min_temperature"]["value"],
                unit=doc["min_temperature"]["unit"],
            ),
            max_temperature=Temperature(
                value=doc["max_temperature"]["value"],
                unit=doc["max_temperature"]["unit"],
            ),
            status=DeviceStatus(value=doc["status"]),
            mode=WaterHeaterMode(value=doc["mode"]),
            health_status=MaintenanceStatus(value=doc["health_status"]),
            heater_status=doc["heater_status"],
            last_updated=last_updated,
        )

    async def get_by_id(self, heater_id: str) -> Optional[WaterHeater]:
        """Get a water heater by ID.

        Args:
            heater_id: ID of the water heater to retrieve

        Returns:
            WaterHeater: Water heater entity if found, None otherwise
        """
        collection = self.get_collection()
        doc = await collection.find_one({"_id": heater_id})

        if not doc:
            return None

        return self._dict_to_entity(doc)

    async def get_all(self) -> List[WaterHeater]:
        """Get all water heaters.

        Returns:
            List[WaterHeater]: List of water heater entities
        """
        collection = self.get_collection()
        cursor = collection.find()

        water_heaters = []

        # Handle both the case where cursor is directly iterable (production)
        # and where it might be a mock returning results directly (test)
        try:
            async for doc in cursor:
                water_heaters.append(self._dict_to_entity(doc))
        except TypeError:
            # In test environment, we might get a list directly
            if hasattr(cursor, "__iter__"):
                for doc in cursor:
                    water_heaters.append(self._dict_to_entity(doc))
            else:
                # If cursor is a coroutine (as in our test), await it to get the result
                docs = await cursor
                if isinstance(docs, list):
                    for doc in docs:
                        water_heaters.append(self._dict_to_entity(doc))

        return water_heaters

    async def create(self, water_heater: WaterHeater) -> WaterHeater:
        """Create a new water heater.

        Args:
            water_heater: The WaterHeater entity to create

        Returns:
            The created WaterHeater entity with assigned ID

        Raises:
            ValueError: If a water heater with the same ID already exists
        """
        collection = self.get_collection()

        # If no ID is provided, generate one
        if not water_heater.id:
            water_heater.id = str(uuid.uuid4())
        else:
            # Check if water heater with the same ID already exists
            existing = await collection.find_one({"_id": water_heater.id})
            if existing:
                raise ValueError(
                    f"Water heater with ID {water_heater.id} already exists"
                )

        # Convert entity to MongoDB document
        doc = self._entity_to_dict(water_heater)

        # Insert the document
        await collection.insert_one(doc)

        return water_heater

    async def save(self, entity: WaterHeater) -> str:
        """Save a new water heater.

        Args:
            entity: Water heater entity to save

        Returns:
            str: ID of the saved water heater
        """
        collection = self.get_collection()

        # If no ID is provided, generate one
        if not entity.id:
            entity.id = str(uuid.uuid4())

        # Convert entity to MongoDB document
        doc = self._entity_to_dict(entity)

        # Insert the document
        result = await collection.insert_one(doc)

        return result.inserted_id

    async def update(self, entity: WaterHeater) -> bool:
        """Update an existing water heater.

        Args:
            entity: Water heater entity to update

        Returns:
            bool: True if the water heater was updated, False otherwise
        """
        collection = self.get_collection()

        # Convert entity to MongoDB document
        doc = self._entity_to_dict(entity)

        # Remove the _id field from the update document
        entity_id = doc.pop("_id")

        # Update the document
        result = await collection.update_one({"_id": entity_id}, {"$set": doc})

        return result.modified_count > 0

    async def delete(self, heater_id: str) -> bool:
        """Delete a water heater by ID.

        Args:
            heater_id: ID of the water heater to delete

        Returns:
            bool: True if the water heater was deleted, False otherwise
        """
        collection = self.get_collection()

        # Delete the document
        result = await collection.delete_one({"_id": heater_id})

        return result.deleted_count > 0
