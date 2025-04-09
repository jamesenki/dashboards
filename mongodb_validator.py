"""
MongoDB Shadow Storage Validator
This script validates the MongoDB connection and shadow storage configuration
to help diagnose why the main application is falling back to in-memory storage.
"""
import asyncio
import logging
import os
import sys
import traceback
from typing import Any, Dict

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def validate_mongodb():
    """Validate MongoDB connection and shadow storage"""
    # Direct MongoDB validation
    try:
        import motor.motor_asyncio

        logger.info("✅ motor package is installed")
    except ImportError:
        logger.error(
            "❌ motor package is not installed! This is required for MongoDB connection"
        )
        return False

    # Test direct MongoDB connection
    try:
        mongo_uri = "mongodb://localhost:27017/"
        logger.info(f"Connecting directly to MongoDB at {mongo_uri}")
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        db = client["iotsphere"]
        await db.command({"ping": 1})
        logger.info("✅ Direct MongoDB connection successful")
    except Exception as e:
        logger.error(f"❌ Direct MongoDB connection failed: {str(e)}")
        logger.error(traceback.format_exc())
        return False

    # Import and test shadow storage
    try:
        from src.infrastructure.device_shadow.mongodb_shadow_storage import (
            MongoDBShadowStorage,
        )

        logger.info("✅ MongoDB shadow storage class is available")

        # Create and initialize storage
        storage = MongoDBShadowStorage()
        logger.info("MongoDB shadow storage instance created")

        # Initialize connection
        try:
            await storage.initialize()
            logger.info("✅ MongoDB shadow storage initialized successfully")
        except Exception as e:
            logger.error(f"❌ MongoDB shadow storage initialization failed: {str(e)}")
            logger.error(traceback.format_exc())
            return False

        # Test shadow operations
        try:
            device_id = "wh-001"
            exists = await storage.shadow_exists(device_id)
            logger.info(f"Shadow exists for {device_id}: {exists}")

            if exists:
                shadow = await storage.get_shadow(device_id)
                logger.info(f"✅ Successfully retrieved shadow for {device_id}")
                logger.info(f"Shadow version: {shadow.get('version')}")

                # Check history
                history = shadow.get("history", [])
                logger.info(f"Shadow contains {len(history)} history entries")
            else:
                logger.warning(f"No shadow document exists for {device_id}")

            await storage.close()
            logger.info("MongoDB connection closed")

        except Exception as e:
            logger.error(f"❌ Error in shadow operations: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    except Exception as e:
        logger.error(f"❌ Error importing or using MongoDB shadow storage: {str(e)}")
        logger.error(traceback.format_exc())
        return False

    # Test shadow storage factory
    try:
        from src.infrastructure.device_shadow.storage_factory import (
            create_shadow_storage_provider,
        )

        logger.info("✅ Shadow storage factory is available")

        # Create storage provider with MongoDB config
        config = {
            "storage_type": "mongodb",
            "mongo_uri": "mongodb://localhost:27017/",
            "mongo_db_name": "iotsphere",
        }

        logger.info(f"Creating shadow storage with config: {config}")
        storage = await create_shadow_storage_provider(config)

        # Check storage type
        logger.info(f"Created storage type: {type(storage).__name__}")
        from src.infrastructure.device_shadow.mongodb_shadow_storage import (
            MongoDBShadowStorage,
        )

        if isinstance(storage, MongoDBShadowStorage):
            logger.info("✅ Factory correctly created MongoDB storage")
        else:
            logger.error("❌ Factory created wrong storage type!")
            return False

    except Exception as e:
        logger.error(f"❌ Error in shadow storage factory: {str(e)}")
        logger.error(traceback.format_exc())
        return False

    logger.info("✅ All MongoDB validation checks passed!")
    return True


if __name__ == "__main__":
    logger.info("Running MongoDB Shadow Storage Validator")
    result = asyncio.run(validate_mongodb())

    if result:
        logger.info("✅ VALIDATION SUCCESS: MongoDB shadow storage is working correctly")
        sys.exit(0)
    else:
        logger.error("❌ VALIDATION FAILED: MongoDB shadow storage has issues")
        sys.exit(1)
