#!/usr/bin/env python
"""
Database schema reset script for IoTSphere.

This script resets the schema of the SQLite database to ensure it matches the
expected schema for our application and tests. It completely rebuilds tables
that have schema issues and migrates data where possible.

Following TDD principles, we adapt our implementation to match the expectations
defined in our tests.
"""
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reset_database():
    """Reset the database schema to match expectations in tests."""
    from src.db.initialize_db import initialize_database

    # Path to the main database
    data_dir = Path(__file__).parent / "data"
    db_path = data_dir / "iotsphere.db"

    if not db_path.exists():
        logger.info(f"Database file {db_path} does not exist. Creating new database.")
    else:
        logger.info(f"Resetting schema of existing database at {db_path}")
        # Backup the database before reset
        import shutil
        import time

        timestamp = int(time.time())
        backup_path = data_dir / f"iotsphere_backup_{timestamp}.db"
        shutil.copy2(db_path, backup_path)
        logger.info(f"Created backup at {backup_path}")

    # Initialize database with force_reset=True to ensure proper schema
    db = initialize_database(db_path=str(db_path), force_reset=True, populate=True)
    db.close()

    logger.info(f"Database schema reset complete for {db_path}")
    return True


if __name__ == "__main__":
    logger.info("Starting database schema reset...")

    try:
        success = reset_database()
        if success:
            logger.info("Database schema reset completed successfully.")
            sys.exit(0)
        else:
            logger.error("Database schema reset failed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error during database schema reset: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
