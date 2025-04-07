#!/usr/bin/env python
"""
Script to test AquaTherm water heater API endpoints
"""
import json
import sys
from pprint import pprint

import requests

# Base URL for the API
API_BASE_URL = "http://localhost:8006"


def test_all_water_heaters():
    """Test the all water heaters endpoint"""
    print("Testing all AquaTherm water heaters endpoint...")

    url = f"{API_BASE_URL}/api/aquatherm-water-heaters"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            heaters = response.json()
            print(f"✅ Found {len(heaters)} AquaTherm water heaters")

            # Count types
            tank_count = 0
            hybrid_count = 0
            tankless_count = 0

            for heater in heaters:
                heater_id = heater.get("id", "Unknown")
                heater_type = heater.get("properties", {}).get("heater_type", "Unknown")
                print(f"  - ID: {heater_id}, Type: {heater_type}")

                if heater_type == "TANK":
                    tank_count += 1
                elif heater_type == "HYBRID":
                    hybrid_count += 1
                elif heater_type == "TANKLESS":
                    tankless_count += 1

            print(f"\nSummary:")
            print(f"  TANK water heaters: {tank_count}")
            print(f"  HYBRID water heaters: {hybrid_count}")
            print(f"  TANKLESS water heaters: {tankless_count}")

            if tank_count < 2 or hybrid_count < 2 or tankless_count < 2:
                print(
                    "❌ Validation would fail: Need at least 2 of each water heater type"
                )
            else:
                print("✅ Water heater count requirements met")
        else:
            print(f"❌ Error: Status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def test_individual_endpoints():
    """Test individual water heater endpoints for different types"""
    print("\nTesting individual water heater endpoints...")

    test_ids = ["aqua-wh-tank-001", "aqua-wh-hybrid-001", "aqua-wh-tankless-001"]

    for device_id in test_ids:
        print(f"\nTesting device ID: {device_id}")
        url = f"{API_BASE_URL}/api/aquatherm-water-heaters/{device_id}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Individual endpoint successful")
                print(f"  - Name: {data.get('name')}")
                print(f"  - Type: {data.get('properties', {}).get('heater_type')}")
            else:
                print(f"❌ Error: Status code {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ Error: {str(e)}")


def test_detailed_endpoints():
    """Test detailed endpoints for a water heater"""
    print("\nTesting detailed water heater endpoints...")

    # Use one of our test IDs
    device_id = "aqua-wh-tank-001"

    # Endpoints to test
    endpoints = [
        "",  # Base device endpoint
        "/eco-net-status",
        "/maintenance-prediction",
        "/efficiency-analysis",
        "/telemetry-analysis",
        "/health-status",
        "/operational-summary",
    ]

    for endpoint in endpoints:
        url = f"{API_BASE_URL}/api/aquatherm-water-heaters/{device_id}{endpoint}"
        print(f"\nTesting endpoint: {url}")
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"✅ Status code: {response.status_code}")
                data = response.json()
                if endpoint == "":
                    print(f"  - Device name: {data.get('name')}")
                else:
                    # Just show that we got data
                    print(f"  - Got valid response data")
            else:
                print(f"❌ Error: Status code {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    print("Testing AquaTherm water heater API...")
    test_all_water_heaters()
    test_individual_endpoints()
    test_detailed_endpoints()
    print("\nTest complete!")
