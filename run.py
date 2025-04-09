"""
Entry point for the IoTSphere application.
This file ensures proper imports and application startup.

By default, this script configures the application to use:
- MongoDB for persistent storage (Shadow Service and Asset Registry)
- Standard port 8006 for the web server
- Port 8888 for WebSockets
- Real database repositories instead of mock data

USAGE EXAMPLES:
  python run.py                        # Standard startup with MongoDB
  python run.py --in-memory            # Use in-memory storage (not recommended)
  python run.py --websocket-port 7777  # Use custom WebSocket port
"""
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

logger.info("Starting IoTSphere application with MongoDB for persistent storage")

# Add the current directory to the path to ensure imports work properly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app from src.main
from src.main import app

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting web server on port 8006")
    logger.info("To access the application, visit http://localhost:8006")

    # Run the application
    uvicorn.run(
        "src.main:app", host="0.0.0.0", port=8006, reload=True, reload_dirs=["src"]
    )
