#!/usr/bin/env python3
"""
Unit tests for manufacturer-agnostic API service
"""
import os
import json
import unittest
from unittest.mock import patch, MagicMock, call
import sys

# Add the src directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

class TestManufacturerAgnosticAPI(unittest.TestCase):
    """Test suite for manufacturer-agnostic API service"""
    
    def setUp(self):
        """Setup test fixtures"""
        # Import here to allow patching
        from src.api.manufacturer_agnostic.api_service import DeviceAPI
        
        # Mock dependencies
        self.db_connection = MagicMock()
        self.redis_client = MagicMock()
        self.message_bus = MagicMock()
        
        # Create API service with mocked dependencies
        self.api = DeviceAPI(
            db_connection=self.db_connection,
            redis_client=self.redis_client,
            message_bus=self.message_bus
        )
        
        # Sample water heater data
        self.water_heaters = [
            {
                "device_id": "wh-rheem-001",
                "device_type": "water_heater",
                "manufacturer": "Rheem",
                "model": "ProTerra",
                "connection_status": "connected",
                "simulated": True
            },
            {
                "device_id": "wh-aosmith-001",
                "device_type": "water_heater",
                "manufacturer": "AO Smith",
                "model": "Signature",
                "connection_status": "disconnected",
                "simulated": True
            }
        ]
    
    def test_get_all_water_heaters(self):
        """Test retrieving all water heaters across manufacturers"""
        # Setup mock
        cursor_mock = MagicMock()
        cursor_mock.fetchall.return_value = self.water_heaters
        self.db_connection.cursor.return_value = cursor_mock
        
        # Call method
        result = self.api.get_water_heaters()
        
        # Verify results
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["manufacturer"], "Rheem")
        self.assertEqual(result[1]["manufacturer"], "AO Smith")
        
        # Verify SQL query was executed
        cursor_mock.execute.assert_called_once()
        # Query should filter for water heater devices
        self.assertIn("device_type = 'water_heater'", 
                      cursor_mock.execute.call_args[0][0])
    
    def test_get_water_heaters_by_manufacturer(self):
        """Test filtering water heaters by manufacturer"""
        # Setup mock
        cursor_mock = MagicMock()
        cursor_mock.fetchall.return_value = [self.water_heaters[0]]  # Only Rheem
        self.db_connection.cursor.return_value = cursor_mock
        
        # Call method with manufacturer filter
        result = self.api.get_water_heaters(manufacturer="Rheem")
        
        # Verify results
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["manufacturer"], "Rheem")
        
        # Verify SQL query was executed with correct filter
        cursor_mock.execute.assert_called_once()
        query_args = cursor_mock.execute.call_args[0]
        self.assertIn("manufacturer = %s", query_args[0])
        self.assertEqual(query_args[1][0], "Rheem")
    
    def test_get_water_heater_by_id(self):
        """Test retrieving a specific water heater by ID"""
        # Sample water heater details
        water_heater_detail = {
            "device_id": "wh-rheem-001",
            "device_type": "water_heater",
            "manufacturer": "Rheem",
            "model": "ProTerra",
            "serial_number": "RH123456",
            "firmware_version": "1.2.3",
            "registration_date": "2025-01-15T10:00:00Z",
            "last_connection": "2025-04-06T09:45:00Z",
            "connection_status": "connected",
            "simulated": True,
            "metadata": {
                "capacity_gallons": 50.0,
                "energy_source": "electric",
                "btu_rating": 4500,
                "efficiency_rating": 0.95,
                "temperature_min": 110.0,
                "temperature_max": 140.0
            }
        }
        
        # Setup mocks
        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = water_heater_detail
        self.db_connection.cursor.return_value = cursor_mock
        
        # Mock Redis to return current state
        self.redis_client.get.return_value = json.dumps({
            "temperature_current": 125.0,
            "temperature_setpoint": 130.0,
            "heating_status": True,
            "mode": "heating"
        })
        
        # Call method
        result = self.api.get_water_heater_by_id("wh-rheem-001")
        
        # Verify results
        self.assertEqual(result["device_id"], "wh-rheem-001")
        self.assertEqual(result["manufacturer"], "Rheem")
        
        # State from Redis should be included
        self.assertEqual(result["state"]["temperature_current"], 125.0)
        self.assertEqual(result["state"]["mode"], "heating")
        
        # Device details should be included
        self.assertEqual(result["metadata"]["capacity_gallons"], 50.0)
        
        # Verify database query
        cursor_mock.execute.assert_called_once()
        query_args = cursor_mock.execute.call_args[0]
        self.assertEqual(query_args[1][0], "wh-rheem-001")
        
        # Verify Redis lookup
        self.redis_client.get.assert_called_once()
    
    def test_get_operational_summary(self):
        """Test getting operational summary with maintenance predictions"""
        # Sample water heater IDs
        water_heater_ids = ["wh-rheem-001", "wh-aosmith-001"]
        
        # Setup cursor to return device IDs
        device_cursor_mock = MagicMock()
        device_cursor_mock.fetchall.return_value = [
            {"device_id": id} for id in water_heater_ids
        ]
        
        # Setup cursor for operational data
        op_cursor_mock = MagicMock()
        op_cursor_mock.fetchall.return_value = [
            {
                "device_id": "wh-rheem-001",
                "avg_temperature": 125.5,
                "heating_cycles_24h": 12,
                "total_heating_time_24h": 120,  # minutes
                "energy_used_24h": 12.5  # kWh
            },
            {
                "device_id": "wh-aosmith-001",
                "avg_temperature": 130.2,
                "heating_cycles_24h": 15,
                "total_heating_time_24h": 150,  # minutes
                "energy_used_24h": 15.2  # kWh
            }
        ]
        
        # Setup cursor for maintenance data
        maint_cursor_mock = MagicMock()
        maint_cursor_mock.fetchall.return_value = [
            {
                "device_id": "wh-rheem-001",
                "health_score": 0.92,
                "estimated_remaining_life": 1825,  # days
                "maintenance_due": False,
                "next_maintenance_date": "2025-10-15",
                "issues": json.dumps([
                    {"component": "heating_element", "status": "good"},
                    {"component": "thermostat", "status": "good"}
                ])
            },
            {
                "device_id": "wh-aosmith-001",
                "health_score": 0.78,
                "estimated_remaining_life": 1095,  # days
                "maintenance_due": True,
                "next_maintenance_date": "2025-04-30",
                "issues": json.dumps([
                    {"component": "heating_element", "status": "good"},
                    {"component": "thermostat", "status": "warning", 
                     "details": "Showing signs of inconsistent temperature control"}
                ])
            }
        ]
        
        self.db_connection.cursor.side_effect = [
            device_cursor_mock, op_cursor_mock, maint_cursor_mock
        ]
        
        # Call method
        result = self.api.get_operational_summary()
        
        # Verify results
        self.assertEqual(len(result), 2)
        
        # Verify first device data
        device1 = next(d for d in result if d["device_id"] == "wh-rheem-001")
        self.assertEqual(device1["operational"]["avg_temperature"], 125.5)
        self.assertEqual(device1["maintenance"]["health_score"], 0.92)
        self.assertFalse(device1["maintenance"]["maintenance_due"])
        
        # Verify second device data
        device2 = next(d for d in result if d["device_id"] == "wh-aosmith-001")
        self.assertEqual(device2["operational"]["energy_used_24h"], 15.2)
        self.assertEqual(device2["maintenance"]["health_score"], 0.78)
        self.assertTrue(device2["maintenance"]["maintenance_due"])
        
        # Verify database queries
        self.assertEqual(self.db_connection.cursor.call_count, 3)
    
    def test_send_command_to_device(self):
        """Test sending command to device"""
        # Setup message bus mock
        self.message_bus.publish.return_value = True
        
        # Command data
        device_id = "wh-rheem-001"
        command = {
            "command": "set_temperature",
            "params": {
                "setpoint": 130.0
            }
        }
        
        # Call method
        result = self.api.send_command(device_id, command)
        
        # Verify message bus was called
        self.message_bus.publish.assert_called_once()
        
        # Verify command was sent to correct topic
        call_args = self.message_bus.publish.call_args[0]
        self.assertEqual(call_args[0], "device.command")
        
        # Verify command data
        command_event = call_args[1]
        self.assertEqual(command_event["device_id"], device_id)
        self.assertEqual(command_event["command"], "set_temperature")
        self.assertEqual(command_event["params"]["setpoint"], 130.0)
        
        # Verify command ID was returned
        self.assertIsNotNone(result["command_id"])
        self.assertTrue(result["success"])

if __name__ == '__main__':
    unittest.main()
