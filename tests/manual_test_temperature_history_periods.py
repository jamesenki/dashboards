#!/usr/bin/env python3
"""
Manual test script to verify temperature history data is available for 7, 14, and 30-day periods.
This helps ensure the History tab functions correctly with all period selectors.
"""
import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import testing client
from fastapi.testclient import TestClient

from src.main import app

# Test device ID - use a known device ID from your environment
TEST_DEVICE_ID = "wh-001"  # Change this if needed


def test_temperature_history_periods():
    """Test temperature history endpoints for 7, 14, and 30-day periods."""
    client = TestClient(app)

    # Create a mock device if needed
    if os.getenv("CREATE_TEST_DEVICE", "false").lower() == "true":
        create_response = client.post(
            "/api/water-heaters",
            json={"id": TEST_DEVICE_ID, "type": "water_heater", "manufacturer": "test"},
        )
        print(f"Create device response: {create_response.status_code}")

    print(f"\n{'=' * 50}")
    print(f"Testing temperature history for device: {TEST_DEVICE_ID}")
    print(f"{'=' * 50}")

    # Test each time period
    for days in [7, 14, 30]:
        base_url = (
            f"/api/manufacturer/water-heaters/{TEST_DEVICE_ID}/history/temperature"
        )
        print(f"\nTesting {days}-day period:")

        # Primary endpoint
        print(f"  Endpoint: {base_url}?days={days}")
        response = client.get(f"{base_url}?days={days}")
        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"  Data points: {len(data)}")
                if data:
                    print(f"  First data point: {data[0]}")
                    print(f"  Last data point: {data[-1]}")
            else:
                print(f"  Data: {data}")
        else:
            print(f"  Error: {response.text}")

            # Try alternate endpoints
            alt_endpoints = [
                f"/api/water-heaters/{TEST_DEVICE_ID}/temperature-history?period={days}d",
                f"/api/devices/{TEST_DEVICE_ID}/readings/temperature?days={days}",
                f"/api/{TEST_DEVICE_ID}/temperature/history?period={days}d",
            ]

            for alt_endpoint in alt_endpoints:
                print(f"\n  Trying alternate endpoint: {alt_endpoint}")
                alt_response = client.get(alt_endpoint)
                print(f"  Status: {alt_response.status_code}")

                if alt_response.status_code == 200:
                    data = alt_response.json()
                    if isinstance(data, list):
                        print(f"  Data points: {len(data)}")
                        if data:
                            print(f"  First data point: {data[0]}")
                            print(f"  Last data point: {data[-1]}")
                    else:
                        print(f"  Data: {data}")
                    break

    print(f"\n{'=' * 50}")
    print("Test complete")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    # Force MongoDB storage type for shadow documents
    os.environ["SHADOW_STORAGE_TYPE"] = "mongodb"

    # Run tests
    test_temperature_history_periods()
