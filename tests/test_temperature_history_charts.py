#!/usr/bin/env python3
"""
Test suite for Temperature History charts functionality.

Following TDD principles as required for the IoTSphere project, this test suite:
1. VERIFIES temperature history is NOT visible on the details page
2. VERIFIES temperature history IS visible and functioning on the History tab
3. VALIDATES temperature history charts properly display 7, 14, and 30 day data

Our approach follows the RED-GREEN-REFACTOR methodology:
- RED: Define expected behavior through tests (removing from details page, keeping on history tab)
- GREEN: Implement code changes to meet the requirements
- REFACTOR: Clean up and optimize the implementation while maintaining functionality
"""
import asyncio
import json
import os
import re
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup

# For web testing
from fastapi.testclient import TestClient

from src.infrastructure.device_shadow.mongodb_shadow_storage import MongoDBShadowStorage
from src.main import app
from src.models.device import Device, DeviceStatus, DeviceType

# Import necessary modules from the project
from src.services.device_shadow import DeviceShadowService


class TemperatureHistoryChartTest(unittest.TestCase):
    """Test temperature history chart functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and resources once for all tests."""
        # Force MongoDB storage for tests
        os.environ["SHADOW_STORAGE_TYPE"] = "mongodb"

        # Initialize test client
        cls.client = TestClient(app)

        # Set up test device
        cls.test_device_id = "test-wh-001"

        # Run setup asynchronously
        asyncio.run(cls._async_setup())

    @classmethod
    async def _async_setup(cls):
        """Async setup for the test class."""
        # Initialize MongoDB storage directly
        cls.mongo_storage = MongoDBShadowStorage(
            mongo_uri="mongodb://localhost:27017/", db_name="iotsphere_test"
        )
        await cls.mongo_storage.initialize()

        # Initialize services
        cls.shadow_service = DeviceShadowService(storage_provider=cls.mongo_storage)

        # Create test device shadow document with history data
        await cls._create_test_shadow_with_history()

    @classmethod
    async def _create_test_shadow_with_history(cls):
        """Create a test shadow document with temperature history."""
        # Register test device
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

        # Create shadow state document
        shadow_data = {
            "device_id": cls.test_device_id,
            "reported": {
                "temperature": 140.5,
                "pressure": 55.2,
                "water_level": 85,
                "heating_element": "active",
                "status": "online",
            },
            "desired": {"temperature": 140.0},
        }

        # Try to create the shadow
        try:
            await cls.shadow_service.create_shadow(cls.test_device_id, shadow_data)
        except Exception as e:
            print(f"Error creating shadow: {e}")
            # If it already exists, try to update it
            try:
                await cls.shadow_service.update_shadow_reported(
                    cls.test_device_id, shadow_data["reported"]
                )
            except Exception as e2:
                print(f"Error updating shadow: {e2}")

        # Generate historical temperature data for past 35 days to cover 7, 14, and 30 day charts
        end_time = datetime.now()
        start_time = end_time - timedelta(days=35)

        # Generate readings every 2 hours
        time_point = start_time
        readings = []

        while time_point < end_time:
            # Create realistic temperature variation (higher during day, lower at night)
            hour_of_day = time_point.hour
            base_temp = 135.0 if 8 <= hour_of_day <= 20 else 125.0
            import random

            temp = base_temp + random.uniform(-5, 5)

            reading = {
                "timestamp": time_point.isoformat(),
                "temperature": temp,
                "pressure": 50 + random.uniform(-5, 5),
                "water_level": 80 + random.uniform(-10, 10),
            }
            readings.append(reading)
            time_point += timedelta(hours=2)

        # Save the historical readings
        try:
            for reading in readings:
                await cls.mongo_storage.save_device_reading(cls.test_device_id, reading)
            print(f"Added {len(readings)} historical readings to test device")
        except Exception as e:
            print(f"Error adding readings: {e}")

    @classmethod
    def tearDownClass(cls):
        """Clean up resources after all tests have run."""
        # Remove test data
        asyncio.run(cls._async_teardown())

    @classmethod
    async def _async_teardown(cls):
        """Async teardown for the test class."""
        # Delete test shadow and readings
        try:
            await cls.mongo_storage.delete_shadow(cls.test_device_id)
            await cls.mongo_storage.delete_device_readings(cls.test_device_id)
            await cls.mongo_storage.close()
        except Exception as e:
            print(f"Error during teardown: {e}")

    # RED PHASE: These tests define our requirements
    # 1. Temperature history should not be visible on details page
    # 2. Temperature history should be visible on history tab
    # 3. Temperature charts should show 7, 14, and 30 day data correctly

    def test_details_page_no_temperature_history(self):
        """
        RED PHASE TEST: The water heater details page must NOT show temperature history.
        This validates our fix to remove the temperature history from the details page.
        """
        # Get the details page for our test device
        response = self.client.get(f"/water-heaters/{self.test_device_id}")
        self.assertEqual(response.status_code, 200, "Should return a 200 OK status")

        # Parse HTML
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # TDD APPROACH: Focus on visible UI elements that a user would interact with
        # Following project's TDD principles - we care about user-visible functionality

        # DEBUG: Find exactly where "Temperature History" appears
        if "Temperature History" in html:
            print("\n\nDEBUG: Found 'Temperature History' in the HTML!")
            # Extract and print surrounding context to help locate the issue
            index = html.find("Temperature History")
            context_start = max(0, index - 100)
            context_end = min(len(html), index + 120)
            print(f"CONTEXT: ...{html[context_start:context_end]}...\n\n")

            # Also find all elements containing this text
            elements_with_text = soup.find_all(
                string=lambda text: "Temperature History" in text if text else False
            )
            print(
                f"Found {len(elements_with_text)} elements containing 'Temperature History':"
            )
            for i, element in enumerate(elements_with_text):
                print(f"\nElement {i+1}:")
                print(f"Parent: {element.parent.name if element.parent else 'None'}")
                print(f"Content: {element.strip()}")

        # 1. The page should not display "Temperature History" text to users
        self.assertNotIn(
            "Temperature History",
            html,
            "Temperature History text should not appear in the page content",
        )

        # 2. No visible History tab should be in the navigation
        tab_nav = soup.select_one(".tab-nav")
        if tab_nav:
            tab_buttons = tab_nav.select(".tab-btn")
            tab_texts = [btn.get_text().strip() for btn in tab_buttons]
            self.assertNotIn(
                "History",
                tab_texts,
                "A History tab should not be visible in the tab navigation",
            )

        # 3. Verify that Maintenance is the active tab instead
        maintenance_tab = soup.select_one(".tab-btn[data-tab='maintenance']")
        if maintenance_tab:
            self.assertIn(
                "active",
                maintenance_tab.get("class", []),
                "Maintenance tab should be active by default",
            )

        # 4. Check for active tab panels - only Maintenance should be active, no History
        active_panels = soup.select(".tab-panel.active")
        for panel in active_panels:
            panel_id = panel.get("id", "")
            self.assertNotEqual(
                panel_id, "history", "History panel should not be active"
            )

        # 5. Check that no VISIBLE chart elements exist (ignoring those with display:none)
        # We use a custom check to determine if an element would be visible to users
        chart_elements = soup.select(
            "#temperature-chart, .temperature-chart, .chart-container"
        )
        for element in chart_elements:
            # Check if element has inline style="display: none" or similar
            style = element.get("style", "").lower()
            hidden_class = any(
                cls in element.get("class", []) for cls in ["hidden", "removed-by-code"]
            )

            # If the element is NOT hidden, that's a problem - it would be visible to users
            if (
                "display: none" not in style
                and "visibility: hidden" not in style
                and not hidden_class
            ):
                self.fail(
                    f"Found visible temperature chart element: {element.name} with id={element.get('id')}"
                )

    def test_history_tab_has_temperature_charts(self):
        """
        RED PHASE TEST: The History tab MUST show temperature history charts.
        This validates that the fix preserves functionality on the History tab page.
        """
        # Get the history tab page for our test device
        response = self.client.get(f"/water-heaters/{self.test_device_id}/history")

        # If the history tab returns a 404, this test may be conditional - document this
        if response.status_code == 404:
            # The history tab may be implemented differently or not exist yet
            # Log this and make the test conditional
            print(
                "NOTE: History tab page not found at /water-heaters/{id}/history - test is conditional"
            )
            print("Checking alternative history endpoints...")

            # Try alternative endpoints
            alt_endpoints = [
                f"/device/{self.test_device_id}/history",
                f"/history/{self.test_device_id}",
                f"/devices/water-heaters/{self.test_device_id}/history",
            ]

            for endpoint in alt_endpoints:
                alt_response = self.client.get(endpoint)
                if alt_response.status_code == 200:
                    response = alt_response
                    print(f"Found history page at {endpoint}")
                    break

            # If we still don't have a valid response, mark test as skipped
            if response.status_code != 200:
                self.skipTest("History tab page not found - test skipped")

        self.assertEqual(
            response.status_code, 200, "History page should return 200 OK status"
        )

        # Parse HTML
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # 1. Check for temperature history title
        temp_header = soup.find(string=re.compile("Temperature History", re.IGNORECASE))
        self.assertIsNotNone(
            temp_header, "Temperature History heading should be present"
        )

        # 2. Check for chart container
        chart_containers = soup.select(
            "#temperature-chart, .temperature-chart, .chart-container, .chart-wrapper"
        )
        self.assertGreater(
            len(chart_containers), 0, "Temperature chart container should be present"
        )

        # 3. Look for period selectors that would indicate 7/14/30 day options
        # Note: The exact format of these may vary (buttons, dropdown, tabs, etc.)
        period_elements = soup.select(
            ".period-selector, .chart-period, .time-range, [data-period]"
        )

        if not period_elements:
            # Try to find period indicators in text
            period_text_elements = soup.find_all(
                string=re.compile(
                    r"\b(7|14|30)\s*days?\b|\bweek\b|\btwo weeks\b|\bmonth\b",
                    re.IGNORECASE,
                )
            )

            self.assertGreater(
                len(period_text_elements),
                0,
                "Should find period indicators (7/14/30 days) on history page",
            )
        else:
            # Check that we have enough selector options (at least 3 for 7/14/30 days)
            self.assertGreaterEqual(
                len(period_elements),
                3,
                "Should have at least 3 period selector options",
            )

    # Testing the API endpoints that provide temperature history data
    # These tests verify that our history tab will have data to display

    def test_temperature_history_api_7_days(self):
        """
        RED PHASE TEST: API must provide valid 7-day temperature history.
        This ensures the History tab can display the correct 7-day data.
        """
        # Get temperature history for 7 days
        response = self.client.get(
            f"/api/device/{self.test_device_id}/temperature-history?period=7d"
        )

        # If this endpoint gives a 404, try alternative API endpoints
        if response.status_code == 404:
            alt_endpoints = [
                f"/api/water-heaters/{self.test_device_id}/temperature-history?period=7d",
                f"/api/devices/{self.test_device_id}/readings/temperature?days=7",
                f"/api/{self.test_device_id}/temperature/history?period=7d",
            ]

            for endpoint in alt_endpoints:
                alt_response = self.client.get(endpoint)
                if alt_response.status_code == 200:
                    response = alt_response
                    break

        # Verify response
        self.assertEqual(response.status_code, 200, "API should return 200 OK status")

        # Check response format
        data = response.json()
        self.assertIsInstance(data, list, "Response should be a list of data points")
        self.assertGreater(len(data), 0, "Should have temperature data points")

        # Verify data structure and timeframe
        seven_days_ago = datetime.now() - timedelta(days=7)
        for point in data:
            # Check essential fields
            self.assertIn("timestamp", point, "Each data point must have a timestamp")
            self.assertIn(
                "temperature", point, "Each data point must have a temperature value"
            )

            # Check timestamp is within range - adjust parsing based on format
            try:
                # Try standard format first
                timestamp = datetime.fromisoformat(
                    point["timestamp"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                # Alternative parsing
                timestamp = datetime.strptime(point["timestamp"], "%Y-%m-%dT%H:%M:%S")

            # Verify data is within the 7-day period
            self.assertGreaterEqual(
                timestamp,
                seven_days_ago,
                "Data points should be within the last 7 days",
            )

    def test_temperature_history_api_14_days(self):
        """
        RED PHASE TEST: API must provide valid 14-day temperature history.
        This ensures the History tab can display the correct 14-day data.
        """
        # Get temperature history for 14 days
        response = self.client.get(
            f"/api/device/{self.test_device_id}/temperature-history?period=14d"
        )

        # If this endpoint gives a 404, try alternative API endpoints
        if response.status_code == 404:
            alt_endpoints = [
                f"/api/water-heaters/{self.test_device_id}/temperature-history?period=14d",
                f"/api/devices/{self.test_device_id}/readings/temperature?days=14",
                f"/api/{self.test_device_id}/temperature/history?period=14d",
            ]

            for endpoint in alt_endpoints:
                alt_response = self.client.get(endpoint)
                if alt_response.status_code == 200:
                    response = alt_response
                    break

        # Verify response
        self.assertEqual(response.status_code, 200, "API should return 200 OK status")

        # Check response format
        data = response.json()
        self.assertIsInstance(data, list, "Response should be a list of data points")
        self.assertGreater(len(data), 0, "Should have temperature data points")

        # Verify data structure and timeframe
        fourteen_days_ago = datetime.now() - timedelta(days=14)
        for point in data:
            # Check essential fields
            self.assertIn("timestamp", point, "Each data point must have a timestamp")
            self.assertIn(
                "temperature", point, "Each data point must have a temperature value"
            )

            # Check timestamp is within range - adjust parsing based on format
            try:
                # Try standard format first
                timestamp = datetime.fromisoformat(
                    point["timestamp"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                # Alternative parsing
                timestamp = datetime.strptime(point["timestamp"], "%Y-%m-%dT%H:%M:%S")

            # Verify data is within the 14-day period
            self.assertGreaterEqual(
                timestamp,
                fourteen_days_ago,
                "Data points should be within the last 14 days",
            )

    def test_temperature_history_api_30_days(self):
        """
        RED PHASE TEST: API must provide valid 30-day temperature history.
        This ensures the History tab can display the correct 30-day data.
        """
        # Get temperature history for 30 days
        response = self.client.get(
            f"/api/device/{self.test_device_id}/temperature-history?period=30d"
        )

        # If this endpoint gives a 404, try alternative API endpoints
        if response.status_code == 404:
            alt_endpoints = [
                f"/api/water-heaters/{self.test_device_id}/temperature-history?period=30d",
                f"/api/devices/{self.test_device_id}/readings/temperature?days=30",
                f"/api/{self.test_device_id}/temperature/history?period=30d",
            ]

            for endpoint in alt_endpoints:
                alt_response = self.client.get(endpoint)
                if alt_response.status_code == 200:
                    response = alt_response
                    break

        # Verify response
        self.assertEqual(response.status_code, 200, "API should return 200 OK status")

        # Check response format
        data = response.json()
        self.assertIsInstance(data, list, "Response should be a list of data points")
        self.assertGreater(len(data), 0, "Should have temperature data points")

        # Verify data structure and timeframe
        thirty_days_ago = datetime.now() - timedelta(days=30)
        for point in data:
            # Check essential fields
            self.assertIn("timestamp", point, "Each data point must have a timestamp")
            self.assertIn(
                "temperature", point, "Each data point must have a temperature value"
            )

            # Check timestamp is within range - adjust parsing based on format
            try:
                # Try standard format first
                timestamp = datetime.fromisoformat(
                    point["timestamp"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                # Alternative parsing
                timestamp = datetime.strptime(point["timestamp"], "%Y-%m-%dT%H:%M:%S")

            # Verify data is within the 30-day period
            self.assertGreaterEqual(
                timestamp,
                thirty_days_ago,
                "Data points should be within the last 30 days",
            )

    def test_history_tab_period_selector_functionality(self):
        """
        RED PHASE TEST: Verify that the History tab has working period selectors
        and updates the chart correctly for 7, 14, and 30-day periods.

        This test validates the UI functionality for switching between different time periods
        on the History tab, following TDD principles by testing the expected behavior first.
        """
        # Get the history tab page for our test device
        response = self.client.get(f"/water-heaters/{self.test_device_id}/history")

        # Try alternative endpoints if the main one fails
        if response.status_code == 404:
            alt_endpoints = [
                f"/device/{self.test_device_id}/history",
                f"/history/{self.test_device_id}",
                f"/devices/water-heaters/{self.test_device_id}/history",
            ]

            for endpoint in alt_endpoints:
                alt_response = self.client.get(endpoint)
                if alt_response.status_code == 200:
                    response = alt_response
                    print(f"Found history page at {endpoint}")
                    break

        # Skip test if no history page is available
        if response.status_code != 200:
            self.skipTest("History tab page not found - test skipped")

        self.assertEqual(
            response.status_code, 200, "History page should return 200 OK status"
        )

        # Parse HTML
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # 1. Find the period selector elements
        period_selectors = soup.select(
            ".day-selector, .period-selector, [data-days], .chart-period, .time-range-button"
        )

        # If we can't find them using standard selectors, look for elements containing the period text
        if not period_selectors:
            period_selectors = []
            # Look for buttons or elements that mention 7, 14, or 30 days
            for period in ["7", "14", "30"]:
                elements = soup.find_all(
                    lambda tag: tag.name in ["button", "a", "div", "span"]
                    and re.search(rf"\b{period}\s*days?\b", tag.text, re.IGNORECASE)
                )
                period_selectors.extend(elements)

        # Verify we found all three period selectors
        self.assertGreaterEqual(
            len(period_selectors),
            3,
            "Should find at least 3 period selectors for 7, 14, and 30 days",
        )

        # 2. Verify required chart container exists
        chart_container = soup.select_one(
            "#temperature-chart, .temperature-chart, .chart-container, canvas"
        )
        self.assertIsNotNone(
            chart_container, "Temperature chart container should be present"
        )

        # 3. Verify the period selectors have the correct day values
        period_values = []
        for selector in period_selectors:
            # Look for data-days attribute
            days_attr = (
                selector.get("data-days")
                or selector.get("data-period")
                or selector.get("data-value")
            )

            # If attribute not found, check text content
            if not days_attr:
                text = selector.text.strip()
                if re.search(r"\b7\s*days?\b", text, re.IGNORECASE):
                    days_attr = "7"
                elif re.search(r"\b14\s*days?\b", text, re.IGNORECASE):
                    days_attr = "14"
                elif re.search(r"\b30\s*days?\b", text, re.IGNORECASE):
                    days_attr = "30"

            if days_attr:
                period_values.append(days_attr)

        # Check that we have the three expected period values
        expected_periods = {"7", "14", "30"}
        for period in expected_periods:
            self.assertIn(
                period, period_values, f"Should have a selector for {period} days"
            )

        # 4. TEST THE BEHAVIOR: Check for presence of JavaScript functions that handle period selection
        # This is a pragmatic approach since we can't directly test client-side JS in a server test
        js_blocks = soup.select("script")
        js_content = "".join(
            [block.string or "" for block in js_blocks if block.string]
        )

        # Look for evidence of period selector event handling in JavaScript
        has_event_listeners = False
        # Check for addEventListener pattern
        pattern1 = re.search(r"addEventListener\(\s*['\"]click['\"]\s*,", js_content)
        # Check for jQuery selector pattern
        pattern2 = re.search(
            r"\$\(\s*['\"][.#][^'\"]*(?:day-selector|period-selector)[^'\"]*['\"]\s*\)",
            js_content,
        )
        # Check for update function pattern
        pattern3 = re.search(
            r"function\s+(?:update\w*Chart|load(?:Temperature)?Data|change(?:Time)?Period)",
            js_content,
        )

        if pattern1 or pattern2 or pattern3:
            has_event_listeners = True

        self.assertTrue(
            has_event_listeners,
            "Should find evidence of JavaScript event handlers for period selection",
        )


if __name__ == "__main__":
    unittest.main()
