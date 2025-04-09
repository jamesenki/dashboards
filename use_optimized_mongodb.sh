#!/bin/bash
# This script sets up the environment variables to use the optimized MongoDB storage
export SHADOW_STORAGE_TYPE=mongodb
export USE_OPTIMIZED_MONGODB=true
export MONGODB_POOL_SIZE=20  # Increased pool size for better performance

echo "✅ Environment configured to use optimized MongoDB storage"
echo "To start the application with these settings, run:"
echo "source use_optimized_mongodb.sh && python -m src.main"
