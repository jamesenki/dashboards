"""
Service provider for dependency injection.

This module provides factory functions for injecting service instances
into API controllers, following Clean Architecture principles by ensuring
that controllers depend on interfaces rather than concrete implementations.
"""
import os
from functools import lru_cache
from typing import Optional

from src.adapters.repositories.in_memory_device_shadow_repository import (
    InMemoryDeviceShadowRepository,
)
from src.adapters.repositories.in_memory_water_heater_repository import (
    InMemoryWaterHeaterRepository,
)
from src.gateways.device_shadow_repository import DeviceShadowRepository
from src.gateways.water_heater_repository import WaterHeaterRepository
from src.use_cases.device_shadow_service import DeviceShadowService
from src.use_cases.water_heater_service import WaterHeaterService


# Repository instances are cached to ensure we use the same instance throughout the application
@lru_cache(maxsize=1)
def get_water_heater_repository() -> WaterHeaterRepository:
    """Get or create a water heater repository instance.

    This function determines which repository implementation to use
    based on environment settings.

    Returns:
        WaterHeaterRepository implementation
    """
    # Check if we should use in-memory repository for testing/development
    use_in_memory = os.getenv("USE_IN_MEMORY_REPO", "True").lower() == "true"

    if use_in_memory:
        # For testing and development, use in-memory repository
        return InMemoryWaterHeaterRepository()
    else:
        # For production, use a persistent repository (implementation to be added)
        # This demonstrates the flexibility of our Clean Architecture approach
        # where we can swap implementations without changing the use cases
        from src.adapters.repositories.mongodb_water_heater_repository import (
            MongoDBWaterHeaterRepository,
        )

        return MongoDBWaterHeaterRepository()


@lru_cache(maxsize=1)
def get_device_shadow_repository() -> DeviceShadowRepository:
    """Get or create a device shadow repository instance.

    This function determines which repository implementation to use
    based on environment settings.

    Returns:
        DeviceShadowRepository implementation
    """
    # Check if we should use in-memory repository for testing/development
    use_in_memory = os.getenv("USE_IN_MEMORY_REPO", "True").lower() == "true"

    if use_in_memory:
        # For testing and development, use in-memory repository
        return InMemoryDeviceShadowRepository()
    else:
        # For production, use a persistent repository (implementation to be added)
        from src.adapters.repositories.mongodb_device_shadow_repository import (
            MongoDBDeviceShadowRepository,
        )

        return MongoDBDeviceShadowRepository()


# Service instances are created on-demand using the appropriate repository
def get_water_heater_service() -> WaterHeaterService:
    """Get a water heater service instance.

    Returns:
        WaterHeaterService instance with injected repository
    """
    repository = get_water_heater_repository()
    return WaterHeaterService(repository=repository)


def get_device_shadow_service() -> DeviceShadowService:
    """Get a device shadow service instance.

    Returns:
        DeviceShadowService instance with injected repository
    """
    repository = get_device_shadow_repository()
    return DeviceShadowService(repository=repository)
