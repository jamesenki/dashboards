"""
Water Heater entity representing a smart water heater device.

This entity encapsulates the core business rules for water heaters.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional

from src.domain.value_objects.device_status import DeviceStatus
from src.domain.value_objects.maintenance_status import MaintenanceStatus
from src.domain.value_objects.temperature import Temperature
from src.domain.value_objects.water_heater_mode import WaterHeaterMode


@dataclass
class WaterHeater:
    """Entity representing a water heater device.

    This is a core domain entity that contains the business rules for water heaters.
    It ensures that water heaters maintain safe temperature ranges and tracks operational
    status and mode.

    Attributes:
        id: Unique identifier for the water heater
        name: Human-readable name
        manufacturer: Manufacturer name
        model: Model identifier
        current_temperature: Current water temperature
        target_temperature: Target/desired water temperature
        min_temperature: Minimum safe temperature
        max_temperature: Maximum safe temperature
        status: Device operational status (online, offline, etc.)
        mode: Operating mode (eco, performance, etc.)
        health_status: Maintenance health status
        location: Physical location description
        heater_status: Heating element status (HEATING, STANDBY, OFF)
        is_simulated: Whether this is a simulated device
        last_updated: Timestamp of last update
    """

    id: str
    name: str
    manufacturer: str
    model: str
    current_temperature: Temperature
    target_temperature: Temperature
    min_temperature: Temperature = field(default_factory=lambda: Temperature(40.0, "C"))
    max_temperature: Temperature = field(default_factory=lambda: Temperature(85.0, "C"))
    status: DeviceStatus = field(default_factory=lambda: DeviceStatus("ONLINE"))
    mode: WaterHeaterMode = field(default_factory=lambda: WaterHeaterMode("ECO"))
    health_status: MaintenanceStatus = field(
        default_factory=lambda: MaintenanceStatus("GREEN")
    )
    location: Optional[str] = None
    heater_status: Literal["HEATING", "STANDBY", "OFF"] = "STANDBY"
    is_simulated: bool = False
    last_updated: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate the water heater attributes after initialization."""
        # Validate temperature relationships
        min_temp = self.min_temperature.to_celsius().value
        max_temp = self.max_temperature.to_celsius().value
        current_temp = self.current_temperature.to_celsius().value
        target_temp = self.target_temperature.to_celsius().value

        if min_temp >= max_temp:
            raise ValueError(
                f"Minimum temperature ({min_temp}°C) must be less than maximum temperature ({max_temp}°C)"
            )

        if target_temp < min_temp or target_temp > max_temp:
            raise ValueError(
                f"Target temperature ({target_temp}°C) must be between {min_temp}°C and {max_temp}°C"
            )

        # Initialize heater status based on temperatures
        self._update_heater_status()

    def set_target_temperature(self, temperature: Temperature) -> None:
        """Set the target temperature, ensuring it's within safe limits.

        Args:
            temperature: The new target temperature

        Raises:
            ValueError: If temperature is outside safe range
        """
        # Convert to celsius for comparison
        temp_c = temperature.to_celsius().value
        min_temp = self.min_temperature.to_celsius().value
        max_temp = self.max_temperature.to_celsius().value

        # Validate temperature is within safe range
        if temp_c < min_temp or temp_c > max_temp:
            raise ValueError(
                f"Target temperature ({temp_c}°C) must be between {min_temp}°C and {max_temp}°C"
            )

        # Update the target temperature
        self.target_temperature = temperature

        # Update heater status based on new target
        self._update_heater_status()
        self.last_updated = datetime.now()

    def set_mode(self, mode: WaterHeaterMode) -> None:
        """Set the operating mode of the water heater.

        Args:
            mode: The new operating mode
        """
        self.mode = mode
        self.last_updated = datetime.now()

    def update_current_temperature(self, temperature: Temperature) -> None:
        """Update the current temperature and adjust heater status accordingly.

        Args:
            temperature: The new current temperature
        """
        self.current_temperature = temperature
        self._update_heater_status()
        self.last_updated = datetime.now()

    def _update_heater_status(self) -> None:
        """Update the heater status based on current and target temperatures."""
        if not self.status.is_online():
            self.heater_status = "OFF"
            return

        # Convert to celsius for comparison
        current_c = self.current_temperature.to_celsius().value
        target_c = self.target_temperature.to_celsius().value

        # Determine if heating is needed (with a small hysteresis)
        if current_c < target_c - 1.0:
            self.heater_status = "HEATING"
        else:
            self.heater_status = "STANDBY"

    def to_dict(self) -> dict:
        """Convert the water heater to a dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "current_temperature": self.current_temperature.value,
            "current_temperature_unit": self.current_temperature.unit,
            "target_temperature": self.target_temperature.value,
            "target_temperature_unit": self.target_temperature.unit,
            "min_temperature": self.min_temperature.value,
            "max_temperature": self.max_temperature.value,
            "status": self.status.value,
            "mode": self.mode.value,
            "health_status": self.health_status.value,
            "location": self.location,
            "heater_status": self.heater_status,
            "is_simulated": self.is_simulated,
            "last_updated": self.last_updated.isoformat()
            if self.last_updated
            else None,
        }
