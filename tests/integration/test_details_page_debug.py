#!/usr/bin/env python3
"""
Diagnostic test for water heater details page
Following TDD principles - debugging before implementing fixes
"""
import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def run_diagnostic():
    """Run diagnostics on water heater details page"""
    print("\n🔍 WATER HEATER DETAILS PAGE DIAGNOSTICS")
    print("========================================")

    # Set up Chrome options
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    base_url = "http://localhost:8000"

    try:
        # Navigate to water heater details
        print("🔄 Navigating to water heater details page...")
        driver.get(f"{base_url}/water-heaters/wh-002")

        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)  # Give extra time for scripts to load

        # 1. Check basic page structure
        print("\n📋 Page Structure Analysis:")
        structure = driver.execute_script(
            """
        return {
            title: document.title,
            url: window.location.href,
            bodyExists: !!document.body,
            contentSelector: "#main-content",
            contentExists: !!document.querySelector("#main-content"),
            tabsExist: !!document.querySelector(".tab-container"),
            tabCount: document.querySelectorAll("[id$='-tab-btn']").length,
            activeTab: document.querySelector(".active-tab")?.id || "none"
        };
        """
        )

        print(json.dumps(structure, indent=2))

        # 2. Check for JavaScript errors
        print("\n⚠️ JavaScript Error Analysis:")
        driver.execute_script(
            """
        window.jsErrors = [];
        window.addEventListener('error', function(e) {
            window.jsErrors.push({
                message: e.message,
                source: e.filename,
                line: e.lineno
            });
        });
        """
        )

        # Load each tab to check for errors
        tabs = driver.find_elements(By.CSS_SELECTOR, "[id$='-tab-btn']")
        for tab in tabs:
            tab_id = tab.get_attribute("id")
            print(f"  Clicking tab: {tab_id}")
            tab.click()
            time.sleep(2)  # Wait for tab content to load

        # Check collected errors
        errors = driver.execute_script("return window.jsErrors;")
        if errors:
            print(f"  Found {len(errors)} JavaScript errors:")
            for i, error in enumerate(errors[:5], 1):  # Show first 5 errors
                print(
                    f"    {i}. {error.get('message')} (in {error.get('source')}:{error.get('line')})"
                )
            if len(errors) > 5:
                print(f"    ...plus {len(errors) - 5} more errors")
        else:
            print("  No JavaScript errors detected")

        # 3. Check chart containers and canvas elements
        print("\n📊 Chart Analysis:")
        chart_analysis = driver.execute_script(
            """
        // Navigate back to details tab
        const detailsTab = document.querySelector("#details-tab-btn");
        if (detailsTab) {
            detailsTab.click();
        }

        // Check chart elements
        const chartContainers = document.querySelectorAll("#temperature-chart, .chart-container, [data-chart]");
        const canvasElements = document.querySelectorAll("canvas");

        // Get chart instance information if available
        let chartInstances = [];
        if (window.ChartInstanceManager && window.ChartInstanceManager.listCharts) {
            chartInstances = window.ChartInstanceManager.listCharts();
        }

        return {
            containers: Array.from(chartContainers).map(el => ({
                id: el.id,
                class: el.className,
                visibility: window.getComputedStyle(el).display,
                width: el.offsetWidth,
                height: el.offsetHeight,
                parent: el.parentElement ? el.parentElement.id || el.parentElement.tagName : "none"
            })),
            canvases: Array.from(canvasElements).map(el => ({
                id: el.id,
                parent: el.parentElement ? el.parentElement.id || el.parentElement.tagName : "none",
                visibility: window.getComputedStyle(el).display,
                width: el.width,
                height: el.height
            })),
            instances: chartInstances
        };
        """
        )

        print("  Chart Containers:")
        for container in chart_analysis.get("containers", []):
            print(
                f"    ID: {container.get('id', 'none')}, Class: {container.get('class', 'none')}, "
                + f"Visibility: {container.get('visibility', 'unknown')}, "
                + f"Size: {container.get('width', 0)}x{container.get('height', 0)}, "
                + f"Parent: {container.get('parent', 'unknown')}"
            )

        print("\n  Canvas Elements:")
        for canvas in chart_analysis.get("canvases", []):
            print(
                f"    ID: {canvas.get('id', 'none')}, "
                + f"Visibility: {canvas.get('visibility', 'unknown')}, "
                + f"Size: {canvas.get('width', 0)}x{canvas.get('height', 0)}, "
                + f"Parent: {canvas.get('parent', 'unknown')}"
            )

        print("\n  Chart Instances:")
        instances = chart_analysis.get("instances", [])
        if instances:
            for instance in instances:
                print(f"    {instance}")
        else:
            print(
                "    No chart instances found or ChartInstanceManager.listCharts() not available"
            )

        # 4. Visual verification - take screenshot
        print("\n📷 Taking verification screenshot...")
        screenshots_dir = project_root / "tests" / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        driver.save_screenshot(str(screenshots_dir / "details_page_debug.png"))
        print(f"  Screenshot saved to: tests/screenshots/details_page_debug.png")

        # 5. Check DOM mutations during tab navigation
        print("\n🔄 Testing Tab Navigation Effects:")
        driver.execute_script(
            """
        window.domChanges = [];

        // Set up mutation observer to track DOM changes
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                if (mutation.type === 'childList' ||
                    (mutation.type === 'attributes' && mutation.attributeName === 'style')) {
                    window.domChanges.push({
                        type: mutation.type,
                        target: mutation.target.id || mutation.target.className || mutation.target.tagName,
                        addedNodes: mutation.addedNodes.length,
                        removedNodes: mutation.removedNodes.length,
                        attribute: mutation.attributeName,
                        timestamp: new Date().toISOString()
                    });
                }
            });
        });

        observer.observe(document.body, {
            childList: true,
            attributes: true,
            subtree: true,
            attributeFilter: ['style', 'class', 'id']
        });

        // Click history tab to observe changes
        const historyTab = document.querySelector("#history-tab-btn");
        if (historyTab) {
            console.log("Clicking history tab for observation...");
            historyTab.click();
        }
        """
        )

        # Wait for tab switch
        time.sleep(3)

        # Get DOM changes
        dom_changes = driver.execute_script("return window.domChanges;")

        print(f"  Recorded {len(dom_changes)} DOM changes during tab navigation")
        print("  Key DOM changes:")

        # Filter to show the most relevant changes (visibility changes, chart-related)
        filtered_changes = [
            c
            for c in dom_changes
            if (
                "chart" in str(c.get("target", "")).lower()
                or "tab" in str(c.get("target", "")).lower()
                or (c.get("addedNodes", 0) > 0 or c.get("removedNodes", 0) > 0)
            )
        ]

        for i, change in enumerate(filtered_changes[:10], 1):
            print(
                f"    {i}. Type: {change.get('type')}, Target: {change.get('target')}, "
                + f"Added: {change.get('addedNodes')}, Removed: {change.get('removedNodes')}"
            )

        if len(filtered_changes) > 10:
            print(f"    ...plus {len(filtered_changes) - 10} more relevant changes")

        print("\n✅ Diagnostics completed successfully")

    except Exception as e:
        print(f"\n❌ Error during diagnostics: {str(e)}")
    finally:
        driver.quit()


if __name__ == "__main__":
    run_diagnostic()
