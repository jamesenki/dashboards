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
        try:
            logger.info(f"Connecting to MongoDB at {self.mongo_uri}")
            # Set server selection timeout to prevent long connection attempts
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=2000,  # 2 seconds timeout for server selection
                connectTimeoutMS=2000,         # 2 seconds timeout for connection
                socketTimeoutMS=2000,          # 2 seconds timeout for socket operations
                maxPoolSize=10                # Limit connection pool size for faster creation
            )
            
            # Fast connection check that will throw an exception if server is not available
            # This prevents hanging during server unavailability
            await self.client.admin.command('ismaster')
            
            self.db = self.client[self.db_name]
            self.shadows = self.db[self.shadows_collection_name]
            self.history = self.db[self.history_collection_name]
            
            # Start index creation in background without waiting for completion
            # This dramatically improves startup time while ensuring indexes are eventually created
            asyncio.create_task(self._create_indexes())
            
            logger.info("MongoDB shadow storage connected successfully")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {str(e)}")
            # Re-raise to let the factory handle the fallback
            raise
            
    async def _create_indexes(self):
        """Create MongoDB indexes in background to avoid blocking startup"""
        try:
            # Create shadow index with background option for faster creation
            await self.shadows.create_index("device_id", unique=True, background=True)
            # Create history index with background option for faster creation
            await self.history.create_index([("device_id", 1), ("version", -1)], background=True)
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            # Log error but don't fail the application - indexes improve performance but aren't critical
            logger.warning(f"Failed to create MongoDB indexes: {str(e)}")
            # System will still function, just with potentially slower queries

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
