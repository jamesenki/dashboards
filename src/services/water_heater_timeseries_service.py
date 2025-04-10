"""
Water Heater Timeseries Service
Handles selective loading, preprocessing, and archiving of time series data.

Following TDD principles:
1. Only load data needed per tab and selection
2. Preprocess data for efficient display
3. Archive data older than 30 days
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from fastapi import HTTPException

from src.models.water_heater import TemperatureReading
from src.repositories.timeseries_repository import TimeseriesRepository

# Configure logger
logger = logging.getLogger("temperature_history")


class WaterHeaterTimeseriesService:
    """Service for managing water heater time series data"""

    def __init__(self):
        """Initialize the service with a repository"""
        self.repository = TimeseriesRepository()
        logger.info("Initializing WaterHeaterTimeseriesService")

    def get_current_reading(self, heater_id: str) -> Dict[str, Any]:
        """
        Get the current temperature for a water heater.
        Only returns the most recent value, not historical data.

        Args:
            heater_id: The ID of the water heater

        Returns:
            Dictionary with current temperature data
        """
        logger.info(f"Getting current temperature for water heater {heater_id}")
        reading = self.repository.get_current_reading(heater_id)

        if not reading:
            logger.warning(f"No temperature data found for water heater {heater_id}")
            return {"temperature": None, "timestamp": None, "status": "no_data"}

        return {
            "temperature": reading.temperature,
            "timestamp": reading.timestamp,
            "status": "ok",
        }

    # Alias for backwards compatibility
    get_current_temperature = get_current_reading

    def get_readings(
        self,
        heater_id: str,
        days: Optional[int] = 7,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get temperature history for a water heater based on specified criteria.

        Args:
            heater_id: The ID of the water heater
            days: Number of days of history to return (default 7, max 30)
            start_date: Start date for custom date range
            end_date: End date for custom date range

        Returns:
            List of temperature readings

        Raises:
            HTTPException: If days parameter exceeds maximum (30)
        """
        # Validate days parameter
        if days and days > 30:
            logger.warning(f"Requested {days} days of data, exceeds maximum of 30 days")
            raise HTTPException(
                status_code=400,
                detail=f"Cannot request more than 30 days of data. Requested: {days} days",
            )

        # Log what we're retrieving to help debug data loading issues
        if days:
            logger.info(
                f"Getting {days} days of temperature history for water heater {heater_id}"
            )
        elif start_date and end_date:
            logger.info(
                f"Getting temperature history for water heater {heater_id} from {start_date} to {end_date}"
            )
        else:
            logger.info(
                f"Getting default (7 days) temperature history for water heater {heater_id}"
            )

        # Get readings from repository
        readings = self.repository.get_readings(heater_id, days, start_date, end_date)

        if not readings:
            logger.warning(f"No temperature history found for water heater {heater_id}")
            return []

        # Convert to dictionary representation
        return [self._reading_to_dict(reading) for reading in readings]

    # Alias for backwards compatibility
    get_temperature_history = get_readings

    def preprocess_temperature_data(
        self, readings: List[Dict[str, Any]], days: int
    ) -> List[Dict[str, Any]]:
        """
        Preprocess temperature data for efficient display based on dataset size and time range.

        Args:
            readings: List of temperature readings
            days: Number of days of data (affects downsampling strategy)

        Returns:
            List of preprocessed temperature readings
        """
        logger.info(
            f"Preprocessing {len(readings)} temperature readings for {days} days display"
        )

        # Skip preprocessing for small datasets
        if len(readings) <= 100:
            logger.info(
                f"Small dataset ({len(readings)} points), skipping preprocessing"
            )
            return readings

        # Convert dict readings to model objects if needed
        model_readings = []
        for reading in readings:
            if isinstance(reading, dict):
                try:
                    model_readings.append(TemperatureReading(**reading))
                except Exception as e:
                    logger.error(f"Error converting reading to model: {e}")
            else:
                model_readings.append(reading)

        # Apply appropriate preprocessing strategy
        preprocessed = self._preprocess_readings(model_readings, days)

        # Convert back to dictionary format if needed
        result = []
        for reading in preprocessed:
            if isinstance(reading, dict):
                result.append(reading)
            else:
                result.append(self._reading_to_dict(reading))

        logger.info(f"Preprocessed {len(readings)} data points down to {len(result)}")
        return result

    def get_preprocessed_temperature_history(
        self, heater_id: str, days: Optional[int] = 7
    ) -> List[Dict[str, Any]]:
        """
        Get preprocessed temperature history with appropriate downsampling based on time range.

        Args:
            heater_id: The ID of the water heater
            days: Number of days of history to return (default 7, max 30)

        Returns:
            List of preprocessed temperature readings
        """
        logger.info(
            f"Getting preprocessed ({days} days) temperature history for water heater {heater_id}"
        )

        # Get raw readings
        readings = self.repository.get_readings(heater_id, days)

        if not readings:
            logger.warning(f"No temperature history found for water heater {heater_id}")
            return []

        # Preprocess the readings using our utility method
        return self.preprocess_temperature_data(
            [self._reading_to_dict(r) for r in readings], days
        )

    def get_archived_readings(
        self, heater_id: str, start_date: datetime, end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get archived temperature history (data older than 30 days).

        Args:
            heater_id: The ID of the water heater
            start_date: Start date for retrieving archived data
            end_date: End date for retrieving archived data

        Returns:
            List of archived temperature readings
        """
        logger.info(
            f"Getting archived temperature history for water heater {heater_id}"
        )

        # Set end_date to 30 days ago if not specified
        if not end_date:
            end_date = datetime.now() - timedelta(days=30)

        # Get archived readings
        readings = self.repository.get_archived_readings(
            heater_id, start_date, end_date
        )

        if not readings:
            logger.warning(
                f"No archived temperature history found for water heater {heater_id}"
            )
            return []

        # Convert to dictionary representation
        return [self._reading_to_dict(reading) for reading in readings]

    # Alias for backwards compatibility
    get_archived_temperature_history = get_archived_readings

    def archive_old_readings(self, days: int = 30) -> int:
        """
        Archive readings older than the specified number of days.

        Args:
            days: Number of days to keep in active storage (default 30)

        Returns:
            Number of readings archived
        """
        logger.info(f"Archiving readings older than {days} days")

        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days)

        # Archive readings
        archived_count = self.repository.archive_old_readings(cutoff_date)

        logger.info(f"Archived {archived_count} readings")
        return archived_count

    def _reading_to_dict(self, reading: TemperatureReading) -> Dict[str, Any]:
        """Convert a TemperatureReading to a dictionary"""
        return {
            "temperature": reading.temperature,
            "timestamp": reading.timestamp,
            "heater_id": reading.heater_id,
        }

    def _preprocess_readings(
        self, readings: List[TemperatureReading], days: int
    ) -> List[Dict[str, Any]]:
        """
        Apply preprocessing strategies to readings based on the time range.

        Args:
            readings: List of temperature readings to preprocess
            days: Number of days of data (affects downsampling strategy)

        Returns:
            List of preprocessed temperature readings
        """
        # Sort readings by timestamp to ensure correct processing
        sorted_readings = sorted(
            readings, key=lambda r: datetime.fromisoformat(r.timestamp)
        )

        # Apply different preprocessing strategies based on time range
        if days <= 7:
            # For 7 days: Aggregate to hourly averages
            preprocessed = self._aggregate_hourly(sorted_readings)
        elif days <= 14:
            # For 14 days: Aggregate to 2-hour averages
            preprocessed = self._aggregate_by_hours(sorted_readings, 2)
        else:
            # For 30 days: Aggregate to 6-hour averages
            preprocessed = self._aggregate_by_hours(sorted_readings, 6)

        return [self._reading_to_dict(reading) for reading in preprocessed]

    def _aggregate_hourly(
        self, readings: List[TemperatureReading]
    ) -> List[TemperatureReading]:
        """Aggregate readings to hourly averages"""
        return self._aggregate_by_hours(readings, 1)

    def _aggregate_by_hours(
        self, readings: List[TemperatureReading], hours: int
    ) -> List[TemperatureReading]:
        """
        Aggregate readings by specified hours.

        Args:
            readings: List of temperature readings to aggregate
            hours: Number of hours to aggregate by

        Returns:
            List of aggregated readings
        """
        # Group readings by hour
        hour_groups = {}

        for reading in readings:
            dt = datetime.fromisoformat(reading.timestamp)
            # Create a key based on the specified hour interval
            hour_key = dt.replace(minute=0, second=0, microsecond=0)
            if hours > 1:
                hour_offset = (hour_key.hour // hours) * hours
                hour_key = hour_key.replace(hour=hour_offset)

            if hour_key not in hour_groups:
                hour_groups[hour_key] = []

            hour_groups[hour_key].append(reading)

        # Create aggregated readings
        aggregated = []

        for hour, group in sorted(hour_groups.items()):
            # Calculate average temperature
            avg_temp = sum(r.temperature for r in group) / len(group)

            # Create new reading with aggregated data
            aggregated.append(
                TemperatureReading(
                    timestamp=hour.isoformat(),
                    temperature=round(avg_temp, 1),
                    heater_id=group[0].heater_id,
                )
            )

        return aggregated
