"""
Dependencies for the water heater API.

This module provides dependency injection for FastAPI endpoints.
"""
from fastapi import Depends

from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)


async def get_service() -> ConfigurableWaterHeaterService:
    """
    Provides an instance of ConfigurableWaterHeaterService.

    This is used as a FastAPI dependency to inject the service into endpoints.

    Returns:
        An instance of ConfigurableWaterHeaterService
    """
    return ConfigurableWaterHeaterService()
