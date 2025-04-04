"""
Dependency injection functions for FastAPI.
Provides service dependencies used across API endpoints.
"""

from typing import Callable, Type

from fastapi import Depends

from src.config.settings import get_settings
from src.services.rheem_water_heater_maintenance import (
    RheemWaterHeaterMaintenanceService,
)
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


def get_rheem_water_heater_service() -> RheemWaterHeaterMaintenanceService:
    """
    Returns an instance of the RheemWaterHeaterMaintenanceService.
    Used as a FastAPI dependency for Rheem water heater endpoints.

    This service includes integrated ML prediction capabilities for
    maintenance, efficiency analysis, and telemetry pattern detection.

    Returns:
        An instance of RheemWaterHeaterMaintenanceService
    """
    # In a production environment, this might interact with configuration,
    # database connections, or other resources
    return RheemWaterHeaterMaintenanceService()


# Add other service dependencies as needed
