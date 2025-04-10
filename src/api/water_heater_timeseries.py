"""
Water Heater Timeseries API
Provides endpoints for selective data loading, preprocessing, and archiving.

Following TDD principles:
1. Only load data needed per tab and selection
2. Preprocess data for efficient display
3. Archive data older than 30 days
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.models.water_heater import TemperatureReading
from src.services.water_heater_timeseries_service import WaterHeaterTimeseriesService

# Create the service instance
timeseries_service = WaterHeaterTimeseriesService()

# Create router
router = APIRouter(
    prefix="/api/water-heaters",
    tags=["water-heater-timeseries"],
)

# Admin router for maintenance tasks
admin_router = APIRouter(
    prefix="/api/admin/timeseries",
    tags=["admin", "timeseries"],
)


@router.get("/{device_id}/temperature/current")
async def get_current_temperature(
    device_id: str,
    service: WaterHeaterTimeseriesService = Depends(lambda: timeseries_service),
):
    """
    Get the current temperature for a water heater.
    Only returns the most recent value, not historical data.

    This endpoint is used by the Details tab to display the current temperature
    without loading historical data.
    """
    return service.get_current_reading(device_id)


@router.get("/{device_id}/temperature/history")
async def get_temperature_history(
    device_id: str,
    days: Optional[int] = Query(
        7, description="Number of days of history to return (default 7, max 30)"
    ),
    start_date: Optional[str] = Query(
        None, description="ISO format start date for custom date range"
    ),
    end_date: Optional[str] = Query(
        None, description="ISO format end date for custom date range"
    ),
    service: WaterHeaterTimeseriesService = Depends(lambda: timeseries_service),
):
    """
    Get temperature history for a water heater based on specified criteria.

    This endpoint is used by the History tab to display temperature charts
    for the selected time period.
    """
    # Parse date strings if provided
    start_datetime = datetime.fromisoformat(start_date) if start_date else None
    end_datetime = datetime.fromisoformat(end_date) if end_date else None

    # Use get_readings to match test expectations
    return service.get_readings(device_id, days, start_datetime, end_datetime)


@router.get("/{device_id}/temperature/history/preprocessed")
async def get_preprocessed_temperature_history(
    device_id: str,
    days: Optional[int] = Query(
        7, description="Number of days of history to return (default 7, max 30)"
    ),
    service: WaterHeaterTimeseriesService = Depends(lambda: timeseries_service),
):
    """
    Get preprocessed temperature history with appropriate downsampling based on time range.

    This endpoint is used for displaying large datasets more efficiently,
    with different downsampling strategies based on the time range.
    """
    # First get the readings, then apply preprocessing
    readings = service.get_readings(device_id, days)
    # Apply preprocessing based on the amount of data
    return service.preprocess_temperature_data(readings, days)


@router.get("/{device_id}/temperature/history/archived")
async def get_archived_temperature_history(
    device_id: str,
    start_date: str = Query(
        ..., description="ISO format start date for retrieving archived data"
    ),
    end_date: Optional[str] = Query(
        None, description="ISO format end date for retrieving archived data"
    ),
    service: WaterHeaterTimeseriesService = Depends(lambda: timeseries_service),
):
    """
    Get archived temperature history (data older than 30 days).

    This endpoint is used for retrieving historical data that has been
    moved to archive storage.
    """
    # Parse date strings
    start_datetime = datetime.fromisoformat(start_date)
    end_datetime = datetime.fromisoformat(end_date) if end_date else None

    return service.get_archived_readings(device_id, start_datetime, end_datetime)


@admin_router.post("/archive")
async def archive_old_readings(
    days: Optional[int] = Query(
        30, description="Number of days to keep in active storage (default 30)"
    ),
    service: WaterHeaterTimeseriesService = Depends(lambda: timeseries_service),
):
    """
    Archive readings older than the specified number of days.

    This endpoint is used by scheduled maintenance tasks to move old data
    from active to archive storage.
    """
    archived_count = service.archive_old_readings(days)

    return {
        "status": "success",
        "archived": archived_count,
        "message": f"Archived {archived_count} readings older than {days} days",
    }
