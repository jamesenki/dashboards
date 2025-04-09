"""
Script to create a shadow document for a specific water heater.

This script checks if a specified water heater exists and creates a shadow document for it.
If the water heater doesn't exist, it creates a new water heater and then creates its shadow.
"""
import asyncio
import json
import logging
import os
import random
import sys
from datetime import datetime, timedelta

# Add parent directory to path to allow imports to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.models.device import DeviceStatus
from src.models.water_heater import WaterHeater, WaterHeaterMode, WaterHeaterStatus
from src.services.device_shadow import DeviceShadowService
from src.services.water_heater import WaterHeaterService

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def create_specific_shadow(heater_id):
    """
    Create a shadow document for the specified water heater.

    Args:
        heater_id: ID of the water heater to create a shadow for
    """
    logger.info(f"Creating shadow document for water heater {heater_id}")

    # Initialize services
    water_heater_service = WaterHeaterService()
    shadow_service = DeviceShadowService()

    # Check if water heater exists
    water_heater = await water_heater_service.get_water_heater(heater_id)

    if not water_heater:
        logger.warning(f"Water heater {heater_id} not found, creating a new one")

        # Create a new water heater
        current_temp = 120.0
        target_temp = 125.0
        new_heater = WaterHeater(
            id=heater_id,
            name=f"Water Heater {heater_id}",
            model="Standard Model",
            manufacturer="Generic",
            current_temperature=current_temp,
            target_temperature=target_temp,
            min_temperature=100.0,
            max_temperature=140.0,
            status=DeviceStatus.ONLINE.value,
            heater_status=WaterHeaterStatus.STANDBY.value,
            mode=WaterHeaterMode.ECO.value,
            location="Building A",
            last_seen=datetime.now(),
        )
        water_heater = await water_heater_service.create_water_heater(new_heater)
        logger.info(f"Created new water heater with ID {heater_id}")
    else:
        logger.info(f"Found existing water heater: {water_heater.id}")

    # Check if shadow already exists
    try:
        await shadow_service.get_device_shadow(heater_id)
        logger.info(f"Shadow document already exists for {heater_id}")

        # Delete existing shadow to recreate it
        await shadow_service.delete_device_shadow(heater_id)
        logger.info(f"Deleted existing shadow for {heater_id} to recreate it")
    except ValueError:
        logger.info(f"No existing shadow found for {heater_id}, will create new one")

    # Create shadow document
    reported_state = {
        "temperature": water_heater.current_temperature,
        "target_temperature": water_heater.target_temperature,
        "status": water_heater.status,
        "heater_status": getattr(
            water_heater, "heater_status", WaterHeaterStatus.STANDBY.value
        ),
        "mode": getattr(water_heater, "mode", WaterHeaterMode.ECO.value),
        "last_updated": datetime.now().isoformat() + "Z",
    }

    desired_state = {
        "target_temperature": water_heater.target_temperature,
        "mode": getattr(water_heater, "mode", WaterHeaterMode.ECO.value),
    }

    try:
        # Create shadow document
        result = await shadow_service.create_device_shadow(
            device_id=heater_id,
            reported_state=reported_state,
            desired_state=desired_state,
        )
        logger.info(f"Successfully created shadow document for {heater_id}: {result}")

        # Generate shadow history for the past week
        await generate_shadow_history(shadow_service, water_heater)

        # Verify shadow was created by retrieving it
        shadow = await shadow_service.get_device_shadow(heater_id)
        logger.info(f"Retrieved shadow document: {json.dumps(shadow, indent=2)}")

    except Exception as e:
        logger.error(f"Error creating shadow for {heater_id}: {e}")


async def generate_shadow_history(shadow_service, heater, days=7):
    """
    Generate shadow history entries for a water heater for the past week.

    Args:
        shadow_service: Instance of DeviceShadowService
        heater: Water heater instance
        days: Number of days of history to generate (default: 7)
    """
    logger.info(f"Generating shadow history for {heater.id} for the past {days} days")

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

        # Determine heater status based on temperature and target
        if temp < target_temp - 1.0:
            heater_status = WaterHeaterStatus.HEATING.value
        else:
            heater_status = WaterHeaterStatus.STANDBY.value

        # Update shadow with historical data
        reported_state = {
            "temperature": temp,
            "heater_status": heater_status,
            "status": DeviceStatus.ONLINE.value,  # Device status remains online
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
    # Get heater ID from command line or use default
    heater_id = sys.argv[1] if len(sys.argv) > 1 else "wh-e0ae2f58"

    # Run the async function
    asyncio.run(create_specific_shadow(heater_id))
