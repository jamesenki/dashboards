#!/bin/bash
# IoTSphere MongoDB Starter Script
# This script:
# 1. Checks MongoDB connection and shadow documents
# 2. Starts the server with MongoDB storage in strict mode
# 3. Ensures temperature history is properly displayed

# Stop any running servers
echo "🛑 Stopping any running Python processes..."
killall -9 python python3 2>/dev/null || echo "No Python processes found"

# Get port from command line or use default
PORT=${1:-7080}
WEBSOCKET_PORT=7777

echo "🔍 Checking MongoDB connection and shadow documents..."
python check_mongodb.py

# Check if the diagnostic was successful
if [ $? -ne 0 ]; then
  echo "❌ MongoDB diagnostic failed. Please fix the issues before starting the server."
  exit 1
fi

echo "🔧 Patching storage factory with fixed version..."
cp src/infrastructure/device_shadow/storage_factory_fix.py src/infrastructure/device_shadow/storage_factory.py

echo "🚀 Starting IoTSphere with MongoDB shadow storage..."
echo "📊 Configuration:"
echo "- Web server: http://localhost:$PORT"
echo "- WebSocket: ws://localhost:$WEBSOCKET_PORT"
echo ""
echo "🔍 Temperature history should be visible at:"
echo "http://localhost:$PORT/water-heaters/wh-001"

# Set environment variables for MongoDB with strict mode
export SHADOW_STORAGE_TYPE="mongodb"
export MONGODB_URI="mongodb://localhost:27017/"
export MONGODB_DB_NAME="iotsphere"
export WEBSOCKET_PORT="$WEBSOCKET_PORT"
export STRICT_SHADOW_STORAGE="true"

# Start the server
python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT --reload
