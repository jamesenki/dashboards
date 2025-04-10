"""
Water Heater Service implementing business logic for water heater operations.

This use case layer class encapsulates the business rules for water heater operations
following Clean Architecture principles, where use cases depend on entities and gateways.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.domain.entities.water_heater import WaterHeater
from src.domain.value_objects.device_status import DeviceStatus
from src.domain.value_objects.temperature import Temperature
from src.domain.value_objects.water_heater_mode import WaterHeaterMode
from src.gateways.water_heater_repository import WaterHeaterRepository


class WaterHeaterService:
    """Service for water heater operations implementing business logic.

    This class implements the use cases related to water heater operations,
    applying domain rules and orchestrating entity interactions.

    It depends on the WaterHeaterRepository interface (not implementation)
    following the Dependency Inversion Principle.
    """

    def __init__(self, repository: WaterHeaterRepository):
        """Initialize the water heater service.

        Args:
            repository: Implementation of WaterHeaterRepository interface
        """
        self.repository = repository

    def get_all_water_heaters(self) -> List[WaterHeater]:
        """Get all water heaters.

        Returns:
            List of WaterHeater entities
        """
        return self.repository.get_all()

    def get_water_heater_by_id(self, heater_id: str) -> WaterHeater:
        """Get a water heater by its ID.

        Args:
            heater_id: The unique identifier of the water heater

        Returns:
            The WaterHeater entity

        Raises:
            ValueError: If the water heater doesn't exist
        """
        water_heater = self.repository.get_by_id(heater_id)
        if not water_heater:
            raise ValueError(f"Water heater with ID {heater_id} not found")
        return water_heater

    def create_water_heater(self, water_heater_data: Dict[str, Any]) -> WaterHeater:
        """Create a new water heater.

        Args:
            water_heater_data: Dictionary containing water heater attributes

        Returns:
            The created WaterHeater entity

        Raises:
            ValueError: If required attributes are missing or invalid
        """
        # Create temperature value objects
        current_temp = Temperature(
            value=water_heater_data["current_temperature"],
            unit=water_heater_data.get("current_temperature_unit", "C"),
        )

        target_temp = Temperature(
            value=water_heater_data["target_temperature"],
            unit=water_heater_data.get("target_temperature_unit", "C"),
        )

        min_temp = Temperature(
            value=water_heater_data.get("min_temperature", 40.0),
            unit=water_heater_data.get("min_temperature_unit", "C"),
        )

        max_temp = Temperature(
            value=water_heater_data.get("max_temperature", 85.0),
            unit=water_heater_data.get("max_temperature_unit", "C"),
        )

        # Create device status
        status = DeviceStatus(water_heater_data.get("status", "ONLINE"))

        # Create mode
        mode = WaterHeaterMode(water_heater_data.get("mode", "ECO"))

        # Create water heater entity
        water_heater = WaterHeater(
            id=water_heater_data.get("id", ""),
            name=water_heater_data["name"],
            manufacturer=water_heater_data["manufacturer"],
            model=water_heater_data["model"],
            current_temperature=current_temp,
            target_temperature=target_temp,
            min_temperature=min_temp,
            max_temperature=max_temp,
            status=status,
            mode=mode,
            location=water_heater_data.get("location"),
            is_simulated=water_heater_data.get("is_simulated", False),
        )

        # Save to repository
        created_heater = self.repository.create(water_heater)
        return created_heater

    def update_target_temperature(
        self, heater_id: str, temperature: Temperature
    ) -> WaterHeater:
        """Update a water heater's target temperature.

        Args:
            heater_id: The unique identifier of the water heater
            temperature: The new target temperature

        Returns:
            The updated WaterHeater entity

        Raises:
            ValueError: If the water heater doesn't exist or temperature is invalid
        """
        # Get the water heater
        water_heater = self.get_water_heater_by_id(heater_id)

        # Update the target temperature using entity method which enforces business rules
        water_heater.set_target_temperature(temperature)

        # Save the updated water heater
        self.repository.update(water_heater)

        return water_heater

    def update_operating_mode(
        self, heater_id: str, mode: WaterHeaterMode
    ) -> WaterHeater:
        """Update a water heater's operating mode.

        Args:
            heater_id: The unique identifier of the water heater
            mode: The new operating mode

        Returns:
            The updated WaterHeater entity

        Raises:
            ValueError: If the water heater doesn't exist
        """
        # Get the water heater
        water_heater = self.get_water_heater_by_id(heater_id)

        # Update the mode using entity method
        water_heater.set_mode(mode)

        # Save the updated water heater
        self.repository.update(water_heater)

        return water_heater

    def process_temperature_update(
        self, heater_id: str, current_temperature: Temperature
    ) -> WaterHeater:
        """Process a temperature update from a water heater sensor.

        This method updates the current temperature and adjusts the heater status
        based on the current and target temperatures.

        Args:
            heater_id: The unique identifier of the water heater
            current_temperature: The new current temperature

        Returns:
            The updated WaterHeater entity

        Raises:
            ValueError: If the water heater doesn't exist
        """
        # Get the water heater
        water_heater = self.get_water_heater_by_id(heater_id)

        # Update the current temperature using entity method
        water_heater.update_current_temperature(current_temperature)

        # Save the updated water heater
        self.repository.update(water_heater)

        return water_heater

    def delete_water_heater(self, heater_id: str) -> bool:
        """Delete a water heater.

        Args:
            heater_id: The unique identifier of the water heater

        Returns:
            True if deletion was successful, False otherwise
        """
        # Check if the water heater exists first
        if not self.repository.get_by_id(heater_id):
            raise ValueError(f"Water heater with ID {heater_id} not found")

        # Delete the water heater
        return self.repository.delete(heater_id)
