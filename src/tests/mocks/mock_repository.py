"""Mock repository for testing."""
from typing import Dict, List, Optional, Type, Union

from src.models.device import Device, DeviceStatus, DeviceType
from src.models.device_reading import DeviceReading


class MockDeviceRepository:
    """Mock implementation of the device repository for testing."""

    async def get_devices(
        self,
        type_filter: Optional[DeviceType] = None,
        status_filter: Optional[DeviceStatus] = None,
    ) -> List[Device]:
        """Mock implementation of get_devices."""
        return []

    async def get_device(self, device_id: str) -> Optional[Device]:
        """Mock implementation of get_device."""
        return None

    async def create_device(self, device: Device) -> Device:
        """Mock implementation of create_device."""
        return device

    async def update_device(
        self, device_id: str, device_data: Dict
    ) -> Optional[Device]:
        """Mock implementation of update_device."""
        return None

    async def delete_device(self, device_id: str) -> bool:
        """Mock implementation of delete_device."""
        return True

    async def add_device_reading(
        self, device_id: str, reading: DeviceReading
    ) -> Optional[Device]:
        """Mock implementation of add_device_reading."""
        return None

    async def get_device_readings(
        self,
        device_id: str,
        metric_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> List[DeviceReading]:
        """Mock implementation of get_device_readings."""
        return []
