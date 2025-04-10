"""
Device Shadow entity for IoT device state synchronization.

This entity encapsulates the core business rules for device shadows,
which track the reported and desired state of IoT devices.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from src.domain.value_objects.shadow_state import ShadowState


@dataclass
class DeviceShadow:
    """Entity representing an IoT device shadow.

    A device shadow is a persistent, virtual representation of an IoT device that
    includes the last reported state from the device and the desired state that
    should be synchronized to the device when it reconnects.

    Attributes:
        device_id: Unique identifier for the device
        reported: The last reported state from the device
        desired: The desired state to be sent to the device
        version: Version number that increments with each update
        timestamp: Timestamp of the last update
        metadata: Additional metadata about the shadow document
    """

    device_id: str
    reported: ShadowState
    desired: ShadowState
    version: int = 1
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

    def update_reported_state(self, state_updates: Dict[str, Any]) -> None:
        """Update the reported state of the device.

        Updates the reported state with the provided state_updates and
        increments the version number.

        Args:
            state_updates: Dictionary of state properties to update
        """
        self.reported = self.reported.update(state_updates)
        self.version += 1
        self.timestamp = datetime.now()

    def update_desired_state(self, state_updates: Dict[str, Any]) -> None:
        """Update the desired state of the device.

        Updates the desired state with the provided state_updates and
        increments the version number.

        Args:
            state_updates: Dictionary of state properties to update
        """
        self.desired = self.desired.update(state_updates)
        self.version += 1
        self.timestamp = datetime.now()

    def clear_desired_state(self) -> None:
        """Clear the desired state after synchronizing with the device."""
        self.desired = ShadowState({})
        self.version += 1
        self.timestamp = datetime.now()

    def get_delta(self) -> Dict[str, Any]:
        """Get the difference between desired and reported states.

        Returns:
            Dictionary containing only the properties that differ
            between desired and reported states
        """
        delta = {}

        # Get all keys from both states
        all_keys = set(self.desired.state.keys()) | set(self.reported.state.keys())

        # Check each key for differences
        for key in all_keys:
            desired_value = self.desired.state.get(key)
            reported_value = self.reported.state.get(key)

            # If key exists in desired but not in reported or values differ
            if key in self.desired.state and (
                key not in self.reported.state or desired_value != reported_value
            ):
                delta[key] = desired_value

        return delta

    def to_dict(self) -> Dict[str, Any]:
        """Convert the device shadow to a dictionary representation."""
        return {
            "device_id": self.device_id,
            "reported": self.reported.state,
            "desired": self.desired.state,
            "version": self.version,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.metadata,
        }
