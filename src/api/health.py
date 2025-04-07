"""
Health Check API endpoints for application status monitoring.

These endpoints provide health and status information about various components
of the application, including database connections and data source details.
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

# Create a dedicated health API router at /api/health
router = APIRouter(
    prefix="/api/health",
    tags=["monitoring", "health"],
    responses={
        500: {"description": "Server error"},
    },
)


@router.get(
    "/data-source",
    response_model=Dict[str, Any],
    summary="Data source information",
    operation_id="get_data_source_info",
)
async def get_data_source() -> Dict[str, Any]:
    """
    Get information about the current data source being used.

    This endpoint is used by the data-source-indicator component to
    show whether the system is using PostgreSQL, SQLite, or mock data.

    Returns:
        Dictionary with data source information.
    """
    # Get base data source info
    data_source_info = ConfigurableWaterHeaterService.get_data_source_info()

    # Determine specific database type when not using mock data
    if not data_source_info["is_using_mock_data"]:
        if db_settings.DB_TYPE == "postgres":
            db_type = "PostgreSQL"
        elif db_settings.DB_TYPE == "sqlite":
            db_type = "SQLite"
        elif db_settings.DB_TYPE == "memory":
            db_type = "In-Memory SQLite"
        else:
            db_type = db_settings.DB_TYPE.capitalize()
    else:
        db_type = "Mock"

    # Build enhanced response
    return {
        "is_using_mock_data": data_source_info["is_using_mock_data"],
        "data_source": db_type,
        "reason": data_source_info["data_source_reason"],
        "timestamp": data_source_info["timestamp"],
        "db_settings": {
            "type": db_settings.DB_TYPE,
            "host": db_settings.DB_HOST if db_settings.DB_TYPE == "postgres" else "N/A",
            "database": db_settings.DB_NAME,
            "fallback_enabled": db_settings.FALLBACK_TO_MOCK,
        },
    }


@router.get(
    "/status",
    response_model=Dict[str, Any],
    summary="Application health status",
    operation_id="get_health_status",
)
async def get_health_status(
    service: ConfigurableWaterHeaterService = Depends(get_service),
) -> Dict[str, Any]:
    """
    Get overall application health status.

    This endpoint checks various components of the application and returns
    a comprehensive health report.

    Returns:
        Dictionary with health status information.
    """
    try:
        # Get environment
        env = os.environ.get("IOTSPHERE_ENV", "development")

        # Get data source information
        data_source_info = await get_data_source()

        # Perform quick query to verify DB connection
        water_heaters = await service.get_water_heaters()
        count = (
            len(water_heaters[0])
            if isinstance(water_heaters, tuple)
            else len(water_heaters)
        )

        # Build response
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "environment": env,
            "database": {
                "type": db_settings.DB_TYPE,
                "connection": "connected",
                "water_heater_count": count,
            },
            "data_source": data_source_info,
            "api_version": "1.0.0",
        }
    except Exception as e:
        # If an error occurs, return error status
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "data_source": {
                "is_using_mock_data": ConfigurableWaterHeaterService.is_using_mock_data,
                "data_source": "Mock"
                if ConfigurableWaterHeaterService.is_using_mock_data
                else "Unknown",
                "reason": ConfigurableWaterHeaterService.data_source_reason,
            },
        }
