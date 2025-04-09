#!/usr/bin/env python3
"""
IMPORTANT: This script will create shadow documents with history data
in both MongoDB and in-memory storage to ensure availability.

Script to fix the shadow document for the specific water heater with ID 'wh-e0ae2f58'.
This script ensures the shadow has temperature history data for chart display.
"""
import asyncio
import logging
import os
import random
import sys
from datetime import datetime, timedelta

# Add parent directory to path to allow imports to work
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def fix_water_heater_shadow():
    """Create or update shadow document for specific water heater."""
    import motor.motor_asyncio

    from src.infrastructure.device_shadow.mongodb_shadow_storage import (
        MongoDBShadowStorage,
    )
    from src.services.asset_registry import AssetRegistryService
    from src.services.device_shadow import DeviceShadowService, InMemoryShadowStorage

    # Target water heater IDs - let's ensure all water heaters have proper shadows
    heater_ids = [
        "wh-e0ae2f58",  # Original heater with issues
        "wh-e1ae2f59",
        "wh-e2ae2f60",
        "wh-e3ae2f61",
        "wh-e4ae2f62",
        "wh-e5ae2f63",
        "wh-001",
        "wh-002",
    ]

    logger.info(f"Fixing shadow documents for {len(heater_ids)} water heaters")

    # First, initialize MongoDB connection directly
    logger.info("Initializing MongoDB connection")
    mongo_uri = "mongodb://localhost:27017/"
    db_name = "iotsphere"
    mongo_storage = MongoDBShadowStorage(mongo_uri=mongo_uri, db_name=db_name)
    await mongo_storage.initialize()

    # Also create in-memory storage for direct access
    in_memory_storage = InMemoryShadowStorage()

    # Create service instances
    shadow_service = DeviceShadowService(storage_provider=in_memory_storage)
    registry_service = AssetRegistryService()

    for heater_id in heater_ids:
        # 1. ENSURE WATER HEATER IS IN REGISTRY
        try:
            # Check if device is in registry
            device = await registry_service.get_device(heater_id)
            logger.info(f"Device {heater_id} already exists in registry")
        except Exception as e:
            logger.info(f"Adding device {heater_id} to asset registry")

            # Create device in asset registry
            device_data = {
                "device_id": heater_id,
                "name": f"Water Heater {heater_id.split('-')[1]}",
                "manufacturer": "AquaSmart",
                "brand": "AquaSmart",
                "model": "SmartTank Pro",
                "type": "water_heater",
                "status": "ONLINE",
                "location": "Building A",
                "installation_date": datetime.now().isoformat(),
                "warranty_expiry": (
                    datetime.now() + timedelta(days=365 * 5)
                ).isoformat(),
                "capacity": 50,
                "efficiency_rating": 0.92,
                "heater_type": "Tank",
                "features": ["Smart Control", "Energy Efficient", "Remote Monitoring"],
            }

            try:
                await registry_service.register_device(device_data)
                logger.info(f"Added {heater_id} to asset registry")
            except Exception as reg_error:
                logger.error(f"Error adding {heater_id} to registry: {reg_error}")

        # 2. CREATE OR UPDATE SHADOW DOCUMENT
        try:
            # Create initial shadow state if needed
            initial_state = {
                "device_id": heater_id,
                "reported": {
                    "name": f"Water Heater {heater_id.split('-')[1]}",
                    "model": "SmartTank Pro",
                    "manufacturer": "AquaSmart",
                    "temperature": 120.5,
                    "target_temperature": 125.0,
                    "min_temperature": 40.0,
                    "max_temperature": 140.0,
                    "pressure": 60.0,
                    "flow_rate": 3.2,
                    "energy_usage": 450.0,
                    "heater_status": "STANDBY",
                    "connection_status": "ONLINE",
                    "mode": "ECO",
                    "timestamp": datetime.now().isoformat() + "Z",
                },
                "desired": {"temperature": 125.0, "mode": "ECO"},
            }

            # 1. Create/update shadow in in-memory storage
            try:
                shadow_exists = True
                try:
                    await shadow_service.get_device_shadow(heater_id)
                    logger.info(f"In-memory shadow exists for {heater_id}")
                except Exception:
                    shadow_exists = False
                    logger.info(f"No in-memory shadow for {heater_id}")

                if not shadow_exists:
                    # Create shadow document if it doesn't exist
                    await shadow_service.create_device_shadow(heater_id, initial_state)
                    logger.info(f"Created in-memory shadow for {heater_id}")
                else:
                    # Update existing shadow
                    await shadow_service.update_device_shadow(
                        heater_id,
                        reported_state=initial_state["reported"],
                        desired_state=initial_state["desired"],
                    )
                    logger.info(f"Updated in-memory shadow for {heater_id}")
            except Exception as mem_error:
                logger.error(
                    f"Error with in-memory shadow for {heater_id}: {mem_error}"
                )

            # 2. Create/update shadow in MongoDB storage directly
            try:
                mongo_shadow_exists = await mongo_storage.shadow_exists(heater_id)

                if not mongo_shadow_exists:
                    # Create new MongoDB shadow document
                    await mongo_storage.save_shadow(heater_id, initial_state)
                    logger.info(f"Created MongoDB shadow for {heater_id}")
                else:
                    # Update existing MongoDB shadow document
                    current = await mongo_storage.get_shadow(heater_id)
                    current["reported"].update(initial_state["reported"])
                    current["desired"].update(initial_state["desired"])
                    current["version"] = current.get("version", 0) + 1
                    current["metadata"] = current.get("metadata", {})
                    current["metadata"]["last_updated"] = (
                        datetime.now().isoformat() + "Z"
                    )

                    await mongo_storage.save_shadow(heater_id, current)
                    logger.info(f"Updated MongoDB shadow for {heater_id}")
            except Exception as mongo_error:
                logger.error(
                    f"Error with MongoDB shadow for {heater_id}: {mongo_error}"
                )

        except Exception as shadow_error:
            logger.error(f"Error updating shadow for {heater_id}: {shadow_error}")
            continue

        # 3. GENERATE HISTORY DATA
        try:
            logger.info(f"Generating history data for {heater_id}")
            historical_readings = await generate_shadow_history_data(heater_id, days=7)

            # Add history to in-memory storage
            try:
                await shadow_service.update_device_shadow_history(
                    heater_id, historical_readings
                )
                logger.info(
                    f"Added {len(historical_readings)} history entries to in-memory storage for {heater_id}"
                )
            except Exception as mem_history_error:
                logger.error(
                    f"Error adding history to in-memory storage: {mem_history_error}"
                )

            # Add history to MongoDB storage directly
            try:
                # Get current shadow from MongoDB
                mongo_shadow = await mongo_storage.get_shadow(heater_id)

                # Add or update history field
                if "history" not in mongo_shadow:
                    mongo_shadow["history"] = []

                # Append new history data and save
                mongo_shadow["history"] = historical_readings
                await mongo_storage.save_shadow(heater_id, mongo_shadow)

                logger.info(
                    f"Added {len(historical_readings)} history entries to MongoDB for {heater_id}"
                )
            except Exception as mongo_history_error:
                logger.error(f"Error adding history to MongoDB: {mongo_history_error}")

            logger.info(f"Successfully generated history for {heater_id}")
        except Exception as history_error:
            logger.error(f"Error generating history: {history_error}")


async def generate_shadow_history_data(heater_id, days=7):
    """
    Generate shadow history entries for a water heater for the past week.

    Args:
        shadow_service: Instance of DeviceShadowService
        heater_id: ID of the water heater
        days: Number of days of history to generate (default: 7)
    """
    logger.info(f"Generating shadow history for {heater_id} for the past {days} days")

    # Use fixed base values rather than trying to retrieve from shadow
    base_temp = 120.0
    target_temp = 125.0
    base_pressure = 60.0
    base_flow = 3.2
    base_energy = 450.0

    current_time = datetime.now()

    # Create a batch of historical readings to store
    historical_readings = []

    # Generate history entries (one every 30 minutes for the past week)
    intervals = days * 24 * 2  # Every 30 minutes
    for i in range(intervals, 0, -1):
        # Calculate timestamp (going backwards from now)
        point_time = current_time - timedelta(minutes=i * 30)

        # Add daily cycle variation
        hour = point_time.hour
        time_factor = ((hour - 12) / 12) * 3  # ±3 degree variation by time of day

        # Add some randomness
        random_temp = random.uniform(-1.0, 1.0)
        random_pressure = random.uniform(-2.0, 2.0)
        random_flow = random.uniform(-0.2, 0.2)
        random_energy = random.uniform(-10.0, 10.0)

        # Calculate metrics with variation
        temp = round(base_temp + time_factor + random_temp, 1)
        pressure = round(base_pressure + random_pressure, 1)
        flow = round(max(0, base_flow + random_flow), 2)
        energy = round(
            base_energy + i / 48 * 5 + random_energy, 2
        )  # Increase over time

        # Keep temperature within reasonable range
        temp = max(min(temp, target_temp + 5), target_temp - 10)

        # Determine heater status based on temperature
        heater_status = "HEATING" if temp < target_temp - 1.0 else "STANDBY"

        # Create history entry
        entry = {
            "timestamp": point_time.isoformat() + "Z",
            "metrics": {
                "temperature": temp,
                "pressure": pressure,
                "flow_rate": flow,
                "energy_usage": energy,
                "heater_status": heater_status,
            },
        }

        historical_readings.append(entry)

    # Return the generated history entries
    return historical_readings


if __name__ == "__main__":
    asyncio.run(fix_water_heater_shadow())
