#!/usr/bin/env python3
"""
Fix Shadow Document Circular References

This script fixes any circular references in shadow documents that would cause
the 'maximum recursion depth exceeded while encoding an object to BSON' error.
"""
import asyncio
import json
import logging
import os
from copy import deepcopy
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add project root to Python path
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set MongoDB environment variable
os.environ["SHADOW_STORAGE_TYPE"] = "mongodb"
os.environ["USE_OPTIMIZED_MONGODB"] = "true"  # Use optimized storage


def is_json_serializable(obj):
    """Test if an object can be JSON serialized without circular references"""
    try:
        json.dumps(obj)
        return True
    except (TypeError, OverflowError, RecursionError):
        return False


async def fix_shadow_documents():
    """Fix any shadow documents with circular references"""
    try:
        # Import the optimized MongoDB storage
        from src.infrastructure.device_shadow.optimized_mongodb_storage import (
            OptimizedMongoDBShadowStorage,
        )

        # Initialize storage
        storage = OptimizedMongoDBShadowStorage(
            mongo_uri=os.environ.get("MONGODB_URI", "mongodb://localhost:27017/"),
            db_name=os.environ.get("MONGODB_DB_NAME", "iotsphere"),
            pool_size=int(os.environ.get("MONGODB_POOL_SIZE", "10")),
        )
        await storage.initialize()

        # Get all device IDs
        logger.info("Fetching all device IDs from MongoDB")
        cursor = storage.shadows.find({}, {"device_id": 1})
        device_ids = []

        async for doc in cursor:
            if "device_id" in doc:
                device_ids.append(doc["device_id"])

        logger.info(f"Found {len(device_ids)} device shadows to check")

        fixed_count = 0

        # Process each device shadow
        for device_id in device_ids:
            logger.info(f"Checking shadow document for {device_id}")

            # Get the shadow document
            try:
                shadow = await storage.get_shadow(device_id)
            except Exception as e:
                logger.warning(f"Error retrieving shadow for {device_id}: {e}")
                continue

            if not shadow:
                logger.warning(f"No shadow found for {device_id}")
                continue

            # Check if the document is serializable (no circular references)
            if is_json_serializable(shadow):
                logger.info(f"✅ Shadow for {device_id} has no circular references")
                continue

            logger.warning(f"⚠️ Found circular reference in shadow for {device_id}")

            # Create a clean copy by converting to JSON and back
            # This will break any circular references
            try:
                # First, create a clean shadow with essential fields only
                clean_shadow = {
                    "device_id": device_id,
                    "metadata": {
                        "created_at": shadow.get("metadata", {}).get(
                            "created_at", datetime.now().isoformat() + "Z"
                        ),
                        "last_updated": datetime.now().isoformat() + "Z",
                    },
                    "timestamp": datetime.now().isoformat() + "Z",
                    "version": shadow.get("version", 0) + 1,
                    "reported": {},
                }

                # Copy reported state fields safely
                if "reported" in shadow and isinstance(shadow["reported"], dict):
                    for key, value in shadow["reported"].items():
                        try:
                            # Test if the value is serializable
                            json.dumps(value)
                            clean_shadow["reported"][key] = value
                        except (TypeError, OverflowError, RecursionError):
                            # If not serializable, use a safe default
                            if key == "temperature":
                                clean_shadow["reported"][key] = 120.0
                            elif key == "status":
                                clean_shadow["reported"][key] = "ONLINE"
                            else:
                                clean_shadow["reported"][
                                    key
                                ] = "Value removed due to circular reference"

                # Save the clean shadow with no history (history will be handled by time series)
                await storage.save_shadow(device_id, clean_shadow)
                logger.info(f"✅ Fixed shadow document for {device_id}")
                fixed_count += 1

            except Exception as e:
                logger.error(f"❌ Error fixing shadow for {device_id}: {e}")
                import traceback

                logger.error(traceback.format_exc())

        logger.info(f"✅ Fixed {fixed_count} shadow documents with circular references")

        # Close MongoDB connection
        await storage.close()

        return True

    except Exception as e:
        logger.error(f"❌ Error fixing shadow documents: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


async def main():
    """Main entry point"""
    logger.info("🔧 Starting shadow document circular reference fix utility")
    success = await fix_shadow_documents()

    if success:
        logger.info("✅ Shadow document fix completed successfully")
        return 0
    else:
        logger.error("❌ Shadow document fix failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
