#!/usr/bin/env python3
"""
IoTSphere Data Flow Diagnostic Tool

This script:
1. Systematically examines each component of the data pipeline
2. Outputs raw data at each step to identify issues
3. Traces the flow of device IDs through each system component
4. Verifies shadow documents and history data
5. Checks frontend UI components

NO DATA MODIFICATIONS - Pure diagnostic tool
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pprint import pformat
from urllib.parse import urljoin

import motor.motor_asyncio
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:7080"
MONGODB_URI = "mongodb://localhost:27017/"
MONGODB_DB = "iotsphere"
SHADOWS_COLLECTION = "device_shadows"


class DataFlowDiagnostic:
    """Systematic diagnostic for IoTSphere data flow issues"""

    def __init__(self):
        self.mongodb_client = None

    async def check_assets_api(self):
        """Check the manufacturer water heaters API"""
        logger.info("=== CHECKING ASSET API ===")

        try:
            # Try both possible API endpoints
            api_endpoints = ["/api/manufacturer/water-heaters", "/api/water-heaters"]

            for endpoint in api_endpoints:
                url = urljoin(BASE_URL, endpoint)
                logger.info(f"Trying endpoint: {url}")

                response = requests.get(url)
                if response.status_code == 200:
                    logger.info(f"✅ API endpoint {endpoint} returned 200 OK")
                    try:
                        data = response.json()
                        logger.info(f"Found {len(data)} water heaters")

                        # Print first item sample
                        if data:
                            logger.info("Sample data (first item):")
                            logger.info(json.dumps(data[0], indent=2))

                            # Check for device_id field
                            if "device_id" in data[0]:
                                logger.info(
                                    f"✅ device_id field exists: {data[0]['device_id']}"
                                )
                            else:
                                logger.info(
                                    "❌ No device_id field found in response. Available fields:"
                                )
                                logger.info(", ".join(data[0].keys()))

                                # Try to identify an ID field with different name
                                id_candidates = [
                                    k for k in data[0].keys() if "id" in k.lower()
                                ]
                                if id_candidates:
                                    logger.info(f"Possible ID fields: {id_candidates}")
                    except json.JSONDecodeError:
                        logger.error(f"❌ Endpoint {endpoint} returned invalid JSON")
                        logger.info(f"Response content: {response.text[:500]}...")
                else:
                    logger.info(
                        f"❌ API endpoint {endpoint} returned {response.status_code}"
                    )

            # Check specific device API endpoint
            device_endpoints = [
                "/api/manufacturer/water-heaters/wh-001",
                "/api/water-heaters/wh-001",
            ]

            for endpoint in device_endpoints:
                url = urljoin(BASE_URL, endpoint)
                logger.info(f"Trying device endpoint: {url}")

                response = requests.get(url)
                if response.status_code == 200:
                    logger.info(f"✅ Device API endpoint {endpoint} returned 200 OK")
                    try:
                        data = response.json()
                        logger.info("Device data:")
                        logger.info(json.dumps(data, indent=2))
                    except json.JSONDecodeError:
                        logger.error(
                            f"❌ Device endpoint {endpoint} returned invalid JSON"
                        )
                else:
                    logger.info(
                        f"❌ Device API endpoint {endpoint} returned {response.status_code}"
                    )

        except Exception as e:
            logger.error(f"Error checking assets API: {e}")

    async def check_device_shadow_api(self):
        """Check the device shadow API"""
        logger.info("\n=== CHECKING DEVICE SHADOW API ===")

        try:
            # Try different shadow API endpoints
            shadow_endpoints = [
                "/api/device-shadows/wh-001",
                "/api/device-shadow/wh-001",
                "/api/shadows/wh-001",
                "/api/manufacturer/water-heaters/wh-001/shadow",
            ]

            for endpoint in shadow_endpoints:
                url = urljoin(BASE_URL, endpoint)
                logger.info(f"Trying shadow endpoint: {url}")

                response = requests.get(url)
                if response.status_code == 200:
                    logger.info(f"✅ Shadow API endpoint {endpoint} returned 200 OK")
                    try:
                        data = response.json()
                        logger.info("Shadow data:")
                        logger.info(json.dumps(data, indent=2))

                        # Check for history field
                        if "history" in data:
                            history = data["history"]
                            logger.info(
                                f"✅ Found history field with {len(history)} entries"
                            )
                            if history:
                                logger.info(f"First history entry: {history[0]}")
                                logger.info(f"Last history entry: {history[-1]}")
                        else:
                            logger.info("❌ No history field found in shadow document")
                    except json.JSONDecodeError:
                        logger.error(
                            f"❌ Shadow endpoint {endpoint} returned invalid JSON"
                        )
                else:
                    logger.info(
                        f"❌ Shadow API endpoint {endpoint} returned {response.status_code}"
                    )

            # Try history-specific endpoints
            history_endpoints = [
                "/api/device-shadows/wh-001/temperature-history",
                "/api/device-shadow/wh-001/history",
                "/api/manufacturer/water-heaters/wh-001/temperature-history",
            ]

            for endpoint in history_endpoints:
                url = urljoin(BASE_URL, endpoint)
                logger.info(f"Trying history endpoint: {url}")

                response = requests.get(url)
                if response.status_code == 200:
                    logger.info(f"✅ History API endpoint {endpoint} returned 200 OK")
                    try:
                        data = response.json()
                        logger.info(f"Found {len(data)} history entries")
                        if data:
                            logger.info(f"First history entry: {data[0]}")
                            logger.info(f"Last history entry: {data[-1]}")
                    except json.JSONDecodeError:
                        logger.error(
                            f"❌ History endpoint {endpoint} returned invalid JSON"
                        )
                else:
                    logger.info(
                        f"❌ History API endpoint {endpoint} returned {response.status_code}"
                    )

        except Exception as e:
            logger.error(f"Error checking device shadow API: {e}")

    async def check_mongodb_connection(self):
        """Check MongoDB connection and examine shadow documents"""
        logger.info("\n=== CHECKING MONGODB CONNECTION ===")

        try:
            # Connect to MongoDB
            client = motor.motor_asyncio.AsyncIOMotorClient(
                MONGODB_URI, serverSelectionTimeoutMS=5000
            )
            self.mongodb_client = client

            # Check connection
            await client.server_info()
            logger.info("✅ MongoDB connection successful")

            # Check database
            db = client[MONGODB_DB]

            # List collections
            collections = await db.list_collection_names()
            logger.info(f"Collections in database: {collections}")

            if SHADOWS_COLLECTION in collections:
                logger.info(f"✅ Found shadows collection: {SHADOWS_COLLECTION}")

                # Count shadow documents
                collection = db[SHADOWS_COLLECTION]
                count = await collection.count_documents({})
                logger.info(f"Found {count} shadow documents")

                # List all shadow document IDs
                cursor = collection.find({}, {"device_id": 1})
                shadow_docs = await cursor.to_list(length=100)
                shadow_ids = [
                    doc.get("device_id") for doc in shadow_docs if "device_id" in doc
                ]

                logger.info(f"Shadow document IDs: {shadow_ids}")

                # Check specific shadow documents
                test_ids = ["wh-001", "wh-002"]
                for device_id in test_ids:
                    shadow = await collection.find_one({"device_id": device_id})
                    if shadow:
                        logger.info(f"✅ Found shadow document for {device_id}")

                        # Check document structure
                        logger.info(f"Shadow structure for {device_id}:")
                        logger.info(f"  Keys: {list(shadow.keys())}")

                        # Check for reported state
                        if "reported" in shadow:
                            reported = shadow["reported"]
                            logger.info(f"  Reported state: {list(reported.keys())}")

                            # Check temperature
                            if "temperature" in reported:
                                logger.info(
                                    f"  Current temperature: {reported['temperature']}"
                                )
                        else:
                            logger.info("  ❌ No reported state found")

                        # Check for history data
                        if "history" in shadow:
                            history = shadow["history"]
                            logger.info(f"  History entries: {len(history)}")

                            # Check history structure
                            if history:
                                logger.info(f"  First history entry: {history[0]}")
                                logger.info(f"  Last history entry: {history[-1]}")

                                # Check for temperature in history entries
                                if "temperature" in history[0]:
                                    logger.info(
                                        "  ✅ History entries contain temperature field"
                                    )
                                else:
                                    logger.info(
                                        "  ❌ History entries missing temperature field"
                                    )
                                    logger.info(
                                        f"  Available fields: {list(history[0].keys())}"
                                    )
                        else:
                            logger.info("  ❌ No history data found")
                    else:
                        logger.info(f"❌ No shadow document found for {device_id}")
            else:
                logger.info(f"❌ Shadows collection {SHADOWS_COLLECTION} not found")

        except Exception as e:
            logger.error(f"Error checking MongoDB: {e}")

    async def check_ui_water_heaters_list(self):
        """Check the water heaters list page in the UI"""
        logger.info("\n=== CHECKING UI WATER HEATERS LIST PAGE ===")

        try:
            # Get the water heaters list page
            response = requests.get(urljoin(BASE_URL, "/water-heaters"))

            if response.status_code == 200:
                logger.info("✅ Water heaters list page loaded successfully")

                # Parse HTML
                soup = BeautifulSoup(response.text, "html.parser")

                # Save HTML for inspection
                with open("water_heaters_list.html", "w") as f:
                    f.write(soup.prettify())

                logger.info("Saved water heaters list HTML to water_heaters_list.html")

                # Look for device IDs in various ways
                logger.info("Searching for device IDs in page...")

                # Method 1: Table rows with data-device-id
                rows = soup.select("tr[data-device-id]")
                if rows:
                    device_ids = [row.get("data-device-id") for row in rows]
                    logger.info(
                        f"Found {len(device_ids)} devices using tr[data-device-id] selector"
                    )
                    logger.info(f"Device IDs: {device_ids}")

                # Method 2: Links to device detail pages
                links = soup.select('a[href^="/water-heaters/wh-"]')
                if links:
                    hrefs = [link.get("href") for link in links]
                    device_ids = [href.split("/")[-1] for href in hrefs]
                    logger.info(
                        f"Found {len(device_ids)} devices using links to detail pages"
                    )
                    logger.info(f"Device IDs: {device_ids}")

                # Method 3: Search for text pattern 'wh-xyz'
                import re

                text = soup.get_text()
                id_matches = re.findall(r"wh-[0-9a-zA-Z]+", text)
                if id_matches:
                    logger.info(
                        f"Found {len(set(id_matches))} device ID patterns in text"
                    )
                    logger.info(f"Device ID patterns: {list(set(id_matches))}")

                # Check page structure
                main_content = soup.select_one("main, #main, .main-content")
                if main_content:
                    logger.info("Found main content container")

                    # Look for table
                    tables = main_content.select("table")
                    if tables:
                        logger.info(f"Found {len(tables)} tables in main content")

                        # Check table headers
                        for i, table in enumerate(tables):
                            headers = table.select("th")
                            if headers:
                                header_text = [h.get_text(strip=True) for h in headers]
                                logger.info(f"Table {i+1} headers: {header_text}")
                    else:
                        logger.info("No tables found in main content")

                        # Look for cards or list items
                        cards = main_content.select(".card, .list-item")
                        if cards:
                            logger.info(f"Found {len(cards)} cards/list items")
                else:
                    logger.info("No main content container found")
            else:
                logger.info(
                    f"❌ Water heaters list page returned {response.status_code}"
                )

        except Exception as e:
            logger.error(f"Error checking UI water heaters list: {e}")

    async def check_ui_device_detail(self):
        """Check a device detail page in the UI"""
        logger.info("\n=== CHECKING UI DEVICE DETAIL PAGE ===")

        try:
            # Try to get a device detail page for wh-001
            response = requests.get(urljoin(BASE_URL, "/water-heaters/wh-001"))

            if response.status_code == 200:
                logger.info("✅ Device detail page for wh-001 loaded successfully")

                # Parse HTML
                soup = BeautifulSoup(response.text, "html.parser")

                # Save HTML for inspection
                with open("device_detail.html", "w") as f:
                    f.write(soup.prettify())

                logger.info("Saved device detail HTML to device_detail.html")

                # Look for temperature display
                temp_selectors = [
                    "#currentTemperature",
                    ".temperature-value",
                    ".current-temperature",
                    '[data-testid="temperature-display"]',
                ]

                for selector in temp_selectors:
                    temp_element = soup.select_one(selector)
                    if temp_element:
                        logger.info(
                            f"✅ Found temperature display using selector: {selector}"
                        )
                        logger.info(
                            f"Temperature text: {temp_element.get_text(strip=True)}"
                        )
                        break
                else:
                    logger.info("❌ No temperature display found using known selectors")

                # Look for temperature history chart
                chart_selectors = [
                    "#temperatureHistoryChart",
                    ".temperature-history-chart",
                    ".history-chart",
                    '[data-testid="temperature-history"]',
                ]

                for selector in chart_selectors:
                    chart_element = soup.select_one(selector)
                    if chart_element:
                        logger.info(
                            f"✅ Found temperature history chart container using selector: {selector}"
                        )

                        # Check for canvas element (chart)
                        canvas = chart_element.select_one("canvas")
                        if canvas:
                            logger.info(
                                "✅ Chart container has canvas element (chart is rendered)"
                            )
                        else:
                            logger.info("❌ No canvas element found in chart container")

                            # Check for error messages
                            error_element = chart_element.select_one(
                                ".error, .alert, .warning"
                            )
                            if error_element:
                                logger.info(
                                    f"Found error message: {error_element.get_text(strip=True)}"
                                )
                        break
                else:
                    logger.info(
                        "❌ No temperature history chart container found using known selectors"
                    )

                # Output page structure summary
                logger.info("Page structure summary:")

                # Check for main divs and sections
                main_sections = soup.select(
                    "main > div, main > section, #main > div, .main-content > div"
                )
                for i, section in enumerate(main_sections):
                    # Get the section ID or class
                    section_id = section.get("id", "")
                    section_class = " ".join(section.get("class", []))
                    section_identifier = section_id if section_id else section_class

                    logger.info(f"Section {i+1} ({section_identifier}):")

                    # List headings in this section
                    headings = section.select("h1, h2, h3, h4")
                    if headings:
                        heading_texts = [h.get_text(strip=True) for h in headings]
                        logger.info(f"  Headings: {heading_texts}")

                    # Check for specific content
                    if (
                        "temperature" in str(section).lower()
                        or "chart" in str(section).lower()
                    ):
                        logger.info(
                            f"  This section may contain temperature data or charts"
                        )
            else:
                logger.info(f"❌ Device detail page returned {response.status_code}")

                # Try alternative path
                alt_response = requests.get(urljoin(BASE_URL, "/water-heater/wh-001"))
                if alt_response.status_code == 200:
                    logger.info("✅ Alternative device detail page loaded successfully")
                else:
                    logger.info(
                        f"❌ Alternative device detail page also failed: {alt_response.status_code}"
                    )

        except Exception as e:
            logger.error(f"Error checking UI device detail: {e}")

    async def run_diagnostics(self):
        """Run all diagnostic checks"""
        try:
            logger.info("Starting IoTSphere Data Flow Diagnostics")
            logger.info(f"Testing against: {BASE_URL}")
            logger.info(f"MongoDB URI: {MONGODB_URI}")
            logger.info(f"Time: {datetime.now().isoformat()}")
            logger.info("-" * 80)

            # Run all checks
            await self.check_assets_api()
            await self.check_device_shadow_api()
            await self.check_mongodb_connection()
            await self.check_ui_water_heaters_list()
            await self.check_ui_device_detail()

            logger.info("\n=== DIAGNOSTICS COMPLETE ===")
            logger.info("Review the logs above to identify data flow issues")

        except Exception as e:
            logger.error(f"Error running diagnostics: {e}")
        finally:
            # Close MongoDB connection if open
            if self.mongodb_client:
                self.mongodb_client.close()


async def main():
    """Main function"""
    # Check if server is running
    try:
        response = requests.get(BASE_URL, timeout=2)
    except requests.ConnectionError:
        logger.error(f"Error: Cannot connect to {BASE_URL}")
        logger.error("Make sure the IoTSphere server is running")
        return 1

    # Run diagnostics
    diagnostic = DataFlowDiagnostic()
    await diagnostic.run_diagnostics()

    return 0


if __name__ == "__main__":
    # Install required packages if needed
    try:
        import bs4
        import motor
    except ImportError:
        print("Installing required packages...")
        os.system("pip install beautifulsoup4 motor requests")
        print("Packages installed, restarting script...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    sys.exit(asyncio.run(main()))
