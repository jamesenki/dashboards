"""
Base Event class for domain events.

This module defines the base Event class for domain events in the IoTSphere application,
following Clean Architecture principles.
"""
from datetime import datetime
from typing import Any, Dict


class Event:
    """Base class for all domain events.

    This abstract class represents a domain event that can be published and consumed
    through the message broker. It provides common properties and methods for all events.
    """

    def __init__(self, timestamp: str = None):
        """Initialize a domain event.

        Args:
            timestamp: ISO format timestamp of when the event occurred
        """
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary.

        This method should be overridden by subclasses to include all event-specific
        properties in the returned dictionary.

        Returns:
            Dict: Dictionary representation of the event
        """
        return {"timestamp": self.timestamp, "event_type": self.__class__.__name__}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create an event from a dictionary.

        This method should be overridden by subclasses to reconstruct an event
        from its dictionary representation.

        Args:
            data: Dictionary representation of the event

        Returns:
            Event: Reconstructed event
        """
        return cls(timestamp=data.get("timestamp"))
