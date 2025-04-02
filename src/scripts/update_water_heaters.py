#!/usr/bin/env python3
"""
Script to update existing water heaters with new fields and add more water heaters.

This script:
1. Updates existing water heaters to include heater_type, specification_link, and diagnostic_codes
2. Adds 5 more water heaters (mix of commercial and residential)
3. Adds diagnostic codes for all water heaters
"""
import asyncio
import json
import logging
import random
from datetime import datetime, timedelta

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, text

from src.db.connection import get_db_session
from src.db.migration import initialize_db
from src.db.models import DeviceModel, DiagnosticCodeModel
from src.models.device import DeviceStatus, DeviceType
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterDiagnosticCode,
    WaterHeaterMode,
    WaterHeaterStatus,
    WaterHeaterType,
)
from src.utils.dummy_data import (
    COMMERCIAL_DIAGNOSTIC_CODES,
    RESIDENTIAL_DIAGNOSTIC_CODES,
    generate_water_heaters,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def update_existing_water_heaters():
    """Update existing water heaters with heater_type, specification_link, and diagnostic_codes."""
    session_generator = get_db_session()
    if not session_generator:
        logger.warning("Database session unavailable.")
        return

    async for session in session_generator:
        if not session:
            logger.warning("Database session is None.")
            return

        try:
            # Find all existing water heaters
            query = select(DeviceModel).where(
                DeviceModel.type == DeviceType.WATER_HEATER
            )
            result = await session.execute(query)
            devices = result.scalars().all()

            logger.info(f"Found {len(devices)} existing water heaters to update")

            for device in devices:
                # Determine if it should be commercial or residential based on capacity
                properties = device.properties or {}
                capacity = properties.get("capacity")

                # Determine heater type based on capacity or random if capacity is not set
                is_commercial = False
                if capacity is not None:
                    is_commercial = (
                        float(capacity) >= 150
                    )  # Commercial if 150L or larger
                else:
                    is_commercial = (
                        random.random() < 0.3
                    )  # 30% chance of being commercial

                heater_type = (
                    WaterHeaterType.COMMERCIAL
                    if is_commercial
                    else WaterHeaterType.RESIDENTIAL
                )

                # Update properties with new fields
                properties["heater_type"] = heater_type
                properties["specification_link"] = (
                    "/docs/specifications/water_heaters/commercial.md"
                    if is_commercial
                    else "/docs/specifications/water_heaters/residential.md"
                )

                # Update the properties in the database
                device.properties = properties

                # Add diagnostic codes
                diagnostic_codes = []
                code_list = (
                    COMMERCIAL_DIAGNOSTIC_CODES
                    if is_commercial
                    else RESIDENTIAL_DIAGNOSTIC_CODES
                )
                selected_codes = random.sample(code_list, random.randint(0, 3))

                for code_info in selected_codes:
                    # 70% of codes are active, 30% resolved
                    active = random.random() < 0.7

                    timestamp = datetime.now() - timedelta(days=random.randint(0, 7))

                    diagnostic = DiagnosticCodeModel(
                        device_id=device.id,
                        code=code_info["code"],
                        description=code_info["description"],
                        severity=code_info["severity"],
                        timestamp=timestamp,
                        active=active,
                    )
                    session.add(diagnostic)
                    diagnostic_codes.append(diagnostic)

                logger.info(
                    f"Updated water heater {device.id} with type {heater_type} and {len(diagnostic_codes)} diagnostic codes"
                )

            await session.commit()
            logger.info("All existing water heaters updated successfully")

        except Exception as e:
            logger.error(f"Error updating existing water heaters: {e}")
            await session.rollback()
            raise


async def add_new_water_heaters():
    """Add 5 more water heaters (mix of commercial and residential)."""
    session_generator = get_db_session()
    if not session_generator:
        logger.warning("Database session unavailable.")
        return

    async for session in session_generator:
        if not session:
            logger.warning("Database session is None.")
            return

        try:
            # Generate 5 new water heaters
            new_heaters = generate_water_heaters(count=5)
            logger.info(f"Generated {len(new_heaters)} new water heaters")

            for heater in new_heaters:
                # Extract data from the Pydantic model without using jsonable_encoder
                # This prevents datetime objects from being converted to strings
                heater_dict = {
                    "id": heater.id,
                    "name": heater.name,
                    "type": heater.type,
                    "status": heater.status,
                    "location": heater.location,
                    "last_seen": heater.last_seen,  # Keep as datetime object
                }

                # Extract fields that need special handling
                readings = heater.readings if hasattr(heater, "readings") else []
                diagnostic_codes = (
                    heater.diagnostic_codes
                    if hasattr(heater, "diagnostic_codes")
                    else []
                )

                # Create properties dict with properly serialized enum values
                properties = {
                    "target_temperature": heater.target_temperature,
                    "current_temperature": heater.current_temperature,
                    "min_temperature": heater.min_temperature,
                    "max_temperature": heater.max_temperature,
                    "mode": heater.mode.value
                    if hasattr(heater.mode, "value")
                    else heater.mode,
                    "heater_status": heater.heater_status.value
                    if hasattr(heater.heater_status, "value")
                    else heater.heater_status,
                    "heater_type": heater.heater_type.value
                    if hasattr(heater.heater_type, "value")
                    else heater.heater_type,
                    "specification_link": heater.specification_link,
                    "capacity": heater.capacity,
                    "efficiency_rating": heater.efficiency_rating,
                }

                # Create the device in the database
                db_device = DeviceModel(
                    id=heater_dict["id"],
                    name=heater_dict["name"],
                    type=heater_dict["type"],
                    status=heater_dict["status"],
                    location=heater_dict.get("location"),
                    last_seen=heater_dict.get("last_seen"),
                    properties=properties,
                )
                session.add(db_device)

                # Add diagnostic codes using the Pydantic objects directly
                for dc in diagnostic_codes:
                    db_diagnostic = DiagnosticCodeModel(
                        device_id=heater.id,
                        code=dc.code,
                        description=dc.description,
                        severity=dc.severity,
                        timestamp=dc.timestamp,  # Keep as datetime object
                        active=dc.active,
                        additional_info=dc.additional_info
                        if hasattr(dc, "additional_info")
                        else None,
                    )
                    session.add(db_diagnostic)

                logger.info(
                    f"Added new water heater {heater.id} of type {heater.heater_type}"
                )

            await session.commit()
            logger.info("All new water heaters added successfully")

        except Exception as e:
            logger.error(f"Error adding new water heaters: {e}")
            await session.rollback()
            raise


async def main():
    """Main entry point for the script."""
    logger.info("Starting water heater update script")

    # First initialize the database to ensure all tables exist
    await initialize_db()

    # Update existing water heaters
    await update_existing_water_heaters()

    # Add new water heaters
    await add_new_water_heaters()

    logger.info("Water heater update script completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
