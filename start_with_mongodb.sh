#!/bin/bash
# Simple script to start IoTSphere with MongoDB shadow storage

# Kill any running servers
echo "🛑 Stopping any running servers..."
killall -9 python python3 2>/dev/null || echo "No Python processes found"

# Get port from command line or use default
PORT=${1:-7080}
WEBSOCKET_PORT=7777

# Set environment variables for MongoDB
export SHADOW_STORAGE_TYPE="mongodb"
export MONGODB_URI="mongodb://localhost:27017/"
export MONGODB_DB_NAME="iotsphere"
export WEBSOCKET_PORT="${WEBSOCKET_PORT}"

echo "🚀 Starting IoTSphere with MongoDB shadow storage"
echo "💾 Using MongoDB at ${MONGODB_URI}, database: ${MONGODB_DB_NAME}"
echo "🌐 Web server: http://localhost:${PORT}"
echo "🔌 WebSocket: ws://localhost:${WEBSOCKET_PORT}"
echo "📊 Temperature history should be visible at: http://localhost:${PORT}/water-heaters/wh-001"
echo ""

# Start the server with uvicorn
cd "$(dirname "$0")"
python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT
