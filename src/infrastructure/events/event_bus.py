"""
Event Bus system for IoTSphere platform.

Provides a centralized event broadcasting and subscription system to enable
loose coupling between components while maintaining real-time responsiveness.
"""
import logging
import asyncio
from typing import Dict, List, Any, Callable, Set, Coroutine

logger = logging.getLogger(__name__)

class EventBus:
    """
    Event bus for publishing and subscribing to events across the system.
    
    The EventBus enables components to communicate without direct dependencies,
    promoting a more modular architecture that supports:
    
    1. Real-time notifications
    2. Asynchronous processing
    3. Multiple subscribers for a single event
    """
    
    def __init__(self):
        """Initialize the event bus."""
        self.subscribers: Dict[str, Set[Callable]] = {}
        logger.info("Event Bus initialized")
    
    async def publish(self, topic: str, data: Dict[str, Any]) -> None:
        """
        Publish an event to all subscribers of the specified topic.
        
        Args:
            topic: The topic/channel name to publish to
            data: Event data to be sent to subscribers
        """
        if topic not in self.subscribers:
            logger.debug(f"No subscribers for topic: {topic}")
            return
            
        tasks = []
        for callback in self.subscribers[topic]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(asyncio.create_task(callback(data)))
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"Error calling subscriber for topic {topic}: {e}")
        
        # Wait for all async callbacks to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def subscribe(self, topic: str, callback: Callable) -> None:
        """
        Subscribe to a topic to receive events.
        
        Args:
            topic: The topic/channel name to subscribe to
            callback: Function to call when an event is published to the topic
        """
        if topic not in self.subscribers:
            self.subscribers[topic] = set()
            
        self.subscribers[topic].add(callback)
        logger.debug(f"Added subscriber to topic: {topic}")
    
    def unsubscribe(self, topic: str, callback: Callable) -> None:
        """
        Unsubscribe from a topic.
        
        Args:
            topic: The topic/channel name to unsubscribe from
            callback: Function to remove from subscribers
        """
        if topic in self.subscribers and callback in self.subscribers[topic]:
            self.subscribers[topic].remove(callback)
            logger.debug(f"Removed subscriber from topic: {topic}")
            
            # Clean up empty subscriber sets
            if not self.subscribers[topic]:
                del self.subscribers[topic]

# Global event bus instance for application-wide events
global_event_bus = EventBus()
