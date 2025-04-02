#!/usr/bin/env python
"""
Script to fix the models dropdown on the Alerts Tab.

This script creates a test alert for the Energy Consumption forecaster model
to ensure it appears in the dropdown.
"""
import logging
import sqlite3
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
DB_PATH = "data/iotsphere.db"
ENERGY_MODEL_ID = "energy-consumption-forecaster-1"
TEST_RULE_ID = f"test-rule-energy-{uuid.uuid4().hex[:8]}"
TEST_ALERT_ID = f"test-alert-energy-{uuid.uuid4().hex[:8]}"


def verify_model_exists():
    """Check if the Energy Consumption forecaster model exists in the database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Check if model exists in the models table
        cursor.execute("SELECT * FROM models WHERE id = ?", (ENERGY_MODEL_ID,))
        model = cursor.fetchone()

        if model:
            logger.info(f"✅ Energy Consumption forecaster model exists: {dict(model)}")
            return True
        else:
            logger.warning(
                f"❌ Energy Consumption forecaster model not found in database"
            )
            return False
    except Exception as e:
        logger.error(f"Error checking model: {str(e)}")
        return False
    finally:
        conn.close()


def create_energy_model():
    """Create the Energy Consumption forecaster model if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Insert model into the correct models table
        cursor.execute(
            """
            INSERT INTO models
            (id, name, description, created_at, updated_at, archived)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                ENERGY_MODEL_ID,
                "Energy Consumption Forecaster",
                "Predicts energy consumption patterns for water heaters",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                0,
            ),
        )

        conn.commit()
        logger.info(f"✅ Created Energy Consumption forecaster model: {ENERGY_MODEL_ID}")
        return True
    except sqlite3.IntegrityError:
        logger.warning(f"Model {ENERGY_MODEL_ID} already exists (integrity error)")
        return True
    except Exception as e:
        logger.error(f"Error creating model: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()


def create_alert_rule():
    """Create an alert rule for the Energy Consumption forecaster model"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if rule already exists
        cursor.execute(
            "SELECT id FROM alert_rules WHERE model_id = ? AND metric_name = 'prediction_accuracy'",
            (ENERGY_MODEL_ID,),
        )
        existing_rule = cursor.fetchone()

        if existing_rule:
            logger.info(f"Alert rule already exists for model {ENERGY_MODEL_ID}")
            return existing_rule[0]

        # Insert alert rule
        cursor.execute(
            """
            INSERT INTO alert_rules
            (id, model_id, metric_name, threshold, condition, severity, created_at, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                TEST_RULE_ID,
                ENERGY_MODEL_ID,
                "prediction_accuracy",
                0.75,
                "BELOW",
                "WARNING",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                1,
            ),
        )

        conn.commit()
        logger.info(f"✅ Created alert rule: {TEST_RULE_ID}")
        return TEST_RULE_ID
    except Exception as e:
        logger.error(f"Error creating alert rule: {str(e)}")
        conn.rollback()
        return None
    finally:
        conn.close()


def create_alert_event(rule_id):
    """Create an alert event for the Energy Consumption forecaster model"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Insert alert event
        cursor.execute(
            """
            INSERT INTO alert_events
            (id, rule_id, model_id, metric_name, metric_value, severity, created_at, resolved, resolved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                TEST_ALERT_ID,
                rule_id,
                ENERGY_MODEL_ID,
                "prediction_accuracy",
                0.72,
                "WARNING",
                datetime.now().isoformat(),
                0,
                None,
            ),
        )

        conn.commit()
        logger.info(f"✅ Created alert event: {TEST_ALERT_ID}")
        return True
    except Exception as e:
        logger.error(f"Error creating alert event: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()


def verify_alerts():
    """Verify that alerts exist for the Energy Consumption forecaster model"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Count alerts for the model
        cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM alert_events
            WHERE model_id = ?
            """,
            (ENERGY_MODEL_ID,),
        )
        result = cursor.fetchone()
        count = result["count"] if result else 0

        if count > 0:
            logger.info(
                f"✅ Found {count} alerts for Energy Consumption forecaster model"
            )

            # Get a sample alert
            cursor.execute(
                """
                SELECT * FROM alert_events
                WHERE model_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (ENERGY_MODEL_ID,),
            )
            sample = cursor.fetchone()
            if sample:
                logger.info(f"  Sample alert: {dict(sample)}")

            return True
        else:
            logger.warning(f"❌ No alerts found for Energy Consumption forecaster model")
            return False
    except Exception as e:
        logger.error(f"Error verifying alerts: {str(e)}")
        return False
    finally:
        conn.close()


def main():
    """Main function to fix the models dropdown"""
    logger.info("=== Starting fix for models dropdown on Alerts Tab ===")

    # Step 1: Verify the model exists
    if not verify_model_exists():
        # Create model if it doesn't exist
        if not create_energy_model():
            logger.error(
                "Failed to create Energy Consumption forecaster model. Aborting."
            )
            return

    # Step 2: Create an alert rule for the model
    rule_id = create_alert_rule()
    if not rule_id:
        logger.error("Failed to create alert rule. Aborting.")
        return

    # Step 3: Create an alert event for the model
    if not create_alert_event(rule_id):
        logger.error("Failed to create alert event. Aborting.")
        return

    # Step 4: Verify alerts exist for the model
    if verify_alerts():
        logger.info(
            "✅ Fix completed successfully! Energy Consumption forecaster should now appear in Alerts Tab."
        )
        logger.info("Please refresh the Alerts Tab in your browser to see the changes.")
    else:
        logger.error(
            "❌ Fix failed. Energy Consumption forecaster might not appear in Alerts Tab."
        )


if __name__ == "__main__":
    main()
