"""
Router for water heater API endpoints
"""
from typing import List, Optional

from fastapi import APIRouter, Body, HTTPException, Path, Query

from src.models.water_heater import WaterHeater, WaterHeaterMode
from src.services.water_heater import WaterHeaterService

router = APIRouter(prefix="/water-heaters", tags=["water-heaters"])
service = WaterHeaterService()


@router.get("/", response_model=List[WaterHeater])
async def get_water_heaters():
    """Get all water heaters"""
    return await service.get_water_heaters()


@router.get("/{device_id}", response_model=WaterHeater)
async def get_water_heater(
    device_id: str = Path(..., description="The ID of the water heater")
):
    """Get a specific water heater by ID"""
    water_heater = await service.get_water_heater(device_id)
    if not water_heater:
        raise HTTPException(status_code=404, detail="Water heater not found")
    return water_heater


@router.post("/", response_model=WaterHeater)
async def create_water_heater(water_heater: WaterHeater):
    """Create a new water heater"""
    try:
        return await service.create_water_heater(water_heater)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{device_id}/temperature", response_model=WaterHeater)
async def update_temperature(
    device_id: str = Path(..., description="The ID of the water heater"),
    temperature: float = Body(
        ..., embed=True, description="The new target temperature"
    ),
):
    """Update a water heater's target temperature"""
    try:
        water_heater = await service.update_target_temperature(device_id, temperature)
        if not water_heater:
            raise HTTPException(status_code=404, detail="Water heater not found")
        return water_heater
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{device_id}/mode", response_model=WaterHeater)
async def update_mode(
    device_id: str = Path(..., description="The ID of the water heater"),
    mode: WaterHeaterMode = Body(
        ..., embed=True, description="The new operational mode"
    ),
):
    """Update a water heater's operational mode"""
    water_heater = await service.update_mode(device_id, mode)
    if not water_heater:
        raise HTTPException(status_code=404, detail="Water heater not found")
    return water_heater


@router.post("/{device_id}/readings", response_model=WaterHeater)
async def add_reading(
    device_id: str = Path(..., description="The ID of the water heater"),
    temperature: float = Body(..., description="The current temperature"),
    pressure: Optional[float] = Body(None, description="The current pressure (bar)"),
    energy_usage: Optional[float] = Body(
        None, description="The current energy usage (watts)"
    ),
    flow_rate: Optional[float] = Body(
        None, description="The current flow rate (L/min)"
    ),
):
    """Add a temperature reading to a water heater"""
    water_heater = await service.add_temperature_reading(
        device_id, temperature, pressure, energy_usage, flow_rate
    )
    if not water_heater:
        raise HTTPException(status_code=404, detail="Water heater not found")
    return water_heater
