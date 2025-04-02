"""
Script to directly insert a test alert event in the database.
Following TDD principles - adapting code to match expected behavior.
"""
import logging
import sqlite3
import uuid
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = "data/iotsphere.db"


def main():
    logger.info("Starting alert event creation...")
    conn = None
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        # Enable dictionary access to rows
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # First, find existing alert rules
        cursor.execute("SELECT * FROM alert_rules LIMIT 1")
        rule = cursor.fetchone()

        if not rule:
            # If no rule exists, create one
            logger.info("No existing alert rule found. Creating a new one...")
            rule_id = str(uuid.uuid4())
            model_id = "water-heater-model"

            # Check schema to determine correct columns
            cursor.execute("PRAGMA table_info(alert_rules)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            # Determine which columns to use
            base_columns = ["id", "model_id", "metric_name", "threshold", "severity"]
            values = [rule_id, model_id, "energy_consumption", 0.85, "WARNING"]

            # Check for optional columns
            if "operator" in column_names:
                base_columns.append("operator")
                values.append(">")
            if "condition" in column_names:
                base_columns.append("condition")
                values.append("ABOVE")
            if "active" in column_names:
                base_columns.append("active")
                values.append(1)
            elif "is_active" in column_names:
                base_columns.append("is_active")
                values.append(1)

            # Create rule
            placeholders = ",".join(["?"] * len(values))
            cols = ",".join(base_columns)
            cursor.execute(
                f"INSERT INTO alert_rules ({cols}) VALUES ({placeholders})", values
            )
            conn.commit()

            # Fetch the created rule
            cursor.execute("SELECT * FROM alert_rules WHERE id = ?", (rule_id,))
            rule = cursor.fetchone()
            logger.info(f"Created new rule: {rule_id}")
        else:
            logger.info(f"Found existing rule: {rule['id']}")

        # Now create an alert event for this rule
        event_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Create a metric value that would trigger the alert
        rule_id = rule["id"]
        model_id = rule["model_id"]
        metric_name = rule["metric_name"]
        metric_value = rule["threshold"] + 0.1  # Value that exceeds threshold
        severity = rule["severity"]

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
        logger.info(f"Successfully created alert event: {event_id}")

        # Verify alert was created
        cursor.execute("SELECT * FROM alert_events WHERE id = ?", (event_id,))
        result = cursor.fetchone()
        if result:
            logger.info(f"Verified alert in database: {result['id']}")
        else:
            logger.warning("Alert created but not found in database verification")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")


if __name__ == "__main__":
    main()
