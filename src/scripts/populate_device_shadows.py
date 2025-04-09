"""
Script to populate device shadow documents for water heaters.

This script ensures that all water heaters in the asset registry have corresponding
device shadow documents, creating them if they don't exist.
"""
import asyncio
import logging
import os
import random
import sys
from datetime import datetime, timedelta

# Add parent directory to path to allow imports to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.models.water_heater import WaterHeaterMode, WaterHeaterStatus
from src.services.device_shadow import DeviceShadowService
from src.services.water_heater import WaterHeaterService

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def populate_device_shadows():
    """
    Create device shadow documents for all water heaters that don't have them.

    Also generates history entries for the past week to ensure temperature history
    charts have data to display.
    """
    logger.info("Starting device shadow population for water heaters")

    # Initialize services
    water_heater_service = WaterHeaterService()
    shadow_service = DeviceShadowService()

    # Get all water heaters
    water_heaters = await water_heater_service.get_water_heaters()
    logger.info(f"Found {len(water_heaters)} water heaters")

    # Create shadow documents for each water heater
    for heater in water_heaters:
        try:
            # Check if shadow exists
            try:
                existing_shadow = await shadow_service.get_device_shadow(heater.id)
                logger.info(f"Shadow document already exists for {heater.id}")
                continue
            except ValueError:
                # Shadow doesn't exist, create it
                logger.info(f"Creating shadow document for {heater.id}")

                # Prepare shadow data
                reported_state = {
                    "temperature": heater.current_temperature,
                    "target_temperature": heater.target_temperature,
                    "status": heater.status,
                    "mode": getattr(heater, "mode", WaterHeaterMode.STANDARD.value),
                    "last_updated": datetime.now().isoformat() + "Z",
                }

                desired_state = {
                    "target_temperature": heater.target_temperature,
                    "mode": getattr(heater, "mode", WaterHeaterMode.STANDARD.value),
                }

                # Create shadow document
                await shadow_service.create_device_shadow(
                    device_id=heater.id,
                    reported_state=reported_state,
                    desired_state=desired_state,
                )
                logger.info(f"Created shadow document for {heater.id}")

                # Generate shadow history for the past week
                await generate_shadow_history(shadow_service, heater)

        except Exception as e:
            logger.error(f"Error creating shadow for {heater.id}: {e}")

    logger.info("Completed device shadow population for water heaters")


async def generate_shadow_history(shadow_service, heater, days=7):
    """
    Generate shadow history entries for a water heater for the past week.

    Args:
        shadow_service: Instance of DeviceShadowService
        heater: Water heater instance
        days: Number of days of history to generate (default: 7)
    """
    logger.info(f"Generating shadow history for {heater.id} for the past {days} days")

    # Current shadow
    try:
        shadow = await shadow_service.get_device_shadow(heater.id)
    except ValueError:
        logger.error(
            f"Shadow document not found for {heater.id}, cannot generate history"
        )
        return

    current_time = datetime.now()
    base_temp = heater.current_temperature
    target_temp = heater.target_temperature

    # Generate one entry every 3 hours for the past week
    hours = days * 24
    for i in range(hours, 0, -3):  # Step by 3 hours
        # Calculate timestamp (going backwards from now)
        point_time = current_time - timedelta(hours=i)

        # Add daily cycle (hotter during day, cooler at night)
        hour = point_time.hour
        time_factor = ((hour - 12) / 12) * 3  # ±3 degree variation by time of day

        # Add some randomness
        random_factor = random.uniform(-1.0, 1.0)

        # Calculate temperature
        temp = base_temp + time_factor + random_factor
        temp = round(
            max(min(temp, target_temp + 5), target_temp - 10), 1
        )  # Keep within reasonable range

        # Determine status based on temperature and target
        if temp < target_temp - 1.0:
            status = WaterHeaterStatus.HEATING.value
        else:
            status = WaterHeaterStatus.STANDBY.value

        # Update shadow with historical data
        reported_state = {
            "temperature": temp,
            "status": status,
            "timestamp": point_time.isoformat() + "Z",
        }

        # Update shadow (this will create history entries)
        try:
            await shadow_service.update_device_shadow(
                device_id=heater.id, reported_state=reported_state
            )
            logger.debug(
                f"Added history entry for {heater.id} at {point_time}: temp={temp}"
            )
        except Exception as e:
            logger.error(f"Error adding history for {heater.id} at {point_time}: {e}")

    logger.info(f"Completed generating {days} days of history for {heater.id}")


if __name__ == "__main__":
    # Run the async function
    asyncio.run(populate_device_shadows())
