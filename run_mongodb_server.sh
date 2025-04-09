#!/bin/bash
# Script to start IoTSphere with MongoDB shadow storage

echo "🚀 Starting IoTSphere with MongoDB shadow storage"

# Stop any running servers
echo "Stopping any running Python processes..."
killall -9 python python3 || echo "No Python processes found"

# Set environment variables for MongoDB
export SHADOW_STORAGE_TYPE="mongodb"
export MONGODB_URI="mongodb://localhost:27017/"
export MONGODB_DB_NAME="iotsphere"
export WEBSOCKET_PORT=7777

# Get port from argument or use default
PORT=${1:-8000}

echo "📊 Configuration:"
echo "- Web server: http://localhost:$PORT"
echo "- WebSocket: ws://localhost:$WEBSOCKET_PORT"
echo "- Shadow storage: MongoDB ($MONGODB_URI)"
echo ""

echo "Starting server..."
cd "$(dirname "$0")"
python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT --reload

echo "Server stopped."
