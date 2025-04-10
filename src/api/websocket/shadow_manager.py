"""
WebSocket Manager for device shadow real-time updates.

DEPRECATED: This module is deprecated in favor of the Message Broker Pattern
implementation as described in ADR-0001. Please use the MQTT-WebSocket Bridge instead.

This module manages WebSocket connections for device shadow updates,
following Clean Architecture by keeping delivery mechanism details separate.
"""
from typing import Any, Dict, List

from fastapi import WebSocket


class ShadowWebSocketManager:
    """Manages WebSocket connections for device shadow updates.

    DEPRECATED: This class is deprecated in favor of the MQTT-WebSocket Bridge 
    implementation as described in ADR-0001.
    
    This class handles the delivery of real-time updates to connected clients,
    maintaining a mapping of device IDs to connected WebSockets.
    """

    def __init__(self):
        """Initialize the manager."""
        # Maps device IDs to a list of connected WebSockets
        self.connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, device_id: str, websocket: WebSocket) -> None:
        """Register a new WebSocket connection for a device.

        Args:
            device_id: The ID of the device to register for
            websocket: The WebSocket connection to register
        """
        # Create an entry for the device if it doesn't exist
        if device_id not in self.connections:
            self.connections[device_id] = []

        # Add the WebSocket to the device's connections
        self.connections[device_id].append(websocket)

    async def disconnect(self, device_id: str, websocket: WebSocket) -> None:
        """Remove a WebSocket connection for a device.

        Args:
            device_id: The ID of the device
            websocket: The WebSocket connection to remove
        """
        # Check if the device has any connections
        if device_id in self.connections:
            # Remove the WebSocket from the device's connections
            if websocket in self.connections[device_id]:
                self.connections[device_id].remove(websocket)

            # Remove the device entry if it has no more connections
            if not self.connections[device_id]:
                del self.connections[device_id]

    async def broadcast_to_device(
        self, device_id: str, message: Dict[str, Any], exclude: WebSocket = None
    ) -> None:
        """Broadcast a message to all WebSockets for a device.

        Args:
            device_id: The ID of the device to broadcast to
            message: The message to broadcast
            exclude: Optional WebSocket to exclude from broadcast
        """
        # Check if the device has any connections
        if device_id not in self.connections:
            return

        # Send the message to all connected WebSockets except the excluded one
        for websocket in self.connections[device_id]:
            if websocket != exclude:
                try:
                    await websocket.send_json(message)
                except:
                    # If sending fails, remove the WebSocket
                    await self.disconnect(device_id, websocket)

    async def broadcast_to_all(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all connected WebSockets.

        Args:
            message: The message to broadcast
        """
        # Create a list of all WebSockets to avoid modifying during iteration
        all_websockets = [
            websocket
            for connections in self.connections.values()
            for websocket in connections
        ]

        # Send the message to all connected WebSockets
        for websocket in all_websockets:
            try:
                await websocket.send_json(message)
            except:
                # Find which device this WebSocket belongs to
                for device_id, connections in self.connections.items():
                    if websocket in connections:
                        await self.disconnect(device_id, websocket)
                        break
