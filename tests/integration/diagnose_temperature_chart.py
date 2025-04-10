#!/usr/bin/env python3
"""
Temperature History Chart Rendering Diagnostic Script

Following TDD principles for the IoTSphere project, this script:
1. Diagnoses why the temperature history chart isn't rendering
2. Provides detailed logging about the DOM structure
3. Captures JavaScript errors and chart initialization issues

This is part of the RED phase in TDD - identifying the problem before fixing it.
"""
import json
import os
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Add project root to path for imports
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Device ID for testing, same as in the logs
DEVICE_ID = "wh-e2ae2f60"
BASE_URL = "http://localhost:8000"
DEVICE_URL = f"{BASE_URL}/water-heaters/{DEVICE_ID}"


def setup_driver():
    """Set up Chrome driver with appropriate options."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1366, 768)
    return driver


def diagnose_chart_rendering():
    """Diagnose why the temperature history chart isn't rendering properly."""
    driver = setup_driver()
    try:
        print(f"Opening URL: {DEVICE_URL}")
        driver.get(DEVICE_URL)

        # Wait for page to load
        print("Waiting for page to load...")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".water-heater-detail")
                )
            )
            print("✅ Water heater detail page loaded successfully")
        except TimeoutException:
            print("❌ Timeout waiting for water heater detail page to load")
            print(f"Current URL: {driver.current_url}")
            print(f"Page source: {driver.page_source[:500]}...")
            return

        # Switch to History tab
        try:
            print("Looking for History tab...")
            history_tabs = driver.find_elements(
                By.XPATH, "//a[contains(text(), 'History')]"
            )
            if not history_tabs:
                print("❌ No History tab found. Looking for any tab elements...")
                all_tabs = driver.find_elements(By.CSS_SELECTOR, ".nav-tabs .nav-link")
                print(f"Found {len(all_tabs)} tabs: {[tab.text for tab in all_tabs]}")

                if all_tabs:
                    # Click the second tab (usually History)
                    if len(all_tabs) > 1:
                        print(f"Clicking second tab: {all_tabs[1].text}")
                        all_tabs[1].click()
                    else:
                        print("Only one tab found, clicking it")
                        all_tabs[0].click()
            else:
                print(f"✅ Found History tab, clicking it...")
                history_tabs[0].click()
        except Exception as e:
            print(f"❌ Error clicking History tab: {str(e)}")

        # Wait for tab content to load
        print("Waiting for tab content to load...")
        time.sleep(2)

        # Look for chart elements
        print("\n--- Temperature Chart DOM Analysis ---")

        # Check for temperature history section
        temp_sections = driver.find_elements(
            By.XPATH, "//*[contains(text(), 'Temperature History')]"
        )
        if temp_sections:
            print(f"✅ Found Temperature History section: {temp_sections[0].tag_name}")
        else:
            print("❌ Temperature History section not found")

        # Check for chart containers
        chart_containers = driver.find_elements(
            By.CSS_SELECTOR,
            ".chart-container, .temperature-chart-container, [id*='temperatureHistoryChart'], [id*='temperature-chart']",
        )
        if chart_containers:
            print(f"✅ Found {len(chart_containers)} chart container(s)")
            for i, container in enumerate(chart_containers):
                print(f"  Container {i+1}:")
                print(f"    ID: {container.get_attribute('id')}")
                print(f"    Class: {container.get_attribute('class')}")
                print(f"    Style: {container.get_attribute('style')}")
                print(
                    f"    Display: {driver.execute_script('return getComputedStyle(arguments[0]).display', container)}"
                )
                print(
                    f"    Visibility: {driver.execute_script('return getComputedStyle(arguments[0]).visibility', container)}"
                )
                print(f"    Dimensions: {container.size}")

                # Check if any canvas elements exist inside
                canvases = container.find_elements(By.TAG_NAME, "canvas")
                if canvases:
                    print(f"    ✅ Contains {len(canvases)} canvas element(s)")
                    for j, canvas in enumerate(canvases):
                        print(f"      Canvas {j+1}:")
                        print(f"        ID: {canvas.get_attribute('id')}")
                        print(f"        Class: {canvas.get_attribute('class')}")
                        print(f"        Width: {canvas.get_attribute('width')}")
                        print(f"        Height: {canvas.get_attribute('height')}")
                        print(f"        Style: {canvas.get_attribute('style')}")
                else:
                    print(f"    ❌ No canvas elements found inside container")

                    # Check what's inside instead
                    inner_html = container.get_attribute("innerHTML")
                    print(
                        f"    Container contents: {inner_html[:100]}..."
                        if len(inner_html) > 100
                        else inner_html
                    )
        else:
            print("❌ No chart containers found")

            # Scan for canvas elements anywhere
            canvases = driver.find_elements(By.TAG_NAME, "canvas")
            if canvases:
                print(f"Found {len(canvases)} canvas elements elsewhere on page")
            else:
                print("No canvas elements found anywhere on page")

        # Get tab content HTML for analysis
        try:
            tab_content = driver.find_element(By.CSS_SELECTOR, ".tab-content")
            tab_panes = tab_content.find_elements(By.CSS_SELECTOR, ".tab-pane")
            print(f"\nFound {len(tab_panes)} tab panes")

            for i, pane in enumerate(tab_panes):
                is_active = "active" in pane.get_attribute("class")
                print(
                    f"Tab pane {i+1}: {pane.get_attribute('id')} (Active: {is_active})"
                )
                if is_active:
                    # Look for chart elements
                    chart_elements = pane.find_elements(
                        By.CSS_SELECTOR, "[id*='chart'], [class*='chart']"
                    )
                    print(
                        f"  Found {len(chart_elements)} chart-related elements in active tab"
                    )
        except Exception as e:
            print(f"Error analyzing tab content: {str(e)}")

        # Execute diagnostic script to check Chart.js and related variables
        print("\n--- JavaScript Diagnostics ---")
        diagnostic_results = driver.execute_script(
            """
        // Create diagnostics container
        let diagnostics = {
            charts: {},
            elements: {},
            globals: {},
            errors: []
        };

        try {
            // Check for Chart.js global
            diagnostics.charts.chartJsGlobal = typeof Chart !== 'undefined';

            // Check Chart.js instances
            if (typeof Chart !== 'undefined' && Chart.instances) {
                diagnostics.charts.instances = Object.keys(Chart.instances).length;
                diagnostics.charts.instanceDetails = Object.keys(Chart.instances).map(key => {
                    try {
                        const chart = Chart.instances[key];
                        return {
                            id: chart.canvas ? chart.canvas.id : null,
                            type: chart.config ? chart.config.type : null,
                            data: chart.data ? {
                                labels: chart.data.labels ? chart.data.labels.length : 0,
                                datasets: chart.data.datasets ? chart.data.datasets.length : 0
                            } : null
                        };
                    } catch (e) {
                        diagnostics.errors.push('Error analyzing Chart instance: ' + e.message);
                        return { error: e.message };
                    }
                });
            } else {
                diagnostics.charts.instances = 0;
                diagnostics.charts.instanceDetails = [];
            }

            // Check for temperature chart specific globals
            diagnostics.globals.temperatureChart = typeof temperatureChart !== 'undefined';
            diagnostics.globals.deviceShadowApi = typeof DeviceShadowApi !== 'undefined';
            diagnostics.globals.deviceShadowTemperatureChart = typeof DeviceShadowTemperatureChart !== 'undefined';

            // Check if any specific chart instance related to temperature exists
            diagnostics.elements.temperatureContainers = [];
            document.querySelectorAll('.chart-container, [id*="temperatureChart"], [id*="chart-container"]').forEach(el => {
                diagnostics.elements.temperatureContainers.push({
                    id: el.id,
                    classes: el.className,
                    visibility: getComputedStyle(el).visibility,
                    display: getComputedStyle(el).display,
                    width: el.offsetWidth,
                    height: el.offsetHeight,
                    hasCanvas: el.querySelector('canvas') !== null,
                    innerHTML: el.innerHTML.length
                });
            });

            // Check all script tags on the page
            diagnostics.scripts = Array.from(document.scripts).map(script => ({
                src: script.src,
                type: script.type,
                id: script.id,
                async: script.async,
                defer: script.defer
            }));

            // Check for console errors
            if (window.consoleErrors) {
                diagnostics.consoleErrors = window.consoleErrors;
            }

            // Check if device-shadow-api.js and device-shadow-temperature-chart.js are loaded
            diagnostics.scripts.temperatureChartScript = Array.from(document.scripts).some(s =>
                s.src && s.src.includes('device-shadow-temperature-chart.js')
            );

            diagnostics.scripts.apiScript = Array.from(document.scripts).some(s =>
                s.src && s.src.includes('device-shadow-api.js')
            );

            // Check for any inline scripts mentioning temperatureChart
            diagnostics.inlineTemperatureChartCode = Array.from(document.scripts)
                .filter(s => !s.src && s.innerHTML.includes('temperatureChart'))
                .length > 0;

        } catch (e) {
            diagnostics.errors.push('Error in diagnostic script: ' + e.message);
        }

        return diagnostics;
        """
        )

        # Print diagnostic results in a readable format
        print("JavaScript Diagnostic Results:")
        print(json.dumps(diagnostic_results, indent=2))

        # Look for specific styling issues
        print("\n--- CSS Diagnostics ---")
        style_diagnostics = driver.execute_script(
            """
        let styles = {};

        // Check if any chart containers have display:none
        styles.hiddenContainers = [];
        document.querySelectorAll('.chart-container, [id*="chart"]').forEach(el => {
            const style = getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden' || el.offsetParent === null) {
                styles.hiddenContainers.push({
                    id: el.id,
                    classes: el.className,
                    display: style.display,
                    visibility: style.visibility,
                    position: style.position,
                    offsetParent: el.offsetParent !== null
                });
            }
        });

        // Check canvas elements specifically
        styles.canvasElements = [];
        document.querySelectorAll('canvas').forEach(canvas => {
            const style = getComputedStyle(canvas);
            styles.canvasElements.push({
                id: canvas.id,
                width: canvas.width,
                height: canvas.height,
                styleWidth: style.width,
                styleHeight: style.height,
                display: style.display,
                visibility: style.visibility,
                position: style.position,
                zIndex: style.zIndex
            });
        });

        return styles;
        """
        )

        print("CSS Diagnostic Results:")
        print(json.dumps(style_diagnostics, indent=2))

        # Check for z-index or positioning issues that might hide the chart
        if style_diagnostics.get("hiddenContainers", []):
            print("\n⚠️ Found hidden chart containers that should be visible!")

    finally:
        driver.quit()


if __name__ == "__main__":
    diagnose_chart_rendering()
