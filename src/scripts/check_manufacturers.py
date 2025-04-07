#!/usr/bin/env python
"""
Script to check what manufacturers are actually in the PostgreSQL database
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
    from src.repositories.postgres_water_heater_repository import (
        PostgresWaterHeaterRepository,
    )
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    sys.exit(1)


async def check_manufacturers():
    """Check what manufacturers are actually in the PostgreSQL database."""
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

        # Count water heaters by manufacturer
        manufacturers_count = defaultdict(list)
        brands_count = defaultdict(list)

        # Print full water heater details
        logger.info("\n--- Water Heater Details ---")
        for heater in water_heaters:
            logger.info(f"ID: {heater.id}")
            logger.info(f"  Name: {heater.name}")
            logger.info(f"  Manufacturer: {heater.manufacturer}")
            logger.info(f"  Brand: {heater.brand}")
            logger.info(f"  Model: {heater.model}")
            logger.info(f"  Type: {heater.type}")

            manufacturers_count[str(heater.manufacturer)].append(heater.id)
            brands_count[str(heater.brand)].append(heater.id)

        # Display manufacturer distribution
        logger.info("\n--- Manufacturer Distribution ---")
        for manufacturer, heater_ids in manufacturers_count.items():
            count = len(heater_ids)
            logger.info(f"Manufacturer: {manufacturer} - Count: {count}")
            logger.info(
                f"  IDs: {', '.join(heater_ids[:5])}"
                + (", ..." if len(heater_ids) > 5 else "")
            )

        # Display brand distribution
        logger.info("\n--- Brand Distribution ---")
        for brand, heater_ids in brands_count.items():
            count = len(heater_ids)
            logger.info(f"Brand: {brand} - Count: {count}")
            logger.info(
                f"  IDs: {', '.join(heater_ids[:5])}"
                + (", ..." if len(heater_ids) > 5 else "")
            )

        # Check if we have at least 2 water heaters for Rheem and AquaTherm
        rheem_count = len(manufacturers_count.get("Rheem", []))
        aquatherm_count = len(manufacturers_count.get("AquaTherm", []))

        logger.info("\n--- Requirements Check ---")
        logger.info(
            f"Rheem water heaters: {rheem_count} {'✅' if rheem_count >= 2 else '❌'}"
        )
        logger.info(
            f"AquaTherm water heaters: {aquatherm_count} {'✅' if aquatherm_count >= 2 else '❌'}"
        )

        if rheem_count >= 2 and aquatherm_count >= 2:
            logger.info("✅ Requirements met: At least 2 water heaters per manufacturer")
        else:
            logger.warning(
                "❌ Requirements not met: Need at least 2 water heaters for each manufacturer"
            )

    except Exception as e:
        logger.error(f"Error checking manufacturers: {e}")
        import traceback

        logger.error(traceback.format_exc())
    finally:
        # Close the database connection
        if "postgres_repo" in locals() and postgres_repo.pool:
            await postgres_repo.pool.close()
            logger.info("Closed PostgreSQL connection pool")


if __name__ == "__main__":
    asyncio.run(check_manufacturers())
