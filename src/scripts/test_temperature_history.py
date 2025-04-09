"""
Test script to verify that temperature history can be retrieved for a specific water heater.

This script tests the get_temperature_history function for a given water heater ID
to ensure that the shadow document exists and contains temperature history data.
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Add parent directory to path to allow imports to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.services.device_shadow import DeviceShadowService
from src.services.water_heater_history import WaterHeaterHistoryService

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_temperature_history(heater_id):
    """
    Test retrieval of temperature history for a specific water heater.

    Args:
        heater_id: ID of the water heater to test
    """
    logger.info(f"Testing temperature history retrieval for water heater {heater_id}")

    # Initialize services
    history_service = WaterHeaterHistoryService()
    shadow_service = DeviceShadowService()

    # Check if shadow exists
    try:
        shadow = await shadow_service.get_device_shadow(heater_id)
        logger.info(f"Shadow document exists for {heater_id}")
        logger.info(f"Current shadow data: {json.dumps(shadow, indent=2)}")
    except ValueError as e:
        logger.error(f"Shadow document error: {e}")
        return

    # Try to get shadow history
    try:
        history = await shadow_service.get_shadow_history(heater_id)
        history_count = len(history)
        logger.info(f"Found {history_count} shadow history entries for {heater_id}")
        if history_count > 0:
            logger.info(f"First history entry: {json.dumps(history[0], indent=2)}")
            logger.info(f"Last history entry: {json.dumps(history[-1], indent=2)}")
    except Exception as e:
        logger.error(f"Error retrieving shadow history: {e}")

    # Try to get temperature history
    try:
        temp_history = await history_service.get_temperature_history(heater_id)
        logger.info(f"Successfully retrieved temperature history for {heater_id}")
        logger.info(f"Temperature history data points: {len(temp_history['labels'])}")
        logger.info(
            f"Temperature history source: {temp_history.get('source', 'unknown')}"
        )
    except Exception as e:
        logger.error(f"Error retrieving temperature history: {e}")


if __name__ == "__main__":
    # Get heater ID from command line or use default
    heater_id = sys.argv[1] if len(sys.argv) > 1 else "wh-e0ae2f58"

    # Run the async function
    asyncio.run(test_temperature_history(heater_id))
