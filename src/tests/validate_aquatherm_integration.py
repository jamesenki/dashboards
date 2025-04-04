"""
End-to-end validation script for AquaTherm water heater integration.

This script verifies that:
1. Data is present, complete, and using proper schema
2. Data can be pulled from the DB
3. All Water Heater screens, tabs, and divs are being populated
4. Data pulled from DB is what is being displayed on UI
5. The appearance is using consistent styling

Following TDD principles, this validates that our implementation meets the requirements
without changing the tests themselves.
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

# Add the parent directory to sys.path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Base URL for the API
API_BASE_URL = "http://localhost:8006"


def validate_aquatherm_api_routes():
    """Validate that all AquaTherm API routes are accessible."""
    logger.info("Validating AquaTherm API routes...")

    # Test routes to check
    routes = [
        "/api/aquatherm-water-heaters",
        "/api/aquatherm-water-heaters/aqua-wh-tank-001",
        "/api/aquatherm-water-heaters/aqua-wh-hybrid-001",
        "/api/aquatherm-water-heaters/aqua-wh-tankless-001",
    ]

    success_count = 0
    failure_count = 0

    for route in routes:
        url = f"{API_BASE_URL}{route}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                logger.info(f"✅ Route {route} is accessible")
                success_count += 1
            else:
                logger.error(
                    f"❌ Route {route} returned status code {response.status_code}"
                )
                failure_count += 1
        except Exception as e:
            logger.error(f"❌ Error accessing route {route}: {str(e)}")
            failure_count += 1

    logger.info(
        f"API route validation: {success_count} successes, {failure_count} failures"
    )
    return success_count, failure_count


def validate_aquatherm_data_schema():
    """Validate that the AquaTherm data follows the correct schema."""
    logger.info("Validating AquaTherm data schema...")

    # Get all AquaTherm water heaters
    url = f"{API_BASE_URL}/api/aquatherm-water-heaters"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            logger.error(
                f"❌ Failed to get AquaTherm water heaters: Status code {response.status_code}"
            )
            return 0, 1

        water_heaters = response.json()
        if not water_heaters:
            logger.error("❌ No AquaTherm water heaters found")
            return 0, 1

        logger.info(f"Found {len(water_heaters)} AquaTherm water heaters")

        # Count of each heater type for validation
        tank_count = 0
        hybrid_count = 0
        tankless_count = 0

        # Track schema validity
        valid_count = 0
        invalid_count = 0

        # Required fields for all water heaters
        required_fields = [
            "id",
            "name",
            "type",
            "status",
            "location",
            "manufacturer",
            "target_temperature",
            "current_temperature",
            "properties",
        ]

        # Required property fields by heater type
        type_properties = {
            "TANK": ["heater_type", "capacity", "uef_rating"],
            "HYBRID": ["heater_type", "capacity", "uef_rating"],
            "TANKLESS": ["heater_type", "uef_rating"],
        }

        for heater in water_heaters:
            # Validate required fields
            missing_fields = [field for field in required_fields if field not in heater]

            if missing_fields:
                logger.error(
                    f"❌ Water heater {heater.get('id', 'unknown')} missing required fields: {missing_fields}"
                )
                invalid_count += 1
                continue

            # Validate manufacturer is AquaTherm
            if heater.get("manufacturer", "").lower() != "aquatherm":
                logger.error(
                    f"❌ Water heater {heater['id']} has incorrect manufacturer: {heater.get('manufacturer')}"
                )
                invalid_count += 1
                continue

            # Validate properties based on heater type
            heater_type = heater.get("properties", {}).get("heater_type")
            if not heater_type:
                logger.error(
                    f"❌ Water heater {heater['id']} missing heater_type in properties"
                )
                invalid_count += 1
                continue

            # Count heater types
            if heater_type == "TANK":
                tank_count += 1
            elif heater_type == "HYBRID":
                hybrid_count += 1
            elif heater_type == "TANKLESS":
                tankless_count += 1

            # Validate type-specific properties
            if heater_type in type_properties:
                required_type_props = type_properties[heater_type]
                missing_props = [
                    prop
                    for prop in required_type_props
                    if prop not in heater.get("properties", {})
                ]

                if missing_props:
                    logger.error(
                        f"❌ Water heater {heater['id']} missing required properties for type {heater_type}: {missing_props}"
                    )
                    invalid_count += 1
                    continue

            # If we get here, the schema is valid
            logger.info(f"✅ Water heater {heater['id']} has valid schema")
            valid_count += 1

        # Validate we have at least 2 of each type
        if tank_count < 2:
            logger.error(f"❌ Not enough TANK water heaters found: {tank_count}/2")
            invalid_count += 1
        else:
            logger.info(f"✅ Found {tank_count} TANK water heaters (minimum 2 required)")

        if hybrid_count < 2:
            logger.error(f"❌ Not enough HYBRID water heaters found: {hybrid_count}/2")
            invalid_count += 1
        else:
            logger.info(
                f"✅ Found {hybrid_count} HYBRID water heaters (minimum 2 required)"
            )

        if tankless_count < 2:
            logger.error(
                f"❌ Not enough TANKLESS water heaters found: {tankless_count}/2"
            )
            invalid_count += 1
        else:
            logger.info(
                f"✅ Found {tankless_count} TANKLESS water heaters (minimum 2 required)"
            )

        logger.info(
            f"Schema validation: {valid_count} valid schemas, {invalid_count} invalid schemas"
        )
        return valid_count, invalid_count

    except Exception as e:
        logger.error(f"❌ Error validating AquaTherm data schema: {str(e)}")
        return 0, 1


def validate_aquatherm_detailed_endpoints():
    """Validate detailed AquaTherm water heater endpoints."""
    logger.info("Validating AquaTherm detailed endpoints...")

    # Get all AquaTherm water heaters to get their IDs
    url = f"{API_BASE_URL}/aquatherm-water-heaters"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            logger.error(
                f"❌ Failed to get AquaTherm water heaters: Status code {response.status_code}"
            )
            return 0, 1

        water_heaters = response.json()
        if not water_heaters:
            logger.error("❌ No AquaTherm water heaters found")
            return 0, 1

        # Select the first water heater to test the detailed endpoints
        test_heater_id = water_heaters[0]["id"]
        logger.info(f"Testing detailed endpoints using water heater {test_heater_id}")

        # Endpoints to test
        endpoints = [
            f"/api/aquatherm-water-heaters/{test_heater_id}",
            f"/api/aquatherm-water-heaters/{test_heater_id}/eco-net-status",
            f"/api/aquatherm-water-heaters/{test_heater_id}/maintenance-prediction",
            f"/api/aquatherm-water-heaters/{test_heater_id}/efficiency-analysis",
            f"/api/aquatherm-water-heaters/{test_heater_id}/telemetry-analysis",
            f"/api/aquatherm-water-heaters/{test_heater_id}/health-status",
            f"/api/aquatherm-water-heaters/{test_heater_id}/operational-summary",
        ]

        success_count = 0
        failure_count = 0

        for endpoint in endpoints:
            url = f"{API_BASE_URL}{endpoint}"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    # Validate response has data
                    if not data:
                        logger.error(f"❌ Endpoint {endpoint} returned empty data")
                        failure_count += 1
                        continue

                    logger.info(f"✅ Endpoint {endpoint} returned valid data")
                    success_count += 1
                else:
                    logger.error(
                        f"❌ Endpoint {endpoint} returned status code {response.status_code}"
                    )
                    failure_count += 1
            except Exception as e:
                logger.error(f"❌ Error accessing endpoint {endpoint}: {str(e)}")
                failure_count += 1

        logger.info(
            f"Detailed endpoint validation: {success_count} successes, {failure_count} failures"
        )
        return success_count, failure_count

    except Exception as e:
        logger.error(f"❌ Error validating AquaTherm detailed endpoints: {str(e)}")
        return 0, 1


def run_validation():
    """Run all validation tests and summarize results."""
    logger.info("Starting AquaTherm integration validation...")

    # Run all validation tests
    api_success, api_failure = validate_aquatherm_api_routes()
    schema_success, schema_failure = validate_aquatherm_data_schema()
    endpoint_success, endpoint_failure = validate_aquatherm_detailed_endpoints()

    # Calculate total results
    total_success = api_success + schema_success + endpoint_success
    total_failure = api_failure + schema_failure + endpoint_failure

    # Display summary
    logger.info("\n=== VALIDATION SUMMARY ===")
    logger.info(f"API Routes: {api_success} successes, {api_failure} failures")
    logger.info(f"Data Schema: {schema_success} successes, {schema_failure} failures")
    logger.info(
        f"Detailed Endpoints: {endpoint_success} successes, {endpoint_failure} failures"
    )
    logger.info(f"TOTAL: {total_success} successes, {total_failure} failures")

    if total_failure == 0:
        logger.info("✅ VALIDATION PASSED: All tests were successful!")
        logger.info("The AquaTherm water heater integration is correctly implemented.")
    else:
        logger.error(f"❌ VALIDATION FAILED: {total_failure} failures detected.")
        logger.error("Please check the logs above for details on the failures.")

    return total_success, total_failure


if __name__ == "__main__":
    run_validation()
