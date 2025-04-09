"""
Optimized MongoDB implementation of shadow storage.

This implementation provides enhanced performance through:
1. Connection pooling
2. Time series collections for history data
3. Reduced logging overhead
4. Improved document structure
"""
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional

import motor.motor_asyncio
from pymongo.operations import InsertOne

logger = logging.getLogger(__name__)

# Ensure MongoDB driver logging is set to WARNING level
logging.getLogger("motor.motor_asyncio").setLevel(logging.WARNING)
logging.getLogger("pymongo").setLevel(logging.WARNING)


class OptimizedMongoDBShadowStorage:
    """
    Optimized MongoDB implementation of shadow storage with connection pooling
    and time series collections for better performance.
    """

    def __init__(
        self,
        mongo_uri: str = "mongodb://localhost:27017/",
        db_name: str = "iotsphere",
        shadows_collection: str = "device_shadows",
        history_collection: str = "temperature_history",
        pool_size: int = 10,
    ):
        """
        Initialize MongoDB storage with connection pooling.

        Args:
            mongo_uri: MongoDB connection URI
            db_name: Database name
            shadows_collection: Collection name for current shadows
            history_collection: Collection name for time series shadow history
            pool_size: Max size of the connection pool
        """
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.shadows_collection_name = shadows_collection
        self.history_collection_name = history_collection
        self.pool_size = pool_size

        # These will be initialized in initialize()
        self.client = None
        self.db = None
        self.shadows = None
        self.history = None

        # Cache configuration - only cache the most recent shadow documents
        self._shadow_cache = {}
        self._cache_size = 32
        self._cache_ttl = 30  # seconds
        self._last_cache_clear = datetime.now()

        logger.info(f"Initialized optimized MongoDB shadow storage (DB: {db_name})")

    async def initialize(self):
        """
        Initialize MongoDB connection and collections with connection pooling.
        Creates time series collection if it doesn't exist.
        """
        logger.info(
            f"Connecting to MongoDB at {self.mongo_uri} with pool size {self.pool_size}"
        )

        # Create connection with pooling
        self.client = motor.motor_asyncio.AsyncIOMotorClient(
            self.mongo_uri,
            maxPoolSize=self.pool_size,
            minPoolSize=1,
            serverSelectionTimeoutMS=5000,  # Faster failure detection
            connectTimeoutMS=10000,
            socketTimeoutMS=45000,
            waitQueueTimeoutMS=10000,
        )

        self.db = self.client[self.db_name]
        self.shadows = self.db[self.shadows_collection_name]

        # Check if time series collection exists, create if not
        collection_names = await self.db.list_collection_names()

        if self.history_collection_name not in collection_names:
            logger.info(
                f"Creating time series collection: {self.history_collection_name}"
            )
            try:
                # Time series collections require MongoDB 5.0+
                await self.db.create_collection(
                    self.history_collection_name,
                    timeseries={
                        "timeField": "timestamp",
                        "metaField": "device_id",
                        "granularity": "minutes",
                    },
                )
                logger.info("Time series collection created successfully")
            except Exception as e:
                logger.warning(f"Unable to create time series collection: {e}")
                logger.warning(
                    "Falling back to regular collection - this may affect performance"
                )
                # If time series creation fails (e.g. older MongoDB version),
                # create a regular collection instead
                if self.history_collection_name not in collection_names:
                    await self.db.create_collection(self.history_collection_name)

        # Get the history collection
        self.history = self.db[self.history_collection_name]

        # Create indexes
        await self.shadows.create_index("device_id", unique=True)
        await self.history.create_index([("device_id", 1), ("timestamp", -1)])

        logger.info("Optimized MongoDB shadow storage initialized successfully")

    async def close(self):
        """Close MongoDB connection."""
        if self.client is not None:
            self.client.close()
            logger.info("MongoDB connection closed")

    def _check_cache_expiry(self):
        """Check and clear cache if TTL has expired"""
        now = datetime.now()
        if (now - self._last_cache_clear).total_seconds() > self._cache_ttl:
            self._shadow_cache.clear()
            self._last_cache_clear = now

    async def shadow_exists(self, device_id: str) -> bool:
        """
        Check if a shadow exists for the device.

        Args:
            device_id: Device identifier

        Returns:
            bool: True if shadow exists, False otherwise
        """
        # Check cache first
        self._check_cache_expiry()
        if device_id in self._shadow_cache:
            return True

        # Not in cache, check database
        count = await self.shadows.count_documents({"device_id": device_id})
        return count > 0

    async def get_shadow(self, device_id: str) -> Dict[str, Any]:
        """
        Get the current shadow document with caching.

        Args:
            device_id: Device identifier

        Returns:
            Dict: Shadow document

        Raises:
            ValueError: If shadow doesn't exist
        """
        # Check cache first
        self._check_cache_expiry()
        if device_id in self._shadow_cache:
            logger.debug(f"Shadow cache hit for {device_id}")
            return self._shadow_cache[device_id]

        # Not in cache, get from database
        shadow = await self.shadows.find_one({"device_id": device_id})
        if not shadow:
            raise ValueError(f"No shadow found for device {device_id}")

        # Convert MongoDB _id to string and remove from result
        if "_id" in shadow:
            shadow["_id"] = str(shadow["_id"])
            del shadow["_id"]

        # Add to cache
        if len(self._shadow_cache) >= self._cache_size:
            # If cache is full, remove oldest entry
            # This is a simple implementation - a real LRU cache would be better
            if self._shadow_cache:
                self._shadow_cache.pop(next(iter(self._shadow_cache)))

        self._shadow_cache[device_id] = shadow
        return shadow

    async def save_shadow(self, device_id: str, shadow: Dict[str, Any]) -> None:
        """
        Save the shadow document with optimized history storage.

        This implementation separates the shadow document from its history
        for better performance.

        Args:
            device_id: Device identifier
            shadow: Shadow document to save
        """
        # Extract history to store separately
        history = shadow.pop("history", []) if "history" in shadow else []

        # Update current shadow
        shadow["timestamp"] = shadow.get("metadata", {}).get(
            "last_updated", datetime.utcnow().isoformat() + "Z"
        )

        # Save the shadow document without history
        await self.shadows.replace_one({"device_id": device_id}, shadow, upsert=True)

        # Update cache
        self._shadow_cache[device_id] = shadow

        logger.debug(f"Saved shadow for {device_id} version {shadow.get('version', 0)}")

        # Save history entries to time series collection
        if history:
            bulk_ops = []
            for entry in history:
                # Ensure each history entry has device_id
                entry["device_id"] = device_id

                # Convert string timestamp to datetime if needed
                if isinstance(entry.get("timestamp"), str):
                    try:
                        # Remove Z and parse
                        ts_str = entry["timestamp"].rstrip("Z")
                        entry["timestamp"] = datetime.fromisoformat(ts_str)
                    except ValueError:
                        # If parsing fails, use current time
                        entry["timestamp"] = datetime.now()

                # Add to bulk operation
                bulk_ops.append(InsertOne(entry))

            # Execute bulk insert if we have operations
            if bulk_ops:
                try:
                    await self.history.bulk_write(bulk_ops, ordered=False)
                    logger.debug(
                        f"Saved {len(bulk_ops)} history entries for {device_id}"
                    )
                except Exception as e:
                    logger.error(f"Error saving history entries: {e}")

    async def delete_shadow(self, device_id: str) -> bool:
        """
        Delete the shadow document and its history.

        Args:
            device_id: Device identifier

        Returns:
            bool: True if deleted, False if not found
        """
        # Check if shadow exists first
        if not await self.shadow_exists(device_id):
            return False

        # Delete from current shadows
        result = await self.shadows.delete_one({"device_id": device_id})

        # Delete from history collection
        await self.history.delete_many({"device_id": device_id})

        # Remove from cache
        if device_id in self._shadow_cache:
            del self._shadow_cache[device_id]

        logger.info(f"Deleted shadow and history for {device_id}")
        return result.deleted_count > 0

    async def get_shadow_history(
        self,
        device_id: str,
        limit: int = 10,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get shadow history with time range support.

        Args:
            device_id: Device identifier
            limit: Maximum number of history entries
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering

        Returns:
            List[Dict]: List of historical shadow entries (newest first)
        """
        query = {"device_id": device_id}

        # Add time range if provided
        if start_time or end_time:
            query["timestamp"] = {}
            if start_time:
                query["timestamp"]["$gte"] = start_time
            if end_time:
                query["timestamp"]["$lte"] = end_time

        # Query with sorting by timestamp
        cursor = self.history.find(query).sort("timestamp", -1).limit(limit)

        # Convert to list
        result = []
        async for doc in cursor:
            # Convert MongoDB _id to string
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
                del doc["_id"]

            # Convert datetime objects to ISO strings for JSON compatibility
            if isinstance(doc.get("timestamp"), datetime):
                doc["timestamp"] = doc["timestamp"].isoformat() + "Z"

            result.append(doc)

        return result

    async def add_shadow_history(
        self, device_id: str, timestamp: str, metrics: Dict[str, Any]
    ) -> None:
        """
        Add a history entry for a device shadow directly to time series collection.

        Args:
            device_id: Device identifier
            timestamp: ISO timestamp string
            metrics: Metrics data to store
        """
        # Create history entry document
        history_entry = {"device_id": device_id, "metrics": metrics}

        # Convert string timestamp to datetime if needed
        if isinstance(timestamp, str):
            try:
                # Remove Z and parse
                ts_str = timestamp.rstrip("Z")
                history_entry["timestamp"] = datetime.fromisoformat(ts_str)
            except ValueError:
                # If parsing fails, use current time
                history_entry["timestamp"] = datetime.now()
        else:
            history_entry["timestamp"] = timestamp

        # Insert into time series collection
        await self.history.insert_one(history_entry)
        logger.debug(f"Added history entry for {device_id} at {timestamp}")

    async def migrate_from_legacy(self, device_id: str = None):
        """
        Migrate data from legacy structure (embedded history) to time series collection.

        Args:
            device_id: Optional device ID to migrate. If None, migrates all devices.
        """
        if device_id:
            # Migrate single device
            try:
                shadow = await self.shadows.find_one({"device_id": device_id})
                if shadow and "history" in shadow and shadow["history"]:
                    await self._migrate_device_history(device_id, shadow["history"])
                    # Remove history from shadow
                    await self.shadows.update_one(
                        {"device_id": device_id}, {"$unset": {"history": ""}}
                    )
            except Exception as e:
                logger.error(f"Error migrating device {device_id}: {e}")
        else:
            # Migrate all devices
            cursor = self.shadows.find({})
            async for shadow in cursor:
                device_id = shadow.get("device_id")
                if device_id and "history" in shadow and shadow["history"]:
                    await self._migrate_device_history(device_id, shadow["history"])
                    # Remove history from shadow
                    await self.shadows.update_one(
                        {"device_id": device_id}, {"$unset": {"history": ""}}
                    )

    async def _migrate_device_history(self, device_id, history_entries):
        """Helper method to migrate history entries for a device"""
        bulk_ops = []

        for entry in history_entries:
            # Ensure each history entry has device_id
            entry["device_id"] = device_id

            # Convert string timestamp to datetime if needed
            if isinstance(entry.get("timestamp"), str):
                try:
                    # Remove Z and parse
                    ts_str = entry["timestamp"].rstrip("Z")
                    entry["timestamp"] = datetime.fromisoformat(ts_str)
                except ValueError:
                    # If parsing fails, use current time
                    entry["timestamp"] = datetime.now()

            # Add to bulk operation
            bulk_ops.append(InsertOne(entry))

        # Execute bulk insert if we have operations
        if bulk_ops:
            try:
                result = await self.history.bulk_write(bulk_ops, ordered=False)
                logger.info(f"Migrated {len(bulk_ops)} history entries for {device_id}")
                return len(bulk_ops)
            except Exception as e:
                logger.error(f"Error migrating history entries: {e}")
                return 0
        return 0
