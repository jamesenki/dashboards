"""
Monkey patch to force MongoDB shadow storage in IoTSphere

This script directly patches the create_shadow_storage_provider function
to always return MongoDB shadow storage, bypassing the fallback mechanism.
"""
import asyncio
import logging
import os
import sys

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Force environment variables
os.environ["SHADOW_STORAGE_TYPE"] = "mongodb"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/"
os.environ["MONGODB_DB_NAME"] = "iotsphere"
os.environ["WEBSOCKET_PORT"] = "7777"

from src.infrastructure.device_shadow.mongodb_shadow_storage import MongoDBShadowStorage

# Import the storage factory
from src.infrastructure.device_shadow.storage_factory import (
    create_shadow_storage_provider,
)

# Store the original function
original_create_shadow_storage_provider = create_shadow_storage_provider


# Create a patched version that always returns MongoDB storage
async def patched_create_shadow_storage_provider(config=None):
    """
    Patched version that always returns MongoDB storage
    """
    logger.info("🛠️ Using patched shadow storage provider - FORCING MongoDB")

    # Create MongoDB storage directly
    mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
    db_name = os.environ.get("MONGODB_DB_NAME", "iotsphere")

    logger.info(f"🔌 Connecting to MongoDB at {mongo_uri}, DB: {db_name}")
    storage = MongoDBShadowStorage(mongo_uri=mongo_uri, db_name=db_name)

    try:
        # Initialize MongoDB connection
        await storage.initialize()
        logger.info("✅ MongoDB connection successful")

        # Verify shadows exist
        device_ids = ["wh-001", "wh-002", "wh-e0ae2f58", "wh-e1ae2f59"]
        for device_id in device_ids:
            if await storage.shadow_exists(device_id):
                shadow = await storage.get_shadow(device_id)
                history = shadow.get("history", [])
                logger.info(
                    f"✅ Shadow for {device_id} exists with {len(history)} history entries"
                )
            else:
                logger.warning(f"⚠️ No shadow found for {device_id}")

        return storage

    except Exception as e:
        logger.error(f"❌ MongoDB initialization failed: {str(e)}")
        import traceback

        logger.error(f"Stack trace: {traceback.format_exc()}")

        # Here's the key: Instead of falling back to InMemoryShadowStorage,
        # we raise an exception to make the issue visible
        raise RuntimeError(
            f"MongoDB shadow storage MUST be used, but failed to initialize: {str(e)}"
        )


# Apply the monkey patch
import src.infrastructure.device_shadow.storage_factory

src.infrastructure.device_shadow.storage_factory.create_shadow_storage_provider = (
    patched_create_shadow_storage_provider
)

logger.info("✅ MongoDB shadow storage patch applied")

# Run the server with the patch
if __name__ == "__main__":
    # Get port from arguments
    port = 7080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass

    logger.info(
        f"🚀 Starting IoTSphere with PATCHED MongoDB shadow storage on port {port}"
    )

    # Start the server
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=port)
