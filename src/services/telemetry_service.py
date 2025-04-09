"""
Telemetry Service for the IoTSphere platform.

This service handles the processing, storage, and retrieval of device telemetry data,
as well as real-time telemetry updates through WebSockets.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from src.models.telemetry import (
    AggregationType,
    TelemetryBatch,
    TelemetryData,
    TelemetryMetadata,
    TelemetryQuery,
)
from src.services.database_service import get_db_service
from src.services.websocket_manager import WebSocketManager, get_websocket_manager

# Setup logger
logger = logging.getLogger(__name__)

# Global service instance for singleton pattern
_telemetry_service = None


def get_telemetry_service():
    """Get or create the Telemetry service instance."""
    global _telemetry_service
    if _telemetry_service is None:
        _telemetry_service = TelemetryService()
    return _telemetry_service


class TelemetryService:
    """
    Service for managing device telemetry data

    This service provides functionality for:
    1. Processing incoming telemetry data from devices
    2. Storing telemetry data for historical analysis
    3. Retrieving recent and historical telemetry data
    4. Broadcasting real-time telemetry updates to clients
    5. Aggregating telemetry data for analysis
    """

    def __init__(self):
        """Initialize the Telemetry Service"""
        self.db_service = get_db_service()
        self.websocket_manager = get_websocket_manager()

        # Cache for recent telemetry values
        self._telemetry_cache = {}

        # Rate limiting for device updates
        self._last_update_time = {}

        logger.info("Telemetry Service initialized")

    async def process_telemetry_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming telemetry data from a device

        Args:
            data: The telemetry data to process
                {
                    "device_id": str,
                    "metric": str,
                    "value": float,
                    "timestamp": str (ISO format),
                    "metadata": dict (optional)
                }

        Returns:
            The processed telemetry data
        """
        try:
            # Validate the data using our model
            telemetry = TelemetryData(**data)

            # Store in database
            await self.db_service.store_telemetry(telemetry.dict())

            # Update the cache
            device_id = telemetry.device_id
            metric = telemetry.metric

            if device_id not in self._telemetry_cache:
                self._telemetry_cache[device_id] = {}

            self._telemetry_cache[device_id][metric] = {
                "value": telemetry.value,
                "timestamp": telemetry.timestamp,
            }

            # Broadcast to clients
            await self.broadcast_telemetry(telemetry.dict())

            # Return the processed data
            return telemetry.dict()

        except Exception as e:
            logger.error(f"Error processing telemetry data: {str(e)}")
            raise

    async def process_telemetry_batch(
        self, batch: TelemetryBatch
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of telemetry data

        Args:
            batch: A batch of telemetry data points

        Returns:
            List of processed telemetry data points
        """
        processed = []

        for metric in batch.metrics:
            metric_data = metric.dict()
            metric_data["device_id"] = batch.device_id
            result = await self.process_telemetry_data(metric_data)
            processed.append(result)

        return processed

    async def get_latest_telemetry(
        self, device_id: str, metric: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest telemetry value for a specific metric

        Args:
            device_id: The device ID
            metric: The metric name

        Returns:
            The latest telemetry value or None if not found
        """
        # Check the cache first
        if (
            device_id in self._telemetry_cache
            and metric in self._telemetry_cache[device_id]
        ):
            return {
                "device_id": device_id,
                "metric": metric,
                "value": self._telemetry_cache[device_id][metric]["value"],
                "timestamp": self._telemetry_cache[device_id][metric]["timestamp"],
            }

        # If not in cache, query the database
        result = await self.db_service.get_latest_telemetry(device_id, metric)

        # Update the cache if found
        if result:
            if device_id not in self._telemetry_cache:
                self._telemetry_cache[device_id] = {}

            self._telemetry_cache[device_id][metric] = {
                "value": result["value"],
                "timestamp": result["timestamp"],
            }

        return result

    async def get_recent_telemetry(
        self, device_id: str, metric: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get recent telemetry data for a device and metric

        Args:
            device_id: The device ID
            metric: The metric name
            limit: Maximum number of records to return

        Returns:
            List of recent telemetry data points
        """
        return await self.db_service.get_recent_telemetry(
            device_id=device_id, metric=metric, limit=limit
        )

    async def get_historical_telemetry(
        self, device_id: str, metric: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get historical telemetry data within a time range

        Args:
            device_id: The device ID
            metric: The metric name
            start_time: Start of the time range
            end_time: End of the time range

        Returns:
            List of telemetry data points in the specified range
        """
        return await self.db_service.get_telemetry_in_range(
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
        return await self.db_service.get_aggregated_telemetry(
            device_id=device_id,
            metric=metric,
            aggregation=aggregation,
            start_time=start_time,
            end_time=end_time,
        )

    async def should_throttle_update(
        self, device_id: str, metric: str, min_interval: float = 0.5
    ) -> bool:
        """
        Check if updates for this device/metric should be throttled

        Args:
            device_id: The device ID
            metric: The metric name
            min_interval: Minimum interval between updates in seconds

        Returns:
            True if updates should be throttled, False otherwise
        """
        now = datetime.utcnow()
        key = f"{device_id}:{metric}"

        if key in self._last_update_time:
            last_time = self._last_update_time[key]
            if (now - last_time).total_seconds() < min_interval:
                return True

        self._last_update_time[key] = now
        return False

    async def broadcast_telemetry(self, telemetry_data: Dict[str, Any]) -> None:
        """
        Broadcast telemetry data to WebSocket clients

        Args:
            telemetry_data: The telemetry data to broadcast
        """
        device_id = telemetry_data["device_id"]
        metric = telemetry_data["metric"]

        # Check for throttling to prevent flooding WebSocket clients
        if await self.should_throttle_update(device_id, metric):
            return

        # Broadcast to clients subscribed to this device's telemetry
        await self.websocket_manager.broadcast_to_device(
            device_id=device_id, message=telemetry_data, connection_type="telemetry"
        )

    async def clear_stale_cache(self, max_age_hours: int = 24) -> None:
        """
        Clear stale entries from the telemetry cache

        Args:
            max_age_hours: Maximum age of cache entries in hours
        """
        now = datetime.utcnow()
        max_age = timedelta(hours=max_age_hours)

        for device_id in list(self._telemetry_cache.keys()):
            for metric in list(self._telemetry_cache[device_id].keys()):
                timestamp = self._telemetry_cache[device_id][metric]["timestamp"]

                if now - timestamp > max_age:
                    del self._telemetry_cache[device_id][metric]

            # Remove empty device entries
            if not self._telemetry_cache[device_id]:
                del self._telemetry_cache[device_id]

        logger.debug(f"Cleared stale cache entries older than {max_age_hours} hours")

    async def simulate_device_telemetry(
        self,
        device_id: str,
        metrics: List[str],
        duration_seconds: int = 60,
        interval_seconds: float = 1.0,
    ) -> None:
        """
        Simulate telemetry data for testing purposes

        Args:
            device_id: The device ID to simulate data for
            metrics: List of metrics to simulate
            duration_seconds: How long to run the simulation
            interval_seconds: Interval between data points
        """
        import random

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(seconds=duration_seconds)

        # Base values for different metrics
        base_values = {
            "temperature": 55.0,
            "pressure": 30.0,
            "flow_rate": 3.5,
            "power": 500.0,
            "humidity": 50.0,
        }

        # Set default values for any metrics not in our defaults
        for metric in metrics:
            if metric not in base_values:
                base_values[metric] = 50.0

        # Run the simulation
        while datetime.utcnow() < end_time:
            for metric in metrics:
                # Generate a random value with some variation
                base = base_values.get(metric, 50.0)
                variation = base * 0.05  # 5% variation
                value = base + random.uniform(-variation, variation)

                # Create the telemetry data point
                telemetry = {
                    "device_id": device_id,
                    "metric": metric,
                    "value": round(value, 2),
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {
                        "unit": self._get_default_unit(metric),
                        "sensor_id": f"sim-{metric}-1",
                        "quality": 95,
                        "tags": {"simulated": True},
                    },
                }

                # Process the telemetry data
                await self.process_telemetry_data(telemetry)

            # Wait for the next interval
            await asyncio.sleep(interval_seconds)

    def _get_default_unit(self, metric: str) -> str:
        """Get the default unit for a metric type"""
        units = {
            "temperature": "celsius",
            "pressure": "psi",
            "flow_rate": "l/min",
            "power": "watts",
            "humidity": "%",
            "level": "%",
            "voltage": "volts",
            "current": "amps",
        }
        return units.get(metric, "units")
