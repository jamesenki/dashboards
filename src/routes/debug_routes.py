"""
Debug routes for development purposes.
These routes help diagnose issues with data sources and other development concerns.
"""
from fastapi import APIRouter
from src.monitoring.model_monitoring_service import ModelMonitoringService
from src.db.real_database import SQLiteDatabase
from src.db.adapters.sqlite_model_metrics import SQLiteModelMetricsRepository
from src.monitoring.model_metrics_repository import ModelMetricsRepository

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
    db_count = sum(1 for m in models if m.get('data_source') == 'database')
    mock_count = sum(1 for m in models if m.get('data_source') == 'mock')
    unknown_count = sum(1 for m in models if 'data_source' not in m)
    
    # Prepare model summary
    model_summary = []
    for model in models:
        model_summary.append({
            "id": model['id'],
            "name": model['name'], 
            "data_source": model.get('data_source', 'unknown')
        })
    
    return {
        "summary": {
            "total_models": len(models),
            "from_database": db_count,
            "from_mock": mock_count,
            "unknown_source": unknown_count
        },
        "models": model_summary
    }
