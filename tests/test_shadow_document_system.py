#!/usr/bin/env python3
"""
Comprehensive test suite for shadow document system.

This test suite validates the entire shadow document system from API to storage,
focusing on MongoDB integration and temperature history data.
"""
import asyncio
import json
import logging
import os
import unittest
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ShadowDocumentSystemTest(unittest.TestCase):
    """Test the shadow document system end-to-end."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and resources once for all tests."""
        # Force MongoDB storage for tests
        os.environ["SHADOW_STORAGE_TYPE"] = "mongodb"

        # Import modules after setting environment variables
        from src.infrastructure.device_shadow.mongodb_shadow_storage import (
            MongoDBShadowStorage,
        )
        from src.services.asset_registry import AssetRegistryService
        from src.services.device_shadow import DeviceShadowService

        cls.test_device_id = "test-wh-001"
        # Run setup asynchronously
        asyncio.run(cls._async_setup())

    @classmethod
    async def _async_setup(cls):
        """Async setup for the test class."""
        from src.infrastructure.device_shadow.mongodb_shadow_storage import (
            MongoDBShadowStorage,
        )
        from src.services.asset_registry import AssetRegistryService
        from src.services.device_shadow import DeviceShadowService

        # Initialize MongoDB storage directly
        cls.mongo_storage = MongoDBShadowStorage(
            mongo_uri="mongodb://localhost:27017/", db_name="iotsphere_test"
        )
        await cls.mongo_storage.initialize()

        # Create test services
        cls.shadow_service = DeviceShadowService(storage_provider=cls.mongo_storage)
        cls.registry_service = AssetRegistryService()

        # Clean test database
        await cls.mongo_storage.drop_collections()

        # Create test device
        device_data = {
            "device_id": cls.test_device_id,
            "name": "Test Water Heater",
            "manufacturer": "AquaSmart",
            "brand": "AquaSmart",
            "model": "SmartTank Pro",
            "type": "water_heater",
            "status": "ONLINE",
            "location": "Test Building",
            "installation_date": datetime.now().isoformat(),
            "warranty_expiry": (datetime.now() + timedelta(days=365 * 5)).isoformat(),
            "capacity": 50,
            "efficiency_rating": 0.92,
            "heater_type": "Tank",
            "features": ["Smart Control", "Energy Efficient", "Remote Monitoring"],
        }

        try:
            await cls.registry_service.register_device(device_data)
            logger.info(f"Test device {cls.test_device_id} registered")
        except Exception as e:
            logger.warning(f"Error registering test device: {e}")

    @classmethod
    def tearDownClass(cls):
        """Clean up resources after all tests."""
        # Run cleanup asynchronously
        asyncio.run(cls._async_teardown())

    @classmethod
    async def _async_teardown(cls):
        """Async teardown for the test class."""
        # Clean test database
        await cls.mongo_storage.drop_collections()
        await cls.mongo_storage.close()

    def test_01_shadow_storage_type(self):
        """Verify shadow storage is configured for MongoDB."""
        from src.services.device_shadow import DeviceShadowService

        service = DeviceShadowService()

        # Check storage type
        storage_type = service.storage_provider.__class__.__name__
        self.assertEqual(
            storage_type,
            "MongoDBShadowStorage",
            f"Expected MongoDB storage, got {storage_type}",
        )
        logger.info("Storage type verified: MongoDB")

    def test_02_create_shadow_document(self):
        """Test creating a shadow document."""
        # Create shadow document
        initial_state = {
            "device_id": self.test_device_id,
            "reported": {
                "name": "Test Water Heater",
                "model": "SmartTank Pro",
                "manufacturer": "AquaSmart",
                "temperature": 120.5,
                "target_temperature": 125.0,
                "min_temperature": 40.0,
                "max_temperature": 140.0,
                "pressure": 60.0,
                "flow_rate": 3.2,
                "energy_usage": 450.0,
                "heater_status": "STANDBY",
                "connection_status": "ONLINE",
                "mode": "ECO",
                "timestamp": datetime.now().isoformat() + "Z",
            },
            "desired": {"temperature": 125.0, "mode": "ECO"},
        }

        # Run test asynchronously
        result = asyncio.run(self._async_create_shadow(initial_state))
        self.assertTrue(result, "Failed to create shadow document")

    async def _async_create_shadow(self, initial_state):
        """Async helper for shadow creation test."""
        try:
            # Create shadow document
            await self.shadow_service.create_device_shadow(
                self.test_device_id, initial_state
            )

            # Verify shadow exists
            exists = await self.mongo_storage.shadow_exists(self.test_device_id)
            self.assertTrue(exists, "Shadow document not found in MongoDB")

            # Retrieve shadow and verify contents
            shadow = await self.mongo_storage.get_shadow(self.test_device_id)
            self.assertEqual(shadow["device_id"], self.test_device_id)
            self.assertEqual(shadow["reported"]["temperature"], 120.5)

            logger.info("Successfully created and verified shadow document")
            return True
        except Exception as e:
            logger.error(f"Error in shadow creation test: {e}")
            return False

    def test_03_generate_history_data(self):
        """Test generating and storing history data."""
        # Generate history data
        history_result = asyncio.run(self._async_generate_history())
        self.assertTrue(history_result, "Failed to generate history data")

    async def _async_generate_history(self):
        """Async helper for history generation test."""
        try:
            # Create historical data points
            history_entries = []
            base_temp = 120.0
            base_pressure = 60.0
            base_flow = 3.2
            base_energy = 450.0

            # Generate data for the past 7 days
            current_time = datetime.now()

            # Create 24 points per day (every hour) for 7 days
            for day in range(7):
                for hour in range(24):
                    # Go back in time
                    point_time = current_time - timedelta(days=day, hours=hour)

                    # Add some variation to values
                    temp_variation = ((day * 24 + hour) % 10) - 5  # -5 to +5
                    pressure_variation = ((day * 24 + hour) % 8) / 10  # -0.4 to +0.4
                    flow_variation = ((day * 24 + hour) % 12) / 10  # -0.6 to +0.6
                    energy_variation = ((day * 24 + hour) % 200) - 100  # -100 to +100

                    # Create data point with timestamp
                    entry = {
                        "temperature": base_temp + temp_variation,
                        "pressure": base_pressure + pressure_variation,
                        "flow_rate": base_flow + flow_variation,
                        "energy_usage": base_energy + energy_variation,
                        "timestamp": point_time.isoformat() + "Z",
                    }

                    history_entries.append(entry)

            # Add history to shadow document
            await self.shadow_service.update_device_shadow_history(
                self.test_device_id, history_entries
            )

            # Verify history was added
            shadow = await self.mongo_storage.get_shadow(self.test_device_id)
            self.assertIn("history", shadow, "History field missing from shadow")
            self.assertEqual(
                len(shadow["history"]),
                len(history_entries),
                "History entry count mismatch",
            )

            logger.info(f"Added {len(history_entries)} history entries to shadow")
            return True
        except Exception as e:
            logger.error(f"Error in history generation test: {e}")
            return False

    def test_04_api_shadow_retrieval(self):
        """Test retrieving shadow document through API."""
        from fastapi.testclient import TestClient

        from src.api.routes import app
        from src.api.routes.shadow_document_api import get_device_shadow

        client = TestClient(app)

        # Test getting shadow document via API
        response = client.get(f"/api/shadows/{self.test_device_id}")
        self.assertEqual(
            response.status_code, 200, f"API returned status {response.status_code}"
        )

        shadow_data = response.json()
        self.assertEqual(
            shadow_data["device_id"],
            self.test_device_id,
            "Device ID mismatch in API response",
        )
        self.assertIn(
            "reported", shadow_data, "Reported state missing from API response"
        )
        self.assertIn(
            "temperature",
            shadow_data["reported"],
            "Temperature missing from reported state",
        )

        # Check if history is returned
        self.assertIn("history", shadow_data, "History missing from API response")
        self.assertTrue(
            len(shadow_data["history"]) > 0, "History is empty in API response"
        )

        logger.info("Successfully verified shadow API retrieval")

    def test_05_history_api_retrieval(self):
        """Test retrieving history data through the history API."""
        from fastapi.testclient import TestClient

        from src.api.routes import app

        client = TestClient(app)

        # Test getting history via the manufacturer API
        response = client.get(
            f"/api/manufacturer/water-heaters/{self.test_device_id}/history?days=7"
        )
        self.assertEqual(
            response.status_code,
            200,
            f"History API returned status {response.status_code}",
        )

        history_data = response.json()
        self.assertIn(
            "temperature", history_data, "Temperature history missing from API response"
        )
        self.assertTrue(
            len(history_data["temperature"]) > 0,
            "Temperature history is empty in API response",
        )

        # Check for other metrics
        self.assertIn(
            "pressure", history_data, "Pressure history missing from API response"
        )
        self.assertIn(
            "flow_rate", history_data, "Flow rate history missing from API response"
        )
        self.assertIn(
            "energy_usage",
            history_data,
            "Energy usage history missing from API response",
        )

        logger.info("Successfully verified history API retrieval")

    def test_06_shadow_performance(self):
        """Test shadow document performance with large history datasets."""
        # Generate a large history dataset and measure retrieval performance
        perf_result = asyncio.run(self._async_performance_test())
        self.assertTrue(perf_result, "Performance test failed")

    async def _async_performance_test(self):
        """Async helper for performance test."""
        try:
            import time

            # Generate a large history dataset (1000 entries)
            history_entries = []
            base_temp = 120.0

            for i in range(1000):
                point_time = datetime.now() - timedelta(hours=i)
                entry = {
                    "temperature": base_temp + (i % 20) - 10,
                    "timestamp": point_time.isoformat() + "Z",
                }
                history_entries.append(entry)

            # Measure write performance
            start_time = time.time()
            await self.shadow_service.update_device_shadow_history(
                self.test_device_id, history_entries
            )
            write_time = time.time() - start_time

            # Measure read performance
            start_time = time.time()
            shadow = await self.mongo_storage.get_shadow(self.test_device_id)
            read_time = time.time() - start_time

            logger.info(f"Write performance: {write_time:.4f}s for 1000 entries")
            logger.info(f"Read performance: {read_time:.4f}s for 1000 entries")

            # Ensure performance is acceptable (adjust thresholds as needed)
            self.assertLess(write_time, 5.0, "Write performance too slow")
            self.assertLess(read_time, 1.0, "Read performance too slow")

            return True
        except Exception as e:
            logger.error(f"Error in performance test: {e}")
            return False


def run_tests():
    """Run the test suite."""
    unittest.main(verbosity=2)


if __name__ == "__main__":
    run_tests()
