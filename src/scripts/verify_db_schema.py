"""
Database Schema Verification Script

This script checks the database schema for completeness and integrity.
It verifies that all required tables exist and have the correct structure,
as well as checking foreign key relationships.

Usage:
    python verify_db_schema.py

"""
import asyncio
import logging
import os
import sys
from typing import Dict, List, Set, Tuple

from sqlalchemy import text

# Add the project root to the Python path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, repo_root)

from src.db.connection import get_db_session

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Define the expected tables and their primary keys
EXPECTED_TABLES = {
    "water_heaters": "id",
    "water_heater_readings": "id",
    "water_heater_diagnostic_codes": "id",
    "water_heater_health_config": "water_heater_id",
    "water_heater_alert_rules": "id",
}

# Define expected foreign key relationships
EXPECTED_RELATIONSHIPS = [
    ("water_heater_readings", "water_heater_id", "water_heaters", "id"),
    ("water_heater_diagnostic_codes", "water_heater_id", "water_heaters", "id"),
    ("water_heater_health_config", "water_heater_id", "water_heaters", "id"),
    ("water_heater_alert_rules", "water_heater_id", "water_heaters", "id"),
]

# Model related tables
MODEL_TABLES = ["models", "model_versions", "model_metrics", "model_health_reference"]


async def verify_db_schema():
    """Check the database schema for completeness and integrity."""
    logger.info("Verifying database schema...")

    # Get a database session
    session_generator = get_db_session()

    if not session_generator:
        logger.error("Failed to create database session")
        return False

    async for session in session_generator:
        try:
            # Get connection for raw SQL queries
            conn = await session.connection()

            # Get list of all tables in the database
            has_success = await check_tables_exist(conn)
            if not has_success:
                return False

            # Check relationships for water heater tables
            await check_relationships(conn)

            # Check model tables required for ModelMonitoringService
            await check_model_tables(conn)

            # Check row counts
            await check_row_counts(conn)

            logger.info("Schema verification complete.")
            return True

        except Exception as e:
            logger.error(f"Error verifying database schema: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            return False
        finally:
            await session.close()

    return False


async def check_tables_exist(conn) -> bool:
    """Check if all expected tables exist in the database."""
    logger.info("Checking if required tables exist...")

    # Get list of all tables
    try:
        # Detect database type from connection URL
        import os

        from src.db.config import db_settings, get_db_url

        conn_url = get_db_url()
        logger.info(f"Database connection URL: {conn_url}")
        logger.info(f"Database type from settings: {db_settings.DB_TYPE}")

        # Let's try directly with a raw query
        if db_settings.DB_TYPE == "postgres":
            # PostgreSQL query
            query = text(
                "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'"
            )
            result = await conn.execute(query)
            rows = await result.fetchall()
            existing_tables = {row[0] for row in rows}
            logger.info(f"Got tables using pg_catalog query: {existing_tables}")
        elif db_settings.DB_TYPE == "sqlite":
            # SQLite query
            query = text("SELECT name FROM sqlite_master WHERE type='table'")
            result = await conn.execute(query)
            rows = await result.fetchall()
            existing_tables = {row[0] for row in rows}
            logger.info(f"Got tables using sqlite_master query: {existing_tables}")
        else:
            logger.error(f"Unsupported database type: {db_settings.DB_TYPE}")
            return False

        logger.info(f"Found {len(existing_tables)} tables in database")
        logger.info(f"Tables: {', '.join(sorted(existing_tables))}")

        # Check if all expected tables exist
        missing_tables = set(EXPECTED_TABLES.keys()) - existing_tables

        if missing_tables:
            logger.error(f"Missing tables: {', '.join(missing_tables)}")
            logger.error(
                "Database schema is incomplete! This will cause fallback to mock data."
            )
            return False
        else:
            logger.info("All required water heater tables exist.")
            return True

    except Exception as e:
        logger.error(f"Error checking tables: {str(e)}")
        return False


async def check_relationships(conn):
    """Check foreign key relationships between tables."""
    logger.info("Checking table relationships...")

    for child_table, fk_column, parent_table, pk_column in EXPECTED_RELATIONSHIPS:
        try:
            # Check if foreign key exists by doing a join query
            query = f"""
            SELECT COUNT(*)
            FROM {child_table} c
            LEFT JOIN {parent_table} p ON c.{fk_column} = p.{pk_column}
            WHERE p.{pk_column} IS NULL AND c.{fk_column} IS NOT NULL
            """

            result = await conn.execute(query)
            orphan_count = await result.scalar()

            if orphan_count > 0:
                logger.warning(
                    f"Found {orphan_count} orphaned records in {child_table} "
                    f"(foreign key {fk_column} references non-existent {parent_table}.{pk_column})"
                )
            else:
                logger.info(
                    f"Relationship {child_table}.{fk_column} -> {parent_table}.{pk_column} is valid"
                )

        except Exception as e:
            logger.error(
                f"Error checking relationship {child_table}.{fk_column} -> {parent_table}.{pk_column}: {str(e)}"
            )


async def check_model_tables(conn):
    """Check if model-related tables required by ModelMonitoringService exist."""
    logger.info("Checking model tables required by ModelMonitoringService...")

    for table in MODEL_TABLES:
        try:
            # Check if table exists
            result = await conn.execute(f"SELECT 1 FROM {table} LIMIT 1")
            try:
                await result.fetchone()
                logger.info(f"Table {table} exists and is accessible")
            except Exception:
                logger.info(f"Table {table} exists but might be empty")

        except Exception as e:
            logger.error(f"Error accessing table {table}: {str(e)}")
            logger.error(
                f"Missing table {table} will cause ModelMonitoringService to fall back to mock data"
            )


async def check_row_counts(conn):
    """Check row counts for key tables."""
    logger.info("Checking row counts for key tables...")

    for table in list(EXPECTED_TABLES.keys()) + MODEL_TABLES:
        try:
            result = await conn.execute(f"SELECT COUNT(*) FROM {table}")
            count = await result.scalar()

            logger.info(f"Table {table} has {count} rows")

            if count == 0:
                logger.warning(
                    f"Table {table} is empty. This might cause fallback to mock data."
                )

        except Exception as e:
            logger.error(f"Error checking row count for {table}: {str(e)}")


if __name__ == "__main__":
    # Set environment variables to use database
    os.environ["USE_MOCK_DATA"] = "False"

    # Run the schema verification
    success = asyncio.run(verify_db_schema())

    # Exit with appropriate code
    sys.exit(0 if success else 1)
