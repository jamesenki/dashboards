"""
Mock data router for Water Heater API.

This module provides an API router for water heater operations
that use mock data instead of a real database.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from src.api.base.base_water_heater_router import BaseWaterHeaterRouter
from src.api.implementations.mock_water_heater_api import MockWaterHeaterApi
from src.repositories.water_heater_repository import MockWaterHeaterRepository
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)

# Create a global singleton instance of the mock repository
# This ensures simulation settings persist between requests
GLOBAL_MOCK_REPOSITORY = MockWaterHeaterRepository()

# Create a router for mock water heater operations
router = APIRouter(
    prefix="/api/mock/water-heaters",
    tags=["water-heaters", "mock"],
    responses={404: {"description": "Not found"}},
)


# Create dependency for mock service using the global repository
def get_mock_water_heater_service():
    """Get a water heater service using the global mock repository."""
    return ConfigurableWaterHeaterService(repository=GLOBAL_MOCK_REPOSITORY)


# Initialize the router with mock implementation
mock_router = BaseWaterHeaterRouter(
    router=router,
    service_dependency=get_mock_water_heater_service,
    api_implementation=MockWaterHeaterApi,
)


# Add simulation controls specific to mock router for testing scenarios
@router.post(
    "/simulate/failure",
    response_model=dict,
    summary="Simulate Failure Condition",
    description="Activates a simulated failure mode in the mock repository to test application behavior under error conditions. Available failure types include: 'network', 'timeout', 'validation', or 'none' to disable simulation.",
)
def simulate_failure(
    failure_type: str = Query(
        ...,
        description="Type of failure to simulate: 'network', 'timeout', 'validation', or 'none' to disable",
        example="network",
    ),
    service: ConfigurableWaterHeaterService = Depends(get_mock_water_heater_service),
):
    """Simulate a specific failure condition in the mock repository for testing error handling.

    This endpoint enables controlled testing of error conditions without affecting real data.
    Use 'none' to disable the simulation and return to normal operation.
    """
    valid_failures = ["network", "timeout", "validation", "none"]

    if failure_type not in valid_failures:
        return {
            "status": "error",
            "message": f"Invalid failure type. Must be one of: {', '.join(valid_failures)}",
            "timestamp": datetime.now().isoformat(),
        }

    if not isinstance(service.repository, MockWaterHeaterRepository):
        return {
            "status": "error",
            "message": "Can only simulate failures with mock repository",
            "timestamp": datetime.now().isoformat(),
        }

    # Set failure simulation flag in mock repository
    if isinstance(service.repository, MockWaterHeaterRepository):
        # Set the simulation type directly in the repository
        service.repository.simulate_failure = (
            failure_type if failure_type != "none" else None
        )

        # Log the change for debugging
        print(f"Setting simulation failure to: {service.repository.simulate_failure}")

    return {
        "status": "success",
        "message": f"Simulating {failure_type} failure"
        if failure_type != "none"
        else "Disabled failure simulation",
        "timestamp": datetime.now().isoformat(),
    }


@router.get(
    "/simulation/status",
    response_model=dict,
    summary="Get Simulation Status",
    description="Retrieves the current status of the mock API simulation, including what type of simulation is active and how many water heaters are currently being mocked.",
)
def get_simulation_status(
    service: ConfigurableWaterHeaterService = Depends(get_mock_water_heater_service),
):
    """Get current simulation status from the mock repository.

    Returns information about active simulations, water heater count in the mock repository,
    and other diagnostic information useful for debugging and testing.
    """
    if not isinstance(service.repository, MockWaterHeaterRepository):
        return {
            "status": "error",
            "message": "Not using mock repository",
            "timestamp": datetime.now().isoformat(),
        }

    # Ensure we're using a mock repository
    if not isinstance(service.repository, MockWaterHeaterRepository):
        return {
            "status": "error",
            "message": "Not using mock repository",
            "timestamp": datetime.now().isoformat(),
        }

    # Get the active simulation type directly from the repository
    failure_type = service.repository.simulate_failure

    # Get count from repository's cached water heaters
    count = (
        len(service.repository.water_heaters)
        if hasattr(service.repository, "water_heaters")
        else 0
    )

    return {
        "status": "active" if failure_type else "inactive",
        "simulation_type": failure_type if failure_type else "none",
        "water_heater_count": count,
        "is_mock_data": True,
        "timestamp": datetime.now().isoformat(),
    }
