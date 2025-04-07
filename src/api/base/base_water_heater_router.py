"""
Base router implementation for Water Heater APIs.

This module provides a base router class that both the database-backed
and mock implementations of the Water Heater API can extend.
"""
import uuid
from typing import List, Optional, Type

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field

from src.api.interfaces.water_heater_api import WaterHeaterApiInterface
from src.api.schemas.water_heater import (
    ModeUpdate,
    TemperatureReading,
    TemperatureUpdate,
    WaterHeaterCreate,
)
from src.models.device import DeviceStatus, DeviceType
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterMode,
    WaterHeaterReading,
    WaterHeaterStatus,
)


class BaseWaterHeaterRouter:
    """
    Base router implementation for Water Heater API endpoints.

    This class provides the common implementation logic for both
    database-backed and mock API endpoints.
    """

    def __init__(
        self,
        router: APIRouter,
        service_dependency,
        api_implementation: Type[WaterHeaterApiInterface],
    ):
        """
        Initialize the base router.

        Args:
            router (APIRouter): FastAPI router to add routes to
            service_dependency: Dependency to get the service implementation
            api_implementation (Type[WaterHeaterApiInterface]): Implementation class
        """
        self.router = router
        self.service_dependency = service_dependency
        self.api_implementation = api_implementation

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register all routes on the router."""

        @self.router.get(
            "/",
            response_model=List[WaterHeater],
            summary="Get All Water Heaters",
            description="Retrieves a list of all water heaters from the configured data source. This endpoint returns detailed information about each water heater including its current status, temperature readings, and configuration. Optionally filter by manufacturer.",
        )
        async def get_water_heaters(
            manufacturer: Optional[str] = None,
            service=Depends(self.service_dependency),
        ):
            """Get all water heaters from the configured data source.

            Args:
                manufacturer: Optional filter by manufacturer (e.g., 'Rheem', 'AquaTherm')
            """
            api = self.api_implementation(service)
            return await api.get_water_heaters(manufacturer=manufacturer)

        @self.router.get(
            "/data-source",
            response_model=dict,
            summary="Get Data Source Information",
            description="Returns detailed information about the current data source being used (e.g., mock repository or database). This helps with transparency and debugging.",
        )
        def get_data_source_info(
            service=Depends(self.service_dependency),
        ):
            """Get information about the current data source including type and connection status."""
            api = self.api_implementation(service)
            return api.get_data_source_info()

        @self.router.get(
            "/{device_id}",
            response_model=WaterHeater,
            summary="Get Water Heater by ID",
            description="Retrieves detailed information about a specific water heater identified by its unique ID. Returns a 404 error if the water heater is not found.",
        )
        async def get_water_heater(
            device_id: str = Path(
                ..., description="Unique identifier of the water heater to retrieve"
            ),
            service=Depends(self.service_dependency),
        ):
            """Get a specific water heater by ID from the configured data source."""
            api = self.api_implementation(service)
            water_heater = await api.get_water_heater(device_id)
            if not water_heater:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Water heater with ID {device_id} not found",
                )
            return water_heater

        @self.router.post(
            "/",
            response_model=WaterHeater,
            status_code=status.HTTP_201_CREATED,
            summary="Create New Water Heater",
            description="Creates a new water heater with the provided configuration. Returns the created water heater with its assigned ID and default values for optional fields.",
        )
        async def create_water_heater(
            water_heater_data: WaterHeaterCreate,
            service=Depends(self.service_dependency),
        ):
            """Create a new water heater in the configured data source."""

            api = self.api_implementation(service)

            # Convert the request model to a domain model with all required fields
            water_heater = WaterHeater(
                id=f"wh-{uuid.uuid4().hex[:8]}",  # Generate a unique ID
                name=water_heater_data.name,
                target_temperature=water_heater_data.target_temperature,
                current_temperature=water_heater_data.target_temperature
                - 5.0,  # Initialize with a reasonable value
                mode=water_heater_data.mode,
                min_temperature=water_heater_data.min_temperature,
                max_temperature=water_heater_data.max_temperature,
                heater_status=WaterHeaterStatus.STANDBY,  # Default status
                status=DeviceStatus.ONLINE,  # Default device status
                type=DeviceType.WATER_HEATER,  # Set device type
            )

            try:
                created_heater = await api.create_water_heater(water_heater)
                return created_heater
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create water heater: {str(e)}",
                )

        @self.router.put("/{device_id}/temperature", response_model=WaterHeater)
        async def update_target_temperature(
            temperature_data: TemperatureUpdate,
            device_id: str = Path(..., description="ID of the water heater"),
            service=Depends(self.service_dependency),
        ):
            """Update a water heater's target temperature."""
            api = self.api_implementation(service)
            updated_heater = await api.update_target_temperature(
                device_id, temperature_data.temperature
            )

            if not updated_heater:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Water heater with ID {device_id} not found",
                )

            return updated_heater

        @self.router.put("/{device_id}/mode", response_model=WaterHeater)
        async def update_mode(
            mode_data: ModeUpdate,
            device_id: str = Path(..., description="ID of the water heater"),
            service=Depends(self.service_dependency),
        ):
            """Update a water heater's operating mode."""
            api = self.api_implementation(service)
            updated_heater = await api.update_mode(device_id, mode_data.mode)

            if not updated_heater:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Water heater with ID {device_id} not found",
                )

            return updated_heater

        @self.router.post("/{device_id}/readings", response_model=WaterHeater)
        async def add_reading(
            reading_data: TemperatureReading,
            device_id: str = Path(..., description="ID of the water heater"),
            service=Depends(self.service_dependency),
        ):
            """Add a new temperature reading to a water heater."""
            api = self.api_implementation(service)

            # Convert the request model to a domain model
            reading = WaterHeaterReading(
                temperature=reading_data.temperature,
                pressure=reading_data.pressure,
                energy_usage=reading_data.energy_usage,
                flow_rate=reading_data.flow_rate,
            )

            updated_heater = await api.add_reading(device_id, reading)

            if not updated_heater:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Water heater with ID {device_id} not found",
                )

            return updated_heater
