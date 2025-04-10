"""
Water Heater domain events.

This module defines the domain events related to water heaters, following
Clean Architecture principles by defining events in the domain layer.
"""
import json
from typing import Any, Dict, List

from src.domain.events.event import Event


class WaterHeaterCreatedEvent(Event):
    """Event emitted when a new water heater is created."""

    def __init__(
        self, heater_id: str, heater_data: Dict[str, Any], timestamp: str = None
    ):
        """Initialize a WaterHeaterCreatedEvent.

        Args:
            heater_id: ID of the created water heater
            heater_data: Data of the created water heater
            timestamp: ISO format timestamp of when the event occurred
        """
        super().__init__(timestamp)
        self.heater_id = heater_id
        self.heater_data = heater_data

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary.

        Returns:
            Dict: Dictionary representation of the event
        """
        result = super().to_dict()
        result.update({"heater_id": self.heater_id, "heater_data": self.heater_data})
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WaterHeaterCreatedEvent":
        """Create an event from a dictionary.

        Args:
            data: Dictionary representation of the event

        Returns:
            WaterHeaterCreatedEvent: Reconstructed event
        """
        return cls(
            heater_id=data["heater_id"],
            heater_data=data["heater_data"],
            timestamp=data.get("timestamp"),
        )


class WaterHeaterUpdatedEvent(Event):
    """Event emitted when a water heater is updated."""

    def __init__(
        self,
        heater_id: str,
        heater_data: Dict[str, Any],
        changed_fields: List[str],
        timestamp: str = None,
    ):
        """Initialize a WaterHeaterUpdatedEvent.

        Args:
            heater_id: ID of the updated water heater
            heater_data: Current data of the water heater
            changed_fields: List of fields that were updated
            timestamp: ISO format timestamp of when the event occurred
        """
        super().__init__(timestamp)
        self.heater_id = heater_id
        self.heater_data = heater_data
        self.changed_fields = changed_fields

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary.

        Returns:
            Dict: Dictionary representation of the event
        """
        result = super().to_dict()
        result.update(
            {
                "heater_id": self.heater_id,
                "heater_data": self.heater_data,
                "changed_fields": self.changed_fields,
            }
        )
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WaterHeaterUpdatedEvent":
        """Create an event from a dictionary.

        Args:
            data: Dictionary representation of the event

        Returns:
            WaterHeaterUpdatedEvent: Reconstructed event
        """
        return cls(
            heater_id=data["heater_id"],
            heater_data=data["heater_data"],
            changed_fields=data["changed_fields"],
            timestamp=data.get("timestamp"),
        )


class WaterHeaterDeletedEvent(Event):
    """Event emitted when a water heater is deleted."""

    def __init__(self, heater_id: str, timestamp: str = None):
        """Initialize a WaterHeaterDeletedEvent.

        Args:
            heater_id: ID of the deleted water heater
            timestamp: ISO format timestamp of when the event occurred
        """
        super().__init__(timestamp)
        self.heater_id = heater_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary.

        Returns:
            Dict: Dictionary representation of the event
        """
        result = super().to_dict()
        result.update({"heater_id": self.heater_id})
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WaterHeaterDeletedEvent":
        """Create an event from a dictionary.

        Args:
            data: Dictionary representation of the event

        Returns:
            WaterHeaterDeletedEvent: Reconstructed event
        """
        return cls(heater_id=data["heater_id"], timestamp=data.get("timestamp"))


class WaterHeaterModeChangedEvent(Event):
    """Event emitted when a water heater's mode is changed."""

    def __init__(
        self, heater_id: str, old_mode: str, new_mode: str, timestamp: str = None
    ):
        """Initialize a WaterHeaterModeChangedEvent.

        Args:
            heater_id: ID of the water heater
            old_mode: Previous mode
            new_mode: New mode
            timestamp: ISO format timestamp of when the event occurred
        """
        super().__init__(timestamp)
        self.heater_id = heater_id
        self.old_mode = old_mode
        self.new_mode = new_mode

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary.

        Returns:
            Dict: Dictionary representation of the event
        """
        result = super().to_dict()
        result.update(
            {
                "heater_id": self.heater_id,
                "old_mode": self.old_mode,
                "new_mode": self.new_mode,
            }
        )
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WaterHeaterModeChangedEvent":
        """Create an event from a dictionary.

        Args:
            data: Dictionary representation of the event

        Returns:
            WaterHeaterModeChangedEvent: Reconstructed event
        """
        return cls(
            heater_id=data["heater_id"],
            old_mode=data["old_mode"],
            new_mode=data["new_mode"],
            timestamp=data.get("timestamp"),
        )


class WaterHeaterTemperatureChangedEvent(Event):
    """Event emitted when a water heater's temperature settings are changed."""

    def __init__(
        self,
        heater_id: str,
        old_temperature: Dict[str, Any],
        new_temperature: Dict[str, Any],
        temperature_type: str,  # 'current', 'target', 'min', or 'max'
        timestamp: str = None,
    ):
        """Initialize a WaterHeaterTemperatureChangedEvent.

        Args:
            heater_id: ID of the water heater
            old_temperature: Previous temperature settings
            new_temperature: New temperature settings
            temperature_type: Type of temperature changed ('current', 'target', 'min', or 'max')
            timestamp: ISO format timestamp of when the event occurred
        """
        super().__init__(timestamp)
        self.heater_id = heater_id
        self.old_temperature = old_temperature
        self.new_temperature = new_temperature
        self.temperature_type = temperature_type

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary.

        Returns:
            Dict: Dictionary representation of the event
        """
        result = super().to_dict()
        result.update(
            {
                "heater_id": self.heater_id,
                "old_temperature": self.old_temperature,
                "new_temperature": self.new_temperature,
                "temperature_type": self.temperature_type,
            }
        )
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WaterHeaterTemperatureChangedEvent":
        """Create an event from a dictionary.

        Args:
            data: Dictionary representation of the event

        Returns:
            WaterHeaterTemperatureChangedEvent: Reconstructed event
        """
        return cls(
            heater_id=data["heater_id"],
            old_temperature=data["old_temperature"],
            new_temperature=data["new_temperature"],
            temperature_type=data["temperature_type"],
            timestamp=data.get("timestamp"),
        )


class WaterHeaterStatusChangedEvent(Event):
    """Event emitted when a water heater's status changes."""

    def __init__(
        self,
        heater_id: str,
        old_status: str,
        new_status: str,
        status_type: str,  # 'device' or 'heater'
        timestamp: str = None,
    ):
        """Initialize a WaterHeaterStatusChangedEvent.

        Args:
            heater_id: ID of the water heater
            old_status: Previous status
            new_status: New status
            status_type: Type of status changed ('device' or 'heater')
            timestamp: ISO format timestamp of when the event occurred
        """
        super().__init__(timestamp)
        self.heater_id = heater_id
        self.old_status = old_status
        self.new_status = new_status
        self.status_type = status_type

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary.

        Returns:
            Dict: Dictionary representation of the event
        """
        result = super().to_dict()
        result.update(
            {
                "heater_id": self.heater_id,
                "old_status": self.old_status,
                "new_status": self.new_status,
                "status_type": self.status_type,
            }
        )
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WaterHeaterStatusChangedEvent":
        """Create an event from a dictionary.

        Args:
            data: Dictionary representation of the event

        Returns:
            WaterHeaterStatusChangedEvent: Reconstructed event
        """
        return cls(
            heater_id=data["heater_id"],
            old_status=data["old_status"],
            new_status=data["new_status"],
            status_type=data["status_type"],
            timestamp=data.get("timestamp"),
        )
