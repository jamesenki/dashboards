#!/usr/bin/env python3
"""
Unit tests for MQTT adapter
"""
import os
import json
import unittest
from unittest.mock import patch, MagicMock, call
import sys

# Add the src directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

class TestMqttAdapter(unittest.TestCase):
    """Test suite for MQTT adapter"""
    
    def setUp(self):
        """Setup test fixtures"""
        # Import here to allow patching
        from src.infrastructure.messaging.mqtt_adapter import MqttAdapter
        
        # Create adapter with mocked MQTT client and message bus
        self.mqtt_client = MagicMock()
        self.message_bus = MagicMock()
        
        self.adapter = MqttAdapter(
            mqtt_client=self.mqtt_client,
            message_bus=self.message_bus
        )
    
    def test_initialization(self):
        """Test adapter initialization"""
        self.assertEqual(self.adapter.mqtt_client, self.mqtt_client)
        self.assertEqual(self.adapter.message_bus, self.message_bus)
    
    def test_start(self):
        """Test starting the adapter"""
        # Call start
        self.adapter.start()
        
        # Verify MQTT client was connected and loop started
        self.mqtt_client.connect.assert_called_once()
        self.mqtt_client.loop_start.assert_called_once()
        
        # Verify subscription to device topics
        self.mqtt_client.subscribe.assert_called()
        # Should subscribe to wildcard topics for devices
        call_args = self.mqtt_client.subscribe.call_args[0]
        self.assertIn("iotsphere/devices/+/", str(call_args))
    
    def test_stop(self):
        """Test stopping the adapter"""
        # Call stop
        self.adapter.stop()
        
        # Verify MQTT client was stopped
        self.mqtt_client.loop_stop.assert_called_once()
        self.mqtt_client.disconnect.assert_called_once()
    
    def test_on_message_telemetry(self):
        """Test handling of telemetry messages"""
        # Create mock telemetry message
        device_id = "test-device-001"
        telemetry = {
            "temperature_current": 120.5,
            "device_id": device_id,
            "timestamp": "2025-04-06T09:45:00Z",
            "simulated": True
        }
        
        message = MagicMock()
        message.payload = json.dumps(telemetry).encode('utf-8')
        message.topic = f"iotsphere/devices/{device_id}/telemetry"
        
        # Call message handler
        self.adapter.on_message(None, None, message)
        
        # Verify message was published to message bus
        self.message_bus.publish.assert_called_once()
        call_args = self.message_bus.publish.call_args[0]
        
        # Should publish to telemetry topic
        self.assertEqual(call_args[0], "device.telemetry")
        
        # Check event data structure
        event_data = call_args[1]
        self.assertEqual(event_data["device_id"], device_id)
        self.assertTrue(event_data["simulated"])
        self.assertEqual(event_data["data"]["temperature_current"], 120.5)
    
    def test_on_message_command_response(self):
        """Test handling of command response messages"""
        # Create mock command response message
        device_id = "test-device-001"
        command_response = {
            "device_id": device_id,
            "command": "set_temperature",
            "status": "success",
            "timestamp": "2025-04-06T09:45:00Z",
            "simulated": True
        }
        
        message = MagicMock()
        message.payload = json.dumps(command_response).encode('utf-8')
        message.topic = f"iotsphere/devices/{device_id}/command_response"
        
        # Call message handler
        self.adapter.on_message(None, None, message)
        
        # Verify message was published to message bus
        self.message_bus.publish.assert_called_once()
        call_args = self.message_bus.publish.call_args[0]
        
        # Should publish to command response topic
        self.assertEqual(call_args[0], "device.command_response")
        
        # Check event data structure
        event_data = call_args[1]
        self.assertEqual(event_data["device_id"], device_id)
        self.assertEqual(event_data["command"], "set_temperature")
        self.assertEqual(event_data["status"], "success")
    
    def test_on_message_event(self):
        """Test handling of device event messages"""
        # Create mock device event message
        device_id = "test-device-001"
        event = {
            "device_id": device_id,
            "event_type": "error_occurred",
            "severity": "error",
            "message": "Error condition",
            "timestamp": "2025-04-06T09:45:00Z",
            "simulated": True
        }
        
        message = MagicMock()
        message.payload = json.dumps(event).encode('utf-8')
        message.topic = f"iotsphere/devices/{device_id}/events"
        
        # Call message handler
        self.adapter.on_message(None, None, message)
        
        # Verify message was published to message bus
        self.message_bus.publish.assert_called_once()
        call_args = self.message_bus.publish.call_args[0]
        
        # Should publish to device event topic
        self.assertEqual(call_args[0], "device.event")
        
        # Check event data structure
        event_data = call_args[1]
        self.assertEqual(event_data["device_id"], device_id)
        self.assertEqual(event_data["event_type"], "error_occurred")
        self.assertEqual(event_data["severity"], "error")

    def test_publish_command(self):
        """Test sending command to device"""
        # Setup
        device_id = "test-device-001"
        command = {
            "command": "set_temperature",
            "setpoint": 125.0
        }
        
        # Call method
        self.adapter.publish_command(device_id, command)
        
        # Verify MQTT publish was called with correct topic and payload
        self.mqtt_client.publish.assert_called_once()
        call_args = self.mqtt_client.publish.call_args[0]
        
        # Check topic
        self.assertEqual(call_args[0], f"iotsphere/devices/{device_id}/commands")
        
        # Check payload
        payload = json.loads(call_args[1])
        self.assertEqual(payload["command"], "set_temperature")
        self.assertEqual(payload["setpoint"], 125.0)
        
if __name__ == '__main__':
    unittest.main()
