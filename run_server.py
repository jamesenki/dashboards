#!/usr/bin/env python3
"""
IoTSphere Server Runner
Properly configures the Python path and starts the IoTSphere application.
Handles import issues by ensuring the root directory is in the Python path.
"""

import argparse
import importlib
import os
import subprocess
import sys


def run_server(port=8006):
    """Configure the environment and run the server with the correct Python path.

    Args:
        port: The port number to run the server on (default: 8006)
    """
    # Get the absolute path to the project root directory
    root_dir = os.path.dirname(os.path.abspath(__file__))

    # Ensure the root directory is in the Python path
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

    print(f"Starting IoTSphere server from: {root_dir}")

    # Run the fix_imports script first
    try:
        # Try to import and run it
        sys.path.insert(0, root_dir)
        print("Running fix_imports.py to repair package structure...")
        from fix_imports import fix_api_routes

        fix_api_routes()
        print("Package structure fixed successfully")
    except Exception as e:
        print(f"Error running fix_imports.py: {e}")
        print("Will attempt to continue anyway...")

    # Initialize water heater shadows to ensure they exist on server start
    try:
        print("\nInitializing water heaters and shadow documents...")
        water_heater_script = os.path.join(root_dir, "create_water_heater_shadows.py")
        subprocess.run([sys.executable, water_heater_script], check=True)
        print("Water heaters initialized successfully")
    except Exception as e:
        print(f"Error initializing water heaters: {e}")
        print("Will attempt to continue anyway...")

    # Set environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = root_dir

    # Start the server using uvicorn
    cmd = [
        "uvicorn",
        "src.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
        "--reload",
    ]

    print(f"Running command: {' '.join(cmd)}")
    print(f"The application will be available at http://localhost:{port}")
    subprocess.run(cmd, env=env)


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the IoTSphere server")
    parser.add_argument(
        "--port",
        type=int,
        default=8006,
        help="Port to run the server on (default: 8006)",
    )
    args = parser.parse_args()

    # Run the server with the specified port
    run_server(port=args.port)
