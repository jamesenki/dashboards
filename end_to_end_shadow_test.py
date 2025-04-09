#!/usr/bin/env python3
"""
End-to-End Shadow Data Validation Test

This test script:
1. Validates device registration data
2. Validates Asset DB entries
3. Validates MongoDB shadow documents and their structure
4. Tests API endpoints for shadow data
5. Checks UI components for data consistency
6. Specifically validates temperature history data flow

IMPORTANT: This is a pure validation test - no changes to system files!
"""
import asyncio
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pprint import pformat
from urllib.parse import urljoin

import motor.motor_asyncio
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:7080"
MONGODB_URI = "mongodb://localhost:27017/"
MONGODB_DB = "iotsphere"
SHADOWS_COLLECTION = "device_shadows"


class EndToEndShadowTest:
    """End-to-End test for shadow data flow"""

    def __init__(self):
        self.mongodb_client = None
        self.water_heaters = []  # Data from API
        self.shadow_docs = []  # Data from MongoDB
        self.temp_history = {}  # Temperature history data
        self.issue_count = 0  # Count of issues found
        self.findings = []  # Findings to report

    def log_finding(self, category, message, critical=False):
        """Log a test finding"""
        prefix = "❌ CRITICAL: " if critical else "⚠️ WARNING: "
        full_message = f"{prefix} [{category}] {message}"
        self.findings.append(full_message)

        if critical:
            logger.error(full_message)
            self.issue_count += 1
        else:
            logger.warning(full_message)

    def log_pass(self, category, message):
        """Log a passing test"""
        full_message = f"✅ PASS: [{category}] {message}"
        self.findings.append(full_message)
        logger.info(full_message)

    def log_step(self, message):
        """Log a test step"""
        line = "=" * 80
        logger.info(f"\n{line}")
        logger.info(f"STEP: {message}")
        logger.info(line)

    async def test_water_heater_assets(self):
        """Test water heater assets through API"""
        self.log_step("Testing Water Heater Assets API")

        # Test manufacturer/water-heaters API
        api_url = urljoin(BASE_URL, "/api/manufacturer/water-heaters")

        try:
            response = requests.get(api_url)
            if response.status_code != 200:
                self.log_finding(
                    "ASSET_API",
                    f"Failed to access {api_url}: HTTP {response.status_code}",
                    critical=True,
                )
                return False

            water_heaters = response.json()
            logger.info(f"Found {len(water_heaters)} water heaters via API")

            # Store for later correlation
            self.water_heaters = water_heaters

            # Check ID field (API uses 'id' not 'device_id')
            if water_heaters and "id" in water_heaters[0]:
                logger.info(
                    f"Water heater IDs from API: {[wh['id'] for wh in water_heaters[:5]]}..."
                )
                self.log_pass(
                    "ASSET_API",
                    f"Successfully retrieved {len(water_heaters)} water heaters",
                )

                # Display sample data
                logger.info(
                    f"Sample water heater data:\n{json.dumps(water_heaters[0], indent=2)}"
                )

                # Look for temperature fields
                if "current_temperature" in water_heaters[0]:
                    self.log_pass("ASSET_API", "API includes current_temperature field")
                else:
                    self.log_finding(
                        "ASSET_API",
                        "API missing current_temperature field",
                        critical=False,
                    )

                return True
            else:
                self.log_finding(
                    "ASSET_API",
                    "API response missing expected 'id' field",
                    critical=True,
                )
                return False

        except Exception as e:
            self.log_finding(
                "ASSET_API",
                f"Error testing water heater assets: {str(e)}",
                critical=True,
            )
            return False

    async def test_mongodb_shadows(self):
        """Test MongoDB shadow documents"""
        self.log_step("Testing MongoDB Shadow Documents")

        try:
            # Connect to MongoDB
            client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
            self.mongodb_client = client

            # Check connection
            await client.server_info()
            self.log_pass("MONGODB", "Connected to MongoDB successfully")

            # Check database and collection
            db = client[MONGODB_DB]
            collections = await db.list_collection_names()

            if SHADOWS_COLLECTION not in collections:
                self.log_finding(
                    "MONGODB",
                    f"Shadow collection '{SHADOWS_COLLECTION}' not found",
                    critical=True,
                )
                return False

            # Count shadow documents
            collection = db[SHADOWS_COLLECTION]
            count = await collection.count_documents({})
            logger.info(f"Found {count} shadow documents in MongoDB")

            if count == 0:
                self.log_finding(
                    "MONGODB", "No shadow documents found in MongoDB", critical=True
                )
                return False

            # Get all shadow documents
            cursor = collection.find({})
            shadow_docs = await cursor.to_list(length=100)
            self.shadow_docs = shadow_docs

            # Check shadow document structure
            for doc in shadow_docs[:5]:  # Examine first 5 documents
                device_id = doc.get("device_id")
                if not device_id:
                    self.log_finding(
                        "MONGODB",
                        "Shadow document missing device_id field",
                        critical=True,
                    )
                    continue

                # Check for required fields
                required_fields = ["reported", "desired", "history"]
                missing_fields = [f for f in required_fields if f not in doc]

                if missing_fields:
                    self.log_finding(
                        "MONGODB",
                        f"Shadow for {device_id} missing required fields: {missing_fields}",
                        critical=True,
                    )
                else:
                    # Validate history data structure
                    history = doc.get("history", [])
                    if not history:
                        self.log_finding(
                            "MONGODB",
                            f"Shadow for {device_id} has empty history array",
                            critical=True,
                        )
                    else:
                        logger.info(
                            f"Shadow {device_id} has {len(history)} history entries"
                        )

                        # Check structure of first history entry
                        first_entry = history[0]
                        if "timestamp" not in first_entry:
                            self.log_finding(
                                "MONGODB",
                                f"History entry missing timestamp field",
                                critical=True,
                            )

                        # Check for temperature data location
                        if "temperature" in first_entry:
                            # Direct temperature field
                            self.log_pass(
                                "MONGODB",
                                f"History entries have direct temperature field",
                            )
                        elif (
                            "metrics" in first_entry
                            and "temperature" in first_entry["metrics"]
                        ):
                            # Temperature in metrics object
                            self.log_pass(
                                "MONGODB",
                                f"History entries have temperature in metrics.temperature",
                            )

                            # Extract and store temperature history for this device
                            temp_history = []
                            for entry in history:
                                timestamp = entry.get("timestamp")
                                temperature = entry.get("metrics", {}).get(
                                    "temperature"
                                )
                                if timestamp and temperature:
                                    temp_history.append(
                                        {
                                            "timestamp": timestamp,
                                            "temperature": temperature,
                                        }
                                    )

                            # Store for API comparison
                            if temp_history:
                                self.temp_history[device_id] = temp_history
                                logger.info(
                                    f"Extracted {len(temp_history)} temperature history entries for {device_id}"
                                )
                        else:
                            self.log_finding(
                                "MONGODB",
                                f"History entries missing temperature data",
                                critical=True,
                            )
                            logger.info(
                                f"Sample history entry structure: {json.dumps(first_entry, indent=2)}"
                            )

            self.log_pass("MONGODB", f"Found {count} valid shadow documents")
            return True

        except Exception as e:
            self.log_finding(
                "MONGODB", f"Error testing MongoDB shadows: {str(e)}", critical=True
            )
            return False
        finally:
            # Don't close client yet as we'll use it for comparison tests
            pass

    async def test_shadow_api(self):
        """Test shadow API endpoints"""
        self.log_step("Testing Shadow API Endpoints")

        # Get a sample device ID from either water heaters or shadow docs
        test_ids = []

        # Try to get IDs from water heaters first
        if self.water_heaters:
            test_ids = [wh.get("id") for wh in self.water_heaters[:3] if wh.get("id")]

        # If no IDs from water heaters, try shadow docs
        if not test_ids and self.shadow_docs:
            test_ids = [
                doc.get("device_id")
                for doc in self.shadow_docs[:3]
                if doc.get("device_id")
            ]

        # If still no IDs, use hardcoded values
        if not test_ids:
            test_ids = ["wh-001", "wh-002", "wh-e0ae2f58"]

        logger.info(f"Testing shadow API with device IDs: {test_ids}")

        # Test shadow API for each device ID
        for device_id in test_ids:
            # Try different potential API endpoints
            api_endpoints = [
                f"/api/device-shadows/{device_id}",
                f"/api/device-shadow/{device_id}",
                f"/api/manufacturer/water-heaters/{device_id}/shadow",
            ]

            found_shadow_api = False
            for endpoint in api_endpoints:
                api_url = urljoin(BASE_URL, endpoint)
                try:
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        found_shadow_api = True
                        shadow_data = response.json()

                        logger.info(f"Found working shadow API: {endpoint}")
                        self.log_pass(
                            "SHADOW_API",
                            f"Successfully retrieved shadow data for {device_id}",
                        )

                        # Check if API returns history
                        if "history" in shadow_data:
                            history = shadow_data["history"]
                            if history:
                                self.log_pass(
                                    "SHADOW_API",
                                    f"Shadow API returns {len(history)} history entries",
                                )

                                # Check history structure
                                first_entry = history[0]
                                logger.info(
                                    f"Sample history entry from API: {json.dumps(first_entry, indent=2)}"
                                )

                                # Check for temperature data
                                if "temperature" in first_entry:
                                    self.log_pass(
                                        "SHADOW_API",
                                        "API history includes direct temperature field",
                                    )
                                elif (
                                    "metrics" in first_entry
                                    and "temperature" in first_entry["metrics"]
                                ):
                                    self.log_pass(
                                        "SHADOW_API",
                                        "API history includes temperature in metrics.temperature",
                                    )
                                else:
                                    self.log_finding(
                                        "SHADOW_API",
                                        "API history missing temperature data",
                                        critical=True,
                                    )
                            else:
                                self.log_finding(
                                    "SHADOW_API",
                                    "Shadow API returns empty history array",
                                    critical=True,
                                )
                        else:
                            self.log_finding(
                                "SHADOW_API",
                                "Shadow API response missing history field",
                                critical=True,
                            )

                        break
                except Exception as e:
                    logger.warning(
                        f"Error testing shadow API endpoint {endpoint}: {str(e)}"
                    )
                    continue

            if not found_shadow_api:
                self.log_finding(
                    "SHADOW_API",
                    f"No working shadow API found for device {device_id}",
                    critical=True,
                )
                continue

            # Now test temperature history specific endpoint if available
            history_endpoints = [
                f"/api/device-shadows/{device_id}/temperature-history",
                f"/api/device-shadow/{device_id}/history",
                f"/api/manufacturer/water-heaters/{device_id}/temperature-history",
            ]

            found_history_api = False
            for endpoint in history_endpoints:
                api_url = urljoin(BASE_URL, endpoint)
                try:
                    response = requests.get(api_url)
                    if response.status_code == 200:
                        found_history_api = True
                        try:
                            history_data = response.json()

                            if isinstance(history_data, list) and history_data:
                                self.log_pass(
                                    "HISTORY_API",
                                    f"Temperature history API returns {len(history_data)} entries",
                                )

                                # Check for expected fields in history entries
                                first_entry = history_data[0]
                                logger.info(
                                    f"Sample history entry from API: {json.dumps(first_entry, indent=2)}"
                                )

                                if "timestamp" in first_entry and (
                                    "temperature" in first_entry
                                    or "value" in first_entry
                                ):
                                    self.log_pass(
                                        "HISTORY_API",
                                        "History entries have expected fields",
                                    )
                                else:
                                    expected_fields = ["timestamp", "temperature/value"]
                                    actual_fields = list(first_entry.keys())
                                    self.log_finding(
                                        "HISTORY_API",
                                        f"Unexpected history entry structure. Expected {expected_fields}, got {actual_fields}",
                                        critical=False,
                                    )
                            else:
                                self.log_finding(
                                    "HISTORY_API",
                                    "Temperature history API returns empty or invalid data",
                                    critical=True,
                                )
                        except json.JSONDecodeError:
                            self.log_finding(
                                "HISTORY_API",
                                "Temperature history API returns invalid JSON",
                                critical=True,
                            )

                        break
                except Exception as e:
                    logger.warning(
                        f"Error testing history API endpoint {endpoint}: {str(e)}"
                    )
                    continue

            if not found_history_api:
                self.log_finding(
                    "HISTORY_API",
                    f"No working temperature history API found for device {device_id}",
                    critical=True,
                )

    async def test_ui_components(self):
        """Test UI components for shadow data display"""
        self.log_step("Testing UI Components for Shadow Data")

        # Get a sample device ID from previous tests
        test_ids = []

        # Try to get IDs from water heaters first
        if self.water_heaters:
            test_ids = [wh.get("id") for wh in self.water_heaters[:3] if wh.get("id")]

        # If no IDs from water heaters, try shadow docs
        if not test_ids and self.shadow_docs:
            test_ids = [
                doc.get("device_id")
                for doc in self.shadow_docs[:3]
                if doc.get("device_id")
            ]

        # If still no IDs, use hardcoded values
        if not test_ids:
            test_ids = ["wh-001", "wh-002", "wh-e0ae2f58"]

        logger.info(f"Testing UI with device IDs: {test_ids}")

        # Test UI for each device ID
        for device_id in test_ids:
            detail_url = urljoin(BASE_URL, f"/water-heaters/{device_id}")
            try:
                response = requests.get(detail_url)
                if response.status_code != 200:
                    self.log_finding(
                        "UI",
                        f"Failed to load detail page for {device_id}: HTTP {response.status_code}",
                        critical=True,
                    )
                    continue

                # Parse HTML
                soup = BeautifulSoup(response.text, "html.parser")

                # Save HTML for reference
                with open(f"detail_page_{device_id}.html", "w") as f:
                    f.write(soup.prettify())

                logger.info(f"Saved detail page HTML to detail_page_{device_id}.html")

                # Look for temperature display
                temp_selectors = [
                    "#currentTemperature",
                    ".temperature-value",
                    ".current-temperature",
                    '[data-testid="temperature-display"]',
                ]

                temp_elem = None
                for selector in temp_selectors:
                    elem = soup.select_one(selector)
                    if elem:
                        temp_elem = elem
                        break

                if temp_elem:
                    temp_text = temp_elem.get_text(strip=True)
                    logger.info(f"Found temperature display: {temp_text}")
                    self.log_pass("UI", f"Detail page shows temperature: {temp_text}")
                else:
                    self.log_finding(
                        "UI",
                        f"Temperature display not found on detail page",
                        critical=True,
                    )

                # Look for temperature history chart
                chart_selectors = [
                    "#temperatureHistoryChart",
                    ".temperature-history-chart",
                    ".history-chart",
                    '[data-testid="temperature-history"]',
                ]

                chart_elem = None
                for selector in chart_selectors:
                    elem = soup.select_one(selector)
                    if elem:
                        chart_elem = elem
                        break

                if chart_elem:
                    logger.info(f"Found temperature history chart container")
                    self.log_pass(
                        "UI", "Detail page has temperature history chart container"
                    )

                    # Check if chart has canvas (visual rendering)
                    canvas = chart_elem.select_one("canvas")
                    if canvas:
                        self.log_pass(
                            "UI",
                            "Temperature history chart has canvas element (chart rendered)",
                        )
                    else:
                        # Check for error messages
                        error_elem = chart_elem.select_one(
                            ".error, .alert, .chart-error"
                        )
                        if error_elem:
                            error_text = error_elem.get_text(strip=True)
                            self.log_finding(
                                "UI",
                                f"Chart error message: {error_text}",
                                critical=True,
                            )
                        else:
                            self.log_finding(
                                "UI",
                                "Temperature history chart container exists but no canvas or error elements found",
                                critical=False,
                            )
                else:
                    self.log_finding(
                        "UI",
                        "Temperature history chart container not found on detail page",
                        critical=True,
                    )

                    # Look for error messages or placeholders
                    history_headers = soup.select("h2, h3, h4")
                    for header in history_headers:
                        text = header.get_text(strip=True).lower()
                        if "temperature" in text and (
                            "history" in text or "chart" in text
                        ):
                            if "unavailable" in text or "error" in text:
                                self.log_finding(
                                    "UI",
                                    f"Found history error message: {header.get_text(strip=True)}",
                                    critical=True,
                                )
                                break

            except Exception as e:
                self.log_finding(
                    "UI", f"Error testing UI for {device_id}: {str(e)}", critical=True
                )

    async def compare_data_sources(self):
        """Compare data between different sources"""
        self.log_step("Comparing Data Between Sources")

        if not self.water_heaters or not self.shadow_docs:
            self.log_finding(
                "COMPARISON",
                "Missing data from previous tests, cannot compare",
                critical=True,
            )
            return

        # Get IDs from both sources
        asset_ids = [wh.get("id") for wh in self.water_heaters if wh.get("id")]
        shadow_ids = [
            doc.get("device_id") for doc in self.shadow_docs if doc.get("device_id")
        ]

        # Check for missing shadow documents
        missing_shadows = set(asset_ids) - set(shadow_ids)
        if missing_shadows:
            self.log_finding(
                "COMPARISON",
                f"Assets without shadow documents: {list(missing_shadows)[:5]}",
                critical=True,
            )
        else:
            self.log_pass(
                "COMPARISON",
                "All water heater assets have corresponding shadow documents",
            )

        # Check for orphaned shadow documents
        orphaned_shadows = set(shadow_ids) - set(asset_ids)
        if orphaned_shadows:
            self.log_finding(
                "COMPARISON",
                f"Shadow documents without assets: {list(orphaned_shadows)[:5]}",
                critical=False,
            )

        # Compare temperature data
        for wh in self.water_heaters[:5]:  # Check first 5 water heaters
            device_id = wh.get("id")
            if not device_id:
                continue

            # Find matching shadow document
            shadow = next(
                (doc for doc in self.shadow_docs if doc.get("device_id") == device_id),
                None,
            )
            if not shadow:
                continue

            # Compare temperature values
            asset_temp = wh.get("current_temperature")
            shadow_temp = shadow.get("reported", {}).get("temperature")

            if asset_temp is not None and shadow_temp is not None:
                # Allow for minor differences due to rounding or timing
                if abs(float(asset_temp) - float(shadow_temp)) > 5:
                    self.log_finding(
                        "COMPARISON",
                        f"Temperature mismatch for {device_id}: Asset={asset_temp}, Shadow={shadow_temp}",
                        critical=False,
                    )
                else:
                    self.log_pass(
                        "COMPARISON", f"Temperature values consistent for {device_id}"
                    )

    async def run_tests(self):
        """Run all end-to-end tests"""
        start_time = time.time()

        logger.info("=" * 80)
        logger.info("STARTING END-TO-END SHADOW DATA VALIDATION TEST")
        logger.info(f"Server: {BASE_URL}")
        logger.info(f"MongoDB: {MONGODB_URI}")
        logger.info(f"Time: {datetime.now().isoformat()}")
        logger.info("=" * 80)

        try:
            # Test water heater assets
            await self.test_water_heater_assets()

            # Test MongoDB shadow documents
            await self.test_mongodb_shadows()

            # Test shadow API
            await self.test_shadow_api()

            # Test UI components
            await self.test_ui_components()

            # Compare data sources
            await self.compare_data_sources()

            # Print summary
            elapsed = time.time() - start_time

            logger.info("\n" + "=" * 80)
            logger.info(f"TEST SUMMARY (completed in {elapsed:.2f} seconds)")
            logger.info("=" * 80)

            # Count results
            passes = len([f for f in self.findings if f.startswith("✅")])
            critical = len([f for f in self.findings if "❌ CRITICAL" in f])
            warnings = len([f for f in self.findings if "⚠️ WARNING" in f])

            logger.info(f"PASSES: {passes}")
            logger.info(f"CRITICAL ISSUES: {critical}")
            logger.info(f"WARNINGS: {warnings}")
            logger.info("=" * 80)

            # Output key findings
            if self.findings:
                logger.info("\nKEY FINDINGS:")
                for finding in self.findings:
                    logger.info(f"  {finding}")

            # Provide recommendations based on findings
            self.provide_recommendations()

            return critical == 0

        except Exception as e:
            logger.error(f"Error running tests: {str(e)}")
            import traceback

            traceback.print_exc()
            return False
        finally:
            # Close MongoDB connection if open
            if self.mongodb_client:
                self.mongodb_client.close()

    def provide_recommendations(self):
        """Provide recommendations based on test findings"""
        logger.info("\n" + "=" * 80)
        logger.info("RECOMMENDATIONS")
        logger.info("=" * 80)

        # Check for specific issues
        missing_shadows = any(
            "Assets without shadow documents" in f for f in self.findings
        )
        empty_history = any("empty history array" in f for f in self.findings)
        history_structure = any(
            "History entries missing temperature" in f
            for f in self.findings
            or "History entries have temperature in metrics.temperature" in f
            for f in self.findings
        )
        ui_chart_missing = any(
            "Temperature history chart container not found" in f for f in self.findings
        )

        recommendations = []

        if missing_shadows:
            recommendations.append(
                "1. Create missing shadow documents for all water heaters:\n"
                "   - Develop a script to ensure each water heater has a shadow document\n"
                "   - Include initialization with empty history array"
            )

        if empty_history:
            recommendations.append(
                "2. Populate history data in shadow documents:\n"
                "   - Generate sample temperature history data points\n"
                "   - Ensure proper structure with timestamp and temperature fields"
            )

        if history_structure:
            recommendations.append(
                "3. Fix history data structure in shadow documents:\n"
                "   - History entries should have direct 'temperature' field, not nested in 'metrics'\n"
                "   - OR update UI code to handle 'metrics.temperature' structure"
            )

        if ui_chart_missing:
            recommendations.append(
                "4. Fix UI temperature history chart:\n"
                "   - Ensure chart container exists in detail page HTML\n"
                "   - Update JavaScript to properly fetch and display history data\n"
                "   - Handle data structure with temperature in metrics object if needed"
            )

        if not recommendations:
            logger.info("No specific issues identified requiring recommendations.")
        else:
            for recommendation in recommendations:
                logger.info(recommendation)
                logger.info("")


async def main():
    """Main function"""
    try:
        # Check if server is running
        try:
            response = requests.get(BASE_URL, timeout=2)
        except requests.ConnectionError:
            logger.error(f"Error: Cannot connect to {BASE_URL}")
            logger.error(
                "Make sure the IoTSphere server is running before running tests"
            )
            return 1

        # Run tests
        tester = EndToEndShadowTest()
        success = await tester.run_tests()

        return 0 if success else 1

    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        return 1


if __name__ == "__main__":
    # Install required packages if needed
    try:
        import bs4
        import motor
    except ImportError:
        print("Installing required packages...")
        os.system("pip install beautifulsoup4 motor requests")
        print("Packages installed, restarting script...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    sys.exit(asyncio.run(main()))
