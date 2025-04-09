#!/usr/bin/env python3
"""
Script to create shadow documents for specific water heaters with complete historical data.

This script ensures that water heaters with IDs 'wh-001' and 'wh-002' have
proper shadow documents with temperature history for chart display.
"""
import asyncio
import json
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

# Create 8 water heaters with consistent IDs
# This includes the wh-e0ae2f58 format IDs already in the system and adds the two from BDD tests
WATER_HEATER_IDS = [
    # BDD test water heaters
    "wh-001",
    "wh-002",
    # Existing water heaters with format wh-e0ae2f58
    "wh-e0ae2f58",
    "wh-e1ae2f59",
    "wh-e2ae2f60",
    "wh-e3ae2f61",
    "wh-e4ae2f62",
    "wh-e5ae2f63",
]


async def create_water_heater_shadows():
    """Create or update shadow documents for specific water heaters."""
    from src.services.asset_registry import AssetRegistryService
    from src.services.device_shadow import DeviceShadowService

    logger.info(f"Creating shadow documents for {len(WATER_HEATER_IDS)} water heaters")
    shadow_service = DeviceShadowService()
    registry_service = AssetRegistryService()

    for heater_id in WATER_HEATER_IDS:
        # 1. ENSURE WATER HEATER IS IN REGISTRY
        try:
            # Check if device is in registry
            device = await registry_service.get_device(heater_id)
            logger.info(f"Device {heater_id} already exists in registry")
        except Exception as e:
            logger.info(f"Adding device {heater_id} to asset registry")

            # Create device in asset registry
            device_data = {
                "device_id": heater_id,  # Changed from 'id' to 'device_id' to match AssetRegistryService expectations
                "name": f"Water Heater {heater_id.split('-')[1]}",
                "manufacturer": "AquaSmart",
                "brand": "AquaSmart",
                "model": "SmartTank Pro",
                "type": "water_heater",
                "status": "ONLINE",
                "location": f"Building {heater_id[-1].upper()}",
                "installation_date": datetime.now().isoformat(),
                "warranty_expiry": (
                    datetime.now() + timedelta(days=365 * 5)
                ).isoformat(),
                "capacity": random.choice([40, 50, 60, 75]),
                "efficiency_rating": random.uniform(0.85, 0.95),
                "heater_type": "Tank",
                "features": ["Smart Control", "Energy Efficient", "Remote Monitoring"],
            }

            try:
                await registry_service.register_device(device_data)
                logger.info(f"Added {heater_id} to asset registry")
            except Exception as reg_error:
                logger.error(f"Error adding {heater_id} to registry: {reg_error}")

        # 2. ENSURE SHADOW DOCUMENT EXISTS
        try:
            shadow = await shadow_service.get_device_shadow(heater_id)
            logger.info(f"Shadow document already exists for {heater_id}")
        except Exception as e:
            logger.info(f"Creating new shadow document for {heater_id}")

            # Create realistic random values
            base_temp = round(
                random.uniform(118.0, 123.0), 1
            )  # Around 120 with variation
            target_temp = round(
                random.uniform(122.0, 128.0), 1
            )  # Around 125 with variation
            base_pressure = round(
                random.uniform(55.0, 65.0), 1
            )  # 60 PSI with variation
            base_flow = round(random.uniform(2.8, 3.5), 2)  # 3.2 GPM with variation
            base_energy = round(
                random.uniform(420.0, 480.0), 1
            )  # 450 kWh with variation

            # Create initial shadow state
            initial_state = {
                "device_id": heater_id,
                "reported": {
                    "name": f"Water Heater {heater_id.split('-')[1]}",
                    "model": "SmartTank Pro",
                    "manufacturer": "AquaSmart",
                    "temperature": base_temp,
                    "target_temperature": target_temp,
                    "min_temperature": 40.0,
                    "max_temperature": 140.0,
                    "pressure": base_pressure,
                    "flow_rate": base_flow,
                    "energy_usage": base_energy,
                    "heater_status": "STANDBY",
                    "connection_status": "ONLINE",
                    "mode": "ECO",
                    "timestamp": datetime.now().isoformat() + "Z",
                },
                "desired": {"temperature": target_temp, "mode": "ECO"},
            }

            # Create the shadow document
            try:
                await shadow_service.create_device_shadow(heater_id, initial_state)
                logger.info(f"Created shadow for {heater_id}")
            except Exception as create_error:
                logger.error(f"Error creating shadow for {heater_id}: {create_error}")
                continue

        # 3. GENERATE HISTORY DATA
        # Always regenerate history to ensure we have enough data points
        logger.info(f"Generating history data for {heater_id}")
        await generate_shadow_history(shadow_service, heater_id, days=7)


async def generate_shadow_history(shadow_service, heater_id, days=7):
    """
    Generate shadow history entries for a water heater for the past week.

    Args:
        shadow_service: Instance of DeviceShadowService
        heater_id: ID of the water heater
        days: Number of days of history to generate (default: 7)
    """
    logger.info(f"Generating shadow history for {heater_id} for the past {days} days")

    # Get current shadow
    try:
        shadow = await shadow_service.get_device_shadow(heater_id)
    except Exception as e:
        logger.error(f"Error getting shadow for {heater_id}: {e}")
        return

    # Extract current state
    if hasattr(shadow, "reported"):
        current_state = shadow.reported
    elif isinstance(shadow, dict) and "reported" in shadow:
        current_state = shadow["reported"]
    else:
        logger.error(f"Shadow for {heater_id} has unexpected format")
        return

    # Get base values from current state
    base_temp = float(current_state.get("temperature", 120.0))
    target_temp = float(current_state.get("target_temperature", 125.0))
    base_pressure = float(current_state.get("pressure", 60.0))
    base_flow = float(current_state.get("flow_rate", 3.2))
    base_energy = float(current_state.get("energy_usage", 450.0))

    current_time = datetime.now()

    # Create a batch of historical readings to store and return
    historical_readings = []

    # Generate history entries (one every 2 hours for the past week)
    hours = days * 24
    for i in range(hours, 0, -2):
        # Calculate timestamp (going backwards from now)
        point_time = current_time - timedelta(hours=i)

        # Add daily cycle variation
        hour = point_time.hour
        time_factor = ((hour - 12) / 12) * 3  # ±3 degree variation by time of day

        # Add some randomness
        random_temp = random.uniform(-1.5, 1.5)
        random_pressure = random.uniform(-5.0, 5.0)
        random_flow = random.uniform(-0.5, 0.5)
        random_energy = random.uniform(-20.0, 20.0)

        # Calculate metrics with variation
        temp = round(base_temp + time_factor + random_temp, 1)
        pressure = round(base_pressure + random_pressure, 1)
        flow = round(max(0, base_flow + random_flow), 2)
        energy = round(
            base_energy + i / 24 * 10 + random_energy, 2
        )  # Increase over time

        # Keep temperature within reasonable range
        temp = max(min(temp, target_temp + 5), target_temp - 10)

        # Determine heater status based on temperature
        heater_status = "HEATING" if temp < target_temp - 1.0 else "STANDBY"

        # Create historical data point
        reported_state = {
            "temperature": temp,
            "pressure": pressure,
            "flow_rate": flow,
            "energy_usage": energy,
            "heater_status": heater_status,
            "timestamp": point_time.isoformat() + "Z",
        }

        # Add to batch of historical readings
        historical_readings.append(reported_state)

        # Update shadow with this historical data point
        try:
            await shadow_service.update_device_shadow(
                device_id=heater_id, reported_state=reported_state
            )
            logger.debug(f"Added history entry for {heater_id} at {point_time}")
        except Exception as e:
            logger.error(f"Error adding history for {heater_id} at {point_time}: {e}")
        # Now update the shadow document to include the historical readings
    try:
        # Get the current shadow again (it now has history through reported state updates)
        shadow = await shadow_service.get_device_shadow(heater_id)

        # Ensure the shadow has a readings array in both formats for maximum compatibility
        # First format: in the main shadow object
        if isinstance(shadow, dict):
            if "readings" not in shadow:
                shadow["readings"] = historical_readings
            else:
                # Clear existing readings and add the new ones to avoid duplicates
                shadow["readings"] = historical_readings

            # Second format: in the reported section (where the frontend often looks)
            if "reported" not in shadow:
                shadow["reported"] = {}

            shadow["reported"]["readings"] = historical_readings
            shadow["reported"]["has_history"] = True

            # Update the shadow with the readings arrays included in both locations
            await shadow_service.update_device_shadow(heater_id, shadow)
            logger.info(
                f"Updated shadow for {heater_id} with {len(historical_readings)} historical readings"
            )

            # Double check that the complete shadow is saved correctly
            verification = await shadow_service.get_device_shadow(heater_id)
            if "readings" in verification or (
                "reported" in verification and "readings" in verification["reported"]
            ):
                logger.info(f"Successfully verified history data for {heater_id}")
            else:
                logger.warning(
                    f"History data not found in shadow verification for {heater_id}"
                )
        else:
            logger.warning(
                f"Shadow for {heater_id} is not a dict, can't add readings array"
            )
    except Exception as history_error:
        logger.error(
            f"Error updating shadow with history for {heater_id}: {history_error}"
        )

    logger.info(f"Completed generating {days} days of history for {heater_id}")


if __name__ == "__main__":
    asyncio.run(create_water_heater_shadows())
