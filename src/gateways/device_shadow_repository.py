"""
Device Shadow Repository interface defining the gateway to shadow storage.

Following Clean Architecture, this defines the interface that use cases
interact with, without dependencies on specific external implementations.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.domain.entities.device_shadow import DeviceShadow


class DeviceShadowRepository(ABC):
    """Abstract interface for device shadow data persistence.

    This interface defines the methods that any device shadow repository
    implementation must provide, following the Repository pattern to
    abstract data access from business logic.
    """

    @abstractmethod
    async def get_shadow(self, device_id: str) -> Optional[DeviceShadow]:
        """Get a device shadow by device ID.

        Args:
            device_id: The unique identifier of the device

        Returns:
            The DeviceShadow entity if found, otherwise None
        """
        pass

    @abstractmethod
    async def create_shadow(self, shadow: DeviceShadow) -> bool:
        """Create a new device shadow.

        Args:
            shadow: The DeviceShadow entity to create

        Returns:
            True if creation was successful, False otherwise

        Raises:
            ValueError: If a shadow with the same device_id already exists
        """
        pass

    @abstractmethod
    async def update_shadow(self, shadow: DeviceShadow) -> bool:
        """Update an existing device shadow.

        Args:
            shadow: The DeviceShadow entity to update

        Returns:
            True if update was successful, False otherwise
        """
        pass

    @abstractmethod
    async def delete_shadow(self, device_id: str) -> bool:
        """Delete a device shadow.

        Args:
            device_id: The unique identifier of the device

        Returns:
            True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass
