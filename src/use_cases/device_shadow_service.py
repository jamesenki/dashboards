"""
Device Shadow Service implementing business logic for device shadow operations.

This use case layer class encapsulates the business rules for device shadow operations
following Clean Architecture principles, where use cases depend on entities and gateways.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.domain.entities.device_shadow import DeviceShadow
from src.domain.value_objects.shadow_state import ShadowState
from src.gateways.device_shadow_repository import DeviceShadowRepository


class DeviceShadowService:
    """Service for device shadow operations implementing business logic.

    This class implements the use cases related to device shadow operations,
    applying domain rules and orchestrating entity interactions.

    It depends on the DeviceShadowRepository interface (not implementation)
    following the Dependency Inversion Principle.
    """

    def __init__(self, repository: DeviceShadowRepository):
        """Initialize the device shadow service.

        Args:
            repository: Implementation of DeviceShadowRepository interface
        """
        self.repository = repository

    async def get_device_shadow(self, device_id: str) -> Dict[str, Any]:
        """Get a device shadow by device ID.

        Args:
            device_id: The unique identifier of the device

        Returns:
            The device shadow as a dictionary

        Raises:
            Exception: If the device shadow doesn't exist
        """
        shadow = await self.repository.get_shadow(device_id)
        if not shadow:
            raise Exception(f"No shadow document exists for device {device_id}")

        # Return the shadow in a standardized format
        return {
            "device_id": shadow.device_id,
            "reported": shadow.reported.state,
            "desired": shadow.desired.state,
            "version": shadow.version,
            "timestamp": shadow.timestamp.isoformat() if shadow.timestamp else None,
        }

    async def create_device_shadow(
        self, device_id: str, initial_state: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a new device shadow.

        Args:
            device_id: The unique identifier of the device
            initial_state: Optional initial reported state

        Returns:
            The created device shadow as a dictionary

        Raises:
            Exception: If a shadow already exists for the device
        """
        # Check if shadow already exists
        existing_shadow = await self.repository.get_shadow(device_id)
        if existing_shadow:
            raise Exception(f"Shadow document already exists for device {device_id}")

        # Create initial states
        reported_state = ShadowState(initial_state or {})
        desired_state = ShadowState({})

        # Create shadow entity
        shadow = DeviceShadow(
            device_id=device_id,
            reported=reported_state,
            desired=desired_state,
            version=1,
            timestamp=datetime.now(),
        )

        # Save to repository
        success = await self.repository.create_shadow(shadow)
        if not success:
            raise Exception(f"Failed to create shadow for device {device_id}")

        # Return the created shadow
        return {
            "device_id": shadow.device_id,
            "reported": shadow.reported.state,
            "desired": shadow.desired.state,
            "version": shadow.version,
            "timestamp": shadow.timestamp.isoformat() if shadow.timestamp else None,
        }

    async def update_reported_state(
        self, device_id: str, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update the reported state of a device shadow.

        Args:
            device_id: The unique identifier of the device
            state: The state updates to apply

        Returns:
            The updated device shadow as a dictionary

        Raises:
            Exception: If the device shadow doesn't exist or update fails
        """
        # Update through repository which handles version increments
        updated_shadow = await self.repository.update_reported_state(device_id, state)
        if not updated_shadow:
            raise Exception(f"Failed to update reported state for device {device_id}")

        # Return the updated shadow
        return {
            "device_id": updated_shadow.device_id,
            "reported": updated_shadow.reported.state,
            "desired": updated_shadow.desired.state,
            "version": updated_shadow.version,
            "timestamp": updated_shadow.timestamp.isoformat()
            if updated_shadow.timestamp
            else None,
        }

    async def update_desired_state(
        self, device_id: str, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update the desired state of a device shadow.

        Args:
            device_id: The unique identifier of the device
            state: The state updates to apply

        Returns:
            The updated device shadow as a dictionary

        Raises:
            Exception: If the device shadow doesn't exist or update fails
        """
        # Update through repository which handles version increments
        updated_shadow = await self.repository.update_desired_state(device_id, state)
        if not updated_shadow:
            raise Exception(f"Failed to update desired state for device {device_id}")

        # Return the updated shadow
        return {
            "device_id": updated_shadow.device_id,
            "reported": updated_shadow.reported.state,
            "desired": updated_shadow.desired.state,
            "version": updated_shadow.version,
            "timestamp": updated_shadow.timestamp.isoformat()
            if updated_shadow.timestamp
            else None,
        }

    async def delete_device_shadow(self, device_id: str) -> bool:
        """Delete a device shadow.

        Args:
            device_id: The unique identifier of the device

        Returns:
            True if deletion was successful, False otherwise

        Raises:
            Exception: If the device shadow doesn't exist
        """
        # Check if shadow exists
        shadow = await self.repository.get_shadow(device_id)
        if not shadow:
            raise Exception(f"No shadow document exists for device {device_id}")

        # Delete the shadow
        return await self.repository.delete_shadow(device_id)

    async def get_shadow_delta(self, device_id: str) -> Dict[str, Any]:
        """Get the delta between desired and reported states.

        The delta contains only the properties that differ between
        desired and reported states.

        Args:
            device_id: The unique identifier of the device

        Returns:
            Dictionary containing the delta and metadata

        Raises:
            Exception: If the device shadow doesn't exist
        """
        # Get the shadow
        shadow = await self.repository.get_shadow(device_id)
        if not shadow:
            raise Exception(f"No shadow document exists for device {device_id}")

        # Calculate delta using entity method
        delta = shadow.get_delta()

        # Return delta with metadata
        return {
            "device_id": shadow.device_id,
            "delta": delta,
            "version": shadow.version,
            "timestamp": shadow.timestamp.isoformat() if shadow.timestamp else None,
        }
