"""
Run the IoTSphere application with MongoDB shadow storage FORCED
This script bypasses the environment variable configuration system
and directly creates and injects the MongoDB shadow storage
"""
import asyncio
import os
import sys
from typing import Any, Dict

import uvicorn

# Add MongoDB driver
os.environ["WEBSOCKET_PORT"] = "9990"

from src.infrastructure.device_shadow.mongodb_shadow_storage import MongoDBShadowStorage

# Import application components
from src.main import app
from src.services.device_shadow import DeviceShadowService, InMemoryShadowStorage


# Override the shadow service provider at runtime
async def setup_mongodb_shadow():
    from src.container import get_container

    print("⚡ BYPASSING ENVIRONMENT: Forcing MongoDB shadow storage")

    # Create MongoDB storage
    mongo_uri = "mongodb://localhost:27017/"
    db_name = "iotsphere"
    print(f"⚡ Creating MongoDB storage with URI: {mongo_uri}, DB: {db_name}")

    mongo_storage = MongoDBShadowStorage(mongo_uri=mongo_uri, db_name=db_name)

    # Initialize it
    print("⚡ Initializing MongoDB connection")
    await mongo_storage.initialize()
    print("✅ MongoDB connection successful!")

    # Get the container
    container = get_container()

    # Force-replace the shadow service
    print("⚡ Creating new DeviceShadowService with MongoDB storage")
    shadow_service = DeviceShadowService(mongo_storage)

    # Replace the shadow service in the container
    print("⚡ Injecting MongoDB shadow service into container")
    container.shadow_service = shadow_service

    # Verify shadow exists
    device_id = "wh-001"
    exists = await mongo_storage.shadow_exists(device_id)
    print(f"✅ Shadow exists for {device_id}: {exists}")

    if exists:
        shadow = await mongo_storage.get_shadow(device_id)
        print(f"✅ Retrieved shadow for {device_id}, version: {shadow.get('version')}")
        history = shadow.get("history", [])
        print(f"✅ Shadow has {len(history)} history entries")

    print("✅ MongoDB shadow storage FORCED - service ready!")
    return True


@app.on_event("startup")
async def startup_db_client():
    await setup_mongodb_shadow()


if __name__ == "__main__":
    print("Starting IoTSphere with FORCED MongoDB shadow storage")

    uvicorn.run(
        "force_mongodb:app",
        host="0.0.0.0",
        port=8090,
        reload=False,  # Disable reload to prevent startup event duplication
    )
