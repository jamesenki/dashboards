"""
Script to load test AquaTherm (Rheem) water heater test data into the database
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Optional

from src.data.test_rheem_data import get_test_rheem_water_heaters
from src.db.connection import get_db_session
from src.db.repository import DeviceRepository

logger = logging.getLogger(__name__)


async def load_aquatherm_test_data():
    """
    Load AquaTherm (Rheem) water heater test data into the database.

    This function is called during application startup to ensure
    test data is available for UI testing and development.

    Following TDD principles, we are updating the implementation to match
    our test expectations without changing the tests themselves.
    """
    logger.info("Loading AquaTherm (Rheem) water heater test data...")

    # Get database session generator
    session_generator = get_db_session()

    # If database session generator not available, skip
    if not session_generator:
        logger.warning(
            "Database session generator is None. Skipping AquaTherm data loading."
        )
        return

    # Use async generator correctly
    async for session in session_generator:
        # If session is not valid, skip
        if not session:
            logger.warning("Database session is None. Skipping AquaTherm data loading.")
            return

        try:
            # Create repository
            repo = DeviceRepository(session)

            # Get water heaters from test_rheem_data.py which contains 16 properly configured water heaters
            # All with manufacturer="Rheem" and valid product series
            aquatherm_heaters = get_test_rheem_water_heaters()

            # First, let's clear any existing water heaters to start fresh
            try:
                # Get all existing water heaters using DeviceRepository methods
                # The DeviceRepository doesn't have get_devices_by_type so we need to get all devices
                # and filter by device type
                all_devices = await repo.get_all_devices()
                for device in all_devices:
                    # Check if it's a water heater by its ID or attributes
                    if hasattr(device, "id") and (
                        "water_heater" in device.id
                        or "wh-" in device.id
                        or "aqua-wh" in device.id
                    ):
                        logger.info(f"Removing existing water heater: {device.id}")
                        await repo.delete_device(device.id)
            except Exception as e:
                logger.warning(f"Error while removing existing water heaters: {str(e)}")

            # Loop over and save all water heaters from test_rheem_data.py
            for i, water_heater in enumerate(aquatherm_heaters):
                # Log water heater that we're saving
                logger.info(
                    f"Saving AquaTherm water heater {i+1}/{len(aquatherm_heaters)}: {water_heater.id} - {water_heater.name}"
                )

                # Create the new water heater using the repository method
                await repo.create_device(water_heater)

            # Commit transaction - session is handled by the repository, so we don't need to commit explicitly

            # Log success
            logger.info(
                f"Successfully loaded {len(aquatherm_heaters)} AquaTherm water heaters."
            )

        except Exception as e:
            # Log error
            logger.error(f"Error loading AquaTherm water heater test data: {str(e)}")

            # Re-raise exception
            raise


async def initialize_aquatherm_data():
    """
    Initialize the AquaTherm test data loading process.
    This function can be called directly from the startup event.
    """
    await load_aquatherm_test_data()


# For testing purposes - can run this script directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(initialize_aquatherm_data())
