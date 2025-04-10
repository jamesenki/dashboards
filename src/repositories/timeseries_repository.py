"""
Timeseries Repository
Handles storage, retrieval and archiving of time series data.

Following TDD principles:
1. Only retrieve data needed for specific time ranges
2. Archive data older than 30 days
3. Maintain separate storage for active vs archived data
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.config import get_database_path
from src.models.water_heater import TemperatureReading

# Configure logger
logger = logging.getLogger("temperature_history")


class TimeseriesRepository:
    """Repository for managing water heater time series data"""

    def __init__(self):
        """Initialize the repository with database connections"""
        # Paths for active and archive databases
        self.active_db_path = get_database_path("timeseries_active.db")
        self.archive_db_path = get_database_path("timeseries_archive.db")

        # Initialize databases if they don't exist
        self._initialize_db(self.active_db_path)
        self._initialize_db(self.archive_db_path)

        logger.info(
            "Initialized TimeseriesRepository with active and archive databases"
        )

    def _initialize_db(self, db_path: str):
        """Initialize the database with required tables"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create readings table if it doesn't exist
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS temperature_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            heater_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        # Create index on heater_id and timestamp
        cursor.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_heater_timestamp
        ON temperature_readings (heater_id, timestamp)
        """
        )

        # Commit changes and close connection
        conn.commit()
        conn.close()

    def get_current_reading(self, heater_id: str) -> Optional[TemperatureReading]:
        """
        Get the most recent temperature reading for a water heater.

        Args:
            heater_id: The ID of the water heater

        Returns:
            Most recent TemperatureReading or None if not found
        """
        logger.info(f"Getting current reading for water heater {heater_id}")

        # Connect to active database
        conn = sqlite3.connect(self.active_db_path)
        cursor = conn.cursor()

        # Query for most recent reading
        cursor.execute(
            """
        SELECT heater_id, timestamp, temperature
        FROM temperature_readings
        WHERE heater_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
        """,
            (heater_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            logger.warning(f"No current reading found for water heater {heater_id}")
            return None

        # Convert to TemperatureReading
        return TemperatureReading(
            heater_id=row[0], timestamp=row[1], temperature=row[2]
        )

    def get_readings(
        self,
        heater_id: str,
        days: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[TemperatureReading]:
        """
        Get temperature readings for a water heater based on specified criteria.

        Args:
            heater_id: The ID of the water heater
            days: Number of days of history to return
            start_date: Start date for custom date range
            end_date: End date for custom date range

        Returns:
            List of TemperatureReading objects
        """
        # Build query parameters
        params = [heater_id]
        date_condition = ""

        # Apply date filtering
        if days:
            # Calculate cutoff date for days filter
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            date_condition = "AND timestamp >= ?"
            params.append(cutoff_date)

            logger.info(
                f"Getting readings for water heater {heater_id} from {cutoff_date}"
            )

        elif start_date and end_date:
            # Use explicit date range
            date_condition = "AND timestamp >= ? AND timestamp <= ?"
            params.extend([start_date.isoformat(), end_date.isoformat()])

            logger.info(
                f"Getting readings for water heater {heater_id} from {start_date} to {end_date}"
            )

        elif start_date:
            # Just start date specified
            date_condition = "AND timestamp >= ?"
            params.append(start_date.isoformat())

            logger.info(
                f"Getting readings for water heater {heater_id} from {start_date}"
            )

        elif end_date:
            # Just end date specified
            date_condition = "AND timestamp <= ?"
            params.append(end_date.isoformat())

            logger.info(
                f"Getting readings for water heater {heater_id} until {end_date}"
            )

        else:
            # Default to 7 days if no criteria specified
            cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()
            date_condition = "AND timestamp >= ?"
            params.append(cutoff_date)

            logger.info(
                f"Getting default (7 days) readings for water heater {heater_id} from {cutoff_date}"
            )

        # Connect to active database
        conn = sqlite3.connect(self.active_db_path)
        cursor = conn.cursor()

        # Query for readings
        query = f"""
        SELECT heater_id, timestamp, temperature
        FROM temperature_readings
        WHERE heater_id = ? {date_condition}
        ORDER BY timestamp ASC
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        logger.info(f"Retrieved {len(rows)} readings for water heater {heater_id}")

        # Convert to TemperatureReading objects
        return [
            TemperatureReading(heater_id=row[0], timestamp=row[1], temperature=row[2])
            for row in rows
        ]

    def get_archived_readings(
        self, heater_id: str, start_date: datetime, end_date: Optional[datetime] = None
    ) -> List[TemperatureReading]:
        """
        Get archived temperature readings for a water heater.

        Args:
            heater_id: The ID of the water heater
            start_date: Start date for retrieving archived data
            end_date: End date for retrieving archived data

        Returns:
            List of TemperatureReading objects from archive
        """
        # Build query parameters
        params = [heater_id, start_date.isoformat()]
        date_condition = "AND timestamp >= ?"

        # Add end date if specified
        if end_date:
            date_condition += " AND timestamp <= ?"
            params.append(end_date.isoformat())

            logger.info(
                f"Getting archived readings for water heater {heater_id} from {start_date} to {end_date}"
            )
        else:
            logger.info(
                f"Getting archived readings for water heater {heater_id} from {start_date}"
            )

        # Connect to archive database
        conn = sqlite3.connect(self.archive_db_path)
        cursor = conn.cursor()

        # Query for readings
        query = f"""
        SELECT heater_id, timestamp, temperature
        FROM temperature_readings
        WHERE heater_id = ? {date_condition}
        ORDER BY timestamp ASC
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        logger.info(
            f"Retrieved {len(rows)} archived readings for water heater {heater_id}"
        )

        # Convert to TemperatureReading objects
        return [
            TemperatureReading(heater_id=row[0], timestamp=row[1], temperature=row[2])
            for row in rows
        ]

    def add_reading(self, reading: TemperatureReading) -> None:
        """
        Add a temperature reading to the active database

        Args:
            reading: The temperature reading to add
        """
        logger.info(
            f"Adding temperature reading for water heater {reading.heater_id} at {reading.timestamp}"
        )

        try:
            # Connect to active database
            conn = sqlite3.connect(self.active_db_path)
            cursor = conn.cursor()

            # Insert reading
            cursor.execute(
                "INSERT INTO temperature_readings (heater_id, timestamp, temperature) VALUES (?, ?, ?)",
                (reading.heater_id, reading.timestamp, reading.temperature),
            )

            # Commit changes
            conn.commit()

        except Exception as e:
            logger.error(f"Error adding temperature reading: {e}")
            raise
        finally:
            # Close connection
            if conn:
                conn.close()

    # Alias for consistency with test naming
    insert_reading = add_reading

    def archive_old_readings(self, cutoff_date: datetime) -> int:
        """
        Archive readings older than the cutoff date.
        Moves data from active to archive database.

        Args:
            cutoff_date: Date before which readings should be archived

        Returns:
            Number of readings archived
        """
        logger.info(f"Archiving readings older than {cutoff_date}")

        # Connect to both databases
        active_conn = sqlite3.connect(self.active_db_path)
        archive_conn = sqlite3.connect(self.archive_db_path)

        active_cursor = active_conn.cursor()
        archive_cursor = archive_conn.cursor()

        # Start transaction
        active_conn.execute("BEGIN TRANSACTION")
        archive_conn.execute("BEGIN TRANSACTION")

        try:
            # Get readings to archive
            active_cursor.execute(
                """
            SELECT heater_id, timestamp, temperature
            FROM temperature_readings
            WHERE timestamp < ?
            """,
                (cutoff_date.isoformat(),),
            )

            rows = active_cursor.fetchall()
            count = len(rows)

            logger.info(f"Found {count} readings to archive")

            if count > 0:
                # Insert into archive database
                archive_cursor.executemany(
                    """
                INSERT INTO temperature_readings (heater_id, timestamp, temperature)
                VALUES (?, ?, ?)
                """,
                    rows,
                )

                # Delete from active database
                active_cursor.execute(
                    """
                DELETE FROM temperature_readings
                WHERE timestamp < ?
                """,
                    (cutoff_date.isoformat(),),
                )

                # Commit transactions
                active_conn.commit()
                archive_conn.commit()

                logger.info(f"Successfully archived {count} readings")
            else:
                # No data to archive
                active_conn.rollback()
                archive_conn.rollback()

                logger.info("No readings to archive")

            return count

        except Exception as e:
            # Rollback on error
            active_conn.rollback()
            archive_conn.rollback()

            logger.error(f"Error archiving readings: {str(e)}")
            raise

        finally:
            # Close connections
            active_conn.close()
            archive_conn.close()
