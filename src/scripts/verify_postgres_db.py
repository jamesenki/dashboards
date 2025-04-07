#!/usr/bin/env python
"""
PostgreSQL Database Schema Verification Script

This script connects to the PostgreSQL database and verifies the schema,
including the presence of required tables and their structure.

Usage:
    IOTSPHERE_ENV=development python src/scripts/verify_postgres_db.py
"""
import os
import sys
from pathlib import Path

# Add project root to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

import psycopg2

# Import database configuration
from src.db.config import db_settings

# Required tables
REQUIRED_TABLES = [
    "water_heaters",
    "water_heater_readings",
    "water_heater_diagnostic_codes",
    "water_heater_health_config",
    "water_heater_alert_rules",
]


def check_postgres_db():
    """Check PostgreSQL database schema and connectivity."""
    print(f"Checking PostgreSQL database...")

    # Get environment
    env = os.environ.get("IOTSPHERE_ENV", "development")
    print(f"Environment: {env}")

    # Display connection parameters
    print(f"PostgreSQL connection parameters:")
    print(f"  Host: {db_settings.DB_HOST}")
    print(f"  Port: {db_settings.DB_PORT}")
    print(f"  Database: {db_settings.DB_NAME}")
    print(f"  User: {db_settings.DB_USER}")

    try:
        # Connect to PostgreSQL
        connection = psycopg2.connect(
            host=db_settings.DB_HOST,
            port=db_settings.DB_PORT,
            database=db_settings.DB_NAME,
            user=db_settings.DB_USER,
            password=db_settings.DB_PASSWORD,
        )
        cursor = connection.cursor()
        print("Connected to PostgreSQL database successfully")

        # Check for required tables
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """
        )
        tables = [table[0] for table in cursor.fetchall()]
        print(f"Found {len(tables)} tables in database")

        # Verify required tables exist
        missing_tables = []
        for table in REQUIRED_TABLES:
            if table not in tables:
                missing_tables.append(table)
                print(f"❌ Missing required table: {table}")
            else:
                print(f"✓ Found table: {table}")

                # Check record count for each table
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  └─ {count} records")

                # Get column information
                cursor.execute(
                    f"""
                    SELECT column_name, data_type, character_maximum_length
                    FROM information_schema.columns
                    WHERE table_name = '{table}'
                """
                )
                columns = cursor.fetchall()
                print(f"  └─ {len(columns)} columns:")
                for col in columns:
                    col_name, data_type, max_length = col
                    type_info = f"{data_type}"
                    if max_length:
                        type_info += f"({max_length})"
                    print(f"     └─ {col_name}: {type_info}")

        if missing_tables:
            print("\n❌ Database schema verification failed!")
            print(
                f"Missing {len(missing_tables)} required tables: {', '.join(missing_tables)}"
            )
            print("You may need to create these tables or run database migrations")
            return False
        else:
            print("\n✓ Database schema verification passed!")
            print("All required tables exist in the PostgreSQL database")
            return True

    except Exception as e:
        print(f"\n❌ Error connecting to PostgreSQL database: {e}")
        print("Make sure PostgreSQL is installed and running")
        print("Verify that the database and user exist with correct permissions")
        return False
    finally:
        if "connection" in locals():
            connection.close()
            print("Connection closed")


if __name__ == "__main__":
    success = check_postgres_db()
    sys.exit(0 if success else 1)
