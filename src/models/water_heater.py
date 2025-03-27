"""
Water heater device model
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Literal, Dict, Any

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
    
class WaterHeaterType(str, Enum):
    """Water heater type classification"""
    COMMERCIAL = "Commercial"
    RESIDENTIAL = "Residential"

class WaterHeaterDiagnosticCode(BaseModel):
    """Water heater diagnostic code"""
    code: str = Field(..., description="Diagnostic code identifier")
    description: str = Field(..., description="Human-readable description")
    severity: str = Field(..., description="Severity level (Info, Warning, Critical, Maintenance)")
    timestamp: datetime = Field(..., description="Time the diagnostic code was generated")
    active: bool = Field(True, description="Whether the code is currently active")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional diagnostic data")

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
    
    # New: Water heater type classification
    heater_type: WaterHeaterType = Field(WaterHeaterType.RESIDENTIAL, description="Water heater type (Commercial or Residential)")
    
    # New: Link to detailed specifications
    specification_link: Optional[str] = Field(None, description="Link to detailed specifications document")
    
    # Device specifications
    capacity: Optional[float] = Field(None, description="Water tank capacity in liters")
    efficiency_rating: Optional[float] = Field(None, description="Energy efficiency rating (0-1)")
    
    # Sensor readings history
    readings: List[WaterHeaterReading] = Field(default_factory=list, description="Historical sensor readings")
    
    # New: Diagnostic codes history
    diagnostic_codes: List[WaterHeaterDiagnosticCode] = Field(default_factory=list, description="Diagnostic codes history")
    
    def add_reading(self, reading: WaterHeaterReading):
        """Add a sensor reading to the water heater and update current temperature."""
        self.readings.append(reading)
        self.current_temperature = reading.temperature
        
        # Automatically update heater status based on temperature
        if self.current_temperature >= self.target_temperature:
            self.heater_status = WaterHeaterStatus.STANDBY
        else:
            self.heater_status = WaterHeaterStatus.HEATING
    
    def add_diagnostic_code(self, diagnostic_code: WaterHeaterDiagnosticCode):
        """Add a diagnostic code to the water heater."""
        self.diagnostic_codes.append(diagnostic_code)
    
    def resolve_diagnostic_code(self, code: str):
        """Mark a diagnostic code as resolved/inactive."""
        for diagnostic in self.diagnostic_codes:
            if diagnostic.code == code and diagnostic.active:
                diagnostic.active = False
                return True
        return False
    
    def get_active_diagnostic_codes(self) -> List[WaterHeaterDiagnosticCode]:
        """Get all currently active diagnostic codes."""
        return [diagnostic for diagnostic in self.diagnostic_codes if diagnostic.active]
