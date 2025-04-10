"""
Temperature History API Module

This module provides optimized endpoints for retrieving temperature history data
with server-side aggregation and processing to reduce client-side burden.

Following best practices:
1. Server-side aggregation - data is pre-processed before sending to client
2. Time period filtering - only requested data is sent (7/14/30 days)
3. Data downsampling - points are reduced based on resolution needs
4. Caching headers - to improve performance on repeated requests
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException, Query, Response

from src.services.device_shadow import get_device_shadow_service
from src.utils.date_utils import parse_iso_datetime

router = APIRouter(
    prefix="/api/temperature-history",
    tags=["Temperature History"],
)


@router.get("/{device_id}")
async def get_temperature_history(
    device_id: str,
    days: int = Query(7, description="Number of days of history (7, 14, or 30)"),
    resolution: str = Query(
        "hourly", description="Data resolution (raw, hourly, daily)"
    ),
    response: Response = None,
):
    """
    Get temperature history for a device with server-side processing.

    Args:
        device_id: The device ID
        days: Number of days of history (7, 14, or 30)
        resolution: Data resolution (raw, hourly, daily)

    Returns:
        JSON with processed temperature history data
    """
    # Validate days parameter
    if days not in [7, 14, 30]:
        raise HTTPException(status_code=400, detail="Days must be 7, 14, or 30")

    # Set cache control headers for improved performance
    if response:
        # Cache for 5 minutes for recent data, longer for older data
        max_age = 300 if days == 7 else 900
        response.headers["Cache-Control"] = f"max-age={max_age}"

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    try:
        # Get shadow service
        shadow_service = get_device_shadow_service()

        # Fetch shadow history data
        try:
            readings = await shadow_service.get_device_shadow_history(device_id)
        except ValueError as ve:
            # Specifically handle missing shadow document error
            if "No shadow document exists" in str(ve):
                # Return a specific error code and message for missing shadow document
                return {
                    "error": "NO_SHADOW_DOCUMENT",
                    "message": str(ve),
                    "timeRange": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat(),
                    },
                    "deviceId": device_id,
                }
            else:
                # Re-raise other ValueError exceptions
                raise ve

        # Filter readings based on date range
        filtered_readings = []
        for reading in readings:
            if "timestamp" in reading:
                reading_time = parse_iso_datetime(reading.get("timestamp"))
                if start_date <= reading_time <= end_date:
                    filtered_readings.append(reading)

        # Use filtered readings
        readings = filtered_readings

        if not readings:
            return {
                "data": [],
                "timeRange": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
            }

        # Process data based on resolution
        processed_data = process_temperature_data(readings, resolution)

        # Return processed data with metadata
        return {
            "data": processed_data,
            "timeRange": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "resolution": resolution,
            "pointCount": len(processed_data),
            "deviceId": device_id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving temperature history: {str(e)}"
        )


def process_temperature_data(readings: List[Dict], resolution: str) -> List[Dict]:
    """
    Process temperature data based on resolution.

    Args:
        readings: List of reading objects with timestamp and temperature
        resolution: Data resolution (raw, hourly, daily)

    Returns:
        Processed data with reduced points based on resolution
    """
    if not readings:
        return []

    # Sort readings by timestamp
    sorted_readings = sorted(
        readings, key=lambda x: parse_iso_datetime(x.get("timestamp", ""))
    )

    # For raw resolution, return all points (with a reasonable limit)
    if resolution == "raw":
        # Limit to 500 most recent points if there are too many
        if len(sorted_readings) > 500:
            sorted_readings = sorted_readings[-500:]

        return [
            {
                "timestamp": reading.get("timestamp", ""),
                "temperature": reading.get("temperature", 0),
            }
            for reading in sorted_readings
        ]

    # For hourly or daily resolution, aggregate data
    aggregated_data = []

    if resolution == "hourly":
        # Group by hour and calculate average
        hour_groups = {}

        for reading in sorted_readings:
            timestamp = parse_iso_datetime(reading.get("timestamp", ""))
            # Truncate to hour
            hour_key = timestamp.replace(minute=0, second=0, microsecond=0).isoformat()

            if hour_key not in hour_groups:
                hour_groups[hour_key] = {"sum": 0, "count": 0}

            hour_groups[hour_key]["sum"] += reading.get("temperature", 0)
            hour_groups[hour_key]["count"] += 1

        for hour, data in hour_groups.items():
            if data["count"] > 0:
                avg_temp = data["sum"] / data["count"]
                aggregated_data.append(
                    {"timestamp": hour, "temperature": round(avg_temp, 1)}
                )

    elif resolution == "daily":
        # Group by day and calculate average
        day_groups = {}

        for reading in sorted_readings:
            timestamp = parse_iso_datetime(reading.get("timestamp", ""))
            # Truncate to day
            day_key = timestamp.replace(
                hour=0, minute=0, second=0, microsecond=0
            ).isoformat()

            if day_key not in day_groups:
                day_groups[day_key] = {"sum": 0, "count": 0}

            day_groups[day_key]["sum"] += reading.get("temperature", 0)
            day_groups[day_key]["count"] += 1

        for day, data in day_groups.items():
            if data["count"] > 0:
                avg_temp = data["sum"] / data["count"]
                aggregated_data.append(
                    {"timestamp": day, "temperature": round(avg_temp, 1)}
                )

    # Sort by timestamp
    return sorted(aggregated_data, key=lambda x: x["timestamp"])
