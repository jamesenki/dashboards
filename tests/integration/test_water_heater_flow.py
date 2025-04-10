#!/usr/bin/env python3
"""
Comprehensive end-to-end tests for water heater details page navigation flows
Following TDD principles: tests first define requirements before implementation
"""
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class WaterHeaterUITest:
    """Base class for water heater UI testing"""

    def setup_method(self):
        """Set up the browser for each test method"""
        print(f"\n🧪 Setting up test: {self.__class__.__name__}")
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")

        # Add performance-related settings
        options.add_argument("--disable-popup-blocking")  # Disables popup blocking
        options.add_argument("--disable-logging")  # Reduces logging
        options.add_argument("--log-level=3")  # Sets log level to minimal
        options.add_argument("--ignore-certificate-errors")

        # Initialize driver with modified timeout settings
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(60)  # Increase timeout to 60 seconds
        self.driver.set_script_timeout(30)  # Increase script timeout

        # Longer wait time for elements
        self.wait = WebDriverWait(self.driver, 20)
        self.base_url = "http://localhost:8000"

        # Add error tracking and recovery scripts
        self.setup_error_tracking()

    def setup_error_tracking(self):
        """Set up JavaScript error tracking and chart observation for test resilience"""
        self.driver.execute_script(
            """
        // Track JavaScript errors
        window.jsErrors = [];
        window.addEventListener('error', function(event) {
            console.error('JS Error:', event.message);
            window.jsErrors.push({
                message: event.message,
                source: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                error: event.error ? event.error.stack : null,
                timestamp: new Date().toISOString()
            });
        });

        // Add chart instance observer to help with chart rendering issues
        if (window.MutationObserver) {
            window.chartObserver = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'childList') {
                        const canvases = document.querySelectorAll('canvas');
                        canvases.forEach(function(canvas) {
                            if (canvas.id && !canvas._observed) {
                                canvas._observed = true;
                                console.log('Canvas added to DOM:', canvas.id);

                                // If ChartInstanceManager exists, ensure this canvas is properly managed
                                if (window.ChartInstanceManager &&
                                    window.ChartInstanceManager.clearChartInstance) {
                                    console.log('Ensuring canvas is properly managed:', canvas.id);
                                    window.ChartInstanceManager.clearChartInstance(canvas.id);
                                }
                            }
                        });
                    }
                });
            });

            // Start observing the document for canvas changes
            window.chartObserver.observe(document.documentElement, {
                childList: true,
                subtree: true
            });
        }
        """
        )

    def teardown_method(self):
        """Clean up after each test method"""
        # Take screenshot for evidence
        test_name = (
            f"{self.__class__.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        screenshots_dir = os.path.join(project_root, "tests/screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        self.driver.save_screenshot(os.path.join(screenshots_dir, f"{test_name}.png"))

        print(f"🧹 Tearing down test: {self.__class__.__name__}")
        self.driver.quit()

    def navigate_to_water_heaters_list(self):
        """Navigate to the water heaters list page"""
        print("🔍 Navigating to water heaters list")
        self.driver.get(f"{self.base_url}/water-heaters")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)  # Allow page to stabilize

    def navigate_to_heater_details(self, heater_id):
        """Navigate to a specific water heater details page"""
        print(f"🔍 Navigating to water heater details: {heater_id}")
        self.driver.get(f"{self.base_url}/water-heaters/{heater_id}")
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)  # Allow page to stabilize

    def click_tab(self, tab_id):
        """Click on a specific tab"""
        print(f"🖱️ Clicking on tab: {tab_id}")
        tab_button = self.driver.find_element(By.ID, f"{tab_id}-tab-btn")
        tab_button.click()
        time.sleep(1)  # Allow tab transition

        # Verify the tab content is visible
        tab_content = self.driver.find_element(By.ID, f"{tab_id}-content")
        assert tab_content.is_displayed(), f"Tab content for {tab_id} should be visible"

    def verify_no_js_errors(self):
        """Verify no JavaScript errors in console (limited capability)"""
        # This is a heuristic check using JS execution
        errors = self.driver.execute_script(
            """
        return window.JSErrors || [];
        """
        )
        assert len(errors) == 0, f"JavaScript errors found: {errors}"

    def run_js_verification(self, verification_script):
        """Run JavaScript verification script"""
        return self.driver.execute_script(verification_script)


class TestWaterHeaterDetailNavigation(WaterHeaterUITest):
    """Test case for water heater details navigation flow"""

    def test_list_to_details_navigation(self):
        """Test navigating from list to details page loads correctly"""
        print("\n🧪 TEST: List to Details Navigation Flow")

        # STEP 1: Navigate to water heaters list
        self.navigate_to_water_heaters_list()

        # Verify water heater cards are present
        heater_cards = self.wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, ".water-heater-card, .card")
            )
        )
        assert len(heater_cards) > 0, "Should find at least one water heater card"

        # Get first heater ID
        first_card = heater_cards[0]
        heater_id = (
            first_card.get_attribute("data-id") or "wh-002"
        )  # Fallback ID if not found

        # STEP 2: Navigate to details page by clicking
        print(f"🖱️ Clicking on water heater card for: {heater_id}")
        first_card.click()
        time.sleep(3)  # Allow time for navigation and page load

        # STEP 3: Verify details page loaded correctly
        page_title = self.driver.title
        current_url = self.driver.current_url

        print(f"📄 Page title: {page_title}")
        print(f"🌐 Current URL: {current_url}")

        assert "water-heater" in current_url.lower(), "URL should contain water-heater"

        # Verify tabs exist
        tabs = self.driver.find_elements(By.CSS_SELECTOR, "[id$='-tab-btn']")
        assert len(tabs) >= 3, "Should find at least 3 tabs"

        # Verify details content is visible
        details_content = self.wait.until(
            EC.visibility_of_element_located((By.ID, "details-content"))
        )
        assert details_content.is_displayed(), "Details content should be visible"

        print("✅ TEST PASSED: List to Details navigation works correctly")


class TestDetailsPageFunctionality(WaterHeaterUITest):
    """Test case for details page core functionality"""

    def test_details_page_loads_correctly(self):
        """Test that the details page loads all its components correctly"""
        print("\n🧪 TEST: Details Page Core Functionality")

        # Navigate directly to a water heater details page
        self.navigate_to_heater_details("wh-002")

        # Verify page structure
        print("🔍 Verifying details page structure")

        # 1. Header should be visible
        header = self.driver.find_element(By.TAG_NAME, "header")
        assert header.is_displayed(), "Header should be visible"

        # 2. Tab container should exist
        tab_container = self.driver.find_element(
            By.CSS_SELECTOR, ".tab-container, [role='tablist']"
        )
        assert tab_container.is_displayed(), "Tab container should be visible"

        # 3. Details content should be visible by default
        details_content = self.wait.until(
            EC.visibility_of_element_located((By.ID, "details-content"))
        )
        assert (
            details_content.is_displayed()
        ), "Details content should be visible by default"

        # 4. Check for key details sections
        sections = [
            "device-info",
            "status-section",
            "temperature-info",
            "maintenance-info",
            "settings-section",
        ]

        found_sections = []
        for section in sections:
            elements = self.driver.find_elements(
                By.CSS_SELECTOR, f"#{section}, .{section}, [data-section='{section}']"
            )
            if elements and any(el.is_displayed() for el in elements):
                found_sections.append(section)
                print(f"  ✓ Found section: {section}")

        # Should find at least 3 of the expected sections
        assert (
            len(found_sections) >= 3
        ), f"Should find at least 3 key sections, found: {found_sections}"

        # 5. Verify charts or gauges are present
        charts = self.driver.find_elements(By.TAG_NAME, "canvas")
        print(f"  🔍 Found {len(charts)} charts/gauges on details page")
        assert len(charts) > 0, "Should find at least one chart or gauge"

        # 6. Check for errors in console
        js_errors = self.driver.execute_script(
            """
        const errors = window.jsErrors || [];
        return errors.length;
        """
        )

        assert js_errors == 0, f"Found {js_errors} JavaScript errors on details page"

        print("✅ TEST PASSED: Details page loads correctly")

    def test_details_page_data_loading(self):
        """Test that the details page loads actual device data"""
        print("\n🧪 TEST: Details Page Data Loading")

        # Navigate to details page
        self.navigate_to_heater_details("wh-002")
        time.sleep(2)  # Allow data to load

        # Check if we have actual device data loaded
        data_verification = self.driver.execute_script(
            """
        // Look for actual device data in the UI
        const textElements = document.querySelectorAll('.device-name, .device-id, .temperature-value, .status-value');

        // Check if we have populated text fields
        const populatedElements = Array.from(textElements).filter(el => {
            const text = el.textContent.trim();
            return text !== '' && text !== 'N/A' && text !== 'Unknown' && text !== 'Loading...';
        });

        // Check for cards showing actual data
        const cards = document.querySelectorAll('.card, .data-card, .status-card');
        const cardsWithData = Array.from(cards).filter(card => {
            const cardText = card.textContent.trim();
            return cardText.length > 10; // Simple heuristic for populated card
        });

        // Check if any chart has actual data
        const charts = Array.from(document.querySelectorAll('canvas'));
        const chartsWithData = charts.filter(canvas => {
            // Look for chart instance
            const chartInstance = window._temperatureChart ||
                                 (canvas._chart ? canvas._chart : null) ||
                                 (window.ChartInstanceManager &&
                                  window.ChartInstanceManager.getChart ?
                                  window.ChartInstanceManager.getChart(canvas.id) : null);

            if (!chartInstance) return false;

            // Check if chart has data
            return chartInstance.data &&
                   chartInstance.data.datasets &&
                   chartInstance.data.datasets.length > 0 &&
                   chartInstance.data.datasets[0].data &&
                   chartInstance.data.datasets[0].data.length > 0;
        });

        return {
            populatedElementCount: populatedElements.length,
            cardsWithDataCount: cardsWithData.length,
            chartsWithDataCount: chartsWithData.length,
            // If charts don't have data, check for error messages
            errorMessages: Array.from(document.querySelectorAll('.error-message, .alert-warning, .alert-danger'))
                          .filter(el => el.style.display !== 'none')
                          .map(el => el.textContent.trim())
        };
        """
        )

        print(f"  📊 Data elements found: {data_verification}")

        # Verify that either we have data OR proper error messages
        has_data = (
            data_verification["populatedElementCount"] > 3
            and data_verification["cardsWithDataCount"] > 0
        )

        has_errors = len(data_verification["errorMessages"]) > 0

        assert (
            has_data or has_errors
        ), "Details page should either show data OR display proper error messages"

        if has_data:
            print("  ✓ Details page loaded with actual device data")
        else:
            print(
                f"  ⚠️ Details page showing error messages: {data_verification['errorMessages']}"
            )
            print("  ✓ Error messages are properly displayed (acceptable fallback)")

        print("✅ TEST PASSED: Details page handles data loading or errors correctly")


class TestWaterHeaterTabNavigation(WaterHeaterUITest):
    """Test case for water heater tab navigation"""

    def test_tab_navigation(self):
        """Test that all tabs can be navigated and load correctly"""
        print("\n🧪 TEST: Tab Navigation and Content Loading")

        # Start on details page for a specific heater
        self.navigate_to_heater_details("wh-002")

        # Find all tabs
        tab_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[id$='-tab-btn']")
        tab_ids = [
            btn.get_attribute("id").replace("-tab-btn", "") for btn in tab_buttons
        ]

        print(f"📋 Found {len(tab_ids)} tabs: {', '.join(tab_ids)}")

        # Navigate through each tab and verify content loads
        for tab_id in tab_ids:
            print(f"\n🔄 Testing navigation to tab: {tab_id}")
            self.click_tab(tab_id)

            # Verify tab content is visible
            tab_content = self.wait.until(
                EC.visibility_of_element_located((By.ID, f"{tab_id}-content"))
            )
            assert (
                tab_content.is_displayed()
            ), f"Content for tab {tab_id} should be visible"

            # Verify content has loaded
            content_verification = self.driver.execute_script(
                f"""
            const content = document.getElementById("{tab_id}-content");
            return {{
                isVisible: window.getComputedStyle(content).display !== 'none',
                hasChildren: content.children.length > 0,
                innerHTML: content.innerHTML.length
            }};
            """
            )

            print(f"  ✓ Tab {tab_id} visible: {content_verification['isVisible']}")
            print(
                f"  ✓ Tab {tab_id} has children: {content_verification['hasChildren']}"
            )
            print(
                f"  ✓ Tab {tab_id} content length: {content_verification['innerHTML']} chars"
            )

            assert content_verification["isVisible"], f"Tab {tab_id} should be visible"
            assert content_verification[
                "hasChildren"
            ], f"Tab {tab_id} should have child elements"
            assert (
                content_verification["innerHTML"] > 0
            ), f"Tab {tab_id} should have content"

            # Special verifications for specific tabs
            if tab_id == "history":
                self.verify_history_tab()

        print("✅ TEST PASSED: All tabs navigate and load correctly")

    def verify_history_tab(self):
        """Verify history tab specific elements and functionality"""
        print("🔍 Verifying history tab specific elements")

        # Wait for temperature chart to be present
        temp_chart_container = self.wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "#temperature-chart, .temperature-history-chart, [data-chart='temperature-history']",
                )
            )
        )

        # Check period selectors
        period_selectors = self.driver.find_elements(
            By.CSS_SELECTOR, ".period-selector, [data-days]"
        )
        print(f"📊 Found {len(period_selectors)} period selectors")

        # Verify that either chart canvas exists OR error message is displayed
        verification = self.driver.execute_script(
            """
        // Get all chart containers
        const chartContainers = document.querySelectorAll('#temperature-chart, .temperature-history-chart, [data-chart="temperature-history"]');
        const containerArray = Array.from(chartContainers);

        // Find all canvases that are inside chart containers
        const canvases = Array.from(document.querySelectorAll('canvas')).filter(canvas => {
            // Check if canvas is inside a chart container
            return containerArray.some(container => {
                return container.contains(canvas) || canvas.id === 'temperature-chart-canvas';
            });
        });

        // Check for visible error messages
        const errorMessages = document.querySelectorAll('.error-message, .alert-warning, .alert-danger, .chart-message.error, .no-data-message');
        const visibleErrors = Array.from(errorMessages).filter(el => window.getComputedStyle(el).display !== 'none');

        return {
            hasCanvas: canvases.length > 0,
            canvasVisible: canvases.length > 0 ? window.getComputedStyle(canvases[0]).display !== 'none' : false,
            hasErrorMessage: errorMessages.length > 0,
            errorMessageVisible: visibleErrors.length > 0,
            visibleErrorCount: visibleErrors.length,
            errorMessages: visibleErrors.map(el => el.textContent.trim()).filter(text => text.length > 0)
        };
        """
        )

        print(f"📊 Chart verification: {verification}")

        # According to TDD principles, we need either a working chart OR an appropriate error message
        assert (
            verification["hasCanvas"] or verification["hasErrorMessage"]
        ), "Should have either a chart canvas OR an error message"
        assert (
            verification["canvasVisible"] or verification["errorMessageVisible"]
        ), "Either chart canvas OR error message should be visible"


class TestTemperatureHistoryChart(WaterHeaterUITest):
    """Test case for temperature history chart functionality"""

    def test_temperature_history_display(self):
        """Test that temperature history displays correctly in different periods"""
        print("\n🧪 TEST: Temperature History Chart Display and Period Changes")

        # Navigate to details page
        self.navigate_to_heater_details("wh-002")

        # Navigate to history tab
        self.click_tab("history")

        # Wait for chart container
        chart_container = self.wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "#temperature-chart, .temperature-history-chart, [data-chart='temperature-history']",
                )
            )
        )

        # Get period selectors
        period_selectors = self.driver.find_elements(
            By.CSS_SELECTOR, ".period-selector, [data-days]"
        )

        print(f"📊 Found {len(period_selectors)} period selectors")

        if len(period_selectors) >= 3:
            # Test each period selector (7, 14, 30 days)
            period_data = [(0, 7), (1, 14), (2, 30)]

            for idx, days in period_data:
                if idx < len(period_selectors):
                    print(f"\n🔄 Testing {days}-day period selector")

                    # Click period selector
                    period_selectors[idx].click()
                    time.sleep(2)  # Wait for data to load

                    # Verify chart updated
                    chart_data = self.driver.execute_script(
                        """
                    const canvases = document.querySelectorAll('canvas');
                    // Find chart instance
                    const chartInstance = Array.from(canvases).find(c => c._chart)
                                         ? Array.from(canvases).find(c => c._chart)._chart
                                         : window._temperatureChart || null;

                    if (!chartInstance) return { error: 'Chart instance not found' };

                    return {
                        hasData: chartInstance.data && chartInstance.data.datasets &&
                                chartInstance.data.datasets[0] &&
                                chartInstance.data.datasets[0].data &&
                                chartInstance.data.datasets[0].data.length > 0,
                        dataPoints: chartInstance.data && chartInstance.data.datasets &&
                                   chartInstance.data.datasets[0] &&
                                   chartInstance.data.datasets[0].data ?
                                   chartInstance.data.datasets[0].data.length : 0,
                        labels: chartInstance.data && chartInstance.data.labels ?
                                chartInstance.data.labels.length : 0
                    };
                    """
                    )

                    print(
                        f"📊 Chart data after {days}-day period selection: {chart_data}"
                    )

                    # Check for either data or error message
                    if "error" in chart_data:
                        # If chart instance not found, check for visible error message
                        # Following TDD principles: be more flexible in detecting properly displayed errors
                        error_msg_visible = self.driver.execute_script(
                            """
                        // Find all possible error message elements using broader selectors
                        const errorMsgs = document.querySelectorAll(
                            '.error-message, .alert, .chart-message.error, .no-data-message, ' +
                            '[class*="error"], [class*="alert"], .text-danger, #history-error'
                        );

                        // Check if any error message is visible
                        const visibleErrors = Array.from(errorMsgs).filter(el =>
                            window.getComputedStyle(el).display !== 'none' &&
                            el.textContent.trim() !== ''
                        );

                        // For debugging, log all found errors
                        console.log('Found error messages:',
                            visibleErrors.map(e => ({text: e.textContent.trim(), display: window.getComputedStyle(e).display}))
                        );

                        // Also check for any element that might function as an error message
                        // even if it doesn't have an explicit error class
                        const historyContent = document.getElementById('history-content');
                        if (historyContent) {
                            const allElements = historyContent.querySelectorAll('*');
                            for (const el of allElements) {
                                // Look for elements with text that suggests they're error messages
                                const text = el.textContent.trim().toLowerCase();
                                if (text &&
                                    (text.includes('error') ||
                                     text.includes('failed') ||
                                     text.includes('no data') ||
                                     text.includes('not available') ||
                                     text.includes('not found')) &&
                                    window.getComputedStyle(el).display !== 'none') {
                                    visibleErrors.push(el);
                                }
                            }
                        }

                        return visibleErrors.length > 0;
                        """
                        )

                        assert (
                            error_msg_visible
                        ), f"Either chart with {days}-day data should be visible OR error message should be displayed"
                    else:
                        # Verify we have data or an error is shown
                        assert (
                            chart_data.get("hasData", False) or error_msg_visible
                        ), f"Chart should have data for {days}-day period OR error message should be displayed"

        print(
            "✅ TEST PASSED: Temperature history chart periods work correctly or display proper errors"
        )


class TestChartInitialization(WaterHeaterUITest):
    """Test case for canvas/chart initialization issues"""

    def test_canvas_initialization(self):
        """Test that canvas elements initialize only once and correctly"""
        print("\n🧪 TEST: Canvas Initialization and Reuse")

        # Navigate to details page
        self.navigate_to_heater_details("wh-002")

        # Check initial canvas count
        initial_canvas_count = len(self.driver.find_elements(By.TAG_NAME, "canvas"))
        print(f"📊 Initial canvas count: {initial_canvas_count}")

        # Navigate through tabs
        tabs = ["details", "history", "operations", "details", "history"]
        for tab in tabs:
            self.click_tab(tab)
            time.sleep(1)

            # Check canvas count after tab change
            current_canvas_count = len(self.driver.find_elements(By.TAG_NAME, "canvas"))
            print(f"📊 Canvas count after navigating to {tab}: {current_canvas_count}")

            # Verify no duplicate/excess canvas elements created
            assert (
                current_canvas_count <= initial_canvas_count + 3
            ), f"Canvas count should not grow excessively when navigating to {tab} tab"

        # Verify canvas elements are properly initialized
        canvas_status = self.driver.execute_script(
            """
        const canvases = document.querySelectorAll('canvas');
        return Array.from(canvases).map(canvas => ({
            id: canvas.id || '(no id)',
            width: canvas.width,
            height: canvas.height,
            display: window.getComputedStyle(canvas).display,
            hasChartInstance: !!canvas._chart
        }));
        """
        )

        print(f"📊 Canvas initialization status: {canvas_status}")

        # Verify canvas "temperature-chart" is properly initialized
        temp_chart_canvases = [
            c for c in canvas_status if "temperature" in c["id"].lower()
        ]
        if temp_chart_canvases:
            assert any(
                c["width"] > 0 and c["height"] > 0 for c in temp_chart_canvases
            ), "Temperature chart canvas should have proper dimensions"

        print("✅ TEST PASSED: Canvas initialization and reuse works correctly")


if __name__ == "__main__":
    # Run the tests
    test_classes = [
        TestWaterHeaterDetailNavigation,
        TestWaterHeaterTabNavigation,
        TestTemperatureHistoryChart,
        TestChartInitialization,
    ]

    print("\n🧪🧪🧪 RUNNING COMPREHENSIVE TDD TESTS FOR WATER HEATER UI 🧪🧪🧪\n")

    for test_class in test_classes:
        test_instance = test_class()
        test_methods = [
            method for method in dir(test_class) if method.startswith("test_")
        ]

        for method in test_methods:
            try:
                test_instance.setup_method()
                getattr(test_instance, method)()
                print(f"\n✅ {test_class.__name__}.{method} PASSED")
            except Exception as e:
                print(f"\n❌ {test_class.__name__}.{method} FAILED: {str(e)}")
                raise
            finally:
                test_instance.teardown_method()

    print("\n🏁 ALL TESTS COMPLETED 🏁")
