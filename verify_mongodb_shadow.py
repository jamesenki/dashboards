#!/usr/bin/env python3
"""
Verify MongoDB Shadow Documents

This script checks if MongoDB is running and shadow documents exist.
If they don't exist, it creates sample documents with temperature history.
"""
import asyncio
import logging
import random
import sys
from datetime import datetime, timedelta

import motor.motor_asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# MongoDB configuration
MONGODB_URI = "mongodb://localhost:27017/"
MONGODB_DB_NAME = "iotsphere"
SHADOWS_COLLECTION = "device_shadows"

# Device IDs to verify
DEVICE_IDS = ["wh-001", "wh-002", "wh-e0ae2f58", "wh-e1ae2f59"]


async def verify_mongodb_shadows():
    """Verify MongoDB connection and shadow documents"""
    try:
        # Connect to MongoDB
        logger.info(f"Connecting to MongoDB at {MONGODB_URI}")
        client = motor.motor_asyncio.AsyncIOMotorClient(
            MONGODB_URI, serverSelectionTimeoutMS=5000
        )

        # Test connection
        await client.server_info()
        logger.info("✅ MongoDB connection successful")

        # Get database and collection
        db = client[MONGODB_DB_NAME]
        collection = db[SHADOWS_COLLECTION]

        # Check if collection exists
        collections = await db.list_collection_names()
        if SHADOWS_COLLECTION not in collections:
            logger.warning(
                f"⚠️ Collection '{SHADOWS_COLLECTION}' doesn't exist, creating it..."
            )
            await db.create_collection(SHADOWS_COLLECTION)

        # Verify shadow documents for each device
        for device_id in DEVICE_IDS:
            shadow = await collection.find_one({"device_id": device_id})

            if shadow:
                # Document exists, check for history
                history = shadow.get("history", [])
                if history and len(history) > 0:
                    logger.info(
                        f"✅ Shadow for {device_id} exists with {len(history)} history entries"
                    )
                else:
                    # Add history to existing document
                    logger.warning(
                        f"⚠️ Shadow for {device_id} has no history, adding sample data..."
                    )
                    history = generate_temperature_history()
                    await collection.update_one(
                        {"device_id": device_id}, {"$set": {"history": history}}
                    )
                    logger.info(
                        f"✅ Added {len(history)} history entries to {device_id}"
                    )
            else:
                # Create new shadow document
                logger.warning(f"⚠️ No shadow found for {device_id}, creating it...")
                new_shadow = create_shadow_document(device_id)
                await collection.insert_one(new_shadow)
                logger.info(
                    f"✅ Created shadow document for {device_id} with {len(new_shadow['history'])} history entries"
                )

        logger.info("🎉 All shadow documents verified and created if needed")

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return False
    finally:
        client.close()

    return True


def generate_temperature_history(days=3, interval_hours=1):
    """Generate sample temperature history data"""
    history = []
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    current_time = start_time

    while current_time <= end_time:
        # Generate a temperature between 120°F and 140°F with fluctuations
        base_temp = 130.0
        fluctuation = random.uniform(-10.0, 10.0)
        temperature = round(base_temp + fluctuation, 1)

        # Add entry to history
        history.append(
            {"timestamp": current_time.isoformat() + "Z", "temperature": temperature}
        )

        # Move to next interval
        current_time += timedelta(hours=interval_hours)

    return history


def create_shadow_document(device_id):
    """Create a new shadow document with history"""
    history = generate_temperature_history()

    # Use most recent temperature as current temperature
    current_temp = history[-1]["temperature"] if history else 130.0

    # Set heater status randomly
    heater_status = random.choice(["active", "idle"])

    return {
        "device_id": device_id,
        "reported": {
            "temperature": current_temp,
            "heater_status": heater_status,
            "water_level": random.randint(80, 100),
            "power": "on",
            "errors": None,
        },
        "desired": {"target_temperature": random.randint(125, 135)},
        "version": 1,
        "metadata": {
            "created_at": datetime.utcnow().isoformat() + "Z",
            "last_updated": datetime.utcnow().isoformat() + "Z",
        },
        "history": history,
    }


async def display_shadow_info():
    """Display shadow document information"""
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
        db = client[MONGODB_DB_NAME]
        collection = db[SHADOWS_COLLECTION]

        for device_id in DEVICE_IDS:
            shadow = await collection.find_one({"device_id": device_id})
            if shadow:
                logger.info(
                    f"\n===================== {device_id} ====================="
                )
                logger.info(
                    f"Current Temperature: {shadow['reported'].get('temperature')}°F"
                )
                logger.info(
                    f"Target Temperature: {shadow['desired'].get('target_temperature')}°F"
                )
                logger.info(f"Heater Status: {shadow['reported'].get('heater_status')}")
                logger.info(f"History Entries: {len(shadow.get('history', []))}")

                # Show first and last history entries
                history = shadow.get("history", [])
                if history:
                    logger.info("\nFirst history entry:")
                    logger.info(f"  Time: {history[0]['timestamp']}")
                    logger.info(f"  Temp: {history[0]['temperature']}°F")

                    logger.info("\nLast history entry:")
                    logger.info(f"  Time: {history[-1]['timestamp']}")
                    logger.info(f"  Temp: {history[-1]['temperature']}°F")
            else:
                logger.warning(f"No shadow document found for {device_id}")
    except Exception as e:
        logger.error(f"Error displaying shadow info: {str(e)}")
    finally:
        client.close()


async def main():
    """Main function"""
    logger.info("🔍 Verifying MongoDB shadow documents...")
    success = await verify_mongodb_shadows()

    if success:
        logger.info("\n🔎 Displaying shadow document information:")
        await display_shadow_info()

        logger.info("\n✅ VERIFICATION COMPLETE")
        logger.info("Temperature history should now be visible at:")
        logger.info("http://localhost:7080/water-heaters/wh-001")
        logger.info("\nIf the server is running, open this URL in your browser.")
        return 0
    else:
        logger.error("\n❌ VERIFICATION FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
