import re

import pytest
from playwright.sync_api import Page, expect

# These tests verify the frontend UI components render and function correctly
# They use Playwright for browser-based testing


class TestWaterHeaterUI:
    """UI tests for water heater components."""

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, page: Page):
        """Setup for each test."""
        # Navigate to the water heater dashboard
        page.goto("http://localhost:8006/water-heaters")

        # Wait for the dashboard to load
        page.wait_for_selector("#water-heater-list .dashboard", timeout=5000)

    def test_dashboard_loads(self, page: Page):
        """Test that the water heater dashboard loads successfully."""
        # Verify page title
        assert "Water Heaters" in page.title()

        # Verify the page header exists
        header = page.query_selector(".page-header h2")
        expect(header).to_contain_text("Water Heaters")

        # Verify navigation items
        nav_items = page.query_selector_all("nav.main-nav li a")
        assert len(nav_items) >= 2  # At least "All Devices" and "Add New"

    def test_water_heater_cards_display(self, page: Page):
        """Test that water heater cards display correctly."""
        # Wait for cards to load
        page.wait_for_selector(".dashboard .heater-card", timeout=5000)

        # Get all water heater cards
        cards = page.query_selector_all(".dashboard .heater-card")

        # Verify we have at least one card
        assert len(cards) > 0, "Expected at least one water heater card"

        # Verify each card has the expected elements
        for card in cards:
            # Card should have a title
            expect(card.query_selector(".card-title")).to_be_visible()

            # Card should have a temperature display
            expect(card.query_selector(".gauge-value")).to_be_visible()

            # Card should show the target temperature
            expect(card.query_selector(".target-temp")).to_be_visible()

    def test_water_heater_status_indicator(self, page: Page):
        """Test that status indicators display correctly."""
        # Wait for cards to load
        page.wait_for_selector(".dashboard .heater-card", timeout=5000)

        # Get all status indicators
        status_indicators = page.query_selector_all(".status-indicator")

        # Verify we have status indicators
        assert len(status_indicators) > 0

        # Check that each indicator has the appropriate class based on status
        for indicator in status_indicators:
            # It should have one of these classes
            assert any(
                [
                    indicator.has_class("status-heating"),
                    indicator.has_class("status-standby"),
                    indicator.has_class("status-error"),
                    indicator.has_class("status-maintenance"),
                ]
            )

    def test_water_heater_detail_view(self, page: Page):
        """Test that clicking a card navigates to the detail view."""
        # Get the first card
        card = page.query_selector(".dashboard .heater-card")
        assert card is not None

        # Get the heater ID from the card for verification later
        heater_id = card.get_attribute("data-id")
        assert heater_id is not None

        # Click on the card
        card.click()

        # Wait for the detail page to load
        page.wait_for_url(re.compile(r"/water-heaters/detail/.*"))

        # Verify we're on the right detail page
        current_url = page.url
        assert heater_id in current_url

        # Verify the detail elements are present
        expect(page.query_selector(".detail-view")).to_be_visible()
        expect(page.query_selector(".temperature-slider")).to_be_visible()
        expect(page.query_selector(".mode-controls")).to_be_visible()

    def test_temperature_control(self, page: Page):
        """Test that temperature controls work."""
        # Navigate to detail page of first heater
        card = page.query_selector(".dashboard .heater-card")
        card.click()
        page.wait_for_selector(".temperature-slider", timeout=5000)

        # Get the current temperature value
        slider = page.query_selector("input[type='range']")
        original_value = slider.get_attribute("value")

        # Change the temperature
        new_value = int(original_value) + 5
        slider.fill(str(new_value))

        # Click the save button
        page.query_selector(".btn-primary").click()

        # Wait for the save operation
        page.wait_for_timeout(1000)

        # Verify the value was updated
        updated_slider = page.query_selector("input[type='range']")
        updated_value = updated_slider.get_attribute("value")
        assert int(updated_value) == new_value
