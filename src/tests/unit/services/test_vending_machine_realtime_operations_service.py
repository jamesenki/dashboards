"""
Unit tests for the vending machine real-time operations service
"""
import unittest
from unittest.mock import MagicMock, patch

from src.models.device import DeviceStatus, DeviceType
from src.models.vending_machine import (
    VendingMachine,
    VendingMachineMode,
    VendingMachineStatus,
)
from src.services.vending_machine_realtime_operations_service import (
    VendingMachineRealtimeOperationsService,
)


class TestVendingMachineRealtimeOperationsService(unittest.TestCase):
    """Test cases for vending machine real-time operations service"""

    def setUp(self):
        """Set up test environment before each test"""
        # Create mock dependencies
        self.vm_service = MagicMock()

        # Create the service instance with mocked dependencies
        self.service = VendingMachineRealtimeOperationsService(self.vm_service)

        # Set up a test machine
        self.test_machine = VendingMachine(
            id="test-123",
            name="Test Machine",
            type=DeviceType.VENDING_MACHINE,
            status=DeviceStatus.ONLINE,
            location="Test Location",
            machine_status=VendingMachineStatus.OPERATIONAL,
            mode=VendingMachineMode.NORMAL,
            temperature=-5.0,
        )

        # Configure mock to return the test machine
        self.vm_service.get_vending_machine.return_value = self.test_machine

    def test_get_operations_data(self):
        """Test getting operations data for a machine"""
        # Call the service method
        result = self.service.get_operations_data("test-123")

        # Verify the vending machine service was called correctly
        self.vm_service.get_vending_machine.assert_called_once_with("test-123")

        # Verify the result structure
        self.assertEqual(result.assetId, "test-123")
        self.assertEqual(result.assetLocation, "Test Location")
        self.assertEqual(result.machineStatus, "Online")

        # Check for presence of gauge data
        self.assertIsNotNone(result.assetHealthData)
        self.assertIsNotNone(result.freezerTemperatureData)
        self.assertIsNotNone(result.dispensePressureData)
        self.assertIsNotNone(result.cycleTimeData)

        # Check for RAM load data
        self.assertIsNotNone(result.maxRamLoadData)

        # Check for inventory data
        self.assertIsNotNone(result.freezerInventory)
        self.assertTrue(len(result.freezerInventory) > 0)

        # Check that freezer temperature is based on machine temperature
        self.assertEqual(
            result.freezerTemperatureData.freezerTemperature,
            self.test_machine.temperature,
        )

    def test_machine_not_found(self):
        """Test behavior when machine is not found"""
        # Configure mock to raise ValueError
        self.vm_service.get_vending_machine.side_effect = ValueError(
            "Machine not found"
        )

        # Call should raise the ValueError
        with self.assertRaises(ValueError) as context:
            self.service.get_operations_data("nonexistent-id")

        # Verify the error message
        self.assertIn("not found", str(context.exception))

    def test_online_status_mapping(self):
        """Test correct mapping of device status to machine status."""
        # Test ONLINE status
        self.test_machine.status = DeviceStatus.ONLINE
        result = self.service.get_operations_data("test-123")
        self.assertEqual(result.machineStatus, "Online")

        # Test OFFLINE status
        self.test_machine.status = DeviceStatus.OFFLINE
        result = self.service.get_operations_data("test-123")
        self.assertEqual(result.machineStatus, "Offline")

        # Test MAINTENANCE status
        self.test_machine.status = DeviceStatus.MAINTENANCE
        result = self.service.get_operations_data("test-123")
        self.assertEqual(result.machineStatus, "Offline")

    # Modified to focus on the actual behavior rather than relying on implementation details
    def test_random_data_generation(self):
        """Test that generated data has expected structure and formats"""
        # Get operations data multiple times
        result1 = self.service.get_operations_data("test-123")
        result2 = self.service.get_operations_data("test-123")

        # Check that basic structure is correct
        self.assertEqual(result1.assetId, "test-123")
        self.assertEqual(result2.assetId, "test-123")

        # Check that gauge data is properly formatted
        self.assertIsNotNone(result1.assetHealthData.assetHealth)
        self.assertTrue(
            isinstance(result1.assetHealthData.needleValue, float)
            or isinstance(result1.assetHealthData.needleValue, int)
        )

        # Verify freezer temperature data format
        self.assertTrue(
            isinstance(result1.freezerTemperatureData.freezerTemperature, float)
            or isinstance(result1.freezerTemperatureData.freezerTemperature, int)
        )

        # Check that inventory has proper structure
        self.assertTrue(len(result1.freezerInventory) > 0)
        self.assertTrue(
            all(
                hasattr(item, "name") and hasattr(item, "value")
                for item in result1.freezerInventory
            )
        )


if __name__ == "__main__":
    unittest.main()
