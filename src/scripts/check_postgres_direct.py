#!/usr/bin/env python3
"""
Verify PostgreSQL data flow by directly using the ConfigurableWaterHeaterService
with forced PostgreSQL settings.
"""
import asyncio
import logging
import os
import sys
from typing import Any, Dict, List

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Set environment variables to force PostgreSQL
os.environ["USE_MOCK_DATA"] = "false"

# Import environment loader after path setup
from src.utils.env_loader import get_db_credentials

os.environ["FALLBACK_TO_MOCK"] = "false"
os.environ["IOTSPHERE_ENV"] = "development"

from src.models.water_heater import WaterHeaterType
from src.repositories.postgres_water_heater_repository import (
    PostgresWaterHeaterRepository,
)
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Disable other modules' logging
logging.getLogger("src.repositories.mock_water_heater_repository").setLevel(
    logging.ERROR
)


async def force_postgres_service():
    """Force the service to use PostgreSQL and check water heater types."""
    # Disable the fallback to mock data
    ConfigurableWaterHeaterService.is_using_mock_data = False
    ConfigurableWaterHeaterService.data_source_reason = (
        "Forced PostgreSQL for verification"
    )

    # Create a service with explicit PostgreSQL repository using environment variables
    db_credentials = get_db_credentials()
    postgres_repo = PostgresWaterHeaterRepository(
        host=db_credentials["host"],
        port=db_credentials["port"],
        database=db_credentials["database"],
        user=db_credentials["user"],
        password=db_credentials["password"],
    )

    # Initialize the repository
    await postgres_repo._initialize()

    # Create service with the initialized repository
    service = ConfigurableWaterHeaterService(repository=postgres_repo)

    # Verify the repository type
    repo_type = type(service.repository).__name__
    logger.info(f"Using repository: {repo_type}")

    if repo_type != "PostgresWaterHeaterRepository":
        logger.error(f"❌ Expected PostgresWaterHeaterRepository, got {repo_type}")
        return False

    # Get water heaters with the service
    logger.info("Getting water heaters from service...")
    water_heaters, from_db = await service.get_water_heaters()

    logger.info(f"Retrieved {len(water_heaters)} water heaters, from_db={from_db}")

    # Get Rheem water heaters
    rheem_water_heaters = [wh for wh in water_heaters if wh.manufacturer == "Rheem"]
    logger.info(f"Found {len(rheem_water_heaters)} Rheem water heaters")

    if not rheem_water_heaters:
        logger.error("❌ No Rheem water heaters found!")
        return False

    # Check water heater types
    type_counts = {}
    for wh in rheem_water_heaters:
        wh_type = str(wh.heater_type)
        type_counts[wh_type] = type_counts.get(wh_type, 0) + 1

    logger.info(f"Rheem water heater types: {type_counts}")

    # Check for required types
    required_types = ["Tank", "Tankless", "Hybrid"]
    missing_types = [t for t in required_types if t not in type_counts]

    if missing_types:
        logger.error(f"❌ Missing required Rheem water heater types: {missing_types}")
        return False

    # Print sample water heater details
    logger.info("\nSample Rheem water heaters:")
    for i, wh in enumerate(rheem_water_heaters[:3]):
        logger.info(f"Sample {i+1}:")
        logger.info(f"  ID: {wh.id}")
        logger.info(f"  Device ID: {wh.device_id}")
        logger.info(f"  Name: {wh.name}")
        logger.info(f"  Manufacturer: {wh.manufacturer}")
        logger.info(f"  Type: {wh.heater_type}")
        logger.info(f"  Model: {wh.model}")
        logger.info(f"  Series: {wh.series}")

    logger.info("\n✅ Successfully verified Rheem water heater types from PostgreSQL!")
    return True


async def main():
    """Run the verification script."""
    logger.info("Starting PostgreSQL direct verification...")

    success = await force_postgres_service()

    if success:
        logger.info("\n✅ SUCCESS: PostgreSQL data flow verified")
    else:
        logger.error("\n❌ FAILURE: Issues with PostgreSQL data flow")

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
