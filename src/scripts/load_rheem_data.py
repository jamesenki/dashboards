"""
Script to load test Rheem water heater data into the database
"""
import asyncio
import logging
from typing import List, Optional

from src.data.test_rheem_data import get_test_rheem_water_heaters
from src.db.connection import get_db_session
from src.db.repository import DeviceRepository
from src.models.rheem_water_heater import RheemWaterHeater

logger = logging.getLogger(__name__)


async def load_rheem_test_data():
    """
    Load Rheem water heater test data into the database.

    This function is called during application startup to ensure
    test data is available for UI testing and development.
    """
    logger.info("Loading Rheem water heater test data...")

    # Get database session
    session = await get_db_session()

    # If database not available, skip
    if not session:
        logger.warning("Database session is None. Skipping Rheem data loading.")
        return

    try:
        # Create repository
        repo = DeviceRepository(session)

        # Get test water heaters
        test_heaters = get_test_rheem_water_heaters()

        # Check if devices already exist
        for heater in test_heaters:
            existing = await repo.get_device(heater.id)
            if not existing:
                logger.info(
                    f"Adding test Rheem water heater: {heater.name} ({heater.id})"
                )
                await repo.create_device(heater)
            else:
                logger.info(
                    f"Test Rheem water heater already exists: {heater.name} ({heater.id})"
                )

        logger.info("Finished loading Rheem water heater test data")
    except Exception as e:
        logger.error(f"Error loading Rheem test data: {str(e)}")
    finally:
        # Close session
        if session:
            await session.close()


async def initialize_rheem_data():
    """
    Initialize the Rheem test data loading process.
    This function can be called directly from the startup event.
    """
    await load_rheem_test_data()


# For testing purposes - can run this script directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(load_rheem_test_data())
