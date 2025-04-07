#!/usr/bin/env python3
"""
Script to verify PostgreSQL to UI data flow.

This script checks:
1. Data is correctly stored in PostgreSQL
2. All expected Rheem water heater types are present
3. Only PostgreSQL data is used (not mock data)
"""
import asyncio
import logging
import os
import sys
from typing import Any, Dict, List, Optional

import asyncpg
import requests
from bs4 import BeautifulSoup

# Setup path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import environment loader for credentials
from src.utils.env_loader import get_db_credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get database connection parameters from environment variables
db_credentials = get_db_credentials()

# API and UI endpoints
API_BASE_URL = "http://localhost:8006"
UI_BASE_URL = "http://localhost:8006"


async def get_postgres_water_heaters() -> List[Dict[str, Any]]:
    """Get all water heaters directly from PostgreSQL."""
    try:
        # Create direct PostgreSQL connection
        conn = await asyncpg.connect(
            host=db_credentials["host"],
            port=db_credentials["port"],
            database=db_credentials["database"],
            user=db_credentials["user"],
            password=db_credentials["password"],
        )

        # Use raw SQL to get all water heaters
        rows = await conn.fetch(
            """
            SELECT id, name, manufacturer, model, type, series,
                   current_temperature, target_temperature
            FROM water_heaters
            ORDER BY manufacturer, type
        """
        )

        # Convert to list of dictionaries
        water_heaters = []
        for row in rows:
            water_heater = dict(row)
            water_heaters.append(water_heater)

        # Close connection
        await conn.close()

        logger.info(f"Retrieved {len(water_heaters)} water heaters from PostgreSQL")
        return water_heaters
    except Exception as e:
        logger.error(f"Error retrieving water heaters from PostgreSQL: {e}")
        return []


def get_api_water_heaters() -> List[Dict[str, Any]]:
    """Get all water heaters from the API."""
    try:
        # Use configurable API endpoint to get all water heaters
        response = requests.get(f"{API_BASE_URL}/api/water-heaters/")
        if response.status_code != 200:
            logger.error(f"Failed to get water heaters from API: {response.text}")
            return []

        water_heaters = response.json()
        logger.info(f"Retrieved {len(water_heaters)} water heaters from API")
        return water_heaters
    except Exception as e:
        logger.error(f"Error retrieving water heaters from API: {e}")
        return []


def get_ui_water_heaters_html() -> Optional[str]:
    """Get the water heaters list page HTML."""
    try:
        response = requests.get(f"{UI_BASE_URL}/water-heaters")
        if response.status_code != 200:
            logger.error(
                f"Failed to get water heaters list page: {response.status_code}"
            )
            return None

        logger.info("Successfully retrieved water heaters UI page")
        return response.text
    except Exception as e:
        logger.error(f"Error retrieving water heaters UI page: {e}")
        return None


async def verify_postgres_data_to_api_consistency():
    """Verify that water heaters from PostgreSQL match those from the API."""
    # Get data
    pg_water_heaters = await get_postgres_water_heaters()
    api_water_heaters = get_api_water_heaters()

    if not pg_water_heaters:
        logger.error("No water heaters found in PostgreSQL")
        return False

    if not api_water_heaters:
        logger.error("No water heaters returned from API")
        return False

    # Create ID maps for easy lookup
    pg_heaters_by_id = {h["id"]: h for h in pg_water_heaters}
    api_heaters_by_id = {h["id"]: h for h in api_water_heaters}

    # Check that all PostgreSQL water heaters are in the API response
    missing_in_api = set(pg_heaters_by_id.keys()) - set(api_heaters_by_id.keys())
    if missing_in_api:
        logger.error(
            f"Water heaters in PostgreSQL but missing from API: {missing_in_api}"
        )
        return False

    # Check that all API water heaters are in PostgreSQL
    # This ensures we're not showing mock data
    missing_in_pg = set(api_heaters_by_id.keys()) - set(pg_heaters_by_id.keys())
    if missing_in_pg:
        logger.error(
            f"Water heaters in API but missing from PostgreSQL: {missing_in_pg}"
        )
        return False

    logger.info("✅ All water heaters in API match those in PostgreSQL")
    return True


async def verify_rheem_water_heater_types():
    """Verify that we have at least 2 water heaters of each Rheem type."""
    pg_water_heaters = await get_postgres_water_heaters()

    if not pg_water_heaters:
        logger.error("No water heaters found in PostgreSQL")
        return False

    # Filter for Rheem water heaters
    rheem_heaters = [h for h in pg_water_heaters if h.get("manufacturer") == "Rheem"]

    if not rheem_heaters:
        logger.error("No Rheem water heaters found in PostgreSQL")
        return False

    # Group by type
    by_type = {}
    for heater in rheem_heaters:
        heater_type = heater.get("type")
        if heater_type not in by_type:
            by_type[heater_type] = []
        by_type[heater_type].append(heater)

    # Check if we have at least 2 water heaters of each type
    all_requirements_met = True
    for heater_type in ["Tank", "Tankless", "Hybrid"]:
        count = len(by_type.get(heater_type, []))
        if count >= 2:
            logger.info(f"✅ Found {count} Rheem {heater_type} water heaters")
        else:
            logger.error(
                f"❌ Only found {count} Rheem {heater_type} water heaters, need at least 2"
            )
            all_requirements_met = False

    return all_requirements_met


def verify_ui_displays_postgres_data():
    """Verify that the UI displays water heaters from PostgreSQL."""
    html = get_ui_water_heaters_html()

    if not html:
        logger.error("Failed to retrieve water heaters UI page")
        return False

    # Parse the HTML
    soup = BeautifulSoup(html, "html.parser")

    # Check if the page has water heater content
    content = soup.get_text().lower()

    if "no water heaters found" in content:
        logger.error("UI indicates no water heaters found")
        return False

    # Check if the page contains references to Rheem water heaters
    has_rheem = "rheem" in content
    if not has_rheem:
        logger.error("UI does not display any Rheem water heaters")
        return False

    # Check if the page contains references to the different types
    has_tank = "tank" in content
    has_tankless = "tankless" in content
    has_hybrid = "hybrid" in content or "proterra" in content

    type_results = []
    if has_tank:
        type_results.append("✅ Tank water heaters appear in UI")
    else:
        type_results.append("❌ Tank water heaters not found in UI")

    if has_tankless:
        type_results.append("✅ Tankless water heaters appear in UI")
    else:
        type_results.append("❌ Tankless water heaters not found in UI")

    if has_hybrid:
        type_results.append("✅ Hybrid water heaters appear in UI")
    else:
        type_results.append("❌ Hybrid water heaters not found in UI")

    for result in type_results:
        logger.info(result)

    # Check if all types are represented
    all_types_displayed = has_tank and has_tankless and has_hybrid

    # Find all water heater cards or indicators
    water_heater_elements = (
        soup.select(".water-heater-card")
        or soup.select(".device-card")
        or soup.select(".heater-listing")
        or soup.select("[data-device-type='WATER_HEATER']")
    )

    if not water_heater_elements:
        logger.warning("No water heater card elements found in UI")
    else:
        logger.info(f"Found {len(water_heater_elements)} water heater elements in UI")

    return all_types_displayed


async def main():
    """Run all verification checks."""
    logger.info("Starting PostgreSQL to UI data flow verification")

    # Set environment variable to ensure we're using PostgreSQL
    os.environ["IOTSPHERE_ENV"] = "development"
    os.environ["USE_MOCK_DATA"] = "false"

    # Verify PostgreSQL has the expected water heaters
    logger.info("\n--- Verifying Water Heater Presence in PostgreSQL ---")
    pg_data_valid = await verify_rheem_water_heater_types()

    # Verify API returns PostgreSQL data
    logger.info("\n--- Verifying PostgreSQL to API Data Flow ---")
    api_data_valid = await verify_postgres_data_to_api_consistency()

    # Verify UI displays PostgreSQL data
    logger.info("\n--- Verifying PostgreSQL Data in UI ---")
    ui_data_valid = verify_ui_displays_postgres_data()

    # Overall check
    logger.info("\n--- Overall Results ---")
    if pg_data_valid:
        logger.info("✅ PostgreSQL contains required Rheem water heaters")
    else:
        logger.error("❌ PostgreSQL is missing required Rheem water heaters")

    if api_data_valid:
        logger.info("✅ API correctly returns PostgreSQL water heaters")
    else:
        logger.error("❌ API does not correctly return PostgreSQL water heaters")

    if ui_data_valid:
        logger.info("✅ UI displays all types of Rheem water heaters")
    else:
        logger.error("❌ UI does not display all types of Rheem water heaters")

    if pg_data_valid and api_data_valid and ui_data_valid:
        logger.info(
            "\n✅ All requirements met: Data flows correctly from PostgreSQL to UI"
        )
        return 0
    else:
        logger.error("\n❌ Some requirements failed: Data flow issues detected")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
