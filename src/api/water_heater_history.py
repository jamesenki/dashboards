"""
API endpoints for water heater history
"""
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Path, Query

from src.services.water_heater_history import WaterHeaterHistoryService

router = APIRouter(prefix="/api", tags=["water_heater_history"])


@router.get("/water-heaters/{heater_id}/history", response_model=Dict[str, Any])
async def get_history_dashboard(
    heater_id: str = Path(..., description="ID of the water heater"),
    days: int = Query(7, description="Number of days of history to retrieve"),
):
    """
    Get the complete history dashboard data for a water heater

    Args:
        heater_id: The ID of the water heater to get history for
        days: Number of days of history to retrieve (default: 7)

    Returns:
        Complete history dashboard data
    """
    try:
        history_service = WaterHeaterHistoryService()
        result = await history_service.get_history_dashboard(heater_id, days)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"Water heater with ID {heater_id} not found"
        )


@router.get(
    "/water-heaters/{heater_id}/history/temperature", response_model=Dict[str, Any]
)
async def get_temperature_history(
    heater_id: str = Path(..., description="ID of the water heater"),
    days: int = Query(7, description="Number of days of history to retrieve"),
):
    """
    Get temperature history data for a water heater

    Args:
        heater_id: The ID of the water heater to get history for
        days: Number of days of history to retrieve (default: 7)

    Returns:
        Chart data for temperature history
    """
    try:
        history_service = WaterHeaterHistoryService()
        result = await history_service.get_temperature_history(heater_id, days)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"Water heater with ID {heater_id} not found"
        )


@router.get("/water-heaters/{heater_id}/history/energy", response_model=Dict[str, Any])
async def get_energy_usage_history(
    heater_id: str = Path(..., description="ID of the water heater"),
    days: int = Query(7, description="Number of days of history to retrieve"),
):
    """
    Get energy usage history data for a water heater

    Args:
        heater_id: The ID of the water heater to get history for
        days: Number of days of history to retrieve (default: 7)

    Returns:
        Chart data for energy usage history
    """
    try:
        history_service = WaterHeaterHistoryService()
        result = await history_service.get_energy_usage_history(heater_id, days)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"Water heater with ID {heater_id} not found"
        )


@router.get(
    "/water-heaters/{heater_id}/history/pressure-flow", response_model=Dict[str, Any]
)
async def get_pressure_flow_history(
    heater_id: str = Path(..., description="ID of the water heater"),
    days: int = Query(7, description="Number of days of history to retrieve"),
):
    """
    Get pressure and flow rate history data for a water heater

    Args:
        heater_id: The ID of the water heater to get history for
        days: Number of days of history to retrieve (default: 7)

    Returns:
        Chart data for pressure and flow rate history
    """
    try:
        history_service = WaterHeaterHistoryService()
        result = await history_service.get_pressure_flow_history(heater_id, days)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"Water heater with ID {heater_id} not found"
        )
