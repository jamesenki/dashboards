#!/usr/bin/env python
"""
Script to check the distribution of water heater types in PostgreSQL.
Ensures we have at least 2 water heaters per type.
"""
import asyncio
import logging
import os
import sys
from collections import defaultdict

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add parent directory to path to import project modules
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Import required modules
try:
    from src.db.config import db_settings
    from src.models.water_heater import WaterHeater
    from src.repositories.postgres_water_heater_repository import (
        PostgresWaterHeaterRepository,
    )
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    sys.exit(1)


async def check_water_heater_types():
    """Check that we have at least 2 water heaters per type in PostgreSQL."""
    # Set environment to development
    os.environ["IOTSPHERE_ENV"] = "development"

    # Initialize PostgreSQL repository
    try:
        postgres_repo = PostgresWaterHeaterRepository(
            host=db_settings.DB_HOST,
            port=db_settings.DB_PORT,
            database=db_settings.DB_NAME,
            user=db_settings.DB_USER,
            password=db_settings.DB_PASSWORD,
        )

        # Initialize the repository
        await postgres_repo._initialize()

        # Get all water heaters
        water_heaters = await postgres_repo.get_water_heaters()
        logger.info(f"Found {len(water_heaters)} water heaters in PostgreSQL database")

        # Count water heaters by type
        types_count = defaultdict(list)
        for heater in water_heaters:
            heater_type = str(heater.type.value) if heater.type else "None"
            types_count[heater_type].append(heater.id)

        # Display results
        logger.info("\n--- Water Heater Types Distribution ---")
        all_requirements_met = True

        for heater_type, heater_ids in types_count.items():
            count = len(heater_ids)
            status = "✅" if count >= 2 else "❌"
            logger.info(f"{status} Type: {heater_type} - Count: {count}")

            if count < 2:
                all_requirements_met = False
                logger.info(f"   IDs: {', '.join(heater_ids)}")

        if all_requirements_met:
            logger.info("\n✅ All water heater types have at least 2 instances.")
        else:
            logger.warning("\n❌ Some water heater types have fewer than 2 instances.")

    except Exception as e:
        logger.error(f"Error checking water heater types: {e}")
        import traceback

        logger.error(traceback.format_exc())
    finally:
        # Close the database connection
        if "postgres_repo" in locals() and postgres_repo.pool:
            await postgres_repo.pool.close()
            logger.info("Closed PostgreSQL connection pool")


if __name__ == "__main__":
    asyncio.run(check_water_heater_types())
