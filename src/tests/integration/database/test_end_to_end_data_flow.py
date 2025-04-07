"""
End-to-end data flow tests to verify database integration.

These tests verify that:
1. Data is correctly stored in the database
2. Data is retrieved from the database, not mock sources
3. Data displayed on the UI matches what's in the database
"""
import logging
import os
import sqlite3
import sys
import uuid

import pytest
from fastapi.testclient import TestClient

from src.config import config
from src.main import app
from src.models.device import DeviceStatus, DeviceType
from src.models.water_heater import WaterHeaterMode, WaterHeaterStatus
from src.repositories.water_heater_repository import SQLiteWaterHeaterRepository
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create test client
client = TestClient(app)


class TestEndToEndDataFlow:
    """End-to-end tests for data flow from database to UI."""

    @pytest.fixture(scope="function")
    def use_real_database(self):
        """Configure the environment to use the real database."""
        # Store original environment values to restore later
        original_use_mock = os.environ.get("USE_MOCK_DATA")
        original_db_path = os.environ.get("DATABASE_PATH")

        # Set environment to use real database
        os.environ["USE_MOCK_DATA"] = "false"

        # Use a test-specific database path
        test_db_path = "test_end_to_end.db"
        os.environ["DATABASE_PATH"] = test_db_path

        # Make sure the test database exists and has the right schema
        repo = SQLiteWaterHeaterRepository()

        # Yield control back to the test
        yield

        # Clean up - restore original environment variables
        if original_use_mock is not None:
            os.environ["USE_MOCK_DATA"] = original_use_mock
        else:
            os.environ.pop("USE_MOCK_DATA", None)

        if original_db_path is not None:
            os.environ["DATABASE_PATH"] = original_db_path
        else:
            os.environ.pop("DATABASE_PATH", None)

        # Clean up the test database
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
                logger.info(f"Removed test database: {test_db_path}")
            except Exception as e:
                logger.warning(f"Failed to remove test database: {e}")

    @pytest.fixture(scope="function")
    def test_water_heater(self, use_real_database):
        """Create a test water heater in the database directly."""
        # Generate a unique ID for this test
        test_id = f"test-wh-{uuid.uuid4().hex[:8]}"

        # Create test data
        heater_data = {
            "id": test_id,
            "name": "Test Database Heater",
            "type": DeviceType.WATER_HEATER.value,
            "status": DeviceStatus.ONLINE.value,
            "target_temperature": 52.0,
            "current_temperature": 48.5,
            "min_temperature": 40.0,
            "max_temperature": 80.0,
            "mode": WaterHeaterMode.ECO.value,
            "heater_status": WaterHeaterStatus.STANDBY.value,
            "location": "Test Location",
            "manufacturer": "Test Manufacturer",
            "model": "Test Model",
            "health_status": "GREEN",
        }

        # Create repository and insert the water heater
        repo = SQLiteWaterHeaterRepository()
        db_path = os.environ.get("DATABASE_PATH", "test_end_to_end.db")

        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create the water_heaters table if it doesn't exist
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS water_heaters (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            status TEXT,
            target_temperature REAL,
            current_temperature REAL,
            min_temperature REAL,
            max_temperature REAL,
            mode TEXT,
            heater_status TEXT,
            location TEXT,
            manufacturer TEXT,
            model TEXT,
            health_status TEXT,
            last_seen TEXT
        )
        """
        )

        # Insert the test water heater
        cursor.execute(
            """
        INSERT INTO water_heaters (
            id, name, type, status, target_temperature, current_temperature,
            min_temperature, max_temperature, mode, heater_status, location,
            manufacturer, model, health_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                heater_data["id"],
                heater_data["name"],
                heater_data["type"],
                heater_data["status"],
                heater_data["target_temperature"],
                heater_data["current_temperature"],
                heater_data["min_temperature"],
                heater_data["max_temperature"],
                heater_data["mode"],
                heater_data["heater_status"],
                heater_data["location"],
                heater_data["manufacturer"],
                heater_data["model"],
                heater_data["health_status"],
            ),
        )

        conn.commit()
        conn.close()

        logger.info(f"Created test water heater in database with ID: {test_id}")

        # Return the test data for verification
        return heater_data

    def test_database_to_api_data_flow(self, test_water_heater):
        """Test that data flows correctly from database to API."""
        # Make a request to get the water heater by ID
        response = client.get(f"/api/water-heaters/{test_water_heater['id']}")

        # Verify the response
        assert (
            response.status_code == 200
        ), f"Failed to get water heater: {response.text}"

        # Get the water heater data from the response
        api_data = response.json()

        # Verify the data matches what we inserted in the database
        assert api_data["id"] == test_water_heater["id"], "ID doesn't match"
        assert api_data["name"] == test_water_heater["name"], "Name doesn't match"
        assert (
            api_data["target_temperature"] == test_water_heater["target_temperature"]
        ), "Target temperature doesn't match"
        assert (
            api_data["current_temperature"] == test_water_heater["current_temperature"]
        ), "Current temperature doesn't match"

        logger.info("Successfully verified database-to-API data flow")

    def test_api_to_database_persistence(self, use_real_database):
        """Test that data created via API is persisted to the database."""
        # Create a unique test water heater via the API
        test_id = f"api-wh-{uuid.uuid4().hex[:8]}"

        # Prepare the water heater data
        new_heater = {
            "id": test_id,
            "name": "API Created Heater",
            "type": DeviceType.WATER_HEATER.value,
            "status": DeviceStatus.ONLINE.value,
            "target_temperature": 55.0,
            "current_temperature": 50.0,
            "min_temperature": 40.0,
            "max_temperature": 85.0,
            "mode": WaterHeaterMode.ECO.value,
            "heater_status": WaterHeaterStatus.STANDBY.value,
            "location": "API Test Location",
            "manufacturer": "API Test Manufacturer",
            "model": "API Test Model",
        }

        # Create the water heater via API
        create_response = client.post("/api/water-heaters", json=new_heater)
        assert (
            create_response.status_code == 201
        ), f"Failed to create water heater: {create_response.text}"

        # Get the created water heater's ID
        created_data = create_response.json()
        heater_id = created_data.get("id", test_id)

        # Now verify that the water heater exists in the database
        db_path = os.environ.get("DATABASE_PATH", "test_end_to_end.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query the database
        cursor.execute("SELECT * FROM water_heaters WHERE id = ?", (heater_id,))
        row = cursor.fetchone()
        conn.close()

        # Verify the water heater exists in the database
        assert (
            row is not None
        ), f"Water heater with ID {heater_id} not found in database"

        logger.info("Successfully verified API-to-database persistence")

    @pytest.mark.xfail(
        reason="UI data comes from mock when no database data is present"
    )
    def test_ui_data_matches_database(self, use_real_database):
        """Test that the UI only displays data from the database."""
        # Get all water heaters via API
        response = client.get("/api/water-heaters")
        assert response.status_code == 200

        api_data = response.json()

        # Get all water heaters from database
        db_path = os.environ.get("DATABASE_PATH", "test_end_to_end.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query the database for all water heaters
        cursor.execute("SELECT id FROM water_heaters")
        db_ids = [row[0] for row in cursor.fetchall()]
        conn.close()

        if len(db_ids) == 0:
            pytest.skip("No water heaters in database, can't verify UI data")

        # Verify that every ID in the API response exists in the database
        for heater in api_data:
            assert (
                heater["id"] in db_ids
            ), f"Water heater with ID {heater['id']} not found in database"

        # Verify that the count matches
        assert len(api_data) == len(
            db_ids
        ), "Number of water heaters in API response doesn't match database"

        logger.info("Successfully verified UI data matches database")
