"""
MongoDB diagnostic tool for IoTSphere

This tool:
1. Checks MongoDB connection and shadow documents
2. Verifies the data needed for temperature history
3. Provides detailed diagnostics

Use this before starting the application to ensure MongoDB is ready.
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("mongodb_diagnostic.log")],
)
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuration - can be overridden with command line args
CONFIG = {
    "mongo_uri": "mongodb://localhost:27017/",
    "db_name": "iotsphere",
    "collection": "device_shadows",
    "device_ids": ["wh-001", "wh-002", "wh-e0ae2f58", "wh-e1ae2f59"],
    "check_history": True,
    "min_history_entries": 10,
    "verbosity": "info",
}


async def check_mongodb_connection():
    """Check basic MongoDB connection"""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient

        logger.info(f"Testing MongoDB connection to {CONFIG['mongo_uri']}")
        client = AsyncIOMotorClient(
            CONFIG["mongo_uri"], serverSelectionTimeoutMS=5000  # 5 second timeout
        )

        # Force a connection check
        await client.server_info()
        logger.info("✅ MongoDB connection successful")

        # Check if database exists
        db_list = await client.list_database_names()
        if CONFIG["db_name"] in db_list:
            logger.info(f"✅ Database '{CONFIG['db_name']}' exists")
        else:
            logger.error(f"❌ Database '{CONFIG['db_name']}' does not exist")
            return False, client

        # Check collection
        db = client[CONFIG["db_name"]]
        collections = await db.list_collection_names()

        if CONFIG["collection"] in collections:
            logger.info(f"✅ Collection '{CONFIG['collection']}' exists")
        else:
            logger.error(f"❌ Collection '{CONFIG['collection']}' does not exist")
            return False, client

        return True, client

    except Exception as e:
        logger.error(f"❌ MongoDB connection error: {str(e)}")
        import traceback

        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False, None


async def check_shadow_documents(client):
    """Check if shadow documents exist with required data"""
    if not client:
        return False

    try:
        # Access the database and collection
        db = client[CONFIG["db_name"]]
        collection = db[CONFIG["collection"]]

        # Count total documents
        count = await collection.count_documents({})
        logger.info(f"📊 Found {count} shadow documents in total")

        if count == 0:
            logger.error("❌ No shadow documents found")
            return False

        # Check each specified device ID
        success = True
        for device_id in CONFIG["device_ids"]:
            shadow = await collection.find_one({"device_id": device_id})

            if shadow:
                logger.info(f"✅ Shadow document for {device_id} exists")

                # Check for history if required
                if CONFIG["check_history"]:
                    history = shadow.get("history", [])
                    history_count = len(history)

                    if history_count >= CONFIG["min_history_entries"]:
                        logger.info(
                            f"✅ Shadow for {device_id} has {history_count} history entries"
                        )

                        # Show a sample history entry if verbose
                        if CONFIG["verbosity"] == "debug" and history:
                            logger.info(
                                f"📊 Sample history entry: {json.dumps(history[0], indent=2)}"
                            )
                    else:
                        logger.warning(
                            f"⚠️ Shadow for {device_id} has only {history_count} history entries (min: {CONFIG['min_history_entries']})"
                        )
                        success = False
            else:
                logger.error(f"❌ No shadow document found for {device_id}")
                success = False

        return success

    except Exception as e:
        logger.error(f"❌ Error checking shadow documents: {str(e)}")
        import traceback

        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False


async def generate_history_data(client):
    """Generate sample history data for shadow documents"""
    if not client:
        return False

    try:
        logger.info("Generating sample history data for shadow documents...")

        # Access the database and collection
        db = client[CONFIG["db_name"]]
        collection = db[CONFIG["collection"]]

        import math
        import random

        # For each device ID
        for device_id in CONFIG["device_ids"]:
            # Check if shadow exists
            shadow = await collection.find_one({"device_id": device_id})

            if not shadow:
                logger.info(f"Creating new shadow document for {device_id}")

                # Create basic shadow document
                shadow = {
                    "device_id": device_id,
                    "reported": {
                        "temperature": 120.5,
                        "pressure": 60,
                        "flow_rate": 3.2,
                        "energy_usage": 450,
                        "mode": "ECO",
                        "connection_status": "ONLINE",
                        "status": "ONLINE",
                        "heater_status": "STANDBY",
                        "name": f"Water Heater {device_id}",
                        "model": "SmartTank Pro",
                        "manufacturer": "AquaSmart",
                        "target_temperature": 125,
                        "min_temperature": 40,
                        "max_temperature": 140,
                        "timestamp": datetime.now().isoformat() + "Z",
                    },
                    "desired": {"temperature": 125, "mode": "ECO"},
                    "metadata": {
                        "created_at": datetime.now().isoformat() + "Z",
                        "last_updated": datetime.now().isoformat() + "Z",
                    },
                    "timestamp": datetime.now().isoformat() + "Z",
                    "version": 1,
                    "history": [],
                }

            # Check if history needs to be generated
            history = shadow.get("history", [])
            if len(history) < CONFIG["min_history_entries"]:
                logger.info(f"Generating history data for {device_id}")

                # Generate history entries (last 7 days, every 30 minutes)
                days = 7
                entries_per_day = 48  # 30 min intervals = 48 entries per day
                total_entries = days * entries_per_day

                # Start time (7 days ago)
                start_time = datetime.now() - timedelta(days=days)

                # Create history array if it doesn't exist
                if "history" not in shadow:
                    shadow["history"] = []

                # Base temperature and variations
                base_temp = 120.0

                new_entries = []
                for i in range(total_entries):
                    # Calculate timestamp for this entry (every 30 minutes from start_time)
                    timestamp = start_time + timedelta(minutes=30 * i)
                    timestamp_str = timestamp.isoformat() + "Z"

                    # Simulate realistic temperature variations over time
                    hour_of_day = timestamp.hour
                    day_factor = 1.0 + 0.1 * math.sin(
                        hour_of_day * math.pi / 12
                    )  # Slight daily cycle

                    # Random variations +/- 2 degrees
                    random_factor = random.uniform(-2.0, 2.0)

                    temperature = base_temp * day_factor + random_factor
                    temperature = round(temperature, 1)  # Round to 1 decimal place

                    # Also generate other metrics
                    pressure = round(random.uniform(58.0, 62.0), 1)
                    flow_rate = round(random.uniform(3.0, 3.4), 2)
                    energy_usage = round(random.uniform(465.0, 492.0), 2)

                    # Most of the time the heater is standby, occasionally heating
                    heater_status = "HEATING" if random.random() < 0.3 else "STANDBY"

                    # Create history entry
                    history_entry = {
                        "timestamp": timestamp_str,
                        "metrics": {
                            "temperature": temperature,
                            "pressure": pressure,
                            "flow_rate": flow_rate,
                            "energy_usage": energy_usage,
                            "heater_status": heater_status,
                        },
                    }

                    # Add to new entries
                    new_entries.append(history_entry)

                # Add new entries to shadow history
                shadow["history"] = new_entries + shadow["history"]

                # Sort history by timestamp (oldest first)
                shadow["history"].sort(key=lambda entry: entry["timestamp"])

                # Update the shadow in the database
                result = await collection.replace_one(
                    {"device_id": device_id}, shadow, upsert=True
                )

                if result.acknowledged:
                    logger.info(
                        f"✅ Updated shadow for {device_id} with {len(shadow['history'])} history entries"
                    )
                else:
                    logger.error(f"❌ Failed to update shadow for {device_id}")
            else:
                logger.info(
                    f"✅ Shadow for {device_id} already has {len(history)} history entries"
                )

        return True

    except Exception as e:
        logger.error(f"❌ Error generating history data: {str(e)}")
        import traceback

        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False


async def run_diagnostics():
    """Run full MongoDB diagnostics"""
    logger.info("=== MongoDB Diagnostic Tool ===")

    # Check MongoDB connection
    logger.info("Step 1: Testing MongoDB connection")
    connection_success, client = await check_mongodb_connection()

    if not connection_success:
        logger.error("❌ MongoDB connection failed. Please check your MongoDB server.")
        if client:
            client.close()
        return False

    # Check shadow documents
    logger.info("Step 2: Checking shadow documents")
    documents_success = await check_shadow_documents(client)

    # Generate history data if needed
    if not documents_success and CONFIG["check_history"]:
        logger.info("Step 3: Generating sample history data")
        generate_success = await generate_history_data(client)

        if generate_success:
            logger.info("✅ Successfully generated history data")
            # Re-check documents
            documents_success = await check_shadow_documents(client)
        else:
            logger.error("❌ Failed to generate history data")

    # Close MongoDB connection
    if client:
        client.close()

    # Final verdict
    if connection_success and documents_success:
        logger.info("✅ MongoDB diagnostic checks PASSED")
        logger.info(
            "MongoDB is properly configured with shadow documents and history data"
        )

        # Output environment variables to use
        logger.info("")
        logger.info("=== Environment Variable Configuration ===")
        logger.info("Use these environment variables to ensure MongoDB shadow storage:")
        logger.info(f"SHADOW_STORAGE_TYPE=mongodb")
        logger.info(f"MONGODB_URI={CONFIG['mongo_uri']}")
        logger.info(f"MONGODB_DB_NAME={CONFIG['db_name']}")
        logger.info("")
        logger.info("You can start the application with:")
        logger.info(
            f"SHADOW_STORAGE_TYPE=mongodb MONGODB_URI={CONFIG['mongo_uri']} MONGODB_DB_NAME={CONFIG['db_name']} python -m src.main"
        )

        return True
    else:
        logger.error("❌ MongoDB diagnostic checks FAILED")
        logger.error("Please fix the issues before starting the application")
        return False


def parse_args():
    """Parse command line arguments"""
    import argparse

    parser = argparse.ArgumentParser(
        description="MongoDB diagnostic tool for IoTSphere"
    )

    parser.add_argument(
        "--mongo-uri", help="MongoDB URI (default: mongodb://localhost:27017/)"
    )
    parser.add_argument("--db-name", help="Database name (default: iotsphere)")
    parser.add_argument(
        "--collection", help="Collection name (default: device_shadows)"
    )
    parser.add_argument(
        "--device-ids", help="Comma-separated list of device IDs to check"
    )
    parser.add_argument("--no-history", action="store_true", help="Skip history check")
    parser.add_argument(
        "--min-history", type=int, help="Minimum number of history entries required"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Update configuration from arguments
    if args.mongo_uri:
        CONFIG["mongo_uri"] = args.mongo_uri
    if args.db_name:
        CONFIG["db_name"] = args.db_name
    if args.collection:
        CONFIG["collection"] = args.collection
    if args.device_ids:
        CONFIG["device_ids"] = args.device_ids.split(",")
    if args.no_history:
        CONFIG["check_history"] = False
    if args.min_history:
        CONFIG["min_history_entries"] = args.min_history
    if args.verbose:
        CONFIG["verbosity"] = "debug"
        logging.getLogger().setLevel(logging.DEBUG)


if __name__ == "__main__":
    # Parse command line arguments
    parse_args()

    # Run diagnostics
    success = asyncio.run(run_diagnostics())

    # Exit with appropriate code
    sys.exit(0 if success else 1)
