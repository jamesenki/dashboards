"""
In-memory implementation of the Device Shadow Repository interface.

This adapter provides an in-memory implementation of the DeviceShadowRepository interface
for testing and development purposes, following Clean Architecture principles.
"""
import asyncio
import copy
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.domain.entities.device_shadow import DeviceShadow
from src.domain.value_objects.shadow_state import ShadowState
from src.gateways.device_shadow_repository import DeviceShadowRepository


class InMemoryDeviceShadowRepository(DeviceShadowRepository):
    """In-memory implementation of DeviceShadowRepository interface.

    This implementation stores device shadows in memory, making it suitable
    for testing and development, but not for production use since data
    is lost when the application restarts.
    """

    def __init__(self, initial_data: Dict[str, DeviceShadow] = None):
        """Initialize with optional initial data.

        Args:
            initial_data: Optional dictionary of device shadows to pre-populate the repository
        """
        # Store shadows in a dictionary keyed by device ID for efficient lookups
        self._shadows: Dict[str, DeviceShadow] = {}

        # Add initial data if provided
        if initial_data:
            for device_id, shadow in initial_data.items():
                self._shadows[device_id] = copy.deepcopy(shadow)

    async def get_shadow(self, device_id: str) -> Optional[DeviceShadow]:
        """Get a device shadow by device ID.

        Args:
            device_id: The unique identifier of the device

        Returns:
            The DeviceShadow entity if found, otherwise None
        """
        # Add a small delay to simulate async behavior for testing consistency
        await asyncio.sleep(0.001)

        # Return a deep copy to prevent external modification of internal state
        shadow = self._shadows.get(device_id)
        return copy.deepcopy(shadow) if shadow else None

    async def create_shadow(self, shadow: DeviceShadow) -> bool:
        """Create a new device shadow.

        Args:
            shadow: The DeviceShadow entity to create

        Returns:
            True if creation was successful, False otherwise

        Raises:
            ValueError: If a shadow with the same device_id already exists
        """
        # Add a small delay to simulate async behavior for testing consistency
        await asyncio.sleep(0.001)

        # Ensure device ID doesn't already exist
        if shadow.device_id in self._shadows:
            raise ValueError(f"Shadow for device {shadow.device_id} already exists")

        # Store a copy of the shadow
        self._shadows[shadow.device_id] = copy.deepcopy(shadow)

        return True

    async def update_shadow(self, shadow: DeviceShadow) -> bool:
        """Update an existing device shadow.

        Args:
            shadow: The DeviceShadow entity to update

        Returns:
            True if update was successful, False otherwise
        """
        # Add a small delay to simulate async behavior for testing consistency
        await asyncio.sleep(0.001)

        # Check if shadow exists
        if shadow.device_id not in self._shadows:
            return False

        # Update the shadow
        self._shadows[shadow.device_id] = copy.deepcopy(shadow)

        return True

    async def delete_shadow(self, device_id: str) -> bool:
        """Delete a device shadow.

        Args:
            device_id: The unique identifier of the device

        Returns:
            True if deletion was successful, False otherwise
        """
        # Add a small delay to simulate async behavior for testing consistency
        await asyncio.sleep(0.001)

        # Check if shadow exists
        if device_id not in self._shadows:
            return False

        # Delete the shadow
        del self._shadows[device_id]

        return True

    async def update_reported_state(
        self, device_id: str, state: Dict[str, Any]
    ) -> Optional[DeviceShadow]:
        """Update the reported state of a device shadow.

        Args:
            device_id: The unique identifier of the device
            state: The state updates to apply

        Returns:
            The updated DeviceShadow if successful, otherwise None
        """
        # Add a small delay to simulate async behavior for testing consistency
        await asyncio.sleep(0.001)

        # Get the shadow
        shadow = self._shadows.get(device_id)
        if not shadow:
            return None

        # Create a deep copy to update
        updated_shadow = copy.deepcopy(shadow)

        # Update the reported state
        updated_shadow.update_reported_state(state)

        # Store the updated shadow
        self._shadows[device_id] = updated_shadow

        # Return a copy of the updated shadow
        return copy.deepcopy(updated_shadow)

    async def update_desired_state(
        self, device_id: str, state: Dict[str, Any]
    ) -> Optional[DeviceShadow]:
        """Update the desired state of a device shadow.

        Args:
            device_id: The unique identifier of the device
            state: The state updates to apply

        Returns:
            The updated DeviceShadow if successful, otherwise None
        """
        # Add a small delay to simulate async behavior for testing consistency
        await asyncio.sleep(0.001)

        # Get the shadow
        shadow = self._shadows.get(device_id)
        if not shadow:
            return None

        # Create a deep copy to update
        updated_shadow = copy.deepcopy(shadow)

        # Update the desired state
        updated_shadow.update_desired_state(state)

        # Store the updated shadow
        self._shadows[device_id] = updated_shadow

        # Return a copy of the updated shadow
        return copy.deepcopy(updated_shadow)
