"""
Health Check Router for Water Heater API

This router provides health and status endpoints to monitor the database connection
and application configuration.
"""
import os
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from src.api.water_heater.dependencies import get_service
from src.db.config import db_settings
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)

router = APIRouter(prefix="/water-heater", tags=["monitoring"])


@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Database and service health check",
    operation_id="check_water_heater_health",
)
async def check_database_health(
    service: ConfigurableWaterHeaterService = Depends(get_service),
) -> Dict[str, Any]:
    """
    Check the health of the water heater service and database connection.

    Returns:
        Dictionary with health check results including:
        - status: "ok" or "error"
        - timestamp: Current time
        - environment: Current environment (development, testing)
        - database: Information about the database connection
        - data: Information about available data
    """
    try:
        # Get data source information
        data_source = ConfigurableWaterHeaterService.get_data_source_info()

        # Get environment
        env = os.environ.get("IOTSPHERE_ENV", "development")

        # Perform quick DB query to verify connection
        water_heaters = await service.get_water_heaters()
        count = (
            len(water_heaters[0])
            if isinstance(water_heaters, tuple)
            else len(water_heaters)
        )

        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "environment": env,
            "database": {
                "type": "mock"
                if data_source["is_using_mock_data"]
                else db_settings.DB_TYPE,
                "using_mock_data": data_source["is_using_mock_data"],
                "reason": data_source["data_source_reason"],
                "connection": "ok",
            },
            "data": {
                "water_heaters_count": count,
            },
        }
    except Exception as e:
        # If there's an error, return error status
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "database": {
                "connection": "failed",
                "using_mock_data": ConfigurableWaterHeaterService.is_using_mock_data,
            },
        }


@router.get(
    "/data-source-status",
    response_model=Dict[str, Any],
    summary="Data source status information",
    operation_id="get_data_source_status",
)
async def get_data_source_status() -> Dict[str, Any]:
    """
    Get information about the current data source being used.

    This endpoint is used by the data-source-indicator component to
    show whether the system is using mock data or a real database.

    Returns:
        Dictionary with data source information.
    """
    return ConfigurableWaterHeaterService.get_data_source_info()
