#!/usr/bin/env python3
"""
Reset Shadow Storage Script for IoTSphere

Following TDD principles, this script resets the shadow storage to ensure
it matches the expected state defined in our tests. This allows us to properly
register our updated mock devices.
"""
import asyncio
import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def reset_shadow_storage():
    """Reset the shadow storage by deleting all shadow documents."""
    # Ensure root directory is in the Python path
    root_dir = os.path.dirname(os.path.abspath(__file__))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

    # Import shadow storage provider
    from src.infrastructure.device_shadow.storage_factory import (
        create_shadow_storage_provider,
    )

    # Create shadow storage provider
    storage_provider = await create_shadow_storage_provider()

    # Get all device IDs
    try:
        device_ids = await storage_provider.get_all_device_ids()
        logger.info(f"Found {len(device_ids)} devices in shadow storage")

        # Delete each shadow document
        for device_id in device_ids:
            logger.info(f"Deleting shadow document for device {device_id}")
            await storage_provider.delete_shadow_document(device_id)

        logger.info("Shadow storage reset complete")
        return True
    except Exception as e:
        logger.error(f"Error resetting shadow storage: {e}")
        return False


async def run():
    """Run the reset and optionally restart the server."""
    await reset_shadow_storage()


if __name__ == "__main__":
    asyncio.run(run())
