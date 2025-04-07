"""
Database-backed router for Water Heater API.

This module provides an API router for water heater operations
that use a real database as the data source.

The database implementation uses SQLite (or PostgreSQL if configured)
to store water heater data and provides ACID-compliant operations
for production use cases, following Test-Driven Development (TDD) principles.
"""
from datetime import datetime

from fastapi import APIRouter, Depends

from src.api.base.base_water_heater_router import BaseWaterHeaterRouter
from src.api.implementations.db_water_heater_api import DatabaseWaterHeaterApi
from src.dependencies import get_db_water_heater_service
from src.repositories.water_heater_repository import SQLiteWaterHeaterRepository
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)

# Create a router for database-backed water heater operations
router = APIRouter(
    prefix="/api/db/water-heaters",
    tags=["water-heaters", "db"],  # Changed from 'database' to 'db' to match our test
    responses={
        404: {"description": "Water heater not found"},
        500: {"description": "Database error or connectivity issue"},
        422: {"description": "Validation error in request data"},
    },
)

# Initialize the router with database implementation
db_router = BaseWaterHeaterRouter(
    router=router,
    service_dependency=get_db_water_heater_service,
    api_implementation=DatabaseWaterHeaterApi,
)


# Add health check endpoint specific to database router
@router.get(
    "/health",
    response_model=dict,
    summary="Database Health Check",
    description="Checks the health and connectivity of the database backend. Returns status information and connection details to help diagnose any issues.",
)
def db_health_check(
    service: ConfigurableWaterHeaterService = Depends(get_db_water_heater_service),
):
    """Check database health status and connection information.

    This endpoint verifies that the application can successfully connect to the database
    and perform basic operations. It returns detailed connection information and status.

    Returns:
        dict: A dictionary containing health check information including:
            - status: 'healthy' or 'unhealthy'
            - database_type: The type of database being used
            - timestamp: When the health check was performed
            - details: Additional connection information
    """
    try:
        # Attempt to connect to the database
        is_connected = isinstance(service.repository, SQLiteWaterHeaterRepository)
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "database_type": "SQLite",
            "timestamp": datetime.now().isoformat(),
            "details": {
                "connection": "active" if is_connected else "inactive",
                "repository_type": service.repository.__class__.__name__,
            },
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
