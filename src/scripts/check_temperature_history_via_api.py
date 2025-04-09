"""
Test script to check temperature history via the API endpoint.

This script sends a request to the API endpoint to retrieve temperature history
for a specific water heater, verifying that the shadow document functionality is working.
"""
import asyncio
import json
import logging
import os
import sys
from urllib.parse import urljoin

import aiohttp

# Add parent directory to path to allow imports to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def check_temperature_history(heater_id, days=7):
    """
    Check if temperature history can be retrieved via the API.

    Args:
        heater_id: ID of the water heater to check
        days: Number of days of history to request
    """
    logger.info(f"Checking temperature history for water heater {heater_id}")

    # API endpoint
    base_url = "http://localhost:8006"
    endpoint = f"/api/water-heaters/{heater_id}/history/temperature?days={days}"
    url = urljoin(base_url, endpoint)

    logger.info(f"Making request to: {url}")

    # Send request to API
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Successfully retrieved temperature history!")
                    logger.info(f"Data points count: {len(data.get('labels', []))}")
                    logger.info(f"Data source: {data.get('source', 'unknown')}")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Failed to retrieve temperature history. Status: {response.status}"
                    )
                    logger.error(f"Error: {error_text}")
                    return None
    except Exception as e:
        logger.error(f"Error connecting to API: {e}")
        return None


if __name__ == "__main__":
    # Get heater ID from command line or use default
    heater_id = sys.argv[1] if len(sys.argv) > 1 else "wh-e0ae2f58"

    # Run the async function
    result = asyncio.run(check_temperature_history(heater_id))

    if result:
        # Print summary of results
        print("\nTemperature History Summary:")
        print(f"Number of data points: {len(result.get('labels', []))}")
        print(f"Data source: {result.get('source', 'unknown')}")
        print(
            f"First timestamp: {result.get('labels', [])[0] if result.get('labels', []) else 'N/A'}"
        )
        print(
            f"Last timestamp: {result.get('labels', [])[-1] if result.get('labels', []) else 'N/A'}"
        )

        # Print the first few data points
        if result.get("datasets", []):
            temps = result["datasets"][0]["data"]
            print("\nFirst 5 temperature readings:")
            for i in range(min(5, len(temps))):
                print(f"{result['labels'][i]}: {temps[i]}°C")
    else:
        print("Failed to retrieve temperature history data.")
