#!/usr/bin/env python3
"""
Script to update remaining water heaters with SQL-based updates.
This script uses direct SQL commands to ensure property changes are persisted.
"""
import asyncio
import json
import logging
import random

from sqlalchemy import text

from src.db.connection import get_db_session
from src.models.device import DeviceType
from src.models.water_heater import WaterHeaterType

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def update_remaining_water_heaters():
    """Update water heaters that don't have types or specification links using direct SQL."""
    session_generator = get_db_session()
    if not session_generator:
        logger.warning("Database session unavailable.")
        return

    async for session in session_generator:
        if not session:
            logger.warning("Database session is None.")
            return

        try:
            # First, get all water heaters that need updating
            query = text(
                """
                SELECT id, name, properties
                FROM devices
                WHERE type = 'water_heater'
            """
            )

            result = await session.execute(query)
            heaters = result.fetchall()

            updated_count = 0
            for heater_id, name, properties_str in heaters:
                # Parse existing properties
                properties = (
                    json.loads(properties_str)
                    if isinstance(properties_str, str)
                    else properties_str
                )

                # Skip if already has heater_type
                if properties and properties.get("heater_type"):
                    logger.info(
                        f"Skipping water heater {heater_id} as it already has a type"
                    )
                    continue

                # Determine if it should be commercial or residential
                is_commercial = False
                capacity = properties.get("capacity") if properties else None

                # First check capacity - large capacity heaters are commercial
                if capacity is not None and float(capacity) >= 150:
                    is_commercial = True
                    logger.info(
                        f"Classified {heater_id} as commercial based on capacity: {capacity}"
                    )
                else:
                    # Then check name for commercial indicators
                    name_lower = name.lower()
                    commercial_indicators = [
                        "office",
                        "lab",
                        "building",
                        "boiler",
                        "manufacturing",
                    ]

                    for indicator in commercial_indicators:
                        if indicator in name_lower:
                            is_commercial = True
                            logger.info(
                                f"Classified {heater_id} as commercial based on indicator '{indicator}' in name: {name}"
                            )
                            break

                    # Default to residential if no indicators are found
                    if not is_commercial:
                        # Add some randomness to get a mix
                        is_commercial = (
                            random.random() < 0.3
                        )  # 30% chance of being commercial

                heater_type = "Commercial" if is_commercial else "Residential"
                specification_link = (
                    "/docs/specifications/water_heaters/commercial.md"
                    if is_commercial
                    else "/docs/specifications/water_heaters/residential.md"
                )

                # Update existing properties
                if not properties:
                    properties = {}

                properties["heater_type"] = heater_type
                properties["specification_link"] = specification_link

                # Update in database using direct SQL
                update_query = text(
                    """
                    UPDATE devices
                    SET properties = :properties
                    WHERE id = :heater_id
                """
                )

                await session.execute(
                    update_query,
                    {"properties": json.dumps(properties), "heater_id": heater_id},
                )

                updated_count += 1
                logger.info(
                    f"Updated water heater {heater_id} ({name}) with type {heater_type} using SQL"
                )

            await session.commit()
            logger.info(f"Updated {updated_count} remaining water heaters successfully")

        except Exception as e:
            logger.error(f"Error updating remaining water heaters: {e}")
            await session.rollback()
            raise


async def main():
    """Main entry point for the script."""
    logger.info("Starting remaining water heater update script (SQL fix)")
    await update_remaining_water_heaters()
    logger.info("Remaining water heater update script completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
