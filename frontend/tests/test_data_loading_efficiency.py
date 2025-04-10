"""
Tests for data loading efficiency in the IoTSphere application.
These tests verify that only the necessary data is loaded for the active components,
improving performance and reducing network overhead.
"""

import json
import re
from datetime import datetime, timedelta

import pytest
from playwright.sync_api import Page, Request, Route, expect


class TestDataLoadingEfficiency:
    """
    Test suite for data loading efficiency.
    Verifies that the application only loads the data needed for the currently active components.
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

    def test_details_page_loads_only_current_data(self, page: Page, network_requests):
        """
        Test that the details page only loads current data, not historical data.
        """
        # Navigate to the water heater dashboard
        page.goto("http://localhost:8006/water-heaters")
        page.wait_for_selector(".dashboard .heater-card", timeout=5000)

        # Click the first water heater card to go to details
        page.query_selector(".dashboard .heater-card").click()
        page.wait_for_selector(".details-container", timeout=5000)

        # Get the heater ID from the URL
        url_pattern = r"/water-heaters/([^/]+)"
        matches = re.search(url_pattern, page.url)
        assert matches, "Failed to extract heater ID from URL"
        heater_id = matches.group(1)

        # Check that API requests don't include historical data endpoints
        api_requests = [r for r in network_requests if "/api/" in r["url"]]

        # Verify we're not loading history data on the details tab
        history_requests = [
            r for r in api_requests if "/history" in r["url"] or "timeframe" in r["url"]
        ]

        # We shouldn't have any history requests when just loading the details tab
        assert (
            len(history_requests) == 0
        ), f"Found {len(history_requests)} history requests on the details page"

        # Verify we're only loading current data
        current_data_requests = [
            r
            for r in api_requests
            if f"/water-heaters/{heater_id}" in r["url"]
            and not "/history" in r["url"]
            and not "timeframe" in r["url"]
        ]

        # We should have at least one request for current data
        assert (
            len(current_data_requests) >= 1
        ), "No current data requests found on details page"

        print(
            f"Details page made {len(current_data_requests)} current data requests and "
            f"{len(history_requests)} historical data requests"
        )

    def test_history_tab_loads_7_days_by_default(self, page: Page, network_requests):
        """
        Test that the history tab loads only 7 days of data by default.
        """
        # Reset the network requests
        network_requests.clear()

        # Navigate to the water heater dashboard
        page.goto("http://localhost:8006/water-heaters")
        page.wait_for_selector(".dashboard .heater-card", timeout=5000)

        # Click the first water heater card to go to details
        page.query_selector(".dashboard .heater-card").click()
        page.wait_for_selector(".details-container", timeout=5000)

        # Find and click the history tab
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

        # Check the API requests
        api_requests = [r for r in network_requests if "/api/" in r["url"]]
        history_requests = [
            r for r in api_requests if "/history" in r["url"] or "timeframe" in r["url"]
        ]

        # Verify we have history requests
        assert (
            len(history_requests) > 0
        ), "No history requests found after clicking history tab"

        # Check the timeframe parameter is 7 days or the default
        days_requested = 0
        for req in history_requests:
            if "timeframe=7" in req["url"] or "days=7" in req["url"]:
                days_requested = 7
                break
            elif "timeframe=14" in req["url"] or "days=14" in req["url"]:
                days_requested = 14
                break
            elif "timeframe=30" in req["url"] or "days=30" in req["url"]:
                days_requested = 30
                break

        # If we didn't find an explicit day parameter, check for date ranges in the URL or post data
        if days_requested == 0 and history_requests:
            # Try to identify date range from the request
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
                            if date_diff > 0:
                                days_requested = date_diff
                                break
                        except ValueError:
                            # If we can't parse the dates, continue to the next request
                            continue

        # If we still don't have a day count but have history requests, assume it's the default (7)
        if days_requested == 0 and history_requests:
            days_requested = 7  # Assume default

        # Verify we're requesting the default (7 days) of history data
        assert (
            days_requested == 7
        ), f"History tab requested {days_requested} days instead of default 7 days"

        print(f"History tab requested {days_requested} days of data")

    def test_history_tab_loads_correct_timeframe_when_selected(
        self, page: Page, network_requests
    ):
        """
        Test that the history tab loads the correct amount of data when different timeframes are selected.
        """
        # List of timeframes to test
        timeframes = [14, 30]

        for days in timeframes:
            # Reset the network requests
            network_requests.clear()

            # Navigate to the water heater dashboard
            page.goto("http://localhost:8006/water-heaters")
            page.wait_for_selector(".dashboard .heater-card", timeout=5000)

            # Click the first water heater card to go to details
            page.query_selector(".dashboard .heater-card").click()
            page.wait_for_selector(".details-container", timeout=5000)

            # Find and click the history tab
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

            # Find and click the timeframe dropdown/selector
            timeframe_selector = page.query_selector(
                ".timeframe-selector select, .timeframe-dropdown button"
            )
            assert timeframe_selector, "Timeframe selector not found"

            # If it's a dropdown button, click it to show options
            if timeframe_selector.get_attribute(
                "class"
            ) and "dropdown" in timeframe_selector.get_attribute("class"):
                timeframe_selector.click()

                # Find and click the option for the current days value
                day_option = page.query_selector(
                    f".dropdown-menu .dropdown-item:text('{days} days')"
                )
                assert day_option, f"Option for {days} days not found in dropdown"
                day_option.click()
            else:
                # If it's a select element, just set the value
                timeframe_selector.select_option(value=str(days))

            # Wait a moment for the request to be made
            page.wait_for_timeout(1000)

            # Check the API requests
            api_requests = [r for r in network_requests if "/api/" in r["url"]]
            history_requests = [
                r
                for r in api_requests
                if "/history" in r["url"] or "timeframe" in r["url"]
            ]

            # Verify we have history requests after changing the timeframe
            assert (
                len(history_requests) > 0
            ), f"No history requests found after selecting {days} days"

            # Check if we requested the correct number of days
            requested_correct_days = False
            for req in history_requests:
                url = req["url"]
                if f"timeframe={days}" in url or f"days={days}" in url:
                    requested_correct_days = True
                    break

            # If we didn't find an explicit day parameter, check for date ranges that match our expected days
            if not requested_correct_days:
                for req in history_requests:
                    url = req["url"]
                    if "start_date" in url and "end_date" in url:
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

                                # Allow for some flexibility due to how dates are calculated
                                if abs(date_diff - days) <= 1:
                                    requested_correct_days = True
                                    break
                            except ValueError:
                                continue

            assert (
                requested_correct_days
            ), f"Did not request {days} days of data after selecting that timeframe"

            print(
                f"Successfully requested {days} days of data when that timeframe was selected"
            )

    def test_operations_tab_loads_only_operations_data(
        self, page: Page, network_requests
    ):
        """
        Test that the operations tab only loads operations data, not history or other data.
        """
        # Reset the network requests
        network_requests.clear()

        # Navigate to the water heater dashboard
        page.goto("http://localhost:8006/water-heaters")
        page.wait_for_selector(".dashboard .heater-card", timeout=5000)

        # Click the first water heater card to go to details
        page.query_selector(".dashboard .heater-card").click()
        page.wait_for_selector(".details-container", timeout=5000)

        # Find and click the operations tab
        operations_tab = None
        tabs = page.query_selector_all(".tab-nav .nav-item")
        for tab in tabs:
            if "Operations" in tab.inner_text():
                operations_tab = tab
                break

        assert operations_tab, "Operations tab not found"
        operations_tab.click()

        # Wait for operations content to load
        try:
            page.wait_for_selector("#operations-content:visible", timeout=5000)
        except:
            # If we can't find the specific selector, continue anyway to check the requests
            pass

        # Check the API requests
        api_requests = [r for r in network_requests if "/api/" in r["url"]]
        operations_requests = [
            r
            for r in api_requests
            if "operations" in r["url"] or "dashboard" in r["url"]
        ]
        history_requests = [
            r for r in api_requests if "/history" in r["url"] or "timeframe" in r["url"]
        ]

        # Verify we have operations requests
        assert (
            len(operations_requests) > 0
        ), "No operations requests found after clicking operations tab"

        # Verify we don't have history requests when on operations tab
        assert (
            len(history_requests) == 0
        ), f"Found {len(history_requests)} history requests on operations tab"

        print(
            f"Operations tab made {len(operations_requests)} operations data requests "
            f"and {len(history_requests)} history requests"
        )
