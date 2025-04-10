"""
Device Shadow domain events.

This module defines the domain events related to device shadows, following
Clean Architecture principles by defining events in the domain layer.
"""
import json
from typing import Any, Dict, List

from src.domain.events.event import Event


class DeviceShadowCreatedEvent(Event):
    """Event emitted when a new device shadow is created."""

    def __init__(
        self, device_id: str, shadow_data: Dict[str, Any], timestamp: str = None
    ):
        """Initialize a DeviceShadowCreatedEvent.

        Args:
            device_id: ID of the device whose shadow was created
            shadow_data: Data of the created device shadow
            timestamp: ISO format timestamp of when the event occurred
        """
        super().__init__(timestamp)
        self.device_id = device_id
        self.shadow_data = shadow_data

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary.

        Returns:
            Dict: Dictionary representation of the event
        """
        result = super().to_dict()
        result.update({"device_id": self.device_id, "shadow_data": self.shadow_data})
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceShadowCreatedEvent":
        """Create an event from a dictionary.

        Args:
            data: Dictionary representation of the event

        Returns:
            DeviceShadowCreatedEvent: Reconstructed event
        """
        return cls(
            device_id=data["device_id"],
            shadow_data=data["shadow_data"],
            timestamp=data.get("timestamp"),
        )


class DeviceShadowDesiredStateUpdatedEvent(Event):
    """Event emitted when a device shadow's desired state is updated."""

    def __init__(
        self,
        device_id: str,
        shadow_data: Dict[str, Any],
        changed_fields: List[str],
        timestamp: str = None,
    ):
        """Initialize a DeviceShadowDesiredStateUpdatedEvent.

        Args:
            device_id: ID of the device whose shadow was updated
            shadow_data: Current data of the device shadow
            changed_fields: List of fields in the desired state that were updated
            timestamp: ISO format timestamp of when the event occurred
        """
        super().__init__(timestamp)
        self.device_id = device_id
        self.shadow_data = shadow_data
        self.changed_fields = changed_fields

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary.

        Returns:
            Dict: Dictionary representation of the event
        """
        result = super().to_dict()
        result.update(
            {
                "device_id": self.device_id,
                "shadow_data": self.shadow_data,
                "changed_fields": self.changed_fields,
            }
        )
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceShadowDesiredStateUpdatedEvent":
        """Create an event from a dictionary.

        Args:
            data: Dictionary representation of the event

        Returns:
            DeviceShadowDesiredStateUpdatedEvent: Reconstructed event
        """
        return cls(
            device_id=data["device_id"],
            shadow_data=data["shadow_data"],
            changed_fields=data["changed_fields"],
            timestamp=data.get("timestamp"),
        )


class DeviceShadowReportedStateUpdatedEvent(Event):
    """Event emitted when a device shadow's reported state is updated."""

    def __init__(
        self,
        device_id: str,
        shadow_data: Dict[str, Any],
        changed_fields: List[str],
        timestamp: str = None,
    ):
        """Initialize a DeviceShadowReportedStateUpdatedEvent.

        Args:
            device_id: ID of the device whose shadow was updated
            shadow_data: Current data of the device shadow
            changed_fields: List of fields in the reported state that were updated
            timestamp: ISO format timestamp of when the event occurred
        """
        super().__init__(timestamp)
        self.device_id = device_id
        self.shadow_data = shadow_data
        self.changed_fields = changed_fields

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary.

        Returns:
            Dict: Dictionary representation of the event
        """
        result = super().to_dict()
        result.update(
            {
                "device_id": self.device_id,
                "shadow_data": self.shadow_data,
                "changed_fields": self.changed_fields,
            }
        )
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceShadowReportedStateUpdatedEvent":
        """Create an event from a dictionary.

        Args:
            data: Dictionary representation of the event

        Returns:
            DeviceShadowReportedStateUpdatedEvent: Reconstructed event
        """
        return cls(
            device_id=data["device_id"],
            shadow_data=data["shadow_data"],
            changed_fields=data["changed_fields"],
            timestamp=data.get("timestamp"),
        )


class DeviceShadowDeletedEvent(Event):
    """Event emitted when a device shadow is deleted."""

    def __init__(self, device_id: str, timestamp: str = None):
        """Initialize a DeviceShadowDeletedEvent.

        Args:
            device_id: ID of the device whose shadow was deleted
            timestamp: ISO format timestamp of when the event occurred
        """
        super().__init__(timestamp)
        self.device_id = device_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary.

        Returns:
            Dict: Dictionary representation of the event
        """
        result = super().to_dict()
        result.update({"device_id": self.device_id})
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceShadowDeletedEvent":
        """Create an event from a dictionary.

        Args:
            data: Dictionary representation of the event

        Returns:
            DeviceShadowDeletedEvent: Reconstructed event
        """
        return cls(device_id=data["device_id"], timestamp=data.get("timestamp"))


class DeviceShadowSyncRequestedEvent(Event):
    """Event emitted when a device shadow sync is requested."""

    def __init__(self, device_id: str, client_token: str, timestamp: str = None):
        """Initialize a DeviceShadowSyncRequestedEvent.

        Args:
            device_id: ID of the device whose shadow sync is requested
            client_token: Client token for correlation
            timestamp: ISO format timestamp of when the event occurred
        """
        super().__init__(timestamp)
        self.device_id = device_id
        self.client_token = client_token

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary.

        Returns:
            Dict: Dictionary representation of the event
        """
        result = super().to_dict()
        result.update({"device_id": self.device_id, "client_token": self.client_token})
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceShadowSyncRequestedEvent":
        """Create an event from a dictionary.

        Args:
            data: Dictionary representation of the event

        Returns:
            DeviceShadowSyncRequestedEvent: Reconstructed event
        """
        return cls(
            device_id=data["device_id"],
            client_token=data["client_token"],
            timestamp=data.get("timestamp"),
        )


class DeviceShadowSyncCompletedEvent(Event):
    """Event emitted when a device shadow sync is completed."""

    def __init__(
        self,
        device_id: str,
        client_token: str,
        success: bool,
        shadow_data: Dict[str, Any] = None,
        error_message: str = None,
        timestamp: str = None,
    ):
        """Initialize a DeviceShadowSyncCompletedEvent.

        Args:
            device_id: ID of the device whose shadow sync is completed
            client_token: Client token for correlation
            success: Whether the sync was successful
            shadow_data: Updated shadow data if sync was successful
            error_message: Error message if sync failed
            timestamp: ISO format timestamp of when the event occurred
        """
        super().__init__(timestamp)
        self.device_id = device_id
        self.client_token = client_token
        self.success = success
        self.shadow_data = shadow_data
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary.

        Returns:
            Dict: Dictionary representation of the event
        """
        result = super().to_dict()
        result.update(
            {
                "device_id": self.device_id,
                "client_token": self.client_token,
                "success": self.success,
            }
        )

        if self.success and self.shadow_data:
            result["shadow_data"] = self.shadow_data
        elif not self.success and self.error_message:
            result["error_message"] = self.error_message

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceShadowSyncCompletedEvent":
        """Create an event from a dictionary.

        Args:
            data: Dictionary representation of the event

        Returns:
            DeviceShadowSyncCompletedEvent: Reconstructed event
        """
        return cls(
            device_id=data["device_id"],
            client_token=data["client_token"],
            success=data["success"],
            shadow_data=data.get("shadow_data"),
            error_message=data.get("error_message"),
            timestamp=data.get("timestamp"),
        )
