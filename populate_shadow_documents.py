#!/usr/bin/env python3
"""
Shadow Document Population Script for IoTSphere
Following TDD principles - implements the GREEN phase to make tests pass
"""
import argparse
import asyncio
import json
import logging
import random
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import project modules
try:
    from src.services.device_shadow import DeviceShadowService
    from src.services.telemetry_service import TelemetryService, get_telemetry_service
except ImportError as e:
    logger.error(f"Could not import required modules: {str(e)}")
    logger.error("Make sure you're running this script from the project root directory")
    sys.exit(1)

# Test device IDs
TEST_DEVICES = [
    "wh-test-001",
    "wh-test-002",
    "wh-test-003",
    "wh-missing-shadow",  # This device will not get a shadow for testing error cases
]


async def populate_shadow_documents(devices: List[str], exclude: List[str] = None):
    """
    Populate shadow documents for test devices

    Args:
        devices: List of device IDs to populate shadows for
        exclude: List of device IDs to exclude (for testing error cases)
    """
    logger.info(f"Populating shadow documents for {len(devices)} devices")

    # Create service instances
    shadow_service = DeviceShadowService()
    telemetry_service = get_telemetry_service()

    # Get current timestamp
    now = datetime.utcnow()

    # Process each device
    for device_id in devices:
        # Skip excluded devices
        if exclude and device_id in exclude:
            logger.info(
                f"Skipping shadow creation for {device_id} (excluded for testing)"
            )
            continue

        # Generate random base temperature
        base_temp = random.uniform(50.0, 70.0)

        # Create shadow document with basic properties
        reported_state = {
            "temperature": round(base_temp, 1),
            "setpoint": round(base_temp + 5.0, 1),
            "mode": random.choice(["heating", "idle", "eco"]),
            "status": "online",
            "firmware_version": "1.2.3",
            "last_updated": now.isoformat(),
        }

        desired_state = {"setpoint": round(base_temp + 5.0, 1), "mode": "heating"}

        try:
            # Create or update shadow document
            logger.info(f"Creating shadow document for {device_id}")
            shadow = await shadow_service.create_device_shadow(
                device_id=device_id,
                reported_state=reported_state,
                desired_state=desired_state,
            )
            logger.info(f"Successfully created shadow for {device_id}")

            # Generate and store historical telemetry data
            await generate_telemetry_history(
                device_id, telemetry_service, base_temp, days=7
            )

        except Exception as e:
            logger.error(f"Error creating shadow for {device_id}: {str(e)}")


async def generate_telemetry_history(
    device_id: str, telemetry_service: TelemetryService, base_temp: float, days: int = 7
):
    """
    Generate historical telemetry data for a device

    Args:
        device_id: Device ID to generate history for
        telemetry_service: Telemetry service instance
        base_temp: Base temperature to vary around
        days: Number of days of history to generate
    """
    logger.info(f"Generating {days} days of telemetry history for {device_id}")

    # Get current timestamp
    now = datetime.utcnow()

    # Generate data points at 30-minute intervals
    data_points = []

    # Create points from the past until now
    current_time = now - timedelta(days=days)
    while current_time < now:
        # Add random variation to temperature
        variation = random.uniform(-3.0, 3.0)
        temperature = round(base_temp + variation, 1)

        # Create telemetry data point
        data_point = {
            "device_id": device_id,
            "timestamp": current_time.isoformat(),
            "metric": "temperature",
            "value": temperature,
            "unit": "celsius",
        }

        # Process each telemetry data point individually
        try:
            await telemetry_service.process_telemetry_data(data_point)
            data_points.append(data_point)
        except Exception as e:
            logger.error(f"Error processing telemetry point: {str(e)}")

        # Increment time by 30 minutes
        current_time += timedelta(minutes=30)

    logger.info(
        f"Successfully generated {len(data_points)} telemetry points for {device_id}"
    )


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(
        description="Populate shadow documents for testing"
    )
    parser.add_argument(
        "--devices",
        nargs="+",
        default=TEST_DEVICES,
        help="List of device IDs to populate shadows for",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=["wh-missing-shadow"],
        help="List of device IDs to exclude (for testing error cases)",
    )

    args = parser.parse_args()

    # Run async tasks
    asyncio.run(populate_shadow_documents(args.devices, args.exclude))

    logger.info("Shadow document population completed")


if __name__ == "__main__":
    main()
