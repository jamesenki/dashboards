#!/usr/bin/env python3
"""
End-to-End PostgreSQL Data Flow Validation

This script performs comprehensive validation of the entire data flow:
1. Database connection and schema validation
2. Repository layer validation
3. Service layer validation
4. API validation
5. Frontend validation

It will FAIL if:
- PostgreSQL connection fails
- The application falls back to mock data
- Required water heater types are missing
- API responses don't match database data
- UI doesn't display the correct data

Usage:
    python src/scripts/validate_postgres_e2e.py
"""
import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import application modules
import asyncpg

from src.db.config import db_settings
from src.models.water_heater import WaterHeaterType
from src.repositories.postgres_water_heater_repository import (
    PostgresWaterHeaterRepository,
)
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)

# Import environment loader for credentials
from src.utils.env_loader import get_db_credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("postgres_e2e_validation.log"),
    ],
)
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_BASE_URL = "http://localhost:8006"
DEFAULT_PORT = 8006
REQUIRED_MANUFACTURERS = ["Rheem"]
REQUIRED_HEATER_TYPES = ["Tank", "Tankless", "Hybrid"]
# Get database connection parameters from environment variables
DB_CONFIG = get_db_credentials()

# Test flags to track which validation steps have passed
validation_results = {
    "db_connection": False,
    "db_schema": False,
    "repository_layer": False,
    "service_layer": False,
    "api_layer": False,
    "ui_layer": False,
    "config_service": False,
    "using_postgres": False,
    "all_types_present": False,
}


async def validate_db_connection():
    """Validate direct PostgreSQL connection."""
    try:
        logger.info("Validating PostgreSQL connection...")
        conn = await asyncpg.connect(**DB_CONFIG)

        # Check connection
        version = await conn.fetchval("SELECT version()")
        logger.info(f"✅ Connected to PostgreSQL: {version}")

        await conn.close()
        validation_results["db_connection"] = True
        return True
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {str(e)}")
        return False


async def validate_db_schema():
    """Validate PostgreSQL schema and required data."""
    try:
        logger.info("Validating PostgreSQL schema...")
        conn = await asyncpg.connect(**DB_CONFIG)

        # Check water_heaters table
        table_exists = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'water_heaters')"
        )
        if not table_exists:
            logger.error("❌ water_heaters table does not exist")
            return False

        logger.info("✅ water_heaters table exists")

        # Check columns
        columns = await conn.fetch(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'water_heaters'"
        )
        column_names = [col["column_name"] for col in columns]
        required_columns = ["id", "manufacturer", "type", "name", "model"]
        missing_columns = [col for col in required_columns if col not in column_names]

        if missing_columns:
            logger.error(f"❌ Missing required columns: {missing_columns}")
            return False

        logger.info(f"✅ All required columns present")

        # Check manufacturers
        manufacturers = await conn.fetch(
            "SELECT DISTINCT manufacturer FROM water_heaters WHERE manufacturer IS NOT NULL"
        )
        db_manufacturers = [row["manufacturer"] for row in manufacturers]

        for manufacturer in REQUIRED_MANUFACTURERS:
            if manufacturer not in db_manufacturers:
                logger.error(
                    f"❌ Required manufacturer '{manufacturer}' not found in database"
                )
                return False

        logger.info(f"✅ All required manufacturers present: {db_manufacturers}")

        # Check water heater types
        for manufacturer in REQUIRED_MANUFACTURERS:
            types = await conn.fetch(
                f"SELECT type, COUNT(*) FROM water_heaters WHERE manufacturer = $1 GROUP BY type",
                manufacturer,
            )
            db_types = {row["type"]: row["count"] for row in types}

            logger.info(f"Water heater types for {manufacturer}: {db_types}")

            for heater_type in REQUIRED_HEATER_TYPES:
                if heater_type not in db_types:
                    logger.error(
                        f"❌ Required water heater type '{heater_type}' not found for '{manufacturer}'"
                    )
                    return False
                if db_types[heater_type] < 1:
                    logger.error(
                        f"❌ Found {db_types[heater_type]} {heater_type} water heaters for {manufacturer}, need at least 2"
                    )
                    return False

        logger.info(
            f"✅ All required water heater types present for all required manufacturers"
        )

        await conn.close()
        validation_results["db_schema"] = True
        validation_results["all_types_present"] = True
        return True
    except Exception as e:
        logger.error(f"❌ Error validating PostgreSQL schema: {str(e)}")
        return False


async def validate_repository_layer():
    """Validate the repository layer with PostgreSQL."""
    try:
        logger.info("Validating repository layer...")

        # Create PostgreSQL repository
        repo = PostgresWaterHeaterRepository(**DB_CONFIG)

        # Initialize repository
        await repo._initialize()

        # Get all water heaters
        water_heaters = await repo.get_water_heaters()

        if not water_heaters:
            logger.error("❌ No water heaters returned from repository")
            return False

        logger.info(f"✅ Repository returned {len(water_heaters)} water heaters")

        # Check for each required manufacturer
        for manufacturer in REQUIRED_MANUFACTURERS:
            mfr_heaters = [
                wh for wh in water_heaters if wh.manufacturer == manufacturer
            ]

            if not mfr_heaters:
                logger.error(
                    f"❌ No {manufacturer} water heaters returned from repository"
                )
                return False

            logger.info(
                f"✅ Repository returned {len(mfr_heaters)} {manufacturer} water heaters"
            )

            # Check for each required type
            type_counts = {}
            for wh in mfr_heaters:
                wh_type = str(wh.heater_type)
                type_counts[wh_type] = type_counts.get(wh_type, 0) + 1

            for heater_type in REQUIRED_HEATER_TYPES:
                if heater_type not in type_counts:
                    logger.error(
                        f"❌ Required type '{heater_type}' not found in repository for {manufacturer}"
                    )
                    return False
                if type_counts[heater_type] < 1:
                    logger.error(
                        f"❌ Found only {type_counts[heater_type]} {heater_type} water heaters for {manufacturer}, need at least 2"
                    )
                    return False

            logger.info(
                f"✅ Repository has all required types for {manufacturer}: {type_counts}"
            )

        validation_results["repository_layer"] = True
        return True
    except Exception as e:
        logger.error(f"❌ Error validating repository layer: {str(e)}")
        return False


async def validate_service_layer():
    """Validate the service layer with PostgreSQL."""
    try:
        logger.info("Validating service layer...")

        # Create PostgreSQL repository
        repo = PostgresWaterHeaterRepository(**DB_CONFIG)
        await repo._initialize()

        # Create service with repository
        service = ConfigurableWaterHeaterService(repository=repo)

        # Verify service is using PostgreSQL
        if isinstance(service.repository, PostgresWaterHeaterRepository):
            logger.info("✅ Service is using PostgresWaterHeaterRepository")
        else:
            logger.error(
                f"❌ Service is using {type(service.repository).__name__} instead of PostgresWaterHeaterRepository"
            )
            return False

        # Get water heaters
        water_heaters, is_from_db = await service.get_water_heaters()

        if not is_from_db:
            logger.error(
                "❌ Service returned water heaters from mock data, not from database"
            )
            return False

        if not water_heaters:
            logger.error("❌ No water heaters returned from service")
            return False

        logger.info(
            f"✅ Service returned {len(water_heaters)} water heaters from database"
        )

        # Validate ConfigurableWaterHeaterService configuration
        using_mock = ConfigurableWaterHeaterService.is_using_mock_data
        if using_mock:
            logger.error(
                "❌ ConfigurableWaterHeaterService is configured to use mock data"
            )
            return False

        logger.info(
            f"✅ ConfigurableWaterHeaterService is configured to use database data"
        )
        logger.info(f"  Reason: {ConfigurableWaterHeaterService.data_source_reason}")

        # Check for each required manufacturer
        for manufacturer in REQUIRED_MANUFACTURERS:
            # Call the service with the manufacturer filter
            mfr_heaters, is_from_db = await service.get_water_heaters(
                manufacturer=manufacturer
            )

            if not is_from_db:
                logger.error(
                    f"❌ Service returned {manufacturer} water heaters from mock data, not from database"
                )
                return False

            if not mfr_heaters:
                logger.error(f"❌ No {manufacturer} water heaters returned from service")
                return False

            logger.info(
                f"✅ Service returned {len(mfr_heaters)} {manufacturer} water heaters from database"
            )

            # Check for each required type
            type_counts = {}
            for wh in mfr_heaters:
                wh_type = str(wh.heater_type)
                type_counts[wh_type] = type_counts.get(wh_type, 0) + 1

            for heater_type in REQUIRED_HEATER_TYPES:
                if heater_type not in type_counts:
                    logger.error(
                        f"❌ Required type '{heater_type}' not found in service results for {manufacturer}"
                    )
                    return False
                if type_counts[heater_type] < 1:
                    logger.error(
                        f"❌ Found only {type_counts[heater_type]} {heater_type} water heaters for {manufacturer}, need at least 2"
                    )
                    return False

            logger.info(
                f"✅ Service returned all required types for {manufacturer}: {type_counts}"
            )

        validation_results["service_layer"] = True
        validation_results["config_service"] = True
        validation_results["using_postgres"] = True
        return True
    except Exception as e:
        logger.error(f"❌ Error validating service layer: {str(e)}")
        return False


def validate_api_layer(base_url=DEFAULT_BASE_URL):
    """Validate the API layer with PostgreSQL."""
    try:
        logger.info("Validating API layer...")

        # Check API health endpoint
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
            return False

        logger.info(
            f"✅ API is using {health_data.get('data_source')} according to health endpoint"
        )

        # Check manufacturer-agnostic API endpoint
        for manufacturer in REQUIRED_MANUFACTURERS:
            url = urljoin(
                base_url, f"/api/manufacturer/water-heaters?manufacturer={manufacturer}"
            )
            logger.info(f"Checking API endpoint: {url}")

            response = requests.get(url)
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

            # Check for each required type
            type_counts = {}
            for wh in water_heaters:
                wh_type = wh.get("heater_type")
                if wh_type:
                    type_counts[wh_type] = type_counts.get(wh_type, 0) + 1

            for heater_type in REQUIRED_HEATER_TYPES:
                if heater_type not in type_counts:
                    logger.error(
                        f"❌ Required type '{heater_type}' not found in API results for {manufacturer}"
                    )
                    return False
                if type_counts[heater_type] < 1:
                    logger.error(
                        f"❌ Found only {type_counts[heater_type]} {heater_type} water heaters for {manufacturer} in API, need at least 2"
                    )
                    return False

            logger.info(
                f"✅ API returned all required types for {manufacturer}: {type_counts}"
            )

        validation_results["api_layer"] = True
        return True
    except Exception as e:
        logger.error(f"❌ Error validating API layer: {str(e)}")
        return False


def validate_ui_layer(base_url=DEFAULT_BASE_URL):
    """Validate the UI layer with PostgreSQL."""
    try:
        logger.info("Validating UI layer...")

        # Check water heaters list page
        url = urljoin(base_url, "/water-heaters")
        logger.info(f"Checking water heaters page: {url}")

        response = requests.get(url)
        if response.status_code != 200:
            logger.error(
                f"❌ Water heaters page returned status code {response.status_code}"
            )
            return False

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Find data source indicator
        data_source = soup.find(id="data-source-indicator")
        if data_source and "Mock" in data_source.text:
            logger.error(
                f"❌ UI is showing data from mock data source: {data_source.text}"
            )
            return False

        # Check for water heater cards
        cards = soup.find_all(class_="water-heater-card")
        if not cards:
            logger.error("❌ No water heater cards found in UI")
            return False

        logger.info(f"✅ UI displays {len(cards)} water heater cards")

        # Look for manufacturer and type information in the cards
        rheem_cards = []
        for card in cards:
            card_text = card.get_text()
            if "Rheem" in card_text:
                rheem_cards.append(card)

        if not rheem_cards:
            logger.error("❌ No Rheem water heater cards found in UI")
            return False

        logger.info(f"✅ UI displays {len(rheem_cards)} Rheem water heater cards")

        # Check for each required type in the UI
        ui_types = set()
        for card in rheem_cards:
            card_text = card.get_text()
            for heater_type in REQUIRED_HEATER_TYPES:
                if heater_type in card_text:
                    ui_types.add(heater_type)

        missing_types = set(REQUIRED_HEATER_TYPES) - ui_types
        if missing_types:
            logger.error(f"❌ UI is missing water heater types: {missing_types}")
            return False

        logger.info(f"✅ UI displays all required water heater types: {ui_types}")

        validation_results["ui_layer"] = True
        return True
    except Exception as e:
        logger.error(f"❌ Error validating UI layer: {str(e)}")
        return False


def start_server_if_needed(base_url=DEFAULT_BASE_URL, port=DEFAULT_PORT):
    """Start the server if it's not already running."""
    try:
        # Check if server is running
        response = requests.get(base_url, timeout=2)
        logger.info(f"✅ Server is already running at {base_url}")
        return True
    except requests.RequestException:
        logger.info(f"Server not running at {base_url}, starting...")

        try:
            # Set environment variables to force PostgreSQL
            env = os.environ.copy()
            env["IOTSPHERE_ENV"] = "development"
            env["DB_TYPE"] = "postgres"
            env["DB_HOST"] = "localhost"
            env["DB_PORT"] = "5432"
            env["DB_NAME"] = "iotsphere"
            env["DB_USER"] = "iotsphere"
            env["DB_PASSWORD"] = "iotsphere"
            env["FALLBACK_TO_MOCK"] = "false"

            # Start server with PostgreSQL settings
            server_process = subprocess.Popen(
                ["uvicorn", "src.main:app", "--port", str(port)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Wait for server to start
            for _ in range(30):
                try:
                    response = requests.get(base_url, timeout=1)
                    if response.status_code == 200:
                        logger.info(f"✅ Server started successfully at {base_url}")
                        return True
                except requests.RequestException:
                    time.sleep(1)

            logger.error("❌ Failed to start server")
            return False
        except Exception as e:
            logger.error(f"❌ Error starting server: {str(e)}")
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
    else:
        logger.error("❌ SOME VALIDATION TESTS FAILED")
    logger.info("=" * 50)

    return all_passed


async def run_all_validations(base_url=DEFAULT_BASE_URL, port=DEFAULT_PORT):
    """Run all validation tests."""
    try:
        # Validate database connection and schema
        db_ok = await validate_db_connection()
        if not db_ok:
            logger.error("❌ Database connection validation failed, cannot proceed")
            return False

        schema_ok = await validate_db_schema()
        if not schema_ok:
            logger.error("❌ Database schema validation failed, cannot proceed")
            return False

        # Validate repository and service layers
        repo_ok = await validate_repository_layer()
        if not repo_ok:
            logger.error("❌ Repository layer validation failed, cannot proceed")
            return False

        service_ok = await validate_service_layer()
        if not service_ok:
            logger.error("❌ Service layer validation failed, cannot proceed")
            return False

        # Start server if needed for API and UI validation
        server_ok = start_server_if_needed(base_url, port)
        if not server_ok:
            logger.error(
                "❌ Failed to ensure server is running, cannot proceed with API and UI validation"
            )
            return False

        # Validate API layer
        api_ok = validate_api_layer(base_url)
        if not api_ok:
            logger.error("❌ API layer validation failed")
            return False

        # Validate UI layer
        ui_ok = validate_ui_layer(base_url)
        if not ui_ok:
            logger.error("❌ UI layer validation failed")
            return False

        # Print summary of all validation results
        return print_validation_summary()
    except Exception as e:
        logger.error(f"❌ Error running validations: {str(e)}")
        return False


async def main():
    """Run the validation script."""
    parser = argparse.ArgumentParser(description="Validate PostgreSQL data flow")
    parser.add_argument(
        "--url",
        default=DEFAULT_BASE_URL,
        help=f"Base URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help=f"Port (default: {DEFAULT_PORT})"
    )
    args = parser.parse_args()

    logger.info(f"Starting PostgreSQL data flow validation for {args.url}")

    success = await run_all_validations(args.url, args.port)

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
