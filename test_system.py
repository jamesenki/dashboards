#!/usr/bin/env python3
"""
Test script to check all components of the IoTSphere system
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Expected water heater IDs
WATER_HEATER_IDS = [
    "wh-001",
    "wh-002",
    "wh-e0ae2f58",
    "wh-e1ae2f59",
    "wh-e2ae2f60",
    "wh-e3ae2f61",
    "wh-e4ae2f62",
    "wh-e5ae2f63",
]


async def test_asset_registry():
    """Test if all water heaters exist in the Asset Registry"""
    from src.services.asset_registry import AssetRegistryService

    logger.info("TESTING ASSET REGISTRY...")
    service = AssetRegistryService()

    # Get all devices
    try:
        devices = await service.get_devices()

        # Filter for water heaters
        water_heaters = [
            d
            for d in devices
            if d.get("type") == "water_heater"
            or (
                isinstance(d.get("device_id", ""), str)
                and d.get("device_id", "").startswith("wh-")
            )
        ]

        logger.info(f"Asset Registry contains {len(water_heaters)} water heaters:")
        for wh in water_heaters:
            logger.info(
                f"- {wh.get('device_id', 'Unknown ID')}: {wh.get('name', 'Unknown Name')}"
            )

        # Check if all expected IDs are present
        missing_ids = []
        for wh_id in WATER_HEATER_IDS:
            found = False
            for wh in water_heaters:
                if wh.get("device_id") == wh_id or wh.get("id") == wh_id:
                    found = True
                    break
            if not found:
                missing_ids.append(wh_id)

        if missing_ids:
            logger.warning(
                f"Missing {len(missing_ids)} water heaters in Asset Registry: {missing_ids}"
            )
        else:
            logger.info("All expected water heaters found in Asset Registry")

        return len(water_heaters), missing_ids
    except Exception as e:
        logger.error(f"Error testing Asset Registry: {e}")
        return 0, WATER_HEATER_IDS


async def test_shadow_documents():
    """Test if all water heaters have shadow documents with history"""
    from src.services.device_shadow import DeviceShadowService

    logger.info("\nTESTING SHADOW DOCUMENTS...")
    service = DeviceShadowService()

    # Check each water heater shadow
    shadows_found = 0
    shadows_with_history = 0
    missing_ids = []
    missing_history = []

    for wh_id in WATER_HEATER_IDS:
        try:
            shadow = await service.get_device_shadow(wh_id)
            shadows_found += 1
            logger.info(f"- Found shadow for {wh_id}")

            # Check for history data
            has_history = False

            # Check main readings array
            if (
                isinstance(shadow, dict)
                and "readings" in shadow
                and len(shadow["readings"]) > 0
            ):
                has_history = True
                logger.info(f"  - Has {len(shadow['readings'])} readings in main array")

            # Check reported.readings array
            elif (
                isinstance(shadow, dict)
                and "reported" in shadow
                and "readings" in shadow["reported"]
                and len(shadow["reported"]["readings"]) > 0
            ):
                has_history = True
                logger.info(
                    f"  - Has {len(shadow['reported']['readings'])} readings in reported.readings array"
                )

            # Check history field
            elif (
                isinstance(shadow, dict)
                and "history" in shadow
                and len(shadow["history"]) > 0
            ):
                has_history = True
                logger.info(
                    f"  - Has {len(shadow['history'])} entries in history array"
                )

            if not has_history:
                logger.warning(f"  - No history data found for {wh_id}")
                missing_history.append(wh_id)
            else:
                shadows_with_history += 1

        except Exception as e:
            logger.error(f"Error getting shadow for {wh_id}: {e}")
            missing_ids.append(wh_id)

    logger.info(
        f"Found {shadows_found}/{len(WATER_HEATER_IDS)} shadows, {shadows_with_history} with history data"
    )
    if missing_ids:
        logger.warning(f"Missing shadows for: {missing_ids}")
    if missing_history:
        logger.warning(f"Missing history data for: {missing_history}")

    return shadows_found, shadows_with_history, missing_ids, missing_history


async def test_api_endpoints():
    """Test if the API endpoints are returning the water heaters"""
    import aiohttp

    logger.info("\nTESTING API ENDPOINTS...")

    async with aiohttp.ClientSession() as session:
        # Test endpoints that might return water heaters
        endpoints = [
            "http://localhost:8006/api/manufacturer/water-heaters",
            "http://localhost:8006/api/devices",
            "http://localhost:8006/api/device-shadow",
        ]

        for endpoint in endpoints:
            try:
                async with session.get(endpoint) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(
                            f"Endpoint {endpoint}: Got {len(data) if isinstance(data, list) else 1} items"
                        )

                        # Look for water heaters in the response
                        if isinstance(data, list):
                            water_heaters = []
                            for item in data:
                                if isinstance(item, dict) and (
                                    (item.get("type") == "water_heater")
                                    or (
                                        isinstance(item.get("device_id", ""), str)
                                        and item.get("device_id", "").startswith("wh-")
                                    )
                                    or (
                                        isinstance(item.get("id", ""), str)
                                        and item.get("id", "").startswith("wh-")
                                    )
                                ):
                                    water_heaters.append(item)

                            if water_heaters:
                                logger.info(
                                    f"  - Found {len(water_heaters)} water heaters in response:"
                                )
                                for wh in water_heaters[:3]:  # Show first 3 as examples
                                    wh_id = wh.get("device_id") or wh.get("id")
                                    logger.info(
                                        f"    - {wh_id}: {wh.get('name', 'Unknown')}"
                                    )
                                if len(water_heaters) > 3:
                                    logger.info(
                                        f"    - ... and {len(water_heaters) - 3} more"
                                    )
                    else:
                        logger.warning(f"Endpoint {endpoint}: Status {response.status}")
            except Exception as e:
                logger.error(f"Error testing endpoint {endpoint}: {e}")

        # Test individual shadow documents
        for wh_id in WATER_HEATER_IDS[:2]:  # Test first 2 water heaters
            shadow_endpoint = f"http://localhost:8006/api/device-shadow/{wh_id}"
            try:
                async with session.get(shadow_endpoint) as response:
                    if response.status == 200:
                        shadow = await response.json()
                        logger.info(f"Shadow endpoint for {wh_id}: Success")

                        # Check for history data
                        if isinstance(shadow, dict):
                            if "readings" in shadow and len(shadow["readings"]) > 0:
                                logger.info(
                                    f"  - Has {len(shadow['readings'])} readings"
                                )
                            elif (
                                "reported" in shadow
                                and "readings" in shadow["reported"]
                                and len(shadow["reported"]["readings"]) > 0
                            ):
                                logger.info(
                                    f"  - Has {len(shadow['reported']['readings'])} readings in reported.readings"
                                )
                            else:
                                logger.warning(f"  - No history data found")
                    else:
                        logger.warning(
                            f"Shadow endpoint for {wh_id}: Status {response.status}"
                        )
            except Exception as e:
                logger.error(f"Error testing shadow endpoint for {wh_id}: {e}")


async def main():
    """Run all tests"""
    logger.info("Starting system tests...")

    # Test Asset Registry
    asset_count, missing_assets = await test_asset_registry()

    # Test Shadow Documents
    (
        shadow_count,
        history_count,
        missing_shadows,
        missing_history,
    ) = await test_shadow_documents()

    # Test API Endpoints
    await test_api_endpoints()

    # Summary
    logger.info("\nTEST SUMMARY:")
    logger.info(f"Asset Registry: {asset_count}/8 water heaters found")
    if missing_assets:
        logger.warning(f"  Missing from Asset Registry: {missing_assets}")

    logger.info(
        f"Shadow Documents: {shadow_count}/8 shadows found, {history_count}/8 with history"
    )
    if missing_shadows:
        logger.warning(f"  Missing Shadows: {missing_shadows}")
    if missing_history:
        logger.warning(f"  Missing History: {missing_history}")


if __name__ == "__main__":
    asyncio.run(main())
