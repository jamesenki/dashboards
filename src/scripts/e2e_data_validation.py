#!/usr/bin/env python3
"""
End-to-End Data Flow Validation

This script validates that the entire IoTSphere application correctly uses PostgreSQL
and fails if it falls back to mock data at any point.

Features:
1. Directly validates PostgreSQL connection
2. Checks repository layer data access
3. Validates API responses
4. Ensures mock data is not being used anywhere
5. Provides clear error messages if validation fails

Usage:
    python src/scripts/e2e_data_validation.py [--url http://localhost:8006]
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

# Import PostgreSQL connection checker
from src.scripts.check_postgres_connection import check_postgres_connection

# Import environment loader for credentials
from src.utils.env_loader import get_db_credentials

# Configuration
DEFAULT_PORT = 8006
DEFAULT_BASE_URL = f"http://localhost:{DEFAULT_PORT}"
REQUIRED_MANUFACTURERS = ["Rheem"]
REQUIRED_HEATER_TYPES = ["Tank", "Tankless", "Hybrid"]
# Get database configuration from environment variables
DB_CONFIG = get_db_credentials()

# Set environment variables to force PostgreSQL usage
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

# Test flags for validation
validation_results = {
    "postgres_connection": False,
    "repository_data": False,
    "api_data_source": False,
    "api_water_heaters": False,
    "all_types_present": False,
}


async def validate_postgres_connection():
    """Validate direct PostgreSQL connection."""
    try:
        logger.info("Validating PostgreSQL connection...")

        # Check PostgreSQL connection with retries
        connection_ok = await check_postgres_connection(
            DB_CONFIG, max_retries=3, retry_delay=2
        )

        validation_results["postgres_connection"] = connection_ok
        return connection_ok
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection validation failed: {str(e)}")
        return False


async def validate_repository_data():
    """Validate repository data retrieval."""
    try:
        logger.info("Validating repository data retrieval...")

        # Create and initialize PostgreSQL repository
        repo = PostgresWaterHeaterRepository(**DB_CONFIG)
        await repo._initialize()

        # Get water heaters
        water_heaters = await repo.get_water_heaters()

        if not water_heaters:
            logger.error("❌ No water heaters returned from PostgreSQL repository")
            return False

        logger.info(f"✅ Repository returned {len(water_heaters)} water heaters")

        # Check for Rheem water heaters
        rheem_heaters = [wh for wh in water_heaters if wh.manufacturer == "Rheem"]

        if not rheem_heaters:
            logger.error("❌ No Rheem water heaters found in repository data")
            return False

        logger.info(f"✅ Found {len(rheem_heaters)} Rheem water heaters")

        # Check water heater types
        type_counts = {}
        for wh in rheem_heaters:
            wh_type = str(wh.heater_type)
            type_counts[wh_type] = type_counts.get(wh_type, 0) + 1

        logger.info(f"✅ Rheem water heater types: {type_counts}")

        # Verify all required types are present
        found_types = {"Tank": False, "Tankless": False, "Hybrid": False}

        for type_key in type_counts.keys():
            if "TANK" in type_key.upper() and "TANKLESS" not in type_key.upper():
                found_types["Tank"] = True
            elif "TANKLESS" in type_key.upper():
                found_types["Tankless"] = True
            elif "HYBRID" in type_key.upper():
                found_types["Hybrid"] = True

        missing_types = [t for t in REQUIRED_HEATER_TYPES if not found_types[t]]
        if missing_types:
            logger.error(
                f"❌ Required types missing for Rheem water heaters: {missing_types}"
            )
            return False

        logger.info("✅ All required water heater types present")
        validation_results["repository_data"] = True
        validation_results["all_types_present"] = True
        return True
    except Exception as e:
        logger.error(f"❌ Repository data validation failed: {str(e)}")
        return False


def validate_api_data_source(base_url=DEFAULT_BASE_URL):
    """Validate API data source via health endpoint."""
    try:
        logger.info("Validating API data source...")

        # Check health endpoint
        health_url = urljoin(base_url, "/api/health/data-source")
        logger.info(f"Checking health endpoint: {health_url}")

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
            reason = health_data.get("reason", "No reason provided")
            logger.error(f"❌ Reason: {reason}")
            return False

        data_source = health_data.get("data_source", "Unknown")
        if data_source != "PostgreSQL":
            logger.error(f"❌ API is using {data_source} instead of PostgreSQL")
            return False

        logger.info(f"✅ API is using PostgreSQL data source")
        validation_results["api_data_source"] = True
        return True
    except Exception as e:
        logger.error(f"❌ API data source validation failed: {str(e)}")
        return False


def validate_api_water_heaters(base_url=DEFAULT_BASE_URL):
    """Validate API water heater endpoints."""
    try:
        logger.info("Validating API water heater endpoints...")

        # Check for each required manufacturer
        for manufacturer in REQUIRED_MANUFACTURERS:
            url = urljoin(
                base_url, f"/api/manufacturer/water-heaters?manufacturer={manufacturer}"
            )
            logger.info(f"Checking endpoint: {url}")

            response = requests.get(url)
            if response.status_code != 200:
                logger.error(f"❌ Endpoint returned status code {response.status_code}")
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

            # Verify all required types are present
            found_types = {"Tank": False, "Tankless": False, "Hybrid": False}

            for type_key in type_counts.keys():
                if "TANK" in type_key.upper() and "TANKLESS" not in type_key.upper():
                    found_types["Tank"] = True
                elif "TANKLESS" in type_key.upper():
                    found_types["Tankless"] = True
                elif "HYBRID" in type_key.upper():
                    found_types["Hybrid"] = True

            missing_types = [t for t in REQUIRED_HEATER_TYPES if not found_types[t]]
            if missing_types:
                logger.error(
                    f"❌ Required types missing in API response for {manufacturer}: {missing_types}"
                )
                return False

            logger.info(
                f"✅ All required types present in API response for {manufacturer}"
            )

        validation_results["api_water_heaters"] = True
        return True
    except Exception as e:
        logger.error(f"❌ API water heater validation failed: {str(e)}")
        return False


def print_validation_summary():
    """Print a summary of validation results."""
    logger.info("\n" + "=" * 50)
    logger.info("POSTGRESQL DATA FLOW VALIDATION SUMMARY")
    logger.info("=" * 50)

    all_passed = True
    for test, result in validation_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        if not result:
            all_passed = False
        logger.info(f"{test.replace('_', ' ').title()}: {status}")

    logger.info("=" * 50)
    if all_passed:
        logger.info("✅ ALL VALIDATION TESTS PASSED")
        logger.info("✅ PostgreSQL data flow is working correctly")
        logger.info("✅ No fallback to mock data detected")
    else:
        logger.error("❌ VALIDATION FAILED: Some tests did not pass")
        if not validation_results["postgres_connection"]:
            logger.error(
                "❌ PostgreSQL connection failed - check database configuration"
            )
        elif not validation_results["api_data_source"]:
            logger.error("❌ API is using mock data instead of PostgreSQL")
        elif not validation_results["all_types_present"]:
            logger.error("❌ Not all required water heater types are present")
    logger.info("=" * 50)

    return all_passed


async def run_validation(base_url=DEFAULT_BASE_URL):
    """Run all validation tests."""
    # Step 1: Validate PostgreSQL connection
    postgres_ok = await validate_postgres_connection()
    if not postgres_ok:
        logger.error("❌ PostgreSQL connection validation failed - cannot proceed")
        return False

    # Step 2: Validate repository data
    repo_ok = await validate_repository_data()
    if not repo_ok:
        logger.error("❌ Repository data validation failed - cannot proceed")
        return False

    # Step 3: Validate API data source via health endpoint
    api_source_ok = validate_api_data_source(base_url)
    if not api_source_ok:
        logger.error("❌ API data source validation failed - cannot proceed")
        return False

    # Step 4: Validate API water heater endpoints
    api_wh_ok = validate_api_water_heaters(base_url)
    if not api_wh_ok:
        logger.error("❌ API water heater validation failed")
        return False

    # Print validation summary
    return print_validation_summary()


async def main():
    """Run the validation script."""
    parser = argparse.ArgumentParser(description="Validate PostgreSQL data flow")
    parser.add_argument(
        "--url",
        default=DEFAULT_BASE_URL,
        help=f"Base URL (default: {DEFAULT_BASE_URL})",
    )
    args = parser.parse_args()

    logger.info(f"Starting PostgreSQL data flow validation for {args.url}")

    # Run validation
    success = await run_validation(args.url)

    return 0 if success else 1


if __name__ == "__main__":
    # Set proper asyncio policy for macOS
    if sys.platform == "darwin":
        import asyncio

        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
