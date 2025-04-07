#!/usr/bin/env python
"""
Script to check AquaTherm water heaters in the database
"""
import asyncio
import os
import sys

# Add the parent directory to sys.path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.db.connection import get_db_session
from src.db.repository import DeviceRepository


async def check_aquatherm_heaters():
    """Check all AquaTherm water heaters in the database"""
    print("Checking AquaTherm water heaters in the database...")

    # Get database session
    session = await get_db_session()

    # If database not available, skip
    if not session:
        print("Database session is None. Cannot check water heaters.")
        return

    try:
        # Create repository
        repo = DeviceRepository(session)

        # Get all devices
        devices = await repo.get_all_devices()

        # Filter for AquaTherm water heaters
        aquatherm_heaters = [
            d for d in devices if getattr(d, "manufacturer", "") == "AquaTherm"
        ]

        print(f"Found {len(aquatherm_heaters)} AquaTherm water heaters:")

        # Count by type
        tank_count = 0
        hybrid_count = 0
        tankless_count = 0

        for heater in aquatherm_heaters:
            heater_type = getattr(heater, "heater_type", "Unknown")
            heater_id = getattr(heater, "id", "Unknown")
            print(f"ID: {heater_id}, Type: {heater_type}")

            if heater_type == "TANK":
                tank_count += 1
            elif heater_type == "HYBRID":
                hybrid_count += 1
            elif heater_type == "TANKLESS":
                tankless_count += 1

        print("\nSummary:")
        print(f"TANK water heaters: {tank_count}")
        print(f"HYBRID water heaters: {hybrid_count}")
        print(f"TANKLESS water heaters: {tankless_count}")

    except Exception as e:
        print(f"Error checking water heaters: {str(e)}")
    finally:
        # Close session
        if session:
            await session.close()


if __name__ == "__main__":
    asyncio.run(check_aquatherm_heaters())
