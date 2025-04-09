"""
Start the IoTSphere application with MongoDB for both Shadow Storage and Asset Registry
"""
import logging
import os
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Kill any processes using port 8006 to prevent conflicts
try:
    import subprocess
    subprocess.run(["lsof", "-ti", ":8006", "|" "xargs", "kill", "-9"], shell=True)
    logger.info("Killed processes using port 8006")
except Exception as e:
    logger.warning(f"Could not kill processes on port 8006: {e}")

# Force MongoDB for ALL services before any imports occur
os.environ["SHADOW_STORAGE_TYPE"] = "mongodb"
os.environ["ASSET_REGISTRY_STORAGE"] = "mongodb"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/"
os.environ["MONGODB_DB_NAME"] = "iotsphere"

# Use a different WebSocket port (8888) to avoid conflicts
os.environ["WEBSOCKET_PORT"] = "8888"

# Force use of MongoDB repositories
os.environ["USE_MOCK_DATA"] = "false"
os.environ["FORCE_DATABASE_REPOSITORY"] = "true"

logger.info("Starting IoTSphere with MongoDB configured for ALL services")
logger.info(f"Shadow storage type: {os.environ.get('SHADOW_STORAGE_TYPE')}")
logger.info(f"Asset Registry storage: {os.environ.get('ASSET_REGISTRY_STORAGE')}")
logger.info(f"MongoDB URI: {os.environ.get('MONGODB_URI')}")
logger.info(f"MongoDB Database: {os.environ.get('MONGODB_DB_NAME')}")
logger.info(f"WebSocket port: {os.environ.get('WEBSOCKET_PORT')}")

# Now import and run the main application
from src.main import app

if __name__ == "__main__":
    # Pass command line arguments to the main application
    import uvicorn

    # Use the standard port for the web server (8006)
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8006,
        reload=True,
        reload_dirs=["src"]
    )
