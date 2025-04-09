"""
Fix for IoTSphere temperature history by ensuring MongoDB shadow storage

This script directly runs the server with MongoDB shadow storage for device shadows,
ensuring temperature history data is visible. No file modifications, just proper configuration.
"""
import asyncio
import logging
import os
import subprocess
import sys
from datetime import datetime

import motor.motor_asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# MongoDB configuration
MONGODB_URI = "mongodb://localhost:27017/"
MONGODB_DB_NAME = "iotsphere"
SHADOWS_COLLECTION = "device_shadows"
DEVICE_IDS = ["wh-001", "wh-002", "wh-e0ae2f58", "wh-e1ae2f59"]


async def verify_mongodb():
    """Verify MongoDB connection and shadow documents"""
    try:
        logger.info(f"Testing MongoDB connection to {MONGODB_URI}")

        # Create MongoDB client
        client = motor.motor_asyncio.AsyncIOMotorClient(
            MONGODB_URI, serverSelectionTimeoutMS=5000  # 5 second timeout
        )

        # Force a connection check
        await client.server_info()
        logger.info("✅ MongoDB connection successful")

        # Check database and collection
        db = client[MONGODB_DB_NAME]
        collections = await db.list_collection_names()

        if SHADOWS_COLLECTION in collections:
            logger.info(f"✅ Collection '{SHADOWS_COLLECTION}' exists")

            # Check for shadow documents
            count = await db[SHADOWS_COLLECTION].count_documents({})
            logger.info(f"✅ Found {count} shadow documents")

            if count > 0:
                # Check specific devices to verify history
                all_valid = True
                for device_id in DEVICE_IDS:
                    shadow = await db[SHADOWS_COLLECTION].find_one(
                        {"device_id": device_id}
                    )

                    if shadow:
                        history = shadow.get("history", [])
                        logger.info(
                            f"✅ Shadow for {device_id} has {len(history)} history entries"
                        )
                        if len(history) < 10:
                            logger.warning(
                                f"⚠️ Shadow for {device_id} has insufficient history entries"
                            )
                            all_valid = False
                    else:
                        logger.warning(f"⚠️ No shadow found for {device_id}")
                        all_valid = False

                return all_valid
            else:
                logger.warning("⚠️ No shadow documents found")
                return False
        else:
            logger.warning(f"⚠️ Collection '{SHADOWS_COLLECTION}' does not exist")
            return False

        client.close()
        return True

    except Exception as e:
        logger.error(f"❌ MongoDB connection error: {str(e)}")
        import traceback

        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False


def start_server(port, websocket_port):
    """Start the server with MongoDB shadow storage"""
    # Set environment variables for MongoDB
    env = os.environ.copy()
    env["SHADOW_STORAGE_TYPE"] = "mongodb"
    env["MONGODB_URI"] = MONGODB_URI
    env["MONGODB_DB_NAME"] = MONGODB_DB_NAME
    env["WEBSOCKET_PORT"] = str(websocket_port)

    # Build the uvicorn command
    cmd = [
        "python",
        "-m",
        "uvicorn",
        "src.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
    ]

    logger.info(f"🚀 Starting IoTSphere with MongoDB shadow storage")
    logger.info(f"Web interface: http://localhost:{port}")
    logger.info(f"WebSocket server: ws://localhost:{websocket_port}")
    logger.info(f"Temperature history: http://localhost:{port}/water-heaters/wh-001")

    # Start the server with the specified environment variables
    subprocess.run(cmd, env=env, check=True)


def main():
    """Main function"""
    # Parse command line args
    port = 7080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid port: {sys.argv[1]}, using default: {port}")

    websocket_port = 7777

    try:
        # Stop any running servers
        os.system(
            "killall -9 python python3 2>/dev/null || echo 'No Python processes found'"
        )

        # Verify MongoDB
        logger.info("🔍 Verifying MongoDB connection and shadow documents")
        success = asyncio.run(verify_mongodb())

        if not success:
            logger.warning("⚠️ MongoDB verification had issues, continuing anyway")

        # Start the server
        start_server(port, websocket_port)

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
