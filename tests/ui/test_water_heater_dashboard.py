"""
Test suite for water heater dashboard UI components.
Following TDD principles, these tests define the expected behaviors
for the water heater dashboard components.
"""

import pytest
import os
import sys
import time
from pathlib import Path
from playwright.sync_api import Page, expect

# Add the project root to the path so we can import modules
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Constants
BASE_URL = "http://localhost:8006"

@pytest.fixture
def setup_page(page: Page):
    """Set up the browser page before each test."""
    # Navigate to water heaters list
    page.goto(f"{BASE_URL}/water-heaters")
    # Wait for page to load
    page.wait_for_selector(".water-heater-card", timeout=5000)
    yield page
    # Nothing to teardown

def test_navigation_to_detail_page(setup_page):
    """Test navigation to a water heater detail page."""
    page = setup_page
    
    # Click on the first water heater card
    page.click(".water-heater-card")
    
    # Verify we've navigated to a detail page
    expect(page).to_have_url(f"{BASE_URL}/water-heaters/")
    expect(page.locator("#water-heater-detail")).to_be_visible()
    
    # Log success
    print("✅ Successfully navigated to water heater detail page")

def test_no_status_duplication(setup_page):
    """Test that status cards are not duplicated when switching tabs."""
    page = setup_page
    
    # Navigate to a detail page
    page.click(".water-heater-card")
    page.wait_for_selector("#water-heater-detail", timeout=5000)
    
    # Verify the operations tab exists and click it
    operations_tab = page.locator("#operations-tab-btn")
    expect(operations_tab).to_be_visible()
    operations_tab.click()
    
    # Wait for operations tab content to be visible
    page.wait_for_selector("#operations-content.active", timeout=5000)
    
    # Count the status items
    status_items_count = page.locator(".status-item").count()
    print(f"Initial status items count: {status_items_count}")
    
    # Switch to a different tab
    page.locator("#history-tab-btn").click()
    
    # Wait for history content to be visible
    page.wait_for_selector("#history-content.active", timeout=5000)
    
    # Switch back to operations tab
    page.locator("#operations-tab-btn").click()
    
    # Wait for operations tab content to be visible again
    page.wait_for_selector("#operations-content.active", timeout=5000)
    
    # Count status items again
    new_status_items_count = page.locator(".status-item").count()
    print(f"Status items after tab switching: {new_status_items_count}")
    
    # Assert there's no duplication
    assert new_status_items_count == status_items_count, f"Status items were duplicated: {new_status_items_count} vs {status_items_count}"
    
    # Log success
    print("✅ No status duplication detected when switching tabs")

def test_temperature_history_chart_visibility(setup_page):
    """Test that temperature history chart is visible when history tab is active."""
    page = setup_page
    
    # Navigate to a detail page
    page.click(".water-heater-card")
    page.wait_for_selector("#water-heater-detail", timeout=5000)
    
    # Click on history tab
    page.locator("#history-tab-btn").click()
    
    # Wait for history tab content to be visible
    page.wait_for_selector("#history-content.active", timeout=5000)
    
    # Give time for charts to load
    time.sleep(2)
    
    # Check if temperature chart exists
    temp_chart = page.locator("#temperature-chart")
    
    # Check visibility of temperature chart
    is_visible = temp_chart.is_visible()
    print(f"Temperature chart visibility: {is_visible}")
    
    # Assert the temperature chart is visible
    assert is_visible, "Temperature history chart is not visible in the history tab"
    
    # Additional check: canvas should be rendered inside the chart
    canvas_visible = page.locator("#temperature-chart canvas").is_visible()
    print(f"Temperature chart canvas visibility: {canvas_visible}")
    
    # Take a screenshot for debugging
    page.screenshot(path=f"{project_root}/temp_chart_test.png")
    
    # Log success or failure
    if is_visible and canvas_visible:
        print("✅ Temperature history chart is visible")
    else:
        print("❌ Temperature history chart is not properly rendered")

if __name__ == "__main__":
    # This allows running the test file directly
    pytest.main(["-xvs", __file__])
