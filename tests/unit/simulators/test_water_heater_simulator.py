#!/usr/bin/env python3
"""
Unit tests for water heater simulator
"""
import os
import json
import unittest
from unittest.mock import patch, MagicMock, call
import threading
import time
import sys

# Add the src directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

class TestWaterHeaterSimulator(unittest.TestCase):
    """Test suite for water heater simulator"""
    
    def setUp(self):
        """Setup test fixtures"""
        # Import here to allow patching
        from src.simulators.water_heater.simulator import WaterHeaterSimulator
        
        # Create a simulator with mocked MQTT client
        self.mqtt_client = MagicMock()
        self.device_id = "sim-water-heater-001"
        self.model = "AquaTherm Pro X7"
        self.manufacturer = "Rheem"
        
        self.initial_state = {
            "temperature_current": 120.0,
            "temperature_setpoint": 125.0,
            "heating_status": False,
            "power_consumption_watts": 0.0,
            "water_flow_gpm": 0.0,
            "mode": "standby",
            "error_code": None
        }
        
        self.simulator = WaterHeaterSimulator(
            device_id=self.device_id,
            model=self.model,
            manufacturer=self.manufacturer,
            initial_state=self.initial_state,
            mqtt_client=self.mqtt_client
        )
    
    def test_initialization(self):
        """Test simulator initialization"""
        self.assertEqual(self.simulator.device_id, self.device_id)
        self.assertEqual(self.simulator.model, self.model)
        self.assertEqual(self.simulator.manufacturer, self.manufacturer)
        self.assertEqual(self.simulator.state["temperature_current"], 120.0)
        self.assertEqual(self.simulator.state["temperature_setpoint"], 125.0)
        # Verify simulator is flagged as simulated
        self.assertTrue(self.simulator.simulated)
    
    def test_connect(self):
        """Test MQTT connection"""
        # Call connect
        self.simulator.connect()
        
        # Verify MQTT client was connected
        self.mqtt_client.connect.assert_called_once()
        
        # Verify subscription to command topic
        topic = f"iotsphere/devices/{self.device_id}/commands"
        self.mqtt_client.subscribe.assert_called_with(topic)
        
        # Verify message callback was set
        self.mqtt_client.on_message = self.simulator.on_message
    
    @patch('src.simulators.water_heater.simulator.json')
    def test_publish_telemetry(self, mock_json):
        """Test telemetry publishing"""
        # Setup
        mock_json.dumps.return_value = '{"temperature": 120.0}'
        
        # Call method
        self.simulator.publish_telemetry()
        
        # Verify MQTT publish was called with correct topic
        self.mqtt_client.publish.assert_called_once()
        call_args = self.mqtt_client.publish.call_args[0]
        self.assertEqual(call_args[0], f"iotsphere/devices/{self.device_id}/telemetry")
        
        # Verify telemetry includes simulated flag
        mock_json.dumps.assert_called_once()
        json_args = mock_json.dumps.call_args[0][0]
        self.assertTrue(json_args["simulated"])
    
    def test_handle_set_temperature_command(self):
        """Test handling temperature setpoint command"""
        # Prepare command message
        command = {
            "command": "set_temperature",
            "setpoint": 130.0
        }
        
        # Create mock MQTT message
        message = MagicMock()
        message.payload = json.dumps(command).encode('utf-8')
        message.topic = f"iotsphere/devices/{self.device_id}/commands"
        
        # Call message handler
        self.simulator.on_message(None, None, message)
        
        # Verify state was updated
        self.assertEqual(self.simulator.state["temperature_setpoint"], 130.0)
        
        # Verify acknowledgment was published
        self.mqtt_client.publish.assert_called_once()
        call_args = self.mqtt_client.publish.call_args[0]
        self.assertEqual(call_args[0], f"iotsphere/devices/{self.device_id}/command_response")
        
        # Verify response contains success status
        response = json.loads(call_args[1])
        self.assertEqual(response["status"], "success")
    
    def test_update_simulation(self):
        """Test simulation state updates"""
        # Set initial state for testing
        self.simulator.state["mode"] = "heating"
        self.simulator.state["heating_status"] = True
        self.simulator.state["temperature_current"] = 120.0
        self.simulator.state["temperature_setpoint"] = 130.0
        
        # Call update method (simulates temperature rising)
        self.simulator.update_simulation()
        
        # Verify temperature increased
        self.assertGreater(self.simulator.state["temperature_current"], 120.0)
        
        # Verify power consumption is non-zero during heating
        self.assertGreater(self.simulator.state["power_consumption_watts"], 0)
    
    @patch('threading.Thread')
    def test_start_stop_simulation(self, mock_thread):
        """Test starting and stopping simulation"""
        # Setup mock
        mock_thread.return_value = MagicMock()
        
        # Start simulation
        self.simulator.start()
        
        # Verify thread was started
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()
        
        # Stop simulation
        self.simulator.stop()
        
        # Verify running flag is cleared
        self.assertFalse(self.simulator.running)

if __name__ == '__main__':
    unittest.main()
