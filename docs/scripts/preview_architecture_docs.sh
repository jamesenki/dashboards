#!/bin/bash

# Simple script to preview the architecture documentation
# Follows TDD principles by providing a reliable, verifiable way to view the documentation

echo "Starting IoTSphere Architecture Documentation Preview Server..."

DOCS_DIR="/Users/lisasimon/repos/IoTSphereAngular/IoTSphere-Refactor/docs"
PORT=8080

# Check if Python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is required but not found."
    exit 1
fi

# Go to docs directory and start a simple HTTP server
cd "$DOCS_DIR" && python3 -m http.server $PORT
