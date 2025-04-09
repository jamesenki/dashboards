#!/usr/bin/env python3
"""
Direct diagnostics and fix for IoTSphere issues:
1. List page duplication issue
2. Temperature history not showing on details page
"""

import json
import logging
import os
import subprocess
import sys
import time

import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("direct_fix")

# Constants
BASE_URL = "http://localhost:8000"


def diagnose_list_page_duplication():
    """Directly examine the list page HTML for duplicated cards"""
    logger.info("=" * 80)
    logger.info("DIAGNOSING LIST PAGE DUPLICATION")
    logger.info("=" * 80)

    # Get the page content
    resp = requests.get(f"{BASE_URL}/water-heaters")
    if resp.status_code != 200:
        logger.error(f"Failed to access list page: {resp.status_code}")
        return

    html = resp.text

    # Check for duplicate patterns in the HTML
    # Look for specific elements that might be duplicated
    device_ids = []

    # Extract device IDs from various patterns
    import re

    # Pattern 1: heater-{id}
    heater_pattern = r'id="heater-([\w-]+)"'
    heater_ids = re.findall(heater_pattern, html)
    logger.info(
        f"Found {len(heater_ids)} devices with 'heater-id' pattern: {heater_ids}"
    )
    device_ids.extend(heater_ids)

    # Pattern 2: data-id="{id}"
    data_id_pattern = r'data-id="([\w-]+)"'
    data_ids = re.findall(data_id_pattern, html)
    logger.info(f"Found {len(data_ids)} devices with 'data-id' pattern: {data_ids}")
    device_ids.extend(data_ids)

    # Pattern 3: class names for cards
    card_pattern = r'class="([^"]*card[^"]*)"'
    cards = re.findall(card_pattern, html)
    card_classes = set(cards)
    logger.info(f"Found {len(cards)} card elements with classes: {card_classes}")

    # Check scripts being loaded
    script_pattern = r'<script src="([^"]+)"'
    scripts = re.findall(script_pattern, html)
    logger.info(f"Found {len(scripts)} scripts being loaded")
    for script in scripts:
        if "water-heater" in script or "deduplication" in script:
            logger.info(f"  - {script}")

    # Check for duplicates
    seen = set()
    duplicates = []
    for device_id in device_ids:
        if device_id in seen:
            duplicates.append(device_id)
        else:
            seen.add(device_id)

    if duplicates:
        logger.info(f"Found {len(duplicates)} duplicated device IDs: {duplicates}")
    else:
        logger.info("No duplicated device IDs found in HTML")


def diagnose_temperature_history():
    """Diagnose temperature history chart issue"""
    logger.info("\n" + "=" * 80)
    logger.info("DIAGNOSING TEMPERATURE HISTORY ISSUE")
    logger.info("=" * 80)

    # Get list of device IDs
    try:
        resp = requests.get(f"{BASE_URL}/api/water-heaters")
        devices = resp.json()
        device_ids = [device.get("id") for device in devices if device.get("id")]
        logger.info(f"Found {len(device_ids)} devices from API: {device_ids}")
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        device_ids = ["wh-001", "wh-002", "wh-e0ae2f58"]
        logger.info(f"Using fallback device IDs: {device_ids}")

    for device_id in device_ids[:1]:  # Test first device
        logger.info(f"Testing temperature history for {device_id}")

        # Check details page
        try:
            resp = requests.get(f"{BASE_URL}/water-heaters/{device_id}")
            if resp.status_code != 200:
                logger.error(f"Failed to access details page: {resp.status_code}")
                continue

            html = resp.text
            # Check for chart containers
            import re

            chart_container_pattern = (
                r'class="[^"]*temperature[^"]*-(?:history|chart)[^"]*"'
            )
            chart_containers = re.findall(chart_container_pattern, html)
            logger.info(f"Found {len(chart_containers)} chart container elements")

            # Check specific chart elements
            chart_patterns = {
                "temp_history_container": r'class="[^"]*temp(?:erature)?[\-_]history[^"]*"',
                "temp_chart": r'class="[^"]*temp(?:erature)?[\-_]chart[^"]*"',
                "chart_id": r'id="temperatureHistoryChart"',
                "canvas": r"<canvas[^>]*>",
            }

            for name, pattern in chart_patterns.items():
                matches = re.findall(pattern, html)
                logger.info(f"  - {name}: {len(matches)} matches")

            # Extract chart initialization script
            script_content = ""
            if "initializeDetailsPageChart" in html:
                script_pattern = (
                    r"function\s+initializeDetailsPageChart\s*\([^)]*\)\s*\{([^}]*)\}"
                )
                scripts = re.findall(script_pattern, html)
                if scripts:
                    script_content = scripts[0]
                    logger.info(
                        f"Found chart initialization script: {len(script_content)} chars"
                    )
                    logger.info(f"Script snippet: {script_content[:100]}...")

            # Check for shadow error messages
            shadow_error_pattern = r"No shadow document exists"
            shadow_errors = re.findall(shadow_error_pattern, html)
            if shadow_errors:
                logger.info(
                    f"Found 'No shadow document exists' message: {len(shadow_errors)} occurrences"
                )

        except Exception as e:
            logger.error(f"Error analyzing details page: {e}")

        # Check API endpoints
        api_endpoints = [
            f"/api/device-shadows/{device_id}",
            f"/api/device-shadows/{device_id}/history",
            f"/api/device-shadows/{device_id}/time-series",
        ]

        for endpoint in api_endpoints:
            full_url = BASE_URL + endpoint
            try:
                resp = requests.get(full_url)
                status = resp.status_code
                logger.info(f"API endpoint {endpoint}: {status}")

                if status == 200:
                    data = resp.json()
                    if isinstance(data, list):
                        logger.info(f"  - Returned {len(data)} items")
                        if data:
                            logger.info(
                                f"  - First item sample: {json.dumps(data[0], default=str)[:100]}..."
                            )
                    elif isinstance(data, dict):
                        if "history" in data:
                            logger.info(
                                f"  - Contains history with {len(data['history'])} items"
                            )
            except Exception as e:
                logger.error(f"Error accessing {endpoint}: {e}")

        # Check loaded JavaScript console logs
        logger.info("\nChecking JS console for history loading issues:")
        try:
            response = requests.get(f"{BASE_URL}/water-heaters/{device_id}")
            html = response.text

            # Extract time-series-history-fix.js content
            script_url = "/static/js/time-series-history-fix.js"
            script_response = requests.get(f"{BASE_URL}{script_url}")
            if script_response.status_code == 200:
                js_content = script_response.text
                # Check for key functions
                key_functions = [
                    "applyHistoryFix",
                    "patchTemperatureHistoryMethod",
                    "getTemperatureHistory",
                    "triggerManualHistoryLoad",
                ]

                for func in key_functions:
                    if func in js_content:
                        logger.info(f"  - Found function: {func}")
                    else:
                        logger.warning(f"  - Missing function: {func}")

                # Look for error handling
                if "catch" in js_content and "error" in js_content:
                    logger.info("  - Contains error handling code")
            else:
                logger.error(
                    f"Failed to load {script_url}: {script_response.status_code}"
                )

        except Exception as e:
            logger.error(f"Error analyzing JS issues: {e}")


def check_database_connections():
    """Check if MongoDB is properly connected"""
    logger.info("\n" + "=" * 80)
    logger.info("CHECKING DATABASE CONNECTIONS")
    logger.info("=" * 80)

    # Check MongoDB connection
    try:
        import pymongo

        client = pymongo.MongoClient(
            "mongodb://localhost:27017/", serverSelectionTimeoutMS=5000
        )
        db = client["iotsphere"]

        # Check if collections exist
        collections = db.list_collection_names()
        logger.info(f"MongoDB collections: {collections}")

        # Check shadows
        if "shadows" in collections:
            shadows_count = db.shadows.count_documents({})
            logger.info(f"Found {shadows_count} shadows")

            # Check specific device
            for device_id in ["wh-001", "wh-002", "wh-e0ae2f58"]:
                shadow = db.shadows.find_one({"device_id": device_id})
                if shadow:
                    logger.info(f"Found shadow for {device_id}")
                    history = shadow.get("history", [])
                    logger.info(f"  - Has {len(history)} history entries")

        # Check history collection
        if "shadow_history" in collections:
            history_count = db.shadow_history.count_documents({})
            logger.info(f"Found {history_count} history entries")

            # Check specific device
            for device_id in ["wh-001", "wh-002", "wh-e0ae2f58"]:
                device_history = db.shadow_history.count_documents(
                    {"device_id": device_id}
                )
                logger.info(f"Found {device_history} history entries for {device_id}")

        client.close()

    except Exception as e:
        logger.error(f"Error checking MongoDB: {e}")
        import traceback

        logger.error(traceback.format_exc())


def main():
    """Run diagnostics"""
    logger.info("=" * 80)
    logger.info("DIRECT DIAGNOSTICS FOR IoTSphere ISSUES")
    logger.info("=" * 80)

    # Ensure server is running
    try:
        resp = requests.get(BASE_URL)
        if resp.status_code != 200:
            logger.error(f"Server returned status {resp.status_code}")
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to {BASE_URL}. Is the server running?")
        sys.exit(1)

    # Check database connections
    check_database_connections()

    # Diagnose list page duplication
    diagnose_list_page_duplication()

    # Diagnose temperature history
    diagnose_temperature_history()


if __name__ == "__main__":
    main()
