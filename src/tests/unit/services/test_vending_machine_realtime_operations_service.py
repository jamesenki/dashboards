"""
Unit tests for the vending machine real-time operations service
"""
import unittest
from unittest.mock import MagicMock, patch
from src.services.vending_machine_realtime_operations_service import VendingMachineRealtimeOperationsService
from src.models.vending_machine import VendingMachine, VendingMachineStatus, VendingMachineMode
from src.models.device import DeviceType, DeviceStatus


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
        self.assertEqual(result.asset_id, "test-123")
        self.assertEqual(result.asset_location, "Test Location")
        self.assertEqual(result.machine_status, "Online")
        
        # Check for presence of gauge data
        self.assertIsNotNone(result.asset_health_data)
        self.assertIsNotNone(result.freezer_temperature_data)
        self.assertIsNotNone(result.dispense_pressure_data)
        self.assertIsNotNone(result.cycle_time_data)
        
        # Check for RAM load data
        self.assertIsNotNone(result.max_ram_load_data)
        
        # Check for inventory data
        self.assertIsNotNone(result.freezer_inventory)
        self.assertTrue(len(result.freezer_inventory) > 0)
        
        # Check that freezer temperature is based on machine temperature
        self.assertEqual(result.freezer_temperature_data.value, self.test_machine.temperature)

    def test_machine_not_found(self):
        """Test behavior when machine is not found"""
        # Configure mock to raise ValueError
        self.vm_service.get_vending_machine.side_effect = ValueError("Machine not found")
        
        # Call should raise the ValueError
        with self.assertRaises(ValueError) as context:
            self.service.get_operations_data("nonexistent-id")
        
        # Verify the error message
        self.assertIn("not found", str(context.exception))

    def test_online_status_mapping(self):
        """Test mapping of device status to machine status display"""
        # Test ONLINE status
        self.test_machine.status = DeviceStatus.ONLINE
        result = self.service.get_operations_data("test-123")
        self.assertEqual(result.machine_status, "Online")
        
        # Test OFFLINE status
        self.test_machine.status = DeviceStatus.OFFLINE
        result = self.service.get_operations_data("test-123")
        self.assertEqual(result.machine_status, "Offline")
        
        # Test MAINTENANCE status
        self.test_machine.status = DeviceStatus.MAINTENANCE
        result = self.service.get_operations_data("test-123")
        self.assertEqual(result.machine_status, "Maintenance")

    @patch('random.randint')
    @patch('random.uniform')
    @patch('random.choice')
    def test_random_data_generation(self, mock_choice, mock_uniform, mock_randint):
        """Test random data generation with controlled randomness"""
        # Control the randomness
        mock_randint.return_value = 7
        mock_uniform.return_value = 5.5
        mock_choice.return_value = "Yes"
        
        # Get operations data
        result = self.service.get_operations_data("test-123")
        
        # Check that random generation was used
        self.assertTrue(mock_randint.called)
        self.assertTrue(mock_uniform.called)
        self.assertTrue(mock_choice.called)
        
        # Verify some values based on our controlled randomness
        # (Note: exact assertions will depend on how the service uses these values)
        self.assertEqual(result.cup_detect, "Yes")  # From our mocked choice


if __name__ == '__main__':
    unittest.main()
