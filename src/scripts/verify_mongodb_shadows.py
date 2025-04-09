"""
Verify MongoDB shadow storage implementation.

This script verifies that shadow documents are properly stored in MongoDB
and lists all the shadow documents that have been created.
"""
import asyncio
import logging
import os
import sys

from pymongo import MongoClient

# Add parent directory to path so we can import modules
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def verify_mongodb_shadows():
    """Verify shadow documents in MongoDB"""
    # Get MongoDB connection settings from environment or use defaults
    mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
    db_name = os.environ.get("MONGODB_DB_NAME", "iotsphere")
    collection_name = "device_shadows"

    logger.info(f"Connecting to MongoDB at {mongo_uri}")
    client = MongoClient(mongo_uri)
    db = client[db_name]
    shadows_collection = db[collection_name]

    # Count total shadows
    total_shadows = shadows_collection.count_documents({})
    logger.info(f"Found {total_shadows} shadow documents in MongoDB")

    # List all shadows
    logger.info("Listing all shadow documents:")
    for shadow in shadows_collection.find({}, {"device_id": 1, "version": 1, "_id": 0}):
        logger.info(f"  - {shadow}")

    # Count water heater shadows specifically
    wh_shadows = shadows_collection.count_documents({"device_id": {"$regex": "^wh-"}})
    logger.info(f"Found {wh_shadows} water heater shadow documents")

    # Verify shadow structure
    logger.info("Checking shadow document structure:")
    if total_shadows > 0:
        sample = shadows_collection.find_one({})
        logger.info(f"Sample shadow fields: {list(sample.keys())}")

        # Check for required fields
        required_fields = ["device_id", "reported", "desired", "version", "metadata"]
        missing_fields = [field for field in required_fields if field not in sample]

        if missing_fields:
            logger.warning(f"Missing required fields in shadow: {missing_fields}")
        else:
            logger.info("All required fields present in shadow documents")

    # Verify shadow history collection
    history_collection = db["shadow_history"]
    history_count = history_collection.count_documents({})
    logger.info(f"Found {history_count} shadow history records")

    client.close()
    return total_shadows > 0


async def main():
    """Main entry point"""
    try:
        logger.info("Verifying MongoDB shadow documents...")
        success = await verify_mongodb_shadows()

        if success:
            logger.info("Shadow documents successfully verified in MongoDB")
            return 0
        else:
            logger.error("No shadow documents found in MongoDB")
            return 1
    except Exception as e:
        logger.error(f"Error verifying MongoDB shadows: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
