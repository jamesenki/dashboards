"""
API models for water heater endpoints.

These Pydantic models define the request and response structures for
water heater API operations, following Clean Architecture by separating
the delivery mechanism from the use cases.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, validator


class WaterHeaterBase(BaseModel):
    """Base model with common water heater attributes."""

    name: str = Field(..., description="Human-readable name")
    manufacturer: str = Field(..., description="Manufacturer name")
    model: str = Field(..., description="Model identifier")
    location: Optional[str] = Field(None, description="Physical location description")
    is_simulated: bool = Field(False, description="Whether this is a simulated device")


class WaterHeaterCreate(WaterHeaterBase):
    """Model for creating a new water heater."""

    current_temperature: float = Field(..., description="Current water temperature")
    current_temperature_unit: Literal["C", "F"] = Field(
        "C", description="Temperature unit"
    )
    target_temperature: float = Field(..., description="Target water temperature")
    target_temperature_unit: Literal["C", "F"] = Field(
        "C", description="Temperature unit"
    )
    min_temperature: Optional[float] = Field(
        40.0, description="Minimum safe temperature"
    )
    max_temperature: Optional[float] = Field(
        85.0, description="Maximum safe temperature"
    )
    status: Optional[Literal["ONLINE", "OFFLINE", "MAINTENANCE", "ERROR"]] = Field(
        "ONLINE", description="Device operational status"
    )
    mode: Optional[Literal["ECO", "PERFORMANCE", "VACATION", "BOOST"]] = Field(
        "ECO", description="Operating mode"
    )

    @validator("current_temperature")
    def validate_current_temperature(cls, value):
        """Validate current temperature is in a reasonable range."""
        if value < 0 or value > 100:
            raise ValueError("Current temperature must be between 0 and 100")
        return value

    @validator("target_temperature")
    def validate_target_temperature(cls, value):
        """Validate target temperature is in a reasonable range."""
        if value < 0 or value > 100:
            raise ValueError("Target temperature must be between 0 and 100")
        return value


class WaterHeaterUpdate(BaseModel):
    """Model for updating an existing water heater."""

    name: Optional[str] = None
    location: Optional[str] = None
    status: Optional[Literal["ONLINE", "OFFLINE", "MAINTENANCE", "ERROR"]] = None


class TemperatureUpdate(BaseModel):
    """Model for updating a water heater's temperature."""

    target_temperature: float = Field(..., description="New target temperature")
    unit: Literal["C", "F"] = Field("C", description="Temperature unit")

    @validator("target_temperature")
    def validate_temperature(cls, value):
        """Validate temperature is in a reasonable range."""
        if value < 0 or value > 100:
            raise ValueError("Temperature must be between 0 and 100")
        return value


class ModeUpdate(BaseModel):
    """Model for updating a water heater's operating mode."""

    mode: Literal["ECO", "PERFORMANCE", "VACATION", "BOOST"] = Field(
        ..., description="New operating mode"
    )


class WaterHeaterResponse(WaterHeaterBase):
    """Model for water heater responses."""

    id: str = Field(..., description="Unique identifier")
    current_temperature: float = Field(..., description="Current water temperature")
    current_temperature_unit: str = Field(..., description="Temperature unit")
    target_temperature: float = Field(..., description="Target water temperature")
    target_temperature_unit: str = Field(..., description="Temperature unit")
    min_temperature: float = Field(..., description="Minimum safe temperature")
    max_temperature: float = Field(..., description="Maximum safe temperature")
    status: str = Field(..., description="Device operational status")
    mode: str = Field(..., description="Operating mode")
    health_status: str = Field(..., description="Maintenance health status")
    heater_status: str = Field(..., description="Heating element status")
    last_updated: Optional[datetime] = Field(
        None, description="Timestamp of last update"
    )

    class Config:
        """Pydantic model configuration."""

        orm_mode = True
