"""
Database-backed implementation of the Water Heater API.

This module provides the implementation of the Water Heater API
that uses a real database repository.
"""
from datetime import datetime
from typing import List, Optional

from src.api.interfaces.water_heater_api import WaterHeaterApiInterface
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterMode,
    WaterHeaterReading,
    WaterHeaterStatus,
)
from src.repositories.water_heater_repository import SQLiteWaterHeaterRepository
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)


class DatabaseWaterHeaterApi(WaterHeaterApiInterface):
    """
    Database-backed implementation of the Water Heater API.

    This class provides an implementation of the Water Heater API
    interface that uses a real database repository.
    """

    def __init__(self, service: ConfigurableWaterHeaterService):
        """
        Initialize the database API implementation.

        Args:
            service (ConfigurableWaterHeaterService): The service to use for data access.
        """
        self.service = service
        # Verify we are using a database repository
        if not isinstance(service.repository, SQLiteWaterHeaterRepository):
            raise ValueError(
                "Service must use a SQLiteWaterHeaterRepository for DatabaseWaterHeaterApi"
            )

    async def get_water_heaters(
        self, manufacturer: Optional[str] = None
    ) -> List[WaterHeater]:
        """
        Get all water heaters from the database, with optional filtering by manufacturer.

        Args:
            manufacturer: Optional name of manufacturer to filter results
                         (e.g., 'Rheem', 'AquaTherm')

        Returns:
            List[WaterHeater]: List of filtered water heaters from the database.
        """
        return await self.service.get_water_heaters(manufacturer=manufacturer)

    async def get_water_heater(self, device_id: str) -> Optional[WaterHeater]:
        """
        Get a specific water heater by ID from the database.

        Args:
            device_id (str): ID of the water heater to retrieve.

        Returns:
            Optional[WaterHeater]: The water heater if found, None otherwise.
        """
        return await self.service.get_water_heater(device_id)

    async def create_water_heater(self, water_heater: WaterHeater) -> WaterHeater:
        """
        Create a new water heater in the database.

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
        Update a water heater's target temperature in the database.

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
        Update a water heater's operating mode in the database.

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
        Add a new temperature reading to a water heater in the database.

        Args:
            device_id (str): ID of the water heater.
            reading (WaterHeaterReading): The temperature reading to add.

        Returns:
            Optional[WaterHeater]: The updated water heater if found, None otherwise.
        """
        return await self.service.add_reading(device_id, reading)

    def get_data_source_info(self) -> dict:
        """
        Get information about the database data source.

        Returns:
            dict: Information about the data source, including type and status.
        """
        return {
            "source_type": "database",
            "repository_type": "SQLite",
            "is_connected": True,
            "water_heater_count": 0,  # This would be populated by an actual count query
            "api_version": "1.0",
            "timestamp": datetime.now().isoformat(),
        }
