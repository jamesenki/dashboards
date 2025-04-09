"""
Start IoTSphere with guaranteed MongoDB shadow storage
This script sets the needed environment variables and starts the server
"""
import os
import subprocess
import sys

# Force MongoDB for shadow storage
os.environ["SHADOW_STORAGE_TYPE"] = "mongodb"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/"
os.environ["MONGODB_DB_NAME"] = "iotsphere"
os.environ["WEBSOCKET_PORT"] = "7777"  # Use a specific WebSocket port

# Set port from command line or use default
port = 7080
if len(sys.argv) > 1:
    try:
        port = int(sys.argv[1])
    except ValueError:
        print(f"Invalid port number: {sys.argv[1]}, using default: {port}")

print(f"🚀 Starting IoTSphere with MongoDB shadow storage on port {port}")
print(f"🌐 Web interface will be at: http://localhost:{port}")
print(f"🔌 WebSocket server will be at: ws://localhost:7777")
print(
    f"📊 Temperature history should now be visible at: http://localhost:{port}/water-heaters/wh-001"
)

try:
    # Start the server with uvicorn directly
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

    # Execute command with environment variables set
    subprocess.run(cmd, check=True)

except KeyboardInterrupt:
    print("\n🛑 Server stopped by user")

except Exception as e:
    print(f"❌ Error starting server: {str(e)}")
    sys.exit(1)
