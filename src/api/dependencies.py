"""
Dependency injection functions for FastAPI.
Provides service dependencies used across API endpoints.
"""

from typing import Callable, Type

from fastapi import Depends

from src.config.settings import get_settings
from src.services.water_heater import WaterHeaterService
from src.services.water_heater_maintenance import WaterHeaterMaintenanceService


def get_water_heater_service() -> WaterHeaterService:
    """
    Returns an instance of the WaterHeaterService.
    Used as a FastAPI dependency for water heater endpoints.

    Returns:
        An instance of WaterHeaterService with extended maintenance capabilities
    """
    # In a production environment, this might interact with configuration,
    # database connections, or other resources
    return WaterHeaterMaintenanceService()


# Add other service dependencies as needed
