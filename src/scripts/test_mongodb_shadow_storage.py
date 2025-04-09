"""
Test script for MongoDB shadow storage.

This script validates that our MongoDB shadow storage implementation works
correctly with real device shadows.
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

# Add parent directory to path so we can import modules
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from src.infrastructure.device_shadow.mongodb_shadow_storage import MongoDBShadowStorage
from src.services.device_shadow import DeviceShadowService

# Set MongoDB environment variables
os.environ["SHADOW_STORAGE_TYPE"] = "mongodb"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/"
os.environ["MONGODB_DB_NAME"] = "iotsphere_test"


async def test_mongodb_shadow_storage():
    """Test MongoDB shadow storage functionality."""
    logger.info("Testing MongoDB shadow storage...")

    # Create MongoDB storage provider
    mongo_storage = MongoDBShadowStorage(
        mongo_uri=os.environ["MONGODB_URI"], db_name=os.environ["MONGODB_DB_NAME"]
    )

    try:
        # Initialize storage
        await mongo_storage.initialize()
        logger.info("MongoDB connection successful")

        # Clean up any existing test data
        await mongo_storage.drop_collections()
        logger.info("Test collections dropped")

        # Create device shadow service using MongoDB storage
        shadow_service = DeviceShadowService(storage_provider=mongo_storage)

        # Test device ID
        test_device_id = "wh-test-device"

        # Check if shadow exists (should not initially)
        exists = await mongo_storage.shadow_exists(test_device_id)
        logger.info(f"Shadow exists before creation: {exists}")
        assert not exists, "Shadow should not exist yet"

        # Create test shadow
        current_time = datetime.now(timezone.utc).isoformat()
        test_shadow = {
            "device_id": test_device_id,
            "reported": {
                "temperature": 120,
                "status": "active",
                "lastUpdated": current_time,
            },
            "desired": {"temperature": 125},
            "metadata": {"version": 1, "last_updated": current_time},
        }

        # Save shadow
        await shadow_service.create_device_shadow(
            device_id=test_device_id,
            reported_state=test_shadow["reported"],
            desired_state=test_shadow["desired"],
        )
        logger.info(f"Created test shadow for {test_device_id}")

        # Verify shadow exists now
        exists = await mongo_storage.shadow_exists(test_device_id)
        logger.info(f"Shadow exists after creation: {exists}")
        assert exists, "Shadow should exist after creation"

        # Retrieve shadow and verify contents
        shadow = await shadow_service.get_device_shadow(test_device_id)
        logger.info(f"Retrieved shadow: {shadow}")
        assert shadow["device_id"] == test_device_id, "Device ID mismatch"
        assert "reported" in shadow, "Missing reported state"
        assert "desired" in shadow, "Missing desired state"
        assert shadow["reported"]["temperature"] == 120, "Temperature mismatch"

        # Update shadow
        await shadow_service.update_device_shadow(
            device_id=test_device_id,
            reported_state={"temperature": 130, "status": "active"},
        )
        logger.info("Updated shadow reported state")

        # Verify update
        updated_shadow = await shadow_service.get_device_shadow(test_device_id)
        logger.info(f"Retrieved updated shadow: {updated_shadow}")
        assert (
            updated_shadow["reported"]["temperature"] == 130
        ), "Updated temperature mismatch"

        # Test shadow history (requires additional implementation)
        if hasattr(mongo_storage, "get_shadow_history"):
            history = await mongo_storage.get_shadow_history(test_device_id)
            logger.info(f"Shadow history entries: {len(history)}")
            if history:
                logger.info(f"First history entry: {history[0]}")

        # Clean up
        deleted = await mongo_storage.delete_shadow(test_device_id)
        logger.info(f"Shadow deleted: {deleted}")

        # Verify deletion
        exists = await mongo_storage.shadow_exists(test_device_id)
        logger.info(f"Shadow exists after deletion: {exists}")
        assert not exists, "Shadow should not exist after deletion"

        logger.info("All tests passed successfully!")
        return True

    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        # Clean up by dropping collections
        await mongo_storage.drop_collections()
        await mongo_storage.close()


async def main():
    """Main entry point for the script."""
    success = await test_mongodb_shadow_storage()
    if success:
        logger.info("MongoDB shadow storage test completed successfully")
    else:
        logger.error("MongoDB shadow storage test failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
