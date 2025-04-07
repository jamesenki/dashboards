#!/usr/bin/env python3
"""
Script to check Rheem water heater types in the PostgreSQL database
"""
import asyncio
import logging
import os
import sys

import asyncpg

# Setup path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import environment loader for credentials
from src.utils.env_loader import get_db_credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get connection parameters for PostgreSQL from environment variables
db_credentials = get_db_credentials()


async def check_water_heater_types():
    """Check Rheem water heater types in the PostgreSQL database."""
    try:
        # Create direct PostgreSQL connection
        conn = await asyncpg.connect(
            host=db_credentials["host"],
            port=db_credentials["port"],
            database=db_credentials["database"],
            user=db_credentials["user"],
            password=db_credentials["password"],
        )

        # Get water heaters grouped by manufacturer and type
        all_rows = await conn.fetch(
            """
            SELECT manufacturer, type, COUNT(*)
            FROM water_heaters
            GROUP BY manufacturer, type
            ORDER BY manufacturer, type
        """
        )

        # Display overall distribution
        logger.info("\n--- Water Heater Type Distribution ---")
        for row in all_rows:
            manufacturer = row["manufacturer"] or "None"
            wh_type = row["type"] or "None"
            count = row["count"]
            logger.info(
                f"Manufacturer: {manufacturer} - Type: {wh_type} - Count: {count}"
            )

        # Get Rheem water heaters by type
        rheem_rows = await conn.fetch(
            """
            SELECT id, name, type, manufacturer, model, series
            FROM water_heaters
            WHERE manufacturer = 'Rheem'
            ORDER BY type
        """
        )

        # Organize by type
        by_type = {}
        for row in rheem_rows:
            wh_type = row["type"]
            if wh_type not in by_type:
                by_type[wh_type] = []
            by_type[wh_type].append(row)

        # Display Rheem details
        logger.info("\n--- Rheem Water Heater Details ---")
        for wh_type, heaters in by_type.items():
            logger.info(f"\nType: {wh_type} - Count: {len(heaters)}")
            for i, heater in enumerate(heaters, 1):
                logger.info(f"  {i}. ID: {heater['id']}")
                logger.info(f"     Name: {heater['name']}")
                logger.info(f"     Series: {heater['series']}")
                logger.info(f"     Model: {heater['model']}")

        # Check if we have at least 2 water heaters for each Rheem type
        logger.info("\n--- Requirements Check ---")
        all_requirements_met = True
        for wh_type in ["Tank", "Tankless", "Hybrid"]:
            count = len(by_type.get(wh_type, []))
            symbol = "✅" if count >= 2 else "❌"
            logger.info(f"Type {wh_type}: {count} {symbol}")
            if count < 2:
                all_requirements_met = False

        if all_requirements_met:
            logger.info(
                "\n✅ All requirements met: At least 2 water heaters for each Rheem type"
            )
        else:
            logger.warning(
                "\n❌ Requirements not met: Need at least 2 water heaters for each Rheem type"
            )

        # Close connection
        await conn.close()

    except Exception as e:
        logger.error(f"Error checking water heater types: {e}")
        import traceback

        logger.error(traceback.format_exc())


async def main():
    """Main entry point"""
    await check_water_heater_types()


if __name__ == "__main__":
    asyncio.run(main())
