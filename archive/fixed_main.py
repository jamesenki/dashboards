"""
IoTSphere main application with fixed MongoDB shadow storage
This version directly initializes MongoDB shadow storage, bypassing the factory
"""
import logging
import os
import sys

import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set environment variables to use MongoDB
os.environ["SHADOW_STORAGE_TYPE"] = "mongodb"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/"
os.environ["MONGODB_DB_NAME"] = "iotsphere"
os.environ["WEBSOCKET_PORT"] = "7777"  # Use a specific WebSocket port

async def start_with_fixed_mongodb():
    """Start the main application with MongoDB shadow storage directly injected"""
    try:
        # Import the main app and required modules
        from src.infrastructure.device_shadow.mongodb_shadow_storage import (
            MongoDBShadowStorage,
        )
        from src.main import app as fastapi_app
        from src.services.device_shadow import DeviceShadowService

        # Get the port from command line or use default
        port = 8000
        if len(sys.argv) > 1:
            try:
                port = int(sys.argv[1])
            except ValueError:
                pass

        # Create MongoDB storage directly
        mongo_uri = os.environ["MONGODB_URI"]
        db_name = os.environ["MONGODB_DB_NAME"]
        logger.info(f"🔌 Directly connecting to MongoDB at {mongo_uri}, DB: {db_name}")

        storage = MongoDBShadowStorage(mongo_uri=mongo_uri, db_name=db_name)

        # Initialize the MongoDB connection
        await storage.initialize()
        logger.info("✅ MongoDB connection initialized successfully")

        # Create a DeviceShadowService with the MongoDB storage
        shadow_service = DeviceShadowService(storage_provider=storage)

        # Inject the service into the FastAPI application
        fastapi_app.state.shadow_service = shadow_service
        logger.info("✅ Shadow service with MongoDB storage injected into application")

        # Display information about MongoDB status
        device_ids = ["wh-001", "wh-002", "wh-e0ae2f58", "wh-e1ae2f59"]
        for device_id in device_ids:
            if await storage.shadow_exists(device_id):
                shadow = await storage.get_shadow(device_id)
                history_count = len(shadow.get("history", []))
                logger.info(f"✅ Shadow for {device_id} has {history_count} history entries")
            else:
                logger.warning(f"⚠️ No shadow document found for {device_id}")

        # Log server information
        logger.info("")
        logger.info("🌐 Server details:")
        logger.info(f"   - Web interface: http://localhost:{port}")
        logger.info(f"   - WebSocket server: ws://localhost:{os.environ['WEBSOCKET_PORT']}")
        logger.info(f"   - Shadow storage: MongoDB ({mongo_uri})")
        logger.info("")
        logger.info("🧪 To test temperature history:")
        logger.info(f"   - Open http://localhost:{port}/water-heaters/wh-001")
        logger.info("   - Verify the temperature history chart appears with data")
        logger.info("")

        # Close the MongoDB connection to avoid potential conflicts when uvicorn starts
        await storage.close()

        # Start the FastAPI application with uvicorn
        logger.info(f"🚀 Starting IoTSphere on port {port}")
        uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=False)

    except Exception as e:
        logger.error(f"❌ Error starting application: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    # Parse port from command line
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid port number: {sys.argv[1]}, using default: {port}")

    # Import asyncio to run the async main function
    import asyncio

    # Run the main function
    logger.info(f"🔧 Starting IoTSphere with fixed MongoDB shadow storage on port {port}")
    asyncio.run(start_with_fixed_mongodb())
