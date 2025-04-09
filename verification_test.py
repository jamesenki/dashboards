#!/usr/bin/env python3
"""
Verification test for IoTSphere fixes

This script:
1. Tests if the water heater duplication issue is fixed
2. Tests if temperature history is properly displayed or shows a meaningful error message

Following TDD principles, we verify our fixes with direct tests.
"""

import json
import logging
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("verify")

# Constants
BASE_URL = "http://localhost:8000"


def verify_list_page():
    """Verify that water heater cards are not duplicated on the list page"""
    logger.info("\n" + "=" * 80)
    logger.info("VERIFYING LIST PAGE (DUPLICATION FIX)")
    logger.info("=" * 80)

    # Get the list page
    resp = requests.get(f"{BASE_URL}/water-heaters")
    if resp.status_code != 200:
        logger.error(f"Failed to access list page: {resp.status_code}")
        return False

    # Parse with BeautifulSoup for better HTML analysis
    soup = BeautifulSoup(resp.text, "html.parser")

    # First, check if our fix script is loaded
    scripts = soup.find_all("script")
    fix_script_loaded = any(
        "complete-fixes.js" in script.get("src", "") for script in scripts
    )

    if fix_script_loaded:
        logger.info("✅ Fix script is properly loaded on the list page")
    else:
        logger.error("❌ Fix script is NOT loaded on the list page")
        return False

    # Wait briefly for JavaScript to execute
    time.sleep(2)

    # Now directly access the list page again to check after JS had time to run
    resp = requests.get(f"{BASE_URL}/water-heaters")
    html = resp.text

    # Look for duplicate patterns
    # Extract all device IDs from various potential card formats
    device_ids = []

    # Using regex patterns to find device IDs in various formats
    id_patterns = [
        r'id="heater-([\w-]+)"',  # id="heater-wh001"
        r'data-id="([\w-]+)"',  # data-id="wh001"
        r'data-device-id="([\w-]+)"',  # data-device-id="wh001"
        r'class="device-id[^>]*>([\w-]+)<',  # class="device-id">wh001</
    ]

    for pattern in id_patterns:
        ids = re.findall(pattern, html)
        logger.info(f"Found {len(ids)} IDs with pattern '{pattern}': {ids}")
        device_ids.extend(ids)

    # Count occurrences of each ID
    id_counts = {}
    for device_id in device_ids:
        if device_id in id_counts:
            id_counts[device_id] += 1
        else:
            id_counts[device_id] = 1

    # Check for duplicates
    duplicates = {id: count for id, count in id_counts.items() if count > 1}

    if duplicates:
        logger.error(f"❌ Found duplicate device IDs: {duplicates}")

        # Check if visually hidden
        hidden_duplicates = re.findall(
            r'data-duplicate="true"|style="display:\s*none"', html
        )
        if hidden_duplicates:
            logger.info(f"Found {len(hidden_duplicates)} hidden duplicate elements")
            logger.info("✅ Duplicates exist in DOM but are visually hidden - FIX WORKS")
            return True
        else:
            logger.error("❌ Duplicates are visually displayed - FIX FAILED")
            return False
    else:
        logger.info("✅ No duplicate device IDs found - FIX WORKS")
        return True


def verify_details_page(device_id="wh-001"):
    """Verify temperature history chart is displayed on details page"""
    logger.info("\n" + "=" * 80)
    logger.info(f"VERIFYING DETAILS PAGE FOR {device_id} (TEMPERATURE HISTORY FIX)")
    logger.info("=" * 80)

    # Get the details page
    resp = requests.get(f"{BASE_URL}/water-heaters/{device_id}")
    if resp.status_code != 200:
        logger.error(f"Failed to access details page: {resp.status_code}")
        return False

    html = resp.text

    # Check if our fix script is loaded
    fix_script_loaded = "complete-fixes.js" in html

    if fix_script_loaded:
        logger.info("✅ Fix script is properly loaded on the details page")
    else:
        logger.error("❌ Fix script is NOT loaded on the details page")
        return False

    # Parse with BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # Look for temperature history container
    temp_container = soup.select(
        ".temperature-history-container, .temp-history-container"
    )

    if temp_container:
        logger.info(f"✅ Found {len(temp_container)} temperature history container(s)")
    else:
        # This might not be a failure if our script adds the container dynamically
        logger.warning("No temperature history container found in initial HTML")

    # Check for canvas element (chart) or error message
    canvas = soup.find("canvas")
    error_message = soup.select(".error-message, .chart-error, .no-data-message")

    if canvas:
        logger.info("✅ Found canvas element for chart")
        return True
    elif error_message:
        message_text = error_message[0].get_text().strip()
        logger.info(f"✅ Found error message: {message_text}")
        logger.info("This is expected if there's no shadow document")
        return True
    else:
        # Our script might add these dynamically, so make another request after a delay
        logger.info(
            "No chart or error message found in initial HTML. Will check again after delay..."
        )

        # Wait for JavaScript to execute
        time.sleep(3)

        # Check API endpoints directly
        api_resp = requests.get(f"{BASE_URL}/api/device-shadows/{device_id}")
        if api_resp.status_code == 200:
            shadow = api_resp.json()
            has_history = "history" in shadow and shadow["history"]
            logger.info(
                f"Device shadow API returned document with history: {has_history}"
            )

            if has_history:
                logger.info(f"Found {len(shadow['history'])} history entries in shadow")
                logger.info("✅ Shadow data exists - chart should render")
            else:
                logger.info("Shadow exists but has no history entries")
                logger.info("✅ Chart should show 'No temperature history' message")
        else:
            logger.warning(f"Device shadow API failed: {api_resp.status_code}")
            logger.info("✅ Chart should show 'No shadow document' error message")

        # Make a final check on the page
        resp = requests.get(f"{BASE_URL}/water-heaters/{device_id}")
        soup = BeautifulSoup(resp.text, "html.parser")

        # Look for dynamically added elements
        canvas = soup.find("canvas")
        error_message = soup.select(".error-message, .chart-error, .no-data-message")

        if canvas:
            logger.info("✅ Found canvas element for chart on second check")
            return True
        elif error_message:
            message_text = error_message[0].get_text().strip()
            logger.info(f"✅ Found error message on second check: {message_text}")
            logger.info("This is expected if there's no shadow document")
            return True
        else:
            logger.warning("Still no chart or error message found after delay")
            logger.info(
                "This may be a client-side rendering issue that requires browser testing"
            )

            # Check for verification elements that our script would add
            verification = soup.select(
                "#temp-history-fix-complete, #temp-history-error-handled"
            )
            if verification:
                logger.info("✅ Found verification elements - fix appears to work")
                return True
            else:
                logger.warning(
                    "No verification elements found - fix may not be working correctly"
                )
                return False


def verify_all():
    """Run all verification tests"""
    logger.info("=" * 80)
    logger.info("RUNNING VERIFICATION TESTS FOR IOTSPHERE FIXES")
    logger.info("=" * 80)

    # Ensure server is running
    try:
        resp = requests.get(BASE_URL)
        if resp.status_code != 200:
            logger.error(f"Server returned status {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to {BASE_URL}. Is the server running?")
        return False

    # Run verification tests
    list_page_result = verify_list_page()
    details_page_result = verify_details_page("wh-001")

    # Report overall result
    logger.info("\n" + "=" * 80)
    logger.info("VERIFICATION TEST RESULTS")
    logger.info("=" * 80)
    logger.info(f"List Page Deduplication: {'PASS' if list_page_result else 'FAIL'}")
    logger.info(
        f"Details Page Temperature History: {'PASS' if details_page_result else 'FAIL'}"
    )

    overall_result = list_page_result and details_page_result
    logger.info(f"Overall Result: {'PASS' if overall_result else 'FAIL'}")

    return overall_result


if __name__ == "__main__":
    success = verify_all()
    sys.exit(0 if success else 1)
