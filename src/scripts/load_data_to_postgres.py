#!/usr/bin/env python3
"""
Script to load generated dummy data into PostgreSQL database with TimescaleDB.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi.encoders import jsonable_encoder

from src.db.connection import get_db_session
from src.db.migration import initialize_db
from src.db.models import DeviceModel, ReadingModel
from src.models.device_reading import DeviceReading
from src.utils.dummy_data import dummy_data

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def ensure_datetime(value: Union[str, datetime, None]) -> Optional[datetime]:
    """Convert a string date to datetime if needed."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            logger.warning(f"Could not parse datetime from string: {value}")
            return None
    return None


def process_device_dict(device_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Process a device dictionary to ensure all values are of the correct type."""
    # Make a copy to avoid modifying the original
    processed = device_dict.copy()

    # Convert string timestamps to datetime objects
    if "last_seen" in processed and processed["last_seen"]:
        processed["last_seen"] = ensure_datetime(processed["last_seen"])

    # Convert created_at and updated_at if they exist
    if "created_at" in processed and processed["created_at"]:
        processed["created_at"] = ensure_datetime(processed["created_at"])
    if "updated_at" in processed and processed["updated_at"]:
        processed["updated_at"] = ensure_datetime(processed["updated_at"])

    return processed


async def load_devices():
    """Load devices from dummy data to PostgreSQL.

    This function checks if devices already exist in the database before inserting them,
    making it safe to run multiple times without causing duplicate key violations.
    """
    # First make sure we have a valid session
    session_generator = get_db_session()
    if not session_generator:
        logger.warning("Database session unavailable. Skipping data loading.")
        return

    async for session in session_generator:
        if not session:
            logger.warning("Database session is None. Skipping data loading.")
            return

        try:
            # First, get a list of existing device IDs to avoid duplicate insertions
            from sqlalchemy import select, text

            existing_devices_result = await session.execute(select(DeviceModel.id))
            existing_device_ids = set(
                row[0] for row in existing_devices_result.fetchall()
            )

            logger.info(
                f"Found {len(existing_device_ids)} existing devices in database"
            )
            # Load vending machines
            for vm_id, vm in dummy_data.vending_machines.items():
                logger.info(f"Loading vending machine {vm_id}")

                # Convert Pydantic model to dict
                vm_dict = jsonable_encoder(vm)

                # Process the device dict to ensure proper data types
                vm_dict = process_device_dict(vm_dict)

                # Extract readings for separate insertion
                readings = vm_dict.pop("readings", [])
                products = vm_dict.pop("products", [])

                # Move specific fields to properties JSON field
                properties = {
                    "model_number": vm_dict.pop("model_number", None),
                    "serial_number": vm_dict.pop("serial_number", None),
                    "machine_status": vm_dict.pop("machine_status", None),
                    "mode": vm_dict.pop("mode", None),
                    "temperature": vm_dict.pop("temperature", None),
                    "total_capacity": vm_dict.pop("total_capacity", None),
                    "cash_capacity": vm_dict.pop("cash_capacity", None),
                    "current_cash": vm_dict.pop("current_cash", None),
                    "location_business_name": vm_dict.pop(
                        "location_business_name", None
                    ),
                    "location_type": vm_dict.pop("location_type", None),
                    "sub_location": vm_dict.pop("sub_location", None),
                    "use_type": vm_dict.pop("use_type", None),
                    "usage_pattern": vm_dict.pop("usage_pattern", None),
                    "stock_level": vm_dict.pop("stock_level", None),
                    "maintenance_partner": vm_dict.pop("maintenance_partner", None),
                    "last_maintenance_date": vm_dict.pop("last_maintenance_date", None),
                    "next_maintenance_date": vm_dict.pop("next_maintenance_date", None),
                    "products": products,
                }

                # Check if this device already exists in the database
                if vm_id in existing_device_ids:
                    logger.info(
                        f"Device {vm_id} already exists, updating instead of inserting"
                    )
                    # Update existing device - convert properties dict to JSON string
                    device_update = {
                        "name": vm_dict.get("name", ""),
                        "status": vm_dict.get("status", "OFFLINE"),
                        "location": vm_dict.get("location", ""),
                        "last_seen": vm_dict.get("last_seen", datetime.utcnow()),
                        "properties": json.dumps(properties),
                    }

                    await session.execute(
                        text(
                            "UPDATE devices SET name = :name, status = :status, location = :location, "
                            "last_seen = :last_seen, properties = :properties WHERE id = :id"
                        ),
                        {"id": vm_id, **device_update},
                    )
                else:
                    # Create new device model
                    device = DeviceModel(
                        id=vm_id,
                        name=vm_dict.get("name", ""),
                        type="vending_machine",
                        status=vm_dict.get("status", "OFFLINE"),
                        location=vm_dict.get("location", ""),
                        last_seen=vm_dict.get("last_seen", datetime.utcnow()),
                        properties=properties,
                    )

                    # Add to session
                    session.add(device)
                    await session.flush()

                # Add readings
                for reading_data in readings:
                    metric_readings = {
                        "temperature": reading_data.get("temperature"),
                        "power_consumption": reading_data.get("power_consumption"),
                        "door_status": reading_data.get("door_status"),
                        "cash_level": reading_data.get("cash_level"),
                        "sales_count": reading_data.get("sales_count"),
                    }

                    # Create separate reading records for each metric
                    for metric_name, value in metric_readings.items():
                        if value is not None:
                            # Ensure timestamp is a datetime object
                            timestamp = reading_data.get("timestamp")
                            if isinstance(timestamp, str):
                                try:
                                    timestamp = datetime.fromisoformat(timestamp)
                                except ValueError:
                                    timestamp = datetime.utcnow()
                            elif not isinstance(timestamp, datetime):
                                timestamp = datetime.utcnow()

                            reading = ReadingModel(
                                device_id=vm_id,
                                timestamp=timestamp,
                                metric_name=metric_name,
                                value=value,
                            )
                            session.add(reading)

            # Load water heaters
            for heater_id, heater in dummy_data.water_heaters.items():
                logger.info(f"Loading water heater {heater_id}")

                # Convert Pydantic model to dict
                heater_dict = jsonable_encoder(heater)

                # Process the device dict to ensure proper data types
                heater_dict = process_device_dict(heater_dict)

                # Extract readings for separate insertion
                readings = heater_dict.pop("readings", [])

                # Move specific fields to properties JSON field
                properties = {
                    "model_number": heater_dict.pop("model_number", None),
                    "serial_number": heater_dict.pop("serial_number", None),
                    "temperature": heater_dict.pop("temperature", None),
                    "capacity": heater_dict.pop("capacity", None),
                    "mode": heater_dict.pop("mode", None),
                    "power_level": heater_dict.pop("power_level", None),
                    "energy_efficiency": heater_dict.pop("energy_efficiency", None),
                    "installation_date": heater_dict.pop("installation_date", None),
                    "last_maintenance": heater_dict.pop("last_maintenance", None),
                    "warranty_expiry": heater_dict.pop("warranty_expiry", None),
                }

                # Check if this device already exists in the database
                if heater_id in existing_device_ids:
                    logger.info(
                        f"Device {heater_id} already exists, updating instead of inserting"
                    )
                    # Update existing device - convert properties dict to JSON string
                    device_update = {
                        "name": heater_dict.get("name", ""),
                        "status": heater_dict.get("status", "OFFLINE"),
                        "location": heater_dict.get("location", ""),
                        "last_seen": heater_dict.get("last_seen", datetime.utcnow()),
                        "properties": json.dumps(properties),
                    }

                    await session.execute(
                        text(
                            "UPDATE devices SET name = :name, status = :status, location = :location, "
                            "last_seen = :last_seen, properties = :properties WHERE id = :id"
                        ),
                        {"id": heater_id, **device_update},
                    )
                else:
                    # Create new device model
                    device = DeviceModel(
                        id=heater_id,
                        name=heater_dict.get("name", ""),
                        type="water_heater",
                        status=heater_dict.get("status", "OFFLINE"),
                        location=heater_dict.get("location", ""),
                        last_seen=heater_dict.get("last_seen", datetime.utcnow()),
                        properties=properties,
                    )

                    # Add to session
                    session.add(device)
                    await session.flush()

                # Add readings
                for reading_data in readings:
                    metric_readings = {
                        "temperature": reading_data.get("temperature"),
                        "pressure": reading_data.get("pressure"),
                        "flow_rate": reading_data.get("flow_rate"),
                        "power_consumption": reading_data.get("power_consumption"),
                    }

                    # Create separate reading records for each metric
                    for metric_name, value in metric_readings.items():
                        if value is not None:
                            # Ensure timestamp is a datetime object
                            timestamp = reading_data.get("timestamp")
                            if isinstance(timestamp, str):
                                try:
                                    timestamp = datetime.fromisoformat(timestamp)
                                except ValueError:
                                    timestamp = datetime.utcnow()
                            elif not isinstance(timestamp, datetime):
                                timestamp = datetime.utcnow()

                            reading = ReadingModel(
                                device_id=heater_id,
                                timestamp=timestamp,
                                metric_name=metric_name,
                                value=value,
                            )
                            session.add(reading)

            # Commit all changes
            await session.commit()
            logger.info("Successfully loaded all devices and readings into PostgreSQL")

        except Exception as e:
            await session.rollback()
            logger.error(f"Error loading data: {e}")
            raise


async def main():
    """Main entry point for data loading."""
    try:
        # Initialize the database first
        logger.info("Initializing database schema...")
        await initialize_db()

        # Load the data
        logger.info("Loading dummy data into PostgreSQL...")
        await load_devices()

        logger.info("Data loading completed successfully.")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")


if __name__ == "__main__":
    asyncio.run(main())
