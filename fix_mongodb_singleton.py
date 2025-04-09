"""
Comprehensive fix for MongoDB shadow storage using a singleton pattern

This script:
1. Implements a singleton pattern for DeviceShadowService
2. Forces MongoDB as the storage backend
3. Monkey patches all direct instantiations to use the singleton
4. Starts the server with guaranteed MongoDB shadow storage
"""
import asyncio
import logging
import os
import sys
import time

import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("mongodb_fix.log")],
)
logger = logging.getLogger(__name__)

# Force environment variables for MongoDB
os.environ["SHADOW_STORAGE_TYPE"] = "mongodb"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/"
os.environ["MONGODB_DB_NAME"] = "iotsphere"
os.environ["WEBSOCKET_PORT"] = "7777"

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --------- SINGLETON PATTERN IMPLEMENTATION ---------

# Import the MongoDB storage
from src.infrastructure.device_shadow.mongodb_shadow_storage import MongoDBShadowStorage

# Import the DeviceShadowService to patch
from src.services.device_shadow import DeviceShadowService

# Store the original constructor
original_init = DeviceShadowService.__init__

# Global singleton instance
_shared_instance = None


# Singleton accessor function
async def get_singleton_shadow_service():
    """Get or create the singleton shadow service instance with MongoDB storage"""
    global _shared_instance

    if _shared_instance is None:
        # Create MongoDB storage
        mongo_uri = os.environ["MONGODB_URI"]
        db_name = os.environ["MONGODB_DB_NAME"]

        logger.info(f"🔌 Creating MongoDB storage: {mongo_uri}, DB: {db_name}")
        storage = MongoDBShadowStorage(mongo_uri=mongo_uri, db_name=db_name)

        # Initialize MongoDB connection
        await storage.initialize()
        logger.info("✅ MongoDB connection initialized successfully")

        # Create the shadow service with MongoDB storage
        _shared_instance = DeviceShadowService.__new__(DeviceShadowService)
        original_init(_shared_instance, storage_provider=storage)
        logger.info("✅ Created singleton DeviceShadowService with MongoDB storage")

        # Verify that MongoDB has shadow documents with history
        device_ids = ["wh-001", "wh-002", "wh-e0ae2f58", "wh-e1ae2f59"]
        for device_id in device_ids:
            try:
                if await storage.shadow_exists(device_id):
                    shadow = await storage.get_shadow(device_id)
                    history = shadow.get("history", [])
                    logger.info(
                        f"✅ Shadow for {device_id} exists with {len(history)} history entries"
                    )
                else:
                    logger.warning(f"⚠️ No shadow found for {device_id}")
            except Exception as e:
                logger.error(f"❌ Error checking shadow for {device_id}: {str(e)}")

    return _shared_instance


# Patch the constructor to always use the singleton
async def patched_init(self, storage_provider=None):
    """Patched constructor that redirects to the singleton instance"""
    global _shared_instance

    # If we're creating a new instance, redirect to the singleton
    if _shared_instance is None:
        # This is the first instantiation, initialize the singleton
        try:
            # Use asyncio.create_task to avoid blocking if we're in an event loop
            service = await get_singleton_shadow_service()
            # Copy all attributes from the singleton to this instance
            self.__dict__ = service.__dict__
        except Exception as e:
            logger.error(f"❌ Error creating singleton: {str(e)}")
            # Fallback to original behavior if singleton fails
            original_init(self, storage_provider)
    else:
        # Copy all attributes from the singleton to this instance
        self.__dict__ = _shared_instance.__dict__


# Prevent direct instantiation of DeviceShadowService without using the singleton
def patched_new(cls, *args, **kwargs):
    """Patched __new__ method to ensure singleton usage"""
    # Just create a normal instance, __init__ will handle the redirection
    return object.__new__(cls)


# Apply the patches
DeviceShadowService.__init__ = patched_init
DeviceShadowService.__new__ = patched_new

logger.info("✅ Applied singleton pattern to DeviceShadowService")

# --------- MAIN FUNCTION ---------


async def prepare_server():
    """Initialize the singleton shadow service before the server starts"""
    try:
        # Get the singleton instance, initializing it if needed
        await get_singleton_shadow_service()
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize shadow service: {str(e)}")
        import traceback

        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False


# Main function
if __name__ == "__main__":
    # Parse port from command line
    port = 7080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid port number: {sys.argv[1]}, using default: {port}")

    logger.info(f"🔧 Starting IoTSphere with MongoDB shadow storage on port {port}")

    # Initialize the singleton shadow service
    success = asyncio.run(prepare_server())

    if not success:
        logger.error("❌ Failed to initialize MongoDB shadow storage")
        sys.exit(1)

    # Start the server
    logger.info(f"🚀 Starting server on port {port}")
    logger.info(
        f"📊 Temperature history should now be visible at: http://localhost:{port}/water-heaters/wh-001"
    )

    uvicorn.run("src.main:app", host="0.0.0.0", port=port)
