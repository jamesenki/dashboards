"""
Entry point for the IoTSphere application.
This file ensures proper imports and application startup.
"""
import os
import sys

# Add the current directory to the path to ensure imports work properly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app from src.main
from src.main import app

if __name__ == "__main__":
    import uvicorn

    # Run the application
    uvicorn.run(
        "src.main:app", host="0.0.0.0", port=8006, reload=True, reload_dirs=["src"]
    )
