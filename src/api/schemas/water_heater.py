"""
Pydantic schemas for Water Heater API requests and responses.

These schemas define the structure of data for API requests and responses,
ensuring proper validation and documentation.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.models.water_heater import WaterHeaterMode, WaterHeaterStatus


class WaterHeaterCreate(BaseModel):
    """Schema for creating a new water heater."""

    name: str = Field(..., description="Name of the water heater")
    target_temperature: float = Field(
        default=45.0, description="Target temperature in Celsius", ge=30.0, le=85.0
    )
    mode: WaterHeaterMode = Field(
        default=WaterHeaterMode.ECO, description="Operating mode of the water heater"
    )
    min_temperature: Optional[float] = Field(
        default=40.0,
        description="Minimum allowed temperature in Celsius",
        ge=30.0,
        le=50.0,
    )
    max_temperature: Optional[float] = Field(
        default=85.0,
        description="Maximum allowed temperature in Celsius",
        ge=50.0,
        le=85.0,
    )


class TemperatureUpdate(BaseModel):
    """Schema for updating water heater temperature."""

    temperature: float = Field(
        ..., description="New target temperature in Celsius", ge=30.0, le=85.0
    )


class ModeUpdate(BaseModel):
    """Schema for updating water heater mode."""

    mode: WaterHeaterMode = Field(
        ..., description="New operating mode for the water heater"
    )


class TemperatureReading(BaseModel):
    """Schema for submitting a new temperature reading."""

    temperature: float = Field(
        ..., description="Current temperature in Celsius", ge=0.0, le=100.0
    )
    pressure: Optional[float] = Field(
        None, description="Water pressure in bar", ge=0.0, le=10.0
    )
    energy_usage: Optional[float] = Field(
        None, description="Energy usage in watts", ge=0.0
    )
    flow_rate: Optional[float] = Field(
        None, description="Water flow rate in liters per minute", ge=0.0, le=100.0
    )


class ApiSourceInfo(BaseModel):
    """Schema for API data source information."""

    source_type: str = Field(..., description="The type of data source (db, mock)")
    repository_type: str = Field(..., description="The type of repository being used")
    is_connected: bool = Field(..., description="Whether the data source is connected")
    water_heater_count: int = Field(
        ..., description="Number of water heaters available"
    )
    api_version: str = Field(..., description="API version identifier")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Timestamp of the information"
    )
