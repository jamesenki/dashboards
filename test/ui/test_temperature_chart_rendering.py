"""
UI Test for Temperature Chart Rendering

This test verifies that temperature charts render properly without duplication
"""
import os
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Set the path to the chromedriver executable
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"


class TemperatureChartRenderingTest(unittest.TestCase):
    """Test temperature chart rendering in the UI"""

    @classmethod
    def setUpClass(cls):
        # Initialize the Chrome WebDriver in headless mode
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")  # Faster startup
        options.add_argument("--disable-logging")  # Reduce log noise
        options.add_argument(
            "--disable-web-security"
        )  # Skip some security checks for speed

        # Create the WebDriver
        try:
            cls.driver = webdriver.Chrome(
                executable_path=CHROMEDRIVER_PATH, options=options
            )
        except:
            # If chromedriver executable isn't found, try the default behavior
            cls.driver = webdriver.Chrome(options=options)

        # Set explicit wait timeout - reduce from 10 to 3 seconds for faster tests
        cls.wait = WebDriverWait(cls.driver, 3)

        # Base URL for tests
        cls.base_url = "http://localhost:8006"

    @classmethod
    def tearDownClass(cls):
        # Close the WebDriver
        cls.driver.quit()

    def test_details_page_has_single_chart(self):
        """Test that the details page has exactly one temperature chart"""
        # Navigate to the details page
        self.driver.get(f"{self.base_url}/water-heaters/wh-001")

        try:
            # Add a print statement to indicate test progress
            print("\nAttempting to load details page...")

            # Wait for the page to load by waiting for the device details header
            self.wait.until(EC.presence_of_element_located((By.ID, "device-details")))
            print("Device details page loaded successfully")

            # Get all temperature chart containers
            charts = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".temperature-history-chart, [data-chart='temperature-history'], #temperature-chart",
            )

            # Verify only one chart container is actually visible
            visible_charts = [chart for chart in charts if chart.is_displayed()]

            # Test assertion
            self.assertEqual(
                len(visible_charts),
                1,
                f"Expected exactly 1 visible temperature chart but found {len(visible_charts)}",
            )

            # Check if there are any duplicate instances of chart.js
            chart_instances = self.driver.execute_script(
                "return document.querySelectorAll('canvas').length"
            )

            self.assertEqual(
                chart_instances,
                1,
                f"Expected exactly 1 chart canvas but found {chart_instances}",
            )

            # Check for any error messages in the chart container
            error_elements = self.driver.find_elements(
                By.CSS_SELECTOR, ".chart-error, .error-message"
            )
            visible_errors = [error for error in error_elements if error.is_displayed()]

            self.assertEqual(
                len(visible_errors),
                0,
                f"Found {len(visible_errors)} error messages in the chart: {[e.text for e in visible_errors]}",
            )

        except TimeoutException:
            self.fail("Timed out waiting for details page to load")

    def test_history_tab_has_single_chart(self):
        """Test that the history tab has exactly one temperature chart"""
        # Navigate to the details page
        self.driver.get(f"{self.base_url}/water-heaters/wh-001")

        try:
            # Add a print statement to indicate test progress
            print("\nAttempting to load details page for history tab test...")

            # Wait for the page to load
            self.wait.until(EC.presence_of_element_located((By.ID, "device-details")))
            print("Device details page loaded successfully for history tab test")

            # Click on the history tab
            history_tab = self.driver.find_element(
                By.CSS_SELECTOR, "a[href='#history-tab']"
            )
            history_tab.click()

            # Wait for the history tab to become active
            self.wait.until(EC.visibility_of_element_located((By.ID, "history-tab")))

            # Get all chart containers in the history tab
            history_tab_element = self.driver.find_element(By.ID, "history-tab")
            charts = history_tab_element.find_elements(
                By.CSS_SELECTOR,
                ".temperature-history-chart, [data-chart='temperature-history']",
            )

            # Verify only one chart container is visible
            visible_charts = [chart for chart in charts if chart.is_displayed()]

            self.assertEqual(
                len(visible_charts),
                1,
                f"Expected exactly 1 visible temperature chart in history tab but found {len(visible_charts)}",
            )

            # Check if there are any duplicate instances of chart.js
            chart_instances = history_tab_element.find_elements(
                By.CSS_SELECTOR, "canvas"
            )

            self.assertEqual(
                len(chart_instances),
                1,
                f"Expected exactly 1 chart canvas in history tab but found {len(chart_instances)}",
            )

        except TimeoutException:
            self.fail("Timed out waiting for history tab to load")


if __name__ == "__main__":
    # For direct execution, use a smaller timeout
    TemperatureChartRenderingTest.wait_timeout = 2
    unittest.main()
