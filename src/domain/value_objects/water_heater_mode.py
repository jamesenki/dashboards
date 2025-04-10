"""
Water heater mode value object representing the operational mode of a water heater.

This immutable object encapsulates water heater mode data and validation rules.
"""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class WaterHeaterMode:
    """Value object representing a water heater's operational mode.

    Attributes:
        value: The mode value (ECO, PERFORMANCE, VACATION, BOOST)
    """

    value: Literal["ECO", "PERFORMANCE", "VACATION", "BOOST"]

    def __post_init__(self):
        """Validate mode value after initialization."""
        valid_modes = ["ECO", "PERFORMANCE", "VACATION", "BOOST"]
        if self.value not in valid_modes:
            raise ValueError(
                f"Water heater mode must be one of {valid_modes}, got {self.value}"
            )

    def is_eco(self) -> bool:
        """Check if the water heater is in eco mode."""
        return self.value == "ECO"

    def is_performance(self) -> bool:
        """Check if the water heater is in performance mode."""
        return self.value == "PERFORMANCE"

    def is_vacation(self) -> bool:
        """Check if the water heater is in vacation mode."""
        return self.value == "VACATION"

    def is_boost(self) -> bool:
        """Check if the water heater is in boost mode."""
        return self.value == "BOOST"

    def get_energy_efficiency(self) -> float:
        """Get the energy efficiency rating for this mode (0.0-1.0)."""
        efficiency_map = {
            "ECO": 0.9,
            "PERFORMANCE": 0.7,
            "VACATION": 0.95,
            "BOOST": 0.5,
        }
        return efficiency_map.get(self.value, 0.8)

    def __str__(self) -> str:
        """String representation of the water heater mode."""
        return self.value
