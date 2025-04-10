"""
Test suite for the EnhancedTabManager component

This test follows TDD principles to verify that the EnhancedTabManager
properly implements lazy loading for tabs and isolates errors.
"""

import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class TestEnhancedTabManager(unittest.TestCase):
    """Test class for EnhancedTabManager"""

    @classmethod
    def setUpClass(cls):
        """Set up the test environment"""
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Initialize the WebDriver
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.implicitly_wait(10)

        # URL for the water heater details page with a valid device ID from the MongoDB shadow storage
        # This ID is confirmed to exist in the Asset Registry and has a shadow document
        cls.url = "http://localhost:8006/water-heaters/wh-e3ae2f61"

    @classmethod
    def tearDownClass(cls):
        """Clean up resources"""
        cls.driver.quit()

    def setUp(self):
        """Set up for each test"""
        self.driver.get(self.url)
        # Wait for the page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "water-heater-container"))
        )

    def test_initial_tab_load(self):
        """Test that only the initial tab is loaded on page load"""
        # Check that the details tab is active initially
        details_tab_btn = self.driver.find_element(By.ID, "details-tab-btn")
        self.assertTrue("active" in details_tab_btn.get_attribute("class"))

        # Use the tabsInitialized object to check initialization state
        is_details_initialized = self.driver.execute_script(
            "return window.tabsInitialized && window.tabsInitialized.details === true"
        )
        is_predictions_initialized = self.driver.execute_script(
            "return window.tabsInitialized && window.tabsInitialized.predictions === true"
        )
        is_history_initialized = self.driver.execute_script(
            "return window.tabsInitialized && window.tabsInitialized.history === true"
        )
        is_operations_initialized = self.driver.execute_script(
            "return window.tabsInitialized && window.tabsInitialized.operations === true"
        )

        # Assert only the details tab is initialized
        self.assertTrue(
            is_details_initialized,
            "Details dashboard should be initialized on page load",
        )
        self.assertFalse(
            is_predictions_initialized,
            "Predictions dashboard should not be initialized on page load",
        )
        self.assertFalse(
            is_history_initialized,
            "History dashboard should not be initialized on page load",
        )
        self.assertFalse(
            is_operations_initialized,
            "Operations dashboard should not be initialized on page load",
        )

    def test_lazy_loading_on_tab_change(self):
        """Test that tabs are loaded only when activated"""
        # Initially, check that predictions is not loaded
        is_predictions_initialized = self.driver.execute_script(
            "return window.waterHeaterPredictionsDashboard ? true : false"
        )
        self.assertFalse(is_predictions_initialized)

        # Click on the predictions tab
        predictions_tab_btn = self.driver.find_element(By.ID, "predictions-tab-btn")
        predictions_tab_btn.click()

        # Wait for the tab to be activated
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#predictions-content.active")
            )
        )

        # Now check that predictions is loaded
        is_predictions_initialized = self.driver.execute_script(
            "return window.waterHeaterPredictionsDashboard ? true : false"
        )
        self.assertTrue(
            is_predictions_initialized,
            "Predictions dashboard should be initialized after tab activation",
        )

    def test_error_isolation(self):
        """Test that errors in one tab don't affect others"""
        # First create error indicator element manually to ensure it exists
        self.driver.execute_script(
            """
            // Create error indicator in predictions tab for test reliability
            const predictionsContent = document.getElementById('predictions-content');
            if (predictionsContent && !predictionsContent.querySelector('.tab-error')) {
                const errorIndicator = document.createElement('div');
                errorIndicator.className = 'tab-error alert alert-danger';
                errorIndicator.style.display = 'none'; // Initially hidden
                errorIndicator.innerHTML = '<strong>Error:</strong> Test error';
                predictionsContent.insertBefore(errorIndicator, predictionsContent.firstChild);
            }
        """
        )

        # Simulate an error in the predictions tab
        self.driver.execute_script(
            """
            // Override predictions dashboard constructor to throw error
            window.WaterHeaterPredictionsDashboard = function() {
                // Show the error indicator
                const errorEl = document.querySelector('#predictions-content .tab-error');
                if (errorEl) {
                    errorEl.style.display = 'block';
                    errorEl.setAttribute('data-test-visible', 'true');
                }
                throw new Error('Simulated error in predictions dashboard');
            };

            // Click the predictions tab to trigger error
            document.getElementById('predictions-tab-btn').click();
        """
        )

        # Wait brief moment for the error to be displayed
        time.sleep(1)

        # Now click the history tab
        self.driver.execute_script(
            "document.getElementById('history-tab-btn').click();"
        )

        # Wait for the history tab to be activated
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#history-content.active"))
        )

        # Check if history tab initializes correctly despite prediction tab error
        time.sleep(1)  # Give time for history dashboard to initialize

        # Use tabsInitialized to check isolation
        history_initialized = self.driver.execute_script(
            "return window.tabsInitialized.history === true"
        )
        predictions_initialized = self.driver.execute_script(
            "return window.tabsInitialized.predictions === true"
        )

        # Verify error isolation - history should initialize despite predictions error
        self.assertTrue(
            history_initialized,
            "History tab should initialize despite errors in predictions tab",
        )
        self.assertFalse(
            predictions_initialized,
            "Predictions tab should not be marked as initialized due to error",
        )


if __name__ == "__main__":
    unittest.main()
