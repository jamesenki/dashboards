#!/usr/bin/env python3
"""
Directly query the PostgreSQL database to check water heater types.

This script bypasses the application's ORM and model layer to directly
check the database values.
"""
import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import environment loader for credentials
from src.utils.env_loader import get_db_credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get database connection parameters from environment variables
db_credentials = get_db_credentials()
DB_HOST = db_credentials["host"]
DB_PORT = db_credentials["port"]
DB_NAME = db_credentials["database"]
DB_USER = db_credentials["user"]
DB_PASSWORD = db_credentials["password"]


async def check_database_directly():
    """Directly query the database to check water heater types."""
    try:
        # Import asyncpg here to avoid import errors if it's not installed
        import asyncpg

        # Connect to PostgreSQL
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )

        try:
            # Check if water_heaters table exists
            table_exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'water_heaters')"
            )

            if not table_exists:
                logger.error("water_heaters table does not exist in the database")
                return False

            logger.info("✅ water_heaters table exists")

            # Get total count of water heaters
            total_count = await conn.fetchval("SELECT COUNT(*) FROM water_heaters")
            logger.info(f"Total water heaters in database: {total_count}")

            # Check Rheem water heaters specifically
            rheem_count = await conn.fetchval(
                "SELECT COUNT(*) FROM water_heaters WHERE manufacturer = 'Rheem'"
            )
            logger.info(f"Rheem water heaters in database: {rheem_count}")

            # Check types distribution in the database
            logger.info("Type values in the database:")
            types = await conn.fetch(
                "SELECT type, COUNT(*) FROM water_heaters GROUP BY type"
            )
            for row in types:
                logger.info(f"  - {row['type']}: {row['count']}")

            # Get Rheem water heater types specifically
            logger.info("Rheem water heater types:")
            rheem_types = await conn.fetch(
                "SELECT type, COUNT(*) FROM water_heaters WHERE manufacturer = 'Rheem' GROUP BY type"
            )
            for row in rheem_types:
                logger.info(f"  - {row['type']}: {row['count']}")

            # Show actual data for a few Rheem water heaters
            logger.info("\nSample Rheem water heaters:")
            rheem_samples = await conn.fetch(
                "SELECT id, name, manufacturer, type, model, series FROM water_heaters WHERE manufacturer = 'Rheem' LIMIT 3"
            )
            for i, row in enumerate(rheem_samples, 1):
                logger.info(f"Sample {i}:")
                logger.info(f"  ID: {row['id']}")
                logger.info(f"  Name: {row['name']}")
                logger.info(f"  Type: {row['type']}")
                logger.info(f"  Model: {row['model']}")
                logger.info(f"  Series: {row['series']}")

            # Verify device_id column existence
            device_id_exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'water_heaters' AND column_name = 'device_id')"
            )

            if device_id_exists:
                logger.info("✅ device_id column exists in water_heaters table")
            else:
                logger.info("⚠️ device_id column does NOT exist in water_heaters table")
                logger.info(
                    "Using 'id' as the device identifier is the correct approach"
                )

            return True
        finally:
            await conn.close()

    except ImportError:
        logger.error(
            "asyncpg package is not installed. Install with: pip install asyncpg"
        )
        return False
    except Exception as e:
        logger.error(f"Error checking database: {str(e)}")
        return False


async def main():
    """Run direct database check."""
    logger.info("Starting direct database check...")

    success = await check_database_directly()

    if success:
        logger.info("\n✅ Direct database check completed successfully")
    else:
        logger.error("\n❌ Direct database check failed")

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
