"""
Shadow Notification Service for IoTSphere platform.

This service listens for shadow updates and notifies connected clients
via WebSockets and other channels.
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ShadowNotificationService:
    """
    Shadow notification service for real-time updates.

    This service:
    1. Listens for shadow update events
    2. Notifies connected clients through appropriate channels
    3. Integrates with WebSocket manager for real-time updates
    """

    def __init__(self, shadow_service, ws_manager):
        """
        Initialize the shadow notification service.

        Args:
            shadow_service: Service for managing device shadows
            ws_manager: WebSocket manager for client connections
        """
        self.shadow_service = shadow_service
        self.ws_manager = ws_manager
        self._event_handlers = {}
        logger.info("Shadow Notification Service initialized")

    async def start(self):
        """Start listening for shadow update events"""
        # In a real implementation, this would register with an event bus
        # For now, we'll set up a direct callback from the shadow service
        logger.info("Shadow notification service started")

    async def handle_shadow_update(self, device_id: str, update_data: Dict[str, Any]):
        """
        Handle a shadow update event.

        Args:
            device_id: Device identifier
            update_data: Shadow update data
        """
        logger.debug(f"Shadow update received for {device_id}")

        try:
            # Notify WebSocket clients
            if self.ws_manager:
                message = json.dumps(update_data)
                await self.ws_manager.broadcast_to_device(device_id, message)
                logger.debug(f"WebSocket notification sent for {device_id}")

            # Trigger any registered event handlers
            await self._trigger_event_handlers(device_id, update_data)

        except Exception as e:
            logger.error(f"Error handling shadow update for {device_id}: {e}")

    def register_event_handler(self, device_id: str, handler):
        """
        Register an event handler for shadow updates.

        Args:
            device_id: Device identifier
            handler: Async function to call on updates
        """
        if device_id not in self._event_handlers:
            self._event_handlers[device_id] = set()

        self._event_handlers[device_id].add(handler)
        logger.debug(f"Event handler registered for {device_id}")

    def unregister_event_handler(self, device_id: str, handler):
        """
        Unregister an event handler.

        Args:
            device_id: Device identifier
            handler: Handler to unregister
        """
        if device_id in self._event_handlers:
            self._event_handlers[device_id].discard(handler)
            logger.debug(f"Event handler unregistered for {device_id}")

    async def _trigger_event_handlers(
        self, device_id: str, update_data: Dict[str, Any]
    ):
        """
        Trigger registered event handlers.

        Args:
            device_id: Device identifier
            update_data: Shadow update data
        """
        if device_id not in self._event_handlers:
            return

        for handler in self._event_handlers[device_id]:
            try:
                await handler(device_id, update_data)
            except Exception as e:
                logger.error(f"Error in event handler for {device_id}: {e}")
