"""
Water heater device model
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Literal

from pydantic import BaseModel, Field

from src.models.device import Device, DeviceType

class WaterHeaterMode(str, Enum):
    """Water heater operational mode"""
    ECO = "ECO"
    BOOST = "BOOST"
    OFF = "OFF"

class WaterHeaterStatus(str, Enum):
    """Water heater heater status"""
    HEATING = "HEATING"
    STANDBY = "STANDBY"

class WaterHeaterReading(BaseModel):
    """Water heater sensor reading"""
    timestamp: datetime = Field(..., description="Time of the reading")
    temperature: float = Field(..., description="Temperature reading in Celsius")
    pressure: Optional[float] = Field(None, description="Water pressure in bar")
    energy_usage: Optional[float] = Field(None, description="Energy usage in watts")
    flow_rate: Optional[float] = Field(None, description="Flow rate in liters per minute")

class WaterHeater(Device):
    """Water heater device model"""
    type: Literal[DeviceType.WATER_HEATER] = Field(DeviceType.WATER_HEATER, description="Device type")
    
    # Temperature settings
    target_temperature: float = Field(..., description="Target water temperature in Celsius")
    current_temperature: float = Field(..., description="Current water temperature in Celsius")
    min_temperature: float = Field(40.0, description="Minimum settable temperature in Celsius")
    max_temperature: float = Field(85.0, description="Maximum settable temperature in Celsius")
    
    # Operational settings
    mode: WaterHeaterMode = Field(WaterHeaterMode.ECO, description="Current operational mode")
    heater_status: WaterHeaterStatus = Field(WaterHeaterStatus.STANDBY, description="Current heater status")
    
    # Device specifications
    capacity: Optional[float] = Field(None, description="Water tank capacity in liters")
    efficiency_rating: Optional[float] = Field(None, description="Energy efficiency rating (0-1)")
    
    # Sensor readings history
    readings: List[WaterHeaterReading] = Field(default_factory=list, description="Historical sensor readings")
