#!/usr/bin/env python3
"""
Unit tests for WebSocket service
"""
import os
import json
import unittest
from unittest.mock import patch, MagicMock, call
import asyncio
import sys
import websockets

# Add the src directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

class TestWebSocketService(unittest.TestCase):
    """Test suite for WebSocket service"""
    
    def setUp(self):
        """Setup test fixtures"""
        # Import here to allow patching
        from src.infrastructure.websocket.websocket_service import WebSocketService, WebSocketClient
        
        # Create service with mocked message bus
        self.message_bus = MagicMock()
        self.websocket_service = WebSocketService(message_bus=self.message_bus)
        
        # Mock connected clients
        self.mock_client = MagicMock()
        self.mock_client.is_connected = True
        self.mock_client.send = MagicMock()
        self.websocket_service.clients = {"client-123": self.mock_client}
    
    def test_initialization(self):
        """Test service initialization"""
        self.assertEqual(self.websocket_service.message_bus, self.message_bus)
        self.assertEqual(self.websocket_service.port, 8765)  # Default port
    
    def test_handle_device_telemetry(self):
        """Test handling device telemetry events"""
        # Create sample telemetry event
        device_id = "test-device-001"
        topic = "device.telemetry"
        event = {
            "event_id": "1234",
            "event_type": "device.telemetry",
            "device_id": device_id,
            "timestamp": "2025-04-06T10:00:00Z",
            "data": {
                "temperature_current": 120.5,
                "heating_status": True
            },
            "simulated": True
        }
        
        # Call handler
        self.websocket_service.handle_device_telemetry(topic, event)
        
        # Verify message was sent to client
        self.mock_client.send.assert_called_once()
        call_args = self.mock_client.send.call_args[0]
        
        # Parse the message that would be sent to the client
        message = json.loads(call_args[0])
        
        # Verify message content
        self.assertEqual(message["type"], "telemetry")
        self.assertEqual(message["device_id"], device_id)
        self.assertEqual(message["data"]["temperature_current"], 120.5)
        self.assertEqual(message["data"]["heating_status"], True)
        self.assertTrue(message["simulated"])
    
    def test_handle_device_event(self):
        """Test handling device events"""
        # Create sample device event
        device_id = "test-device-001"
        topic = "device.event"
        event = {
            "event_id": "5678",
            "event_type": "error_occurred",
            "device_id": device_id,
            "timestamp": "2025-04-06T10:00:00Z",
            "severity": "error",
            "message": "Device error",
            "details": {"error_code": "E01"},
            "simulated": True
        }
        
        # Call handler
        self.websocket_service.handle_device_event(topic, event)
        
        # Verify message was sent to client
        self.mock_client.send.assert_called_once()
        call_args = self.mock_client.send.call_args[0]
        
        # Parse the message that would be sent to the client
        message = json.loads(call_args[0])
        
        # Verify message content
        self.assertEqual(message["type"], "event")
        self.assertEqual(message["device_id"], device_id)
        self.assertEqual(message["event_type"], "error_occurred")
        self.assertEqual(message["severity"], "error")
        self.assertEqual(message["details"]["error_code"], "E01")
        self.assertTrue(message["simulated"])
    
    def test_handle_command_response(self):
        """Test handling command responses"""
        # Create sample command response
        device_id = "test-device-001"
        topic = "device.command_response"
        response = {
            "event_id": "9012",
            "event_type": "device.command_response",
            "device_id": device_id,
            "command_id": "cmd-123",
            "command": "set_temperature",
            "status": "success",
            "message": "Temperature set",
            "timestamp": "2025-04-06T10:00:00Z",
            "simulated": True
        }
        
        # Call handler
        self.websocket_service.handle_command_response(topic, response)
        
        # Verify message was sent to client
        self.mock_client.send.assert_called_once()
        call_args = self.mock_client.send.call_args[0]
        
        # Parse the message that would be sent to the client
        message = json.loads(call_args[0])
        
        # Verify message content
        self.assertEqual(message["type"], "command_response")
        self.assertEqual(message["device_id"], device_id)
        self.assertEqual(message["command"], "set_temperature")
        self.assertEqual(message["status"], "success")
        self.assertTrue(message["simulated"])
    
    @patch('src.infrastructure.websocket.websocket_service.asyncio.get_event_loop')
    def test_start_service(self, mock_get_event_loop):
        """Test starting the WebSocket service"""
        # Setup mocks
        mock_loop = MagicMock()
        mock_get_event_loop.return_value = mock_loop
        
        # Call start
        self.websocket_service.start()
        
        # Verify subscriptions to message bus topics
        self.message_bus.subscribe.assert_any_call("device.telemetry", self.websocket_service.handle_device_telemetry)
        self.message_bus.subscribe.assert_any_call("device.event", self.websocket_service.handle_device_event)
        self.message_bus.subscribe.assert_any_call("device.command_response", self.websocket_service.handle_command_response)
        
        # Verify server was started
        mock_loop.create_task.assert_called_once()
    
    def test_stop_service(self):
        """Test stopping the WebSocket service"""
        # Setup mock
        self.websocket_service.server = MagicMock()
        
        # Call stop
        self.websocket_service.stop()
        
        # Verify server was closed
        self.websocket_service.server.close.assert_called_once()
        
        # Verify disconnection from message bus
        self.message_bus.unsubscribe.assert_any_call("device.telemetry", self.websocket_service.handle_device_telemetry)
        self.message_bus.unsubscribe.assert_any_call("device.event", self.websocket_service.handle_device_event)
        self.message_bus.unsubscribe.assert_any_call("device.command_response", self.websocket_service.handle_command_response)
    
    @patch('src.infrastructure.websocket.websocket_service.WebSocketClient')
    async def test_handle_new_connection(self, mock_client_class):
        """Test handling new WebSocket connections"""
        # Setup mocks
        mock_websocket = MagicMock()
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Create a client ID (this would normally be generated)
        client_id = "client-456"
        
        # Call handler (directly, to bypass asyncio)
        await self.websocket_service.handle_connection(mock_websocket, {})
        
        # Verify client was created and stored
        mock_client_class.assert_called_once()
        
        # Verify client listen method was called
        mock_client.listen.assert_called_once()

if __name__ == '__main__':
    unittest.main()
