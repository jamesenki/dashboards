#!/usr/bin/env python3
"""
Lazy Loading Diagnostics Tool

This tool performs automated diagnostics to validate the lazy loading implementation
for the Water Heater Details page. It checks that tabs are only loaded when activated,
ensuring improved performance and error isolation.

Following TDD principles, this tests the expected behavior of the enhanced tab manager
and helps verify that our implementation meets the requirements.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Append the project root to the path to ensure imports work
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)


class LazyLoadingDiagnostics:
    """Diagnostics tool to validate the lazy loading implementation"""

    def __init__(
        self, base_url="http://localhost:8006", device_id="aqua-wh-1001", headless=True
    ):
        """Initialize the diagnostics tool with the target URL and device ID"""
        self.base_url = base_url
        self.device_id = device_id
        self.detail_url = f"{base_url}/water-heaters/{device_id}"
        self.network_requests = []

        # Configure Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--log-level=3")  # Suppress console noise

        # Initialize the WebDriver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)

        print(f"Diagnostics initialized for device: {device_id}")
        print(f"Target URL: {self.detail_url}")

    def __del__(self):
        """Clean up resources"""
        if hasattr(self, "driver"):
            self.driver.quit()

    def run_diagnostics(self):
        """Run a complete set of diagnostics tests"""
        print("\n==== Starting Lazy Loading Diagnostics ====")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Load the details page
        success = self.load_details_page()
        if not success:
            print("Failed to load details page. Exiting diagnostics.")
            return False

        # Test initial tab state
        print("\n- Testing initial tab state...")
        self.test_initial_tab_state()

        # Test lazy loading on tab change
        print("\n- Testing lazy loading on tab change...")
        self.test_lazy_loading_on_tab_change()

        # Test performance improvement
        print("\n- Testing performance improvements...")
        self.test_performance_improvements()

        # Test error isolation
        print("\n- Testing error isolation between tabs...")
        self.test_error_isolation()

        print("\n==== Diagnostics Complete ====")
        return True

    def load_details_page(self):
        """Load the water heater details page and wait for it to initialize"""
        try:
            print(f"Loading details page for device: {self.device_id}")
            self.driver.get(self.detail_url)

            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "water-heater-container"))
            )

            print("✅ Details page loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to load details page: {e}")
            return False

    def test_initial_tab_state(self):
        """Test that only the active tab is loaded initially"""
        try:
            # Check which tab is active initially
            active_tab = self.driver.execute_script(
                "return window.tabManager ? window.tabManager.activeTab : 'unknown';"
            )
            print(f"Initial active tab: {active_tab}")

            # Check initialization state of each dashboard
            tab_states = {
                "details": self.driver.execute_script(
                    "return window.dataLoadingState ? window.dataLoadingState.detail : false;"
                ),
                "operations": self.driver.execute_script(
                    "return window.dataLoadingState ? window.dataLoadingState.operations : false;"
                ),
                "predictions": self.driver.execute_script(
                    "return window.dataLoadingState ? window.dataLoadingState.predictions : false;"
                ),
                "history": self.driver.execute_script(
                    "return window.dataLoadingState ? window.dataLoadingState.history : false;"
                ),
            }

            # Verify that only the active tab is initialized
            for tab, state in tab_states.items():
                expected = tab == active_tab
                result = "✅" if state == expected else "❌"
                print(
                    f"{result} {tab.capitalize()} tab initialization state: {state} (Expected: {expected})"
                )

            return True
        except Exception as e:
            print(f"❌ Failed to test initial tab state: {e}")
            return False

    def test_lazy_loading_on_tab_change(self):
        """Test that inactive tabs are loaded only when activated"""
        try:
            # Find a tab that isn't loaded yet
            unloaded_tabs = []
            tab_buttons = {
                "operations": self.driver.find_element(By.ID, "operations-tab-btn"),
                "predictions": self.driver.find_element(By.ID, "predictions-tab-btn"),
                "history": self.driver.find_element(By.ID, "history-tab-btn"),
            }

            # Check which tabs are not loaded
            for tab, button in tab_buttons.items():
                is_loaded = self.driver.execute_script(
                    f"return window.dataLoadingState ? window.dataLoadingState.{tab} : false;"
                )
                if not is_loaded:
                    unloaded_tabs.append(tab)

            if not unloaded_tabs:
                print("All tabs are already loaded, cannot test lazy loading.")
                return False

            # Select the first unloaded tab
            test_tab = unloaded_tabs[0]
            print(f"Testing lazy loading for tab: {test_tab}")

            # Check before clicking
            before_state = self.driver.execute_script(
                f"return window.dataLoadingState ? window.dataLoadingState.{test_tab} : false;"
            )
            print(f"Before activation - {test_tab} tab loaded: {before_state}")

            # Click the tab button
            tab_buttons[test_tab].click()

            # Wait for the tab to become active
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, f"#{test_tab}-content.active")
                )
            )

            # Check after clicking
            time.sleep(2)  # Give it a moment to initialize
            after_state = self.driver.execute_script(
                f"return window.dataLoadingState ? window.dataLoadingState.{test_tab} : false;"
            )
            print(f"After activation - {test_tab} tab loaded: {after_state}")

            if not before_state and after_state:
                print(f"✅ Lazy loading confirmed for {test_tab} tab!")
                return True
            else:
                print(f"❌ Lazy loading failed for {test_tab} tab!")
                return False

        except Exception as e:
            print(f"❌ Failed to test lazy loading on tab change: {e}")
            return False

    def test_performance_improvements(self):
        """Test performance improvements from lazy loading"""
        try:
            # Reset the page to start fresh
            self.driver.refresh()
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "water-heater-container"))
            )

            # Time the initial page load (with lazy loading)
            start_time_lazy = time.time()
            # Wait for the critical elements to be loaded
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#water-heater-detail")
                )
            )
            lazy_load_time = time.time() - start_time_lazy

            # Now manually load all tabs to simulate the old approach
            self.driver.execute_script(
                """
                console.time('all_tabs_load');
                if (!window.waterHeaterOperationsDashboard) {
                    window.waterHeaterOperationsDashboard = new WaterHeaterOperationsDashboard(
                        document.body.getAttribute('data-heater-id'),
                        'operations-content'
                    );
                }
                if (!window.waterHeaterHistoryDashboard) {
                    window.waterHeaterHistoryDashboard = new WaterHeaterHistoryDashboard(
                        document.body.getAttribute('data-heater-id')
                    );
                }
                if (!window.waterHeaterPredictionsDashboard) {
                    window.waterHeaterPredictionsDashboard = new WaterHeaterPredictionsDashboard(
                        'water-heater-predictions-dashboard',
                        document.body.getAttribute('data-heater-id')
                    );
                }
                console.timeEnd('all_tabs_load');
            """
            )

            # Get the time it took to load all tabs
            all_tabs_load_time = self.driver.execute_script(
                "return window.performance.getEntriesByName('all_tabs_load')[0].duration;"
            )

            print(
                f"Initial page load time (lazy loading): {lazy_load_time:.2f} seconds"
            )
            print(f"Time to load all tabs: {all_tabs_load_time/1000:.2f} seconds")
            print(
                f"Performance improvement: {(all_tabs_load_time/1000 - lazy_load_time):.2f} seconds"
            )

            if lazy_load_time < all_tabs_load_time / 1000:
                print("✅ Lazy loading provides performance improvements!")
                return True
            else:
                print("❌ No performance improvement detected.")
                return False

        except Exception as e:
            print(f"❌ Failed to test performance improvements: {e}")
            return False

    def test_error_isolation(self):
        """Test that errors in one tab don't affect others"""
        try:
            # Reset the page to start fresh
            self.driver.refresh()
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "water-heater-container"))
            )

            # Inject code to make the predictions dashboard throw an error
            self.driver.execute_script(
                """
                // Store the original constructor
                window._originalPredictionsDashboard = window.WaterHeaterPredictionsDashboard;

                // Replace with one that throws an error
                window.WaterHeaterPredictionsDashboard = function() {
                    throw new Error('Simulated error in predictions dashboard');
                };

                // Flag to indicate we've tampered with it
                window._predictionsModified = true;
            """
            )

            # Click the predictions tab to trigger the error
            predictions_tab = self.driver.find_element(By.ID, "predictions-tab-btn")
            predictions_tab.click()

            # Wait a moment for the error to occur
            time.sleep(2)

            # Check if an error was displayed
            predictions_error_visible = self.driver.execute_script(
                "return Boolean(document.querySelector('#predictions-content .error-message')) && "
                + "document.querySelector('#predictions-content .error-message').style.display !== 'none';"
            )

            print(f"Predictions tab error visible: {predictions_error_visible}")

            # Now try to load the history tab
            history_tab = self.driver.find_element(By.ID, "history-tab-btn")
            history_tab.click()

            # Wait for the history tab to activate
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#history-content.active")
                )
            )

            # Give it time to initialize
            time.sleep(3)

            # Check if history tab initialized successfully
            history_initialized = self.driver.execute_script(
                "return window.waterHeaterHistoryDashboard ? true : false;"
            )

            print(
                f"History tab initialized despite predictions error: {history_initialized}"
            )

            # Clean up: restore the original constructor
            self.driver.execute_script(
                """
                if (window._predictionsModified) {
                    window.WaterHeaterPredictionsDashboard = window._originalPredictionsDashboard;
                    delete window._predictionsModified;
                    delete window._originalPredictionsDashboard;
                }
            """
            )

            if predictions_error_visible and history_initialized:
                print(
                    "✅ Error isolation confirmed! Errors in one tab don't affect others."
                )
                return True
            else:
                print("❌ Error isolation test failed!")
                return False

        except Exception as e:
            print(f"❌ Failed to test error isolation: {e}")
            return False


def main():
    """Main function to run the diagnostics"""
    parser = argparse.ArgumentParser(description="Lazy Loading Diagnostics Tool")
    parser.add_argument(
        "--url", default="http://localhost:8006", help="Base URL of the server"
    )
    parser.add_argument(
        "--device", default="aqua-wh-1001", help="Device ID to test with"
    )
    parser.add_argument(
        "--no-headless", action="store_true", help="Run with browser visible"
    )
    args = parser.parse_args()

    # Run diagnostics
    diagnostics = LazyLoadingDiagnostics(
        base_url=args.url, device_id=args.device, headless=not args.no_headless
    )

    try:
        diagnostics.run_diagnostics()
    except KeyboardInterrupt:
        print("\nDiagnostics interrupted by user")
    finally:
        del diagnostics


if __name__ == "__main__":
    main()
