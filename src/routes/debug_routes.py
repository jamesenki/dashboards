"""
Debug routes for development purposes.
These routes help diagnose issues with data sources and other development concerns.
"""
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.db.adapters.sqlite_model_metrics import SQLiteModelMetricsRepository
from src.db.real_database import SQLiteDatabase
from src.dependencies import get_configurable_water_heater_service
from src.monitoring.model_metrics_repository import ModelMetricsRepository
from src.monitoring.model_monitoring_service import ModelMonitoringService
from src.repositories.water_heater_repository import (
    MockWaterHeaterRepository,
    SQLiteWaterHeaterRepository,
)
from src.services.configurable_water_heater_service import (
    ConfigurableWaterHeaterService,
)

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/debug",
    tags=["debug"],
    responses={404: {"description": "Not found"}},
)


@router.get("/data-sources")
async def check_data_sources():
    # Create necessary components directly
    db = SQLiteDatabase()
    sqlite_repo = SQLiteModelMetricsRepository(db=db)
    metrics_repo = ModelMetricsRepository(sql_repo=sqlite_repo)
    service = ModelMonitoringService(metrics_repository=metrics_repo)
    """
    Returns information about what data sources are being used for models.
    This helps diagnose whether data is coming from the database or mock implementations.
    """
    # Get all models
    models = await service.get_models()

    # Count sources
    db_count = sum(1 for m in models if m.get("data_source") == "database")
    mock_count = sum(1 for m in models if m.get("data_source") == "mock")
    unknown_count = sum(1 for m in models if "data_source" not in m)

    # Prepare model summary
    model_summary = []
    for model in models:
        model_summary.append(
            {
                "id": model["id"],
                "name": model["name"],
                "data_source": model.get("data_source", "unknown"),
            }
        )

    return {
        "summary": {
            "total_models": len(models),
            "from_database": db_count,
            "from_mock": mock_count,
            "unknown_source": unknown_count,
        },
        "models": model_summary,
    }


class WaterHeaterDataSourceInfo(BaseModel):
    """Model for water heater data source information"""

    data_source: str
    total_water_heaters: int
    using_mock_data: bool
    repository_type: str
    aquatherm_count: int
    non_aquatherm_count: int
    database_connection_status: str


@router.get("/water-heater-data-source", response_model=WaterHeaterDataSourceInfo)
async def check_water_heater_data_source(
    service: ConfigurableWaterHeaterService = Depends(
        get_configurable_water_heater_service
    ),
):
    """
    Check what data source is being used for water heaters and verify connectivity.

    This helps diagnose whether water heater data is coming from the database or mock implementations,
    following TDD principles by making the implementation explicit and testable.
    """
    try:
        # Get all water heaters
        water_heaters = await service.get_water_heaters()

        # Determine repository type
        repo_type = type(service.repository).__name__
        using_mock = isinstance(service.repository, MockWaterHeaterRepository)

        # Count AquaTherm vs. non-AquaTherm water heaters
        aquatherm_count = 0
        non_aquatherm_count = 0

        for heater in water_heaters:
            # Check if it's an AquaTherm water heater by ID prefix (safer method)
            # The manufacturer might be in properties dict if available
            is_aquatherm = False

            # Check ID prefix first
            if heater.id and "aqua-wh-" in heater.id:
                is_aquatherm = True
            # Check properties dict if it exists
            elif hasattr(heater, "properties") and isinstance(heater.properties, dict):
                manufacturer = heater.properties.get("manufacturer")
                if manufacturer and manufacturer == "Rheem":
                    is_aquatherm = True
            # Check model attribute if it contains "AquaTherm" or "Rheem"
            elif hasattr(heater, "model") and heater.model:
                if "AquaTherm" in heater.model or "Rheem" in heater.model:
                    is_aquatherm = True

            if is_aquatherm:
                aquatherm_count += 1
            else:
                non_aquatherm_count += 1

        # Determine data source and connection status
        if using_mock:
            data_source = "mock"
            db_status = "not applicable (using mock data)"
        elif isinstance(service.repository, SQLiteWaterHeaterRepository):
            data_source = "sqlite"
            # Try to access the database to check connection
            try:
                # Simple validation by trying to access the database
                await service.repository.get_water_heaters()
                db_status = "connected"
            except Exception as e:
                logger.error(f"Database connection error: {str(e)}")
                db_status = f"error: {str(e)}"
        else:
            data_source = "unknown"
            db_status = "unknown"

        return WaterHeaterDataSourceInfo(
            data_source=data_source,
            total_water_heaters=len(water_heaters),
            using_mock_data=using_mock,
            repository_type=repo_type,
            aquatherm_count=aquatherm_count,
            non_aquatherm_count=non_aquatherm_count,
            database_connection_status=db_status,
        )

    except Exception as e:
        logger.error(f"Error checking water heater data source: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error checking water heater data source: {str(e)}"
        )
