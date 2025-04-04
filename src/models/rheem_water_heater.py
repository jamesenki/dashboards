"""
Rheem water heater device models

This module contains Pydantic models for Rheem water heaters,
supporting various product lines including ProTerra hybrid models,
tankless models, and tank-type water heaters with EcoNet capabilities.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field

from src.models.device import Device, DeviceType
from src.models.water_heater import (
    WaterHeaterDiagnosticCode,
    WaterHeaterReading,
    WaterHeaterStatus,
)


class RheemWaterHeaterMode(str, Enum):
    """Rheem water heater operational modes based on ProTerra and other modern models"""

    # Standard modes
    OFF = "OFF"
    VACATION = "VACATION"

    # Efficiency modes
    ENERGY_SAVER = "ENERGY_SAVER"
    HEAT_PUMP = "HEAT_PUMP"
    ELECTRIC = "ELECTRIC"
    HIGH_DEMAND = "HIGH_DEMAND"

    # Legacy modes (for backward compatibility)
    ECO = "ECO"
    BOOST = "BOOST"


class RheemWaterHeaterType(str, Enum):
    """Rheem water heater type classification"""

    # Physical types
    TANK = "Tank"
    TANKLESS = "Tankless"
    HYBRID = "Hybrid"
    SOLAR = "Solar"

    # Market segments
    RESIDENTIAL = "Residential"
    COMMERCIAL = "Commercial"


class RheemProductSeries(str, Enum):
    """Rheem product series"""

    # Tank water heaters
    CLASSIC = "Classic"
    CLASSIC_PLUS = "Classic Plus"
    PRESTIGE = "Prestige"
    PROFESSIONAL = "Professional"

    # Tankless water heaters
    PERFORMANCE = "Performance"
    PERFORMANCE_PLATINUM = "Performance Platinum"

    # Hybrid water heaters
    PROTERRA = "ProTerra"


class RheemWaterHeaterReading(WaterHeaterReading):
    """Enhanced water heater readings for Rheem models with additional sensors"""

    # Additional Rheem-specific readings
    inlet_temperature: Optional[float] = Field(
        None, description="Temperature of incoming water in Celsius"
    )
    outlet_temperature: Optional[float] = Field(
        None, description="Temperature of outgoing water in Celsius"
    )
    ambient_temperature: Optional[float] = Field(
        None, description="Temperature of surrounding environment in Celsius"
    )
    humidity: Optional[float] = Field(None, description="Ambient humidity percentage")
    heating_element_status: Optional[str] = Field(
        None, description="Status of heating element (ON, OFF)"
    )
    compressor_status: Optional[str] = Field(
        None, description="Status of compressor for hybrid models (ON, OFF)"
    )
    power_source: Optional[str] = Field(
        None, description="Current power source being used (HEAT_PUMP, ELECTRIC, etc.)"
    )
    wifi_signal_strength: Optional[int] = Field(
        None, description="WiFi signal strength percentage"
    )
    total_energy_used: Optional[float] = Field(
        None, description="Cumulative energy consumption in kWh"
    )


class RheemWaterHeaterMaintenance(BaseModel):
    """Maintenance information for Rheem water heaters"""

    last_maintenance_date: Optional[datetime] = Field(
        None, description="Date of last maintenance service"
    )
    next_maintenance_date: Optional[datetime] = Field(
        None, description="Predicted date for next maintenance"
    )
    maintenance_history: List[Dict[str, Any]] = Field(
        default_factory=list, description="Historical maintenance records"
    )
    anode_rod_replacement_date: Optional[datetime] = Field(
        None, description="Date of last anode rod replacement"
    )
    filter_replacement_date: Optional[datetime] = Field(
        None, description="Date of last filter replacement"
    )
    descaling_date: Optional[datetime] = Field(
        None, description="Date of last descaling service"
    )
    warranty_expiration: Optional[datetime] = Field(
        None, description="Date when warranty expires"
    )
    installer_info: Optional[Dict[str, str]] = Field(
        None, description="Information about the installer"
    )


class RheemEcoNetStatus(BaseModel):
    """Status information for Rheem EcoNet connectivity"""

    connected: bool = Field(
        False, description="Whether the device is connected to EcoNet"
    )
    wifi_signal_strength: Optional[int] = Field(
        None, description="WiFi signal strength percentage"
    )
    last_connected: Optional[datetime] = Field(
        None, description="Last time device was connected to EcoNet"
    )
    firmware_version: Optional[str] = Field(
        None, description="Current EcoNet firmware version"
    )
    update_available: Optional[bool] = Field(
        None, description="Whether a firmware update is available"
    )
    remote_control_enabled: bool = Field(
        True, description="Whether remote control is enabled"
    )
    energy_usage_data: Optional[Dict[str, Any]] = Field(
        None, description="Energy usage data from EcoNet"
    )
    demand_response_enrolled: bool = Field(
        False, description="Whether enrolled in utility demand response program"
    )


class RheemWaterHeater(Device):
    """Rheem water heater device model with extended capabilities"""

    type: Literal[DeviceType.WATER_HEATER] = Field(
        DeviceType.WATER_HEATER, description="Device type"
    )

    # Manufacturer information
    manufacturer: str = Field("Rheem", description="Manufacturer name")
    series: RheemProductSeries = Field(..., description="Rheem product series")
    model_number: Optional[str] = Field(None, description="Model number")
    serial_number: Optional[str] = Field(None, description="Serial number")

    # Temperature settings
    target_temperature: float = Field(
        ..., description="Target water temperature in Celsius"
    )
    current_temperature: float = Field(
        ..., description="Current water temperature in Celsius"
    )
    min_temperature: float = Field(
        35.0, description="Minimum settable temperature in Celsius"
    )
    max_temperature: float = Field(
        85.0, description="Maximum settable temperature in Celsius"
    )

    # Operational settings
    mode: RheemWaterHeaterMode = Field(
        RheemWaterHeaterMode.ENERGY_SAVER, description="Current operational mode"
    )
    heater_status: WaterHeaterStatus = Field(
        WaterHeaterStatus.STANDBY, description="Current heater status"
    )
    heater_type: RheemWaterHeaterType = Field(..., description="Water heater type")

    # EcoNet smart features
    smart_enabled: bool = Field(
        False, description="Whether the water heater has EcoNet smart capabilities"
    )
    econet_status: Optional[RheemEcoNetStatus] = Field(
        None, description="EcoNet connectivity status"
    )
    leak_detection: Optional[bool] = Field(
        False, description="Whether the water heater has LeakGuard technology"
    )

    # Specifications
    capacity: Optional[float] = Field(
        None, description="Water tank capacity in gallons"
    )
    first_hour_rating: Optional[float] = Field(
        None, description="First hour rating in gallons"
    )
    uef_rating: Optional[float] = Field(
        None, description="Uniform Energy Factor rating"
    )
    energy_star_certified: Optional[bool] = Field(
        None, description="Whether the product is ENERGY STAR certified"
    )
    warranty_info: Optional[Dict[str, Any]] = Field(
        None, description="Warranty information"
    )
    installation_date: Optional[datetime] = Field(
        None, description="Date of installation"
    )

    # Maintenance information
    maintenance: RheemWaterHeaterMaintenance = Field(
        default_factory=RheemWaterHeaterMaintenance,
        description="Maintenance information",
    )

    # Telemetry and diagnostics
    readings: List[RheemWaterHeaterReading] = Field(
        default_factory=list, description="Historical sensor readings"
    )
    diagnostic_codes: List[WaterHeaterDiagnosticCode] = Field(
        default_factory=list, description="Diagnostic codes history"
    )

    def add_reading(self, reading: Union[WaterHeaterReading, RheemWaterHeaterReading]):
        """Add a sensor reading to the water heater and update current temperature."""
        self.readings.append(reading)
        self.current_temperature = reading.temperature

        # Automatically update heater status based on temperature
        if self.current_temperature >= self.target_temperature:
            self.heater_status = WaterHeaterStatus.STANDBY
        else:
            self.heater_status = WaterHeaterStatus.HEATING

        # Update EcoNet status if it's a smart-enabled model and the reading has wifi data
        if (
            self.smart_enabled
            and hasattr(reading, "wifi_signal_strength")
            and reading.wifi_signal_strength is not None
        ):
            if self.econet_status is None:
                self.econet_status = RheemEcoNetStatus()
            self.econet_status.wifi_signal_strength = reading.wifi_signal_strength
            self.econet_status.connected = reading.wifi_signal_strength > 0
            self.econet_status.last_connected = reading.timestamp

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
