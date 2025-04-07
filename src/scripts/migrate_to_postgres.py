#!/usr/bin/env python
"""
Migration Script: SQLite to PostgreSQL

This script copies data from the SQLite database to PostgreSQL.
It preserves all water heater data and related tables.

Usage:
    IOTSPHERE_ENV=development python src/scripts/migrate_to_postgres.py
"""
import os
import sys
import time
from pathlib import Path

# Add project root to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

# Set environment
os.environ["IOTSPHERE_ENV"] = os.environ.get("IOTSPHERE_ENV", "development")

import sqlite3

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Import after setting environment
from src.db.config import db_settings

# Tables to migrate
TABLES = [
    "water_heaters",
    "water_heater_readings",
    "water_heater_diagnostic_codes",
    "water_heater_health_config",
    "water_heater_alert_rules",
]


def get_sqlite_path():
    """Get path to SQLite database file."""
    return repo_root / "data" / "iotsphere.db"


def migrate_to_postgres():
    """Migrate data from SQLite to PostgreSQL."""
    print(f"\n📊 Starting migration from SQLite to PostgreSQL...")
    print(f"Environment: {os.environ.get('IOTSPHERE_ENV', 'development')}")

    # Check SQLite database
    sqlite_path = get_sqlite_path()
    if not sqlite_path.exists():
        print(f"❌ SQLite database not found at {sqlite_path}")
        return False

    print(f"✓ SQLite database found at: {sqlite_path}")

    # Get PostgreSQL connection parameters
    pg_host = db_settings.DB_HOST
    pg_port = db_settings.DB_PORT
    pg_database = db_settings.DB_NAME
    pg_user = db_settings.DB_USER
    pg_password = db_settings.DB_PASSWORD

    print(f"\n🔌 PostgreSQL connection parameters:")
    print(f"  Host: {pg_host}")
    print(f"  Port: {pg_port}")
    print(f"  Database: {pg_database}")
    print(f"  User: {pg_user}")

    try:
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(sqlite_path)
        print(f"✓ Connected to SQLite database")

        # Ensure PostgreSQL database exists
        temp_conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            user=pg_user,
            password=pg_password,
            database="postgres",  # Connect to default database to create our database
        )
        temp_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        temp_cursor = temp_conn.cursor()

        # Check if database exists
        temp_cursor.execute(
            f"SELECT 1 FROM pg_database WHERE datname = '{pg_database}'"
        )
        if not temp_cursor.fetchone():
            print(f"⚠️ Database '{pg_database}' does not exist, creating it...")
            temp_cursor.execute(f"CREATE DATABASE {pg_database}")
            print(f"✓ Created database '{pg_database}'")
        else:
            print(f"✓ Database '{pg_database}' already exists")

        temp_conn.close()

        # Connect to PostgreSQL
        pg_conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            database=pg_database,
            user=pg_user,
            password=pg_password,
        )
        pg_cursor = pg_conn.cursor()
        print(f"✓ Connected to PostgreSQL database")

        # For each table
        for table_name in TABLES:
            print(f"\n📋 Processing table: {table_name}")

            # Get table schema
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = sqlite_cursor.fetchall()

            if not columns:
                print(f"  ⚠️ Table {table_name} not found in SQLite, skipping")
                continue

            # Get column definitions
            column_defs = []
            column_names = []
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, is_pk = col
                column_names.append(col_name)

                # Map SQLite types to PostgreSQL types
                if col_type.upper() in ("INTEGER", "INT"):
                    pg_type = "INTEGER"
                elif col_type.upper() in ("REAL", "FLOAT", "DOUBLE"):
                    pg_type = "DOUBLE PRECISION"
                elif col_type.upper() in ("TEXT", "VARCHAR", "CHAR"):
                    pg_type = "TEXT"
                elif col_type.upper() == "BOOLEAN":
                    pg_type = "BOOLEAN"
                elif col_type.upper() == "BLOB":
                    pg_type = "BYTEA"
                elif col_type.upper() == "TIMESTAMP":
                    pg_type = "TIMESTAMP"
                else:
                    pg_type = "TEXT"  # Default to TEXT for unknown types

                # Add constraints
                constraints = []
                if is_pk:
                    constraints.append("PRIMARY KEY")
                if not_null:
                    constraints.append("NOT NULL")

                constraint_str = " ".join(constraints)
                column_defs.append(f"{col_name} {pg_type} {constraint_str}".strip())

            # Create table in PostgreSQL if it doesn't exist
            columns_sql = ", ".join(column_defs)
            create_table_sql = (
                f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql})"
            )

            try:
                pg_cursor.execute(create_table_sql)
                pg_conn.commit()
                print(f"  ✓ Created table {table_name} in PostgreSQL")
            except Exception as e:
                print(f"  ❌ Error creating table {table_name}: {e}")
                pg_conn.rollback()
                continue

            # Get data from SQLite
            sqlite_cursor.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            print(f"  ℹ️ Found {len(rows)} rows in SQLite table {table_name}")

            if not rows:
                print(f"  ⚠️ Table {table_name} is empty, skipping data migration")
                continue

            # Clear existing data in PostgreSQL table
            try:
                pg_cursor.execute(f"DELETE FROM {table_name}")
                pg_conn.commit()
                print(f"  ✓ Cleared existing data from PostgreSQL table {table_name}")
            except Exception as e:
                print(f"  ❌ Error clearing data from table {table_name}: {e}")
                pg_conn.rollback()

            # Insert data into PostgreSQL
            columns_str = ", ".join(column_names)
            placeholders = ", ".join(["%s"] * len(column_names))
            insert_sql = (
                f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            )

            try:
                pg_cursor.executemany(insert_sql, rows)
                pg_conn.commit()
                print(f"  ✓ Migrated {len(rows)} rows to PostgreSQL table {table_name}")
            except Exception as e:
                print(f"  ❌ Error inserting data into table {table_name}: {e}")
                print(f"    Error details: {str(e)}")
                pg_conn.rollback()

        print("\n✅ Migration completed!")
        return True

    except Exception as e:
        print(f"\n❌ Error during migration: {str(e)}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        # Close connections
        if "sqlite_conn" in locals():
            sqlite_conn.close()
        if "pg_conn" in locals():
            pg_conn.close()
        print("\n🔌 Database connections closed")


if __name__ == "__main__":
    start_time = time.time()
    success = migrate_to_postgres()
    end_time = time.time()

    # Print summary
    print(f"\n⏱️ Migration took {end_time - start_time:.2f} seconds")
    if success:
        print("✅ Migration completed successfully")
    else:
        print("❌ Migration failed")

    sys.exit(0 if success else 1)
