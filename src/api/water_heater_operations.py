"""
API endpoints for water heater operations.
Provides data for the operations dashboard display.
"""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Path, status

from src.services.water_heater_operations_service import WaterHeaterOperationsService


# Dependency injection
def get_water_heater_operations_service():
    """Dependency to get the water heater operations service."""
    return WaterHeaterOperationsService()


# Router
router = APIRouter(prefix="/water-heaters", tags=["water-heaters", "operations"])


@router.get("/{heater_id}/operations", response_model=Dict[str, Any])
async def get_operations_dashboard(
    heater_id: str = Path(..., description="ID of the water heater"),
    service: WaterHeaterOperationsService = Depends(
        get_water_heater_operations_service
    ),
):
    """
    Get operations dashboard data for a specific water heater.

    This endpoint provides comprehensive data for the real-time operations
    dashboard, including:
    - Current machine status
    - Heater status (heating/standby)
    - Temperature readings
    - Pressure readings
    - Energy usage
    - Flow rate
    - Overall asset health score

    Args:
        heater_id: ID of the water heater to get operations data for

    Returns:
        Dictionary containing formatted operations dashboard data

    Raises:
        HTTPException: If water heater with specified ID is not found
    """
    dashboard_data = await service.get_operations_dashboard(heater_id)

    if not dashboard_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Water heater with ID {heater_id} not found",
        )

    return dashboard_data
