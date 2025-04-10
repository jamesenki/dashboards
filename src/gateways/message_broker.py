"""
Message Broker interface defining the gateway for event publishing and consumption.

Following Clean Architecture, this defines the interface that use cases
interact with, without dependencies on specific external implementations.
"""
from abc import ABC, abstractmethod
from typing import Callable, List, Optional

from src.domain.events.event import Event


class MessageBroker(ABC):
    """Abstract interface for message broker interactions.

    This interface defines the methods that any message broker implementation
    must provide, following Clean Architecture principles to abstract the
    communication mechanism from business logic.
    """

    @abstractmethod
    def publish_event(
        self, topic: str, event: Event, key: Optional[str] = None
    ) -> None:
        """Publish an event to the specified topic.

        Args:
            topic: The topic to publish the event to
            event: The event to publish
            key: Optional key for routing or partitioning
        """
        pass

    @abstractmethod
    def register_handler(self, topic: str, handler: Callable) -> None:
        """Register a handler for a specific topic.

        Args:
            topic: The topic to handle events from
            handler: The callback function to handle events
        """
        pass

    @abstractmethod
    def init_producer(self) -> None:
        """Initialize the event producer.

        This method prepares the broker for publishing events.
        """
        pass

    @abstractmethod
    def init_consumer(self, topics: List[str]) -> None:
        """Initialize the event consumer for the specified topics.

        Args:
            topics: List of topics to consume events from
        """
        pass

    @abstractmethod
    async def start_consuming(self) -> None:
        """Start consuming events from subscribed topics.

        This method starts the event consumption process.
        """
        pass

    @abstractmethod
    async def stop_consuming(self) -> None:
        """Stop consuming events.

        This method stops the event consumption process.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close all connections and resources.

        This method performs cleanup before the broker is destroyed.
        """
        pass
