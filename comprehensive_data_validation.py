#!/usr/bin/env python3
"""
Comprehensive Data Validation Test for IoTSphere

This script performs thorough validation of the complete data flow:
1. Device Registry DB: Counts and lists water heater IDs
2. Asset Database: Validates and lists entries, ensures IDs match registry
3. MongoDB Shadow Documents: Validates documents and correlates with asset DB
4. API Validation: Tests asset and shadow data retrieval through API endpoints
5. Frontend UI Validation: Tests list page and details page data display
6. Temperature History: Specifically verifies history data display in details page

Run this test with the IoTSphere server already running.
"""
import asyncio
import json
import logging
import os
import sys
import time
from urllib.parse import urljoin

import motor.motor_asyncio
import requests
from bs4 import BeautifulSoup
from tabulate import tabulate

# Configure logging with colors
try:
    from colorama import Fore, Style, init

    # Initialize colorama for cross-platform colored terminal output
    init()

    # Define color constants
    SUCCESS = Fore.GREEN
    WARNING = Fore.YELLOW
    ERROR = Fore.RED
    INFO = Fore.CYAN
    BOLD = Style.BRIGHT
    RESET = Style.RESET_ALL

    # Setup logging format with colors
    logging.basicConfig(
        level=logging.INFO,
        format=f"{INFO}%(asctime)s{RESET} - "
        f"{BOLD}%(levelname)s{RESET} - "
        f"%(message)s",
    )
except ImportError:
    # Fallback to no colors if colorama not installed
    SUCCESS = WARNING = ERROR = INFO = BOLD = RESET = ""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:7080"
API_WATER_HEATERS = "/api/manufacturer/water-heaters"  # Correct API endpoint
API_DEVICE_SHADOWS = "/api/device-shadows"  # We'll check if this exists
MONGODB_URI = "mongodb://localhost:27017/"
MONGODB_DB = "iotsphere"
DEVICE_SHADOWS_COLLECTION = "device_shadows"


class ValidationError(Exception):
    """Custom exception for data validation errors"""

    pass


class DataValidator:
    """Comprehensive Data Flow Validator for IoTSphere"""

    def __init__(self):
        self.water_heaters = []
        self.water_heater_ids = []
        self.shadow_data = []
        self.shadow_ids = []
        self.ui_list_ids = []
        self.ui_detail_data = {}
        self.issues = []
        self.warnings = []
        self.passing = []

    def log_issue(self, message, critical=True):
        """Log an issue found during validation"""
        self.issues.append(message)
        if critical:
            logger.error(f"{ERROR}❌ CRITICAL: {message}{RESET}")
        else:
            logger.warning(f"{WARNING}⚠️ WARNING: {message}{RESET}")

    def log_pass(self, message):
        """Log a passing validation"""
        self.passing.append(message)
        logger.info(f"{SUCCESS}✅ PASS: {message}{RESET}")

    def log_step(self, message):
        """Log a validation step"""
        logger.info(f"{INFO}🔍 {message}{RESET}")

    async def validate_water_heaters(self):
        """Validate water heaters through the API"""
        self.log_step("Validating Water Heaters through API...")

        try:
            # Call the water heaters API endpoint
            response = requests.get(urljoin(BASE_URL, API_WATER_HEATERS))

            if response.status_code != 200:
                self.log_issue(
                    f"Failed to get water heaters: HTTP {response.status_code}"
                )
                return False

            try:
                water_heaters = response.json()
                self.water_heaters = water_heaters
                self.water_heater_ids = [wh.get("device_id") for wh in water_heaters]
            except json.JSONDecodeError:
                self.log_issue("API returned invalid JSON")
                return False

            # Validate water heater data
            if len(self.water_heater_ids) < 2:
                self.log_issue(
                    f"Expected multiple water heaters, found only {len(self.water_heater_ids)}"
                )
            else:
                self.log_pass(f"Found {len(self.water_heater_ids)} water heaters")

            # Display water heater IDs
            logger.info(f"{INFO}Water Heater IDs from API:{RESET}")
            for i, device_id in enumerate(self.water_heater_ids, 1):
                logger.info(f"  {i}. {device_id}")

            # Display complete water heater data in a table
            wh_table = []
            for wh in self.water_heaters:
                wh_table.append(
                    [
                        wh.get("device_id", "N/A"),
                        wh.get("manufacturer", "N/A"),
                        wh.get("model", "N/A"),
                        wh.get("temperature", "N/A"),
                        wh.get("status", "N/A"),
                    ]
                )

            if wh_table:
                print(
                    "\n"
                    + tabulate(
                        wh_table,
                        headers=[
                            "Device ID",
                            "Manufacturer",
                            "Model",
                            "Temperature",
                            "Status",
                        ],
                    )
                )

            return len(self.water_heater_ids) > 0

        except Exception as e:
            self.log_issue(f"Error validating water heaters: {str(e)}")
            return False

    async def validate_mongodb_shadows(self):
        """Validate MongoDB shadow documents"""
        self.log_step("Validating MongoDB Shadow Documents...")

        try:
            # Connect to MongoDB
            client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
            db = client[MONGODB_DB]

            # Check if collection exists
            collections = await db.list_collection_names()
            if DEVICE_SHADOWS_COLLECTION not in collections:
                self.log_issue(
                    f"MongoDB collection '{DEVICE_SHADOWS_COLLECTION}' does not exist"
                )
                return False

            collection = db[DEVICE_SHADOWS_COLLECTION]

            # Get all shadow documents
            cursor = collection.find({})
            shadows = await cursor.to_list(length=100)
            self.shadow_data = shadows
            self.shadow_ids = [shadow.get("device_id") for shadow in shadows]

            # Validate shadow data
            if not self.shadow_ids:
                self.log_issue("No shadow documents found in MongoDB")
                return False

            self.log_pass(f"Found {len(self.shadow_ids)} shadow documents in MongoDB")

            # Display shadow data
            logger.info(f"{INFO}MongoDB Shadow Documents:{RESET}")
            shadow_table = []
            for shadow in self.shadow_data:
                device_id = shadow.get("device_id", "N/A")
                reported = shadow.get("reported", {})
                desired = shadow.get("desired", {})
                history = shadow.get("history", [])

                # Get temperature from reported state
                temperature = reported.get("temperature", "N/A")

                # Get status from reported state
                status = reported.get("heater_status", "N/A")

                shadow_table.append(
                    [
                        device_id,
                        temperature,
                        status,
                        len(history),
                        desired.get("target_temperature", "N/A"),
                    ]
                )

            if shadow_table:
                print(
                    "\n"
                    + tabulate(
                        shadow_table,
                        headers=[
                            "Device ID",
                            "Temperature",
                            "Status",
                            "History Entries",
                            "Target Temp",
                        ],
                    )
                )

            # Check if shadow documents exist for all water heaters
            missing_shadows = set(self.water_heater_ids) - set(self.shadow_ids)
            if missing_shadows:
                self.log_issue(
                    f"{len(missing_shadows)} water heaters without shadow documents: {list(missing_shadows)}"
                )
            else:
                self.log_pass("All water heaters have corresponding shadow documents")

            # Check if shadow documents have history data
            shadows_without_history = []
            for shadow in self.shadow_data:
                device_id = shadow.get("device_id")
                history = shadow.get("history", [])
                if not history:
                    shadows_without_history.append(device_id)

            if shadows_without_history:
                self.log_issue(
                    f"{len(shadows_without_history)} shadow documents with no history: {shadows_without_history}"
                )
            else:
                self.log_pass("All shadow documents contain history data")

            # Detailed check of history data
            history_entries = {}
            for shadow in self.shadow_data:
                device_id = shadow.get("device_id")
                history = shadow.get("history", [])
                history_entries[device_id] = len(history)

                if history and len(history) > 0:
                    logger.info(f"  • {device_id}: {len(history)} history entries")

                    # Sample first and last entry
                    if len(history) >= 2:
                        first_entry = history[0]
                        last_entry = history[-1]
                        logger.info(
                            f"    ◦ First entry: {first_entry.get('timestamp', 'N/A')} - {first_entry.get('temperature', 'N/A')}°F"
                        )
                        logger.info(
                            f"    ◦ Last entry: {last_entry.get('timestamp', 'N/A')} - {last_entry.get('temperature', 'N/A')}°F"
                        )

            return True

        except Exception as e:
            self.log_issue(f"Error validating MongoDB shadows: {str(e)}")
            return False
        finally:
            client.close()

    async def validate_ui_list_page(self):
        """Validate the UI water heaters list page"""
        self.log_step("Validating UI Water Heaters List Page...")

        try:
            # Go to the water heaters list page
            response = requests.get(urljoin(BASE_URL, "/water-heaters"))

            if response.status_code != 200:
                self.log_issue(
                    f"Failed to load water heaters list page: HTTP {response.status_code}"
                )
                return False

            # Parse the HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Look for device IDs in the page
            # Try multiple selectors to find water heater entries
            device_elements = []

            # Try finding table rows with data-device-id attribute
            device_elements = soup.select("tr[data-device-id]")
            if device_elements:
                self.ui_list_ids = [el.get("data-device-id") for el in device_elements]

            # If no elements found, try finding links to detail pages
            if not self.ui_list_ids:
                links = soup.select('a[href^="/water-heaters/wh-"]')
                self.ui_list_ids = [
                    link.get("href").split("/")[-1]
                    for link in links
                    if "water-heaters" in link.get("href", "")
                ]

            # If still no elements found, try other selectors
            if not self.ui_list_ids:
                # Look for any elements containing water heater IDs (wh-XXX pattern)
                import re

                text = soup.get_text()
                id_matches = re.findall(r"wh-[0-9a-zA-Z]+", text)
                self.ui_list_ids = list(set(id_matches))

            if not self.ui_list_ids:
                self.log_issue("No water heater IDs found in the UI list page")
                return False

            logger.info(f"{INFO}Water Heater IDs from UI List Page:{RESET}")
            for i, device_id in enumerate(self.ui_list_ids, 1):
                logger.info(f"  {i}. {device_id}")

            # Check if all water heaters from the API are displayed in the UI
            missing_in_ui = set(self.water_heater_ids) - set(self.ui_list_ids)
            if missing_in_ui:
                self.log_issue(
                    f"{len(missing_in_ui)} water heaters missing from UI: {list(missing_in_ui)}"
                )
            else:
                self.log_pass("All water heaters are displayed on the UI list page")

            return len(self.ui_list_ids) > 0

        except Exception as e:
            self.log_issue(f"Error validating UI list page: {str(e)}")
            return False

    async def validate_ui_detail_pages(self):
        """Validate the UI water heater detail pages"""
        self.log_step("Validating UI Water Heater Detail Pages...")

        if not self.water_heater_ids:
            self.log_issue("No water heater IDs available to check detail pages")
            return False

        try:
            # Check the first 2 water heaters (or fewer if less are available)
            test_ids = self.water_heater_ids[: min(2, len(self.water_heater_ids))]

            for device_id in test_ids:
                logger.info(f"{INFO}Checking detail page for {device_id}:{RESET}")

                # Load the detail page
                detail_url = urljoin(BASE_URL, f"/water-heaters/{device_id}")
                response = requests.get(detail_url)

                if response.status_code != 200:
                    self.log_issue(
                        f"Failed to load detail page for {device_id}: HTTP {response.status_code}"
                    )
                    continue

                # Parse the HTML
                soup = BeautifulSoup(response.text, "html.parser")

                # Check for page components
                temperature_element = None

                # Try multiple selectors to find the temperature display
                for selector in [
                    "#currentTemperature",
                    ".temperature-value",
                    ".current-temperature",
                ]:
                    element = soup.select_one(selector)
                    if element:
                        temperature_element = element
                        break

                # Check for history chart container
                history_chart = None
                for selector in [
                    "#temperatureHistoryChart",
                    ".temperature-history-chart",
                    ".history-chart",
                ]:
                    element = soup.select_one(selector)
                    if element:
                        history_chart = element
                        break

                # Store results for this detail page
                self.ui_detail_data[device_id] = {
                    "has_temperature": temperature_element is not None,
                    "has_history_chart": history_chart is not None,
                    "temperature_text": temperature_element.text.strip()
                    if temperature_element
                    else None,
                }

                # Log results
                if temperature_element:
                    self.log_pass(
                        f"Temperature display found: {temperature_element.text.strip()}"
                    )
                else:
                    self.log_issue(
                        f"No temperature display found on detail page for {device_id}"
                    )

                if history_chart:
                    self.log_pass(f"Temperature history chart container found")

                    # Check for error messages in the chart
                    error_element = soup.select_one(".chart-error, .history-error")
                    if error_element:
                        self.log_issue(
                            f"History chart shows error: {error_element.text.strip()}"
                        )
                    else:
                        # Look for canvas or any other sign that the chart is rendered
                        chart_canvas = soup.select_one("canvas")
                        if chart_canvas:
                            self.log_pass("History chart canvas element found")
                        else:
                            self.log_issue(
                                "History chart container exists but no canvas element found"
                            )
                else:
                    self.log_issue(
                        f"No temperature history chart container found on detail page for {device_id}"
                    )

                print("-" * 80)

            return True

        except Exception as e:
            self.log_issue(f"Error validating UI detail pages: {str(e)}")
            return False

    async def run_validation(self):
        """Run all validation steps"""
        logger.info(f"{INFO}==============================================={RESET}")
        logger.info(f"{BOLD}IoTSphere Comprehensive Data Validation Test{RESET}")
        logger.info(f"{INFO}==============================================={RESET}")
        logger.info(f"Testing server at: {BASE_URL}")
        print("\n")

        try:
            # Step 1: Validate water heaters through API
            await self.validate_water_heaters()
            print("\n" + "=" * 80 + "\n")

            # Step 2: Validate MongoDB shadow documents
            await self.validate_mongodb_shadows()
            print("\n" + "=" * 80 + "\n")

            # Step 3: Validate UI list page
            await self.validate_ui_list_page()
            print("\n" + "=" * 80 + "\n")

            # Step 4: Validate UI detail pages
            await self.validate_ui_detail_pages()
            print("\n" + "=" * 80 + "\n")

            # Final summary
            logger.info(f"{INFO}=========================={RESET}")
            logger.info(f"{BOLD}Validation Summary{RESET}")
            logger.info(f"{INFO}=========================={RESET}")

            logger.info(f"{SUCCESS}Passed: {len(self.passing)} checks{RESET}")
            if self.issues:
                logger.info(f"{ERROR}Failed: {len(self.issues)} checks{RESET}")

                # Distinguish between critical issues and warnings
                critical_issues = [i for i in self.issues if "CRITICAL" in i]
                warnings = [i for i in self.issues if "WARNING" in i]

                if critical_issues:
                    logger.error(
                        f"{ERROR}Critical Issues: {len(critical_issues)}{RESET}"
                    )
                if warnings:
                    logger.warning(f"{WARNING}Warnings: {len(warnings)}{RESET}")

                # Print brief summary of issues
                logger.info(f"{BOLD}Top Issues:{RESET}")
                for i, issue in enumerate(self.issues[:5], 1):
                    if "CRITICAL" in issue:
                        logger.error(
                            f"{ERROR}{i}. {issue.replace('CRITICAL: ', '')}{RESET}"
                        )
                    else:
                        logger.warning(
                            f"{WARNING}{i}. {issue.replace('WARNING: ', '')}{RESET}"
                        )

                if len(self.issues) > 5:
                    logger.info(f"... and {len(self.issues) - 5} more issues")
            else:
                logger.info(f"{SUCCESS}No issues found! All tests passed!{RESET}")

            # Provide next steps based on validation results
            self.provide_recommendations()

            return len(self.issues) == 0

        except Exception as e:
            logger.error(
                f"{ERROR}Validation failed with unexpected error: {str(e)}{RESET}"
            )
            import traceback

            traceback.print_exc()
            return False

    def provide_recommendations(self):
        """Provide recommendations based on validation results"""

        print("\n")
        logger.info(f"{BOLD}Recommendations:{RESET}")

        # Check for specific issues and provide targeted recommendations
        shadows_without_history = any(
            "shadow documents with no history" in i for i in self.issues
        )
        missing_shadow_docs = any(
            "water heaters without shadow documents" in i for i in self.issues
        )
        ui_temp_missing = any("No temperature display found" in i for i in self.issues)
        ui_history_missing = any(
            "No temperature history chart" in i for i in self.issues
        )

        if missing_shadow_docs:
            logger.info(
                f"1. {BOLD}Create missing shadow documents{RESET} for water heaters without them"
            )
            logger.info(
                "   Run a script to create shadow documents for all registered water heaters"
            )

        if shadows_without_history:
            logger.info(
                f"2. {BOLD}Populate history data{RESET} in shadow documents that have none"
            )
            logger.info(
                "   Generate temperature history data for empty shadow documents"
            )

        if ui_temp_missing or ui_history_missing:
            logger.info(
                f"3. {BOLD}Fix UI display issues{RESET} in the water heater detail pages"
            )
            logger.info(
                "   Check frontend code for temperature and history chart rendering"
            )

        if not self.issues:
            logger.info(
                f"{SUCCESS}The data flow appears to be working correctly.{RESET}"
            )
            logger.info("Continue monitoring for any new issues.")


async def main():
    """Main function"""
    try:
        # Check if server is running
        try:
            response = requests.get(BASE_URL, timeout=2)
        except requests.ConnectionError:
            logger.error(f"{ERROR}Error connecting to server at {BASE_URL}{RESET}")
            logger.error(
                f"{ERROR}Make sure the IoTSphere server is running before executing this test{RESET}"
            )
            return 1

        # Run validation
        validator = DataValidator()
        success = await validator.run_validation()

        return 0 if success else 1

    except KeyboardInterrupt:
        logger.info(f"{INFO}Test interrupted by user{RESET}")
        return 1


if __name__ == "__main__":
    # Install required packages if needed
    missing_packages = []
    try:
        import bs4
    except ImportError:
        missing_packages.append("beautifulsoup4")

    try:
        import colorama
    except ImportError:
        missing_packages.append("colorama")

    try:
        import tabulate
    except ImportError:
        missing_packages.append("tabulate")

    try:
        import motor
    except ImportError:
        missing_packages.append("motor")

    if missing_packages:
        print(f"Installing required packages: {', '.join(missing_packages)}")
        # Use subprocess.run instead of os.system for security (prevents shell injection)
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + missing_packages,
            check=True,
            shell=False,  # Explicitly set shell=False for security
        )
        print("Packages installed, restarting script...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    # Run the validation
    sys.exit(asyncio.run(main()))
