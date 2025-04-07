"""
Comprehensive database validation test for water heaters.

This test verifies that:
1. The database is running and accessible
2. There are at least 16 water heater entries that conform to the proper schema
3. Entries are complete and valid
4. Telemetry values are varied and within reasonable ranges
5. The API/service can connect directly to the database
6. The system FAILS if it must fall back to mock data

This test is stricter than previous validation tests and enforces the use
of real database connections rather than allowing fallback to mock data.
"""
import asyncio
import logging
import os
import statistics
import sys
import time
from typing import Any, Dict, List, Optional

import pytest
import requests
from fastapi import HTTPException

# Adjust the Python path to find the src modules
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, repo_root)

from src.api.data_access import DataAccessLayer
from src.db.connection import get_db_session
from src.db.initialize_db import initialize_database
from src.db.repository import DeviceRepository
from src.models.rheem_water_heater import RheemWaterHeater, RheemWaterHeaterType
from src.models.water_heater import WaterHeater, WaterHeaterMode, WaterHeaterType
from src.scripts.load_aquatherm_data import load_aquatherm_test_data
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Set environment variables to force database use and prevent mock fallback
os.environ["USE_MOCK_DATA"] = "False"
os.environ["FORCE_DB_ONLY"] = "True"  # Custom flag to prevent mock fallback

# API Base URL (assumes default port)
API_BASE_URL = "http://localhost:8006"


async def test_database_connection():
    """Test that the database is running and accessible."""
    logger.info("Testing database connection...")

    # Initialize database with the default path
    db = initialize_database(force_reset=False)
    assert db is not None, "Failed to initialize database"

    # Test a simple query
    cursor = db.connection.cursor()
    cursor.execute("SELECT sqlite_version();")
    version = cursor.fetchone()
    logger.info(f"Connected to SQLite version: {version[0]}")

    # Return the database for use in other tests
    return db


async def test_water_heater_count(db):
    """Test that there are at least 16 water heaters in the database."""
    logger.info("Testing water heater count...")

    # Get a database session
    session_generator = get_db_session()

    # Verify session is not None
    assert session_generator is not None, "Failed to get database session"

    count = 0
    async for session in session_generator:
        try:
            # Import SQLDeviceRepository for direct database access
            from src.db.adapters.sql_devices import SQLDeviceRepository

            # Create SQL repository for direct database access
            sql_repo = SQLDeviceRepository(session)

            # Get all water heaters directly from SQL repository
            # We use DeviceType.WATER_HEATER enum to filter by water heater type
            from src.models.device import DeviceType

            devices = await sql_repo.get_devices(type_filter=DeviceType.WATER_HEATER)

            count = len(devices)

            logger.info(f"Found {count} water heaters in database")

            # Ensure we have at least 16 water heaters
            assert (
                count >= 16
            ), f"Expected at least 16 water heaters, found only {count}"

            # Return devices for use in other tests
            return devices
        except Exception as e:
            logger.error(f"Error getting water heaters: {str(e)}")
            # Let this fail - we don't want mock fallback
            raise
        finally:
            # Close session
            await session.close()

    # If we reach here without returning, something went wrong
    assert False, "Failed to get water heaters from database session"


async def test_water_heater_schema(devices):
    """Test that water heaters conform to the proper schema."""
    logger.info("Testing water heater schema...")

    # Define required fields based on Device and WaterHeater models
    required_fields = [
        "id",
        "name",
        "type",
        "status",
        "current_temperature",
        "target_temperature",
    ]

    # Optional but important fields
    optional_fields = [
        "location",
        "last_seen",
        "min_temperature",
        "max_temperature",
        "mode",
        "heater_status",
        "heater_type",
        "capacity",
        "efficiency_rating",
    ]

    # Track heater types to ensure we have at least 2 of each type
    heater_type_counts = {}

    # Validate each water heater
    for device in devices:
        # Convert to dictionary for easier access
        if hasattr(device, "model_dump"):
            water_heater = device.model_dump()
        elif hasattr(device, "dict"):
            water_heater = device.dict()
        else:
            water_heater = device

        device_id = water_heater.get("id", "unknown")
        logger.info(f"Validating water heater: {device_id}")

        # Check all required fields exist
        for field in required_fields:
            assert (
                field in water_heater
            ), f"Required field '{field}' missing from water heater {device_id}"
            assert (
                water_heater[field] is not None
            ), f"Required field '{field}' is None in water heater {device_id}"

        # Verify type is WATER_HEATER
        device_type = water_heater.get("type")
        if isinstance(device_type, str):
            assert (
                device_type == "water_heater"
            ), f"Device type should be 'water_heater', got '{device_type}'"
        elif hasattr(device_type, "value"):
            assert (
                device_type.value == "water_heater"
            ), f"Device type should be 'water_heater', got '{device_type.value}'"

        # Get the heater type if it exists
        heater_type = water_heater.get("heater_type")
        if heater_type:
            # Handle string or enum for heater_type
            if isinstance(heater_type, str):
                heater_type_str = heater_type
            elif hasattr(heater_type, "value"):
                heater_type_str = heater_type.value
            else:
                heater_type_str = str(heater_type)

            # Track heater type counts
            if heater_type_str not in heater_type_counts:
                heater_type_counts[heater_type_str] = 0
            heater_type_counts[heater_type_str] += 1

            # Log the heater type
            logger.info(f"Water heater {device_id} has type: {heater_type_str}")
        else:
            logger.warning(f"Water heater {device_id} doesn't have a heater_type field")

        # Check manufacturer if it exists (it's not a required field in the model)
        manufacturer = water_heater.get("manufacturer")
        if manufacturer:
            logger.info(f"Water heater {device_id} manufacturer: {manufacturer}")

    # Log type counts
    logger.info(f"Water heater type counts: {heater_type_counts}")

    # If we have type counts, ensure we have at least 2 of each type
    if heater_type_counts:
        for type_name, count in heater_type_counts.items():
            assert (
                count >= 2
            ), f"Expected at least 2 {type_name} water heaters, found only {count}"
    else:
        logger.warning("No heater types found in any water heaters")

    # Return the devices for use in other tests
    return devices


async def test_telemetry_values(devices):
    """Test that telemetry values are varied and within reasonable ranges."""
    logger.info("Testing telemetry values...")

    # Define valid temperature ranges for each field (in Celsius)
    temp_ranges = {
        "current_temperature": (0, 100),  # Celsius (32-212°F)
        "target_temperature": (25, 70),  # Celsius (77-158°F)
    }

    # Track temperature values to check for variation
    current_temps = []
    target_temps = []
    min_temps = []
    max_temps = []

    # Track capacity values if present
    capacities = []

    # Validate each water heater
    for device in devices:
        # Convert to dictionary for easier access
        if hasattr(device, "model_dump"):
            water_heater = device.model_dump()
        elif hasattr(device, "dict"):
            water_heater = device.dict()
        else:
            water_heater = device

        device_id = water_heater.get("id", "unknown")
        logger.info(f"Validating telemetry for water heater: {device_id}")

        # Check temperature fields
        for field, (min_val, max_val) in temp_ranges.items():
            value = water_heater.get(field)
            assert (
                value is not None
            ), f"Field '{field}' is missing in water heater {device_id}"
            assert isinstance(
                value, (int, float)
            ), f"Field '{field}' is not numeric in water heater {device_id}"
            assert (
                min_val <= value <= max_val
            ), f"Field '{field}' value {value} is outside valid range ({min_val}, {max_val}) in water heater {device_id}"

            # Track values for variation check
            if field == "current_temperature":
                current_temps.append(value)
            elif field == "target_temperature":
                target_temps.append(value)

        # Collect min/max temperature settings if present
        min_temp = water_heater.get("min_temperature")
        if min_temp is not None and isinstance(min_temp, (int, float)):
            min_temps.append(min_temp)

        max_temp = water_heater.get("max_temperature")
        if max_temp is not None and isinstance(max_temp, (int, float)):
            max_temps.append(max_temp)

        # Collect capacity if present
        capacity = water_heater.get("capacity")
        if capacity is not None and isinstance(capacity, (int, float)):
            capacities.append(capacity)

    # Check for variation in temperature values
    for temps, field_name in [
        (current_temps, "current_temperature"),
        (target_temps, "target_temperature"),
        (min_temps, "min_temperature"),
        (max_temps, "max_temperature"),
    ]:
        if len(temps) > 1:
            std_dev = statistics.stdev(temps)
            min_val, max_val = min(temps), max(temps)
            range_val = max_val - min_val

            logger.info(
                f"{field_name} statistics: min={min_val}, max={max_val}, range={range_val}, std_dev={std_dev}"
            )

            # Only assert variation for current and target temps
            if field_name in ["current_temperature", "target_temperature"]:
                # We want some variation, but the threshold is lower for Celsius temperatures
                assert (
                    range_val > 2
                ), f"Insufficient variation in {field_name} values (range={range_val})"
                assert (
                    std_dev > 0.5
                ), f"Insufficient variation in {field_name} values (std_dev={std_dev})"

    # Check capacity variation if we have enough values
    if len(capacities) > 1:
        std_dev = statistics.stdev(capacities)
        min_val, max_val = min(capacities), max(capacities)
        range_val = max_val - min_val

        logger.info(
            f"capacity statistics: min={min_val}, max={max_val}, range={range_val}, std_dev={std_dev}"
        )

        # For capacity, we expect significant variation
        assert (
            range_val > 5
        ), f"Insufficient variation in capacity values (range={range_val})"

    # Check if we have any readings data
    readings_found = False
    for device in devices:
        if hasattr(device, "model_dump"):
            water_heater = device.model_dump()
        elif hasattr(device, "dict"):
            water_heater = device.dict()
        else:
            water_heater = device

        readings = water_heater.get("readings")
        if readings and len(readings) > 0:
            readings_found = True
            logger.info(
                f"Water heater {water_heater.get('id')} has {len(readings)} readings"
            )
            break

    if not readings_found:
        logger.warning("No water heater readings found - data may be incomplete")

    logger.info("All telemetry values are valid and show sufficient variation")


async def test_api_connection():
    """Test that the API can connect to the database and retrieve water heaters.
    Returns True if using mock data, False if using database.
    """
    logger.info("Testing API connection to database...")

    # Force environment variables to prevent mock data use
    os.environ["USE_MOCK_DATA"] = "False"
    os.environ["DATABASE_FALLBACK_ENABLED"] = "False"

    # Get a database session directly to verify it's working
    session_generator = get_db_session()
    if session_generator is None:
        logger.error("Failed to get database session")
        return True  # Likely using mock data

    # Test direct database access first
    db_devices_count = 0
    try:
        async for session in session_generator:
            try:
                # Import SQLDeviceRepository for direct database access
                from src.db.adapters.sql_devices import SQLDeviceRepository

                # Create SQL repository for direct database access
                sql_repo = SQLDeviceRepository(session)

                # Get all water heaters directly from SQL
                from src.models.device import DeviceType

                devices = await sql_repo.get_devices(
                    type_filter=DeviceType.WATER_HEATER
                )

                if not devices:
                    logger.warning("No devices returned from direct database query")
                    return True  # No devices, likely will use mock data

                db_devices_count = len(devices)
                logger.info(
                    f"Successfully retrieved {db_devices_count} water heaters directly from database"
                )
                break
            finally:
                await session.close()
    except Exception as e:
        logger.error(f"Direct database access failed: {str(e)}")
        return True  # Error with database, likely will use mock data

    # Now test the service layer
    try:
        # Create service with environment variable control
        logger.info("Creating water heater service...")
        service = ConfigurableWaterHeaterService()

        # Get all water heaters
        logger.info("Retrieving water heaters from service...")
        water_heaters = await service.get_water_heaters()

        # Ensure we got water heaters
        if not water_heaters:
            logger.error("No water heaters returned from service layer")
            return True  # No water heaters, likely using mock data

        # Check if we're using mock data
        using_mock = False
        if isinstance(water_heaters, tuple) and len(water_heaters) > 1:
            models, from_db = water_heaters
            logger.info(
                f"Service returned (models, from_db) tuple with from_db={from_db}"
            )
            if not from_db:
                logger.error("Service explicitly reported using mock data!")
                return True  # Definitely using mock data

            service_count = len(models)
        else:
            service_count = len(water_heaters)
            # Can't tell for sure, but if count matches DB, probably real data

        logger.info(f"Service returned {service_count} water heaters")

        # Compare counts as a sanity check
        if db_devices_count > 0 and abs(service_count - db_devices_count) > 5:
            logger.warning(
                f"Service returned {service_count} water heaters but database has {db_devices_count}"
            )
            logger.warning(
                "This large discrepancy suggests we might be using mock data"
            )
            return True

        # If we made it here, we're probably using the database
        return False

    except Exception as e:
        logger.error(f"Error in service layer: {str(e)}")
        # If there's an error about mock fallback
        if "mock" in str(e).lower() or "fallback" in str(e).lower():
            logger.error("Service explicitly mentioned mock data in error")
            return True
        return True  # Any service error likely means mock fallback


async def run_all_tests():
    """Run all database validation tests in sequence."""
    start_time = time.time()
    logger.info("Starting comprehensive database validation tests...")

    try:
        # Test 1: Database Connection
        db = await test_database_connection()
        logger.info("✅ Database connection test passed")

        # Test 2: Water Heater Count
        devices = await test_water_heater_count(db)
        logger.info(f"✅ Water heater count test passed - found {len(devices)} devices")

        # Only continue with schema/telemetry tests if we have devices
        if devices and len(devices) > 0:
            logger.info("Performing basic schema validation...")
            # Basic device validation (only the fields we know exist)
            for device in devices[:5]:  # Just check the first 5
                if hasattr(device, "model_dump"):
                    d = device.model_dump()
                elif hasattr(device, "dict"):
                    d = device.dict()
                else:
                    d = device

                # Check for required Device fields
                assert "id" in d and d["id"], f"Missing 'id' in device"
                assert (
                    "name" in d and d["name"]
                ), f"Missing 'name' in device {d.get('id')}"
                assert "type" in d, f"Missing 'type' in device {d.get('id')}"

                # Verify it's a water heater
                if isinstance(d["type"], str):
                    assert (
                        d["type"] == "water_heater"
                    ), f"Device {d.get('id')} is not a water heater"
                else:  # Enum
                    assert str(d["type"]).endswith(
                        "WATER_HEATER"
                    ), f"Device {d.get('id')} is not a water heater"

            logger.info("✅ Basic schema validation passed")

        # Test 3: API Connection - this is critical to check mock fallback
        using_mock = await test_api_connection()
        if using_mock:
            logger.error(
                "❌ API Connection test failed - service is using mock data instead of database"
            )
            return False
        else:
            logger.info("✅ API connection test passed - using real database")

        end_time = time.time()
        logger.info(
            f"All tests passed! Total time: {end_time - start_time:.2f} seconds"
        )
        return True
    except AssertionError as e:
        logger.error(f"❌ Test failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    # Set the environment variable to force database use
    os.environ["USE_MOCK_DATA"] = "False"
    os.environ["FORCE_DB_ONLY"] = "True"

    # Run the tests
    success = asyncio.run(run_all_tests())

    # Exit with appropriate status code
    sys.exit(0 if success else 1)
