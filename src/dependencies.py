"""
Dependency injection for FastAPI.
This module provides functions for injecting dependencies into FastAPI routes.
"""
import logging
from typing import Optional

from fastapi import Depends

from src.db.adapters.sqlite_model_metrics import SQLiteModelMetricsRepository
from src.db.real_database import SQLiteDatabase
from src.monitoring.model_metrics_repository import ModelMetricsRepository
from src.monitoring.model_monitoring_service import ModelMonitoringService
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)

# Cache service instances for singleton pattern
_monitoring_service_instance = None
_water_heater_service_instance = None


def get_model_monitoring_service() -> ModelMonitoringService:
    """
    Provides a singleton instance of the ModelMonitoringService.

    Returns:
        A ModelMonitoringService instance for use in API routes
    """
    global _monitoring_service_instance

    if _monitoring_service_instance is None:
        # Create the database and repository
        db = SQLiteDatabase()
        sqlite_repo = SQLiteModelMetricsRepository(db=db)
        metrics_repo = ModelMetricsRepository(sql_repo=sqlite_repo)

        # Create the service
        _monitoring_service_instance = ModelMonitoringService(
            metrics_repository=metrics_repo
        )

    return _monitoring_service_instance


def get_configurable_water_heater_service() -> ConfigurableWaterHeaterService:
    """
    Provides a singleton instance of the ConfigurableWaterHeaterService.

    This follows our architecture's dependency injection pattern and ensures
    consistent water heater data access across API endpoints.

    Injects the message bus from the FastAPI app state if available.

    Returns:
        A ConfigurableWaterHeaterService instance for use in API routes
    """
    global _water_heater_service_instance

    if _water_heater_service_instance is None:
        # Get the FastAPI app instance
        import inspect

        from fastapi import FastAPI
        from fastapi.concurrency import run_in_threadpool
        from starlette.applications import Starlette

        # Get the current app from the calling context
        frame = inspect.currentframe()
        while frame:
            if "app" in frame.f_locals and isinstance(
                frame.f_locals["app"], (FastAPI, Starlette)
            ):
                app = frame.f_locals["app"]
                break
            frame = frame.f_back

        # Try to get message_bus from app state if available
        message_bus = None
        try:
            from fastapi import Request

            if "request" in inspect.currentframe().f_back.f_locals:
                request = inspect.currentframe().f_back.f_locals["request"]
                if isinstance(request, Request) and hasattr(
                    request.app.state, "message_bus"
                ):
                    message_bus = request.app.state.message_bus
        except Exception as e:
            logging.getLogger(__name__).warning(
                f"Failed to get message_bus from app state: {e}"
            )

        # Create the service with default repository selection and inject message bus if available
        _water_heater_service_instance = ConfigurableWaterHeaterService(
            message_bus=message_bus
        )
        logging.getLogger(__name__).info(
            f"Created ConfigurableWaterHeaterService with message_bus: {message_bus is not None}"
        )

    return _water_heater_service_instance


def get_db_water_heater_service() -> ConfigurableWaterHeaterService:
    """
    Provides a ConfigurableWaterHeaterService instance that explicitly uses a database repository.

    This ensures the service is using the database regardless of environment settings.
    Used by the database-specific API endpoints.

    Returns:
        A ConfigurableWaterHeaterService instance using a database repository
    """
    # Import directly to avoid circular imports
    from src.repositories.water_heater_repository import SQLiteWaterHeaterRepository

    # Create a new service instance with SQLite repository to ensure database access
    # Don't use the singleton pattern for this to ensure we always get a fresh DB connection
    return ConfigurableWaterHeaterService(repository=SQLiteWaterHeaterRepository())


def get_mock_water_heater_service() -> ConfigurableWaterHeaterService:
    """
    Provides a ConfigurableWaterHeaterService instance that explicitly uses a mock repository.

    This ensures the service is using mock data regardless of environment settings.
    Used by the mock-specific API endpoints.

    Returns:
        A ConfigurableWaterHeaterService instance using a mock repository
    """
    # Import directly to avoid circular imports
    from src.repositories.water_heater_repository import MockWaterHeaterRepository

    # Create a new service instance with Mock repository
    # Don't use the singleton pattern for this to ensure we always get a fresh mock instance
    return ConfigurableWaterHeaterService(repository=MockWaterHeaterRepository())
