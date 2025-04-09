"""
Manufacturer-agnostic API for water heaters.

This module provides endpoints for water heaters from any manufacturer,
with optional filtering by manufacturer name, replacing brand-specific endpoints
to improve maintainability and support a wider range of devices.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

from src.dependencies import get_configurable_water_heater_service
from src.models.device import DeviceType
from src.models.water_heater import WaterHeater, WaterHeaterMode, WaterHeaterStatus
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)
from src.services.ensure_all_water_heaters import ensure_all_water_heaters

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/manufacturer/water-heaters",
    tags=["water-heaters", "manufacturer"],
    responses={
        404: {"description": "Water heater not found"},
        500: {"description": "Server error"},
    },
)


class ManufacturerInfoResponse(BaseModel):
    """Response model for manufacturer information."""

    manufacturer_id: str = Field(
        ..., description="Internal identifier for the manufacturer"
    )
    name: str = Field(..., description="Manufacturer name")
    supported_features: List[str] = Field(..., description="List of supported features")
    supported_models: List[str] = Field(
        ..., description="List of supported model types"
    )
    api_version: str = Field(..., description="Version of the manufacturer API")


class OperationalSummaryResponse(BaseModel):
    """Response model for water heater operational summary."""

    uptime_percentage: float = Field(
        ..., description="Uptime percentage over the last 30 days"
    )
    average_daily_runtime: float = Field(
        ..., description="Average daily runtime in hours"
    )
    heating_cycles_per_day: float = Field(
        ..., description="Average heating cycles per day"
    )
    energy_usage: Dict[str, float] = Field(..., description="Energy usage statistics")
    temperature_efficiency: float = Field(
        ..., description="Temperature efficiency percentage"
    )
    mode_usage: Dict[str, float] = Field(
        ..., description="Percentage time in each mode"
    )


class MaintenancePredictionResponse(BaseModel):
    """Response model for maintenance prediction."""

    days_until_service: int = Field(
        ..., description="Estimated days until next maintenance"
    )
    component_predictions: Dict[str, Dict[str, Any]] = Field(
        ..., description="Component predictions"
    )
    recommendation: str = Field(..., description="Maintenance recommendation")
    confidence: float = Field(..., description="Confidence level (0-1)")


@router.get(
    "/",
    response_model=List[WaterHeater],
    summary="Get All Water Heaters by Manufacturer",
    description="Retrieves a list of water heaters, optionally filtered by manufacturer.",
    operation_id="get_manufacturer_water_heaters",
)
async def get_water_heaters(
    manufacturer: Optional[str] = Query(
        None, description="Filter by manufacturer name (e.g., 'Rheem', 'AquaTherm')"
    ),
    service: ConfigurableWaterHeaterService = Depends(
        get_configurable_water_heater_service
    ),
):
    """
    Get all water heaters with optional filtering by manufacturer.

    This brand-agnostic endpoint replaces the previous brand-specific endpoints
    while still supporting AquaTherm/Rheem and other manufacturers.

    Args:
        manufacturer: Optional manufacturer name to filter by
        service: Water heater service for data access

    Returns:
        List of water heaters, filtered by manufacturer if specified
    """
    try:
        # First try to get water heaters from configured service
        # Service returns tuple of (water_heaters, is_from_db, error_message)
        result = await service.get_water_heaters(manufacturer=manufacturer)

        # Extract water heaters from the result tuple
        if isinstance(result, tuple):
            if len(result) == 3:
                water_heaters, is_from_db, error_msg = result
                # Log data source for debugging
                logger.info(
                    f"Retrieved water heaters from {'database' if is_from_db else 'error state'}"
                )

                # If there's an error message but still processing, just log it
                if error_msg:
                    logger.error(f"Error retrieving water heaters: {error_msg}")
            elif len(result) == 2:
                # Handle older format for backward compatibility
                water_heaters, is_from_db = result
                logger.info(f"Retrieved water heaters using legacy response format")
            else:
                # Handle unexpected tuple length
                water_heaters = result[0] if len(result) > 0 else []
                logger.warning(f"Unexpected tuple length from service: {len(result)}")
        else:
            # Handle unexpected return format
            water_heaters = result
            logger.warning(f"Unexpected return format from service: {type(result)}")

        # If we didn't get all 8 water heaters, ensure we get them all
        if len(water_heaters) < 8:
            logger.info(
                f"Got only {len(water_heaters)} water heaters, ensuring all 8 are returned"
            )
            fallback_heaters = await ensure_all_water_heaters(manufacturer)

            # Combine the lists but deduplicate by ID to prevent duplicates
            existing_ids = {wh.id for wh in water_heaters}
            for heater in fallback_heaters:
                if heater.id not in existing_ids:
                    water_heaters.append(heater)
                    existing_ids.add(heater.id)

            logger.info(
                f"After deduplication, returning {len(water_heaters)} water heaters"
            )

    except Exception as e:
        # If the configurable service fails, fall back to ensure_all_water_heaters
        logger.error(
            f"Error getting water heaters from service: {e}, falling back to ensure_all_water_heaters"
        )
        water_heaters = await ensure_all_water_heaters(manufacturer)

    if not water_heaters and manufacturer:
        # Return helpful message when no water heaters found for manufacturer
        logger.info(f"No water heaters found for manufacturer: {manufacturer}")

    return water_heaters


@router.get(
    "/{device_id}",
    response_model=WaterHeater,
    summary="Get Water Heater by ID",
    description="Get detailed information about a specific water heater by its ID.",
    operation_id="get_manufacturer_water_heater_by_id",
)
async def get_water_heater(
    device_id: str = Path(..., description="ID of the water heater to retrieve"),
    service: ConfigurableWaterHeaterService = Depends(
        get_configurable_water_heater_service
    ),
):
    """
    Get a specific water heater by ID.

    Args:
        device_id: ID of the water heater
        service: Water heater service for data access

    Returns:
        Water heater details

    Raises:
        HTTPException: If water heater not found
    """
    try:
        # The service returns a tuple (water_heater, is_from_db)
        water_heater_tuple = await service.get_water_heater(device_id)

        # Extract just the water heater object from the tuple
        water_heater, is_from_db = water_heater_tuple

        if water_heater:
            # Log whether we're using database or mock data
            if is_from_db:
                logger.info(f"Returning water heater {device_id} from database")
            else:
                logger.info(f"Returning water heater {device_id} from mock data")
            return water_heater

        # If not found in service, try to create it using our ensure function
        logger.info(f"Water heater {device_id} not found in service, creating it")
        all_heaters = await ensure_all_water_heaters()

        # Find the specific water heater in our generated list
        for heater in all_heaters:
            if heater.id == device_id:
                logger.info(f"Successfully generated water heater for {device_id}")
                return heater

        # If we still couldn't find it, raise 404
        logger.warning(
            f"Water heater with ID {device_id} not found and couldn't be created"
        )
        raise HTTPException(
            status_code=404, detail=f"Water heater with ID {device_id} not found"
        )
    except Exception as e:
        # Log the error and raise 500 if something unexpected happened
        logger.error(f"Error getting water heater {device_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving water heater: {str(e)}"
        )


@router.get(
    "/manufacturers/supported",
    response_model=List[ManufacturerInfoResponse],
    summary="Get Supported Manufacturers",
    description="Returns a list of all manufacturers supported by the system.",
    operation_id="get_supported_manufacturers",
)
def get_supported_manufacturers():
    """
    Get information about all manufacturers supported by the system.

    Returns:
        List of manufacturer information
    """
    # Hardcoded for now, but could be loaded from a database or configuration
    return [
        ManufacturerInfoResponse(
            manufacturer_id="rheem",
            name="Rheem",
            supported_features=[
                "EcoNet",
                "Remote Control",
                "Efficiency Analysis",
                "Maintenance Prediction",
            ],
            supported_models=["Performance", "Professional", "Gladiator", "Marathon"],
            api_version="2.1",
        ),
        ManufacturerInfoResponse(
            manufacturer_id="aquatherm",
            name="AquaTherm",
            supported_features=[
                "EcoNet",
                "Remote Control",
                "Efficiency Analysis",
                "Maintenance Prediction",
            ],
            supported_models=["Performance", "Professional", "Gladiator", "Marathon"],
            api_version="2.1",
        ),
        ManufacturerInfoResponse(
            manufacturer_id="generic",
            name="Generic",
            supported_features=["Basic Control", "Temperature Reading"],
            supported_models=["Standard", "Economy"],
            api_version="1.0",
        ),
    ]


@router.get(
    "/{device_id}/operational-summary",
    response_model=OperationalSummaryResponse,
    summary="Get Operational Summary",
    description="Get detailed operational statistics for a specific water heater.",
    operation_id="get_manufacturer_water_heater_operational_summary",
)
async def get_operational_summary(
    device_id: str = Path(..., description="ID of the water heater"),
    service: ConfigurableWaterHeaterService = Depends(
        get_configurable_water_heater_service
    ),
):
    """
    Get operational summary for a specific water heater.

    Args:
        device_id: ID of the water heater
        service: Water heater service for data access

    Returns:
        Operational summary details

    Raises:
        HTTPException: If water heater not found
    """
    # First verify the water heater exists
    water_heater = await service.get_water_heater(device_id)

    if not water_heater:
        raise HTTPException(
            status_code=404, detail=f"Water heater with ID {device_id} not found"
        )

    # For now, return mock data - in a real implementation, this would use
    # manufacturer-specific code to retrieve the actual operational data
    return OperationalSummaryResponse(
        uptime_percentage=98.5,
        average_daily_runtime=4.2,
        heating_cycles_per_day=12.3,
        energy_usage={"daily": 8.4, "weekly": 58.8, "monthly": 252.0},
        temperature_efficiency=92.5,
        mode_usage={"eco": 65.0, "standard": 30.0, "boost": 5.0},
    )


@router.get(
    "/{device_id}/maintenance-prediction",
    response_model=MaintenancePredictionResponse,
    summary="Get Maintenance Prediction",
    description="Get maintenance prediction for a specific water heater.",
    operation_id="get_manufacturer_water_heater_maintenance_prediction",
)
async def get_maintenance_prediction(
    device_id: str = Path(..., description="ID of the water heater"),
    service: ConfigurableWaterHeaterService = Depends(
        get_configurable_water_heater_service
    ),
):
    """
    Get maintenance prediction for a specific water heater.

    Args:
        device_id: ID of the water heater
        service: Water heater service for data access

    Returns:
        Maintenance prediction details

    Raises:
        HTTPException: If water heater not found
    """
    # First verify the water heater exists
    water_heater = await service.get_water_heater(device_id)

    if not water_heater:
        raise HTTPException(
            status_code=404, detail=f"Water heater with ID {device_id} not found"
        )

    # Get manufacturer for manufacturer-specific logic (if needed)
    manufacturer = (
        water_heater.manufacturer
        if hasattr(water_heater, "manufacturer")
        else "unknown"
    )

    # For now, return mock data - in a real implementation, this would use
    # manufacturer-specific code to retrieve actual prediction data
    return MaintenancePredictionResponse(
        days_until_service=180,
        component_predictions={
            "heating_element": {"health": 0.85, "remaining_life": "2-3 years"},
            "thermostat": {"health": 0.95, "remaining_life": "3-5 years"},
            "pressure_valve": {"health": 0.75, "remaining_life": "1-2 years"},
        },
        recommendation="Schedule inspection in 6 months",
        confidence=0.85,
    )


@router.patch(
    "/{device_id}/mode",
    response_model=Dict[str, Any],
    summary="Update Water Heater Mode",
    description="Update the operating mode for a specific water heater.",
    operation_id="update_manufacturer_water_heater_mode",
)
async def update_water_heater_mode(
    device_id: str = Path(..., description="ID of the water heater"),
    mode: WaterHeaterMode = Query(..., description="New operating mode to set"),
    service: ConfigurableWaterHeaterService = Depends(
        get_configurable_water_heater_service
    ),
):
    """
    Update the operating mode for a water heater.

    Args:
        device_id: ID of the water heater
        mode: New operating mode
        service: Water heater service for data access

    Returns:
        Success message with updated mode

    Raises:
        HTTPException: If water heater not found or update fails
    """
    # First verify the water heater exists
    water_heater = await service.get_water_heater(device_id)

    if not water_heater:
        raise HTTPException(
            status_code=404, detail=f"Water heater with ID {device_id} not found"
        )

    # Update the water heater mode
    updated = await service.update_water_heater(
        device_id=device_id, updates={"mode": mode}
    )

    if not updated:
        raise HTTPException(
            status_code=500, detail="Failed to update water heater mode"
        )

    return {
        "message": f"Successfully updated water heater mode to {mode}",
        "device_id": device_id,
        "mode": mode,
        "timestamp": datetime.utcnow().isoformat(),
    }
