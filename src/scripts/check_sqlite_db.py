"""
Direct SQLite Database Verification

This script directly connects to the SQLite database and verifies:
1. If the database file exists
2. What tables are present
3. The structure of water heater related tables
4. The count of records in each table

This bypasses the async SQLAlchemy layer to provide direct diagnostic information.
"""
import os
import sqlite3
import sys
from pathlib import Path

# Add the project root to the Python path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, repo_root)

# Expected tables for water heater functionality
EXPECTED_TABLES = [
    "water_heaters",
    "water_heater_readings",
    "water_heater_diagnostic_codes",
    "water_heater_health_config",
    "water_heater_alert_rules",
]

# Model-related tables
MODEL_TABLES = [
    "models",
    "model_versions",
    "model_metrics",
    "model_health_reference",
]


def get_db_path():
    """Get the path to the SQLite database file.

    Check both possible locations:
    1. Default name in project root
    2. Custom path from environment variable
    """
    # Check for explicit DB path in environment
    db_path = os.environ.get("DB_PATH")
    if db_path and os.path.exists(db_path):
        return db_path

    # Try default locations
    possible_paths = [
        # Project root
        os.path.join(repo_root, "iotsphere.db"),
        # Data directory
        os.path.join(repo_root, "data", "iotsphere.db"),
        # In src directory
        os.path.join(repo_root, "src", "iotsphere.db"),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    # If not found, return the default path (which doesn't exist)
    return possible_paths[0]


def check_database():
    """Check the SQLite database structure and contents."""
    # Find database file
    db_path = get_db_path()
    print(f"Database path: {db_path}")

    # Check if database file exists
    if not os.path.exists(db_path):
        print(f"❌ ERROR: Database file does not exist: {db_path}")
        print("This explains why the system falls back to mock data!")
        return False

    # Get database file size
    db_size = os.path.getsize(db_path)
    print(f"Database file size: {db_size / 1024:.2f} KB")

    # Connect to database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        print(f"Found {len(tables)} tables in database: {', '.join(tables)}")

        # Check for expected tables
        missing_tables = set(EXPECTED_TABLES) - set(tables)
        if missing_tables:
            print(f"❌ MISSING TABLES: {', '.join(missing_tables)}")
            print("This will cause fallback to mock data for water heater operations!")
        else:
            print("✅ All required water heater tables exist")

        # Check model tables
        missing_model_tables = set(MODEL_TABLES) - set(tables)
        if missing_model_tables:
            print(f"❌ MISSING MODEL TABLES: {', '.join(missing_model_tables)}")
            print("This will cause fallback to mock data for model monitoring!")
        else:
            print("✅ All required model tables exist")

        # Check table contents
        print("\n--- Table Row Counts ---")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"Table {table}: {count} rows")

            # Check for empty tables
            if count == 0 and table in EXPECTED_TABLES:
                print(f"⚠️ WARNING: Table {table} is empty")

        # Specifically check water heaters table
        if "water_heaters" in tables:
            print("\n--- Water Heaters Data Sample ---")
            cursor.execute("PRAGMA table_info(water_heaters)")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"Columns in water_heaters: {', '.join(columns)}")

            cursor.execute("SELECT * FROM water_heaters LIMIT 5")
            rows = cursor.fetchall()
            if rows:
                print(f"Sample data: {len(rows)} rows")
                for i, row in enumerate(rows):
                    print(f"Row {i+1}: {row}")
            else:
                print("No data in water_heaters table")

        # Check relationships
        if all(table in tables for table in ["water_heaters", "water_heater_readings"]):
            print("\n--- Checking Relationships ---")
            # Join water_heaters and readings
            try:
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM water_heater_readings r
                    LEFT JOIN water_heaters h ON r.water_heater_id = h.id
                    WHERE h.id IS NULL
                """
                )
                orphan_count = cursor.fetchone()[0]
                if orphan_count > 0:
                    print(
                        f"⚠️ WARNING: Found {orphan_count} orphaned readings with no parent water heater"
                    )
                else:
                    print(
                        "✅ All water_heater_readings properly reference parent water heaters"
                    )
            except sqlite3.OperationalError as e:
                print(f"❌ ERROR checking relationships: {e}")
                print("This suggests a schema mismatch or missing foreign key")

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"❌ ERROR accessing database: {e}")
        return False


if __name__ == "__main__":
    # Set environment variables to use database
    os.environ["USE_MOCK_DATA"] = "False"

    # Run the database check
    success = check_database()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
