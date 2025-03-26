from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field

# Using absolute imports to ensure consistency
from src.models.device import DeviceType, DeviceStatus
from src.models.water_heater import (
    WaterHeaterMode, 
    WaterHeaterStatus,
    WaterHeaterReading,
    WaterHeater
)
from src.services.water_heater import WaterHeaterService


# API Models
class WaterHeaterCreate(BaseModel):
    """Schema for creating a new water heater."""
    name: str = Field(..., description="Name of the water heater")
    target_temperature: float = Field(
        default=45.0,
        description="Target temperature in Celsius",
        ge=30.0,
        le=85.0
    )
    mode: WaterHeaterMode = Field(
        default=WaterHeaterMode.ECO,
        description="Operating mode of the water heater"
    )
    min_temperature: Optional[float] = Field(
        default=40.0,
        description="Minimum allowed temperature in Celsius",
        ge=30.0,
        le=50.0
    )
    max_temperature: Optional[float] = Field(
        default=85.0,
        description="Maximum allowed temperature in Celsius",
        ge=50.0,
        le=85.0
    )


class TemperatureUpdate(BaseModel):
    """Schema for updating water heater temperature."""
    temperature: float = Field(
        ...,
        description="New target temperature in Celsius",
        ge=30.0,
        le=85.0
    )


class ModeUpdate(BaseModel):
    """Schema for updating water heater mode."""
    mode: WaterHeaterMode = Field(
        ...,
        description="New operating mode for the water heater"
    )


class TemperatureReading(BaseModel):
    """Schema for submitting a new temperature reading."""
    temperature: float = Field(
        ...,
        description="Current temperature in Celsius",
        ge=0.0,
        le=100.0
    )
    pressure: Optional[float] = Field(
        None,
        description="Water pressure in bar",
        ge=0.0,
        le=10.0
    )
    energy_usage: Optional[float] = Field(
        None,
        description="Energy usage in watts",
        ge=0.0
    )
    flow_rate: Optional[float] = Field(
        None,
        description="Water flow rate in liters per minute",
        ge=0.0,
        le=100.0
    )


# Dependency Injection
def get_water_heater_service():
    """Dependency to get the water heater service."""
    return WaterHeaterService()


# Router
router = APIRouter(prefix="/water-heaters", tags=["water-heaters"])


@router.get("/", response_model=List[WaterHeater])
async def get_water_heaters(
    service: WaterHeaterService = Depends(get_water_heater_service)
):
    """Get all water heaters."""
    heaters = await service.get_water_heaters()
    print(f"API: Returning {len(heaters)} water heaters")
    for i, h in enumerate(heaters):
        print(f"API: Heater {i+1}: id={h.id}, name={h.name}, status={h.status}")
    return heaters


@router.get("/{device_id}", response_model=WaterHeater)
async def get_water_heater(
    device_id: str = Path(..., description="ID of the water heater"),
    service: WaterHeaterService = Depends(get_water_heater_service)
):
    """Get a specific water heater by ID."""
    water_heater = await service.get_water_heater(device_id)
    if not water_heater:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Water heater with ID {device_id} not found"
        )
    return water_heater


@router.post("/", response_model=WaterHeater, status_code=status.HTTP_201_CREATED)
async def create_water_heater(
    water_heater_data: WaterHeaterCreate,
    service: WaterHeaterService = Depends(get_water_heater_service)
):
    """Create a new water heater."""
    # Create a water heater model from the input data
    water_heater = WaterHeater(
        name=water_heater_data.name,
        type=DeviceType.WATER_HEATER,
        status=DeviceStatus.ONLINE,
        target_temperature=water_heater_data.target_temperature,
        current_temperature=water_heater_data.target_temperature,  # Initially same as target
        mode=water_heater_data.mode,
        heater_status=WaterHeaterStatus.STANDBY,
        min_temperature=water_heater_data.min_temperature,
        max_temperature=water_heater_data.max_temperature,
        readings=[]  # Initialize with empty readings list
    )
    
    # Create the water heater
    created_heater = await service.create_water_heater(water_heater)
    return created_heater


@router.patch("/{device_id}/temperature", response_model=WaterHeater)
async def update_target_temperature(
    temperature_data: TemperatureUpdate,
    device_id: str = Path(..., description="ID of the water heater"),
    service: WaterHeaterService = Depends(get_water_heater_service)
):
    """Update a water heater's target temperature."""
    # Check if the water heater exists
    water_heater = await service.get_water_heater(device_id)
    if not water_heater:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Water heater with ID {device_id} not found"
        )
    
    try:
        # Update the temperature
        updated_heater = await service.update_target_temperature(
            device_id, temperature_data.temperature
        )
        return updated_heater
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{device_id}/mode", response_model=WaterHeater)
async def update_mode(
    mode_data: ModeUpdate,
    device_id: str = Path(..., description="ID of the water heater"),
    service: WaterHeaterService = Depends(get_water_heater_service)
):
    """Update a water heater's operating mode."""
    # Check if the water heater exists
    water_heater = await service.get_water_heater(device_id)
    if not water_heater:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Water heater with ID {device_id} not found"
        )
    
    # Update the mode
    updated_heater = await service.update_mode(device_id, mode_data.mode)
    return updated_heater


@router.post("/{device_id}/readings", response_model=WaterHeater)
async def add_reading(
    reading_data: TemperatureReading,
    device_id: str = Path(..., description="ID of the water heater"),
    service: WaterHeaterService = Depends(get_water_heater_service)
):
    """Add a new temperature reading to a water heater."""
    # Check if the water heater exists
    water_heater = await service.get_water_heater(device_id)
    if not water_heater:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Water heater with ID {device_id} not found"
        )
    
    # Add the reading
    updated_heater = await service.add_temperature_reading(
        device_id,
        temperature=reading_data.temperature,
        pressure=reading_data.pressure,
        energy_usage=reading_data.energy_usage,
        flow_rate=reading_data.flow_rate
    )
    
    return updated_heater
