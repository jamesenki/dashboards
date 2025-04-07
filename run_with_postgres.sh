#!/bin/bash
# Run the IoTSphere application with PostgreSQL settings
# This script ensures that the application uses PostgreSQL without falling back to mock data

# Set temporary environment variables
export IOTSPHERE_ENV=development
export DB_TYPE=postgres
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=iotsphere
export DB_USER=iotsphere
export DB_PASSWORD=iotsphere
export FALLBACK_TO_MOCK=false

# Print status
echo "Starting IoTSphere with PostgreSQL data source..."
echo "Data source configuration:"
echo "  DB_TYPE: $DB_TYPE"
echo "  DB_HOST: $DB_HOST"
echo "  FALLBACK_TO_MOCK: $FALLBACK_TO_MOCK"

# Run the application
uvicorn src.main:app --port 8006 --reload

# Notes:
# 1. Access the application at http://localhost:8006
# 2. Check the data source indicator in the bottom-right corner
# 3. Look for "PostgreSQL" instead of "Mock"
