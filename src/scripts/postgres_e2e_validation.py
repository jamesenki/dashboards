#!/usr/bin/env python3
"""
End-to-End PostgreSQL Validation

This script validates that the entire IoTSphere application correctly uses PostgreSQL
and fails if it falls back to mock data at any point.
"""
import argparse
import asyncio
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from src.models.water_heater import WaterHeaterType

# Import application modules
from src.repositories.postgres_water_heater_repository import (
    PostgresWaterHeaterRepository,
)
from src.repositories.water_heater_repository import MockWaterHeaterRepository

# Import PostgreSQL connection checker
from src.scripts.check_postgres_connection import check_postgres_connection
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)

# Import environment loader for credentials
from src.utils.env_loader import get_db_credentials

# Configuration
DEFAULT_PORT = 8006
DEFAULT_BASE_URL = f"http://localhost:{DEFAULT_PORT}"
REQUIRED_MANUFACTURERS = ["Rheem"]

# We need to handle both string representations and enum values
REQUIRED_HEATER_TYPES = ["Tank", "Tankless", "Hybrid"]
REQUIRED_HEATER_TYPE_PATTERNS = [
    "Tank",
    "TANK",
    "WaterHeaterType.TANK",
    "Tankless",
    "TANKLESS",
    "WaterHeaterType.TANKLESS",
    "Hybrid",
    "HYBRID",
    "WaterHeaterType.HYBRID",
]
# Get database connection parameters from environment variables
DB_CONFIG = get_db_credentials()


class PostgresOnlyWaterHeaterService(ConfigurableWaterHeaterService):
    """
    Modified service that raises an exception if it falls back to mock data.
    This ensures we fail validation tests when mock data is used.
    """

    def __init__(self, repository=None):
        """Initialize with strict PostgreSQL requirements."""
        # Call parent initializer
        super().__init__(repository)

        # Verify repository type
        if isinstance(self.repository, MockWaterHeaterRepository):
            raise RuntimeError(
                "VALIDATION FAILURE: Service is using MockWaterHeaterRepository instead of PostgresWaterHeaterRepository.\n"
                f"Reason: {ConfigurableWaterHeaterService.data_source_reason}"
            )

    async def get_water_heaters(self, manufacturer=None):
        """Override to fail if mock data is used."""
        result, is_from_db = await super().get_water_heaters(manufacturer)

        if not is_from_db:
            raise RuntimeError(
                "VALIDATION FAILURE: get_water_heaters returned mock data instead of database data.\n"
                f"Reason: {ConfigurableWaterHeaterService.data_source_reason}"
            )

        return result, is_from_db

    async def get_water_heater(self, device_id):
        """Override to fail if mock data is used."""
        result, is_from_db = await super().get_water_heater(device_id)

        if not is_from_db:
            raise RuntimeError(
                "VALIDATION FAILURE: get_water_heater returned mock data instead of database data.\n"
                f"Reason: {ConfigurableWaterHeaterService.data_source_reason}"
            )

        return result, is_from_db


async def validate_postgres_direct():
    """
    Validate PostgreSQL connectivity and data retrieval directly.
    """
    try:
        logger.info("Validating PostgreSQL connection...")

        # First check PostgreSQL connection with retries
        connection_check = await check_postgres_connection(DB_CONFIG, max_retries=3)
        if not connection_check:
            logger.error("❌ PostgreSQL connection check failed")
            return False

        logger.info("Validating PostgresWaterHeaterRepository...")

        # Create and initialize the PostgreSQL repository
        repo = PostgresWaterHeaterRepository(**DB_CONFIG)
        await repo._initialize()

        # Get water heaters
        water_heaters = await repo.get_water_heaters()

        if not water_heaters:
            logger.error("❌ No water heaters returned from PostgreSQL repository")
            return False

        logger.info(
            f"✅ PostgreSQL repository returned {len(water_heaters)} water heaters"
        )

        # Check for Rheem heaters
        rheem_heaters = [wh for wh in water_heaters if wh.manufacturer == "Rheem"]

        if not rheem_heaters:
            logger.error("❌ No Rheem water heaters found in PostgreSQL repository")
            return False

        logger.info(f"✅ Found {len(rheem_heaters)} Rheem water heaters")

        # Check water heater types
        type_counts = {}
        for wh in rheem_heaters:
            wh_type = str(wh.heater_type)
            type_counts[wh_type] = type_counts.get(wh_type, 0) + 1

        logger.info(f"✅ Rheem water heater types: {type_counts}")

        # Verify all required types exist by checking for matching patterns
        found_types = {"Tank": False, "Tankless": False, "Hybrid": False}

        for type_key in type_counts.keys():
            if "TANK" in type_key.upper() and "TANKLESS" not in type_key.upper():
                found_types["Tank"] = True
            elif "TANKLESS" in type_key.upper():
                found_types["Tankless"] = True
            elif "HYBRID" in type_key.upper():
                found_types["Hybrid"] = True

        # Check if all required types were found
        missing_types = [t for t in REQUIRED_HEATER_TYPES if not found_types[t]]
        if missing_types:
            logger.error(
                f"❌ Required types missing for Rheem water heaters: {missing_types}"
            )
            return False

        logger.info(f"✅ All required types found for Rheem water heaters")

        logger.info("✅ All required Rheem water heater types present")

        return True
    except Exception as e:
        logger.error(f"❌ Error in direct PostgreSQL validation: {str(e)}")
        return False


async def validate_strict_service():
    """
    Validate that the service layer correctly uses PostgreSQL without falling back to mock.
    """
    try:
        logger.info("Validating service layer with strict PostgreSQL requirements...")

        # Create direct PostgreSQL repository
        repo = PostgresWaterHeaterRepository(**DB_CONFIG)
        await repo._initialize()

        # Create patched service that fails on mock data
        service = PostgresOnlyWaterHeaterService(repository=repo)

        # Get all water heaters
        water_heaters, is_from_db = await service.get_water_heaters()

        logger.info(
            f"✅ Service returned {len(water_heaters)} water heaters from database"
        )

        # Check for Rheem heaters
        for manufacturer in REQUIRED_MANUFACTURERS:
            # Get water heaters filtered by manufacturer
            mfr_heaters, is_from_db = await service.get_water_heaters(
                manufacturer=manufacturer
            )

            if not mfr_heaters:
                logger.error(f"❌ No {manufacturer} water heaters returned by service")
                return False

            logger.info(
                f"✅ Service returned {len(mfr_heaters)} {manufacturer} water heaters"
            )

            # Check water heater types
            type_counts = {}
            for wh in mfr_heaters:
                wh_type = str(wh.heater_type)
                type_counts[wh_type] = type_counts.get(wh_type, 0) + 1

            logger.info(f"✅ {manufacturer} water heater types: {type_counts}")

            # Verify all required types exist by checking for matching patterns
            found_types = {"Tank": False, "Tankless": False, "Hybrid": False}

            for type_key in type_counts.keys():
                if "TANK" in type_key.upper() and "TANKLESS" not in type_key.upper():
                    found_types["Tank"] = True
                elif "TANKLESS" in type_key.upper():
                    found_types["Tankless"] = True
                elif "HYBRID" in type_key.upper():
                    found_types["Hybrid"] = True

            # Check if all required types were found
            missing_types = [t for t in REQUIRED_HEATER_TYPES if not found_types[t]]
            if missing_types:
                logger.error(
                    f"❌ Required types missing for {manufacturer} water heaters: {missing_types}"
                )
                return False

            logger.info(f"✅ All required types found for {manufacturer} water heaters")

            logger.info(f"✅ All required {manufacturer} water heater types present")

        return True
    except Exception as e:
        logger.error(f"❌ Error in service layer validation: {str(e)}")
        return False


async def validate_api_layer(base_url=DEFAULT_BASE_URL):
    """
    Validate that the API returns data from PostgreSQL.
    """
    try:
        logger.info("Validating API layer...")

        # Check health endpoint
        health_url = urljoin(base_url, "/api/health/data-source")
        logger.info(f"Checking data source health endpoint: {health_url}")

        response = requests.get(health_url)
        if response.status_code != 200:
            logger.error(
                f"❌ Health endpoint returned status code {response.status_code}"
            )
            return False

        health_data = response.json()
        logger.info(f"Health endpoint response: {json.dumps(health_data, indent=2)}")

        if health_data.get("is_using_mock_data", True):
            logger.error("❌ API is using mock data according to health endpoint")
            return False

        logger.info(f"✅ API is using database data according to health endpoint")

        # Check API endpoints for each required manufacturer
        for manufacturer in REQUIRED_MANUFACTURERS:
            api_url = urljoin(
                base_url, f"/api/manufacturer/water-heaters?manufacturer={manufacturer}"
            )
            logger.info(f"Checking API endpoint: {api_url}")

            response = requests.get(api_url)
            if response.status_code != 200:
                logger.error(
                    f"❌ API endpoint returned status code {response.status_code}"
                )
                return False

            water_heaters = response.json()

            if not water_heaters:
                logger.error(f"❌ No {manufacturer} water heaters returned from API")
                return False

            logger.info(
                f"✅ API returned {len(water_heaters)} {manufacturer} water heaters"
            )

            # Check water heater types
            type_counts = {}
            for wh in water_heaters:
                wh_type = wh.get("heater_type")
                if wh_type:
                    type_counts[wh_type] = type_counts.get(wh_type, 0) + 1

            logger.info(f"✅ {manufacturer} water heater types from API: {type_counts}")

            # Verify all required types exist by checking for matching patterns
            found_types = {"Tank": False, "Tankless": False, "Hybrid": False}

            for type_key in type_counts.keys():
                if "TANK" in type_key.upper() and "TANKLESS" not in type_key.upper():
                    found_types["Tank"] = True
                elif "TANKLESS" in type_key.upper():
                    found_types["Tankless"] = True
                elif "HYBRID" in type_key.upper():
                    found_types["Hybrid"] = True

            # Check if all required types were found
            missing_types = [t for t in REQUIRED_HEATER_TYPES if not found_types[t]]
            if missing_types:
                logger.error(
                    f"❌ Required types missing in API response for {manufacturer}: {missing_types}"
                )
                return False

            logger.info(
                f"✅ All required {manufacturer} water heater types present in API response"
            )

        return True
    except Exception as e:
        logger.error(f"❌ Error in API layer validation: {str(e)}")
        return False


def setup_environment():
    """
    Set up required environment variables to force PostgreSQL usage.
    """
    # Set environment variables to force PostgreSQL and disable fallback
    os.environ["IOTSPHERE_ENV"] = "development"
    os.environ["DB_TYPE"] = "postgres"
    os.environ["DB_HOST"] = DB_CONFIG["host"]
    os.environ["DB_PORT"] = str(DB_CONFIG["port"])
    os.environ["DB_NAME"] = DB_CONFIG["database"]
    os.environ["DB_USER"] = DB_CONFIG["user"]
    os.environ["DB_PASSWORD"] = DB_CONFIG["password"]
    os.environ["FALLBACK_TO_MOCK"] = "false"
    os.environ["DATABASE_FALLBACK_ENABLED"] = "false"
    os.environ["USE_MOCK_DATA"] = "false"

    logger.info("Environment variables set:")
    logger.info(f"  IOTSPHERE_ENV: {os.environ.get('IOTSPHERE_ENV')}")
    logger.info(f"  DB_TYPE: {os.environ.get('DB_TYPE')}")
    logger.info(f"  DB_HOST: {os.environ.get('DB_HOST')}")
    logger.info(f"  FALLBACK_TO_MOCK: {os.environ.get('FALLBACK_TO_MOCK')}")
    logger.info(
        f"  DATABASE_FALLBACK_ENABLED: {os.environ.get('DATABASE_FALLBACK_ENABLED')}"
    )
    logger.info(f"  USE_MOCK_DATA: {os.environ.get('USE_MOCK_DATA')}")


def patch_module_for_validation():
    """
    Patch the ConfigurableWaterHeaterService to fail on mock data.
    """
    # Monkey patch the original service class to use our validation class
    import src.services.configurable_water_heater_service as service_module

    service_module.ConfigurableWaterHeaterService = PostgresOnlyWaterHeaterService
    logger.info("✅ Patched ConfigurableWaterHeaterService to fail on mock data")


async def run_server_for_testing(port=DEFAULT_PORT):
    """
    Run the IoTSphere server for API testing.
    """
    # IMPORTANT: This needs to be called after environment setup and patching
    import asyncio

    import uvicorn

    from src.main import app

    logger.info(f"Starting server for testing on port {port}...")

    config = uvicorn.Config(app, host="127.0.0.1", port=port)
    server = uvicorn.Server(config)

    # Start server in a separate task
    task = asyncio.create_task(server.serve())

    # Wait for server to start
    for _ in range(5):
        try:
            response = requests.get(f"http://localhost:{port}/")
            if response.status_code == 200:
                logger.info(f"✅ Server started on port {port}")
                break
        except requests.RequestException:
            await asyncio.sleep(1)

    return task


async def main():
    """Run the validation script."""
    parser = argparse.ArgumentParser(description="Validate PostgreSQL data flow")
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port for server (default: {DEFAULT_PORT})",
    )
    args = parser.parse_args()

    logger.info("Starting PostgreSQL E2E validation")

    # Set up environment variables
    setup_environment()

    # Validate PostgreSQL connection directly
    postgres_valid = await validate_postgres_direct()
    if not postgres_valid:
        logger.error("❌ Direct PostgreSQL validation failed")
        return 1

    # Validate service layer with strict PostgreSQL requirements
    service_valid = await validate_strict_service()
    if not service_valid:
        logger.error("❌ Service layer validation failed")
        return 1

    # Patch module for API validation
    patch_module_for_validation()

    # Run server for API testing
    server_task = await run_server_for_testing(args.port)

    try:
        # Wait a moment for server to fully initialize
        await asyncio.sleep(2)

        # Validate API layer
        api_valid = await validate_api_layer(DEFAULT_BASE_URL)
        if not api_valid:
            logger.error("❌ API layer validation failed")
            return 1

        logger.info("\n========================================")
        logger.info("✅ ALL VALIDATION TESTS PASSED")
        logger.info("✅ PostgreSQL data flow is working correctly")
        logger.info("✅ No fallback to mock data detected")
        logger.info("========================================\n")

        return 0
    finally:
        # Cancel server task
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    # Set up proper asyncio policy for macOS
    if sys.platform == "darwin":
        import asyncio

        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
