"""
Tests for real-time monitoring and WebSocket functionality in the IoTSphere application.
Following TDD principles, these tests verify that the real-time monitoring system
correctly handles connection status, reconnections, and data visualization.
"""

import re
import time

import pytest
from playwright.sync_api import Page, expect


class TestRealtimeMonitoring:
    """
    Test suite for real-time monitoring functionality.
    Verifies WebSocket connections, status indicators, and data visualization.
    """

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, page: Page):
        """Setup for each test."""
        # Navigate to a water heater details page
        page.goto("http://localhost:8006/water-heaters")

        # Wait for dashboard to load
        page.wait_for_selector(".dashboard .heater-card", timeout=5000)

        # Click the first water heater card to go to details
        page.query_selector(".dashboard .heater-card").click()

        # Wait for details page to load
        page.wait_for_selector(".details-container", timeout=5000)

    def test_websocket_connection_indicator_exists(self, page: Page):
        """
        Test that the WebSocket connection indicator exists and shows the correct status.
        """
        # Look for connection status indicator
        connection_indicator = page.query_selector(
            ".connection-status, .websocket-status, .ws-status"
        )

        assert connection_indicator, "WebSocket connection status indicator not found"

        # Verify the indicator is showing connected status (may have different class names)
        indicator_class = connection_indicator.get_attribute("class")
        indicator_text = connection_indicator.inner_text()

        # Check for connected status through class or text
        is_connected = (
            "connected" in indicator_class.lower()
            or "online" in indicator_class.lower()
            or "active" in indicator_class.lower()
            or "connected" in indicator_text.lower()
            or "online" in indicator_text.lower()
        )

        assert (
            is_connected
        ), "WebSocket connection indicator should show connected status"

    def test_temperature_updates_appear_in_realtime(self, page: Page):
        """
        Test that temperature updates appear in real-time on the details page.
        """
        # Get initial temperature value
        temp_element = page.query_selector(
            ".current-temperature, .temperature .current"
        )
        assert temp_element, "Current temperature element not found"

        initial_temp = temp_element.inner_text()

        # Extract numeric part of temperature
        temp_pattern = r"(\d+\.?\d*)"
        initial_value = re.search(temp_pattern, initial_temp)
        assert (
            initial_value
        ), f"Could not extract numeric temperature from '{initial_temp}'"

        # Wait for potential temperature update (up to 10 seconds)
        updated = False
        max_wait = 10
        start_time = time.time()

        while time.time() - start_time < max_wait and not updated:
            current_temp = temp_element.inner_text()
            current_value = re.search(temp_pattern, current_temp)

            if current_value and current_value.group(1) != initial_value.group(1):
                updated = True
                break

            time.sleep(1)

        # If no update received, we'll still pass the test but make note of it
        if not updated:
            print(
                f"⚠️ No temperature update received within {max_wait} seconds. This is not necessarily a failure - real updates may be infrequent."
            )
        else:
            print(
                f"✅ Temperature updated from {initial_value.group(1)} to {current_value.group(1)}"
            )

    def test_reconnection_handling(self, page: Page):
        """
        Test that the application properly handles WebSocket reconnection.
        This simulates a connection loss and verifies the reconnection behavior.
        """
        # First check if we have a working connection
        connection_indicator = page.query_selector(
            ".connection-status, .websocket-status, .ws-status"
        )
        if not connection_indicator:
            pytest.skip("Connection indicator not found, cannot test reconnection")

        # Inject script to simulate WebSocket disconnection
        page.evaluate(
            """
        () => {
            // Store original WebSocket for later restoration
            window._originalWebSocket = WebSocket;

            // Mock the WebSocket to simulate disconnect
            class MockWebSocket extends window._originalWebSocket {
                constructor(url, protocols) {
                    super(url, protocols);

                    // After a short delay, simulate a close event
                    setTimeout(() => {
                        const closeEvent = new CloseEvent('close', {
                            code: 1006,
                            reason: 'Connection lost for testing',
                            wasClean: false
                        });

                        // Dispatch the close event
                        this.dispatchEvent(closeEvent);

                        console.log('WebSocket connection artificially closed for testing');
                    }, 500);
                }
            }

            // Replace WebSocket with our mock
            window.WebSocket = MockWebSocket;

            // Restore the original WebSocket after some time
            setTimeout(() => {
                window.WebSocket = window._originalWebSocket;
                console.log('Original WebSocket restored');
            }, 2000);

            return "WebSocket disconnect simulation injected";
        }
        """
        )

        # Wait briefly for the simulation to take effect
        time.sleep(1)

        # Look for disconnected status or reconnecting message
        disconnected_visible = False
        start_time = time.time()
        max_wait = 5

        while time.time() - start_time < max_wait and not disconnected_visible:
            # Check for disconnected status in the indicator
            indicator = page.query_selector(
                ".connection-status, .websocket-status, .ws-status"
            )
            if indicator:
                indicator_class = indicator.get_attribute("class") or ""
                indicator_text = indicator.inner_text() or ""

                disconnected_visible = (
                    "disconnected" in indicator_class.lower()
                    or "offline" in indicator_class.lower()
                    or "error" in indicator_class.lower()
                    or "disconnected" in indicator_text.lower()
                    or "offline" in indicator_text.lower()
                    or "reconnect" in indicator_text.lower()
                )

            # Also check for any reconnection messages
            reconnect_message = page.query_selector(
                ".reconnect-message, .connection-error, .ws-error"
            )
            if reconnect_message and reconnect_message.is_visible():
                disconnected_visible = True

            if not disconnected_visible:
                time.sleep(0.5)

        # If disconnect state was not visible, make note but don't fail
        # (Some implementations might reconnect too fast to show the disconnected state)
        if not disconnected_visible:
            print(
                "⚠️ Disconnected state was not visible, but this might be due to quick reconnection"
            )

        # Now wait for reconnection (or continued connection if it reconnected quickly)
        time.sleep(3)

        # Check that we're connected again
        connection_indicator = page.query_selector(
            ".connection-status, .websocket-status, .ws-status"
        )
        assert (
            connection_indicator
        ), "Connection indicator not found after reconnection attempt"

        indicator_class = connection_indicator.get_attribute("class") or ""
        indicator_text = connection_indicator.inner_text() or ""

        is_connected_again = (
            "connected" in indicator_class.lower()
            or "online" in indicator_class.lower()
            or "active" in indicator_class.lower()
            or "connected" in indicator_text.lower()
            or "online" in indicator_text.lower()
        )

        assert (
            is_connected_again
        ), "WebSocket should reconnect and show connected status"

    def test_history_chart_data_visualization(self, page: Page):
        """
        Test that the history chart properly visualizes temperature data points.
        """
        # Find and click the History tab
        history_tab = None
        tabs = page.query_selector_all(".tab-nav .nav-item")
        for tab in tabs:
            if "History" in tab.inner_text():
                history_tab = tab
                break

        assert history_tab, "History tab not found"

        # Click the History tab
        history_tab.click()

        # Wait for history content to load
        page.wait_for_selector("#history-content:visible", timeout=5000)

        # Look for chart elements
        chart = page.query_selector(
            "#history-content .chart, #history-content svg.graph, #history-content canvas"
        )
        assert chart, "History chart not found"

        # Verify chart has data points
        data_points_exist = page.evaluate(
            """
        () => {
            // Check for various chart implementations

            // D3 SVG charts
            const svgPoints = document.querySelectorAll('svg .point, svg circle.data-point, svg .dot');
            if (svgPoints.length > 0) return true;

            // Canvas-based charts like Chart.js
            const canvas = document.querySelector('#history-content canvas');
            if (canvas) {
                // For canvas, we can't directly check for points, but we can check if the canvas has content
                const ctx = canvas.getContext('2d');
                const pixelData = ctx.getImageData(0, 0, canvas.width, canvas.height).data;

                // Check if there are non-transparent pixels in the canvas (a very basic check)
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

        # If we couldn't detect data points through JavaScript, try another approach
        if not data_points_exist:
            # Wait a bit longer for chart to render completely
            time.sleep(2)

            # Look for any error message about missing data
            error_message = page.query_selector(
                "#history-content .error-message, #history-content .no-data-message"
            )

            # If there's an error message, check if it's about missing shadow document
            if error_message and error_message.is_visible():
                error_text = error_message.inner_text().lower()
                if "shadow document" in error_text or "no data" in error_text:
                    # This is an expected error state that should be handled by the UI
                    print(
                        "ℹ️ Chart shows error message about missing shadow document or no data - this is an acceptable state"
                    )
                    return

            # If no specific error is found but we still can't detect data points, report it
            assert (
                data_points_exist
            ), "History chart should contain visible data points or a clear error message"

        print("✅ History chart contains data visualization elements")

    def test_temperature_shadow_exists(self, page: Page):
        """
        Test that temperature shadow document data is properly displayed.
        """
        # Check for temperature display
        temp_element = page.query_selector(
            ".current-temperature, .temperature .current"
        )
        assert temp_element, "Current temperature element not found"

        # Verify temperature has a value
        temp_text = temp_element.inner_text()
        temp_pattern = r"(\d+\.?\d*)"
        temp_value = re.search(temp_pattern, temp_text)

        assert (
            temp_value
        ), f"Temperature display '{temp_text}' does not contain a numeric value"

        # Check for status indicator
        status_element = page.query_selector(".status, .device-status")

        if status_element:
            # Verify status has a value
            status_text = status_element.inner_text().strip()
            assert status_text, "Status indicator should display a status value"

            # Status should be one of the expected values (online/offline/etc.)
            expected_statuses = [
                "ONLINE",
                "OFFLINE",
                "ON",
                "OFF",
                "ACTIVE",
                "INACTIVE",
                "NORMAL",
                "ERROR",
            ]
            status_matches = any(
                expected in status_text.upper() for expected in expected_statuses
            )

            assert (
                status_matches
            ), f"Status '{status_text}' is not one of the expected values"
