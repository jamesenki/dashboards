"""
Test MongoDB connection and shadow document access
"""
import asyncio
import json
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.infrastructure.device_shadow.mongodb_shadow_storage import MongoDBShadowStorage


async def test_mongodb_connection():
    # Create MongoDB storage with explicit URI
    mongo_uri = "mongodb://localhost:27017/"
    db_name = "iotsphere"
    storage = MongoDBShadowStorage(mongo_uri=mongo_uri, db_name=db_name)

    try:
        logger.info(f"Connecting to MongoDB at {mongo_uri}, DB: {db_name}")
        await storage.initialize()
        logger.info("MongoDB connection successful!")

        # Test getting shadow for wh-001
        device_id = "wh-001"
        logger.info(f"Testing shadow document access for device {device_id}")

        # Check if shadow exists
        exists = await storage.shadow_exists(device_id)
        logger.info(f"Shadow exists for {device_id}: {exists}")

        if exists:
            # Get shadow
            shadow = await storage.get_shadow(device_id)
            logger.info(f"Got shadow document: {device_id}")
            logger.info(f"Shadow version: {shadow.get('version', 'N/A')}")
            logger.info(f"Shadow timestamp: {shadow.get('timestamp', 'N/A')}")

            # Check if history exists in the shadow
            history = shadow.get("history", [])
            logger.info(f"Shadow has {len(history)} history entries in the document")

            # Try the dedicated history API
            history_entries = await storage.get_shadow_history(device_id, limit=5)
            logger.info(f"Got {len(history_entries)} history entries from history API")

            # Print the latest history entry timestamp
            if history:
                logger.info(f"Latest history entry: {history[0]['timestamp']}")

        else:
            logger.error(f"No shadow document exists for device {device_id}")

        return True

    except Exception as e:
        logger.error(f"MongoDB connection or operation failed: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False
    finally:
        if storage.client:
            await storage.close()
            logger.info("MongoDB connection closed")


if __name__ == "__main__":
    logger.info("Testing MongoDB connection")
    success = asyncio.run(test_mongodb_connection())
    if success:
        logger.info("MongoDB tests completed successfully")
        sys.exit(0)
    else:
        logger.error("MongoDB tests failed")
        sys.exit(1)
