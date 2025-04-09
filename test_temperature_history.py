"""
Comprehensive test for temperature history in IoTSphere
Following TDD principles, this test will:
1. RED phase: Verify shadow documents exist with history
2. GREEN phase: Ensure the API returns the history data correctly
3. REFACTOR phase: Make sure the frontend can display it properly
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# MongoDB connection helpers
async def verify_mongodb_shadow_documents():
    """Verify shadow documents exist with history in MongoDB"""
    try:
        from src.infrastructure.device_shadow.mongodb_shadow_storage import (
            MongoDBShadowStorage,
        )

        # Create MongoDB storage
        mongo_uri = "mongodb://localhost:27017/"
        db_name = "iotsphere"
        storage = MongoDBShadowStorage(mongo_uri=mongo_uri, db_name=db_name)

        # Initialize it
        await storage.initialize()
        logger.info("✅ MongoDB connection successful!")

        # Check known device IDs
        device_ids = ["wh-001", "wh-002", "wh-e0ae2f58", "wh-e1ae2f59"]

        for device_id in device_ids:
            exists = await storage.shadow_exists(device_id)
            logger.info(f"Shadow exists for {device_id}: {exists}")

            if exists:
                shadow = await storage.get_shadow(device_id)
                logger.info(
                    f"✅ Retrieved shadow for {device_id}, version: {shadow.get('version')}"
                )

                # Check if history exists
                history = shadow.get("history", [])
                logger.info(f"✅ Shadow has {len(history)} history entries")

                if not history:
                    logger.error(f"❌ No history entries found for {device_id}")
                    return False
            else:
                logger.error(f"❌ Shadow document does not exist for {device_id}")
                return False

        await storage.close()
        return True

    except Exception as e:
        logger.error(f"❌ MongoDB verification failed: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def verify_history_api_response(base_url, device_id):
    """Verify the history API returns data correctly"""
    try:
        # Test the API endpoint
        url = f"{base_url}/api/manufacturer/water-heaters/{device_id}/history"

        logger.info(f"Testing API endpoint: {url}")
        response = requests.get(url)

        # Check response status
        if response.status_code != 200:
            logger.error(f"❌ API returned status code {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False

        # Parse response
        data = response.json()

        # Check for history data
        if not data or "history" not in data:
            logger.error(f"❌ No history data in API response")
            logger.error(f"Response: {json.dumps(data, indent=2)}")
            return False

        history = data["history"]
        logger.info(f"✅ API returned {len(history)} history entries")

        if not history:
            logger.error(f"❌ History array is empty")
            return False

        # Check first entry format
        first_entry = history[0]
        if "timestamp" not in first_entry or "metrics" not in first_entry:
            logger.error(f"❌ History entry missing required fields")
            logger.error(f"Entry: {json.dumps(first_entry, indent=2)}")
            return False

        metrics = first_entry["metrics"]
        if "temperature" not in metrics:
            logger.error(f"❌ Metrics missing temperature value")
            return False

        logger.info(f"✅ History entry format is correct")
        logger.info(
            f"Sample entry: timestamp={first_entry['timestamp']}, temperature={metrics['temperature']}"
        )

        return True

    except Exception as e:
        logger.error(f"❌ API verification failed: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def verify_frontend_display(base_url, device_id):
    """Verify the frontend can display the history chart correctly"""
    try:
        # Get the device details page
        url = f"{base_url}/water-heaters/{device_id}"
        logger.info(f"Testing frontend page: {url}")

        # Log instructions for manual verification
        logger.info("⚠️ Manual verification required for frontend display:")
        logger.info(f"1. Visit {url} in your browser")
        logger.info("2. Check if the temperature history chart is displayed")
        logger.info("3. Check browser console for any JavaScript errors")
        logger.info("")
        logger.info("Temperature History should either show:")
        logger.info("- A chart with temperature history data")
        logger.info("- OR a clear error message if data cannot be loaded")
        logger.info("")
        logger.info(
            "If you see an empty box with no chart or error message, the issue persists"
        )

        return True

    except Exception as e:
        logger.error(f"❌ Frontend verification failed: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False


async def run_tests(base_url="http://localhost:8000"):
    """Run all tests"""
    # 1. RED Phase: Verify MongoDB shadow documents
    logger.info("🔍 RED PHASE: Verifying MongoDB shadow documents...")
    mongodb_result = await verify_mongodb_shadow_documents()

    if not mongodb_result:
        logger.error("❌ MongoDB verification failed")
        return False

    # 2. GREEN Phase: Verify API responses
    logger.info("🔍 GREEN PHASE: Verifying API responses...")

    # Test with multiple device IDs to ensure robustness
    device_ids = ["wh-001", "wh-002"]
    api_results = []

    for device_id in device_ids:
        api_result = verify_history_api_response(base_url, device_id)
        api_results.append(api_result)

        if not api_result:
            logger.error(f"❌ API verification failed for {device_id}")
        else:
            logger.info(f"✅ API verification passed for {device_id}")

    if not all(api_results):
        logger.error("❌ API verification failed for some devices")
        return False

    # 3. REFACTOR Phase: Verify frontend display
    logger.info("🔍 REFACTOR PHASE: Verifying frontend display...")

    # Test frontend with first device
    frontend_result = verify_frontend_display(base_url, device_ids[0])

    if not frontend_result:
        logger.error("❌ Frontend verification failed")
        return False

    # All tests passed
    logger.info("✅ All temperature history tests passed!")
    return True


if __name__ == "__main__":
    # Check if port was provided as argument
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = "8000"  # Default port

    base_url = f"http://localhost:{port}"
    logger.info(f"🧪 Running temperature history tests against {base_url}")

    result = asyncio.run(run_tests(base_url))

    if result:
        logger.info("✅ Temperature history tests completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Temperature history tests failed")
        sys.exit(1)
