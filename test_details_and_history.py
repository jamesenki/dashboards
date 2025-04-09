"""
Test Details Page and History Tab Separation

REQUIREMENTS:
1. Details page should NOT have temperature history chart or API calls for history
2. Details page should only show current shadow information
3. History tab should properly display temperature history chart
"""
import asyncio
import json
import logging
import os
import sys
import time
import unittest
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class DetailsAndHistoryTabTests(unittest.TestCase):
    """Test separation of concerns between details page and history tab"""

    BASE_URL = "http://localhost:8000"
    TEST_DEVICE_ID = "wh-001"  # Use a consistent test device

    @classmethod
    def setUpClass(cls):
        """Setup before all tests - verify server is running"""
        # List of URLs to try for health check
        test_urls = [
            cls.BASE_URL,  # Root URL
            f"{cls.BASE_URL}/water-heaters",  # Water heaters page
            f"{cls.BASE_URL}/api/manufacturer/water-heaters",  # API endpoint
        ]

        for url in test_urls:
            try:
                logger.info(f"Checking if server is running at {url}")
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    logger.info(f"✅ Server is running and responding at {url}")
                    return
                else:
                    logger.warning(f"Got status code {response.status_code} from {url}")
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ) as e:
                logger.warning(f"Could not connect to {url}: {str(e)}")
                continue

        # If we reach here, none of the URLs worked
        logger.error("❌ Failed to connect to server on any test URL")
        raise Exception(
            "Server not running, please start it with 'python start_with_guaranteed_history.py 8000'"
        )

        logger.info("✅ Server is running")

    def test_1_details_page_has_no_temperature_history_chart(self):
        """
        RED Phase:
        Details page should NOT have a temperature history chart
        """
        # Get the details page for our test device
        url = f"{self.BASE_URL}/water-heaters/{self.TEST_DEVICE_ID}"
        logger.info(f"Testing details page: {url}")

        response = requests.get(url)
        self.assertEqual(response.status_code, 200, "Failed to get details page")

        # Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the details content section
        details_content = soup.find(id="details-content")
        self.assertIsNotNone(details_content, "Details content section not found")

        # Check if there are any chart-container elements in the details content
        chart_containers = details_content.select(".chart-container")

        # We want simple temperature display, not charts in details section
        for container in chart_containers:
            # This container should not have a canvas element (which would indicate a chart)
            canvas = container.find("canvas")
            if canvas:
                self.fail(
                    f"Found canvas element in details page chart container: {container.get('id')}"
                )

        logger.info(
            "✅ Details page does not have temperature history chart with canvas"
        )

    def test_2_details_page_does_not_make_history_api_calls(self):
        """
        RED Phase:
        Details page JavaScript should not make API calls for history data
        """
        # Get the details page
        url = f"{self.BASE_URL}/water-heaters/{self.TEST_DEVICE_ID}"
        response = requests.get(url)
        self.assertEqual(response.status_code, 200, "Failed to get details page")

        # Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Analyze inline scripts for history API calls
        scripts = soup.find_all("script")
        for script in scripts:
            if script.string:  # Only check scripts with content
                script_content = script.string.lower()
                # Check for history API call patterns
                history_call_patterns = [
                    "/api/manufacturer/water-heaters/*/history",
                    "/api/device-shadows/*/history",
                    "get_temperature_history",
                    "fetchtemperaturehistory",
                ]

                for pattern in history_call_patterns:
                    if "*" in pattern:
                        # Handle wildcard pattern
                        parts = pattern.split("*")
                        if all(part in script_content for part in parts if part):
                            self.fail(
                                f"Found history API call pattern in details page script: {pattern}"
                            )
                    elif pattern.lower() in script_content:
                        self.fail(
                            f"Found history API call pattern in details page script: {pattern}"
                        )

        logger.info("✅ Details page scripts do not make history API calls")

    def test_3_details_page_shows_current_shadow_information(self):
        """
        GREEN Phase:
        Details page should display current shadow information
        """
        # Get the details page
        url = f"{self.BASE_URL}/water-heaters/{self.TEST_DEVICE_ID}"
        response = requests.get(url)
        self.assertEqual(response.status_code, 200, "Failed to get details page")

        # Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Check for current temperature display
        temperature_value = soup.select_one(".temperature-value")
        self.assertIsNotNone(temperature_value, "Current temperature value not found")

        # Check for status display
        status_value = soup.select_one(".device-status-value")
        self.assertIsNotNone(status_value, "Device status value not found")

        logger.info("✅ Details page shows current shadow information")

    def test_4_history_tab_has_temperature_chart(self):
        """
        GREEN Phase:
        History tab should have a temperature chart
        """
        # Get the device details page (which contains all tabs)
        url = f"{self.BASE_URL}/water-heaters/{self.TEST_DEVICE_ID}"
        response = requests.get(url)
        self.assertEqual(
            response.status_code, 200, "Failed to get details page with history tab"
        )

        # Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the history content section
        history_content = soup.find(id="history-content")
        self.assertIsNotNone(history_content, "History content section not found")

        # Find temperature chart container in history tab
        temp_chart = history_content.find(id="temperature-chart")
        self.assertIsNotNone(temp_chart, "Temperature chart not found in history tab")

        logger.info("✅ History tab has temperature chart")

    def test_5_history_api_endpoint_returns_valid_data(self):
        """
        GREEN Phase:
        History API endpoint should return valid data for the history tab
        """
        # Call the history API endpoint directly
        url = f"{self.BASE_URL}/api/manufacturer/water-heaters/{self.TEST_DEVICE_ID}/history"
        logger.info(f"Testing API endpoint: {url}")

        response = requests.get(url)
        self.assertEqual(
            response.status_code,
            200,
            f"History API returned status code {response.status_code}",
        )

        # Parse response
        data = response.json()

        # Log the full structure for debugging
        logger.info(f"API response keys: {list(data.keys())}")

        # Verify data structure (updated for new API format)
        self.assertIn("device_id", data, "Device ID not found in API response")
        self.assertEqual(
            data["device_id"],
            self.TEST_DEVICE_ID,
            "Device ID doesn't match expected value",
        )

        # Check if either the old format or new format is present
        has_old_format = "history" in data
        has_new_format = "temperature" in data and "datasets" in data["temperature"]

        if has_old_format:
            # Old format validation
            self.assertTrue(len(data["history"]) > 0, "History array is empty")
            first_entry = data["history"][0]
            self.assertIn(
                "timestamp", first_entry, "Timestamp not found in history entry"
            )
            self.assertIn("metrics", first_entry, "Metrics not found in history entry")
            self.assertIn(
                "temperature",
                first_entry["metrics"],
                "Temperature not found in metrics",
            )
            logger.info(
                f"✅ History API returned {len(data['history'])} valid history entries (old format)"
            )
        elif has_new_format:
            # New format validation - structured data with temperature datasets
            temperature_data = data["temperature"]
            self.assertIn("labels", temperature_data, "Temperature labels not found")
            self.assertIn(
                "datasets", temperature_data, "Temperature datasets not found"
            )
            self.assertTrue(
                len(temperature_data["datasets"]) > 0,
                "Temperature datasets array is empty",
            )
            self.assertTrue(
                len(temperature_data["labels"]) > 0, "Temperature labels array is empty"
            )

            # Verify the temperature dataset has data points
            first_dataset = temperature_data["datasets"][0]
            self.assertIn(
                "data", first_dataset, "Data points not found in temperature dataset"
            )
            self.assertTrue(
                len(first_dataset["data"]) > 0, "Temperature data points array is empty"
            )

            logger.info(
                f"✅ History API returned valid temperature history with {len(first_dataset['data'])} data points (new format)"
            )
        else:
            self.fail(
                "Neither old 'history' format nor new 'temperature.datasets' format found in API response"
            )

        return data

    def test_6_verify_browser_network_requests(self):
        """
        REFACTOR Phase:
        Print instructions for manual verification of browser network requests
        """
        # This is a special test that provides instructions for manual testing
        # since automated browser testing would require additional setup

        logger.info("\n⚠️ MANUAL VERIFICATION REQUIRED ⚠️")
        logger.info("Please manually verify network requests in the browser:")
        logger.info(f"1. Visit {self.BASE_URL}/water-heaters/{self.TEST_DEVICE_ID}")
        logger.info("2. Open browser developer tools (F12 or right-click > Inspect)")
        logger.info("3. Go to the Network tab")
        logger.info(
            "4. Verify that NO history API calls are made when viewing the details tab"
        )
        logger.info("5. Click on the History tab")
        logger.info(
            "6. Verify that history API calls ARE made when viewing the history tab"
        )
        logger.info("7. Verify the temperature chart appears in the history tab")

        # This test always passes, it's just for documentation
        self.assertTrue(True)


def run_tests():
    """Run all tests"""
    # Create test suite and run
    suite = unittest.TestLoader().loadTestsFromTestCase(DetailsAndHistoryTabTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)

    # Print summary
    logger.info("\n===== TEST SUMMARY =====")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")

    # Return True if all tests passed
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == "__main__":
    # Check if server is running
    # List of URLs to try for health check
    test_urls = [
        DetailsAndHistoryTabTests.BASE_URL,  # Root URL
        f"{DetailsAndHistoryTabTests.BASE_URL}/water-heaters",  # Water heaters page
        f"{DetailsAndHistoryTabTests.BASE_URL}/api/manufacturer/water-heaters",  # API endpoint
    ]

    server_running = False
    for url in test_urls:
        try:
            logger.info(f"Checking if server is running at {url}")
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                logger.info(f"✅ Server is running and responding at {url}")
                server_running = True
                break
            else:
                logger.warning(f"Got status code {response.status_code} from {url}")
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            logger.warning(f"Could not connect to {url}: {str(e)}")
            continue

    if not server_running:
        logger.error("❌ Failed to connect to server on any test URL")
        logger.error(
            "Please start the server with: python start_with_guaranteed_history.py 8000"
        )
        sys.exit(1)

    success = run_tests()
    if success:
        logger.info("✅ All tests passed!")
        sys.exit(0)
    else:
        logger.error("❌ Some tests failed!")
        sys.exit(1)
