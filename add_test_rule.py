"""
Script to add test alert rules to the database for testing the dashboard.
"""
import asyncio
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Make sure we're using real data, not mock
os.environ["USE_MOCK_DATA"] = "False"


async def main():
    # Import here to ensure environment vars are set first
    from src.db.adapters.sqlite_model_metrics import SQLiteModelMetricsRepository
    from src.db.real_database import SQLiteDatabase

    logger.info("=== Adding Test Alert Rules ===")

    # Initialize database
    db_path = "data/iotsphere.db"
    db = SQLiteDatabase(connection_string=db_path)
    logger.info(f"DB initialization complete: {db}")

    # Create repo
    repo = SQLiteModelMetricsRepository(db=db)

    try:
        # Add model if it doesn't exist
        model_id = "anomaly-detection-1"
        model_version = "0.9"

        # Example alert rule parameters
        rule_data = {
            "id": "testrule1",
            "model_id": model_id,
            "metric_name": "accuracy",
            "threshold": 0.9,
            "condition": "BELOW",  # This is 'condition' not 'operator'
            "severity": "WARNING"
            # created_at and active have defaults
        }

        # Add the rule
        await db.execute(
            """
            INSERT OR REPLACE INTO alert_rules
            (id, model_id, metric_name, threshold, condition, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                rule_data["id"],
                rule_data["model_id"],
                rule_data["metric_name"],
                rule_data["threshold"],
                rule_data["condition"],
                rule_data["severity"],
            ),
        )

        # Add a second rule
        rule_data2 = {
            "id": "testrule2",
            "model_id": model_id,
            "metric_name": "f1_score",
            "threshold": 0.85,
            "condition": "BELOW",  # This is 'condition' not 'operator'
            "severity": "CRITICAL"
            # created_at and active have defaults
        }

        # Add the second rule
        await db.execute(
            """
            INSERT OR REPLACE INTO alert_rules
            (id, model_id, metric_name, threshold, condition, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                rule_data2["id"],
                rule_data2["model_id"],
                rule_data2["metric_name"],
                rule_data2["threshold"],
                rule_data2["condition"],
                rule_data2["severity"],
            ),
        )

        logger.info("Successfully added test alert rules to the database")

        # Verify the rules were added
        cursor = await db.execute(
            "SELECT * FROM alert_rules WHERE model_id = ?", (model_id,)
        )
        rules = await cursor.fetchall()
        logger.info(f"Rules in database: {len(rules)}")
        for rule in rules:
            logger.info(f"Rule: {rule}")

    except Exception as e:
        logger.error(f"Error adding test alert rules: {str(e)}")
    finally:
        # Close the DB connection - handle the case where db might be None
        if db is not None:
            try:
                await db.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
