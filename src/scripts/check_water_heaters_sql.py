#!/usr/bin/env python3
"""
Script to check water heater properties directly using SQL queries.
This will help us diagnose any issues with property storage or retrieval.
"""
import asyncio
import json
import logging

from sqlalchemy import text

from src.db.connection import get_db_session
from src.models.device import DeviceType

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def check_water_heaters_sql():
    """Check water heater properties using direct SQL queries."""
    session_generator = get_db_session()
    if not session_generator:
        logger.warning("Database session unavailable.")
        return

    async for session in session_generator:
        if not session:
            logger.warning("Database session is None.")
            return

        try:
            # Use SQL to directly query the devices table and check properties
            sql = text(
                """
                SELECT id, name, properties
                FROM devices
                WHERE type = 'water_heater'
            """
            )

            result = await session.execute(sql)
            rows = result.fetchall()

            logger.info(f"Found {len(rows)} water heaters in database")

            commercial_count = 0
            residential_count = 0
            with_specs_count = 0

            for row in rows:
                device_id, name, properties_str = row

                logger.info(f"Water Heater: {name} (ID: {device_id})")
                logger.info(f"  - Raw Properties: {properties_str}")

                # Parse properties
                if properties_str:
                    properties = (
                        json.loads(properties_str)
                        if isinstance(properties_str, str)
                        else properties_str
                    )
                    heater_type = properties.get("heater_type")
                    spec_link = properties.get("specification_link")

                    if heater_type:
                        logger.info(f"  - Heater Type: {heater_type}")
                        if heater_type == "Commercial":
                            commercial_count += 1
                        elif heater_type == "Residential":
                            residential_count += 1
                    else:
                        logger.info(f"  - Heater Type: None")

                    if spec_link:
                        logger.info(f"  - Specification Link: {spec_link}")
                        with_specs_count += 1
                    else:
                        logger.info(f"  - Specification Link: None")
                else:
                    logger.info(f"  - Properties: None")

            logger.info(f"Summary:")
            logger.info(f"  - Total Water Heaters: {len(rows)}")
            logger.info(f"  - Commercial: {commercial_count}")
            logger.info(f"  - Residential: {residential_count}")
            logger.info(f"  - With Specification Links: {with_specs_count}")

        except Exception as e:
            logger.error(f"Error checking water heaters with SQL: {e}")


async def main():
    """Main entry point for the script."""
    logger.info("Starting SQL water heater check script")
    await check_water_heaters_sql()
    logger.info("SQL water heater check script completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
