"""
Script to populate model metrics for all model versions in the database.
This will ensure that all models and their versions show up in dropdown menus.
"""
import logging
import os
import random
import sqlite3
import uuid
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = "data/iotsphere.db"


def main():
    """Populate metrics for all model versions."""
    logger.info("Starting metrics population for all model versions")

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Get all models and their versions
        logger.info("Getting all model versions from model_versions table")
        cursor.execute(
            """
        SELECT mv.model_id, mv.version, m.name
        FROM model_versions mv
        JOIN models m ON mv.model_id = m.id
        """
        )
        model_versions = cursor.fetchall()

        logger.info(f"Found {len(model_versions)} model versions")

        # For each model version, add sample metrics if they don't exist
        for model_version in model_versions:
            model_id = model_version["model_id"]
            version = model_version["version"]
            model_name = model_version["name"]

            # Check if metrics exist for this model version
            cursor.execute(
                """
            SELECT COUNT(*) as count
            FROM model_metrics
            WHERE model_id = ? AND model_version = ?
            """,
                (model_id, version),
            )

            metrics_count = cursor.fetchone()["count"]

            if metrics_count > 0:
                logger.info(
                    f"Metrics already exist for {model_name} ({model_id}) version {version} - {metrics_count} records found"
                )
                continue

            logger.info(
                f"Adding sample metrics for {model_name} ({model_id}) version {version}"
            )

            # Generate sample metrics for this model version
            now = datetime.now()
            metrics_to_insert = []

            # Generate values for common ML metrics
            metrics = {
                "accuracy": round(random.uniform(0.85, 0.99), 4),
                "precision": round(random.uniform(0.80, 0.98), 4),
                "recall": round(random.uniform(0.80, 0.97), 4),
                "f1_score": round(random.uniform(0.82, 0.98), 4),
                "drift_score": round(random.uniform(0.01, 0.15), 4),
                "latency_ms": round(random.uniform(5, 50), 2),
            }

            # Create metrics records
            for metric_name, metric_value in metrics.items():
                metric_id = str(uuid.uuid4())
                timestamp = (now - timedelta(days=random.randint(0, 30))).isoformat()

                metrics_to_insert.append(
                    (metric_id, model_id, version, metric_name, metric_value, timestamp)
                )

            # Insert metrics
            cursor.executemany(
                """
            INSERT INTO model_metrics
                (id, model_id, model_version, metric_name, metric_value, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
                metrics_to_insert,
            )

            logger.info(
                f"Successfully added {len(metrics_to_insert)} metrics for {model_name} ({model_id}) version {version}"
            )

        # Commit changes
        conn.commit()
        logger.info("Successfully populated metrics for all model versions")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error populating metrics: {str(e)}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
