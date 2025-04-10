"""
Maintenance status value object representing maintenance health status.

This immutable object encapsulates maintenance status data and validation rules.
"""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class MaintenanceStatus:
    """Value object representing a device's maintenance health status.

    Attributes:
        value: The status value (GREEN, YELLOW, RED)
          - GREEN: Healthy, no maintenance required
          - YELLOW: Warning, maintenance recommended
          - RED: Critical, maintenance required
    """

    value: Literal["GREEN", "YELLOW", "RED"]

    def __post_init__(self):
        """Validate maintenance status value after initialization."""
        valid_statuses = ["GREEN", "YELLOW", "RED"]
        if self.value not in valid_statuses:
            raise ValueError(
                f"Maintenance status must be one of {valid_statuses}, got {self.value}"
            )

    def is_healthy(self) -> bool:
        """Check if the device is in a healthy state."""
        return self.value == "GREEN"

    def needs_attention(self) -> bool:
        """Check if the device needs maintenance attention."""
        return self.value == "YELLOW"

    def requires_maintenance(self) -> bool:
        """Check if the device requires immediate maintenance."""
        return self.value == "RED"

    def get_severity_level(self) -> int:
        """Get numerical severity level (0-2, where 2 is most severe)."""
        severity_map = {"GREEN": 0, "YELLOW": 1, "RED": 2}
        return severity_map.get(self.value, 0)

    def __str__(self) -> str:
        """String representation of the maintenance status."""
        return self.value
