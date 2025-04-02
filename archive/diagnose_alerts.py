"""
Diagnostic script to trace alert flow from creation to display.
Following TDD principles - verifying each component works as expected.
"""
import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Set environment variable to ensure real data is used
os.environ["USE_MOCK_DATA"] = "False"

# Database path
DB_PATH = "data/iotsphere.db"


def inspect_database_schema():
    """Inspect database schema to understand table structure."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    logger.info("=== DATABASE TABLES ===")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        logger.info(f"Table: {table[0]}")
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        for col in columns:
            logger.info(f"  - {col[1]} ({col[2]})")

    conn.close()


def check_alert_rules():
    """Check existing alert rules in the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    logger.info("=== ALERT RULES ===")
    try:
        cursor.execute("SELECT * FROM alert_rules ORDER BY created_at DESC")
        rules = cursor.fetchall()

        if not rules:
            logger.warning("No alert rules found in database!")

        for rule in rules:
            rule_dict = dict(rule)
            logger.info(f"Rule: {json.dumps(rule_dict, default=str)}")

    except Exception as e:
        logger.error(f"Error checking alert rules: {str(e)}")
    finally:
        conn.close()


def check_alert_events():
    """Check existing alert events in the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    logger.info("=== ALERT EVENTS ===")
    try:
        cursor.execute("SELECT * FROM alert_events ORDER BY created_at DESC LIMIT 10")
        events = cursor.fetchall()

        if not events:
            logger.warning("No alert events found in database!")

        for event in events:
            event_dict = dict(event)
            logger.info(f"Event: {json.dumps(event_dict, default=str)}")

    except Exception as e:
        logger.error(f"Error checking alert events: {str(e)}")
    finally:
        conn.close()


def create_test_alert():
    """Create a test alert rule and event."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    logger.info("=== CREATING TEST ALERT ===")
    try:
        # Check if we have any existing rules
        cursor.execute("SELECT * FROM alert_rules LIMIT 1")
        rule = cursor.fetchone()

        if not rule:
            # Create a new rule
            logger.info("No rules found, creating a test rule...")
            rule_id = str(uuid.uuid4())
            model_id = "test-model"

            # Check schema to determine correct columns
            cursor.execute("PRAGMA table_info(alert_rules)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            # Determine which columns to use
            active_column = (
                "active"
                if "active" in column_names
                else "is_active"
                if "is_active" in column_names
                else None
            )
            operator_column = (
                "operator"
                if "operator" in column_names
                else "condition"
                if "condition" in column_names
                else None
            )

            # Build query
            base_columns = ["id", "model_id", "metric_name", "threshold", "severity"]
            values = [rule_id, model_id, "energy_consumption", 0.85, "WARNING"]

            # Add operator column if exists
            if operator_column:
                base_columns.append(operator_column)
                values.append(">")

            # Add active column if exists
            if active_column:
                base_columns.append(active_column)
                values.append(1)

            # Build and execute query
            cols = ",".join(base_columns)
            placeholders = ",".join(["?"] * len(values))
            cursor.execute(
                f"INSERT INTO alert_rules ({cols}) VALUES ({placeholders})", values
            )
            conn.commit()

            # Fetch the created rule
            cursor.execute("SELECT * FROM alert_rules WHERE id = ?", (rule_id,))
            rule = cursor.fetchone()
            logger.info(f"Created new rule: {rule_id}")
        else:
            logger.info(f"Using existing rule: {rule['id']}")

        # Create an alert event
        event_id = str(uuid.uuid4())
        rule_id = rule["id"]
        model_id = rule["model_id"]
        metric_name = rule["metric_name"]
        metric_value = rule["threshold"] + 0.1  # Value that exceeds threshold
        severity = rule["severity"]
        timestamp = datetime.now().isoformat()

        # Insert alert event
        cursor.execute(
            """
        INSERT INTO alert_events
            (id, rule_id, model_id, metric_name, metric_value, severity, created_at, resolved)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                event_id,
                rule_id,
                model_id,
                metric_name,
                metric_value,
                severity,
                timestamp,
                0,
            ),
        )

        conn.commit()
        logger.info(f"Created alert event: {event_id}")

        # Verify alert was created
        cursor.execute("SELECT * FROM alert_events WHERE id = ?", (event_id,))
        result = cursor.fetchone()
        if result:
            logger.info(f"Verified alert in database: {result['id']}")
        else:
            logger.warning("Alert created but not found in database verification")

    except Exception as e:
        logger.error(f"Error creating test alert: {str(e)}")
        conn.rollback()
    finally:
        conn.close()


def check_alerts_endpoint():
    """Check the /alerts endpoint response."""
    logger.info("=== TESTING /API/MONITORING/ALERTS ENDPOINT ===")
    logger.info("To test the API endpoint, run the following curl command:")
    logger.info("curl -X GET http://localhost:8006/api/monitoring/alerts")
    logger.info("Or open http://localhost:8006/api/monitoring/alerts in your browser")


def diagnose_frontend():
    """Instructions to diagnose frontend issues."""
    logger.info("=== FRONTEND DIAGNOSTICS ===")
    logger.info("To diagnose frontend issues:")
    logger.info("1. Open browser developer tools (F12)")
    logger.info("2. Go to Network tab")
    logger.info("3. Navigate to http://localhost:8006/monitoring/alerts")
    logger.info("4. Check the request to /api/monitoring/alerts")
    logger.info("5. Verify the response contains the expected data")
    logger.info("6. Check the browser console for any JavaScript errors")


if __name__ == "__main__":
    logger.info("Starting alert diagnosis...")
    inspect_database_schema()
    check_alert_rules()
    check_alert_events()
    create_test_alert()
    check_alert_rules()
    check_alert_events()
    check_alerts_endpoint()
    diagnose_frontend()
    logger.info("Diagnosis complete.")
