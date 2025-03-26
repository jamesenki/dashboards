"""
Router for prediction API endpoints
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Path, Query

from src.services.prediction import PredictionService
from src.predictions.interfaces import PredictionResult

router = APIRouter(prefix="/predictions", tags=["predictions"])
prediction_service = PredictionService()

@router.get("/water-heaters/{device_id}/lifespan-estimation", response_model=PredictionResult)
async def get_lifespan_prediction(
    device_id: str = Path(..., description="The ID of the water heater"),
    refresh: bool = Query(False, description="Force refresh the prediction")
):
    """
    Get a lifespan estimation prediction for a specific water heater
    
    Args:
        device_id: ID of the water heater
        refresh: If True, force recalculation of the prediction
        
    Returns:
        PredictionResult with lifespan estimation details
    """
    prediction = await prediction_service.get_prediction(
        device_id=device_id,
        prediction_type="lifespan_estimation",
        force_refresh=refresh
    )
    
    # Ensure we're returning a proper PredictionResult object
    
    if not prediction:
        raise HTTPException(
            status_code=404, 
            detail="Water heater not found or prediction unavailable"
        )
    
    return prediction
