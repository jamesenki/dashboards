"""
Test script to verify that the manufacturer-agnostic API endpoints are working correctly.
This script makes requests to the API endpoints and verifies that they return valid data.
"""
import asyncio
import json
import os
import sys
from pprint import pprint

import aiohttp

# Set environment variables for testing
os.environ["IOTSPHERE_ENV"] = "development"

# API base URL
BASE_URL = "http://localhost:8007/api"

# Test device ID
TEST_DEVICE_ID = "wh-001"  # Example water heater ID


async def test_prediction_endpoints():
    """Test the prediction endpoints."""
    print("\n=== Testing Prediction Endpoints ===")

    prediction_endpoints = [
        f"/manufacturer/water-heaters/{TEST_DEVICE_ID}/predictions/lifespan",
        f"/manufacturer/water-heaters/{TEST_DEVICE_ID}/predictions/anomalies",
        f"/manufacturer/water-heaters/{TEST_DEVICE_ID}/predictions/usage",
        f"/manufacturer/water-heaters/{TEST_DEVICE_ID}/predictions/factors",
    ]

    async with aiohttp.ClientSession() as session:
        for endpoint in prediction_endpoints:
            full_url = f"{BASE_URL}{endpoint}"
            print(f"\nTesting endpoint: {full_url}")

            try:
                async with session.get(full_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"SUCCESS: Status {response.status}")
                        # Print summary of the response
                        print(f"Prediction type: {data.get('prediction_type')}")
                        print(f"Device ID: {data.get('device_id')}")
                        print(f"Confidence: {data.get('confidence')}")
                        print(f"Features used: {data.get('features_used')}")
                        if (
                            "recommended_actions" in data
                            and data["recommended_actions"]
                        ):
                            print(
                                f"Recommended actions: {len(data['recommended_actions'])}"
                            )
                    else:
                        error = await response.text()
                        print(f"ERROR: Status {response.status}")
                        print(f"Response: {error}")
            except Exception as e:
                print(f"ERROR: {str(e)}")


async def test_history_endpoints():
    """Test the history endpoints."""
    print("\n=== Testing History Endpoints ===")

    history_endpoints = [
        f"/manufacturer/water-heaters/{TEST_DEVICE_ID}/history/dashboard",
        f"/manufacturer/water-heaters/{TEST_DEVICE_ID}/history/temperature",
        f"/manufacturer/water-heaters/{TEST_DEVICE_ID}/history/energy-usage",
        f"/manufacturer/water-heaters/{TEST_DEVICE_ID}/history/pressure-flow",
    ]

    async with aiohttp.ClientSession() as session:
        for endpoint in history_endpoints:
            full_url = f"{BASE_URL}{endpoint}"
            print(f"\nTesting endpoint: {full_url}")

            try:
                async with session.get(full_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"SUCCESS: Status {response.status}")
                        # Print summary of the response based on endpoint
                        if endpoint.endswith("/dashboard"):
                            print(f"Device ID: {data.get('device_id')}")
                            print(f"Timestamp: {data.get('timestamp')}")
                            if "summary" in data:
                                print(f"Summary: {list(data['summary'].keys())}")
                            if "recent_trends" in data:
                                print(
                                    f"Recent trends: {list(data['recent_trends'].keys())}"
                                )
                        elif endpoint.endswith("/temperature"):
                            print(f"Device ID: {data.get('device_id')}")
                            print(f"Days: {data.get('days')}")
                            print(f"Data points: {len(data.get('timestamps', []))}")
                            if "statistics" in data:
                                print(f"Statistics: {list(data['statistics'].keys())}")
                        elif endpoint.endswith("/energy-usage"):
                            print(f"Device ID: {data.get('device_id')}")
                            print(f"Days: {data.get('days')}")
                            print(f"Data points: {len(data.get('timestamps', []))}")
                            if "statistics" in data:
                                print(f"Statistics: {list(data['statistics'].keys())}")
                        elif endpoint.endswith("/pressure-flow"):
                            print(f"Device ID: {data.get('device_id')}")
                            print(f"Days: {data.get('days')}")
                            print(f"Data points: {len(data.get('timestamps', []))}")
                            if "statistics" in data:
                                print(f"Statistics: {list(data['statistics'].keys())}")
                    else:
                        error = await response.text()
                        print(f"ERROR: Status {response.status}")
                        print(f"Response: {error}")
            except Exception as e:
                print(f"ERROR: {str(e)}")


async def main():
    """Main test function."""
    print("Starting API endpoint tests...")
    print("Make sure the IoTSphere server is running on http://localhost:8007")

    # Test prediction endpoints
    await test_prediction_endpoints()

    # Test history endpoints
    await test_history_endpoints()

    print("\n=== All tests completed ===")


if __name__ == "__main__":
    asyncio.run(main())
