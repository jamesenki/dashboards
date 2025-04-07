#!/usr/bin/env python
"""
Development server runner for IoTSphere with proper environment setup.

This script sets up the development environment with appropriate variables for
testing and debugging WebSockets and other features, then starts the uvicorn server.
"""
import os
import sys
import subprocess
from pathlib import Path

# Set environment variables needed for development
env_vars = {
    "APP_ENV": "development",
    "DEBUG_WEBSOCKET": "true",
    "LOG_LEVEL": "INFO" 
}

# Update the environment
for key, value in env_vars.items():
    os.environ[key] = value
    print(f"Set {key}={value}")

# Path to the app
app_path = str(Path(__file__).parent / "src" / "main.py")
print(f"Starting server with app at: {app_path}")

# Command for uvicorn with reload
cmd = [
    sys.executable,
    "-m", "uvicorn",
    "src.main:app",
    "--reload",
    "--host", "127.0.0.1",
    "--port", "8000"
]

# Print the command for reference
print(f"Running command: {' '.join(cmd)}")
print("\nIoTSphere Development Server")
print("============================")
print("Environment:")
for key, value in env_vars.items():
    print(f"  {key}: {value}")
print("\nTest Token for WebSockets:")
print("  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidGVzdC11c2VyLTAwMSIsInVzZXJuYW1lIjoidGVzdF91c2VyIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzQ0MDYwMDAwfQ.thisIsATestToken")
print("\nTest Endpoints:")
print("  /ws/test/device/wh-d94a7707")
print("  /ws/test/broadcast")
print("  /ws/fixed/devices/wh-d94a7707/state")
print("  /ws/fixed/broadcast")
print("\nPress Ctrl+C to stop the server\n")

try:
    # Run uvicorn with the environment variables
    process = subprocess.run(cmd, env=os.environ)
    sys.exit(process.returncode)
except KeyboardInterrupt:
    print("\nShutting down server")
    sys.exit(0)
