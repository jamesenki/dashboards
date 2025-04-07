#!/usr/bin/env python3
"""
Verify that Rheem water heater types are correctly loaded from PostgreSQL.

This script directly tests the PostgresWaterHeaterRepository to ensure it can properly
map between the database 'type' column and the model's 'heater_type' field.
"""
import asyncio
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.models.water_heater import WaterHeaterType
from src.repositories.postgres_water_heater_repository import (
    PostgresWaterHeaterRepository,
)

# Import environment loader for credentials
from src.utils.env_loader import get_db_credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get database connection parameters from environment variables
db_credentials = get_db_credentials()
DB_HOST = db_credentials["host"]
DB_PORT = db_credentials["port"]
DB_NAME = db_credentials["database"]
DB_USER = db_credentials["user"]
DB_PASSWORD = db_credentials["password"]


async def verify_repository_mapping():
    """Verify that the PostgresWaterHeaterRepository correctly maps between DB and model fields."""
    logger.info("Creating PostgreSQL repository...")
    repo = PostgresWaterHeaterRepository(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )

    # Initialize repository (using private method since that's the implementation)
    await repo._initialize()

    # Get all water heaters
    logger.info("Getting all water heaters from PostgreSQL...")
    water_heaters = await repo.get_water_heaters()

    # Debug: Print raw data about each water heater
    logger.info(f"Total water heaters retrieved: {len(water_heaters)}")
    for wh in water_heaters[:2]:  # Just show the first 2 for brevity
        logger.info(
            f"Water heater: id={wh.id}, manufacturer={wh.manufacturer}, type={wh.type}, heater_type={wh.heater_type}"
        )

    # Check if we have any water heaters
    if not water_heaters:
        logger.error("❌ No water heaters found in PostgreSQL database!")
        return False

    logger.info(f"✅ Found {len(water_heaters)} water heaters in PostgreSQL")

    # Count water heater types for Rheem
    rheem_water_heaters = [wh for wh in water_heaters if wh.manufacturer == "Rheem"]

    if not rheem_water_heaters:
        logger.error("❌ No Rheem water heaters found in PostgreSQL database!")
        return False

    logger.info(f"✅ Found {len(rheem_water_heaters)} Rheem water heaters in PostgreSQL")

    # Count by type
    type_counts = {}
    for wh in rheem_water_heaters:
        # The actual model property is 'heater_type' (not 'water_heater_type')
        wh_type = str(wh.heater_type) if wh.heater_type else "Unknown"
        type_counts[wh_type] = type_counts.get(wh_type, 0) + 1

    # Check if we have all required types
    # Add some debug output to understand the values we're getting
    logger.info(f"Found type_counts: {type_counts}")

    # Case-insensitive check for required types
    required_types = [
        WaterHeaterType.TANK.value,
        WaterHeaterType.TANKLESS.value,
        WaterHeaterType.HYBRID.value,
    ]
    type_counts_upper = {k.upper(): v for k, v in type_counts.items()}
    missing_types = [t for t in required_types if t.upper() not in type_counts_upper]

    if missing_types:
        logger.error(f"❌ Missing Rheem water heater types: {missing_types}")
        return False

    logger.info(f"✅ All Rheem water heater types found: {type_counts}")

    # Check if models have device_id correctly set
    for wh in rheem_water_heaters:
        if not wh.device_id:
            logger.error(f"❌ Water heater {wh.id} is missing device_id!")
            return False

        # The device_id should match the id in our mapping
        if wh.device_id != wh.id:
            logger.error(
                f"❌ Water heater {wh.id} has mismatched device_id: {wh.device_id}"
            )
            return False

    logger.info("✅ All water heaters have correct device_id mapping")

    # Print a sample water heater to verify all fields are correctly mapped
    sample = rheem_water_heaters[0]
    logger.info("\nSample water heater data:")
    logger.info(f"ID: {sample.id}")
    logger.info(f"Device ID: {sample.device_id}")
    logger.info(f"Name: {sample.name}")
    logger.info(f"Manufacturer: {sample.manufacturer}")
    logger.info(f"Type: {sample.heater_type}")
    logger.info(f"Model: {sample.model}")
    logger.info(f"Series: {sample.series}")

    return True


async def main():
    """Run verification of water heater type mapping."""
    logger.info("Starting verification of Rheem water heater types in PostgreSQL...")

    success = await verify_repository_mapping()

    if success:
        logger.info(
            "\n✅ SUCCESS: PostgreSQL repository correctly maps water heater types!"
        )
    else:
        logger.error("\n❌ FAILURE: Issues found with water heater type mapping!")

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
