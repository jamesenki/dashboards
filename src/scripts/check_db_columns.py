#!/usr/bin/env python3
"""
Check database schema to find columns similar to water_heater_type.
"""
import asyncio
import os
import sys

import asyncpg

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import environment loader for credentials
from src.utils.env_loader import get_db_credentials


async def check_columns():
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
        # Get all columns from water_heaters table
        columns = await conn.fetch(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'water_heaters'
            ORDER BY ordinal_position;
        """
        )

        print("\nColumns in water_heaters table:")
        for col in columns:
            print(f"- {col['column_name']} ({col['data_type']})")

        # Check for columns that might be similar to water_heater_type
        type_like_columns = await conn.fetch(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'water_heaters'
            AND (
                column_name LIKE '%type%'
                OR column_name LIKE '%category%'
                OR column_name LIKE '%model%'
                OR column_name LIKE '%kind%'
            )
            ORDER BY column_name;
        """
        )

        if type_like_columns:
            print("\nColumns that might be similar to water_heater_type:")
            for col in type_like_columns:
                print(f"- {col['column_name']} ({col['data_type']})")
        else:
            print("\nNo columns found that might be similar to water_heater_type")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_columns())
