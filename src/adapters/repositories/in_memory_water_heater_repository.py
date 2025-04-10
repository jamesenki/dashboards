"""
In-memory implementation of the Water Heater Repository interface.

This adapter provides an in-memory implementation of the WaterHeaterRepository interface
for testing and development purposes, following Clean Architecture principles.
"""
import copy
import uuid
from typing import Dict, List, Optional

from src.domain.entities.water_heater import WaterHeater
from src.gateways.water_heater_repository import WaterHeaterRepository


class InMemoryWaterHeaterRepository(WaterHeaterRepository):
    """In-memory implementation of WaterHeaterRepository interface.

    This implementation stores water heaters in memory, making it suitable
    for testing and development, but not for production use since data
    is lost when the application restarts.
    """

    def __init__(self, initial_data: List[WaterHeater] = None):
        """Initialize with optional initial data.

        Args:
            initial_data: Optional list of WaterHeater entities to pre-populate the repository
        """
        # Store water heaters in a dictionary keyed by ID for efficient lookups
        self._water_heaters: Dict[str, WaterHeater] = {}

        # Add initial data if provided
        if initial_data:
            for water_heater in initial_data:
                self._water_heaters[water_heater.id] = copy.deepcopy(water_heater)

    def get_all(self) -> List[WaterHeater]:
        """Get all water heaters.

        Returns:
            List of WaterHeater entities
        """
        # Return a copy of all water heaters to prevent external modification
        return list(copy.deepcopy(heater) for heater in self._water_heaters.values())

    def get_by_id(self, water_heater_id: str) -> Optional[WaterHeater]:
        """Get a water heater by its ID.

        Args:
            water_heater_id: The unique identifier of the water heater

        Returns:
            The WaterHeater entity if found, otherwise None
        """
        # Return a deep copy to prevent external modification of internal state
        heater = self._water_heaters.get(water_heater_id)
        return copy.deepcopy(heater) if heater else None

    def create(self, water_heater: WaterHeater) -> WaterHeater:
        """Create a new water heater.

        Args:
            water_heater: The WaterHeater entity to create

        Returns:
            The created WaterHeater entity with assigned ID

        Raises:
            ValueError: If a water heater with the same ID already exists
        """
        # Generate ID if not provided
        if not water_heater.id:
            water_heater_copy = copy.deepcopy(water_heater)
            water_heater_copy.id = f"wh-{uuid.uuid4()}"
        else:
            water_heater_copy = copy.deepcopy(water_heater)

            # Ensure ID doesn't already exist
            if water_heater_copy.id in self._water_heaters:
                raise ValueError(
                    f"Water heater with ID {water_heater_copy.id} already exists"
                )

        # Store the water heater
        self._water_heaters[water_heater_copy.id] = water_heater_copy

        # Return a copy of the created water heater
        return copy.deepcopy(water_heater_copy)

    def update(self, water_heater: WaterHeater) -> bool:
        """Update an existing water heater.

        Args:
            water_heater: The WaterHeater entity to update

        Returns:
            True if update was successful, False otherwise

        Raises:
            ValueError: If the water heater doesn't exist
        """
        # Check if water heater exists
        if water_heater.id not in self._water_heaters:
            raise ValueError(f"Water heater with ID {water_heater.id} not found")

        # Update the water heater
        self._water_heaters[water_heater.id] = copy.deepcopy(water_heater)

        return True

    def delete(self, water_heater_id: str) -> bool:
        """Delete a water heater.

        Args:
            water_heater_id: The unique identifier of the water heater to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        # Check if water heater exists
        if water_heater_id not in self._water_heaters:
            return False

        # Delete the water heater
        del self._water_heaters[water_heater_id]

        return True
