"""
Database initialization script for IoTSphere.

This script initializes the SQLite database and populates it with test data.
"""
import logging
import os
from pathlib import Path

from src.db.real_database import SQLiteDatabase
from src.db.schema_migration import force_reset_schema

logger = logging.getLogger(__name__)


def initialize_database(
    db_path=None, in_memory=False, populate=True, force_reset=False
):
    """
    Initialize the database with schema and optionally populate with test data.

    Args:
        db_path: Path to the database file (will be created if it doesn't exist)
        in_memory: If True, create an in-memory database instead of a file
        populate: If True, populate with test data
        force_reset: If True, force reset schema tables to resolve any issues

    Returns:
        Database instance
    """
    if in_memory:
        logger.info("Initializing in-memory SQLite database")
        connection_string = ":memory:"
    elif db_path:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        logger.info(f"Initializing SQLite database at {db_path}")
        connection_string = db_path
    else:
        # Default to a file in the data directory
        data_dir = Path(__file__).parent.parent.parent / "data"
        os.makedirs(data_dir, exist_ok=True)
        db_path = data_dir / "iotsphere.db"
        logger.info(f"Initializing SQLite database at {db_path}")
        connection_string = str(db_path)

    # Create database instance
    db = SQLiteDatabase(connection_string)

    # Force reset schema if requested
    if force_reset:
        logger.info("Forcing schema reset to ensure database integrity")
        force_reset_schema(db.connection, db.connection.cursor())

    # Populate with test data if requested
    if populate:
        db.populate_test_data()

    return db


# If run directly, initialize the database
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db = initialize_database()
    logger.info("Database initialization complete")
