"""
Script to configure alerts for all models in the database
and delete test models.
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
    """Configure alerts for all models and delete test models."""
    logger.info("Starting alert configuration for all models")

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Delete test models
        test_models_to_delete = ["test-model-123", "model1"]
        for model_id in test_models_to_delete:
            logger.info(f"Deleting test model: {model_id}")

            # Delete from model_metrics first (due to foreign key constraints)
            cursor.execute("DELETE FROM model_metrics WHERE model_id = ?", (model_id,))
            logger.info(f"Deleted {cursor.rowcount} metrics for model {model_id}")

            # Delete from model_versions
            cursor.execute("DELETE FROM model_versions WHERE model_id = ?", (model_id,))
            logger.info(f"Deleted {cursor.rowcount} versions for model {model_id}")

            # Delete from alert_rules
            cursor.execute("DELETE FROM alert_rules WHERE model_id = ?", (model_id,))
            logger.info(f"Deleted {cursor.rowcount} alert rules for model {model_id}")

            # Delete from models
            cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))
            logger.info(f"Deleted {cursor.rowcount} model record for {model_id}")

        # Get all models (excluding any remaining test models)
        logger.info("Getting all active models")
        cursor.execute(
            """
        SELECT m.id, m.name, mv.version
        FROM models m
        JOIN model_versions mv ON m.id = mv.model_id
        WHERE m.id NOT LIKE '%test%' AND m.id NOT LIKE 'model%'
        ORDER BY m.name, mv.version
        """
        )
        model_versions = cursor.fetchall()

        logger.info(
            f"Found {len(model_versions)} model versions to configure alerts for"
        )

        # Clear out existing alert rules
        cursor.execute("DELETE FROM alert_rules")
        logger.info(f"Deleted {cursor.rowcount} existing alert rules")

        # Define alert rule templates for different model types
        alert_templates = {
            "water-heater": [
                {
                    "metric_name": "accuracy",
                    "threshold": 0.85,
                    "operator": "<",
                    "severity": "HIGH",
                    "rule_name": "Low Accuracy Alert",
                    "description": "Alert when model accuracy falls below threshold",
                },
                {
                    "metric_name": "drift_score",
                    "threshold": 0.10,
                    "operator": ">",
                    "severity": "MEDIUM",
                    "rule_name": "Data Drift Alert",
                    "description": "Alert when drift score exceeds threshold",
                },
                {
                    "metric_name": "latency_ms",
                    "threshold": 40.0,
                    "operator": ">",
                    "severity": "LOW",
                    "rule_name": "High Latency Alert",
                    "description": "Alert when model inference latency exceeds threshold",
                },
            ],
            "energy": [
                {
                    "metric_name": "accuracy",
                    "threshold": 0.87,
                    "operator": "<",
                    "severity": "HIGH",
                    "rule_name": "Accuracy Degradation Alert",
                    "description": "Alert when forecasting accuracy falls below threshold",
                },
                {
                    "metric_name": "drift_score",
                    "threshold": 0.15,
                    "operator": ">",
                    "severity": "MEDIUM",
                    "rule_name": "Energy Consumption Pattern Shift",
                    "description": "Alert when consumption patterns show significant shift",
                },
            ],
            "anomaly": [
                {
                    "metric_name": "precision",
                    "threshold": 0.82,
                    "operator": "<",
                    "severity": "HIGH",
                    "rule_name": "Precision Degradation Alert",
                    "description": "Alert when anomaly detection precision falls below threshold",
                },
                {
                    "metric_name": "recall",
                    "threshold": 0.85,
                    "operator": "<",
                    "severity": "MEDIUM",
                    "rule_name": "Recall Degradation Alert",
                    "description": "Alert when anomaly detection recall falls below threshold",
                },
                {
                    "metric_name": "f1_score",
                    "threshold": 0.83,
                    "operator": "<",
                    "severity": "MEDIUM",
                    "rule_name": "F1 Score Alert",
                    "description": "Alert when F1 score falls below threshold",
                },
            ],
            "maintenance": [
                {
                    "metric_name": "accuracy",
                    "threshold": 0.88,
                    "operator": "<",
                    "severity": "HIGH",
                    "rule_name": "Prediction Accuracy Alert",
                    "description": "Alert when maintenance prediction accuracy falls below threshold",
                },
                {
                    "metric_name": "precision",
                    "threshold": 0.80,
                    "operator": "<",
                    "severity": "MEDIUM",
                    "rule_name": "False Maintenance Alert",
                    "description": "Alert when too many false maintenance predictions occur",
                },
            ],
        }

        # Default template for any model type not specifically defined
        default_template = [
            {
                "metric_name": "accuracy",
                "threshold": 0.85,
                "operator": "<",
                "severity": "MEDIUM",
                "rule_name": "Generic Accuracy Alert",
                "description": "Alert when model accuracy falls below threshold",
            }
        ]

        # For each model version, add appropriate alerts
        for model_version in model_versions:
            model_id = model_version["id"]
            model_name = model_version["name"]
            version = model_version["version"]

            # Determine which template to use based on the model name
            template_key = None
            if "water" in model_id.lower() or "heater" in model_id.lower():
                template_key = "water-heater"
            elif "energy" in model_id.lower() or "forecast" in model_id.lower():
                template_key = "energy"
            elif "anomaly" in model_id.lower() or "detect" in model_id.lower():
                template_key = "anomaly"
            elif "maintenance" in model_id.lower() or "predict" in model_id.lower():
                template_key = "maintenance"

            # Get appropriate template
            template = alert_templates.get(template_key, default_template)

            logger.info(
                f"Configuring alerts for {model_name} ({model_id}) version {version} using {template_key if template_key else 'default'} template"
            )

            # Create alert rules for this model
            alert_rules = []
            for alert_config in template:
                rule_id = str(uuid.uuid4())
                created_at = datetime.now().isoformat()
                # Randomize thresholds slightly to create variety
                threshold = alert_config["threshold"] * random.uniform(0.95, 1.05)
                threshold = round(threshold, 4)

                alert_rules.append(
                    (
                        rule_id,
                        model_id,
                        version,
                        alert_config["rule_name"],
                        alert_config["metric_name"],
                        threshold,
                        alert_config["operator"],
                        alert_config["severity"],
                        alert_config["description"],
                        created_at,
                        1,  # is_active
                    )
                )

            # Insert alert rules
            cursor.executemany(
                """
            INSERT INTO alert_rules
                (id, model_id, model_version, rule_name, metric_name, threshold, operator, severity, description, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                alert_rules,
            )

            logger.info(
                f"Added {len(alert_rules)} alert rules for {model_name} ({model_id}) version {version}"
            )

            # Create a few alert events (some resolved, some active)
            now = datetime.now()
            if random.random() < 0.6:  # 60% chance of having alert events
                # Get some of the rules we just created
                cursor.execute(
                    """
                SELECT id, metric_name, severity
                FROM alert_rules
                WHERE model_id = ? AND model_version = ?
                """,
                    (model_id, version),
                )
                rules = cursor.fetchall()

                if rules:
                    # Create 1-3 events for random rules
                    num_events = random.randint(1, min(3, len(rules)))
                    selected_rules = random.sample(list(rules), num_events)

                    events = []
                    for rule in selected_rules:
                        event_id = str(uuid.uuid4())
                        rule_id = rule["id"]
                        metric_name = rule["metric_name"]
                        severity = rule["severity"]

                        # Metrics that violated the rule
                        if (
                            metric_name.startswith("accuracy")
                            or metric_name.startswith("precision")
                            or metric_name.startswith("recall")
                            or metric_name.startswith("f1")
                        ):
                            # For metrics where lower is worse
                            metric_value = round(random.uniform(0.70, 0.85), 4)
                        else:
                            # For metrics where higher is worse (like drift, latency)
                            metric_value = round(random.uniform(0.15, 0.30), 4)

                        # 70% chance of being resolved
                        resolved = random.random() < 0.7
                        created_at = (
                            now - timedelta(days=random.randint(1, 30))
                        ).isoformat()
                        resolved_at = (
                            (now - timedelta(days=random.randint(0, 5))).isoformat()
                            if resolved
                            else None
                        )

                        events.append(
                            (
                                event_id,
                                rule_id,
                                model_id,
                                metric_name,
                                metric_value,
                                severity,
                                created_at,
                                1 if resolved else 0,
                                resolved_at,
                            )
                        )

                    # Insert events
                    cursor.executemany(
                        """
                    INSERT INTO alert_events
                        (id, rule_id, model_id, metric_name, metric_value, severity, created_at, resolved, resolved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        events,
                    )

                    logger.info(
                        f"Added {len(events)} alert events for {model_name} ({model_id}) version {version}"
                    )

        # Commit changes
        conn.commit()
        logger.info("Successfully configured alerts for all models")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error configuring alerts: {str(e)}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
