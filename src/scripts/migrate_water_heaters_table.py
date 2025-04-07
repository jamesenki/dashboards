#!/usr/bin/env python3
"""
Database migration script to add Rheem-specific fields to the water_heaters table.

Usage:
    IOTSPHERE_ENV=development python src/scripts/migrate_water_heaters_table.py
"""

import asyncio
import logging
import os
import sys

# Setup path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import asyncpg
from asyncpg import Connection, Pool

# Import environment loader for credentials
from src.utils.env_loader import get_db_credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get database connection parameters from environment variables
db_credentials = get_db_credentials()


async def migrate_water_heaters_table():
    """Add Rheem-specific columns to the water_heaters table."""
    pool = None
    try:
        # Get environment
        environment = os.environ.get("IOTSPHERE_ENV", "development")
        print(f"Configuring database for environment: {environment}")

        # Create a connection pool
        pool = await asyncpg.create_pool(
            host=db_credentials["host"],
            port=db_credentials["port"],
            database=db_credentials["database"],
            user=db_credentials["user"],
            password=db_credentials["password"],
            min_size=5,
            max_size=20,
        )
        logger.info("PostgreSQL connection pool created")

        # Perform the schema alterations
        async with pool.acquire() as conn:
            # Check if columns already exist
            exists_query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'water_heaters'
                AND column_name IN ('series', 'features', 'operation_modes')
            """
            existing_columns = await conn.fetch(exists_query)
            existing_column_names = [row["column_name"] for row in existing_columns]

            if "series" not in existing_column_names:
                logger.info("Adding 'series' column to water_heaters table")
                await conn.execute("ALTER TABLE water_heaters ADD COLUMN series TEXT")
            else:
                logger.info("'series' column already exists in water_heaters table")

            if "features" not in existing_column_names:
                logger.info("Adding 'features' column to water_heaters table")
                await conn.execute("ALTER TABLE water_heaters ADD COLUMN features TEXT")
            else:
                logger.info("'features' column already exists in water_heaters table")

            if "operation_modes" not in existing_column_names:
                logger.info("Adding 'operation_modes' column to water_heaters table")
                await conn.execute(
                    "ALTER TABLE water_heaters ADD COLUMN operation_modes TEXT"
                )
            else:
                logger.info(
                    "'operation_modes' column already exists in water_heaters table"
                )

            # Verify the table structure after changes
            table_schema = await conn.fetch(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'water_heaters'
                ORDER BY ordinal_position
            """
            )

            # Log the table structure
            logger.info("Updated water_heaters table schema:")
            for column in table_schema:
                logger.info(f"  {column['column_name']} ({column['data_type']})")

            logger.info("Database migration completed successfully")

    except Exception as e:
        logger.error(f"Error during database migration: {e}")
        import traceback

        logger.error(traceback.format_exc())
    finally:
        # Close the connection pool
        if pool:
            await pool.close()
            logger.info("Closed PostgreSQL connection pool")


async def main():
    """Main entry point"""
    await migrate_water_heaters_table()


if __name__ == "__main__":
    asyncio.run(main())
