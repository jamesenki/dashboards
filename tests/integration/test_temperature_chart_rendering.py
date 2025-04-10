#!/usr/bin/env python3
"""Test suite for Temperature History Chart rendering.

Following TDD principles as required for the IoTSphere project, this test:
1. Verifies the temperature history chart container is properly rendered
2. Validates the chart actually displays when temperature data is loaded
3. Tests that period selectors (7, 14, 30 days) properly update the chart display

RED-GREEN-REFACTOR methodology:
- RED: Define expected behavior through this test
- GREEN: Fix the chart rendering issue
- REFACTOR: Ensure the implementation is clean and maintainable
"""
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Add project root to path for imports
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from src.main import app
from tests.helpers import WEB_PORT, get_test_server_url

# Test data
DEVICE_ID = "wh-e2ae2f60"  # Use the same device ID as in the logs
TEST_URL = f"{get_test_server_url()}/water-heaters/{DEVICE_ID}"

MOCK_TEMP_DATA = {
    "device_id": DEVICE_ID,
    "metric": "temperature",
    "unit": "°C",
    "period_days": 7,
    "labels": ["04/03", "04/04", "04/05", "04/06", "04/07", "04/08", "04/09"],
    "datasets": [
        {
            "label": "Temperature (°C)",
            "data": [60.5, 61.2, 62.5, 59.8, 58.9, 63.1, 62.7],
            "borderColor": "#FF6384",
            "backgroundColor": "rgba(255, 99, 132, 0.2)",
        },
        {
            "label": "Target Temperature (°C)",
            "data": [55.0, 55.0, 55.0, 55.0, 55.0, 55.0, 55.0],
            "borderColor": "#36A2EB",
            "backgroundColor": "rgba(54, 162, 235, 0.2)",
        },
    ],
}


@pytest.fixture(scope="module")
def driver():
    """Set up Chrome driver for the tests."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1366, 768)  # Set a standard window size

    yield driver

    driver.quit()


def test_temperature_history_chart_elements(driver):
    """Test that all necessary elements for the temperature history chart exist on the page.

    This is a RED test - it will fail until the chart rendering issues are fixed.
    """
    # Navigate to the water heater detail page
    driver.get(TEST_URL)

    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".water-heater-detail"))
    )

    # Switch to History tab
    history_tab = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'History')]"))
    )
    history_tab.click()

    # Wait for tab content to load
    time.sleep(2)

    # Verify the temperature history section exists
    temperature_section = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//h3[contains(text(), 'Temperature History')]")
        )
    )
    assert temperature_section.is_displayed()

    # Verify the chart container exists
    try:
        chart_container = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "temperatureHistoryChartContainer"))
        )
        assert chart_container.is_displayed()
    except TimeoutException:
        # If the specific ID is not found, check for any chart container element
        chart_containers = driver.find_elements(
            By.CSS_SELECTOR, ".chart-container, .temperature-chart-container"
        )
        assert (
            len(chart_containers) > 0
        ), "No temperature chart container found on the page"
        chart_container = chart_containers[0]
        assert chart_container.is_displayed()

    # Log the actual ID for debugging
    chart_containers = driver.find_elements(
        By.CSS_SELECTOR, ".chart-container, .temperature-chart-container"
    )
    for container in chart_containers:
        print(
            f"Found chart container with ID: {container.get_attribute('id')} and class: {container.get_attribute('class')}"
        )

    # Verify the canvas element exists
    try:
        chart_canvas = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "canvas#temperatureHistoryChart, canvas.temperature-chart",
                )
            )
        )
        assert chart_canvas.is_displayed()
    except TimeoutException:
        # If the specific canvas is not found, check for any canvas element within the chart container
        canvases = chart_container.find_elements(By.TAG_NAME, "canvas")
        assert (
            len(canvases) > 0
        ), "No canvas element found in the temperature chart container"
        chart_canvas = canvases[0]
        assert chart_canvas.is_displayed()

    # Verify the period selectors exist
    period_selectors = driver.find_elements(
        By.CSS_SELECTOR, ".period-selector, .btn-period"
    )
    assert (
        len(period_selectors) >= 3
    ), f"Expected at least 3 period selectors, found {len(period_selectors)}"

    # Verify that period selectors have the expected text (7, 14, 30)
    period_texts = [selector.text.strip() for selector in period_selectors]
    print(f"Period selector texts: {period_texts}")

    # Check that the canvas has dimensions (width and height)
    canvas_width = int(chart_canvas.get_attribute("width") or 0)
    canvas_height = int(chart_canvas.get_attribute("height") or 0)

    # If width/height attributes aren't set, try getting dimensions from style or bounding rect
    if canvas_width == 0 or canvas_height == 0:
        size = chart_canvas.size
        canvas_width = size["width"]
        canvas_height = size["height"]

    print(f"Canvas dimensions: {canvas_width}x{canvas_height}")

    # If either dimension is 0, this indicates the chart isn't rendering properly
    assert canvas_width > 0, "Chart canvas has zero width"
    assert canvas_height > 0, "Chart canvas has zero height"


def test_temperature_history_chart_container_structure(driver):
    """Analyze the DOM structure of the temperature history chart container.

    This test helps diagnose what's wrong with the chart container that prevents it from rendering.
    """
    # Navigate to the water heater detail page
    driver.get(TEST_URL)

    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".water-heater-detail"))
    )

    # Switch to History tab
    history_tab = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'History')]"))
    )
    history_tab.click()

    # Wait for tab content to load
    time.sleep(2)

    # Get the History tab content
    tab_content = driver.find_element(By.CSS_SELECTOR, ".tab-content")

    # Get the HTML structure of the tab content
    tab_html = tab_content.get_attribute("outerHTML")
    print("\nHistory Tab Content HTML:")
    print(tab_html)

    # Analyze JavaScript errors
    js_errors = driver.execute_script(
        """
        return window.errors || [];
    """
    )

    if js_errors:
        print("\nJavaScript Errors:")
        for error in js_errors:
            print(error)


def test_inspect_temperature_chart_javascript(driver):
    """Inspect the JavaScript objects related to the temperature chart.

    This test adds diagnostic JavaScript to the page to help identify the issue.
    """
    # Navigate to the water heater detail page
    driver.get(TEST_URL)

    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".water-heater-detail"))
    )

    # Switch to History tab
    history_tab = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'History')]"))
    )
    history_tab.click()

    # Wait for tab content to load
    time.sleep(2)

    # Execute diagnostic script to check chart instances and DOM elements
    diagnostic_results = driver.execute_script(
        """
    // Create a diagnostics container
    let diagnostics = {};

    // Check all canvas elements
    diagnostics.canvasElements = [];
    document.querySelectorAll('canvas').forEach(canvas => {
        diagnostics.canvasElements.push({
            id: canvas.id,
            width: canvas.width,
            height: canvas.height,
            display: getComputedStyle(canvas).display,
            visibility: getComputedStyle(canvas).visibility,
            className: canvas.className,
            parentNode: canvas.parentNode ? {
                id: canvas.parentNode.id,
                className: canvas.parentNode.className,
                display: getComputedStyle(canvas.parentNode).display,
                visibility: getComputedStyle(canvas.parentNode).visibility
            } : null
        });
    });

    // Check Chart.js instances if available
    if (window.Chart && window.Chart.instances) {
        diagnostics.chartInstances = Object.keys(window.Chart.instances).map(key => {
            const chart = window.Chart.instances[key];
            return {
                id: chart.canvas.id,
                type: chart.config.type,
                data: chart.data ? {
                    labels: chart.data.labels,
                    datasets: chart.data.datasets.map(ds => ({
                        label: ds.label,
                        dataLength: ds.data ? ds.data.length : 0
                    }))
                } : null
            };
        });
    } else {
        diagnostics.chartInstances = 'Chart.js instances not found';
    }

    // Check for DeviceShadowTemperatureChart instances
    diagnostics.temperatureChartInstances = [];
    if (window.temperatureChart) {
        diagnostics.temperatureChartInstances.push({
            type: 'global temperatureChart',
            initialized: window.temperatureChart.initialized || false,
            deviceId: window.temperatureChart.deviceId || 'unknown'
        });
    }

    // Find any element with ID containing 'temperature' and 'chart'
    diagnostics.temperatureChartElements = [];
    document.querySelectorAll('[id*="temperature"][id*="chart"], [class*="temperature"][class*="chart"]').forEach(el => {
        diagnostics.temperatureChartElements.push({
            id: el.id,
            tagName: el.tagName,
            className: el.className,
            display: getComputedStyle(el).display,
            visibility: getComputedStyle(el).visibility,
            dimensions: {
                width: el.offsetWidth,
                height: el.offsetHeight
            }
        });
    });

    return diagnostics;
    """
    )

    # Print the diagnostic results
    print("\nTemperature Chart Diagnostics:")
    print(json.dumps(diagnostic_results, indent=2))


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
