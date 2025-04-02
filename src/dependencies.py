"""
Dependency injection for FastAPI.
This module provides functions for injecting dependencies into FastAPI routes.
"""
from typing import Optional

from fastapi import Depends

from src.db.adapters.sqlite_model_metrics import SQLiteModelMetricsRepository
from src.db.real_database import SQLiteDatabase
from src.monitoring.model_metrics_repository import ModelMetricsRepository
from src.monitoring.model_monitoring_service import ModelMonitoringService

# Cache the monitoring service instance
_monitoring_service_instance = None


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
