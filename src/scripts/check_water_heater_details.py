"""
Script to check water heater details through the application API and service layers.
"""
import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# Add the parent directory to the Python path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, repo_root)

from src.db.adapters.sql_devices import SQLDeviceRepository
from src.db.connection import get_db_session
from src.models.device import DeviceType
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Force using database, not mock data
os.environ["USE_MOCK_DATA"] = "False"
# Also disable fallback to mock data if we really want to test the database
os.environ["DATABASE_FALLBACK_ENABLED"] = "False"


async def check_water_heater_details():
    """Check if we can retrieve water heater details from the service layer."""
    logger.info("Checking water heater details through service layer...")

    # Get device list from repository layer first
    session_generator = get_db_session()
    device_ids = []

    if session_generator:
        async for session in session_generator:
            try:
                sql_repo = SQLDeviceRepository(session)
                devices = await sql_repo.get_devices(
                    type_filter=DeviceType.WATER_HEATER
                )

                if devices:
                    device_ids = [device.id for device in devices]
                    logger.info(f"Found {len(device_ids)} water heater IDs in database")
                    # Just use the first 5 for testing
                    device_ids = device_ids[:5]
                    logger.info(f"Will check details for: {', '.join(device_ids)}")
                else:
                    logger.warning("No water heaters found in database")
            except Exception as e:
                logger.error(f"Error accessing devices: {str(e)}")
            finally:
                await session.close()

    if not device_ids:
        logger.error("No device IDs found to check")
        return

    # Now use the service layer to get details
    try:
        # Create service without parameters - it will use the environment variables
        logger.info("Creating water heater service...")
        service = ConfigurableWaterHeaterService()

        # First get all water heaters
        logger.info("Retrieving all water heaters...")
        all_heaters = await service.get_water_heaters()

        # Check if we got a tuple (models, from_db) or just models
        using_db = False
        if isinstance(all_heaters, tuple) and len(all_heaters) > 1:
            heaters, using_db = all_heaters
            logger.info(
                f"Retrieved {len(heaters)} water heaters, using database: {using_db}"
            )
        else:
            heaters = all_heaters
            logger.info(f"Retrieved {len(heaters)} water heaters")

        # Check if we're actually using the database or falling back to mock data
        if isinstance(all_heaters, tuple) and len(all_heaters) > 1:
            _, using_db = all_heaters
            if not using_db:
                logger.warning("Service is using MOCK DATA instead of database!")

        # Now check individual heaters
        logger.info("\nChecking individual water heater details:")
        for device_id in device_ids:
            try:
                logger.info(f"\nRetrieving details for {device_id}...")
                water_heater = await service.get_water_heater(device_id)

                # Check if we got a tuple (model, from_db)
                if isinstance(water_heater, tuple) and len(water_heater) > 1:
                    heater, using_db = water_heater
                    logger.info(f"Retrieved {device_id}, using database: {using_db}")
                    if not using_db:
                        logger.warning(f"Service used MOCK DATA for {device_id}!")
                else:
                    heater = water_heater

                if heater:
                    # Convert to dict for better printing
                    if hasattr(heater, "model_dump"):
                        heater_dict = heater.model_dump()
                    elif hasattr(heater, "dict"):
                        heater_dict = heater.dict()
                    else:
                        heater_dict = heater

                    # Collect important fields to verify
                    key_fields = {
                        "id": heater_dict.get("id"),
                        "name": heater_dict.get("name"),
                        "type": str(heater_dict.get("type")),
                        "current_temperature": heater_dict.get("current_temperature"),
                        "target_temperature": heater_dict.get("target_temperature"),
                        "mode": str(heater_dict.get("mode")),
                    }

                    logger.info(f"Key fields for {device_id}:")
                    for field, value in key_fields.items():
                        logger.info(f"  - {field}: {value}")

                    # Check for extended attributes
                    extended_fields = {
                        "readings": len(heater_dict.get("readings", [])),
                        "diagnostic_codes": len(
                            heater_dict.get("diagnostic_codes", [])
                        ),
                        "capacity": heater_dict.get("capacity"),
                        "efficiency_rating": heater_dict.get("efficiency_rating"),
                        "heater_type": str(heater_dict.get("heater_type")),
                    }

                    logger.info(f"Extended fields for {device_id}:")
                    for field, value in extended_fields.items():
                        logger.info(f"  - {field}: {value}")

                else:
                    logger.error(f"No water heater returned for ID {device_id}")

            except Exception as e:
                logger.error(f"Error retrieving water heater {device_id}: {str(e)}")
                import traceback

                logger.error(traceback.format_exc())

        # Try to get readings specifically
        if device_ids:
            sample_id = device_ids[0]
            logger.info(f"\nTrying to get readings for {sample_id}...")
            try:
                readings = await service.get_water_heater_readings(sample_id)
                logger.info(f"Retrieved {len(readings)} readings for {sample_id}")

                if readings:
                    # Look at first reading
                    first_reading = readings[0]
                    if hasattr(first_reading, "model_dump"):
                        reading_dict = first_reading.model_dump()
                    elif hasattr(first_reading, "dict"):
                        reading_dict = first_reading.dict()
                    else:
                        reading_dict = first_reading

                    logger.info(
                        f"Sample reading: {json.dumps(reading_dict, default=str)}"
                    )
            except Exception as e:
                logger.error(f"Error retrieving readings for {sample_id}: {str(e)}")
                import traceback

                logger.error(traceback.format_exc())

    except Exception as e:
        logger.error(f"Service layer error: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(check_water_heater_details())
