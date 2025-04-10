"""
Water Heater Controller for handling HTTP requests.

This module contains the FastAPI route handlers for water heater operations.
Following Clean Architecture, controllers depend on use cases.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies.service_provider import get_water_heater_service
from src.api.models.water_heater_models import (
    ModeUpdate,
    TemperatureUpdate,
    WaterHeaterCreate,
    WaterHeaterResponse,
    WaterHeaterUpdate,
)
from src.domain.value_objects.temperature import Temperature
from src.domain.value_objects.water_heater_mode import WaterHeaterMode
from src.use_cases.water_heater_service import WaterHeaterService

# Create a router instance for water heater endpoints
router = APIRouter(prefix="/api/water-heaters", tags=["water-heaters"])


@router.get("/", response_model=List[WaterHeaterResponse])
def get_water_heaters(
    service: WaterHeaterService = Depends(get_water_heater_service),
) -> List[Dict[str, Any]]:
    """Get all water heaters.

    Args:
        service: Water heater service injected by dependency

    Returns:
        List of water heater response models
    """
    water_heaters = service.get_all_water_heaters()
    return [heater.to_dict() for heater in water_heaters]


@router.get("/{heater_id}", response_model=WaterHeaterResponse)
def get_water_heater_by_id(
    heater_id: str, service: WaterHeaterService = Depends(get_water_heater_service)
) -> Dict[str, Any]:
    """Get a water heater by ID.

    Args:
        heater_id: Water heater ID
        service: Water heater service injected by dependency

    Returns:
        Water heater response model

    Raises:
        HTTPException: If water heater not found
    """
    try:
        water_heater = service.get_water_heater_by_id(heater_id)
        return water_heater.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/", response_model=WaterHeaterResponse, status_code=status.HTTP_201_CREATED
)
def create_water_heater(
    water_heater_data: WaterHeaterCreate,
    service: WaterHeaterService = Depends(get_water_heater_service),
) -> Dict[str, Any]:
    """Create a new water heater.

    Args:
        water_heater_data: Water heater data to create
        service: Water heater service injected by dependency

    Returns:
        Created water heater response model

    Raises:
        HTTPException: If creation fails
    """
    try:
        # Convert Pydantic model to dictionary
        data_dict = water_heater_data.dict()

        # Create water heater through service
        water_heater = service.create_water_heater(data_dict)

        return water_heater.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{heater_id}/temperature", response_model=WaterHeaterResponse)
def update_water_heater_temperature(
    heater_id: str,
    temperature_data: TemperatureUpdate,
    service: WaterHeaterService = Depends(get_water_heater_service),
) -> Dict[str, Any]:
    """Update a water heater's target temperature.

    Args:
        heater_id: Water heater ID
        temperature_data: Temperature update data
        service: Water heater service injected by dependency

    Returns:
        Updated water heater response model

    Raises:
        HTTPException: If update fails or water heater not found
    """
    try:
        # Create temperature value object
        temperature = Temperature(
            value=temperature_data.target_temperature, unit=temperature_data.unit
        )

        # Update temperature through service
        water_heater = service.update_target_temperature(heater_id, temperature)

        return water_heater.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{heater_id}/mode", response_model=WaterHeaterResponse)
def update_water_heater_mode(
    heater_id: str,
    mode_data: ModeUpdate,
    service: WaterHeaterService = Depends(get_water_heater_service),
) -> Dict[str, Any]:
    """Update a water heater's operating mode.

    Args:
        heater_id: Water heater ID
        mode_data: Mode update data
        service: Water heater service injected by dependency

    Returns:
        Updated water heater response model

    Raises:
        HTTPException: If update fails or water heater not found
    """
    try:
        # Create mode value object
        mode = WaterHeaterMode(value=mode_data.mode)

        # Update mode through service
        water_heater = service.update_operating_mode(heater_id, mode)

        return water_heater.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{heater_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_water_heater(
    heater_id: str, service: WaterHeaterService = Depends(get_water_heater_service)
) -> None:
    """Delete a water heater.

    Args:
        heater_id: Water heater ID
        service: Water heater service injected by dependency

    Raises:
        HTTPException: If deletion fails or water heater not found
    """
    try:
        success = service.delete_water_heater(heater_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Water heater with ID {heater_id} not found",
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
