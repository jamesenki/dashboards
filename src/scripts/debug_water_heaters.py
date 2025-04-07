"""
Script to debug water heater data structure from database.
This will print out the actual structure of water heaters retrieved from the database
so we can validate against the correct fields.
"""
import asyncio
import json
import logging
import os
import sys

# Add the parent directory to the Python path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, repo_root)

from src.db.adapters.sql_devices import SQLDeviceRepository
from src.db.connection import get_db_session
from src.models.device import DeviceType

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Set environment variables to force database use and prevent mock fallback
os.environ["USE_MOCK_DATA"] = "False"


async def print_water_heater_structure():
    """Print the structure of water heaters from the database."""
    logger.info("Retrieving water heaters from database...")

    # Get a database session
    session_generator = get_db_session()

    if not session_generator:
        logger.error("Failed to get database session")
        return

    async for session in session_generator:
        try:
            # Create SQL repository for direct database access
            sql_repo = SQLDeviceRepository(session)

            # Get all water heaters directly from SQL repository
            devices = await sql_repo.get_devices(type_filter=DeviceType.WATER_HEATER)

            if not devices:
                logger.warning("No water heaters found in database")
                return

            # Print count of water heaters
            logger.info(f"Found {len(devices)} water heaters in database")

            # Print device IDs
            logger.info("Water heater IDs:")
            for device in devices:
                if hasattr(device, "id"):
                    logger.info(f"  - {device.id}")

            # Get the first water heater for inspection
            if devices:
                first_device = devices[0]
                logger.info(f"\nFirst water heater ({first_device.id}) details:")

                # Convert to dict for better printing
                if hasattr(first_device, "model_dump"):
                    device_dict = first_device.model_dump()
                elif hasattr(first_device, "dict"):
                    device_dict = first_device.dict()
                else:
                    device_dict = first_device

                # Pretty print the device structure
                logger.info(json.dumps(device_dict, indent=2, default=str))

                # Print all available keys/properties
                logger.info("\nAvailable fields:")
                for key in device_dict.keys():
                    logger.info(f"  - {key}")

                # Debug for specific water heater causing errors
                target_id = "aqua-wh-tankless-001"
                for device in devices:
                    if hasattr(device, "id") and device.id == target_id:
                        logger.info(f"\nFound {target_id} - checking its structure:")

                        if hasattr(device, "model_dump"):
                            prob_device = device.model_dump()
                        elif hasattr(device, "dict"):
                            prob_device = device.dict()
                        else:
                            prob_device = device

                        # Print available fields
                        logger.info(f"Fields present in {target_id}:")
                        for key in prob_device.keys():
                            logger.info(f"  - {key}: {prob_device[key]}")

                        break
                else:
                    logger.warning(f"Could not find water heater {target_id}")

        except Exception as e:
            logger.error(f"Error debugging water heaters: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())

            # Try to get the device class structure directly
            if devices and len(devices) > 0:
                first_device = devices[0]
                logger.info(f"Object type: {type(first_device)}")
                if hasattr(first_device, "__dict__"):
                    logger.info(f"Object attributes: {first_device.__dict__.keys()}")

        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(print_water_heater_structure())
