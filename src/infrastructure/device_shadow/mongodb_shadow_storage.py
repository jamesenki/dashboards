"""
MongoDB-backed implementation of shadow storage.

This implementation provides persistent storage for device shadows using MongoDB,
following the pattern defined in ADR-0005.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import motor.motor_asyncio

logger = logging.getLogger(__name__)


class MongoDBShadowStorage:
    """
    MongoDB implementation of shadow storage for production use.

    This implementation provides:
    - Persistent storage across application restarts
    - Efficient versioning and history tracking
    - Query capabilities for finding shadows by various attributes
    """

    def __init__(
        self,
        mongo_uri: str = "mongodb://localhost:27017/",
        db_name: str = "iotsphere",
        shadows_collection: str = "device_shadows",
        history_collection: str = "shadow_history",
    ):
        """
        Initialize MongoDB storage.

        Args:
            mongo_uri: MongoDB connection URI
            db_name: Database name
            shadows_collection: Collection name for current shadows
            history_collection: Collection name for shadow history
        """
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.shadows_collection_name = shadows_collection
        self.history_collection_name = history_collection

        # These will be initialized in initialize()
        self.client = None
        self.db = None
        self.shadows = None
        self.history = None

        logger.info(f"Initialized MongoDB shadow storage (DB: {db_name})")

    async def initialize(self):
        """Initialize MongoDB connection and collections."""
        logger.info(f"Connecting to MongoDB at {self.mongo_uri}")
        self.client = motor.motor_asyncio.AsyncIOMotorClient(self.mongo_uri)
        self.db = self.client[self.db_name]
        self.shadows = self.db[self.shadows_collection_name]
        self.history = self.db[self.history_collection_name]

        # Create indexes
        await self.shadows.create_index("device_id", unique=True)
        await self.history.create_index([("device_id", 1), ("version", -1)])

        logger.info("MongoDB shadow storage initialized successfully")

    async def close(self):
        """Close MongoDB connection."""
        if self.client is not None:
            self.client.close()
            logger.info("MongoDB connection closed")

    async def drop_collections(self):
        """Drop collections (for testing)."""
        if self.db is not None:
            await self.db.drop_collection(self.shadows_collection_name)
            await self.db.drop_collection(self.history_collection_name)
            logger.info(f"Dropped collections in {self.db_name}")

    async def shadow_exists(self, device_id: str) -> bool:
        """
        Check if a shadow exists for the device.

        Args:
            device_id: Device identifier

        Returns:
            bool: True if shadow exists, False otherwise
        """
        count = await self.shadows.count_documents({"device_id": device_id})
        return count > 0

    async def get_shadow(self, device_id: str) -> Dict[str, Any]:
        """
        Get the current shadow document.

        Args:
            device_id: Device identifier

        Returns:
            Dict: Shadow document

        Raises:
            ValueError: If shadow doesn't exist
        """
        shadow = await self.shadows.find_one({"device_id": device_id})
        if not shadow:
            raise ValueError(f"No shadow found for device {device_id}")

        # Convert MongoDB _id to string and remove from result
        if "_id" in shadow:
            shadow["_id"] = str(shadow["_id"])
            del shadow["_id"]

        return shadow

    async def save_shadow(self, device_id: str, shadow: Dict[str, Any]) -> None:
        """
        Save the shadow document.

        This method:
        1. Saves the current shadow to the shadows collection
        2. Adds a copy to the history collection

        Args:
            device_id: Device identifier
            shadow: Shadow document to save
        """
        # Save previous version to history if it exists
        try:
            previous = await self.get_shadow(device_id)
            # Add timestamp for history tracking
            previous["timestamp"] = previous.get("metadata", {}).get(
                "last_updated", datetime.utcnow().isoformat() + "Z"
            )
            await self.history.insert_one(previous)
            logger.debug(
                f"Saved history for {device_id} version {previous.get('version', 0)}"
            )
        except ValueError:
            # No previous version exists
            pass

        # Update current shadow
        shadow["timestamp"] = shadow.get("metadata", {}).get(
            "last_updated", datetime.utcnow().isoformat() + "Z"
        )
        await self.shadows.replace_one({"device_id": device_id}, shadow, upsert=True)
        logger.debug(f"Saved shadow for {device_id} version {shadow.get('version', 0)}")

    async def delete_shadow(self, device_id: str) -> bool:
        """
        Delete the shadow document.

        Args:
            device_id: Device identifier

        Returns:
            bool: True if deleted, False if not found
        """
        # Check if shadow exists first
        if not await self.shadow_exists(device_id):
            return False

        # Move current shadow to history with deletion marker
        try:
            current = await self.get_shadow(device_id)
            current["deleted"] = True
            current["timestamp"] = datetime.utcnow().isoformat() + "Z"
            await self.history.insert_one(current)
        except Exception as e:
            logger.error(f"Error archiving shadow before deletion: {e}")

        # Delete from current shadows
        result = await self.shadows.delete_one({"device_id": device_id})
        logger.info(f"Deleted shadow for {device_id}")
        return result.deleted_count > 0

    async def get_shadow_history(
        self, device_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get shadow history.

        Args:
            device_id: Device identifier
            limit: Maximum number of history entries

        Returns:
            List[Dict]: List of historical shadow versions (newest first)
        """
        # Get current shadow
        try:
            current = await self.get_shadow(device_id)

            # Add current shadow to history list
            history = [current]

            # Get previous versions from history collection
            cursor = (
                self.history.find({"device_id": device_id})
                .sort("version", -1)
                .limit(limit - 1)
            )

            async for doc in cursor:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                    del doc["_id"]
                history.append(doc)

            return history[:limit]  # Ensure we don't exceed limit

        except ValueError:
            # If current shadow doesn't exist, just return history
            cursor = (
                self.history.find({"device_id": device_id})
                .sort("version", -1)
                .limit(limit)
            )

            history = []
            async for doc in cursor:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                    del doc["_id"]
                history.append(doc)

            return history
