"""
Mock implementation of the Water Heater API.

This module provides an implementation of the Water Heater API
that uses mock data instead of a real database.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from src.api.interfaces.water_heater_api import WaterHeaterApiInterface
from src.models.device import DeviceType
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterMode,
    WaterHeaterReading,
    WaterHeaterStatus,
)
from src.repositories.water_heater_repository import MockWaterHeaterRepository
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)


class MockWaterHeaterApi(WaterHeaterApiInterface):
    """
    Mock implementation of the Water Heater API.

    This class provides an implementation of the Water Heater API
    interface that uses mock data instead of a real database.
    """

    def __init__(self, service: ConfigurableWaterHeaterService):
        """
        Initialize the mock API implementation.

        Args:
            service (ConfigurableWaterHeaterService): The service to use for data access.
        """
        self.service = service
        # Verify we are using a mock repository
        if not isinstance(service.repository, MockWaterHeaterRepository):
            # Force the service to use a mock repository
            service.repository = MockWaterHeaterRepository()

    async def get_water_heaters(
        self, manufacturer: Optional[str] = None
    ) -> List[WaterHeater]:
        """
        Get all water heaters from the mock repository, with optional filtering by manufacturer.

        Args:
            manufacturer: Optional name of manufacturer to filter results
                         (e.g., 'Rheem', 'AquaTherm')

        Returns:
            List[WaterHeater]: List of filtered mock water heaters.
        """
        # Get heaters from service with optional manufacturer filter
        heaters = await self.service.get_water_heaters(manufacturer=manufacturer)

        # Ensure all heaters conform to the WaterHeater model
        validated_heaters = []
        for heater in heaters:
            # Convert to dict for validation, ensuring all required fields exist
            heater_dict = heater.dict() if hasattr(heater, "dict") else heater

            # Ensure required fields exist
            if "id" not in heater_dict or not heater_dict["id"]:
                heater_dict["id"] = f"mock-wh-{uuid.uuid4().hex[:8]}"

            if "name" not in heater_dict or not heater_dict["name"]:
                heater_dict["name"] = f"Mock Water Heater {heater_dict['id'][-5:]}"

            if "target_temperature" not in heater_dict:
                heater_dict["target_temperature"] = 50.0

            if "current_temperature" not in heater_dict:
                heater_dict["current_temperature"] = 45.0

            if "type" not in heater_dict:
                heater_dict["type"] = DeviceType.WATER_HEATER

            # Create a valid WaterHeater instance
            try:
                validated_heater = WaterHeater(**heater_dict)
                validated_heaters.append(validated_heater)
            except Exception as e:
                # Skip invalid heaters in mock data
                pass

        return validated_heaters

    async def get_water_heater(self, device_id: str) -> Optional[WaterHeater]:
        """
        Get a specific water heater by ID from the mock repository.

        Args:
            device_id (str): ID of the water heater to retrieve.

        Returns:
            Optional[WaterHeater]: The water heater if found, None otherwise.
        """
        return await self.service.get_water_heater(device_id)

    async def create_water_heater(self, water_heater: WaterHeater) -> WaterHeater:
        """
        Create a new water heater in the mock repository.

        Args:
            water_heater (WaterHeater): Water heater to create.

        Returns:
            WaterHeater: The created water heater with populated ID.
        """
        return await self.service.create_water_heater(water_heater)

    async def update_target_temperature(
        self, device_id: str, temperature: float
    ) -> Optional[WaterHeater]:
        """
        Update a water heater's target temperature in the mock repository.

        Args:
            device_id (str): ID of the water heater to update.
            temperature (float): New target temperature.

        Returns:
            Optional[WaterHeater]: The updated water heater if found, None otherwise.
        """
        return await self.service.update_target_temperature(device_id, temperature)

    async def update_mode(
        self, device_id: str, mode: WaterHeaterMode
    ) -> Optional[WaterHeater]:
        """
        Update a water heater's operating mode in the mock repository.

        Args:
            device_id (str): ID of the water heater to update.
            mode (WaterHeaterMode): New operating mode.

        Returns:
            Optional[WaterHeater]: The updated water heater if found, None otherwise.
        """
        return await self.service.update_mode(device_id, mode)

    async def add_reading(
        self, device_id: str, reading: WaterHeaterReading
    ) -> Optional[WaterHeater]:
        """
        Add a new temperature reading to a water heater in the mock repository.

        Args:
            device_id (str): ID of the water heater.
            reading (WaterHeaterReading): The temperature reading to add.

        Returns:
            Optional[WaterHeater]: The updated water heater if found, None otherwise.
        """
        return await self.service.add_reading(device_id, reading)

    def get_data_source_info(self) -> dict:
        """
        Get information about the mock data source.

        Returns:
            dict: Information about the data source, including type and status.
        """
        # Access water heaters directly from dummy_data
        from src.utils.dummy_data import dummy_data

        # Get water heaters count
        water_heaters = dummy_data.get_water_heaters()
        count = len(water_heaters) if water_heaters else 0

        return {
            "source_type": "mock",
            "repository_type": "MockWaterHeaterRepository",
            "is_connected": True,
            "water_heater_count": count,
            "api_version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "is_simulated_data": True,
        }
