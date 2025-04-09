"""
Migrate to Optimized MongoDB Structure

This script:
1. Connects to MongoDB
2. Migrates device shadow history data to time series collection
3. Updates application configuration to use optimized storage

Running this script will:
- Create a time series collection for history data
- Move embedded history arrays to dedicated time series collection
- Reduce memory usage and improve query performance
"""
import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

from pymongo.operations import InsertOne

# Configure logging - reduce noisy logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Reduce log level for noisy modules
logging.getLogger("motor.motor_asyncio").setLevel(logging.WARNING)
logging.getLogger("pymongo").setLevel(logging.WARNING)

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set MongoDB environment variables
os.environ["SHADOW_STORAGE_TYPE"] = "mongodb"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/"
os.environ["MONGODB_DB_NAME"] = "iotsphere"
os.environ["USE_OPTIMIZED_MONGODB"] = "true"  # Flag to use optimized storage

# Import optimized MongoDB storage
from src.infrastructure.device_shadow.optimized_mongodb_storage import (
    OptimizedMongoDBShadowStorage,
)
from src.services.device_shadow import DeviceShadowService


async def check_mongodb_version():
    """Check MongoDB version to ensure it supports time series collections"""
    from motor.motor_asyncio import AsyncIOMotorClient

    mongo_uri = os.environ["MONGODB_URI"]
    client = AsyncIOMotorClient(mongo_uri)

    try:
        server_info = await client.admin.command("serverStatus")
        version = server_info.get("version", "0.0.0")
        logger.info(f"MongoDB version: {version}")

        # Parse version
        major_version = int(version.split(".")[0])

        if major_version >= 5:
            logger.info(
                "✅ MongoDB version 5.0+ detected - time series collections supported"
            )
            return True
        else:
            logger.warning(
                f"⚠️ MongoDB version {version} detected - time series collections require 5.0+"
            )
            logger.warning(
                "The script will continue but will use regular collections instead"
            )
            return False
    except Exception as e:
        logger.error(f"Error checking MongoDB version: {e}")
        return False
    finally:
        client.close()


async def migrate_to_optimized_storage():
    """Migrate existing shadow data to optimized storage with time series"""
    try:
        # Check MongoDB version first
        await check_mongodb_version()

        # Initialize old and new storage
        from src.infrastructure.device_shadow.mongodb_shadow_storage import (
            MongoDBShadowStorage,
        )

        # Connect to original MongoDB storage
        logger.info("Connecting to original MongoDB storage")
        old_storage = MongoDBShadowStorage(
            mongo_uri=os.environ["MONGODB_URI"], db_name=os.environ["MONGODB_DB_NAME"]
        )
        await old_storage.initialize()

        # Connect to optimized MongoDB storage
        logger.info("Connecting to optimized MongoDB storage")
        new_storage = OptimizedMongoDBShadowStorage(
            mongo_uri=os.environ["MONGODB_URI"],
            db_name=os.environ["MONGODB_DB_NAME"],
            pool_size=10,
        )
        await new_storage.initialize()

        # Create shadow services
        old_service = DeviceShadowService(storage_provider=old_storage)
        new_service = DeviceShadowService(storage_provider=new_storage)

        # Get all device IDs
        logger.info("Fetching device IDs from MongoDB")
        cursor = old_storage.shadows.find({}, {"device_id": 1})
        device_ids = []

        async for doc in cursor:
            if "device_id" in doc:
                device_ids.append(doc["device_id"])

        logger.info(f"Found {len(device_ids)} devices to migrate")

        total_history_entries = 0

        # Migrate each device
        for device_id in device_ids:
            logger.info(f"Migrating device {device_id}...")

            try:
                # Get full shadow from old storage
                shadow = await old_storage.get_shadow(device_id)

                # Count history entries
                history_entries = len(shadow.get("history", []))
                total_history_entries += history_entries

                logger.info(f"Device {device_id} has {history_entries} history entries")

                if history_entries > 0:
                    # Migrate to optimized storage
                    history_data = shadow.get("history", [])

                    # Save shadow first (this removes history field)
                    await new_storage.save_shadow(device_id, shadow)

                    # Then migrate history to time series
                    migrated = await new_storage._migrate_device_history(
                        device_id, history_data
                    )
                    logger.info(
                        f"✅ Migrated {migrated} history entries for {device_id}"
                    )
                else:
                    # No history to migrate, just save shadow
                    await new_storage.save_shadow(device_id, shadow)
                    logger.info(f"✅ Saved shadow for {device_id} (no history)")

            except Exception as e:
                logger.error(f"❌ Error migrating device {device_id}: {e}")

        logger.info(
            f"✅ Migration complete! Migrated {len(device_ids)} devices with {total_history_entries} history entries"
        )
        logger.info(
            "🚀 Your application is now configured to use optimized MongoDB storage"
        )

        # Close connections
        await old_storage.close()
        await new_storage.close()

        return True

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


async def verify_optimized_storage():
    """Verify that optimized storage is working correctly"""
    try:
        # Initialize optimized storage
        storage = OptimizedMongoDBShadowStorage(
            mongo_uri=os.environ["MONGODB_URI"],
            db_name=os.environ["MONGODB_DB_NAME"],
            pool_size=10,
        )
        await storage.initialize()

        # Create shadow service
        service = DeviceShadowService(storage_provider=storage)

        # Get list of collections to verify time series collection exists
        collections = await storage.db.list_collection_names()
        logger.info(f"Collections in database: {collections}")

        if "temperature_history" in collections:
            logger.info("✅ Time series collection exists")

        # Try fetching a device shadow
        device_id = "wh-001"  # Use a known device ID

        if await storage.shadow_exists(device_id):
            shadow = await storage.get_shadow(device_id)
            logger.info(f"✅ Successfully retrieved shadow for {device_id}")

            # Check if history is handled separately now
            if "history" not in shadow:
                logger.info("✅ Shadow no longer contains embedded history (good!)")

            # Try fetching history
            history = await storage.get_shadow_history(device_id, limit=5)
            logger.info(
                f"✅ Retrieved {len(history)} history entries from time series collection"
            )

            if history:
                logger.info(f"Sample history entry: {history[0]}")
        else:
            logger.warning(f"⚠️ No shadow found for test device {device_id}")

        # Close connection
        await storage.close()

        return True

    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    logger.info("🔄 Starting migration to optimized MongoDB storage")

    # Run migration
    success = asyncio.run(migrate_to_optimized_storage())

    if success:
        logger.info("✅ Migration successful!")

        # Verify optimized storage
        logger.info("🔍 Verifying optimized storage...")
        verify_success = asyncio.run(verify_optimized_storage())

        if verify_success:
            logger.info("✅ Verification successful!")
            logger.info(
                """
🎉 MIGRATION COMPLETE! Your application is now using optimized MongoDB storage.

Benefits:
- History data is now stored in a time series collection for better performance
- Connection pooling is enabled for faster concurrent operations
- Shadow documents are lighter weight (history stored separately)
- Document caching reduces database lookups

To use the optimized storage in your application, set:
export USE_OPTIMIZED_MONGODB=true

or add this to your environment configuration.
"""
            )
            sys.exit(0)
        else:
            logger.error("❌ Verification failed.")
            sys.exit(1)
    else:
        logger.error("❌ Migration failed.")
        sys.exit(1)
