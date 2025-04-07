"""
Script to verify water heater related tables in the database.
Checks if we have data in all the extended tables.
"""
import asyncio
import logging
import os
import sys

# Add the parent directory to the Python path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, repo_root)

from src.db.connection import get_db_session

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# These are the tables we want to check
WATER_HEATER_TABLES = [
    "water_heaters",
    "water_heater_readings",
    "water_heater_diagnostic_codes",
    "water_heater_health_config",
    "water_heater_alert_rules",
]


async def check_tables():
    """Check if the water heater related tables have data."""

    # Get a database session
    session_generator = get_db_session()

    if not session_generator:
        logger.error("Failed to get database session")
        return

    async for session in session_generator:
        try:
            # Connection needs to be awaited
            conn = await session.connection()

            # Check each table
            results = {}

            for table in WATER_HEATER_TABLES:
                try:
                    # Execute SQL to count rows in the table
                    result = await conn.execute(f"SELECT COUNT(*) FROM {table}")
                    count = await result.scalar()

                    # If we get here, the table exists
                    logger.info(f"Table {table} exists with {count} rows")
                    results[table] = count

                    # If the table has rows, get a sample
                    if count > 0:
                        sample = await conn.execute(f"SELECT * FROM {table} LIMIT 1")
                        row = await sample.fetchone()
                        if row:
                            columns = row.keys()
                            logger.info(
                                f"Sample columns in {table}: {', '.join(columns)}"
                            )

                except Exception as e:
                    logger.error(f"Error checking table {table}: {str(e)}")
                    results[table] = f"ERROR: {str(e)}"

            # Print summary
            logger.info("\nSummary of water heater tables:")
            for table, count in results.items():
                logger.info(f"{table}: {count} rows")

            # Check specific relationships
            # Get a sample water heater ID
            try:
                result = await conn.execute("SELECT id FROM water_heaters LIMIT 1")
                sample_id = await result.scalar()

                if sample_id:
                    logger.info(
                        f"\nChecking relationships for water heater ID: {sample_id}"
                    )

                    # Check for readings
                    result = await conn.execute(
                        f"SELECT COUNT(*) FROM water_heater_readings WHERE water_heater_id = '{sample_id}'"
                    )
                    count = await result.scalar()
                    logger.info(f"Readings for {sample_id}: {count}")

                    # Check for diagnostic codes
                    result = await conn.execute(
                        f"SELECT COUNT(*) FROM water_heater_diagnostic_codes WHERE water_heater_id = '{sample_id}'"
                    )
                    count = await result.scalar()
                    logger.info(f"Diagnostic codes for {sample_id}: {count}")

            except Exception as e:
                logger.error(f"Error checking relationships: {str(e)}")

        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(check_tables())
