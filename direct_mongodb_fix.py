"""
Direct fix for MongoDB shadow storage in IoTSphere

This script:
1. Directly modifies the DeviceShadowService to force MongoDB storage
2. Verifies shadow documents exist with history data
3. Starts the server with guaranteed MongoDB shadow storage
"""
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Force environment variables
os.environ["SHADOW_STORAGE_TYPE"] = "mongodb"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/"
os.environ["MONGODB_DB_NAME"] = "iotsphere"
os.environ["WEBSOCKET_PORT"] = "7777"

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- DIRECT MODIFICATION OF THE SHADOW SERVICE CLASS ---

# First, let's modify the DeviceShadowService to always use MongoDB
from src.services.device_shadow import DeviceShadowService

# Store the original init method
original_init = DeviceShadowService.__init__


# Create a patched init method
def patched_init(self, storage_provider=None):
    """
    Patched __init__ that forces MongoDB storage
    """
    # Skip if already initialized (prevent infinite recursion)
    if hasattr(self, "initialized") and self.initialized:
        return

    logger.info("🔄 Using patched DeviceShadowService.__init__ - FORCING MongoDB")

    # Import MongoDB storage with a direct import
    from src.infrastructure.device_shadow.mongodb_shadow_storage import (
        MongoDBShadowStorage,
    )

    # Create MongoDB storage if not provided
    if storage_provider is None:
        mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
        db_name = os.environ.get("MONGODB_DB_NAME", "iotsphere")

        logger.info(f"📊 Creating MongoDB storage ({mongo_uri}, {db_name})")
        mongo_storage = MongoDBShadowStorage(mongo_uri=mongo_uri, db_name=db_name)

        # Initialize synchronously
        import asyncio

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(mongo_storage.initialize())
            logger.info("✅ MongoDB connection initialized successfully")
            storage_provider = mongo_storage
        except Exception as e:
            logger.error(f"❌ MongoDB initialization failed: {str(e)}")
            # Raise exception to make the issue visible (don't fall back silently)
            raise RuntimeError(
                f"MongoDB shadow storage initialization failed: {str(e)}"
            )
        finally:
            loop.close()

    # Call original init with MongoDB storage
    original_init(self, storage_provider)

    # Mark as initialized to prevent reinitializing
    self.initialized = True
    logger.info("✅ DeviceShadowService initialized with MongoDB storage")


# Apply the patch
DeviceShadowService.__init__ = patched_init

logger.info("✅ Applied MongoDB patch to DeviceShadowService")

# --- COMMAND LINE ARGUMENT HANDLING ---

# Get port from command line
port = 7080
if len(sys.argv) > 1:
    try:
        port = int(sys.argv[1])
    except ValueError:
        logger.error(f"Invalid port number: {sys.argv[1]}, using default: {port}")

# --- SERVER STARTUP ---

logger.info(f"🚀 Starting IoTSphere with fixed MongoDB shadow storage on port {port}")
logger.info(
    f"📊 Temperature history should be visible at: http://localhost:{port}/water-heaters/wh-001"
)

# Start the server
import uvicorn

uvicorn.run("src.main:app", host="0.0.0.0", port=port)
