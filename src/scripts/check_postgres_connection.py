#!/usr/bin/env python3
"""
Check PostgreSQL connection with retry logic.

This script attempts to connect to the PostgreSQL database with retries,
to ensure the database is up and running before we proceed with validation.
"""
import asyncio
import logging
import os
import sys
import time
from typing import Dict, Optional

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import environment loader after path setup
from src.utils.env_loader import get_db_credentials

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get PostgreSQL connection settings from environment variables
DEFAULT_PG_CONFIG = get_db_credentials()


async def check_postgres_connection(
    config: Dict[str, str] = DEFAULT_PG_CONFIG,
    max_retries: int = 5,
    retry_delay: int = 2,
) -> bool:
    """
    Check PostgreSQL connection with retry logic.

    Args:
        config: PostgreSQL connection configuration
        max_retries: Maximum number of connection attempts
        retry_delay: Delay in seconds between retries

    Returns:
        True if connection successful, False otherwise
    """
    try:
        import asyncpg

        logger.info(
            f"Checking PostgreSQL connection to {config['host']}:{config['port']}/{config['database']}..."
        )

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Connection attempt {attempt}/{max_retries}...")

                # Attempt to connect to PostgreSQL
                connection = await asyncpg.connect(
                    host=config["host"],
                    port=config["port"],
                    database=config["database"],
                    user=config["user"],
                    password=config["password"],
                )

                # Execute a simple query to verify connection
                version = await connection.fetchval("SELECT version()")
                logger.info(f"✅ Successfully connected to PostgreSQL: {version}")

                # Check water_heaters table existence
                table_exists = await connection.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'water_heaters')"
                )
                if table_exists:
                    logger.info("✅ water_heaters table exists")

                    # Check count of water heaters
                    count = await connection.fetchval(
                        "SELECT COUNT(*) FROM water_heaters"
                    )
                    logger.info(f"✅ Found {count} water heaters in database")

                    # Check for Rheem water heaters
                    rheem_count = await connection.fetchval(
                        "SELECT COUNT(*) FROM water_heaters WHERE manufacturer = 'Rheem'"
                    )
                    logger.info(f"✅ Found {rheem_count} Rheem water heaters")

                    # Check for specific water heater types
                    types = await connection.fetch(
                        "SELECT type, COUNT(*) FROM water_heaters WHERE manufacturer = 'Rheem' GROUP BY type"
                    )
                    type_counts = {row["type"]: row["count"] for row in types}
                    logger.info(f"✅ Water heater types for Rheem: {type_counts}")

                    # Verify all required types exist
                    required_types = ["Tank", "Tankless", "Hybrid"]
                    missing_types = [t for t in required_types if t not in type_counts]

                    if missing_types:
                        logger.warning(
                            f"⚠️ Missing required Rheem water heater types: {missing_types}"
                        )
                    else:
                        logger.info("✅ All required Rheem water heater types present")

                else:
                    logger.error("❌ water_heaters table does not exist!")

                # Close connection
                await connection.close()
                return True

            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Connection attempt {attempt} failed: {str(e)}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(
                        f"❌ Failed to connect after {max_retries} attempts: {str(e)}"
                    )
                    return False

    except ImportError:
        logger.error(
            "❌ asyncpg package not installed. Please install it with: pip install asyncpg"
        )
        return False

    return False


async def main():
    """Run the script."""
    # Get PostgreSQL connection settings from environment or use defaults
    config = {
        "host": os.environ.get("DB_HOST", DEFAULT_PG_CONFIG["host"]),
        "port": int(os.environ.get("DB_PORT", DEFAULT_PG_CONFIG["port"])),
        "database": os.environ.get("DB_NAME", DEFAULT_PG_CONFIG["database"]),
        "user": os.environ.get("DB_USER", DEFAULT_PG_CONFIG["user"]),
        "password": os.environ.get("DB_PASSWORD", DEFAULT_PG_CONFIG["password"]),
    }

    # Check connection
    success = await check_postgres_connection(config, max_retries=5, retry_delay=2)

    if success:
        logger.info("✅ PostgreSQL connection check successful")
        return 0
    else:
        logger.error("❌ PostgreSQL connection check failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
