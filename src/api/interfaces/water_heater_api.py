"""
Interface definition for Water Heater APIs.

This module defines the common interface that both the real database
and mock implementations of the Water Heater API must follow.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.models.water_heater import (
    WaterHeater,
    WaterHeaterMode,
    WaterHeaterReading,
    WaterHeaterStatus,
)


class WaterHeaterApiInterface(ABC):
    """
    Interface for Water Heater API implementations.

    This abstract base class defines the methods that must be implemented
    by both the database-backed and mock implementations of the Water Heater API.
    """

    @abstractmethod
    async def get_water_heaters(
        self, manufacturer: Optional[str] = None
    ) -> List[WaterHeater]:
        """
        Get all water heaters, with optional filtering by manufacturer.

        Args:
            manufacturer: Optional name of manufacturer to filter results
                         (e.g., 'Rheem', 'AquaTherm')

        Returns:
            List[WaterHeater]: List of filtered water heaters.
        """
        pass

    @abstractmethod
    async def get_water_heater(self, device_id: str) -> Optional[WaterHeater]:
        """
        Get a specific water heater by ID.

        Args:
            device_id (str): ID of the water heater to retrieve.

        Returns:
            Optional[WaterHeater]: The water heater if found, None otherwise.
        """
        pass

    @abstractmethod
    async def create_water_heater(self, water_heater: WaterHeater) -> WaterHeater:
        """
        Create a new water heater.

        Args:
            water_heater (WaterHeater): Water heater to create.

        Returns:
            WaterHeater: The created water heater with populated ID.
        """
        pass

    @abstractmethod
    async def update_target_temperature(
        self, device_id: str, temperature: float
    ) -> Optional[WaterHeater]:
        """
        Update a water heater's target temperature.

        Args:
            device_id (str): ID of the water heater to update.
            temperature (float): New target temperature.

        Returns:
            Optional[WaterHeater]: The updated water heater if found, None otherwise.
        """
        pass

    @abstractmethod
    async def update_mode(
        self, device_id: str, mode: WaterHeaterMode
    ) -> Optional[WaterHeater]:
        """
        Update a water heater's operating mode.

        Args:
            device_id (str): ID of the water heater to update.
            mode (WaterHeaterMode): New operating mode.

        Returns:
            Optional[WaterHeater]: The updated water heater if found, None otherwise.
        """
        pass

    @abstractmethod
    async def add_reading(
        self, device_id: str, reading: WaterHeaterReading
    ) -> Optional[WaterHeater]:
        """
        Add a new temperature reading to a water heater.

        Args:
            device_id (str): ID of the water heater.
            reading (WaterHeaterReading): The temperature reading to add.

        Returns:
            Optional[WaterHeater]: The updated water heater if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_data_source_info(self) -> dict:
        """
        Get information about the data source.

        Returns:
            dict: Information about the data source, including type and status.
        """
        pass
