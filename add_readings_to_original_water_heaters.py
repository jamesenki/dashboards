"""
Script to add readings with complete data (including pressure, energy usage,
and flow rate) to original water heaters in the database.

This ensures all water heaters show all relevant readings in the details view.
"""
import asyncio
import os
import random
import sqlite3
import sys
import uuid
from datetime import datetime, timedelta

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models.water_heater import WaterHeater, WaterHeaterReading
from src.repositories.water_heater_repository import SQLiteWaterHeaterRepository

# Set DATABASE_PATH environment variable to use a specific database
# Default is the development database
DATABASE_PATH = os.environ.get("DATABASE_PATH", "data/iotsphere.db")

# Create repository instance
repository = SQLiteWaterHeaterRepository(DATABASE_PATH)


async def get_original_water_heaters():
    """Get the original water heaters from the database."""
    # Get all water heaters
    water_heaters = await repository.get_water_heaters()

    # Filter for water heaters without complete readings
    water_heaters_needing_data = []

    for wh in water_heaters:
        has_complete_readings = False
        if wh.readings:
            for reading in wh.readings:
                if (
                    reading.pressure is not None
                    and reading.energy_usage is not None
                    and reading.flow_rate is not None
                ):
                    has_complete_readings = True
                    break

        if not has_complete_readings:
            water_heaters_needing_data.append(wh)

    return water_heaters_needing_data


async def add_readings(water_heaters):
    """Add readings with complete data to water heaters."""
    for water_heater in water_heaters:
        print(
            f"Adding readings to water heater: {water_heater.name} (ID: {water_heater.id})"
        )

        # Generate 24 hours of readings (one per hour)
        now = datetime.now()

        for i in range(24):
            # Create reading with randomized values
            timestamp = now - timedelta(hours=i)

            # Base temperature on current temperature with some variation
            base_temp = water_heater.current_temperature or 140.0
            temperature = round(base_temp + random.uniform(-5.0, 5.0), 1)

            # Add pressure, energy usage, and flow rate
            pressure = round(random.uniform(40.0, 60.0), 1)  # PSI
            energy_usage = round(random.uniform(1.0, 5.0), 2)  # kWh
            flow_rate = round(random.uniform(1.5, 3.0), 2)  # GPM

            reading = WaterHeaterReading(
                id=str(uuid.uuid4()),
                temperature=temperature,
                pressure=pressure,
                energy_usage=energy_usage,
                flow_rate=flow_rate,
                timestamp=timestamp,
            )

            # Add reading to the database
            await repository.add_reading(water_heater.id, reading)

        print(f"Added 24 readings to water heater: {water_heater.name}")


async def main():
    """Main function to add readings to original water heaters."""
    try:
        # Get water heaters needing complete readings
        water_heaters = await get_original_water_heaters()

        if not water_heaters:
            print("No water heaters found that need complete readings.")
            return

        print(f"Found {len(water_heaters)} water heaters that need complete readings.")

        # Add readings to water heaters
        await add_readings(water_heaters)

        print("Successfully added readings to all original water heaters.")

    except Exception as e:
        print(f"Error adding readings to water heaters: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
