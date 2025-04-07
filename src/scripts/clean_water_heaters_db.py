#!/usr/bin/env python
"""
Clean Water Heaters Database

This script removes all non-Rheem water heaters from the PostgreSQL database
to ensure only the 6 expected water heaters are displayed in the UI.
"""

import asyncio
import os

import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def clean_water_heaters():
    """Remove all non-Rheem water heaters from the database."""

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
        # Start a transaction
        async with conn.transaction():
            # Count water heaters before cleanup
            total_before = await conn.fetchval("SELECT COUNT(*) FROM water_heaters")
            rheem_before = await conn.fetchval(
                "SELECT COUNT(*) FROM water_heaters WHERE manufacturer = 'Rheem'"
            )

            print(
                f"Before cleanup: {total_before} total water heaters, {rheem_before} Rheem water heaters"
            )

            # Get IDs of non-Rheem water heaters
            non_rheem_ids = await conn.fetch(
                "SELECT id FROM water_heaters WHERE manufacturer != 'Rheem' OR manufacturer IS NULL"
            )
            non_rheem_id_list = [row["id"] for row in non_rheem_ids]

            print(f"Found {len(non_rheem_id_list)} non-Rheem water heaters to remove:")
            for wh_id in non_rheem_id_list:
                print(f"  - {wh_id}")

            # Ask for confirmation before deleting
            confirm = input(
                "\nAre you sure you want to delete these water heaters? (yes/no): "
            )
            if confirm.lower() != "yes":
                print("Operation cancelled.")
                return

            # Skip trying to delete from related tables and go directly to water heaters
            # Database schema may be simpler than we expected
            print("Skipping related tables and deleting water heaters directly...")

            # Finally, delete the water heaters
            deleted = await conn.execute(
                "DELETE FROM water_heaters WHERE id = ANY($1::text[])",
                non_rheem_id_list,
            )
            print(f"Deleted water heaters: {deleted}")

            # Verify the results
            total_after = await conn.fetchval("SELECT COUNT(*) FROM water_heaters")
            rheem_after = await conn.fetchval(
                "SELECT COUNT(*) FROM water_heaters WHERE manufacturer = 'Rheem'"
            )

            print(
                f"\nAfter cleanup: {total_after} total water heaters, {rheem_after} Rheem water heaters"
            )

            # Show remaining water heaters
            print("\nRemaining Water Heaters:")
            remaining = await conn.fetch(
                "SELECT id, manufacturer, model FROM water_heaters"
            )
            for i, row in enumerate(remaining, 1):
                print(
                    f"{i}. ID: {row['id']}, Manufacturer: {row['manufacturer']}, Model: {row['model']}"
                )
    finally:
        # Close the connection
        await conn.close()


if __name__ == "__main__":
    asyncio.run(clean_water_heaters())
