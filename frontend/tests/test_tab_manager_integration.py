"""
Tests for the TabManager system in the IoTSphere application.
Following TDD principles, these tests verify that the TabManager is properly
handling tab activation, component lifecycle, and visibility.
"""

import time

import pytest
from playwright.sync_api import Page, expect


class TestTabManagerIntegration:
    """
    Test suite for the TabManager integration with dashboard components.
    Verifies proper component registration, event propagation, and tab
    activation/deactivation behavior.
    """

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, page: Page):
        """Setup for each test."""
        # Navigate to a water heater details page where tabs are used
        page.goto("http://localhost:8006/water-heaters")

        # Wait for dashboard to load
        page.wait_for_selector(".dashboard .heater-card", timeout=5000)

        # Click the first water heater card to go to details
        page.query_selector(".dashboard .heater-card").click()

        # Wait for details page to load
        page.wait_for_selector(".details-container", timeout=5000)

    def test_tab_visibility_is_mutually_exclusive(self, page: Page):
        """
        Test that only one tab content area is visible at a time.
        This verifies the TabManager is correctly setting visibility.
        """
        # Get all tab content elements
        tab_contents = [
            "#details-content",
            "#history-content",
            "#operations-content",
            "#predictions-content",
        ]

        # Verify all tabs exist
        for selector in tab_contents:
            assert page.query_selector(selector), f"Tab content {selector} not found"

        # Check initial state (should be on details tab by default)
        assert page.query_selector(
            "#details-content"
        ).is_visible(), "Details tab should be visible initially"

        # Verify other tabs are not visible
        for selector in [s for s in tab_contents if s != "#details-content"]:
            assert not page.query_selector(
                selector
            ).is_visible(), f"Tab {selector} should not be visible initially"

        # Click on each tab and verify correct visibility
        tab_nav_items = page.query_selector_all(".tab-nav .nav-item")
        for i, tab in enumerate(tab_nav_items):
            # Skip if this is the Details tab (already tested above)
            if i == 0:
                continue

            # Click the tab
            tab.click()
            time.sleep(0.5)  # Allow for tab transition

            # Determine which content area should be visible
            visible_selector = tab_contents[i] if i < len(tab_contents) else None
            if not visible_selector:
                continue

            # Verify the correct tab is visible
            assert page.query_selector(
                visible_selector
            ).is_visible(), f"Tab {visible_selector} should be visible after clicking"

            # Verify other tabs are not visible
            for selector in [s for s in tab_contents if s != visible_selector]:
                assert not page.query_selector(
                    selector
                ).is_visible(), f"Tab {selector} should not be visible when {visible_selector} is active"

    def test_active_tab_nav_item_has_active_class(self, page: Page):
        """Test that the active tab navigation item has the 'active' class."""
        # Check initial state (should be on details tab by default)
        tab_nav_items = page.query_selector_all(".tab-nav .nav-item")

        # Verify the first tab has the active class
        assert "active" in tab_nav_items[0].get_attribute(
            "class"
        ), "Details tab should have active class initially"

        # Click each tab and verify the active class moves
        for i, tab in enumerate(tab_nav_items):
            # Skip if this is the Details tab (already verified above)
            if i == 0:
                continue

            # Click the tab
            tab.click()
            time.sleep(0.5)  # Allow for tab transition

            # Verify the clicked tab has the active class
            assert "active" in tab.get_attribute(
                "class"
            ), f"Tab {i} should have active class when clicked"

            # Verify other tabs do not have the active class
            for j, other_tab in enumerate(tab_nav_items):
                if j != i:
                    assert "active" not in other_tab.get_attribute(
                        "class"
                    ), f"Tab {j} should not have active class when tab {i} is active"

    def test_history_tab_reloads_data_when_activated(self, page: Page):
        """
        Test that the History tab reloads its data when activated.
        This verifies the TabManager's component reload mechanism.
        """
        # First find the History tab
        history_tab = None
        tabs = page.query_selector_all(".tab-nav .nav-item")
        for tab in tabs:
            if "History" in tab.inner_text():
                history_tab = tab
                break

        assert history_tab, "History tab not found"

        # Click the History tab to activate it
        history_tab.click()

        # Wait for history content to load
        page.wait_for_selector("#history-content:visible", timeout=5000)

        # Check if a loading indicator appears or disappears, indicating reload
        # If there's a loading indicator, wait for it to appear and disappear
        try:
            page.wait_for_selector(
                ".history-loading:visible, .loading-indicator:visible", timeout=2000
            )
            page.wait_for_selector(
                ".history-loading:visible, .loading-indicator:visible",
                state="hidden",
                timeout=5000,
            )
        except:
            # If no loading indicator is found, look for chart elements
            page.wait_for_selector(
                "#history-content .chart, #history-content .graph", timeout=5000
            )

        # Look for history data elements
        history_elements = page.query_selector_all(
            "#history-content .chart, #history-content .temperature-history, #history-content .graph"
        )
        assert len(history_elements) > 0, "History tab should load data when activated"

    def test_operations_tab_reloads_data_when_activated(self, page: Page):
        """
        Test that the Operations tab reloads its data when activated.
        This verifies another component's integration with TabManager.
        """
        # First find the Operations tab
        operations_tab = None
        tabs = page.query_selector_all(".tab-nav .nav-item")
        for tab in tabs:
            if "Operations" in tab.inner_text():
                operations_tab = tab
                break

        assert operations_tab, "Operations tab not found"

        # Click the Operations tab to activate it
        operations_tab.click()

        # Wait for operations content to load
        page.wait_for_selector("#operations-content:visible", timeout=5000)

        # Look for operations-specific elements
        try:
            # First try to find gauges which might be in the new operations implementation
            page.wait_for_selector(
                "#operations-content .gauge, #operations-content .chart, #operations-content .status-card",
                timeout=5000,
            )
        except:
            # If those aren't found, check for any operations-related content
            page.wait_for_selector(
                "#operations-content .data-row, #operations-content .control-panel",
                timeout=5000,
            )

        # Verify some operations-specific content is visible
        operations_elements = page.query_selector_all(
            "#operations-content .gauge, #operations-content .chart, "
            + "#operations-content .status-card, #operations-content .data-row, "
            + "#operations-content .control-panel"
        )
        assert (
            len(operations_elements) > 0
        ), "Operations tab should load data when activated"

    def test_switching_back_to_previously_loaded_tab_preserves_state(self, page: Page):
        """
        Test that switching back to a previously loaded tab preserves its state.
        This verifies the TabManager correctly manages component state.
        """
        # First navigate to History tab
        history_tab = None
        tabs = page.query_selector_all(".tab-nav .nav-item")
        for tab in tabs:
            if "History" in tab.inner_text():
                history_tab = tab
                break

        assert history_tab, "History tab not found"
        history_tab.click()

        # Wait for history content to load
        page.wait_for_selector("#history-content:visible", timeout=5000)

        # Check for any selectable elements (like timeframe dropdown) and change settings
        timeframe_selector = page.query_selector(
            ".timeframe-selector select, .timeframe-dropdown"
        )

        # If there's a timeframe selector, change it to 30 days
        if timeframe_selector:
            # Might be a select element or a dropdown button
            if timeframe_selector.get_attribute("tagName") == "SELECT":
                # Select element
                timeframe_selector.select_option("30")
            else:
                # Dropdown button
                timeframe_selector.click()
                # Find and click 30 days option
                day_option = page.query_selector(
                    ".dropdown-menu .dropdown-item:text('30 days')"
                )
                if day_option:
                    day_option.click()

        # Now switch to another tab
        operations_tab = None
        for tab in tabs:
            if "Operations" in tab.inner_text():
                operations_tab = tab
                break

        assert operations_tab, "Operations tab not found"
        operations_tab.click()

        # Wait for operations content to load
        page.wait_for_selector("#operations-content:visible", timeout=5000)

        # Now switch back to history tab
        history_tab.click()

        # Wait for history content to become visible again
        page.wait_for_selector("#history-content:visible", timeout=5000)

        # If we had a timeframe selector and changed it, verify it's still at 30 days
        if timeframe_selector:
            if timeframe_selector.get_attribute("tagName") == "SELECT":
                # Check the select element value
                selected_value = page.evaluate(
                    """
                    () => {
                        const selector = document.querySelector('.timeframe-selector select');
                        return selector ? selector.value : null;
                    }
                """
                )
                if selected_value:
                    assert (
                        selected_value == "30"
                    ), "Timeframe selection should be preserved when returning to History tab"
            else:
                # Check for visual indication of 30 days selection
                selected_text = page.evaluate(
                    """
                    () => {
                        const dropdown = document.querySelector('.timeframe-dropdown .dropdown-toggle');
                        return dropdown ? dropdown.textContent : null;
                    }
                """
                )
                if selected_text:
                    assert (
                        "30" in selected_text
                    ), "Timeframe selection should be preserved when returning to History tab"
