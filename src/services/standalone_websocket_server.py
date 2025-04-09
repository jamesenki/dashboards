"""
Standalone WebSocket server implementation for IoTSphere.

This implementation provides a basic WebSocket server that can be integrated
with the FastAPI application without requiring the full infrastructure module.
"""
import asyncio
import logging
import os
from typing import Any, Awaitable, Callable, Dict, Optional, Set

from fastapi import FastAPI
from starlette.websockets import WebSocket

logger = logging.getLogger(__name__)


class StandaloneWebSocketServer:
    """
    WebSocket server that integrates with FastAPI WebSocket endpoints.

    This server replaces the more complex infrastructure.websocket implementation
    with a simple integration that works directly with FastAPI's WebSocket routes.
    """

    def __init__(self, app: FastAPI):
        """
        Initialize the WebSocket server.

        Args:
            app: FastAPI application instance
        """
        self.app = app
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_count = 0
        self.running = False

        # Get configured WebSocket port from environment
        self.port = int(os.environ.get("WEBSOCKET_PORT", "7777"))
        logger.info(f"Standalone WebSocket server initialized (port {self.port})")

    async def start(self) -> None:
        """Start the WebSocket server."""
        # This server integrates with FastAPI's WebSocket handling
        # so we don't need to start a separate server process.

        # Log the port we're using for debugging
        logger.info(f"Standalone WebSocket server starting on port: {self.port}")

        # Import socket module for port checking
        import socket

        # Perform a quick check to see if this port is already in use
        port_check_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Set socket options to allow immediate reuse
            port_check_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Short timeout
            port_check_socket.settimeout(0.5)
            # Try to bind to the port and immediately release it
            port_check_socket.bind(("0.0.0.0", self.port))
            port_check_socket.close()
            logger.info(f"Port {self.port} verified available for WebSocket")
        except socket.error as e:
            logger.warning(
                f"Port {self.port} appears to be in use by another process: {e}"
            )
            logger.warning(
                "This may cause connection issues if the infrastructure WebSocket is also running"
            )
            port_check_socket.close()

        self.running = True
        logger.info("Standalone WebSocket server started")

    async def stop(self) -> None:
        """Stop the WebSocket server and close all connections."""
        self.running = False
        # Close all active connections
        for device_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.close()
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")

        self.active_connections.clear()
        logger.info("Standalone WebSocket server stopped")

    async def register_connection(self, websocket: WebSocket, device_id: str) -> None:
        """
        Register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            device_id: Device ID this connection is associated with
        """
        if not self.running:
            logger.warning("Cannot register connection: WebSocket server not running")
            return

        if device_id not in self.active_connections:
            self.active_connections[device_id] = set()

        self.active_connections[device_id].add(websocket)
        self.connection_count += 1
        logger.info(
            f"Connection registered for device {device_id} (total: {self.connection_count})"
        )

    async def unregister_connection(self, websocket: WebSocket, device_id: str) -> None:
        """
        Unregister a WebSocket connection.

        Args:
            websocket: The WebSocket connection
            device_id: Device ID this connection is associated with
        """
        if device_id in self.active_connections:
            if websocket in self.active_connections[device_id]:
                self.active_connections[device_id].remove(websocket)
                self.connection_count -= 1
                logger.info(
                    f"Connection unregistered for device {device_id} (total: {self.connection_count})"
                )

            if not self.active_connections[device_id]:
                del self.active_connections[device_id]

    async def broadcast_to_device(self, device_id: str, message: str) -> int:
        """
        Broadcast a message to all connections for a specific device.

        Args:
            device_id: Device ID to broadcast to
            message: Message to broadcast

        Returns:
            Number of clients the message was sent to
        """
        if not self.running:
            logger.warning("Cannot broadcast: WebSocket server not running")
            return 0

        if device_id not in self.active_connections:
            return 0

        count = 0
        disconnected = []

        for connection in self.active_connections[device_id]:
            try:
                await connection.send_text(message)
                count += 1
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            await self.unregister_connection(connection, device_id)

        return count

    async def broadcast_to_all(self, message: str) -> int:
        """
        Broadcast a message to all connected clients.

        Args:
            message: Message to broadcast

        Returns:
            Number of clients the message was sent to
        """
        if not self.running:
            logger.warning("Cannot broadcast: WebSocket server not running")
            return 0

        count = 0
        for device_id in list(self.active_connections.keys()):
            count += await self.broadcast_to_device(device_id, message)

        return count


# Singleton instance for the application to use
_websocket_server_instance = None


def get_websocket_server(app: Optional[FastAPI] = None) -> StandaloneWebSocketServer:
    """
    Get or create the WebSocket server instance.

    Args:
        app: FastAPI application instance (required first time)

    Returns:
        StandaloneWebSocketServer instance
    """
    global _websocket_server_instance

    if _websocket_server_instance is None:
        if app is None:
            raise ValueError(
                "FastAPI app instance required to initialize WebSocket server"
            )
        _websocket_server_instance = StandaloneWebSocketServer(app)

    return _websocket_server_instance
