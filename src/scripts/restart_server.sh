#!/bin/bash
# Simple script to restart the IoTSphere server with a clean state

echo "Stopping any running IoTSphere processes..."
pkill -f "python -m src.main" || echo "No running processes found"

echo "Cleaning browser cache files..."
rm -f ui_validation_screenshot.png

echo "Starting server..."
cd /Users/lisasimon/repos/IoTSphereAngular/IoTSphere-Refactor
python -m src.main &

echo "Server started in background. Wait a moment for it to initialize..."
sleep 5

echo "Server is ready. Now let's run the UI validation script to check water heater count..."
python src/scripts/ui_data_validation.py
