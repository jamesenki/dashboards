"""
SQL implementation for model metrics and monitoring data.

This module provides concrete SQL-based data access for model metrics,
following the same pattern as other SQLRepository implementations.
"""
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.connection import get_db_session
from src.db.models import Base
from src.monitoring.metrics import ModelMetric

logger = logging.getLogger(__name__)


class SQLModelMetricsRepository:
    """SQL implementation for model metrics data access."""

    def __init__(self, session: AsyncSession = Depends(get_db_session)):
        """Initialize with a database session."""
        self.session = session

    async def record_model_metrics(
        self,
        model_id: str,
        model_version: str,
        metrics: Dict[str, float],
        timestamp: datetime = None,
    ) -> str:
        """
        Record performance metrics for a model.

        Args:
            model_id: ID of the model
            model_version: Version of the model
            metrics: Dictionary of metric names and values
            timestamp: Optional timestamp (defaults to now)

        Returns:
            ID of the recorded metrics
        """
        timestamp = timestamp or datetime.now()
        record_id = str(uuid.uuid4())

        # Build values for batch insert
        values = []
        for metric_name, metric_value in metrics.items():
            metric_id = str(uuid.uuid4())
            values.append(
                {
                    "id": metric_id,
                    "model_id": model_id,
                    "model_version": model_version,
                    "metric_name": metric_name,
                    "metric_value": metric_value,
                    "timestamp": timestamp,
                }
            )

        # Execute batch insert using SQLAlchemy's execute method
        if values:
            query = text(
                """
                INSERT INTO model_metrics
                (id, model_id, model_version, metric_name, metric_value, timestamp)
                VALUES (:id, :model_id, :model_version, :metric_name, :metric_value, :timestamp)
            """
            )

            await self.session.execute(query, values)
            await self.session.commit()

        return record_id

    async def get_model_metrics_history(
        self,
        model_id: str,
        model_version: str,
        metric_name: str,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> List[Dict[str, Any]]:
        """
        Get the history of a specific metric for a model.

        Args:
            model_id: ID of the model
            model_version: Version of the model
            metric_name: Name of the metric
            start_date: Optional start date for the range
            end_date: Optional end date for the range

        Returns:
            List of metric records
        """
        # Default to last 30 days if no range specified
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        query = text(
            """
            SELECT id, model_id, model_version, metric_name, metric_value, timestamp
            FROM model_metrics
            WHERE model_id = :model_id
              AND model_version = :model_version
              AND metric_name = :metric_name
              AND timestamp BETWEEN :start_date AND :end_date
            ORDER BY timestamp DESC
        """
        )

        result = await self.session.execute(
            query,
            {
                "model_id": model_id,
                "model_version": model_version,
                "metric_name": metric_name,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        # Convert to list of dictionaries
        return [dict(row) for row in result]

    async def get_latest_metrics(
        self, model_id: str, model_version: str
    ) -> List[Dict[str, Any]]:
        """
        Get the most recent metrics for a model.

        Args:
            model_id: ID of the model
            model_version: Version of the model

        Returns:
            Dictionary of the latest metrics by name
        """
        query = text(
            """
            SELECT m1.*
            FROM model_metrics m1
            JOIN (
                SELECT metric_name, MAX(timestamp) as max_timestamp
                FROM model_metrics
                WHERE model_id = :model_id AND model_version = :model_version
                GROUP BY metric_name
            ) m2
            ON m1.metric_name = m2.metric_name AND m1.timestamp = m2.max_timestamp
            WHERE m1.model_id = :model_id AND m1.model_version = :model_version
        """
        )

        result = await self.session.execute(
            query,
            {
                "model_id": model_id,
                "model_version": model_version,
            },
        )

        # Convert to list of dictionaries
        return [dict(row) for row in result]

    async def get_models(self) -> List[Dict[str, Any]]:
        """
        Get a list of all active models.

        Returns:
            List of model information
        """
        query = text(
            """
            SELECT model_id, model_name, description, created_at,
                   model_type, tags, FALSE as archived
            FROM model_metadata
            WHERE archived IS NULL OR archived = FALSE
        """
        )

        models_data_result = await self.session.execute(query)
        models_data = [dict(row) for row in models_data_result]

        # Process each model to get versions, metrics, etc.
        result = []
        for model in models_data:
            # Get versions for this model
            versions_query = text(
                """
                SELECT DISTINCT model_version
                FROM model_metrics
                WHERE model_id = :model_id
                ORDER BY model_version
            """
            )

            versions_result = await self.session.execute(
                versions_query, {"model_id": model["model_id"]}
            )
            versions = [row["model_version"] for row in versions_result]

            # Get latest metrics for this model
            metrics_query = text(
                """
                SELECT mm.metric_name, mm.metric_value
                FROM model_metrics mm
                INNER JOIN (
                    SELECT model_id, MAX(timestamp) as latest_time
                    FROM model_metrics
                    WHERE model_id = :model_id
                    GROUP BY model_id
                ) latest ON mm.model_id = latest.model_id AND mm.timestamp = latest.latest_time
            """
            )

            metrics_result = await self.session.execute(
                metrics_query, {"model_id": model["model_id"]}
            )
            metrics = {
                row["metric_name"]: row["metric_value"] for row in metrics_result
            }

            # Add health status based on metrics
            if (
                metrics.get("accuracy", 0) > 0.9
                and metrics.get("drift_score", 1) < 0.05
            ):
                health_status = "GREEN"
            elif (
                metrics.get("accuracy", 0) > 0.8 and metrics.get("drift_score", 1) < 0.1
            ):
                health_status = "YELLOW"
            else:
                health_status = "RED"

            metrics["health_status"] = health_status

            # Get alert count
            alerts_query = text(
                """
                SELECT COUNT(*) as alert_count
                FROM alert_events
                WHERE model_id = :model_id AND resolved = FALSE
            """
            )

            alerts_result = await self.session.execute(
                alerts_query, {"model_id": model["model_id"]}
            )
            alert_count = next(alerts_result)["alert_count"] if alerts_result else 0

            # Parse tags if they exist
            tags = []
            if model.get("tags"):
                tags = model["tags"].split(",")

            # Combine all the data
            result.append(
                {
                    "id": model["model_id"],
                    "name": model["model_name"],
                    "versions": versions,
                    "archived": model.get("archived", False),
                    "metrics": metrics,
                    "alert_count": alert_count,
                    "tags": tags,
                }
            )

        return result

    async def get_alert_rules(self, model_id: str = None) -> List[Dict[str, Any]]:
        """
        Get alert rules for a model or all models.

        Args:
            model_id: Optional model ID to filter by

        Returns:
            List of alert rules
        """
        if model_id:
            query = text(
                """
                SELECT * FROM alert_rules
                WHERE model_id = :model_id
            """
            )
            result = await self.session.execute(query, {"model_id": model_id})
        else:
            query = text("SELECT * FROM alert_rules")
            result = await self.session.execute(query)

        return [dict(row) for row in result]

    async def create_alert_rule(
        self,
        model_id: str,
        metric_name: str,
        threshold: float,
        condition: str,
        severity: str = "WARNING",
    ) -> Dict[str, Any]:
        """
        Create a new alert rule.

        Args:
            model_id: ID of the model
            metric_name: Name of the metric to monitor
            threshold: Threshold value
            condition: Condition (e.g., 'BELOW', 'ABOVE')
            severity: Alert severity

        Returns:
            Created alert rule
        """
        rule_id = str(uuid.uuid4())
        query = text(
            """
            INSERT INTO alert_rules
            (id, model_id, metric_name, threshold, condition, severity, created_at)
            VALUES (:id, :model_id, :metric_name, :threshold, :condition, :severity, :created_at)
        """
        )

        await self.session.execute(
            query,
            {
                "id": rule_id,
                "model_id": model_id,
                "metric_name": metric_name,
                "threshold": threshold,
                "condition": condition,
                "severity": severity,
                "created_at": datetime.now(),
            },
        )
        await self.session.commit()

        return {
            "id": rule_id,
            "model_id": model_id,
            "metric_name": metric_name,
            "threshold": threshold,
            "condition": condition,
            "severity": severity,
        }

    async def record_alert_event(
        self,
        rule_id: str,
        model_id: str,
        metric_name: str,
        metric_value: float,
        severity: str = "WARNING",
    ) -> Dict[str, Any]:
        """
        Record an alert event.

        Args:
            rule_id: ID of the alert rule
            model_id: ID of the model
            metric_name: Name of the metric
            metric_value: Value that triggered the alert
            severity: Alert severity

        Returns:
            Created alert event
        """
        event_id = str(uuid.uuid4())
        query = text(
            """
            INSERT INTO alert_events
            (id, rule_id, model_id, metric_name, metric_value, severity, created_at, resolved)
            VALUES (:id, :rule_id, :model_id, :metric_name, :metric_value, :severity, :created_at, FALSE)
        """
        )

        await self.session.execute(
            query,
            {
                "id": event_id,
                "rule_id": rule_id,
                "model_id": model_id,
                "metric_name": metric_name,
                "metric_value": metric_value,
                "severity": severity,
                "created_at": datetime.now(),
            },
        )
        await self.session.commit()

        return {
            "id": event_id,
            "rule_id": rule_id,
            "model_id": model_id,
            "metric_name": metric_name,
            "metric_value": metric_value,
            "severity": severity,
            "resolved": False,
        }
