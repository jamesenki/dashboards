#!/usr/bin/env python3
"""
Register mock devices for testing the IoTSphere platform.

This script will:
1. Create sample device manifests for different device types
2. Register the devices using the ManifestProcessor service
3. Generate sample shadow documents with initial state
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path so we can import modules
project_root = Path(__file__).parent.parent.absolute()
sys.path.append(str(project_root))

from src.infrastructure.device_shadow.storage_factory import (
    create_shadow_storage_provider,
)
from src.models.device import DeviceStatus, DeviceType
from src.services.device_shadow import DeviceShadowService
from src.services.manifest_processor import ManifestProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Sample device manifests
WATER_HEATER_MANIFEST = {
    "device_id": "wh-001",
    "name": "Master Bathroom Water Heater",
    "manufacturer": "EcoTemp",
    "model": "Pro X7500",
    "device_type": DeviceType.WATER_HEATER.value,
    "capabilities": {
        "temperature": {"min": 40, "max": 180, "unit": "F", "read_only": True},
        "target_temperature": {
            "min": 80,
            "max": 140,
            "unit": "F",
            "default": 120,
            "read_only": False,
        },
        "mode": {
            "options": ["NORMAL", "ECO", "VACATION", "HIGH_DEMAND"],
            "default": "NORMAL",
            "read_only": False,
        },
        "status": {
            "options": ["ONLINE", "OFFLINE", "MAINTENANCE", "ERROR"],
            "default": "ONLINE",
            "read_only": True,
        },
        "heater_status": {
            "options": ["HEATING", "STANDBY", "OFF"],
            "default": "STANDBY",
            "read_only": True,
        },
    },
    "firmware": {"version": "3.1.4", "last_updated": "2025-01-15T00:00:00Z"},
    "location": {"room": "Master Bathroom", "floor": 2},
}

WATER_HEATER_MANIFEST_2 = {
    "device_id": "wh-002",
    "name": "Kitchen Water Heater",
    "manufacturer": "EcoTemp",
    "model": "Pro X7500",
    "device_type": DeviceType.WATER_HEATER.value,
    "capabilities": {
        "temperature": {"min": 40, "max": 180, "unit": "F", "read_only": True},
        "target_temperature": {
            "min": 80,
            "max": 140,
            "unit": "F",
            "default": 120,
            "read_only": False,
        },
        "pressure": {"min": 0, "max": 5, "unit": "bar", "read_only": True},
        "flow_rate": {"min": 0, "max": 20, "unit": "gpm", "read_only": True},
        "energy_usage": {"min": 0, "max": 10000, "unit": "W", "read_only": True},
        "mode": {
            "options": ["NORMAL", "ECO", "VACATION", "HIGH_DEMAND"],
            "default": "NORMAL",
            "read_only": False,
        },
        "status": {
            "options": ["ONLINE", "OFFLINE", "MAINTENANCE", "ERROR"],
            "default": "ONLINE",
            "read_only": True,
        },
        "heater_status": {
            "options": ["HEATING", "STANDBY", "OFF"],
            "default": "STANDBY",
            "read_only": True,
        },
    },
    "firmware": {"version": "3.1.4", "last_updated": "2025-01-15T00:00:00Z"},
    "location": {"room": "Kitchen", "floor": 1},
}


async def register_mock_devices():
    """Register mock devices and create shadow documents"""
    logger.info("Starting mock device registration")

    # Configure shadow storage
    if "SHADOW_STORAGE_TYPE" not in os.environ:
        os.environ["SHADOW_STORAGE_TYPE"] = "memory"
        logger.info("Using in-memory shadow storage for mock device registration")

    # Create storage provider and services
    storage_provider = await create_shadow_storage_provider()
    shadow_service = DeviceShadowService(storage_provider=storage_provider)
    manifest_processor = ManifestProcessor(shadow_service=shadow_service)

    # Register water heater
    logger.info(
        f"Registering water heater with ID: {WATER_HEATER_MANIFEST['device_id']}"
    )
    success = await manifest_processor.process_device_manifest(
        device_id=WATER_HEATER_MANIFEST["device_id"], manifest=WATER_HEATER_MANIFEST
    )

    if success:
        logger.info(
            f"Successfully registered water heater {WATER_HEATER_MANIFEST['device_id']}"
        )

        # Update with some initial state data
        await shadow_service.update_device_shadow(
            device_id=WATER_HEATER_MANIFEST["device_id"],
            reported_state={
                "temperature": 118,
                "status": DeviceStatus.ONLINE.value,
                "heater_status": "HEATING",
                "last_updated": datetime.utcnow().isoformat() + "Z",
            },
        )
    else:
        logger.error(
            f"Failed to register water heater {WATER_HEATER_MANIFEST['device_id']}"
        )

    # Register second water heater
    logger.info(
        f"Registering second water heater with ID: {WATER_HEATER_MANIFEST_2['device_id']}"
    )
    success = await manifest_processor.process_device_manifest(
        device_id=WATER_HEATER_MANIFEST_2["device_id"], manifest=WATER_HEATER_MANIFEST_2
    )

    if success:
        logger.info(
            f"Successfully registered water heater {WATER_HEATER_MANIFEST_2['device_id']}"
        )

        # Update with some initial state data
        await shadow_service.update_device_shadow(
            device_id=WATER_HEATER_MANIFEST_2["device_id"],
            reported_state={
                "temperature": 125,
                "pressure": 2.1,
                "flow_rate": 0.0,
                "energy_usage": 3800,
                "status": DeviceStatus.ONLINE.value,
                "heater_status": "STANDBY",
                "last_updated": datetime.utcnow().isoformat() + "Z",
            },
        )
    else:
        logger.error(
            f"Failed to register water heater {WATER_HEATER_MANIFEST_2['device_id']}"
        )

    logger.info("Mock device registration complete")

    # Print shadow documents for verification
    for device_id in [
        WATER_HEATER_MANIFEST["device_id"],
        WATER_HEATER_MANIFEST_2["device_id"],
    ]:
        shadow = await shadow_service.get_device_shadow(device_id)
        logger.info(f"Shadow document for {device_id}:\n{json.dumps(shadow, indent=2)}")


if __name__ == "__main__":
    asyncio.run(register_mock_devices())
