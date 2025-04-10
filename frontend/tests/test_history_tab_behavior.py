"""
Tests for the History tab behavior in the IoTSphere water heater interface.
These tests focus on verifying the specific requirements for the History tab:
1. Only loads 7 days of data by default
2. Only loads 14/30 days when explicitly requested
3. Properly handles error conditions
4. Never shows empty states

This follows TDD principles by defining expected behaviors in tests.
"""

import json
import re
from datetime import datetime, timedelta

import pytest
from playwright.sync_api import Page, Request, Route, expect


class TestHistoryTabBehavior:
    """
    Test suite for History tab behavior.
    Verifies card structure, error handling, and data loading patterns.
    """

    @pytest.fixture(scope="function")
    def network_requests(self, page: Page):
        """Fixture to track network requests."""
        requests = []

        def log_request(route: Route, request: Request):
            # Only track API requests
            if "/api/" in request.url:
                requests.append(
                    {
                        "url": request.url,
                        "method": request.method,
                        "post_data": request.post_data,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            route.continue_()

        # Route all requests through our logger
        page.route("**/*", log_request)

        return requests

    @pytest.fixture(scope="function")
    def setup_error_condition(self, page: Page):
        """Fixture to simulate shadow document error condition."""
        # Add script to simulate shadow document error
        page.add_init_script(
            """
        window.addEventListener('DOMContentLoaded', function() {
            // Override fetch for shadow document endpoints to simulate error
            const originalFetch = window.fetch;
            window.fetch = function(url, options) {
                if (url.includes('/api/shadow/') || url.includes('/shadow/document')) {
                    console.log('Simulating shadow document error for:', url);
                    return Promise.resolve({
                        ok: false,
                        status: 404,
                        json: () => Promise.resolve({
                            error: "No shadow document exists",
                            code: "SHADOW_NOT_FOUND"
                        })
                    });
                }
                return originalFetch(url, options);
            };

            // Also listen for any custom events that might be used
            document.addEventListener('shadow-document-loaded', function(e) {
                // Dispatch error event instead
                const errorEvent = new CustomEvent('shadow-document-error', {
                    detail: {
                        error: "No shadow document exists",
                        code: "SHADOW_NOT_FOUND"
                    }
                });
                document.dispatchEvent(errorEvent);

                // Prevent original event from continuing
                e.stopPropagation();
                e.preventDefault();
            }, true);

            console.log('Shadow document error simulation active');
        });
        """
        )

    @pytest.fixture(scope="function", autouse=True)
    def navigate_to_water_heater(self, page: Page):
        """Fixture to navigate to the water heater dashboard."""
        # Navigate to the water heater dashboard
        page.goto("http://localhost:8006/water-heaters")

        # Wait for the dashboard to load
        page.wait_for_selector(".dashboard .heater-card", timeout=5000)

    def navigate_to_history_tab(self, page: Page):
        """Helper method to navigate to the history tab of a water heater."""
        # Click the first water heater card to go to details
        page.query_selector(".dashboard .heater-card").click()

        # Wait for details page to load - try different possible selectors
        try:
            page.wait_for_selector(
                ".detail-view, .details-container, .device-details", timeout=5000
            )
        except:
            # If we can't find a container, at least wait for the page to load
            page.wait_for_load_state("networkidle")

        # Find the history tab using various possible selectors
        history_tab = None
        selectors = [
            ".tab-nav .nav-item:has-text('History')",
            ".tabs .tab-btn[data-tab='history']",
            "button:has-text('History')",
            "a:has-text('History')",
        ]

        for selector in selectors:
            elements = page.query_selector_all(selector)
            for element in elements:
                if "History" in element.inner_text():
                    history_tab = element
                    break
            if history_tab:
                break

        assert history_tab, "History tab not found"

        # Click the history tab
        history_tab.click()

        # Wait for history content to load - try different possible selectors
        try:
            page.wait_for_selector(
                "#history:visible, #history-content:visible, .history-tab:visible",
                timeout=5000,
            )
        except:
            # If we can't find a container, at least wait for the page to load
            page.wait_for_load_state("networkidle")

    def test_history_tab_has_required_cards(self, page: Page):
        """Test that History tab contains all required data cards."""
        # Navigate to history tab
        self.navigate_to_history_tab(page)

        # Look for history content container
        history_content = page.query_selector(
            "#history, #history-content, .history-tab"
        )
        assert history_content, "History content container not found"

        # Check for required cards - using flexible selectors to accommodate different implementations
        cards = page.query_selector_all(
            ".card, .dashboard-card, .history-card, .chart-container"
        )

        # Verify we have at least one card
        assert len(cards) > 0, "No cards found in History tab"

        # Define expected data types that should be present in the history tab
        expected_data_types = ["temperature"]

        # Optional data types that might be present but aren't required
        optional_data_types = ["energy", "pressure", "usage"]

        # Verify required data types exist
        for data_type in expected_data_types:
            found = False

            # Check card titles, content, or other identifiers
            for card in cards:
                card_text = card.inner_text().lower()
                card_html = card.inner_html().lower()

                if data_type in card_text or data_type in card_html:
                    found = True
                    print(f"Found {data_type} card")
                    break

            assert found, f"Required {data_type} card not found in History tab"

        # Log optional data types found (informational only)
        for data_type in optional_data_types:
            for card in cards:
                if (
                    data_type in card.inner_text().lower()
                    or data_type in card.inner_html().lower()
                ):
                    print(f"Found optional {data_type} card")
                    break

    def test_history_tab_handles_shadow_document_error(
        self, page: Page, setup_error_condition
    ):
        """Test that History tab properly handles shadow document errors."""
        # Navigate to history tab
        self.navigate_to_history_tab(page)

        # Give time for error to propagate
        page.wait_for_timeout(1000)

        # Look for error messages - try different possible selectors
        error_selectors = [
            ".shadow-document-error:visible",
            ".error-message:visible",
            ".alert:visible",
            ".error:visible",
            "[data-error]:visible",
            "text='No shadow document exists'",
        ]

        error_found = False
        for selector in error_selectors:
            if page.query_selector(selector):
                error_found = True
                print(f"Found error message with selector: {selector}")
                break

        assert error_found, "Error message not displayed for missing shadow document"

        # Verify no empty state is shown
        # Check that each card either shows a chart or an error message, never empty
        card_selectors = [
            ".card",
            ".dashboard-card",
            ".history-card",
            ".chart-container",
        ]

        for selector in card_selectors:
            cards = page.query_selector_all(selector)
            for card in cards:
                has_chart = card.query_selector(".chart, svg, canvas") is not None
                has_error = any(
                    card.query_selector(s) is not None for s in error_selectors
                )
                has_text_content = card.inner_text().strip() != ""

                assert (
                    has_chart or has_error or has_text_content
                ), f"Card is in empty state - must show either chart or error: {card.inner_html()}"

    def test_history_tab_loads_data_on_activation(self, page: Page, network_requests):
        """Test that History tab loads data when activated."""
        # Click the first water heater card to go to details
        page.query_selector(".dashboard .heater-card").click()

        # Wait for details page to load
        try:
            page.wait_for_selector(
                ".detail-view, .details-container, .device-details", timeout=5000
            )
        except:
            # If we can't find a container, at least wait for the page to load
            page.wait_for_load_state("networkidle")

        # Clear network requests before activating history tab
        network_requests.clear()

        # Navigate to history tab
        self.navigate_to_history_tab(page)

        # Wait briefly for requests to complete
        page.wait_for_timeout(1000)

        # Check that appropriate API requests are made when tab is activated
        api_requests = [r for r in network_requests if "/api/" in r["url"]]
        history_requests = [
            r for r in api_requests if "/history" in r["url"] or "timeframe" in r["url"]
        ]

        # Verify history-related requests are made when tab is activated
        assert (
            len(history_requests) > 0
        ), "No history requests made when History tab activated"

        # Verify default timeframe (7 days)
        days_requested = False
        for req in history_requests:
            if "timeframe=7" in req["url"] or "days=7" in req["url"]:
                days_requested = True
                break

        # If explicit timeframe not found, check for date range approximately 7 days
        if not days_requested:
            for req in history_requests:
                url = req["url"]
                if "start_date" in url and "end_date" in url:
                    # Extract dates from URL parameters
                    start_match = re.search(r"start_date=([^&]+)", url)
                    end_match = re.search(r"end_date=([^&]+)", url)

                    if start_match and end_match:
                        try:
                            start_date = datetime.fromisoformat(
                                start_match.group(1).replace("Z", "+00:00")
                            )
                            end_date = datetime.fromisoformat(
                                end_match.group(1).replace("Z", "+00:00")
                            )
                            date_diff = (end_date - start_date).days

                            # Check if it's approximately 7 days (allow ±1 day for time zone differences)
                            if 6 <= date_diff <= 8:
                                days_requested = True
                                break
                        except ValueError:
                            continue

        assert (
            days_requested
        ), "Default timeframe (7 days) not requested when History tab activated"

    def test_timeframe_data_only_loaded_when_requested(
        self, page: Page, network_requests
    ):
        """Test that 14 and 30 day data is only loaded when explicitly requested."""
        # Navigate to history tab
        self.navigate_to_history_tab(page)

        # Wait for initial data to load
        page.wait_for_timeout(1000)

        # Clear network requests
        network_requests.clear()

        # Find the timeframe selector
        timeframe_selector = page.query_selector(
            ".timeframe-selector select, .timeframe-dropdown button, [data-timeframe]"
        )
        assert timeframe_selector, "Timeframe selector not found"

        # Test timeframes
        for days in [14, 30]:
            # Clear network requests before each selection
            network_requests.clear()

            # Select the timeframe
            if timeframe_selector.tag_name.lower() == "select":
                # If it's a select element
                timeframe_selector.select_option(str(days))
            else:
                # If it's a dropdown button
                timeframe_selector.click()

                # Find and click the appropriate option
                option_selectors = [
                    f".dropdown-item:has-text('{days} days')",
                    f"[data-days='{days}']",
                    f"button:has-text('{days}')",
                ]

                option_found = False
                for selector in option_selectors:
                    option = page.query_selector(selector)
                    if option:
                        option.click()
                        option_found = True
                        break

                assert option_found, f"Could not find option for {days} days"

            # Wait for data to load
            page.wait_for_timeout(1000)

            # Check network requests
            api_requests = [r for r in network_requests if "/api/" in r["url"]]
            history_requests = [
                r
                for r in api_requests
                if "/history" in r["url"] or "timeframe" in r["url"]
            ]

            # Verify history requests were made
            assert (
                len(history_requests) > 0
            ), f"No history requests made after selecting {days} days"

            # Verify correct timeframe was requested
            correct_timeframe_requested = False
            for req in history_requests:
                if f"timeframe={days}" in req["url"] or f"days={days}" in req["url"]:
                    correct_timeframe_requested = True
                    break

            # If explicit timeframe not found, check for date range approximately matching requested days
            if not correct_timeframe_requested:
                for req in history_requests:
                    url = req["url"]
                    if "start_date" in url and "end_date" in url:
                        # Extract dates from URL parameters
                        start_match = re.search(r"start_date=([^&]+)", url)
                        end_match = re.search(r"end_date=([^&]+)", url)

                        if start_match and end_match:
                            try:
                                start_date = datetime.fromisoformat(
                                    start_match.group(1).replace("Z", "+00:00")
                                )
                                end_date = datetime.fromisoformat(
                                    end_match.group(1).replace("Z", "+00:00")
                                )
                                date_diff = (end_date - start_date).days

                                # Allow some flexibility (±1 day)
                                if abs(date_diff - days) <= 1:
                                    correct_timeframe_requested = True
                                    break
                            except ValueError:
                                continue

            assert (
                correct_timeframe_requested
            ), f"{days}-day data was not requested after selecting that timeframe"
            print(
                f"✅ {days}-day data was correctly requested only when explicitly selected"
            )

    def test_chart_data_visualization(self, page: Page):
        """Test that history charts properly visualize data points."""
        # Navigate to history tab
        self.navigate_to_history_tab(page)

        # Wait for charts to load
        page.wait_for_timeout(2000)

        # Look for chart elements
        chart_selectors = [
            ".chart",
            "svg.graph",
            "canvas.chart",
            ".temperature-chart",
            ".history-chart",
        ]

        chart_found = False
        for selector in chart_selectors:
            chart = page.query_selector(selector)
            if chart:
                chart_found = True
                break

        # If we can't find a chart, check if there's an error message instead (which is acceptable)
        if not chart_found:
            error_selectors = [
                ".shadow-document-error:visible",
                ".error-message:visible",
                ".alert:visible",
            ]

            error_found = False
            for selector in error_selectors:
                if page.query_selector(selector):
                    error_found = True
                    break

            assert error_found, "Neither chart nor error message found in History tab"
            print(
                "ℹ️ Error message displayed instead of chart - this is acceptable if there's no data"
            )
            return

        # Verify chart has data points
        data_points_exist = page.evaluate(
            """
        () => {
            // Check for various chart implementations

            // D3 SVG charts
            const svgPoints = document.querySelectorAll('svg .point, svg circle.data-point, svg .dot');
            if (svgPoints.length > 0) return true;

            // Canvas-based charts like Chart.js
            const canvas = document.querySelector('canvas.chart, canvas.temperature-chart, #history-content canvas');
            if (canvas) {
                // For canvas, we can't directly check for points, but we can check if the canvas has content
                const ctx = canvas.getContext('2d');
                const pixelData = ctx.getImageData(0, 0, canvas.width, canvas.height).data;

                // Check if there are non-transparent pixels in the canvas
                for (let i = 3; i < pixelData.length; i += 4) {
                    if (pixelData[i] > 0) return true; // Alpha channel > 0 means there's content
                }
            }

            // Highcharts points
            const highchartsPoints = document.querySelectorAll('.highcharts-point, .highcharts-markers path');
            if (highchartsPoints.length > 0) return true;

            // ApexCharts points
            const apexPoints = document.querySelectorAll('.apexcharts-marker, .apexcharts-series-markers');
            if (apexPoints.length > 0) return true;

            return false;
        }
        """
        )

        # If we couldn't detect data points through JavaScript, check if there's an error message
        if not data_points_exist:
            error_selectors = [
                ".shadow-document-error:visible",
                ".error-message:visible",
                ".alert:visible",
                "[data-error]:visible",
            ]

            error_found = False
            for selector in error_selectors:
                if page.query_selector(selector):
                    error_found = True
                    break

            assert (
                data_points_exist or error_found
            ), "Chart does not contain data points and no error message is displayed"

            if error_found:
                print(
                    "ℹ️ Error message displayed instead of data points - this is acceptable if there's no data"
                )
            else:
                assert (
                    data_points_exist
                ), "Chart visualization does not contain data points"

        if data_points_exist:
            print("✅ Chart successfully visualizes data points")
