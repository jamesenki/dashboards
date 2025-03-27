"""
Router for prediction API endpoints
"""
from typing import Dict, Any, Optional, List
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

@router.get("/water-heaters/{device_id}/anomaly-detection", response_model=PredictionResult)
async def get_anomaly_detection_prediction(
    device_id: str = Path(..., description="The ID of the water heater"),
    refresh: bool = Query(False, description="Force refresh the prediction")
):
    """
    Get anomaly detection predictions for a specific water heater
    
    Args:
        device_id: ID of the water heater
        refresh: If True, force recalculation of the prediction
        
    Returns:
        PredictionResult with anomaly detection details
    """
    prediction = await prediction_service.get_prediction(
        device_id=device_id,
        prediction_type="anomaly_detection",
        force_refresh=refresh
    )
    
    if not prediction:
        raise HTTPException(
            status_code=404, 
            detail="Water heater not found or prediction unavailable"
        )
    
    return prediction

@router.get("/water-heaters/{device_id}/usage-patterns", response_model=PredictionResult)
async def get_usage_pattern_prediction(
    device_id: str = Path(..., description="The ID of the water heater"),
    refresh: bool = Query(False, description="Force refresh the prediction")
):
    """
    Get usage pattern predictions for a specific water heater
    
    Args:
        device_id: ID of the water heater
        refresh: If True, force recalculation of the prediction
        
    Returns:
        PredictionResult with usage pattern analysis details
    """
    prediction = await prediction_service.get_prediction(
        device_id=device_id,
        prediction_type="usage_patterns",
        force_refresh=refresh
    )
    
    if not prediction:
        raise HTTPException(
            status_code=404, 
            detail="Water heater not found or prediction unavailable"
        )
    
    return prediction

@router.get("/water-heaters/{device_id}/multi-factor", response_model=PredictionResult)
async def get_multi_factor_prediction(
    device_id: str = Path(..., description="The ID of the water heater"),
    refresh: bool = Query(False, description="Force refresh the prediction")
):
    """
    Get multi-factor predictions for a specific water heater
    
    Args:
        device_id: ID of the water heater
        refresh: If True, force recalculation of the prediction
        
    Returns:
        PredictionResult with comprehensive multi-factor analysis
    """
    prediction = await prediction_service.get_prediction(
        device_id=device_id,
        prediction_type="multi_factor",
        force_refresh=refresh
    )
    
    if not prediction:
        raise HTTPException(
            status_code=404, 
            detail="Water heater not found or prediction unavailable"
        )
    
    return prediction

@router.get("/water-heaters/{device_id}/all", response_model=List[PredictionResult])
async def get_all_predictions(
    device_id: str = Path(..., description="The ID of the water heater"),
    refresh: bool = Query(False, description="Force refresh the predictions")
):
    """
    Get all available predictions for a specific water heater
    
    Args:
        device_id: ID of the water heater
        refresh: If True, force recalculation of all predictions
        
    Returns:
        List of PredictionResult objects for all prediction types
    """
    prediction_types = [
        "lifespan_estimation",
        "anomaly_detection",
        "usage_patterns",
        "multi_factor"
    ]
    
    results = []
    for prediction_type in prediction_types:
        prediction = await prediction_service.get_prediction(
            device_id=device_id,
            prediction_type=prediction_type,
            force_refresh=refresh
        )
        if prediction:
            results.append(prediction)
    
    if not results:
        raise HTTPException(
            status_code=404, 
            detail="Water heater not found or no predictions available"
        )
    
    return results
