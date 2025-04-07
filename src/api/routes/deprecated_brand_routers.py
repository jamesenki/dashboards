"""
Deprecated brand-specific API routes that redirect to manufacturer-agnostic routes.

This module contains redirecting routers for brand-specific water heater endpoints,
marking them as deprecated while maintaining backward compatibility.
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from fastapi.responses import RedirectResponse

from src.dependencies import get_configurable_water_heater_service
from src.models.water_heater import WaterHeater, WaterHeaterMode
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)

logger = logging.getLogger(__name__)

# Create deprecated Rheem router - include_in_schema=False hides from OpenAPI docs
rheem_router = APIRouter(
    prefix="/api/rheem-water-heaters",
    tags=["deprecated"],
    responses={404: {"description": "Not found"}},
    deprecated=True,
    include_in_schema=False,  # Hide from OpenAPI docs
)

# Create deprecated AquaTherm router - include_in_schema=False hides from OpenAPI docs
aquatherm_router = APIRouter(
    prefix="/aquatherm-water-heaters",
    tags=["deprecated"],
    responses={404: {"description": "Not found"}},
    deprecated=True,
    include_in_schema=False,  # Hide from OpenAPI docs
)

# Generic message about redirection
DEPRECATION_MESSAGE = (
    "This endpoint is deprecated. Please use the manufacturer-agnostic version at {}"
)


@rheem_router.get(
    "/",
    response_model=List[WaterHeater],
    summary="[DEPRECATED] Get All Rheem Water Heaters",
    description="This endpoint is deprecated. Please use the manufacturer-agnostic endpoint at /api/manufacturer/water-heaters/?manufacturer=Rheem instead.",
)
async def get_all_rheem_water_heaters(
    response: Response,
    service: ConfigurableWaterHeaterService = Depends(
        get_configurable_water_heater_service
    ),
):
    """
    [DEPRECATED] Get all Rheem water heaters.

    This endpoint is maintained for backward compatibility only.
    New code should use the manufacturer-agnostic endpoint.

    Returns:
        List of Rheem water heaters
    """
    response.headers["Deprecation"] = "true"
    response.headers[
        "Link"
    ] = '</api/manufacturer/water-heaters/?manufacturer=Rheem>; rel="successor-version"'
    response.headers["Warning"] = '299 - "This endpoint is deprecated"'

    return await service.get_water_heaters(manufacturer="Rheem")


@rheem_router.get(
    "/{device_id}",
    response_model=WaterHeater,
    summary="[DEPRECATED] Get Rheem Water Heater by ID",
    description="This endpoint is deprecated. Please use the manufacturer-agnostic endpoint at /api/manufacturer/water-heaters/{device_id} instead.",
)
async def get_rheem_water_heater(
    device_id: str,
    response: Response,
    service: ConfigurableWaterHeaterService = Depends(
        get_configurable_water_heater_service
    ),
):
    """
    [DEPRECATED] Get a specific Rheem water heater by ID.

    This endpoint is maintained for backward compatibility only.
    New code should use the manufacturer-agnostic endpoint.

    Args:
        device_id: ID of the water heater

    Returns:
        Water heater details

    Raises:
        HTTPException: If water heater not found
    """
    response.headers["Deprecation"] = "true"
    response.headers[
        "Link"
    ] = f'</api/manufacturer/water-heaters/{device_id}>; rel="successor-version"'
    response.headers["Warning"] = '299 - "This endpoint is deprecated"'

    water_heater = await service.get_water_heater(device_id)

    if not water_heater:
        raise HTTPException(
            status_code=404, detail=f"Water heater with ID {device_id} not found"
        )

    # Check if it's actually a Rheem water heater
    if water_heater.manufacturer.lower() != "rheem":
        raise HTTPException(
            status_code=404,
            detail=f"The water heater with ID {device_id} is not a Rheem water heater",
        )

    return water_heater


@rheem_router.patch(
    "/{device_id}/mode",
    response_model=Dict[str, Any],
    summary="[DEPRECATED] Update Rheem Water Heater Mode",
    description="This endpoint is deprecated. Please use the manufacturer-agnostic endpoint at /api/manufacturer/water-heaters/{device_id}/mode instead.",
)
async def set_rheem_water_heater_mode(
    device_id: str,
    response: Response,
    mode: WaterHeaterMode = Query(...),
    service: ConfigurableWaterHeaterService = Depends(
        get_configurable_water_heater_service
    ),
):
    """
    [DEPRECATED] Update the operating mode for a Rheem water heater.

    This endpoint is maintained for backward compatibility only.
    New code should use the manufacturer-agnostic endpoint.

    Args:
        device_id: ID of the water heater
        mode: New operating mode

    Returns:
        Redirect to the manufacturer-agnostic endpoint
    """
    redirect_url = f"/api/manufacturer/water-heaters/{device_id}/mode?mode={mode}"
    return RedirectResponse(url=redirect_url, status_code=307)


# AquaTherm endpoints (similar pattern as Rheem)
@aquatherm_router.get(
    "/",
    response_model=List[WaterHeater],
    summary="[DEPRECATED] Get All AquaTherm Water Heaters",
    description="This endpoint is deprecated. Please use the manufacturer-agnostic endpoint at /api/manufacturer/water-heaters/?manufacturer=AquaTherm instead.",
)
async def get_all_aquatherm_water_heaters(
    response: Response,
    service: ConfigurableWaterHeaterService = Depends(
        get_configurable_water_heater_service
    ),
):
    """
    [DEPRECATED] Get all AquaTherm water heaters.

    This endpoint is maintained for backward compatibility only.
    New code should use the manufacturer-agnostic endpoint.

    Returns:
        List of AquaTherm water heaters
    """
    response.headers["Deprecation"] = "true"
    response.headers[
        "Link"
    ] = '</api/manufacturer/water-heaters/?manufacturer=AquaTherm>; rel="successor-version"'
    response.headers["Warning"] = '299 - "This endpoint is deprecated"'

    return await service.get_water_heaters(manufacturer="AquaTherm")


@aquatherm_router.get(
    "/{device_id}",
    response_model=WaterHeater,
    summary="[DEPRECATED] Get AquaTherm Water Heater by ID",
    description="This endpoint is deprecated. Please use the manufacturer-agnostic endpoint at /api/manufacturer/water-heaters/{device_id} instead.",
)
async def get_aquatherm_water_heater(
    device_id: str,
    response: Response,
    service: ConfigurableWaterHeaterService = Depends(
        get_configurable_water_heater_service
    ),
):
    """
    [DEPRECATED] Get a specific AquaTherm water heater by ID.

    This endpoint is maintained for backward compatibility only.
    New code should use the manufacturer-agnostic endpoint.

    Args:
        device_id: ID of the water heater

    Returns:
        Water heater details

    Raises:
        HTTPException: If water heater not found
    """
    response.headers["Deprecation"] = "true"
    response.headers[
        "Link"
    ] = f'</api/manufacturer/water-heaters/{device_id}>; rel="successor-version"'
    response.headers["Warning"] = '299 - "This endpoint is deprecated"'

    water_heater = await service.get_water_heater(device_id)

    if not water_heater:
        raise HTTPException(
            status_code=404, detail=f"Water heater with ID {device_id} not found"
        )

    # Check if it's actually an AquaTherm water heater
    if water_heater.manufacturer.lower() != "aquatherm":
        raise HTTPException(
            status_code=404,
            detail=f"The water heater with ID {device_id} is not an AquaTherm water heater",
        )

    return water_heater


@aquatherm_router.patch(
    "/{device_id}/mode",
    response_model=Dict[str, Any],
    summary="[DEPRECATED] Update AquaTherm Water Heater Mode",
    description="This endpoint is deprecated. Please use the manufacturer-agnostic endpoint at /api/manufacturer/water-heaters/{device_id}/mode instead.",
)
async def set_aquatherm_water_heater_mode(
    device_id: str,
    response: Response,
    mode: WaterHeaterMode = Query(...),
    service: ConfigurableWaterHeaterService = Depends(
        get_configurable_water_heater_service
    ),
):
    """
    [DEPRECATED] Update the operating mode for an AquaTherm water heater.

    This endpoint is maintained for backward compatibility only.
    New code should use the manufacturer-agnostic endpoint.

    Args:
        device_id: ID of the water heater
        mode: New operating mode

    Returns:
        Redirect to the manufacturer-agnostic endpoint
    """
    redirect_url = f"/api/manufacturer/water-heaters/{device_id}/mode?mode={mode}"
    return RedirectResponse(url=redirect_url, status_code=307)
