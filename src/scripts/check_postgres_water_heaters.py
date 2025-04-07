#!/usr/bin/env python
"""
Check PostgreSQL Water Heaters

Simple script to check how many water heaters are in the PostgreSQL database
and which manufacturers they belong to.
"""

import asyncio
import os

import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def count_water_heaters():
    """Count water heaters in PostgreSQL and group by manufacturer."""

    # Get connection details from environment
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "iotsphere")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")

    # Connect to PostgreSQL
    print(f"Connecting to PostgreSQL database at {db_host}:{db_port}...")
    conn = await asyncpg.connect(
        host=db_host, port=db_port, user=db_user, password=db_password, database=db_name
    )

    try:
        # Count all water heaters
        total = await conn.fetchval("SELECT COUNT(*) FROM water_heaters")
        print(f"Total water heaters in PostgreSQL: {total}")

        # Count by manufacturer
        result = await conn.fetch(
            "SELECT manufacturer, COUNT(*) FROM water_heaters GROUP BY manufacturer"
        )
        print("Manufacturers:")
        for row in result:
            print(f"  - {row['manufacturer']}: {row['count']}")

        # Show details for all water heaters
        print("\nWater Heater Details:")
        details = await conn.fetch("SELECT id, manufacturer, model FROM water_heaters")
        for i, row in enumerate(details, 1):
            print(
                f"{i}. ID: {row['id']}, Manufacturer: {row['manufacturer']}, Model: {row['model']}"
            )
    finally:
        # Close the connection
        await conn.close()


if __name__ == "__main__":
    asyncio.run(count_water_heaters())
