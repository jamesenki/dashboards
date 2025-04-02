"""
Script to fix missing pressure, energy usage, and flow rate readings
for the original water heaters in the database.

This fixes the issue where the original water heaters were missing these values.
"""
import os
import random
import sqlite3
import uuid
from datetime import datetime, timedelta

# Database path
DATABASE_PATH = "data/iotsphere.db"


def get_water_heaters_needing_readings():
    """Get water heaters that need complete readings."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    water_heaters = []

    try:
        # Get all water heaters
        cursor.execute("SELECT id, name, current_temperature FROM water_heaters")
        water_heaters = [dict(row) for row in cursor.fetchall()]

        # Check which water heaters need readings with pressure, energy_usage, and flow_rate
        for wh in water_heaters:
            cursor.execute(
                """
            SELECT COUNT(*) FROM water_heater_readings
            WHERE water_heater_id = ? AND pressure IS NOT NULL AND energy_usage IS NOT NULL AND flow_rate IS NOT NULL
            """,
                (wh["id"],),
            )

            count = cursor.fetchone()[0]
            wh["has_complete_readings"] = count > 0

    except Exception as e:
        print(f"Error getting water heaters: {str(e)}")
    finally:
        conn.close()

    # Filter for water heaters without complete readings
    return [wh for wh in water_heaters if not wh["has_complete_readings"]]


def add_readings_to_water_heaters(water_heaters):
    """Add readings with complete data to water heaters."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        for water_heater in water_heaters:
            print(
                f"Adding readings to water heater: {water_heater['name']} (ID: {water_heater['id']})"
            )

            # Generate 24 hours of readings (one per hour)
            now = datetime.now()

            for i in range(24):
                # Create reading with randomized values
                timestamp = now - timedelta(hours=i)

                # Base temperature on current temperature with some variation
                base_temp = water_heater["current_temperature"] or 140.0
                temperature = round(base_temp + random.uniform(-5.0, 5.0), 1)

                # Add pressure, energy usage, and flow rate
                pressure = round(random.uniform(40.0, 60.0), 1)  # PSI
                energy_usage = round(random.uniform(1.0, 5.0), 2)  # kWh
                flow_rate = round(random.uniform(1.5, 3.0), 2)  # GPM

                # Generate a unique ID for the reading
                reading_id = str(uuid.uuid4())

                # Insert the reading into the database
                cursor.execute(
                    """
                INSERT INTO water_heater_readings
                (id, water_heater_id, temperature, pressure, energy_usage, flow_rate, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        reading_id,
                        water_heater["id"],
                        temperature,
                        pressure,
                        energy_usage,
                        flow_rate,
                        timestamp.isoformat(),
                    ),
                )

            print(f"Added 24 readings to water heater: {water_heater['name']}")

        # Commit all changes
        conn.commit()
        print("Successfully added readings to all water heaters needing them.")

    except Exception as e:
        print(f"Error adding readings: {str(e)}")
        conn.rollback()
    finally:
        conn.close()


def verify_readings():
    """Verify that all water heaters have readings with complete data."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Get all water heaters
        cursor.execute("SELECT id, name FROM water_heaters")
        water_heaters = [dict(row) for row in cursor.fetchall()]

        for wh in water_heaters:
            # Get some sample readings
            cursor.execute(
                """
            SELECT id, temperature, pressure, energy_usage, flow_rate, timestamp
            FROM water_heater_readings
            WHERE water_heater_id = ?
            ORDER BY timestamp DESC LIMIT 3
            """,
                (wh["id"],),
            )

            readings = [dict(row) for row in cursor.fetchall()]

            print(f"\nWater Heater: {wh['name']} (ID: {wh['id']})")
            print(f"Number of readings found: {len(readings)}")

            if readings:
                print("Sample readings:")
                for reading in readings:
                    print(
                        f"  Temp: {reading['temperature']}, Pressure: {reading['pressure']}, "
                        + f"Energy: {reading['energy_usage']}, Flow: {reading['flow_rate']}"
                    )
    except Exception as e:
        print(f"Error verifying readings: {str(e)}")
    finally:
        conn.close()


def main():
    """Main function to add readings to water heaters."""
    try:
        # Get water heaters needing readings
        water_heaters = get_water_heaters_needing_readings()

        if not water_heaters:
            print("No water heaters found that need readings.")
            return

        print(f"Found {len(water_heaters)} water heaters that need readings.")

        # Add readings to water heaters
        add_readings_to_water_heaters(water_heaters)

        # Verify readings were added correctly
        verify_readings()

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
