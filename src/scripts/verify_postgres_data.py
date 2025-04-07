#!/usr/bin/env python
"""
Script to verify and adjust PostgreSQL data according to requirements:
- At least 2 entries per water heater
- Less than 21 entries total
"""
import asyncio
import logging
import os
import random
import sys
from datetime import datetime, timedelta

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
    from src.models.water_heater import WaterHeaterReading
    from src.repositories.postgres_water_heater_repository import (
        PostgresWaterHeaterRepository,
    )
except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    sys.exit(1)


async def verify_and_adjust_data():
    """Verify and adjust PostgreSQL data to meet requirements."""
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

        # Check total readings for each water heater
        total_readings = 0
        water_heater_readings = {}

        for heater in water_heaters:
            readings = await postgres_repo.get_readings(heater.id)
            reading_count = len(readings)
            water_heater_readings[heater.id] = reading_count
            total_readings += reading_count
            logger.info(
                f"Water heater {heater.id} ({heater.name}): {reading_count} readings"
            )

        logger.info(f"Total readings across all water heaters: {total_readings}")

        # Check if requirements are met
        requirements_met = True

        # Check requirement 1: At least 2 readings per water heater
        heaters_with_insufficient_readings = [
            heater_id for heater_id, count in water_heater_readings.items() if count < 2
        ]

        if heaters_with_insufficient_readings:
            logger.warning(
                f"{len(heaters_with_insufficient_readings)} water heaters have less than 2 readings"
            )
            requirements_met = False

            # Add readings for water heaters with insufficient data
            for heater_id in heaters_with_insufficient_readings:
                # Number of readings to add (to reach at least 2)
                readings_to_add = 2 - water_heater_readings[heater_id]

                for _ in range(readings_to_add):
                    # Create a reading with random but realistic values
                    reading = WaterHeaterReading(
                        temperature=round(random.uniform(40.0, 60.0), 1),
                        pressure=round(random.uniform(40.0, 60.0), 1),
                        energy_usage=round(random.uniform(1.0, 5.0), 2),
                        flow_rate=round(random.uniform(2.0, 8.0), 1),
                        timestamp=datetime.now()
                        - timedelta(minutes=random.randint(5, 60)),
                    )

                    # Add the reading
                    logger.info(f"Adding new reading for water heater {heater_id}")
                    await postgres_repo.add_reading(heater_id, reading)

                    # Update count
                    water_heater_readings[heater_id] += 1
                    total_readings += 1

        # Check requirement 2: Less than 21 total readings
        if total_readings > 20:
            logger.warning(f"Total readings ({total_readings}) exceeds maximum (20)")
            requirements_met = False

            # Calculate how many readings to remove
            readings_to_remove = total_readings - 20
            logger.info(f"Need to remove {readings_to_remove} readings")

            # Sort water heaters by number of readings (descending)
            sorted_heaters = sorted(
                water_heater_readings.items(), key=lambda x: x[1], reverse=True
            )

            # Remove readings from water heaters with the most readings
            readings_removed = 0
            for heater_id, count in sorted_heaters:
                # Skip if this water heater only has 2 readings
                if count <= 2:
                    continue

                # Determine how many readings to remove from this water heater
                can_remove = count - 2  # Keep at least 2 readings
                will_remove = min(can_remove, readings_to_remove - readings_removed)

                if will_remove > 0:
                    logger.info(
                        f"Removing {will_remove} readings from water heater {heater_id}"
                    )

                    # Get readings for this water heater
                    readings = await postgres_repo.get_readings(heater_id)

                    # Sort by timestamp (oldest first)
                    readings.sort(key=lambda x: x.timestamp)

                    # Remove oldest readings
                    for i in range(will_remove):
                        if i < len(readings):
                            reading_id = readings[i].id
                            await postgres_repo.remove_reading(heater_id, reading_id)
                            logger.info(f"Removed reading {reading_id}")

                    # Update counts
                    water_heater_readings[heater_id] -= will_remove
                    readings_removed += will_remove

                    # Check if we've removed enough
                    if readings_removed >= readings_to_remove:
                        break

        # Verify again after adjustments
        if not requirements_met:
            logger.info("Verifying data after adjustments...")

            # Get updated counts
            total_readings = 0
            for heater in water_heaters:
                readings = await postgres_repo.get_readings(heater.id)
                reading_count = len(readings)
                logger.info(
                    f"Water heater {heater.id} now has {reading_count} readings"
                )
                total_readings += reading_count

            logger.info(f"Total readings after adjustments: {total_readings}")

            # Final verification
            if total_readings <= 20:
                logger.info("✅ Requirement met: Less than 21 total readings")
            else:
                logger.error(
                    "❌ Requirement not met: Still have more than 20 total readings"
                )

            min_readings = min(
                len(await postgres_repo.get_readings(heater.id))
                for heater in water_heaters
            )
            if min_readings >= 2:
                logger.info(
                    "✅ Requirement met: All water heaters have at least 2 readings"
                )
            else:
                logger.error(
                    "❌ Requirement not met: Some water heaters still have less than 2 readings"
                )
        else:
            logger.info("✅ All requirements already met, no adjustments needed")

    except Exception as e:
        logger.error(f"Error verifying and adjusting PostgreSQL data: {e}")
        import traceback

        logger.error(traceback.format_exc())
    finally:
        # Close the database connection
        if "postgres_repo" in locals() and postgres_repo.pool:
            await postgres_repo.pool.close()
            logger.info("Closed PostgreSQL connection pool")


if __name__ == "__main__":
    asyncio.run(verify_and_adjust_data())
