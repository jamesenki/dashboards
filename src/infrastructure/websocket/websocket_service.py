#!/usr/bin/env python3
"""
WebSocket Service for IoTSphere

This module provides a WebSocket server that bridges between the internal message bus
and browser clients, enabling real-time updates to the user interface.
"""
import os
import json
import logging
import asyncio
import uuid
import websockets
from datetime import datetime
import threading

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default WebSocket server configuration
DEFAULT_WS_HOST = os.environ.get('WS_HOST', '0.0.0.0')
DEFAULT_WS_PORT = int(os.environ.get('WS_PORT', 8765))

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
        self.subscriptions = set()  # Track which device IDs this client is subscribed to
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
                    message_type = data.get('type')
                    
                    # Process different message types
                    if message_type == 'subscribe':
                        device_id = data.get('device_id')
                        if device_id:
                            self.subscriptions.add(device_id)
                            logger.info(f"Client {self.client_id} subscribed to device {device_id}")
                            
                            # Send acknowledgment
                            await self.send(json.dumps({
                                'type': 'subscribe_ack',
                                'device_id': device_id,
                                'success': True
                            }))
                    
                    elif message_type == 'unsubscribe':
                        device_id = data.get('device_id')
                        if device_id and device_id in self.subscriptions:
                            self.subscriptions.remove(device_id)
                            logger.info(f"Client {self.client_id} unsubscribed from device {device_id}")
                            
                            # Send acknowledgment
                            await self.send(json.dumps({
                                'type': 'unsubscribe_ack',
                                'device_id': device_id,
                                'success': True
                            }))
                    
                    # Forward commands to parent WebSocketService
                    elif message_type == 'command':
                        # This will be handled by the parent service
                        # which has access to the message bus for command publishing
                        pass
                    
                except json.JSONDecodeError:
                    logger.warning(f"Received invalid JSON from client {self.client_id}")
                except Exception as e:
                    logger.error(f"Error processing message from client {self.client_id}: {e}")
        
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
        await client.send(json.dumps({
            'type': 'connection_ack',
            'client_id': client.client_id,
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        # Listen for messages from client
        await client.listen()
        
        # Remove client when disconnected
        if client.client_id in self.clients:
            del self.clients[client.client_id]
    
    async def start_server(self):
        """Start WebSocket server"""
        self.server = await websockets.serve(self.handle_connection, self.host, self.port)
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
        """Start the WebSocket service"""
        try:
            # Subscribe to message bus topics
            if self.message_bus:
                self.message_bus.subscribe("device.telemetry", self.handle_device_telemetry)
                self.message_bus.subscribe("device.event", self.handle_device_event)
                self.message_bus.subscribe("device.command_response", self.handle_command_response)
            
            # Start server in a background thread
            server_thread = threading.Thread(target=self._run_server, daemon=True)
            server_thread.start()
            
            # If we have an external event loop, use that instead
            loop = asyncio.get_event_loop()
            self.server_task = loop.create_task(self.start_server())
            
            logger.info("WebSocket service started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting WebSocket service: {e}")
            return False
    
    def stop(self):
        """Stop the WebSocket service"""
        try:
            # Unsubscribe from message bus
            if self.message_bus:
                self.message_bus.unsubscribe("device.telemetry", self.handle_device_telemetry)
                self.message_bus.unsubscribe("device.event", self.handle_device_event)
                self.message_bus.unsubscribe("device.command_response", self.handle_command_response)
            
            # Close all client connections
            if self.loop:
                for client_id, client in list(self.clients.items()):
                    if client.is_connected:
                        asyncio.run_coroutine_threadsafe(
                            client.websocket.close(),
                            self.loop
                        )
            
            # Close server
            if self.server:
                self.server.close()
                if self.loop:
                    asyncio.run_coroutine_threadsafe(
                        self.server.wait_closed(),
                        self.loop
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
                "simulated": event.get("simulated", False)
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
                "simulated": event.get("simulated", False)
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
                "simulated": event.get("simulated", False)
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
            if (not client.subscriptions or          # Empty means subscribed to all
                device_id in client.subscriptions or # Specific device subscription
                "*" in client.subscriptions):        # Wildcard subscription
                
                if client.is_connected:
                    # Send message via event loop
                    asyncio.run_coroutine_threadsafe(
                        client.send(message),
                        self.loop
                    )
    
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
            self.message_bus.publish("device.command", {
                "event_id": str(uuid.uuid4()),
                "event_type": "device.command",
                "device_id": device_id,
                "command_id": command["command_id"],
                "command": command.get("command"),
                "params": command.get("params", {}),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Sent command to device {device_id}: {command.get('command')}")
            return command["command_id"]
            
        except Exception as e:
            logger.error(f"Error sending command to device {device_id}: {e}")
            return None
