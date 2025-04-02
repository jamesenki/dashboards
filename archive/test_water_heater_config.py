#!/usr/bin/env python3
"""
Simple test script for water heater configuration management.
This demonstrates the TDD principles by testing our implementation.
"""
import asyncio
import os
import sys
import unittest
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Set testing environment
os.environ["TESTING"] = "True"
os.environ["USE_MOCK_DATA"] = "True"

from src.models.device import DeviceStatus, DeviceType
from src.models.water_heater import WaterHeater, WaterHeaterMode, WaterHeaterStatus
from src.repositories.water_heater_repository import (
    MockWaterHeaterRepository,
    SQLiteWaterHeaterRepository,
)
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)


class TestWaterHeaterConfiguration(unittest.TestCase):
    """Test cases for water heater configuration management."""

    def setUp(self):
        """Set up test environment."""
        # For in-memory SQLite database, we need to use a specific connection string
        # that allows SQLite to persist the in-memory database between connections
        self.db_path = "file:memdb1?mode=memory&cache=shared"

        # We need to initialize the SQLite connection first to ensure database is ready
        import sqlite3

        self.connection = sqlite3.connect(self.db_path, uri=True)

        # Initialize our repositories
        self.sqlite_repo = SQLiteWaterHeaterRepository(db_path=self.db_path)
        self.mock_repo = MockWaterHeaterRepository()

        # Explicitly create all required tables before running tests
        self.sqlite_repo._create_tables(self.connection)

        # Create water_heater_health_config table if not exists (double-check)
        cursor = self.connection.cursor()
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS water_heater_health_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parameter TEXT NOT NULL,
            threshold REAL,
            status TEXT NOT NULL
        )
        """
        )

        # Create water_heater_alert_rules table if not exists (double-check)
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS water_heater_alert_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            condition TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1
        )
        """
        )
        self.connection.commit()

        # Set up service with our repository
        self.service = ConfigurableWaterHeaterService(repository=self.sqlite_repo)

    def tearDown(self):
        """Clean up after tests."""
        # Close our in-memory database connection
        if hasattr(self, "connection"):
            self.connection.close()

    def test_repository_selection(self):
        """Test service selects repository based on environment variable."""
        # Test with USE_MOCK_DATA=True
        os.environ["USE_MOCK_DATA"] = "True"
        service = ConfigurableWaterHeaterService()
        self.assertIsInstance(service.repository, MockWaterHeaterRepository)

        # Test with USE_MOCK_DATA=False
        os.environ["USE_MOCK_DATA"] = "False"
        service = ConfigurableWaterHeaterService()
        self.assertIsInstance(service.repository, SQLiteWaterHeaterRepository)

        # Reset for other tests
        os.environ["USE_MOCK_DATA"] = "True"

    def test_create_water_heater(self):
        """Test creating a water heater."""
        water_heater = WaterHeater(
            id="wh-test-1",  # Must provide a valid ID
            name="Test Water Heater",
            type=DeviceType.WATER_HEATER,  # Required field
            current_temperature=45.0,
            target_temperature=50.0,
            status=DeviceStatus.ONLINE,  # Device status (not WaterHeaterStatus)
            mode=WaterHeaterMode.ECO,
            heater_status=WaterHeaterStatus.STANDBY,  # Water heater status
        )

        # Create water heater
        created = asyncio.run(self.service.create_water_heater(water_heater))

        # Verify
        self.assertIsNotNone(created)
        self.assertIsNotNone(created.id)
        self.assertEqual(created.name, "Test Water Heater")
        self.assertEqual(created.heater_status, WaterHeaterStatus.STANDBY)

    def test_health_configuration(self):
        """Test health configuration management."""
        # Define test configuration
        test_config = {
            "temperature_high": {"threshold": 70.0, "status": "RED"},
            "temperature_warning": {"threshold": 65.0, "status": "YELLOW"},
        }

        # Set configuration
        asyncio.run(self.sqlite_repo.set_health_configuration(test_config))

        # Retrieve and verify
        config = asyncio.run(self.sqlite_repo.get_health_configuration())
        self.assertEqual(len(config), 2)
        self.assertEqual(config["temperature_high"]["threshold"], 70.0)
        self.assertEqual(config["temperature_high"]["status"], "RED")
        self.assertEqual(config["temperature_warning"]["status"], "YELLOW")

    def test_alert_rules(self):
        """Test alert rule management."""
        # Define test rule
        test_rule = {
            "name": "High Temperature Alert",
            "condition": "temperature > 75",
            "severity": "HIGH",
            "message": "Water heater temperature exceeds safe level",
            "enabled": True,
        }

        # Add rule
        added_rule = asyncio.run(self.sqlite_repo.add_alert_rule(test_rule))
        self.assertIsNotNone(added_rule["id"])

        # Retrieve and verify
        rules = asyncio.run(self.sqlite_repo.get_alert_rules())
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["name"], "High Temperature Alert")
        self.assertEqual(rules[0]["severity"], "HIGH")

        # Update rule
        rule_id = rules[0]["id"]
        updated_rule = {**test_rule, "severity": "CRITICAL", "enabled": False}
        asyncio.run(self.sqlite_repo.update_alert_rule(rule_id, updated_rule))

        # Verify update
        rules = asyncio.run(self.sqlite_repo.get_alert_rules())
        self.assertEqual(rules[0]["severity"], "CRITICAL")
        self.assertEqual(rules[0]["enabled"], False)

        # Delete rule
        deleted = asyncio.run(self.sqlite_repo.delete_alert_rule(rule_id))
        self.assertTrue(deleted)

        # Verify deletion
        rules = asyncio.run(self.sqlite_repo.get_alert_rules())
        self.assertEqual(len(rules), 0)

    def test_update_water_heater(self):
        """Test updating a water heater."""
        # Create water heater
        water_heater = WaterHeater(
            id="wh-test-2",  # Must provide a valid ID
            name="Update Test",
            type=DeviceType.WATER_HEATER,  # Required field
            current_temperature=45.0,
            target_temperature=50.0,
            status=DeviceStatus.ONLINE,  # Device status (not WaterHeaterStatus)
            mode=WaterHeaterMode.ECO,
            heater_status=WaterHeaterStatus.STANDBY,  # Water heater status
        )

        created = asyncio.run(self.service.create_water_heater(water_heater))
        device_id = created.id

        # Update temperature
        updated = asyncio.run(self.service.update_target_temperature(device_id, 55.0))
        self.assertEqual(updated.target_temperature, 55.0)

        # Update mode - should change from ECO to BOOST
        updated = asyncio.run(
            self.service.update_mode(device_id, WaterHeaterMode.BOOST)
        )
        self.assertEqual(updated.mode, WaterHeaterMode.BOOST)
        # BOOST mode should set temperature to higher level, typically 65°C
        self.assertGreaterEqual(updated.target_temperature, 60.0)


if __name__ == "__main__":
    # Run the tests
    unittest.main()
