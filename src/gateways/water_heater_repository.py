"""
Water Heater Repository interface defining the gateway to data storage.

Following Clean Architecture, this defines the interface that use cases
interact with, without dependencies on specific external implementations.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.water_heater import WaterHeater


class WaterHeaterRepository(ABC):
    """Abstract interface for water heater data persistence.

    This interface defines the methods that any water heater repository
    implementation must provide, following the Repository pattern to
    abstract data access from business logic.
    """

    @abstractmethod
    def get_all(self) -> List[WaterHeater]:
        """Get all water heaters.

        Returns:
            List of WaterHeater entities
        """
        pass

    @abstractmethod
    def get_by_id(self, water_heater_id: str) -> Optional[WaterHeater]:
        """Get a water heater by its ID.

        Args:
            water_heater_id: The unique identifier of the water heater

        Returns:
            The WaterHeater entity if found, otherwise None
        """
        pass

    @abstractmethod
    def create(self, water_heater: WaterHeater) -> WaterHeater:
        """Create a new water heater.

        Args:
            water_heater: The WaterHeater entity to create

        Returns:
            The created WaterHeater entity with assigned ID

        Raises:
            ValueError: If a water heater with the same ID already exists
        """
        pass

    @abstractmethod
    def update(self, water_heater: WaterHeater) -> bool:
        """Update an existing water heater.

        Args:
            water_heater: The WaterHeater entity to update

        Returns:
            True if update was successful, False otherwise

        Raises:
            ValueError: If the water heater doesn't exist
        """
        pass

    @abstractmethod
    def delete(self, water_heater_id: str) -> bool:
        """Delete a water heater.

        Args:
            water_heater_id: The unique identifier of the water heater to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        pass
