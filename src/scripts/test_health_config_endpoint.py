"""
Simple test script to verify the health configuration endpoint is working correctly.
This helps diagnose issues with the endpoint that our test suite is encountering.
"""
import os
import sys

import requests

# Add the parent directory to the path so we can import the main app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from fastapi.testclient import TestClient

# Import app to ensure it's started
from IoTSphere_Refactor.src.main import app

# Create test client
client = TestClient(app)


def test_health_config_endpoint():
    """Test the health configuration endpoint directly."""
    # Get current health configuration
    response = client.get("/api/water-heaters/health-configuration")
    print(f"Status code: {response.status_code}")
    print(f"Response headers: {response.headers}")
    print(f"Response body: {response.text}")

    # If we got a valid response, try setting a new configuration
    if response.status_code == 200:
        config = response.json()
        print(f"Current config: {config}")

        # Make a small change
        if isinstance(config, dict) and "temperature" in config:
            if "warning_high" in config["temperature"]:
                config["temperature"]["warning_high"] += 1

        # Post the updated config
        post_response = client.post(
            "/api/water-heaters/health-configuration", json=config
        )
        print(f"POST status code: {post_response.status_code}")
        print(f"POST response: {post_response.text}")


if __name__ == "__main__":
    test_health_config_endpoint()
