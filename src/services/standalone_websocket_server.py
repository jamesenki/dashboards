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

# Import standardized environment variable names
try:
    from src.infrastructure.websocket.websocket_manager import (
        ENV_ACTIVE_WS_PORT,
        ENV_WS_DISABLED,
        ENV_WS_HOST,
        ENV_WS_INIT_ATTEMPTED,
        ENV_WS_INITIALIZED,
        ENV_WS_PORT,
        ENV_WS_PORT_UNAVAILABLE,
        get_websocket_service,
    )

    _USING_MANAGER = True
except ImportError:
    # Fallback environment variables if manager not available
    ENV_WS_HOST = "WS_HOST"
    ENV_WS_PORT = "WS_PORT"
    ENV_WS_DISABLED = "DISABLE_WEBSOCKET"
    ENV_WS_INIT_ATTEMPTED = "WEBSOCKET_INIT_ATTEMPTED"
    ENV_WS_INITIALIZED = "WEBSOCKET_INITIALIZED"
    ENV_WS_PORT_UNAVAILABLE = "WEBSOCKET_PORT_UNAVAILABLE"
    ENV_ACTIVE_WS_PORT = "ACTIVE_WS_PORT"
    _USING_MANAGER = False

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
        # CRITICAL: First check if infrastructure WebSocket service is already running
        # If it is, we should use that instead of starting a new one
        if os.environ.get(ENV_WS_INITIALIZED, "false").lower() == "true":
            logger.warning(
                "Infrastructure WebSocket service already running - standalone server will not initialize"
            )
            self.enabled = False
        else:
            self.enabled = os.environ.get(ENV_WS_DISABLED, "false").lower() != "true"

        # Track if we already tried to start this server
        self._start_attempted = False

        self.app = app
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_count = 0
        self.running = False

        # Use the standardized environment variables
        self.default_port = int(os.environ.get(ENV_WS_PORT, "8912"))

        # If infrastructure WebSocket has claimed a port, use that
        active_port = os.environ.get(ENV_ACTIVE_WS_PORT)
        if active_port:
            self.port = int(active_port)
            logger.info(f"Using active WebSocket port from infrastructure: {self.port}")
        else:
            self.port = self.default_port

        logger.info(
            f"Standalone WebSocket server initialized (port {self.port}, enabled: {self.enabled})"
        )

    async def start(self) -> None:
        """Start the WebSocket server."""
        # Check if already disabled or previously attempted to start
        if not self.enabled:
            logger.warning("Standalone WebSocket server is disabled - not starting")
            return

        if self._start_attempted:
            logger.warning(
                "Standalone WebSocket server was already started - not starting again"
            )
            return

        # Mark that we attempted to start
        self._start_attempted = True

        # Check if infrastructure WebSocket is already running
        if os.environ.get(ENV_WS_INITIALIZED, "false").lower() == "true":
            logger.warning(
                "Infrastructure WebSocket already running - not starting standalone server"
            )
            # Set infrastructure port for client connections
            active_port = os.environ.get(ENV_ACTIVE_WS_PORT)
            if active_port:
                self.port = int(active_port)
            return

        # This server integrates with FastAPI's WebSocket handling
        # so we don't need to start a separate server process.
        logger.info(f"Standalone WebSocket server starting on port: {self.port}")

        # Mark as initialized to prevent other services from starting
        os.environ[ENV_WS_INITIALIZED] = "true"
        os.environ[ENV_ACTIVE_WS_PORT] = str(self.port)

        # Import socket module for port checking
        import socket

        # Try a range of ports if the default is not available
        available_port_found = False
        alternate_ports = [
            7890,
            7891,
            7892,
            7893,
            7894,
            7895,
            7896,
            7897,
            7898,
            7899,
            8900,
            8901,
        ]

        # Also check if the problematic port 9090 is in use and log a warning if it is
        problem_port_check = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            problem_port_check.settimeout(0.5)
            problem_port_check.bind(("0.0.0.0", 9090))
            problem_port_check.close()
            logger.info("Port 9090 is not in use by another process")
        except socket.error:
            logger.warning(
                "Port 9090 is in use by another process. This may cause conflicts with other WebSocket services."
            )
            try:
                problem_port_check.close()
            except:
                pass

        # Try to find an available port
        for port in [self.default_port] + alternate_ports:
            port_check_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                # Set socket options to allow immediate reuse
                port_check_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # Short timeout
                port_check_socket.settimeout(0.5)
                # Try to bind to the port and immediately release it
                port_check_socket.bind(("0.0.0.0", port))
                port_check_socket.close()
                # Found an available port
                self.port = port
                available_port_found = True
                logger.info(f"Port {self.port} verified available for WebSocket")
                break
            except socket.error as e:
                logger.warning(
                    f"Port {port} appears to be in use by another process: {e}"
                )
                try:
                    port_check_socket.close()
                except:
                    pass

        if not available_port_found:
            logger.error("Could not find an available port for the WebSocket server")
            logger.warning("WebSocket functionality will be limited")
            # Set running to False to indicate that the server is not properly started
            self.running = False
            return

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


def get_websocket_server(
    app: Optional[FastAPI] = None,
) -> Optional[StandaloneWebSocketServer]:
    """
    Get or create the WebSocket server instance, but only if WebSocketServiceManager isn't already running.
    This function enforces the single WebSocket server policy.

    Args:
        app: FastAPI application instance (required first time)

    Returns:
        StandaloneWebSocketServer instance or None if WebSocketServiceManager is active
    """
    global _websocket_server_instance

    # Check if the centralized WebSocketServiceManager is active and has initialized a server
    if _USING_MANAGER:
        # If WebSocketServiceManager initialized a service, don't create a duplicate standalone server
        if os.environ.get(ENV_WS_INITIALIZED) == "true":
            logger.info(
                "WebSocketServiceManager has already initialized a WebSocket server. "
                "Standalone server will not be created."
            )
            return None

    # Check if we're disabled globally
    if os.environ.get(ENV_WS_DISABLED, "").lower() in ("true", "1", "yes"):
        logger.info("WebSocket server disabled via environment variable")
        return None

    # Only create if we haven't already
    if _websocket_server_instance is None:
        if app is None:
            raise ValueError(
                "FastAPI app instance required to initialize WebSocket server"
            )

        # Set flag to indicate we're attempting initialization
        os.environ[ENV_WS_INIT_ATTEMPTED] = "true"

        logger.info("Creating standalone WebSocket server")
        _websocket_server_instance = StandaloneWebSocketServer(app)

        # Record successful initialization
        if _websocket_server_instance:
            os.environ[ENV_WS_INITIALIZED] = "true"

    return _websocket_server_instance
