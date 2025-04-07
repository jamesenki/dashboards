#!/usr/bin/env python3
"""
Check the values in the 'type' column to see if they match what we expect for water heater types.
"""
import asyncio
import os
import sys

import asyncpg

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import environment loader for credentials
from src.utils.env_loader import get_db_credentials


async def check_type_values():
    # Get database credentials from environment variables
    db_credentials = get_db_credentials()

    # Connect to PostgreSQL
    conn = await asyncpg.connect(
        host=db_credentials["host"],
        port=db_credentials["port"],
        user=db_credentials["user"],
        password=db_credentials["password"],
        database=db_credentials["database"],
    )

    try:
        # Check type values for Rheem water heaters
        results = await conn.fetch(
            """
            SELECT id, name, manufacturer, type, model
            FROM water_heaters
            WHERE manufacturer = 'Rheem'
            LIMIT 10;
        """
        )

        if results:
            print("\nType values for Rheem water heaters:")
            for row in results:
                print(
                    f"ID: {row['id']}, Name: {row['name']}, Type: {row['type']}, Model: {row['model']}"
                )
        else:
            print("\nNo Rheem water heaters found in the database")

        # Check all possible type values in the database
        type_values = await conn.fetch(
            """
            SELECT DISTINCT type, manufacturer, COUNT(*) as count
            FROM water_heaters
            GROUP BY type, manufacturer
            ORDER BY manufacturer, type;
        """
        )

        if type_values:
            print("\nAll distinct 'type' values in the database:")
            for row in type_values:
                print(
                    f"Type: {row['type']}, Manufacturer: {row['manufacturer']}, Count: {row['count']}"
                )
        else:
            print("\nNo type values found in the database")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_type_values())
