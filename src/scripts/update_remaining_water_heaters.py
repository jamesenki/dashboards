#!/usr/bin/env python3
"""
Script to update remaining water heaters that don't have types or specification links.
"""
import asyncio
import logging
import random
from datetime import datetime, timedelta

from sqlalchemy import select, update

from src.db.connection import get_db_session
from src.db.models import DeviceModel
from src.models.device import DeviceType
from src.models.water_heater import WaterHeaterType

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def update_remaining_water_heaters():
    """Update water heaters that don't have types or specification links."""
    session_generator = get_db_session()
    if not session_generator:
        logger.warning("Database session unavailable.")
        return

    async for session in session_generator:
        if not session:
            logger.warning("Database session is None.")
            return

        try:
            # Find water heaters without heater_type
            query = select(DeviceModel).where(
                DeviceModel.type == DeviceType.WATER_HEATER
            )
            result = await session.execute(query)
            heaters = result.scalars().all()

            updated_count = 0
            for heater in heaters:
                properties = heater.properties or {}

                # Skip already updated heaters
                if properties.get("heater_type") is not None:
                    continue

                # Determine if it should be commercial or residential based on name or capacity
                is_commercial = False
                capacity = properties.get("capacity")

                # First check capacity - large capacity heaters are commercial
                if (
                    capacity is not None and float(capacity) >= 150
                ):  # Commercial if 150L or larger
                    is_commercial = True
                else:
                    # Then check name for commercial indicators
                    name = heater.name.lower()
                    commercial_indicators = [
                        "office",
                        "lab",
                        "building",
                        "boiler",
                        "manufacturing",
                    ]

                    # Check each indicator to see if it appears in the name
                    for indicator in commercial_indicators:
                        if indicator in name:
                            is_commercial = True
                            logger.info(
                                f"Classified as commercial based on indicator '{indicator}' in name: {heater.name}"
                            )
                            break

                    # Default to residential if no indicators are found
                    if not is_commercial:
                        # Add some randomness to get a mix
                        is_commercial = (
                            random.random() < 0.3
                        )  # 30% chance of being commercial

                heater_type = (
                    WaterHeaterType.COMMERCIAL
                    if is_commercial
                    else WaterHeaterType.RESIDENTIAL
                )

                # Update properties with new fields
                properties["heater_type"] = heater_type
                properties["specification_link"] = (
                    "/docs/specifications/water_heaters/commercial.md"
                    if is_commercial
                    else "/docs/specifications/water_heaters/residential.md"
                )

                # Update the properties in the database
                heater.properties = properties
                updated_count += 1

                logger.info(
                    f"Updated water heater {heater.id} ({heater.name}) with type {heater_type}"
                )

            await session.commit()
            logger.info(f"Updated {updated_count} remaining water heaters successfully")

        except Exception as e:
            logger.error(f"Error updating remaining water heaters: {e}")
            await session.rollback()
            raise


async def main():
    """Main entry point for the script."""
    logger.info("Starting remaining water heater update script")
    await update_remaining_water_heaters()
    logger.info("Remaining water heater update script completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
