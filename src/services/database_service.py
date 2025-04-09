"""
Database Service for the IoTSphere platform.

This service provides database access and operations for various IoTSphere components,
including device registry, telemetry storage, and user management.
"""
import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

# Setup logger
logger = logging.getLogger(__name__)

# Global service instance for singleton pattern
_database_service = None


class DatabaseService:
    """
    Database service for IoTSphere.

    This service provides methods for:
    - Telemetry data storage and retrieval
    - Device registry operations
    - User and authentication data

    Currently uses SQLite for development and testing. For production,
    this would be replaced with PostgreSQL or another scalable database.
    """

    def __init__(self):
        """Initialize the database service."""
        self.db_path = os.path.join(
            os.path.dirname(__file__), "../../data/iotsphere.db"
        )
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialize database
        self._init_db()
        logger.info(f"Database service initialized with database: {self.db_path}")

    def _init_db(self):
        """Initialize the database schema if it doesn't exist."""
        # Connect to database and create tables if they don't exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create telemetry table
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL NOT NULL,
            timestamp TEXT NOT NULL,
            metadata TEXT,
            UNIQUE(device_id, metric, timestamp)
        )
        """
        )

        # Create index on device_id and timestamp
        cursor.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_telemetry_device_id_timestamp
        ON telemetry (device_id, timestamp)
        """
        )

        # Create index on device_id and metric
        cursor.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_telemetry_device_id_metric
        ON telemetry (device_id, metric)
        """
        )

        conn.commit()
        conn.close()

    async def store_telemetry(self, data: Dict[str, Any]) -> bool:
        """
        Store telemetry data.

        Args:
            data: Telemetry data with device_id, metric, value, and timestamp

        Returns:
            bool: True if successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            metadata = data.get("metadata")
            if metadata:
                metadata_json = json.dumps(metadata)
            else:
                metadata_json = None

            cursor.execute(
                """
                INSERT OR REPLACE INTO telemetry
                (device_id, metric, value, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    data["device_id"],
                    data["metric"],
                    data["value"],
                    data["timestamp"],
                    metadata_json,
                ),
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Error storing telemetry data: {e}")
            return False

    async def get_latest_telemetry(
        self, device_id: str, metric: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest telemetry data for a device and metric.

        Args:
            device_id: The device ID
            metric: The telemetry metric name

        Returns:
            Latest telemetry data or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Use row factory to get dict-like results
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT device_id, metric, value, timestamp, metadata
                FROM telemetry
                WHERE device_id = ? AND metric = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (device_id, metric),
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                data = dict(row)
                if data["metadata"]:
                    data["metadata"] = json.loads(data["metadata"])
                return data
            return None

        except Exception as e:
            logger.error(f"Error retrieving latest telemetry data: {e}")
            return None

    async def get_recent_telemetry(
        self, device_id: str, metric: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recent telemetry data for a device and metric.

        Args:
            device_id: The device ID
            metric: The telemetry metric name
            limit: Maximum number of records to return

        Returns:
            List of telemetry data dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Use row factory to get dict-like results
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT device_id, metric, value, timestamp, metadata
                FROM telemetry
                WHERE device_id = ? AND metric = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (device_id, metric, limit),
            )

            rows = cursor.fetchall()
            conn.close()

            # Convert rows to dictionaries and parse metadata
            result = []
            for row in rows:
                data = dict(row)
                if data["metadata"]:
                    data["metadata"] = json.loads(data["metadata"])
                result.append(data)

            return result

        except Exception as e:
            logger.error(f"Error retrieving telemetry data: {e}")
            return []

    async def get_telemetry_range(
        self, device_id: str, metric: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get telemetry data for a device and metric within a time range.

        Args:
            device_id: The device ID
            metric: The telemetry metric name
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of telemetry data dictionaries
        """
        try:
            # Convert datetime to string
            start_str = start_time.isoformat()
            end_str = end_time.isoformat()

            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT device_id, metric, value, timestamp, metadata
                FROM telemetry
                WHERE device_id = ? AND metric = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
                """,
                (device_id, metric, start_str, end_str),
            )

            rows = cursor.fetchall()
            conn.close()

            # Convert rows to dictionaries and parse metadata
            result = []
            for row in rows:
                data = dict(row)
                if data["metadata"]:
                    data["metadata"] = json.loads(data["metadata"])
                result.append(data)

            return result

        except Exception as e:
            logger.error(f"Error retrieving telemetry data range: {e}")
            return []

    async def get_telemetry_in_range(
        self, device_id: str, metric: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Alias for get_telemetry_range to match the function call from TelemetryService

        Args:
            device_id: The device ID
            metric: The metric name
            start_time: Start of the time range
            end_time: End of the time range

        Returns:
            List of telemetry data points in the specified range
        """
        return await self.get_telemetry_range(
            device_id=device_id, metric=metric, start_time=start_time, end_time=end_time
        )

    async def get_aggregated_telemetry(
        self,
        device_id: str,
        metric: str,
        aggregation: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Get aggregated telemetry data (e.g., hourly averages)

        Args:
            device_id: The device ID
            metric: The metric name
            aggregation: Type of aggregation (hourly, daily, weekly, monthly)
            start_time: Start of the time range
            end_time: End of the time range

        Returns:
            List of aggregated data points
        """
        # This is a simplified implementation for the prototype
        # In a production system, this would use proper SQL aggregation
        try:
            # Get raw data first
            raw_data = await self.get_telemetry_range(
                device_id=device_id,
                metric=metric,
                start_time=start_time,
                end_time=end_time,
            )

            if not raw_data:
                return []

            # Simple aggregation based on the specified interval
            result = []
            interval_seconds = {
                "hourly": 3600,
                "daily": 86400,
                "weekly": 604800,
                "monthly": 2592000,  # Approximation
            }.get(aggregation.lower(), 3600)

            # Group by time intervals and calculate averages
            # For the prototype, just return some basic aggregated data
            return [
                {
                    "device_id": device_id,
                    "metric": metric,
                    "value": sum(item["value"] for item in raw_data) / len(raw_data),
                    "timestamp": start_time.isoformat(),
                    "aggregation": aggregation,
                    "count": len(raw_data),
                }
            ]

        except Exception as e:
            logger.error(f"Error aggregating telemetry data: {e}")
            return []


def get_db_service() -> DatabaseService:
    """
    Get or create the database service instance.

    Returns:
        DatabaseService: The singleton database service instance
    """
    global _database_service

    if _database_service is None:
        _database_service = DatabaseService()
        logger.info("Created singleton DatabaseService instance")

    return _database_service
