"""
Simple MongoDB connection verifier and server starter for IoTSphere

This script:
1. Verifies MongoDB connection and shadow documents
2. Directly modifies the main.py file to enforce MongoDB shadow storage
3. Starts the server with proper configuration
"""
import asyncio
import logging
import os
import shutil
import sys
import tempfile
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
CONFIG = {
    "mongo_uri": "mongodb://localhost:27017/",
    "db_name": "iotsphere",
    "collection": "device_shadows",
}


async def verify_mongodb():
    """Verify MongoDB connection and shadow documents"""
    try:
        logger.info(f"Testing MongoDB connection to {CONFIG['mongo_uri']}")

        # Create MongoDB client
        client = motor.motor_asyncio.AsyncIOMotorClient(
            CONFIG["mongo_uri"], serverSelectionTimeoutMS=5000  # 5 second timeout
        )

        # Force a connection check
        await client.server_info()
        logger.info("✅ MongoDB connection successful")

        # Check database and collection
        db = client[CONFIG["db_name"]]
        collections = await db.list_collection_names()

        if CONFIG["collection"] in collections:
            logger.info(f"✅ Collection '{CONFIG['collection']}' exists")

            # Check for shadow documents
            count = await db[CONFIG["collection"]].count_documents({})
            logger.info(f"✅ Found {count} shadow documents")

            if count > 0:
                # Check a specific device to verify history
                device_id = "wh-001"
                shadow = await db[CONFIG["collection"]].find_one(
                    {"device_id": device_id}
                )

                if shadow:
                    history = shadow.get("history", [])
                    logger.info(
                        f"✅ Shadow for {device_id} has {len(history)} history entries"
                    )
                    return True
                else:
                    logger.warning(f"⚠️ No shadow found for {device_id}")
                    return False
            else:
                logger.warning("⚠️ No shadow documents found")
                return False
        else:
            logger.warning(f"⚠️ Collection '{CONFIG['collection']}' does not exist")
            return False

        client.close()
        return True

    except Exception as e:
        logger.error(f"❌ MongoDB connection error: {str(e)}")
        import traceback

        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False


def modify_main_py():
    """Directly modify the main.py file to use MongoDB storage"""
    main_py_path = "src/main.py"
    backup_path = "src/main.py.backup"

    # Create backup of original file
    shutil.copy2(main_py_path, backup_path)
    logger.info(f"Created backup at {backup_path}")

    # Read the file
    with open(main_py_path, "r") as f:
        content = f.read()

    # Flag to track if we made changes
    modified = False

    # Add the modified imports if needed
    if (
        "from src.infrastructure.device_shadow.mongodb_shadow_storage import MongoDBShadowStorage"
        not in content
    ):
        import_line = "from src.infrastructure.device_shadow.storage_factory import create_shadow_storage_provider"
        new_import = """from src.infrastructure.device_shadow.storage_factory import create_shadow_storage_provider
from src.infrastructure.device_shadow.mongodb_shadow_storage import MongoDBShadowStorage"""
        content = content.replace(import_line, new_import)
        modified = True

    # Find the startup_event function and modify it to use MongoDB
    if '@app.on_event("startup")' in content:
        # Look for the line where shadow storage is created
        if "storage_provider = await create_shadow_storage_provider()" in content:
            # Replace it with direct MongoDB initialization
            old_code = "    storage_provider = await create_shadow_storage_provider()"
            new_code = """    # Force MongoDB shadow storage
    logger.info("Forcing MongoDB shadow storage")
    mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
    db_name = os.environ.get("MONGODB_DB_NAME", "iotsphere")
    logger.info(f"Using MongoDB: {mongo_uri}, DB: {db_name}")

    storage_provider = MongoDBShadowStorage(mongo_uri=mongo_uri, db_name=db_name)
    await storage_provider.initialize()
    logger.info("MongoDB shadow storage initialized successfully")"""

            content = content.replace(old_code, new_code)
            modified = True

    if modified:
        # Write the modified content
        with open(main_py_path, "w") as f:
            f.write(content)
        logger.info("✅ Successfully modified main.py to force MongoDB shadow storage")
        return True
    else:
        logger.warning("⚠️ No changes made to main.py")
        return False


def main():
    """Main function to verify MongoDB and start the server"""
    # Parse command line args
    port = 7080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid port: {sys.argv[1]}, using default: {port}")

    websocket_port = 7777

    # Verify MongoDB
    logger.info("🔍 Verifying MongoDB connection and shadow documents")
    success = asyncio.run(verify_mongodb())

    if not success:
        logger.error(
            "❌ MongoDB verification failed. Please ensure MongoDB is running with shadow documents."
        )
        return 1

    # Modify main.py to force MongoDB
    logger.info("🔧 Modifying main.py to force MongoDB shadow storage")
    if not modify_main_py():
        logger.error("❌ Failed to modify main.py")
        return 1

    # Set environment variables
    os.environ["SHADOW_STORAGE_TYPE"] = "mongodb"
    os.environ["MONGODB_URI"] = CONFIG["mongo_uri"]
    os.environ["MONGODB_DB_NAME"] = CONFIG["db_name"]
    os.environ["WEBSOCKET_PORT"] = str(websocket_port)

    # Start the server
    logger.info(
        f"🚀 Starting IoTSphere on port {port} with WebSocket on port {websocket_port}"
    )
    logger.info(
        f"📊 Temperature history should be visible at: http://localhost:{port}/water-heaters/wh-001"
    )

    # Build the command
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

    # Execute the command
    import subprocess

    try:
        subprocess.run(cmd, check=True)
        return 0
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error starting server: {str(e)}")
        return 1
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return 0


if __name__ == "__main__":
    # Kill any running Python processes
    os.system(
        "killall -9 python python3 2>/dev/null || echo 'No Python processes found'"
    )

    # Run the main function
    sys.exit(main())
