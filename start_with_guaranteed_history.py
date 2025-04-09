"""
Start IoTSphere with guaranteed temperature history

This script:
1. Forces MongoDB for shadow storage
2. Preserves existing data - never overwrites it if it exists
3. Verifies temperature history for each water heater
4. Starts the server after ensuring data is ready
"""
import asyncio
import importlib
import json
import logging
import os
import random
import sys
from datetime import datetime, timedelta

# Configure logging - use only file handler to reduce console spam
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("temperature_history.log")],
)
# Add console handler with higher level to reduce spam
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)  # Only ERROR and above go to console
logging.getLogger().addHandler(console_handler)

logger = logging.getLogger(__name__)

# Reduce log level for noisy modules - set most to ERROR to reduce terminal spam
logging.getLogger("src.services.device_shadow").setLevel(logging.ERROR)
logging.getLogger("src.infrastructure.device_shadow").setLevel(logging.ERROR)
logging.getLogger("motor.motor_asyncio").setLevel(logging.ERROR)
logging.getLogger("src.services.websocket_manager").setLevel(logging.ERROR)
logging.getLogger("src.api.routes.websocket").setLevel(logging.ERROR)
logging.getLogger("src.services.standalone_websocket_server").setLevel(logging.ERROR)
logging.getLogger("src.infrastructure.websocket").setLevel(logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("aiomongo").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("matplotlib").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)
# Disable logging for time series data processing
logging.getLogger("src.infrastructure.device_shadow.timeseries").setLevel(logging.ERROR)

# CRITICAL: Force MongoDB for shadow storage
os.environ["SHADOW_STORAGE_TYPE"] = "mongodb"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/"
os.environ["MONGODB_DB_NAME"] = "iotsphere"
os.environ["WEBSOCKET_PORT"] = "7777"  # Use a specific WebSocket port
os.environ[
    "DISABLE_INFRASTRUCTURE_WEBSOCKET"
] = "true"  # Disable the infrastructure WebSocket server to prevent port conflicts

# Check if optimized MongoDB is configured
USE_OPTIMIZED_MONGODB = os.environ.get("USE_OPTIMIZED_MONGODB", "").lower() == "true"

# Add the repo root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Flag to track if history generation was needed
HISTORY_GENERATED = False


async def ensure_shadow_documents_with_history():
    """
    Verify shadow documents exist with history data
    If they don't exist or don't have history, create them
    BUT NEVER OVERWRITE EXISTING DATA
    """
    global HISTORY_GENERATED

    try:
        # Import appropriate storage based on configuration
        if USE_OPTIMIZED_MONGODB:
            logger.info("Using optimized MongoDB storage with time series collections")
            from src.infrastructure.device_shadow.optimized_mongodb_storage import (
                OptimizedMongoDBShadowStorage as ShadowStorage,
            )

            # Create optimized MongoDB storage
            mongo_uri = os.environ["MONGODB_URI"]
            db_name = os.environ["MONGODB_DB_NAME"]
            pool_size = int(os.environ.get("MONGODB_POOL_SIZE", "10"))
            logger.info(
                f"🔌 Connecting to MongoDB at {mongo_uri}, DB: {db_name}, Pool Size: {pool_size}"
            )
        else:
            logger.info("Using standard MongoDB storage")
            from src.infrastructure.device_shadow.mongodb_shadow_storage import (
                MongoDBShadowStorage as ShadowStorage,
            )

            # Create standard MongoDB storage
            mongo_uri = os.environ["MONGODB_URI"]
            db_name = os.environ["MONGODB_DB_NAME"]
            logger.info(f"🔌 Connecting to MongoDB at {mongo_uri}, DB: {db_name}")

        # Initialize storage based on detected type
        if USE_OPTIMIZED_MONGODB:
            storage = ShadowStorage(
                mongo_uri=mongo_uri, db_name=db_name, pool_size=pool_size
            )
        else:
            storage = ShadowStorage(mongo_uri=mongo_uri, db_name=db_name)

        # Initialize it
        await storage.initialize()
        logger.info("✅ MongoDB connection successful!")

        # Import shadow service
        from src.services.device_shadow import DeviceShadowService

        shadow_service = DeviceShadowService(storage_provider=storage)

        # List of device IDs to check/create
        device_ids = ["wh-001", "wh-002", "wh-e0ae2f58", "wh-e1ae2f59"]

        for device_id in device_ids:
            # Check if shadow exists
            exists = await storage.shadow_exists(device_id)
            logger.info(f"Shadow exists for {device_id}: {exists}")

            if exists:
                # Get the existing shadow
                shadow = await storage.get_shadow(device_id)
                logger.info(
                    f"Retrieved shadow for {device_id}, version: {shadow.get('version', 'N/A')}"
                )

                # Check if it has history
                history = shadow.get("history", [])
                logger.info(f"Shadow has {len(history)} history entries")

                if not history or len(history) < 10:
                    logger.warning(
                        f"⚠️ Shadow document for {device_id} has insufficient history, generating data"
                    )
                    await generate_history_for_device(
                        storage, shadow_service, device_id
                    )
                    HISTORY_GENERATED = True
                else:
                    # Just log and skip - don't regenerate data when it already exists
                    logger.info(
                        f"✅ Shadow document for {device_id} has sufficient history ({len(history)} entries), preserving data"
                    )
            else:
                logger.warning(
                    f"⚠️ Shadow document does not exist for {device_id}, creating it"
                )
                await create_shadow_with_history(storage, shadow_service, device_id)
                HISTORY_GENERATED = True

        # Close the connection when done
        await storage.close()

        return True

    except Exception as e:
        logger.error(f"❌ Error ensuring shadow documents: {str(e)}")
        import traceback

        logger.error(f"❌ Stack trace: {traceback.format_exc()}")
        return False


async def create_shadow_with_history(storage, shadow_service, device_id):
    """Create a new shadow document with history for a device"""
    try:
        # Create basic shadow document
        logger.info(f"Creating new shadow document for {device_id}")

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
            "history": [],  # Initialize empty history array
        }

        # Save the shadow
        await storage.save_shadow(device_id, shadow)
        logger.info(f"Created new shadow document for {device_id}")

        # Generate history
        await generate_history_for_device(storage, shadow_service, device_id)

    except Exception as e:
        logger.error(f"❌ Error creating shadow for {device_id}: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())


async def generate_history_for_device(
    storage, shadow_service, device_id, log_progress=False
):
    """Generate and add history data for a device shadow"""
    try:
        # Get current shadow
        shadow = await storage.get_shadow(device_id)

        # Generate history entries (last 7 days, every 30 minutes)
        days = 7
        entries_per_day = 48  # 30 min intervals = 48 entries per day
        total_entries = days * entries_per_day

        # Set start time to days ago from now
        start_time = datetime.now() - timedelta(days=days)

        # Create history array if it doesn't exist
        if "history" not in shadow:
            shadow["history"] = []

        # Skip if we already have sufficient history (at least 10 entries)
        if len(shadow["history"]) >= 10:
            logger.info(
                f"Shadow for {device_id} already has {len(shadow['history'])} history entries, no generation needed"
            )
            return

        logger.info(f"Generating {total_entries} history entries for {device_id}")

        # Base temperature and variations
        base_temp = 120.0
        import math  # Import math for sin function

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

            # Add to shadow history without logging each entry to reduce spam
            shadow["history"].append(history_entry)

            # Only log occasionally to reduce terminal spam
            if i % 100 == 0 and i > 0:
                logger.info(
                    f"Generated {i}/{total_entries} history entries for {device_id}"
                )

        # Sort history by timestamp (oldest first)
        shadow["history"].sort(key=lambda entry: entry["timestamp"])

        # For optimized storage, we need to handle history separately
        if os.environ.get("USE_OPTIMIZED_MONGODB", "").lower() == "true":
            # Get history entries first
            history_entries = shadow.pop("history", [])

            # Save the shadow without history
            await storage.save_shadow(device_id, shadow)

            # Add each history entry individually using the optimized method
            added_count = 0
            for entry in history_entries:
                try:
                    # Extract timestamp and metrics
                    timestamp = entry.get("timestamp")
                    metrics = entry.get("metrics", {})

                    # Add to shadow history using optimized method
                    if hasattr(storage, "add_shadow_history"):
                        await storage.add_shadow_history(device_id, timestamp, metrics)
                    else:
                        # For backward compatibility - fall back to direct access
                        history_entry = {
                            "device_id": device_id,
                            "timestamp": timestamp,
                            "metrics": metrics,
                        }
                        await storage.history.insert_one(history_entry)
                    added_count += 1
                except Exception as e:
                    logger.warning(f"Error adding history entry: {e}")

            logger.info(
                f"✅ Updated shadow for {device_id} with {added_count} history entries using optimized storage"
            )
        else:
            # Update the shadow with embedded history for traditional storage
            await storage.save_shadow(device_id, shadow)
            logger.info(
                f"✅ Updated shadow for {device_id} with {len(shadow['history'])} history entries"
            )

    except Exception as e:
        logger.error(f"❌ Error generating history for {device_id}: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())


async def prepare_data():
    """Prepare shadow documents with history data"""
    try:
        logger.info("🚀 Preparing IoTSphere with guaranteed temperature history")

        # Ensure shadow documents with history
        logger.info("Ensuring shadow documents with history")
        success = await ensure_shadow_documents_with_history()

        if not success:
            logger.error("❌ Failed to ensure shadow documents with history")
            return False

        return True
    except Exception as e:
        logger.error(f"❌ Error preparing data: {str(e)}")
        return False


def main():
    """Main function to prepare and start the server"""
    try:
        # First prepare the data asynchronously
        success = asyncio.run(prepare_data())

        if not success:
            logger.error("❌ Failed to prepare data. Exiting.")
            return False

        # Start the server
        logger.info("Starting the server")

        port = 8000
        if len(sys.argv) > 1:
            port = int(sys.argv[1])

        logger.info(f"Starting server on port {port}")

        # Import uvicorn and app
        import uvicorn

        # Status report
        if HISTORY_GENERATED:
            logger.info("📊 History data was generated for some devices")
            logger.info("🔍 The temperature history charts should now work correctly")
        else:
            logger.info("📊 All shadow documents already had sufficient history data")
            logger.info("🔍 No data generation was needed")

        logger.info("")
        logger.info("🌐 Server details:")
        logger.info(f"   - Web interface: http://localhost:{port}")
        logger.info(
            f"   - WebSocket server: ws://localhost:{os.environ['WEBSOCKET_PORT']}"
        )
        logger.info(f"   - Shadow storage: MongoDB ({os.environ['MONGODB_URI']})")
        logger.info("")
        logger.info("🧪 To test temperature history:")
        logger.info(f"   - Open http://localhost:{port}/water-heaters/wh-001")
        logger.info("   - Check that the temperature history chart appears with data")
        logger.info("")

        # Run the server (non-async call)
        uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=False)

        return True

    except Exception as e:
        logger.error(f"❌ Error in main function: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    # Parse port from command line if provided
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid port number: {sys.argv[1]}, using default: {port}")

    logger.info(
        f"Starting IoTSphere with guaranteed temperature history on port {port}"
    )
    asyncio.run(main())
