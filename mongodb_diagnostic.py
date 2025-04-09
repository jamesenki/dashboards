"""
MongoDB Diagnostic Script

This script directly tests the MongoDB connection and verifies
that shadow documents are accessible with history data.
"""
import asyncio
import json
import logging
import sys
from datetime import datetime

import motor.motor_asyncio

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("mongodb_diagnostic.log")],
)
logger = logging.getLogger(__name__)


async def test_mongodb_connection():
    """Test basic MongoDB connection"""
    mongo_uri = "mongodb://localhost:27017/"
    db_name = "iotsphere"
    collection_name = "device_shadows"

    logger.info(f"Attempting to connect to MongoDB at {mongo_uri}")

    # Connect directly using motor
    client = None
    try:
        # Create the MongoDB client
        client = motor.motor_asyncio.AsyncIOMotorClient(
            mongo_uri, serverSelectionTimeoutMS=5000  # 5 second timeout
        )

        # Force a connection check
        await client.server_info()
        logger.info("✅ Successfully connected to MongoDB server")

        # Check if database exists
        db_list = await client.list_database_names()
        logger.info(f"Available databases: {db_list}")

        if db_name in db_list:
            logger.info(f"✅ Database '{db_name}' exists")
        else:
            logger.error(f"❌ Database '{db_name}' does not exist")
            return False

        # Access the database
        db = client[db_name]

        # Check if collections exist
        collection_list = await db.list_collection_names()
        logger.info(f"Collections in {db_name}: {collection_list}")

        if collection_name in collection_list:
            logger.info(f"✅ Collection '{collection_name}' exists")
        else:
            logger.error(f"❌ Collection '{collection_name}' does not exist")
            return False

        # Count documents in the shadows collection
        shadows = db[collection_name]
        count = await shadows.count_documents({})
        logger.info(f"📊 Found {count} shadow documents in {collection_name}")

        if count == 0:
            logger.error("❌ No shadow documents found")
            return False

        # Check a specific shadow document
        device_id = "wh-001"
        shadow = await shadows.find_one({"device_id": device_id})

        if shadow:
            logger.info(f"✅ Successfully retrieved shadow for {device_id}")
            logger.info(f"📊 Shadow version: {shadow.get('version')}")

            # Check for history in the shadow
            history = shadow.get("history", [])
            logger.info(f"📊 Shadow has {len(history)} history entries")

            if history:
                logger.info(f"✅ Shadow has history data")
                # Show a sample of the first history entry
                if len(history) > 0:
                    logger.info(
                        f"📊 Sample history entry: {json.dumps(history[0], indent=2)}"
                    )
            else:
                logger.error(f"❌ No history data found in shadow")
                return False
        else:
            logger.error(f"❌ Shadow for {device_id} not found")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ MongoDB connection error: {str(e)}")
        import traceback

        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False

    finally:
        if client:
            client.close()
            logger.info("MongoDB connection closed")


async def diagnostic():
    """Run all diagnostics"""
    logger.info("=== MongoDB Diagnostic Tool ===")

    # Test MongoDB connection
    connection_result = await test_mongodb_connection()

    if connection_result:
        logger.info("✅ MongoDB diagnostic tests PASSED")
        logger.info(
            "MongoDB is properly configured and shadow documents with history exist"
        )
        return True
    else:
        logger.error("❌ MongoDB diagnostic tests FAILED")
        logger.error("Please check the logs for detailed error information")
        return False


if __name__ == "__main__":
    logger.info("Starting MongoDB diagnostic")
    result = asyncio.run(diagnostic())

    if result:
        logger.info("✅ All tests passed! MongoDB is properly configured")
        sys.exit(0)
    else:
        logger.error("❌ Tests failed! See logs for details")
        sys.exit(1)
