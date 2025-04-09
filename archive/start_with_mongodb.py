"""
Start the IoTSphere application with MongoDB shadow storage
"""
import os
import sys

# Force MongoDB shadow storage before any imports occur
os.environ["SHADOW_STORAGE_TYPE"] = "mongodb"
os.environ["WEBSOCKET_PORT"] = "9990"  # Use a different WebSocket port to avoid conflicts

# Now import and run the main application
from src.main import app

if __name__ == "__main__":
    # Pass command line arguments to the main application
    import uvicorn

    print("Starting IoTSphere with MongoDB shadow storage")
    print(f"Shadow storage type: {os.environ.get('SHADOW_STORAGE_TYPE')}")
    print(f"WebSocket port: {os.environ.get('WEBSOCKET_PORT')}")

    # Use a different port for the web server to avoid conflicts
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8090,
        reload=True
    )
