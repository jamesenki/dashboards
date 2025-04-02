from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.models.vending_machine import VendingMachine, VendingMachineReading
from src.services.vending_machine_operations_service import (
    VendingMachineOperationsService,
)


class TestVendingMachineOperationsService:
    """Test cases for vending machine operations service."""

    def setup_method(self):
        """Setup for each test method."""
        # Create mocks for the service dependencies
        self.mock_vm_service = MagicMock()
        self.mock_db = MagicMock()
        # Initialize the service with mocked dependencies
        self.service = VendingMachineOperationsService(
            self.mock_vm_service, self.mock_db
        )

    def test_get_operations_summary(self):
        """Test retrieving operations summary data."""
        # Arrange
        vm_id = "test-vm-123"
        mock_readings = [
            VendingMachineReading(
                timestamp=datetime.now() - timedelta(hours=3),
                temperature=4.5,
                door_open=False,
                stock_level=75,
            ),
            VendingMachineReading(
                timestamp=datetime.now() - timedelta(hours=1),
                temperature=5.0,
                door_open=True,
                stock_level=70,
            ),
        ]

        with patch(
            "src.services.vending_machine.VendingMachineService.get_readings"
        ) as mock_get_readings:
            mock_get_readings.return_value = mock_readings

            # Act
            result = self.service.get_operations_summary(vm_id)

            # Assert
            assert result is not None
            assert "temperature" in result
            assert "door_events" in result
            assert "stock_levels" in result
            mock_get_readings.assert_called_once_with(vm_id)

    def test_transform_temperature_data(self):
        """Test transformation of temperature readings."""
        # Arrange
        readings = [
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 10, 0),
                temperature=3.5,
                door_open=False,
                stock_level=100,
            ),
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 11, 0),
                temperature=4.0,
                door_open=False,
                stock_level=95,
            ),
        ]

        # Act
        result = self.service._transform_temperature_data(readings)

        # Assert
        assert len(result) == 2
        assert result[0]["timestamp"] == "2023-01-01T10:00:00"
        assert result[0]["value"] == 3.5
        assert result[1]["timestamp"] == "2023-01-01T11:00:00"
        assert result[1]["value"] == 4.0

    def test_transform_door_events(self):
        """Test transformation of door open/close events."""
        # Arrange
        readings = [
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 10, 0),
                temperature=3.5,
                door_open=False,
                stock_level=100,
            ),
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 11, 0),
                temperature=4.0,
                door_open=True,
                stock_level=95,
            ),
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 12, 0),
                temperature=4.0,
                door_open=False,
                stock_level=90,
            ),
        ]

        # Act
        result = self.service._transform_door_events(readings)

        # Assert
        assert len(result) == 2
        assert result[0]["timestamp"] == "2023-01-01T11:00:00"
        assert result[0]["event"] == "open"
        assert result[1]["timestamp"] == "2023-01-01T12:00:00"
        assert result[1]["event"] == "close"

    def test_transform_stock_levels(self):
        """Test transformation of stock level readings."""
        # Arrange
        readings = [
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 10, 0),
                temperature=3.5,
                door_open=False,
                stock_level=100,
            ),
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 11, 0),
                temperature=4.0,
                door_open=False,
                stock_level=95,
            ),
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 12, 0),
                temperature=4.0,
                door_open=False,
                stock_level=90,
            ),
        ]

        # Act
        result = self.service._transform_stock_levels(readings)

        # Assert
        assert len(result) == 2
        assert result[0]["timestamp"] == "2023-01-01T10:00:00"
        assert result[0]["value"] == 100
        assert result[1]["timestamp"] == "2023-01-01T11:00:00"
        assert result[1]["value"] == 95

    def test_transform_sales_data(self):
        """Test transformation of sales data."""
        # Arrange
        readings = [
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 10, 0),
                temperature=3.5,
                door_open=False,
                stock_level=100,
            ),
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 11, 0),
                temperature=4.0,
                door_open=False,
                stock_level=95,
            ),
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 12, 0),
                temperature=4.0,
                door_open=False,
                stock_level=90,
            ),
        ]

        # Act
        result = self.service._transform_sales_data(readings)

        # Assert
        assert len(result) == 2
        assert result[0]["timestamp"] == "2023-01-01T10:00:00"
        assert result[0]["value"] == 100
        assert result[1]["timestamp"] == "2023-01-01T11:00:00"
        assert result[1]["value"] == 95

    def test_transform_sales_data(self):
        """Test transformation of sales data."""
        # Arrange
        readings = [
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 10, 0),
                temperature=3.5,
                door_open=False,
                stock_level=100,
            ),
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 11, 0),
                temperature=4.0,
                door_open=False,
                stock_level=95,
            ),
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 12, 0),
                temperature=4.0,
                door_open=False,
                stock_level=90,
            ),
        ]

        # Act
        result = self.service._transform_sales_data(readings)

        # Assert
        assert len(result) == 2
        assert result[0]["timestamp"] == "2023-01-01T10:00:00"
        assert result[0]["value"] == 100
        assert result[1]["timestamp"] == "2023-01-01T11:00:00"
        assert result[1]["value"] == 95

    def test_transform_power_consumption_data(self):
        """Test transformation of power consumption data."""
        # Arrange
        readings = [
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 10, 0),
                temperature=3.5,
                door_open=False,
                stock_level=100,
            ),
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 11, 0),
                temperature=4.0,
                door_open=False,
                stock_level=95,
            ),
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 12, 0),
                temperature=4.0,
                door_open=False,
                stock_level=90,
            ),
        ]

        # Act
        result = self.service._transform_power_consumption_data(readings)

        # Assert
        assert len(result) == 2
        assert result[0]["timestamp"] == "2023-01-01T10:00:00"
        assert result[0]["value"] == 100
        assert result[1]["timestamp"] == "2023-01-01T11:00:00"
        assert result[1]["value"] == 95

    def test_transform_device_status_data(self):
        """Test transformation of device status data."""
        # Arrange
        readings = [
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 10, 0),
                temperature=3.5,
                door_open=False,
                stock_level=100,
            ),
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 11, 0),
                temperature=4.0,
                door_open=False,
                stock_level=95,
            ),
            VendingMachineReading(
                timestamp=datetime(2023, 1, 1, 12, 0),
                temperature=4.0,
                door_open=False,
                stock_level=90,
            ),
        ]

        # Act
        result = self.service._transform_device_status_data(readings)

        # Assert
        assert len(result) == 2
        assert result[0]["timestamp"] == "2023-01-01T10:00:00"
        assert result[0]["value"] == 100
        assert result[1]["timestamp"] == "2023-01-01T11:00:00"
        assert result[1]["value"] == 95
