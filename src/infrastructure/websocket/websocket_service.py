#!/usr/bin/env python3
"""
WebSocket Service for IoTSphere

This module provides a WebSocket server that bridges between the internal message bus
and browser clients, enabling real-time updates to the user interface.
"""
import asyncio
import json
import logging
import os
import threading
import uuid
from datetime import datetime

import websockets

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import standardized environment variable names from websocket_manager
from src.infrastructure.websocket.websocket_manager import (
    ENV_ACTIVE_WS_PORT,
    ENV_WS_DISABLED,
    ENV_WS_HOST,
    ENV_WS_INIT_ATTEMPTED,
    ENV_WS_INITIALIZED,
    ENV_WS_PORT,
    ENV_WS_PORT_UNAVAILABLE,
)

# Default WebSocket server configuration
DEFAULT_WS_HOST = os.environ.get(ENV_WS_HOST, "0.0.0.0")
# Using port 8912 to avoid conflicts with other services
# Previous ports (8765, 9090) have had conflict issues
DEFAULT_WS_PORT = int(os.environ.get(ENV_WS_PORT, 8912))

# Check early if we're disabled or already initialized
_ENABLE_WEBSOCKET = os.environ.get(ENV_WS_DISABLED, "false").lower() != "true"
_ALREADY_INITIALIZED = os.environ.get(ENV_WS_INITIALIZED, "false").lower() == "true"


class WebSocketClient:
    """
    Represents a connected WebSocket client.

    Manages connection state and message sending for an individual browser client.
    """

    def __init__(self, websocket, client_id=None):
        """
        Initialize WebSocket client

        Args:
            websocket: WebSocket connection object
            client_id: Optional client identifier (generated if not provided)
        """
        self.websocket = websocket
        self.client_id = client_id or str(uuid.uuid4())
        self.is_connected = True
        self.subscriptions = (
            set()
        )  # Track which device IDs this client is subscribed to
        logger.info(f"New WebSocket client connected: {self.client_id}")

    async def send(self, message):
        """
        Send message to client

        Args:
            message (str): JSON message to send

        Returns:
            bool: Success status
        """
        try:
            if self.is_connected:
                await self.websocket.send(message)
                return True
            return False
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed while sending to client {self.client_id}")
            self.is_connected = False
            return False
        except Exception as e:
            logger.error(f"Error sending message to client {self.client_id}: {e}")
            return False

    async def listen(self):
        """
        Listen for incoming messages from client

        This method processes messages like:
        - subscribe: Subscribe to device updates
        - unsubscribe: Unsubscribe from device updates
        - command: Send command to device
        """
        try:
            async for message in self.websocket:
                try:
                    # Parse message
                    data = json.loads(message)
                    message_type = data.get("type")

                    # Process different message types
                    if message_type == "subscribe":
                        device_id = data.get("device_id")
                        if device_id:
                            self.subscriptions.add(device_id)
                            logger.info(
                                f"Client {self.client_id} subscribed to device {device_id}"
                            )

                            # Send acknowledgment
                            await self.send(
                                json.dumps(
                                    {
                                        "type": "subscribe_ack",
                                        "device_id": device_id,
                                        "success": True,
                                    }
                                )
                            )

                    elif message_type == "unsubscribe":
                        device_id = data.get("device_id")
                        if device_id and device_id in self.subscriptions:
                            self.subscriptions.remove(device_id)
                            logger.info(
                                f"Client {self.client_id} unsubscribed from device {device_id}"
                            )

                            # Send acknowledgment
                            await self.send(
                                json.dumps(
                                    {
                                        "type": "unsubscribe_ack",
                                        "device_id": device_id,
                                        "success": True,
                                    }
                                )
                            )

                    # Forward commands to parent WebSocketService
                    elif message_type == "command":
                        # This will be handled by the parent service
                        # which has access to the message bus for command publishing
                        pass

                except json.JSONDecodeError:
                    logger.warning(
                        f"Received invalid JSON from client {self.client_id}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error processing message from client {self.client_id}: {e}"
                    )

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection closed for client {self.client_id}")
        except Exception as e:
            logger.error(f"Error in client listener for {self.client_id}: {e}")

        finally:
            # Mark client as disconnected
            self.is_connected = False
            logger.info(f"Client disconnected: {self.client_id}")


class WebSocketService:
    """
    WebSocket server for real-time communications with the UI.

    This service:
    - Accepts WebSocket connections from browser clients
    - Subscribes to relevant topics on the message bus
    - Forwards events to connected clients
    - Processes commands from clients to devices
    """

    def __init__(self, message_bus=None, host=DEFAULT_WS_HOST, port=DEFAULT_WS_PORT):
        """
        Initialize WebSocket service

        Args:
            message_bus: Message bus for communication
            host: Host address to bind to
            port: Port to listen on
        """
        self.message_bus = message_bus
        self.host = host
        self.port = port

        # Connected clients (client_id -> WebSocketClient)
        self.clients = {}

        # Server instance
        self.server = None
        self.loop = None
        self.server_task = None

        logger.info(f"Initialized WebSocket service on {host}:{port}")

    async def handle_connection(self, websocket, path):
        """
        Handle new WebSocket connection

        Args:
            websocket: WebSocket connection object
            path: Connection path
        """
        # Create client
        client = WebSocketClient(websocket)

        # Store client
        self.clients[client.client_id] = client

        # Send connection acknowledgment with client ID
        await client.send(
            json.dumps(
                {
                    "type": "connection_ack",
                    "client_id": client.client_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        )

        # Listen for messages from client
        await client.listen()

        # Remove client when disconnected
        if client.client_id in self.clients:
            del self.clients[client.client_id]

    async def start_server(self):
        """Start WebSocket server"""
        self.server = await websockets.serve(
            self.handle_connection, self.host, self.port
        )
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")

        # Keep server running
        await self.server.wait_closed()

    def _run_server(self):
        """Run server in event loop"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.start_server())
            self.loop.run_forever()
        except Exception as e:
            logger.error(f"Error in WebSocket server: {e}")
        finally:
            if self.loop:
                self.loop.close()

    def start(self):
        """Start the WebSocket service

        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            # First check if WebSocket service is disabled or already initialized elsewhere
            if os.environ.get(ENV_WS_DISABLED, "false").lower() == "true":
                logger.warning("WebSocket service disabled by environment variable")
                return False

            # Check if we've already attempted to start this instance
            if hasattr(self, "_start_attempted") and self._start_attempted:
                logger.warning(
                    "WebSocket service start already attempted on this instance - skipping"
                )
                return False

            # Mark that we've attempted to start this instance
            self._start_attempted = True
            logger.info(f"Starting WebSocket service on {self.host}:{self.port}")

            # Subscribe to message bus topics
            if self.message_bus:
                logger.info("Subscribing to message bus topics for real-time updates")
                self.message_bus.subscribe(
                    "device.telemetry", self.handle_device_telemetry
                )
                self.message_bus.subscribe("device.event", self.handle_device_event)
                self.message_bus.subscribe(
                    "device.command_response", self.handle_command_response
                )

            # Use the active port from environment if available
            env_port = os.environ.get(ENV_ACTIVE_WS_PORT)
            if env_port and str(self.port) != env_port:
                logger.info(
                    f"Using environment-specified WebSocket port: {env_port} (was {self.port})"
                )
                self.port = int(env_port)

            # Port selection is now handled by WebSocketServiceManager
            # We only need to check if the current port is available
            if not self._is_port_available(self.port):
                logger.error(
                    f"WebSocket port {self.port} is not available - cannot start server"
                )
                os.environ[ENV_WS_PORT_UNAVAILABLE] = "true"
                return False

            logger.info(
                f"WebSocket port {self.port} is available - proceeding with server startup"
            )

            logger.info(f"Starting WebSocket server on ws://{self.host}:{self.port}")

            # Start server in a background thread ONLY - removed duplicate server initialization
            server_thread = threading.Thread(target=self._run_server, daemon=True)
            server_thread.start()

            # Set environment variables to track WebSocket state
            os.environ[ENV_ACTIVE_WS_PORT] = str(self.port)
            os.environ[ENV_WS_INITIALIZED] = "true"

            logger.info("WebSocket service started successfully")
            return True

        except Exception as e:
            logger.error(f"Error starting WebSocket service: {e}")
            return False

    def _is_port_available(self, port):
        """Check if the given port is available for binding.

        Args:
            port (int): Port number to check

        Returns:
            bool: True if port is available, False otherwise
        """
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Set socket options to allow immediate reuse
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Use a short timeout for quick response
            sock.settimeout(0.5)
            # Try to bind to the port
            sock.bind((self.host, port))
            return True
        except socket.error:
            return False
        finally:
            sock.close()

    def stop(self):
        """Stop the WebSocket service"""
        try:
            # Unsubscribe from message bus
            if self.message_bus:
                self.message_bus.unsubscribe(
                    "device.telemetry", self.handle_device_telemetry
                )
                self.message_bus.unsubscribe("device.event", self.handle_device_event)
                self.message_bus.unsubscribe(
                    "device.command_response", self.handle_command_response
                )

            # Close all client connections
            if self.loop:
                for client_id, client in list(self.clients.items()):
                    if client.is_connected:
                        asyncio.run_coroutine_threadsafe(
                            client.websocket.close(), self.loop
                        )

            # Close server
            if self.server:
                self.server.close()
                if self.loop:
                    asyncio.run_coroutine_threadsafe(
                        self.server.wait_closed(), self.loop
                    )

            logger.info("WebSocket service stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping WebSocket service: {e}")
            return False

    def handle_device_telemetry(self, topic, event):
        """
        Handle device telemetry events

        Args:
            topic (str): Message topic
            event (dict): Event data
        """
        try:
            device_id = event.get("device_id")
            if not device_id:
                return

            # Create WebSocket message
            message = {
                "type": "telemetry",
                "device_id": device_id,
                "timestamp": event.get("timestamp", datetime.utcnow().isoformat()),
                "data": event.get("data", {}),
                "simulated": event.get("simulated", False),
            }

            # Send to interested clients
            self._send_to_clients(device_id, json.dumps(message))

        except Exception as e:
            logger.error(f"Error handling device telemetry: {e}")

    def handle_device_event(self, topic, event):
        """
        Handle device events

        Args:
            topic (str): Message topic
            event (dict): Event data
        """
        try:
            device_id = event.get("device_id")
            if not device_id:
                return

            # Create WebSocket message
            message = {
                "type": "event",
                "device_id": device_id,
                "event_type": event.get("event_type"),
                "severity": event.get("severity", "info"),
                "message": event.get("message", ""),
                "timestamp": event.get("timestamp", datetime.utcnow().isoformat()),
                "details": event.get("details", {}),
                "simulated": event.get("simulated", False),
            }

            # Send to interested clients
            self._send_to_clients(device_id, json.dumps(message))

        except Exception as e:
            logger.error(f"Error handling device event: {e}")

    def handle_command_response(self, topic, event):
        """
        Handle command responses

        Args:
            topic (str): Message topic
            event (dict): Event data
        """
        try:
            device_id = event.get("device_id")
            if not device_id:
                return

            # Create WebSocket message
            message = {
                "type": "command_response",
                "device_id": device_id,
                "command_id": event.get("command_id"),
                "command": event.get("command"),
                "status": event.get("status"),
                "message": event.get("message", ""),
                "timestamp": event.get("timestamp", datetime.utcnow().isoformat()),
                "simulated": event.get("simulated", False),
            }

            # Send to interested clients
            self._send_to_clients(device_id, json.dumps(message))

        except Exception as e:
            logger.error(f"Error handling command response: {e}")

    def _send_to_clients(self, device_id, message):
        """
        Send message to clients subscribed to device

        Args:
            device_id (str): Device identifier
            message (str): JSON message to send
        """
        if not self.loop:
            logger.warning("Cannot send message: event loop not available")
            return

        for client_id, client in list(self.clients.items()):
            # Check if client is subscribed to this device or to all devices
            if (
                not client.subscriptions
                or device_id in client.subscriptions  # Empty means subscribed to all
                or "*" in client.subscriptions  # Specific device subscription
            ):  # Wildcard subscription
                if client.is_connected:
                    # Send message via event loop
                    asyncio.run_coroutine_threadsafe(client.send(message), self.loop)

    def send_command(self, device_id, command):
        """
        Send command to device via message bus

        Args:
            device_id (str): Target device identifier
            command (dict): Command data

        Returns:
            str: Command ID or None if failed
        """
        if not self.message_bus:
            logger.warning("Cannot send command: no message bus available")
            return None

        try:
            # Add command_id if not present
            if "command_id" not in command:
                command["command_id"] = str(uuid.uuid4())

            # Publish command to message bus
            self.message_bus.publish(
                "device.command",
                {
                    "event_id": str(uuid.uuid4()),
                    "event_type": "device.command",
                    "device_id": device_id,
                    "command_id": command["command_id"],
                    "command": command.get("command"),
                    "params": command.get("params", {}),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            logger.info(f"Sent command to device {device_id}: {command.get('command')}")
            return command["command_id"]

        except Exception as e:
            logger.error(f"Error sending command to device {device_id}: {e}")
            return None
