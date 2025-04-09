#!/usr/bin/env python3
"""
Comprehensive end-to-end test for IoTSphere

This script tests:
1. Duplication issue on water heater list page
2. Temperature history population on details page
3. Navigation between list and details pages

Following TDD principles:
- Each test verifies a specific behavior
- Actual results are compared to expected results
- Detailed logging of all steps and findings
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from urllib.parse import urljoin

import aiohttp
import pymongo
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("e2e_test")

# Test configuration
BASE_URL = "http://localhost:8000"
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "iotsphere"


class IoTSphereE2ETest:
    """End-to-end test for IoTSphere"""

    def __init__(self):
        self.session = None
        self.mongo_client = None
        self.device_ids = []
        self.test_results = {
            "list_page": {
                "status": "Not Run",
                "details": "",
                "duplication_found": False,
            },
            "details_page": {
                "status": "Not Run",
                "details": "",
                "temperature_history_found": False,
            },
            "navigation": {"status": "Not Run", "details": ""},
        }

    async def setup(self):
        """Setup test environment"""
        logger.info("Setting up test environment")
        self.session = aiohttp.ClientSession()
        try:
            # Connect to MongoDB
            self.mongo_client = pymongo.MongoClient(MONGO_URI)
            db = self.mongo_client[MONGO_DB]
            # Get list of device IDs
            devices = list(db.shadows.find({}, {"device_id": 1}))
            self.device_ids = [d["device_id"] for d in devices if "device_id" in d]
            logger.info(
                f"Found {len(self.device_ids)} devices in MongoDB: {self.device_ids}"
            )
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            self.mongo_client = None

    async def teardown(self):
        """Teardown test environment"""
        logger.info("Tearing down test environment")
        if self.session:
            await self.session.close()
        if self.mongo_client:
            self.mongo_client.close()

    async def test_list_page(self):
        """Test water heater list page for duplication"""
        logger.info("Testing water heater list page")
        self.test_results["list_page"]["status"] = "Running"

        try:
            # Get the list page
            async with self.session.get(
                urljoin(BASE_URL, "/water-heaters")
            ) as response:
                if response.status != 200:
                    self.test_results["list_page"]["status"] = "Failed"
                    self.test_results["list_page"][
                        "details"
                    ] = f"Error accessing list page: {response.status}"
                    return

                # Parse HTML content
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                # Look for water heater cards
                water_heater_cards = soup.select(
                    '.water-heater-card, .card, [id^="heater-"]'
                )

                # Extract device IDs from cards
                device_ids = []
                device_id_elements = []

                for card in water_heater_cards:
                    # Try to extract device ID from various elements
                    device_id = None

                    # Check for data-id attribute
                    if card.has_attr("data-id"):
                        device_id = card["data-id"]
                    # Check for id attribute starting with heater-
                    elif card.has_attr("id") and card["id"].startswith("heater-"):
                        device_id = card["id"][7:]  # Remove 'heater-' prefix
                    # Check for device-id element
                    else:
                        id_elem = card.select_one(".device-id")
                        if id_elem:
                            device_id = id_elem.get_text().strip()

                    if device_id:
                        device_ids.append(device_id)
                        device_id_elements.append((device_id, card))

                # Check for duplicates
                duplicate_ids = []
                seen = set()
                for device_id in device_ids:
                    if device_id in seen:
                        duplicate_ids.append(device_id)
                    else:
                        seen.add(device_id)

                # Log results
                logger.info(
                    f"Found {len(water_heater_cards)} water heater cards on page"
                )
                logger.info(f"Extracted {len(device_ids)} device IDs from cards")
                logger.info(f"Unique device IDs: {len(seen)}")

                if duplicate_ids:
                    logger.error(
                        f"Found {len(duplicate_ids)} duplicate device IDs: {duplicate_ids}"
                    )
                    self.test_results["list_page"]["status"] = "Failed"
                    self.test_results["list_page"][
                        "details"
                    ] = f"Duplicates found: {duplicate_ids}"
                    self.test_results["list_page"]["duplication_found"] = True
                else:
                    logger.info("No duplicates found on list page")
                    self.test_results["list_page"]["status"] = "Passed"
                    self.test_results["list_page"][
                        "details"
                    ] = f"Verified {len(device_ids)} unique water heaters"

                # Store device IDs for later tests
                self.device_ids = list(seen)

        except Exception as e:
            logger.error(f"Error testing list page: {e}")
            import traceback

            logger.error(traceback.format_exc())
            self.test_results["list_page"]["status"] = "Error"
            self.test_results["list_page"]["details"] = f"Exception: {str(e)}"

    async def test_details_page(self):
        """Test temperature history on details page"""
        logger.info("Testing temperature history on details page")
        self.test_results["details_page"]["status"] = "Running"

        if not self.device_ids:
            if self.mongo_client:
                # Get device IDs from MongoDB if list page test failed
                db = self.mongo_client[MONGO_DB]
                devices = list(db.shadows.find({}, {"device_id": 1}))
                self.device_ids = [d["device_id"] for d in devices if "device_id" in d]

            if not self.device_ids:
                # Fallback to default device IDs
                self.device_ids = ["wh-001", "wh-002", "wh-e0ae2f58"]

        for device_id in self.device_ids[:1]:  # Test only first device to save time
            logger.info(f"Testing details page for device {device_id}")

            try:
                # Get the details page
                details_url = urljoin(BASE_URL, f"/water-heaters/{device_id}")
                async with self.session.get(details_url) as response:
                    if response.status != 200:
                        self.test_results["details_page"]["status"] = "Failed"
                        self.test_results["details_page"][
                            "details"
                        ] = f"Error accessing details page for {device_id}: {response.status}"
                        continue

                    # Parse HTML content
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    # Check if page has device ID
                    device_header = soup.select_one("h1, .device-header")
                    if not device_header or device_id not in device_header.get_text():
                        logger.warning(
                            f"Details page for {device_id} doesn't contain device ID in header"
                        )

                    # Look for temperature history chart containers
                    temp_chart_containers = soup.select(
                        ".temperature-history-container, .temp-history-container, #temperatureHistoryChart, .temperature-chart"
                    )

                    if not temp_chart_containers:
                        logger.error(
                            f"No temperature history chart container found for {device_id}"
                        )
                        self.test_results["details_page"]["status"] = "Failed"
                        self.test_results["details_page"][
                            "details"
                        ] = f"No temperature history chart container found for {device_id}"
                        continue

                    logger.info(
                        f"Found {len(temp_chart_containers)} temperature history chart containers"
                    )

                    # Check for loading indicators or canvas elements
                    has_loading = any(
                        container.select(".loading")
                        for container in temp_chart_containers
                    )
                    has_canvas = any(
                        container.select("canvas")
                        for container in temp_chart_containers
                    )
                    has_error = any(
                        container.select(
                            ".error-message, .chart-error, .no-data-message"
                        )
                        for container in temp_chart_containers
                    )

                    logger.info(
                        f"Chart status: loading={has_loading}, canvas={has_canvas}, error={has_error}"
                    )

                    if has_canvas:
                        logger.info(
                            f"Temperature history chart is displayed for {device_id}"
                        )
                        self.test_results["details_page"]["status"] = "Passed"
                        self.test_results["details_page"][
                            "details"
                        ] = f"Temperature history chart found for {device_id}"
                        self.test_results["details_page"][
                            "temperature_history_found"
                        ] = True
                    elif has_error:
                        logger.error(
                            f"Temperature history chart shows error for {device_id}"
                        )
                        self.test_results["details_page"]["status"] = "Failed"
                        self.test_results["details_page"][
                            "details"
                        ] = f"Temperature history chart shows error for {device_id}"
                    elif has_loading:
                        logger.warning(
                            f"Temperature history chart is still loading for {device_id}"
                        )
                        self.test_results["details_page"]["status"] = "Inconclusive"
                        self.test_results["details_page"][
                            "details"
                        ] = f"Temperature history chart is loading for {device_id}"
                    else:
                        logger.error(
                            f"Temperature history chart status unclear for {device_id}"
                        )
                        self.test_results["details_page"]["status"] = "Failed"
                        self.test_results["details_page"][
                            "details"
                        ] = f"Temperature history chart status unclear for {device_id}"

            except Exception as e:
                logger.error(f"Error testing details page for {device_id}: {e}")
                import traceback

                logger.error(traceback.format_exc())
                self.test_results["details_page"]["status"] = "Error"
                self.test_results["details_page"]["details"] = f"Exception: {str(e)}"

    async def test_api_temperature_history(self):
        """Test the temperature history API"""
        logger.info("Testing temperature history API")

        if not self.device_ids:
            if self.mongo_client:
                # Get device IDs from MongoDB
                db = self.mongo_client[MONGO_DB]
                devices = list(db.shadows.find({}, {"device_id": 1}))
                self.device_ids = [d["device_id"] for d in devices if "device_id" in d]

            if not self.device_ids:
                # Fallback to default device IDs
                self.device_ids = ["wh-001", "wh-002", "wh-e0ae2f58"]

        for device_id in self.device_ids[:1]:  # Test only first device
            logger.info(f"Testing temperature history API for device {device_id}")

            try:
                # Test standard history endpoint
                history_url = urljoin(
                    BASE_URL, f"/api/device-shadows/{device_id}/history"
                )
                async with self.session.get(history_url) as response:
                    status = response.status
                    if status == 200:
                        data = await response.json()
                        logger.info(
                            f"Standard history API returned {len(data)} entries"
                        )
                        if len(data) > 0:
                            logger.info(
                                f"Sample entry: {json.dumps(data[0], indent=2)}"
                            )
                    else:
                        logger.warning(f"Standard history API failed: {status}")

                # Test time series endpoint
                timeseries_url = urljoin(
                    BASE_URL, f"/api/device-shadows/{device_id}/time-series?limit=100"
                )
                async with self.session.get(timeseries_url) as response:
                    status = response.status
                    if status == 200:
                        data = await response.json()
                        logger.info(f"Time series API returned {len(data)} entries")
                        if len(data) > 0:
                            logger.info(
                                f"Sample entry: {json.dumps(data[0], indent=2)}"
                            )
                    else:
                        logger.warning(f"Time series API failed: {status}")

                # Test shadow document
                shadow_url = urljoin(BASE_URL, f"/api/device-shadows/{device_id}")
                async with self.session.get(shadow_url) as response:
                    status = response.status
                    if status == 200:
                        data = await response.json()
                        has_history = "history" in data and isinstance(
                            data["history"], list
                        )
                        history_count = len(data.get("history", []))
                        logger.info(
                            f"Shadow API returned document with history: {has_history} (count: {history_count})"
                        )
                    else:
                        logger.warning(f"Shadow API failed: {status}")

            except Exception as e:
                logger.error(
                    f"Error testing temperature history API for {device_id}: {e}"
                )
                import traceback

                logger.error(traceback.format_exc())

    async def check_mongodb_data(self):
        """Check MongoDB for temperature history data"""
        logger.info("Checking MongoDB for temperature history data")

        if not self.mongo_client:
            logger.error("MongoDB client not available")
            return

        try:
            db = self.mongo_client[MONGO_DB]

            # Check shadows collection
            shadows_count = db.shadows.count_documents({})
            logger.info(f"Found {shadows_count} documents in shadows collection")

            # Check if shadows have history
            shadows_with_history = db.shadows.count_documents(
                {"history": {"$exists": True, "$ne": []}}
            )
            logger.info(f"Found {shadows_with_history} shadows with non-empty history")

            # Check optimized history collection if it exists
            if "shadow_history" in db.list_collection_names():
                history_count = db.shadow_history.count_documents({})
                logger.info(
                    f"Found {history_count} documents in shadow_history collection"
                )

                # Sample history entries
                for device_id in self.device_ids[:1]:
                    history_for_device = db.shadow_history.count_documents(
                        {"device_id": device_id}
                    )
                    logger.info(
                        f"Found {history_for_device} history entries for device {device_id}"
                    )

                    if history_for_device > 0:
                        sample = list(
                            db.shadow_history.find({"device_id": device_id})
                            .sort("timestamp", -1)
                            .limit(1)
                        )
                        if sample:
                            logger.info(
                                f"Sample history entry: {json.dumps(sample[0], default=str)}"
                            )

        except Exception as e:
            logger.error(f"Error checking MongoDB data: {e}")
            import traceback

            logger.error(traceback.format_exc())

    async def run_tests(self):
        """Run all tests"""
        logger.info("Starting end-to-end tests")

        try:
            await self.setup()

            # Test list page
            await self.test_list_page()

            # Test details page
            await self.test_details_page()

            # Test temperature history API
            await self.test_api_temperature_history()

            # Check MongoDB data
            await self.check_mongodb_data()

        finally:
            await self.teardown()

        # Print test results
        logger.info("\n" + "=" * 80)
        logger.info("TEST RESULTS:")
        logger.info("=" * 80)

        for test_name, results in self.test_results.items():
            status = results["status"]
            details = results["details"]
            logger.info(f"{test_name.upper()}: {status}")
            if details:
                logger.info(f"  Details: {details}")

        logger.info("=" * 80)

        # Determine overall pass/fail
        all_passed = all(
            results["status"] == "Passed" for results in self.test_results.values()
        )
        logger.info(f"OVERALL: {'PASSED' if all_passed else 'FAILED'}")

        return all_passed


async def main():
    """Main function"""
    test = IoTSphereE2ETest()
    success = await test.run_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
