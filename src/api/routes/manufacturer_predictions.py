"""
Manufacturer-agnostic API for water heater predictions.

This module provides prediction endpoints for water heaters from any manufacturer,
following the manufacturer-agnostic API pattern for consistency.
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Path, Query

from src.predictions.interfaces import ActionSeverity, PredictionResult, RecommendedAction
from src.services.prediction import PredictionService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/manufacturer/water-heaters",
    tags=["predictions", "manufacturer"],
    responses={
        404: {"description": "Water heater not found or prediction unavailable"},
        500: {"description": "Server error"},
    },
)

prediction_service = PredictionService()


def create_mock_lifespan_prediction(device_id: str) -> PredictionResult:
    """Create mock lifespan prediction for development mode."""
    current_time = datetime.now()
    due_date = current_time + timedelta(days=30)
    
    return PredictionResult(
        prediction_type="lifespan_estimation",
        device_id=device_id,
        predicted_value=1825.0,  # Days (5 years)
        confidence=0.92,
        features_used=["operational_time", "water_quality", "temperature_variations"],
        timestamp=current_time,
        recommended_actions=[
            RecommendedAction(
                action_id=f"maintenance_{device_id}_{current_time.strftime('%Y%m%d')}",
                description="Schedule routine maintenance",
                severity=ActionSeverity.MEDIUM,
                impact="Extends lifespan by preventing scaling and corrosion",
                expected_benefit="Extended operational life",
                due_date=due_date,
                estimated_cost=150.0,
                estimated_duration="2 hours",
            )
        ],
        raw_details={
            "lifetime_metrics": {
                "estimated_total_days": 1825,
                "expected_high_efficiency_days": 1460,
                "component_breakdown": {
                    "heating_element": {"estimated_days": 1825, "confidence": 0.95},
                    "thermostat": {"estimated_days": 2190, "confidence": 0.92},
                    "tank": {"estimated_days": 2555, "confidence": 0.90},
                }
            },
            "environmental_factors": {
                "water_hardness": "medium",
                "temperature_range": "normal",
                "usage_intensity": "moderate"
            }
        },
    )


def create_mock_anomaly_prediction(device_id: str) -> PredictionResult:
    """Create mock anomaly detection for development mode."""
    current_time = datetime.now()
    due_date = current_time + timedelta(days=7)
    
    return PredictionResult(
        prediction_type="anomaly_detection",
        device_id=device_id,
        predicted_value=0.15,  # 15% chance of anomaly
        confidence=0.88,
        features_used=["temperature_pattern", "pressure_readings", "energy_consumption"],
        timestamp=current_time,
        recommended_actions=[
            RecommendedAction(
                action_id=f"inspect_{device_id}_{current_time.strftime('%Y%m%d')}",
                description="Inspect temperature sensor",
                severity=ActionSeverity.LOW,
                impact="Ensures accurate temperature control",
                expected_benefit="Prevents potential overheating issues",
                due_date=due_date,
                estimated_cost=50.0,
                estimated_duration="30 minutes",
            )
        ],
        raw_details={
            "detected_anomalies": [
                {
                    "type": "temperature_fluctuation",
                    "severity": "low",
                    "first_detected": (current_time - timedelta(days=2)).isoformat(),
                    "confidence": 0.82
                }
            ],
            "trend_analysis": {
                "temperature": {
                    "trend_direction": "slightly_increasing",
                    "rate_of_change_per_day": 0.3,
                    "component_affected": "heating_element",
                    "probability": 0.15,
                    "days_until_critical": 60,
                }
            },
        },
    )


def create_mock_usage_prediction(device_id: str) -> PredictionResult:
    """Create mock usage pattern prediction for development mode."""
    current_time = datetime.now()
    
    return PredictionResult(
        prediction_type="usage_patterns",
        device_id=device_id,
        predicted_value=42.5,  # Daily gallons used
        confidence=0.94,
        features_used=["time_of_day_usage", "day_of_week", "seasonal_patterns"],
        timestamp=current_time,
        recommended_actions=[],
        raw_details={
            "daily_patterns": {
                "morning_peak": {"start": "06:30", "end": "08:30", "intensity": "high"},
                "evening_peak": {"start": "18:00", "end": "21:00", "intensity": "medium"},
            },
            "weekly_patterns": {
                "weekday_avg_gallons": 45.2,
                "weekend_avg_gallons": 52.8,
                "highest_usage_day": "Saturday",
            },
            "seasonal_variations": {
                "winter_adjustment": 1.15,  # 15% more usage in winter
                "summer_adjustment": 0.92,  # 8% less usage in summer
            },
            "energy_efficiency_recommendations": {
                "optimal_temperature": 120,
                "potential_savings_percent": 8.5,
            }
        },
    )


def create_mock_multifactor_prediction(device_id: str) -> PredictionResult:
    """Create mock multi-factor analysis for development mode."""
    current_time = datetime.now()
    due_date = current_time + timedelta(days=90)
    
    return PredictionResult(
        prediction_type="multi_factor",
        device_id=device_id,
        predicted_value=0.78,  # Efficiency score
        confidence=0.91,
        features_used=["efficiency", "maintenance_history", "water_quality", "usage_patterns"],
        timestamp=current_time,
        recommended_actions=[
            RecommendedAction(
                action_id=f"optimize_{device_id}_{current_time.strftime('%Y%m%d')}",
                description="Optimize temperature settings based on usage patterns",
                severity=ActionSeverity.LOW,
                impact="Reduce energy consumption while maintaining comfort",
                expected_benefit="10% reduction in energy costs",
                due_date=due_date,
                estimated_cost=0.0,
                estimated_duration="15 minutes",
            )
        ],
        raw_details={
            "factor_weights": {
                "age": 0.25,
                "maintenance": 0.30,
                "water_quality": 0.25,
                "usage_intensity": 0.20,
            },
            "factor_scores": {
                "age": 0.85,  # Newer unit scores higher
                "maintenance": 0.65,  # Could improve with more regular maintenance
                "water_quality": 0.70,  # Moderate water hardness
                "usage_intensity": 0.90,  # Normal usage patterns
            },
            "interaction_effects": {
                "age_x_maintenance": 0.15,  # Regular maintenance more important with age
                "water_quality_x_usage": 0.10,  # Hard water + heavy usage accelerates wear
            },
            "optimization_scenarios": {
                "scenario_1": {
                    "description": "Maintain current settings",
                    "efficiency_score": 0.78,
                    "annual_cost": 520,
                },
                "scenario_2": {
                    "description": "Optimize temperature and usage times",
                    "efficiency_score": 0.85,
                    "annual_cost": 470,
                },
                "scenario_3": {
                    "description": "Install recirculation pump",
                    "efficiency_score": 0.92,
                    "annual_cost": 430,
                    "installation_cost": 350,
                },
            }
        },
    )


@router.get(
    "/{device_id}/predictions/lifespan", 
    response_model=PredictionResult,
    summary="Get Lifespan Prediction",
    description="Returns lifespan estimation prediction for a specific water heater",
)
async def get_lifespan_prediction(
    device_id: str = Path(..., description="The ID of the water heater"),
    refresh: bool = Query(False, description="Force refresh the prediction"),
):
    """
    Get a lifespan estimation prediction for a specific water heater

    Args:
        device_id: ID of the water heater
        refresh: If True, force recalculation of the prediction

    Returns:
        PredictionResult with lifespan estimation details
    """
    try:
        prediction = await prediction_service.get_prediction(
            device_id=device_id,
            prediction_type="lifespan_estimation",
            force_refresh=refresh,
        )

        if not prediction:
            # In development mode, return mock data
            if os.getenv("IOTSPHERE_ENV", "development") == "development":
                logger.info(f"Returning mock lifespan prediction for {device_id}")
                return create_mock_lifespan_prediction(device_id)
            raise HTTPException(
                status_code=404, detail="Water heater not found or prediction unavailable"
            )

        return prediction
    except Exception as e:
        logger.error(f"Error generating lifespan prediction: {str(e)}")
        if os.getenv("IOTSPHERE_ENV", "development") == "development":
            return create_mock_lifespan_prediction(device_id)
        raise HTTPException(
            status_code=500, detail=f"Error generating prediction: {str(e)}"
        )


@router.get(
    "/{device_id}/predictions/anomalies", 
    response_model=PredictionResult,
    summary="Get Anomaly Detection",
    description="Returns anomaly detection prediction for a specific water heater",
)
async def get_anomaly_detection_prediction(
    device_id: str = Path(..., description="The ID of the water heater"),
    refresh: bool = Query(False, description="Force refresh the prediction"),
):
    """
    Get anomaly detection predictions for a specific water heater

    Args:
        device_id: ID of the water heater
        refresh: If True, force recalculation of the prediction

    Returns:
        PredictionResult with anomaly detection details
    """
    try:
        prediction = await prediction_service.get_prediction(
            device_id=device_id, 
            prediction_type="anomaly_detection", 
            force_refresh=refresh
        )

        if not prediction:
            # In development mode, return mock data
            if os.getenv("IOTSPHERE_ENV", "development") == "development":
                logger.info(f"Returning mock anomaly detection for {device_id}")
                return create_mock_anomaly_prediction(device_id)
            raise HTTPException(
                status_code=404, detail="Water heater not found or prediction unavailable"
            )

        return prediction
    except Exception as e:
        logger.error(f"Error generating anomaly detection: {str(e)}")
        if os.getenv("IOTSPHERE_ENV", "development") == "development":
            return create_mock_anomaly_prediction(device_id)
        raise HTTPException(
            status_code=500, detail=f"Error generating prediction: {str(e)}"
        )


@router.get(
    "/{device_id}/predictions/usage", 
    response_model=PredictionResult,
    summary="Get Usage Pattern Prediction",
    description="Returns usage pattern prediction for a specific water heater",
)
async def get_usage_pattern_prediction(
    device_id: str = Path(..., description="The ID of the water heater"),
    refresh: bool = Query(False, description="Force refresh the prediction"),
):
    """
    Get usage pattern predictions for a specific water heater

    Args:
        device_id: ID of the water heater
        refresh: If True, force recalculation of the prediction

    Returns:
        PredictionResult with usage pattern analysis details
    """
    try:
        prediction = await prediction_service.get_prediction(
            device_id=device_id, 
            prediction_type="usage_patterns", 
            force_refresh=refresh
        )

        if not prediction:
            # In development mode, return mock data
            if os.getenv("IOTSPHERE_ENV", "development") == "development":
                logger.info(f"Returning mock usage patterns for {device_id}")
                return create_mock_usage_prediction(device_id)
            raise HTTPException(
                status_code=404, detail="Water heater not found or prediction unavailable"
            )

        return prediction
    except Exception as e:
        logger.error(f"Error generating usage patterns: {str(e)}")
        if os.getenv("IOTSPHERE_ENV", "development") == "development":
            return create_mock_usage_prediction(device_id)
        raise HTTPException(
            status_code=500, detail=f"Error generating prediction: {str(e)}"
        )


@router.get(
    "/{device_id}/predictions/factors", 
    response_model=PredictionResult,
    summary="Get Multi-Factor Prediction",
    description="Returns multi-factor prediction analysis for a specific water heater",
)
async def get_multi_factor_prediction(
    device_id: str = Path(..., description="The ID of the water heater"),
    refresh: bool = Query(False, description="Force refresh the prediction"),
):
    """
    Get multi-factor predictions for a specific water heater

    Args:
        device_id: ID of the water heater
        refresh: If True, force recalculation of the prediction

    Returns:
        PredictionResult with comprehensive multi-factor analysis
    """
    try:
        prediction = await prediction_service.get_prediction(
            device_id=device_id, 
            prediction_type="multi_factor", 
            force_refresh=refresh
        )

        if not prediction:
            # In development mode, return mock data
            if os.getenv("IOTSPHERE_ENV", "development") == "development":
                logger.info(f"Returning mock multi-factor analysis for {device_id}")
                return create_mock_multifactor_prediction(device_id)
            raise HTTPException(
                status_code=404, detail="Water heater not found or prediction unavailable"
            )

        return prediction
    except Exception as e:
        logger.error(f"Error generating multi-factor analysis: {str(e)}")
        if os.getenv("IOTSPHERE_ENV", "development") == "development":
            return create_mock_multifactor_prediction(device_id)
        raise HTTPException(
            status_code=500, detail=f"Error generating prediction: {str(e)}"
        )


@router.get(
    "/{device_id}/predictions/all", 
    response_model=List[PredictionResult],
    summary="Get All Predictions",
    description="Returns all available predictions for a specific water heater",
)
async def get_all_predictions(
    device_id: str = Path(..., description="The ID of the water heater"),
    refresh: bool = Query(False, description="Force refresh the predictions"),
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
        "multi_factor",
    ]

    results = []
    for prediction_type in prediction_types:
        try:
            prediction = await prediction_service.get_prediction(
                device_id=device_id, 
                prediction_type=prediction_type, 
                force_refresh=refresh
            )
            if prediction:
                results.append(prediction)
        except Exception as e:
            logger.error(f"Error getting {prediction_type} prediction: {str(e)}")
            # In development, create mock predictions for each type
            if os.getenv("IOTSPHERE_ENV", "development") == "development":
                if prediction_type == "lifespan_estimation":
                    results.append(create_mock_lifespan_prediction(device_id))
                elif prediction_type == "anomaly_detection":
                    results.append(create_mock_anomaly_prediction(device_id))
                elif prediction_type == "usage_patterns":
                    results.append(create_mock_usage_prediction(device_id))
                elif prediction_type == "multi_factor":
                    results.append(create_mock_multifactor_prediction(device_id))

    # In development mode, always return mock data if no results
    if not results and os.getenv("IOTSPHERE_ENV", "development") == "development":
        logger.info(f"Returning all mock predictions for {device_id}")
        results.append(create_mock_lifespan_prediction(device_id))
        results.append(create_mock_anomaly_prediction(device_id))
        results.append(create_mock_usage_prediction(device_id))
        results.append(create_mock_multifactor_prediction(device_id))
    elif not results:
        raise HTTPException(
            status_code=404, detail="Water heater not found or no predictions available"
        )

    return results
