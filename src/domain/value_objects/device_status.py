"""
Device status value object representing a device's operational status.

This immutable object encapsulates device status data and validation rules.
"""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class DeviceStatus:
    """Value object representing a device's operational status.

    Attributes:
        value: The status value (ONLINE, OFFLINE, MAINTENANCE, ERROR)
    """

    value: Literal["ONLINE", "OFFLINE", "MAINTENANCE", "ERROR"]

    def __post_init__(self):
        """Validate status value after initialization."""
        valid_statuses = ["ONLINE", "OFFLINE", "MAINTENANCE", "ERROR"]
        if self.value not in valid_statuses:
            raise ValueError(
                f"Device status must be one of {valid_statuses}, got {self.value}"
            )

    def is_online(self) -> bool:
        """Check if the device is online."""
        return self.value == "ONLINE"

    def is_offline(self) -> bool:
        """Check if the device is offline."""
        return self.value == "OFFLINE"

    def is_in_maintenance(self) -> bool:
        """Check if the device is in maintenance mode."""
        return self.value == "MAINTENANCE"

    def is_in_error(self) -> bool:
        """Check if the device is in an error state."""
        return self.value == "ERROR"

    def __str__(self) -> str:
        """String representation of the device status."""
        return self.value
