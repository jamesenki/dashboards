"""
Tests for UI performance and behavior in the IoTSphere application.
These tests focus on actual user-facing behavior rather than just API responses.
"""

import re
import time

import pytest
from playwright.sync_api import Page, TimeoutError, expect


class TestUIPerformance:
    """
    Test suite for UI performance and behavior.
    Verifies that UI components load within acceptable timeframes and function properly.
    """

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, page: Page):
        """Setup for each test."""
        # Navigate to the water heater dashboard
        page.goto("http://localhost:8006/water-heaters")

        # Wait for dashboard to load
        page.wait_for_selector("#water-heater-list .dashboard", timeout=5000)

    def test_dashboard_loads_within_threshold(self, page: Page):
        """Test that the main dashboard loads within 3 seconds."""
        # Clear page and reload with timing
        page.goto("about:blank")

        # Start timing
        start_time = time.time()

        # Load the dashboard
        page.goto("http://localhost:8006/water-heaters")

        # Wait for essential content to appear
        page.wait_for_selector(".dashboard .heater-card", timeout=5000)

        # Calculate load time
        load_time = time.time() - start_time

        # Assert load time is acceptable (under 3 seconds)
        assert (
            load_time < 3.0
        ), f"Dashboard took {load_time:.2f}s to load (threshold: 3.0s)"

        # Log the actual time for reference
        print(f"Dashboard loaded in {load_time:.2f}s")

    def test_details_page_loads_within_threshold(self, page: Page):
        """Test that water heater details page loads within 3 seconds."""
        # Get the first heater card
        cards = page.query_selector_all(".dashboard .heater-card")
        assert len(cards) > 0, "No water heater cards found"

        # Get the heater ID from the card
        first_card = cards[0]
        heater_id = first_card.get_attribute("data-id")

        if not heater_id:
            # If data-id attribute isn't available, click the card to navigate to details
            first_card.click()
            # Extract ID from URL
            url_pattern = r"/water-heaters/([^/]+)"
            matches = re.search(url_pattern, page.url)
            assert matches, "Failed to extract heater ID from URL"
            heater_id = matches.group(1)
            # Go back to dashboard
            page.goto("http://localhost:8006/water-heaters")
            page.wait_for_selector(".dashboard .heater-card", timeout=5000)

        # Clear page and reload with timing
        page.goto("about:blank")

        # Start timing
        start_time = time.time()

        # Navigate directly to details page
        page.goto(f"http://localhost:8006/water-heaters/{heater_id}")

        # Wait for essential content to appear
        page.wait_for_selector(".details-container", timeout=5000)

        # Calculate load time
        load_time = time.time() - start_time

        # Assert load time is acceptable (under 3 seconds)
        assert (
            load_time < 3.0
        ), f"Details page took {load_time:.2f}s to load (threshold: 3.0s)"

        # Log the actual time for reference
        print(f"Details page loaded in {load_time:.2f}s")

    def test_tab_switching_response_time(self, page: Page):
        """Test that switching tabs responds within 1 second."""
        # Navigate to a water heater details page
        cards = page.query_selector_all(".dashboard .heater-card")
        assert len(cards) > 0, "No water heater cards found"
        cards[0].click()

        # Wait for details page to load
        page.wait_for_selector(".details-container", timeout=5000)

        # Make sure we have tabs
        tabs = page.query_selector_all(".tab-nav .nav-item")
        assert len(tabs) >= 3, "Expected at least 3 tabs (Details, History, Operations)"

        # Find the operations tab
        operations_tab = None
        for tab in tabs:
            if "Operations" in tab.inner_text():
                operations_tab = tab
                break

        assert operations_tab, "Operations tab not found"

        # Click the operations tab and measure response time
        start_time = time.time()
        operations_tab.click()

        try:
            # Wait for operations content to be visible
            page.wait_for_selector("#operations-content:visible", timeout=3000)
            response_time = time.time() - start_time

            # Assert response time is acceptable (under 1 second)
            assert (
                response_time < 1.0
            ), f"Tab switching took {response_time:.2f}s (threshold: 1.0s)"

            # Log the actual time for reference
            print(f"Tab switched in {response_time:.2f}s")
        except TimeoutError:
            # If timeout, fail the test
            assert False, "Operations tab content didn't become visible within timeout"

    def test_ui_elements_become_interactive(self, page: Page):
        """Test that UI elements become interactive shortly after page load."""
        # Navigate to a water heater details page
        cards = page.query_selector_all(".dashboard .heater-card")
        assert len(cards) > 0, "No water heater cards found"
        cards[0].click()

        # Wait for details page to load
        page.wait_for_selector(".details-container", timeout=5000)

        # Find temperature control input
        temp_control = page.query_selector("input[type='range']")
        assert temp_control, "Temperature control slider not found"

        # Measure time until element is interactive
        start_time = time.time()

        # Try to interact with the element
        temp_control.click()

        # Check if we can change the value
        original_value = temp_control.get_attribute("value")
        temp_control.fill(str(int(original_value) + 1))

        # Verify the value changed
        new_value = temp_control.get_attribute("value")
        assert (
            new_value != original_value
        ), "Failed to interact with temperature control"

        # Calculate interaction time
        interaction_time = time.time() - start_time

        # Assert interaction time is acceptable (under 1 second)
        assert (
            interaction_time < 1.0
        ), f"UI became interactive in {interaction_time:.2f}s (threshold: 1.0s)"

        # Log the actual time for reference
        print(f"UI became interactive in {interaction_time:.2f}s")
