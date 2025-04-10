"""
Temperature value object representing a temperature value with a unit.

This immutable object encapsulates temperature data and validation rules.
"""
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class Temperature:
    """Value object representing a temperature measurement with a unit.

    Attributes:
        value: The temperature value as a float
        unit: The temperature unit (C for Celsius, F for Fahrenheit)
    """

    value: float
    unit: Literal["C", "F"] = "C"

    def __post_init__(self):
        """Validate temperature values after initialization."""
        if not isinstance(self.value, (int, float)):
            raise ValueError(
                f"Temperature value must be a number, got {type(self.value)}"
            )

        if self.unit not in ["C", "F"]:
            raise ValueError(f"Temperature unit must be 'C' or 'F', got {self.unit}")

    def to_celsius(self) -> "Temperature":
        """Convert temperature to Celsius."""
        if self.unit == "C":
            return self

        # Convert from Fahrenheit to Celsius
        celsius_value = (self.value - 32) * 5 / 9
        return Temperature(value=celsius_value, unit="C")

    def to_fahrenheit(self) -> "Temperature":
        """Convert temperature to Fahrenheit."""
        if self.unit == "F":
            return self

        # Convert from Celsius to Fahrenheit
        fahrenheit_value = (self.value * 9 / 5) + 32
        return Temperature(value=fahrenheit_value, unit="F")

    def __str__(self) -> str:
        """String representation of the temperature."""
        return f"{self.value:.1f}°{self.unit}"
