#!/usr/bin/env python3
"""
Detail Page Diagnostics Tool

This script tests the water heater details page functionality by:
1. Checking if necessary API endpoints are available and returning data
2. Testing the shadow document API which is critical for the details page
3. Validating all required JavaScript files are accessible
4. Checking for client-side rendering issues

Usage:
    python -m src.tools.detail_page_diagnostics

Following TDD principles, this script first establishes expectations,
then tests against those expectations to identify issues.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

import httpx

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("detail-page-diagnostics")

# Constants
BASE_URL = "http://localhost:8006"
TEST_HEATER_ID = "aqua-wh-1001"  # Using a known AquaTherm ID that should work
REQUIRED_JS_FILES = [
    "/static/js/shadow-document-handler.js",
    "/static/js/api.js",
    "/static/js/water-heater-details-only.js",
    "/static/js/tab-manager.js",
    "/static/js/device-shadow-api.js",
    "/static/js/device-shadow-temperature-chart.js",
    "/static/js/device-shadow-chart-integration.js",
]


async def test_api_endpoints() -> Dict[str, bool]:
    """Test all API endpoints needed by the details page."""
    logger.info("Testing API endpoints...")
    results = {}
    endpoints = [
        f"/api/manufacturer/water-heaters/{TEST_HEATER_ID}",
        f"/api/device-shadow/{TEST_HEATER_ID}",
        f"/api/device-shadow/{TEST_HEATER_ID}/history",
        f"/api/predictions/water-heaters/{TEST_HEATER_ID}/all",
    ]

    async with httpx.AsyncClient() as client:
        for endpoint in endpoints:
            url = f"{BASE_URL}{endpoint}"
            try:
                logger.info(f"Testing endpoint: {url}")
                response = await client.get(url)
                if response.status_code == 200:
                    logger.info(f"✅ Endpoint {endpoint} is working (200 OK)")
                    # Check for valid JSON response
                    try:
                        data = response.json()
                        logger.info(
                            f"   Content: {json.dumps(data, indent=2)[:200]}..."
                        )
                        results[endpoint] = True
                    except json.JSONDecodeError:
                        logger.error(f"❌ Endpoint {endpoint} returned invalid JSON")
                        results[endpoint] = False
                else:
                    logger.error(
                        f"❌ Endpoint {endpoint} failed with status {response.status_code}"
                    )
                    logger.error(f"   Response: {response.text[:200]}...")
                    results[endpoint] = False
            except Exception as e:
                logger.error(f"❌ Error accessing {endpoint}: {str(e)}")
                results[endpoint] = False

    return results


async def test_html_response() -> Dict[str, Union[bool, str]]:
    """Test the HTML response of the details page."""
    logger.info(f"Testing HTML response for device {TEST_HEATER_ID}...")
    result = {"success": False, "error": None, "content": None}

    url = f"{BASE_URL}/water-heaters/{TEST_HEATER_ID}"
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Requesting details page: {url}")
            response = await client.get(url, follow_redirects=True)

            if response.status_code == 200:
                logger.info(f"✅ Details page loaded with status 200")
                # Check if we have the expected HTML content
                html_content = response.text
                required_elements = [
                    f'data-device-id="{TEST_HEATER_ID}"',
                    'id="water-heater-detail"',
                    'id="tab-manager"',
                    'id="device-shadow-handler"',
                ]

                all_found = True
                for element in required_elements:
                    if element not in html_content:
                        logger.error(f"❌ Required HTML element missing: {element}")
                        all_found = False
                    else:
                        logger.info(f"✅ Found element: {element}")

                result["success"] = all_found
                # Store the first 1000 characters for analysis
                result["content"] = html_content[:1000]

                if not all_found:
                    result["error"] = "Missing required HTML elements"
            else:
                logger.error(
                    f"❌ Details page failed with status {response.status_code}"
                )
                logger.error(f"   Response: {response.text[:200]}...")
                result["success"] = False
                result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
    except Exception as e:
        logger.error(f"❌ Error accessing details page: {str(e)}")
        result["success"] = False
        result["error"] = str(e)

    return result


async def test_js_file_availability() -> Dict[str, bool]:
    """Test if all required JavaScript files are available."""
    logger.info("Testing JavaScript file availability...")
    results = {}

    async with httpx.AsyncClient() as client:
        for js_file in REQUIRED_JS_FILES:
            url = f"{BASE_URL}{js_file}"
            try:
                logger.info(f"Testing JS file: {url}")
                response = await client.get(url)
                if response.status_code == 200:
                    logger.info(f"✅ JS file {js_file} is available")
                    results[js_file] = True
                else:
                    logger.error(
                        f"❌ JS file {js_file} returned status {response.status_code}"
                    )
                    results[js_file] = False
            except Exception as e:
                logger.error(f"❌ Error accessing JS file {js_file}: {str(e)}")
                results[js_file] = False

    return results


async def test_shadow_document_endpoint() -> Dict[str, Union[bool, Dict]]:
    """Test shadow document API specifically as it's critical for details page."""
    logger.info(f"Testing shadow document API for {TEST_HEATER_ID}...")
    result = {"success": False, "data": None, "error": None}

    url = f"{BASE_URL}/api/device-shadow/{TEST_HEATER_ID}"
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Requesting shadow document: {url}")
            response = await client.get(url)

            if response.status_code == 200:
                try:
                    shadow_data = response.json()
                    logger.info(f"✅ Shadow document API returned valid JSON")

                    # Inspect the shadow document for required fields
                    if "reported" in shadow_data:
                        logger.info(f"✅ Shadow document has 'reported' state")
                        if "temperature" in shadow_data["reported"]:
                            logger.info(f"✅ Shadow document has temperature data")
                            logger.info(
                                f"   Temperature: {shadow_data['reported']['temperature']}"
                            )
                        else:
                            logger.warning(
                                "⚠️ Shadow document missing temperature data"
                            )
                    else:
                        logger.error("❌ Shadow document missing 'reported' state")

                    result["success"] = True
                    result["data"] = shadow_data
                except json.JSONDecodeError:
                    logger.error(f"❌ Shadow document API returned invalid JSON")
                    result["error"] = "Invalid JSON in shadow document response"
            else:
                logger.error(
                    f"❌ Shadow document API failed with status {response.status_code}"
                )
                logger.error(f"   Response: {response.text[:200]}...")
                result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
    except Exception as e:
        logger.error(f"❌ Error accessing shadow document API: {str(e)}")
        result["error"] = str(e)

    return result


async def run_diagnostics():
    """Run all diagnostic tests and print a summary report."""
    logger.info("=" * 50)
    logger.info("WATER HEATER DETAILS PAGE DIAGNOSTICS")
    logger.info("=" * 50)

    # Run all tests
    api_results = await test_api_endpoints()
    html_result = await test_html_response()
    js_results = await test_js_file_availability()
    shadow_result = await test_shadow_document_endpoint()

    # Generate report
    logger.info("\n" + "=" * 50)
    logger.info("DIAGNOSTIC SUMMARY")
    logger.info("=" * 50)

    # API endpoints report
    logger.info("\nAPI ENDPOINTS:")
    all_api_ok = all(api_results.values())
    status = "✅ All endpoints OK" if all_api_ok else "❌ Some endpoints failing"
    logger.info(status)
    for endpoint, success in api_results.items():
        status = "✅" if success else "❌"
        logger.info(f"{status} {endpoint}")

    # HTML response report
    logger.info("\nHTML RESPONSE:")
    status = (
        "✅ Details page HTML OK"
        if html_result["success"]
        else f"❌ Details page HTML error: {html_result['error']}"
    )
    logger.info(status)

    # JavaScript files report
    logger.info("\nJAVASCRIPT FILES:")
    all_js_ok = all(js_results.values())
    status = "✅ All JS files available" if all_js_ok else "❌ Some JS files missing"
    logger.info(status)
    for js_file, success in js_results.items():
        status = "✅" if success else "❌"
        logger.info(f"{status} {js_file}")

    # Shadow document report
    logger.info("\nSHADOW DOCUMENT:")
    status = (
        "✅ Shadow document API OK"
        if shadow_result["success"]
        else f"❌ Shadow document error: {shadow_result['error']}"
    )
    logger.info(status)

    # Overall assessment
    logger.info("\n" + "=" * 50)
    logger.info("OVERALL ASSESSMENT")
    logger.info("=" * 50)

    if all_api_ok and html_result["success"] and all_js_ok and shadow_result["success"]:
        logger.info("✅ All tests passed. Details page should be working correctly.")
        logger.info(
            "If you're still experiencing issues, check browser console for client-side errors."
        )
    else:
        logger.info("❌ Some tests failed. Details page may not work correctly.")

        if not all_api_ok:
            logger.info(
                "⚠️ API endpoints failing. Check API implementation and routes."
            )

        if not html_result["success"]:
            logger.info(
                "⚠️ HTML template issues. Check template rendering and device data."
            )

        if not all_js_ok:
            logger.info(
                "⚠️ JavaScript files missing. Check static file paths and server configuration."
            )

        if not shadow_result["success"]:
            logger.info(
                "⚠️ Shadow document API failing. This is critical for temperature display."
            )

    logger.info("\n" + "=" * 50)
    logger.info("END OF DIAGNOSTICS")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(run_diagnostics())
