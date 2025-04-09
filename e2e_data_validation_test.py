#!/usr/bin/env python3
"""
End-to-End Data Validation Test for IoTSphere

This script performs comprehensive validation of data flow across all system components:
1. Device Registry data validation
2. Asset Database validation and correlation with Registry
3. MongoDB Shadow Documents validation and correlation with Asset DB
4. API validation for both Asset DB and Device Shadow data
5. Frontend UI validation for Assets and Device Shadows
6. Specific validation of history data in UI components

IMPORTANT: This test must be run with the IoTSphere server already running
"""
import asyncio
import json
import logging
import os
import sys
from pprint import pformat
from urllib.parse import urljoin

import motor.motor_asyncio
import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
from tabulate import tabulate

# Initialize colorama for cross-platform colored terminal output
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=f"{Fore.CYAN}%(asctime)s{Style.RESET_ALL} - "
    f"{Fore.GREEN}%(levelname)s{Style.RESET_ALL} - "
    f"%(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:7080"
API_BASE_URL = urljoin(BASE_URL, "/api/")
MONGODB_URI = "mongodb://localhost:27017/"
MONGODB_DB = "iotsphere"
DEVICE_SHADOWS_COLLECTION = "device_shadows"


class ValidationError(Exception):
    """Custom exception for data validation errors"""

    pass


class RegistryData:
    """Container for Registry Data"""

    def __init__(self):
        self.devices = []
        self.device_ids = []


class AssetData:
    """Container for Asset DB Data"""

    def __init__(self):
        self.assets = []
        self.asset_ids = []


class ShadowData:
    """Container for Shadow Data"""

    def __init__(self):
        self.shadows = []
        self.shadow_ids = []


class UIData:
    """Container for UI Data"""

    def __init__(self):
        self.list_page_ids = []
        self.detail_pages = {}


class DataValidator:
    """Comprehensive Data Validator for IoTSphere"""

    def __init__(self):
        self.registry_data = RegistryData()
        self.asset_data = AssetData()
        self.shadow_data = ShadowData()
        self.ui_data = UIData()
        self.issues = []
        self.warnings = []
        self.passing = []
        self.has_critical_issues = False

    def log_issue(self, message, critical=True):
        """Log an issue found during validation"""
        self.issues.append(message)
        if critical:
            self.has_critical_issues = True
            logger.error(f"{Fore.RED}❌ CRITICAL: {message}{Style.RESET_ALL}")
        else:
            logger.warning(f"{Fore.YELLOW}⚠️ WARNING: {message}{Style.RESET_ALL}")

    def log_pass(self, message):
        """Log a passing validation"""
        self.passing.append(message)
        logger.info(f"{Fore.GREEN}✅ PASS: {message}{Style.RESET_ALL}")

    def log_step(self, message):
        """Log a validation step"""
        logger.info(f"{Fore.BLUE}🔍 {message}{Style.RESET_ALL}")

    async def validate_registry_data(self):
        """Validate device registry data"""
        self.log_step("Validating Device Registry data...")

        try:
            # Call registry API endpoint
            response = requests.get(urljoin(API_BASE_URL, "devices"))
            if response.status_code != 200:
                self.log_issue(
                    f"Failed to get registry data: HTTP {response.status_code}"
                )
                return False

            registry_data = response.json()
            self.registry_data.devices = registry_data
            self.registry_data.device_ids = [
                device.get("device_id") for device in registry_data
            ]

            # Validate registry data
            if len(self.registry_data.device_ids) < 8:
                self.log_issue(
                    f"Expected at least 8 water heaters, found only {len(self.registry_data.device_ids)}"
                )
            else:
                self.log_pass(
                    f"Found {len(self.registry_data.device_ids)} devices in registry"
                )

            # Display device IDs
            logger.info(f"{Fore.CYAN}Registry Device IDs:{Style.RESET_ALL}")
            for i, device_id in enumerate(self.registry_data.device_ids, 1):
                logger.info(f"  {i}. {device_id}")

            if not self.registry_data.device_ids:
                self.log_issue("No devices found in registry")
                return False

            return len(self.registry_data.device_ids) > 0

        except Exception as e:
            self.log_issue(f"Error validating registry data: {str(e)}")
            return False

    async def validate_asset_data(self):
        """Validate asset database data and correlation with registry"""
        self.log_step("Validating Asset Database data...")

        try:
            # Call asset API endpoint
            response = requests.get(urljoin(API_BASE_URL, "water-heaters"))
            if response.status_code != 200:
                self.log_issue(f"Failed to get asset data: HTTP {response.status_code}")
                return False

            asset_data = response.json()
            self.asset_data.assets = asset_data
            self.asset_data.asset_ids = [asset.get("device_id") for asset in asset_data]

            # Validate asset data
            if len(self.asset_data.asset_ids) < 8:
                self.log_issue(
                    f"Expected at least 8 water heaters in asset DB, found only {len(self.asset_data.asset_ids)}"
                )
            else:
                self.log_pass(
                    f"Found {len(self.asset_data.asset_ids)} water heaters in asset DB"
                )

            # Display asset data
            logger.info(f"{Fore.CYAN}Asset Database entries:{Style.RESET_ALL}")
            asset_table = []
            for asset in self.asset_data.assets:
                asset_table.append(
                    [
                        asset.get("device_id"),
                        asset.get("manufacturer"),
                        asset.get("model"),
                        asset.get("location"),
                    ]
                )

            if asset_table:
                print(
                    tabulate(
                        asset_table,
                        headers=["Device ID", "Manufacturer", "Model", "Location"],
                    )
                )

            # Check correlation with registry
            missing_in_registry = set(self.asset_data.asset_ids) - set(
                self.registry_data.device_ids
            )
            missing_in_asset = set(self.registry_data.device_ids) - set(
                self.asset_data.asset_ids
            )

            if missing_in_registry:
                self.log_issue(
                    f"Found {len(missing_in_registry)} device(s) in asset DB but not in registry: {list(missing_in_registry)}",
                    critical=False,
                )
            if missing_in_asset:
                self.log_issue(
                    f"Found {len(missing_in_asset)} device(s) in registry but not in asset DB: {list(missing_in_asset)}",
                    critical=False,
                )

            if not missing_in_registry and not missing_in_asset:
                self.log_pass("Perfect correlation between registry and asset DB")

            return len(self.asset_data.asset_ids) > 0

        except Exception as e:
            self.log_issue(f"Error validating asset data: {str(e)}")
            return False

    async def validate_shadow_data(self):
        """Validate MongoDB shadow documents and correlation with asset DB"""
        self.log_step("Validating MongoDB Shadow Documents...")

        try:
            # Connect to MongoDB
            client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
            db = client[MONGODB_DB]
            collection = db[DEVICE_SHADOWS_COLLECTION]

            # Get all shadow documents
            cursor = collection.find({})
            shadows = await cursor.to_list(length=100)
            self.shadow_data.shadows = shadows
            self.shadow_data.shadow_ids = [
                shadow.get("device_id") for shadow in shadows
            ]

            # Validate shadow data
            if len(self.shadow_data.shadow_ids) < 8:
                self.log_issue(
                    f"Expected at least 8 shadow documents, found only {len(self.shadow_data.shadow_ids)}"
                )
            else:
                self.log_pass(
                    f"Found {len(self.shadow_data.shadow_ids)} shadow documents in MongoDB"
                )

            # Display shadow data
            logger.info(f"{Fore.CYAN}Shadow Documents:{Style.RESET_ALL}")
            shadow_table = []
            for shadow in self.shadow_data.shadows:
                device_id = shadow.get("device_id")
                reported = shadow.get("reported", {})
                history = shadow.get("history", [])
                shadow_table.append(
                    [
                        device_id,
                        reported.get("temperature", "N/A"),
                        len(history),
                        history[0]["timestamp"] if history else "N/A",
                        history[-1]["timestamp"] if history else "N/A",
                    ]
                )

            if shadow_table:
                print(
                    tabulate(
                        shadow_table,
                        headers=[
                            "Device ID",
                            "Current Temp",
                            "History Count",
                            "Oldest Entry",
                            "Newest Entry",
                        ],
                    )
                )

            # Check correlation with asset DB
            missing_in_asset = set(self.shadow_data.shadow_ids) - set(
                self.asset_data.asset_ids
            )
            missing_in_shadow = set(self.asset_data.asset_ids) - set(
                self.shadow_data.shadow_ids
            )

            if missing_in_asset:
                self.log_issue(
                    f"Found {len(missing_in_asset)} shadow(s) without matching asset: {list(missing_in_asset)}",
                    critical=False,
                )
            if missing_in_shadow:
                self.log_issue(
                    f"Found {len(missing_in_shadow)} asset(s) without shadow documents: {list(missing_in_shadow)}"
                )

            if not missing_in_asset and not missing_in_shadow:
                self.log_pass(
                    "Perfect correlation between shadow documents and asset DB"
                )

            # Validate each shadow document has history data
            missing_history = [
                s.get("device_id")
                for s in self.shadow_data.shadows
                if len(s.get("history", [])) == 0
            ]
            if missing_history:
                self.log_issue(
                    f"Found {len(missing_history)} shadow document(s) with empty history: {missing_history}"
                )
            else:
                self.log_pass("All shadow documents have history data")

            return len(self.shadow_data.shadow_ids) > 0

        except Exception as e:
            self.log_issue(f"Error validating shadow data: {str(e)}")
            return False
        finally:
            client.close()

    async def validate_api_calls(self):
        """Test API calls for both asset and shadow data"""
        self.log_step("Validating API endpoints...")

        try:
            # Test asset list API
            asset_response = requests.get(urljoin(API_BASE_URL, "water-heaters"))
            if asset_response.status_code != 200:
                self.log_issue(
                    f"Asset list API failed: HTTP {asset_response.status_code}"
                )
            else:
                self.log_pass("Asset list API returns 200 OK")

            # Test a few individual asset APIs
            if self.asset_data.asset_ids:
                test_ids = self.asset_data.asset_ids[:3]  # Test first 3 IDs
                for device_id in test_ids:
                    # Test asset detail API
                    detail_url = urljoin(API_BASE_URL, f"water-heaters/{device_id}")
                    detail_response = requests.get(detail_url)
                    if detail_response.status_code != 200:
                        self.log_issue(
                            f"Asset detail API for {device_id} failed: HTTP {detail_response.status_code}"
                        )
                    else:
                        self.log_pass(
                            f"Asset detail API for {device_id} returns 200 OK"
                        )

                    # Test shadow API
                    shadow_url = urljoin(API_BASE_URL, f"device-shadows/{device_id}")
                    shadow_response = requests.get(shadow_url)
                    if shadow_response.status_code != 200:
                        self.log_issue(
                            f"Shadow API for {device_id} failed: HTTP {shadow_response.status_code}"
                        )
                    else:
                        shadow_data = shadow_response.json()
                        if "history" in shadow_data and shadow_data["history"]:
                            self.log_pass(
                                f"Shadow API for {device_id} returns history data with {len(shadow_data['history'])} entries"
                            )
                        else:
                            self.log_issue(
                                f"Shadow API for {device_id} returns no history data"
                            )

                    # Test temperature history API
                    history_url = urljoin(
                        API_BASE_URL, f"device-shadows/{device_id}/temperature-history"
                    )
                    history_response = requests.get(history_url)
                    if history_response.status_code != 200:
                        self.log_issue(
                            f"Temperature history API for {device_id} failed: HTTP {history_response.status_code}"
                        )
                    else:
                        history_data = history_response.json()
                        if history_data and len(history_data) > 0:
                            self.log_pass(
                                f"Temperature history API for {device_id} returns {len(history_data)} data points"
                            )
                        else:
                            self.log_issue(
                                f"Temperature history API for {device_id} returns empty data"
                            )

            return True

        except Exception as e:
            self.log_issue(f"Error validating API calls: {str(e)}")
            return False

    async def validate_ui_data(self):
        """Validate frontend UI data for assets and device shadows"""
        self.log_step("Validating frontend UI data...")

        try:
            # Check water heaters list page
            list_response = requests.get(BASE_URL + "/water-heaters")
            if list_response.status_code != 200:
                self.log_issue(
                    f"List page failed to load: HTTP {list_response.status_code}"
                )
                return False

            # Parse HTML to extract device IDs from list page
            list_soup = BeautifulSoup(list_response.text, "html.parser")
            device_rows = list_soup.select("tr[data-device-id]")
            self.ui_data.list_page_ids = [
                row.get("data-device-id")
                for row in device_rows
                if row.get("data-device-id")
            ]

            if not self.ui_data.list_page_ids:
                # Try alternative selectors if data-device-id isn't found
                device_links = list_soup.select('a[href^="/water-heaters/wh-"]')
                self.ui_data.list_page_ids = list(
                    set(
                        [
                            link.get("href").split("/")[-1]
                            for link in device_links
                            if link.get("href")
                            and link.get("href").startswith("/water-heaters/wh-")
                        ]
                    )
                )

            logger.info(f"{Fore.CYAN}UI List Page Device IDs:{Style.RESET_ALL}")
            for i, device_id in enumerate(self.ui_data.list_page_ids, 1):
                logger.info(f"  {i}. {device_id}")

            # Check if list page contains all expected device IDs
            missing_in_ui = set(self.asset_data.asset_ids) - set(
                self.ui_data.list_page_ids
            )
            if missing_in_ui:
                self.log_issue(
                    f"Found {len(missing_in_ui)} device(s) missing from UI list page: {list(missing_in_ui)}"
                )
            else:
                self.log_pass("All assets are displayed on the UI list page")

            # Check detail pages for first 3 devices
            test_ids = (
                self.asset_data.asset_ids[:3] if self.asset_data.asset_ids else []
            )
            for device_id in test_ids:
                detail_url = f"{BASE_URL}/water-heaters/{device_id}"
                detail_response = requests.get(detail_url)
                if detail_response.status_code != 200:
                    self.log_issue(
                        f"Detail page for {device_id} failed to load: HTTP {detail_response.status_code}"
                    )
                    continue

                # Parse HTML to extract temperature and history data
                detail_soup = BeautifulSoup(detail_response.text, "html.parser")

                # Check for temperature display
                temp_element = detail_soup.select_one(
                    ".current-temperature, #currentTemperature"
                )
                if temp_element:
                    self.log_pass(
                        f"Detail page for {device_id} shows temperature: {temp_element.text.strip()}"
                    )
                else:
                    self.log_issue(
                        f"Detail page for {device_id} missing temperature display"
                    )

                # Check for history chart
                history_container = detail_soup.select_one(
                    "#temperatureHistoryChart, .temperature-history-chart"
                )
                if history_container:
                    self.log_pass(
                        f"Detail page for {device_id} has temperature history chart container"
                    )

                    # Check for error messages in history container
                    error_msg = detail_soup.select_one(".history-error, .chart-error")
                    if error_msg:
                        self.log_issue(
                            f"History chart for {device_id} shows error: {error_msg.text.strip()}"
                        )
                else:
                    self.log_issue(
                        f"Detail page for {device_id} missing temperature history chart"
                    )

                # Store detail page info
                self.ui_data.detail_pages[device_id] = {
                    "has_temperature": temp_element is not None,
                    "has_history_chart": history_container is not None,
                }

            return True

        except Exception as e:
            self.log_issue(f"Error validating UI data: {str(e)}")
            return False

    async def run_validation(self):
        """Run all validation steps"""
        try:
            logger.info(
                f"{Fore.GREEN}===================================================={Style.RESET_ALL}"
            )
            logger.info(
                f"{Fore.GREEN}= IoTSphere End-to-End Data Validation Test Suite ={Style.RESET_ALL}"
            )
            logger.info(
                f"{Fore.GREEN}===================================================={Style.RESET_ALL}"
            )
            logger.info(f"Testing against server: {BASE_URL}")

            # Step 1: Validate registry data
            reg_valid = await self.validate_registry_data()
            print("\n")

            if not reg_valid:
                self.log_issue("Registry validation failed, cannot continue")
                return False

            # Step 2: Validate asset data
            asset_valid = await self.validate_asset_data()
            print("\n")

            if not asset_valid:
                self.log_issue("Asset validation failed, cannot continue")
                return False

            # Step 3: Validate shadow data
            shadow_valid = await self.validate_shadow_data()
            print("\n")

            # Step 4: Validate API calls
            await self.validate_api_calls()
            print("\n")

            # Step 5: Validate UI data
            await self.validate_ui_data()
            print("\n")

            # Final summary
            logger.info(f"{Fore.GREEN}====================={Style.RESET_ALL}")
            logger.info(f"{Fore.GREEN}= Validation Summary ={Style.RESET_ALL}")
            logger.info(f"{Fore.GREEN}====================={Style.RESET_ALL}")

            logger.info(
                f"{Fore.GREEN}Passed: {len(self.passing)} checks{Style.RESET_ALL}"
            )
            if self.issues:
                logger.info(
                    f"{Fore.RED}Failed: {len(self.issues)} checks{Style.RESET_ALL}"
                )

                critical_issues = [i for i in self.issues if "CRITICAL" in i]
                warnings = [i for i in self.issues if "WARNING" in i]

                if critical_issues:
                    logger.info(
                        f"{Fore.RED}Critical Issues: {len(critical_issues)}{Style.RESET_ALL}"
                    )
                if warnings:
                    logger.info(
                        f"{Fore.YELLOW}Warnings: {len(warnings)}{Style.RESET_ALL}"
                    )
            else:
                logger.info(
                    f"{Fore.GREEN}No issues found! All tests passed!{Style.RESET_ALL}"
                )

            return not self.has_critical_issues

        except Exception as e:
            logger.error(
                f"{Fore.RED}Validation failed with error: {str(e)}{Style.RESET_ALL}"
            )
            import traceback

            traceback.print_exc()
            return False


async def main():
    """Main function"""
    # Check if IoTSphere server is running
    try:
        response = requests.get(BASE_URL)
        if response.status_code != 200:
            logger.error(
                f"{Fore.RED}IoTSphere server not responding at {BASE_URL}{Style.RESET_ALL}"
            )
            logger.error(
                f"{Fore.RED}Please start the server before running this test{Style.RESET_ALL}"
            )
            return 1
    except requests.ConnectionError:
        logger.error(
            f"{Fore.RED}IoTSphere server not running at {BASE_URL}{Style.RESET_ALL}"
        )
        logger.error(
            f"{Fore.RED}Please start the server before running this test{Style.RESET_ALL}"
        )
        return 1

    validator = DataValidator()
    success = await validator.run_validation()

    return 0 if success else 1


if __name__ == "__main__":
    # Handle requirements
    try:
        import bs4
        import colorama
        import tabulate
    except ImportError:
        print("Installing required packages...")
        os.system("pip install beautifulsoup4 colorama tabulate requests motor")
        print("Packages installed, restarting script...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    sys.exit(asyncio.run(main()))
