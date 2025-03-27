"""
Tests for the water heater predictions API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import asyncio

from src.main import app
from src.predictions.interfaces import PredictionResult, RecommendedAction

client = TestClient(app)

@pytest.fixture
def mock_lifespan_prediction():
    """Create a mock lifespan prediction result"""
    return PredictionResult(
        device_id="test-wh-123",
        prediction_type="lifespan_estimation",
        predicted_value=0.75,
        confidence=0.85,
        features_used=["installation_date", "total_operation_hours", "water_hardness"],
        timestamp="2025-03-26T16:00:00",
        recommended_actions=[
            RecommendedAction(
                action_id="test-wh-123_regular_maintenance",
                description="Continue regular annual maintenance",
                severity="low",
                impact="Maintain optimal performance and maximize lifespan",
                expected_benefit="Prevention of premature wear and identification of minor issues",
                due_date="2026-03-26T16:00:00"
            )
        ],
        raw_details={
            "estimated_remaining_years": 7.5,
            "total_expected_lifespan_years": 10,
            "current_age_years": 2.5,
            "contributing_factors": [
                "Regular maintenance history",
                "Low water hardness",
                "Moderate usage intensity"
            ],
            "prediction_quality": "Complete"
        }
    )

@pytest.fixture
def mock_anomaly_detection_prediction():
    """Create a mock anomaly detection prediction result"""
    return PredictionResult(
        device_id="test-wh-123",
        prediction_type="anomaly_detection",
        predicted_value=0.65,
        confidence=0.90,
        features_used=["temperature_readings", "pressure_readings", "heating_cycle_data"],
        timestamp="2025-03-26T16:00:00",
        recommended_actions=[
            RecommendedAction(
                action_id="temp_trend_thermostat_20250326",
                description="Investigate thermostat due to anomaly in increasing temperature pattern",
                severity="high",
                impact="Temperature pattern indicates 92% probability of thermostat issues within 14 days",
                expected_benefit="Prevent potential thermostat failure and extend water heater lifespan",
                due_date="2025-04-10T16:00:00",
                estimated_cost=75.0,
                estimated_duration="1-2 hours"
            )
        ],
        raw_details={
            "detected_anomalies": [
                {
                    "measurement_type": "temperature",
                    "anomaly_type": "spike",
                    "timestamp": "2025-03-25T14:30:00",
                    "value": 155.5,
                    "baseline": 140.0,
                    "deviation_percent": 11.07
                }
            ],
            "trend_analysis": {
                "temperature": {
                    "trend_direction": "increasing",
                    "rate_of_change_per_day": 0.8,
                    "component_affected": "thermostat",
                    "probability": 0.92,
                    "days_until_critical": 14
                }
            }
        }
    )

@pytest.fixture
def mock_usage_pattern_prediction():
    """Create a mock usage pattern prediction result"""
    return PredictionResult(
        device_id="test-wh-123",
        prediction_type="usage_patterns",
        predicted_value=0.55,
        confidence=0.85,
        features_used=["hourly_usage", "daily_usage", "weekly_usage_pattern", "recovery_times"],
        timestamp="2025-03-26T16:00:00",
        recommended_actions=[
            RecommendedAction(
                action_id="usage_wear_heating_element_20250326",
                description="Monitor Heating Element due to High usage pattern",
                severity="medium",
                impact="Current High usage pattern accelerating Heating Element wear by 35% above normal",
                expected_benefit="Early detection of Heating Element degradation to prevent unexpected failures",
                due_date="2025-05-26T16:00:00",
                estimated_cost=None,
                estimated_duration="N/A - ongoing monitoring"
            )
        ],
        raw_details={
            "usage_classification": "high",
            "peak_periods": ["7:00-8:00", "19:00-21:00"],
            "component_impacts": {
                "heating_element": {
                    "wear_factor": 1.35,
                    "days_until_impact": 60
                },
                "thermostat": {
                    "wear_factor": 1.15,
                    "days_until_impact": 90
                }
            },
            "efficiency_projection": {
                "current_efficiency": 0.88,
                "projected_decline_30_days": 0.03,
                "projected_decline_90_days": 0.08
            }
        }
    )

@pytest.fixture
def mock_multi_factor_prediction():
    """Create a mock multi-factor prediction result"""
    return PredictionResult(
        device_id="test-wh-123",
        prediction_type="multi_factor",
        predicted_value=0.40,
        confidence=0.95,
        features_used=["water_hardness", "ambient_temperature", "component_health", "maintenance_history", "usage_patterns"],
        timestamp="2025-03-26T16:00:00",
        recommended_actions=[
            RecommendedAction(
                action_id="water_softener_high_20250326",
                description="Install water softener system for high water hardness",
                impact="Reduce scale buildup damage to heating element and tank, extending lifespan by 15-25%",
                expected_benefit="Increased efficiency, longer component lifespan, and reduced maintenance costs",
                severity="medium",
                due_date="2025-04-26T16:00:00",
                estimated_cost=350.0,
                estimated_duration="4-6 hours"
            )
        ],
        raw_details={
            "combined_factors": True,
            "factor_scores": {
                "water_quality": 0.65,
                "component_interactions": 0.45,
                "maintenance_history": 0.30
            },
            "environmental_impact": {
                "scale_buildup": {
                    "severity": "high",
                    "impact_score": 0.7,
                    "days_until_critical": 60
                }
            },
            "component_interactions": {
                "thermostat_heating_element": {
                    "source_component": "thermostat",
                    "target_component": "heating_element",
                    "interaction_strength": 0.7,
                    "source_degradation": 0.25,
                    "days_until_impact": 45
                }
            },
            "overall_evaluation": {
                "risk_category": "medium",
                "combined_score": 0.4,
                "top_contributing_factors": ["water_quality", "component_interactions"],
                "estimated_months_to_failure": 24
            }
        }
    )

@patch("src.api.predictions.PredictionService.get_prediction")
def test_get_lifespan_prediction(mock_get_prediction, mock_lifespan_prediction):
    """Test getting a lifespan prediction for a water heater"""
    # Configure the mock to return the prediction
    mock_get_prediction.return_value = mock_lifespan_prediction
    
    # Make the request
    response = client.get("/api/predictions/water-heaters/test-wh-123/lifespan-estimation")
    
    # Verify the response
    assert response.status_code == 200
    
    # Check prediction data
    data = response.json()
    assert data["device_id"] == "test-wh-123"
    assert data["prediction_type"] == "lifespan_estimation"
    assert data["predicted_value"] == 0.75
    assert data["confidence"] == 0.85
    
    # Check recommended actions
    assert len(data["recommended_actions"]) == 1
    action = data["recommended_actions"][0]
    assert action["description"] == "Continue regular annual maintenance"
    assert action["severity"] == "low"
    
    # Check raw details
    assert data["raw_details"]["estimated_remaining_years"] == 7.5
    assert data["raw_details"]["current_age_years"] == 2.5
    assert len(data["raw_details"]["contributing_factors"]) == 3

@patch("src.api.predictions.PredictionService.get_prediction")
def test_get_lifespan_prediction_not_found(mock_get_prediction):
    """Test getting a lifespan prediction for a non-existent water heater"""
    # Configure the mock to return None
    mock_get_prediction.return_value = None
    
    # Make the request
    response = client.get("/api/predictions/water-heaters/non-existent-id/lifespan-estimation")
    
    # Verify the response
    assert response.status_code == 404
    assert response.json()["detail"] == "Water heater not found or prediction unavailable"

@patch("src.api.predictions.PredictionService.get_prediction")
def test_get_anomaly_detection_prediction(mock_get_prediction, mock_anomaly_detection_prediction):
    """Test getting an anomaly detection prediction for a water heater"""
    # Configure the mock to return the prediction
    mock_get_prediction.return_value = mock_anomaly_detection_prediction
    
    # Make the request
    response = client.get("/api/predictions/water-heaters/test-wh-123/anomaly-detection")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == "test-wh-123"
    assert data["prediction_type"] == "anomaly_detection"
    assert len(data["recommended_actions"]) > 0
    assert "detected_anomalies" in data["raw_details"]
    assert "trend_analysis" in data["raw_details"]

@patch("src.api.predictions.PredictionService.get_prediction")
def test_get_usage_pattern_prediction(mock_get_prediction, mock_usage_pattern_prediction):
    """Test getting a usage pattern prediction for a water heater"""
    # Configure the mock to return the prediction
    mock_get_prediction.return_value = mock_usage_pattern_prediction
    
    # Make the request
    response = client.get("/api/predictions/water-heaters/test-wh-123/usage-patterns")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == "test-wh-123"
    assert data["prediction_type"] == "usage_patterns"
    assert len(data["recommended_actions"]) > 0
    assert "usage_classification" in data["raw_details"]
    assert "component_impacts" in data["raw_details"]

@patch("src.api.predictions.PredictionService.get_prediction")
def test_get_multi_factor_prediction(mock_get_prediction, mock_multi_factor_prediction):
    """Test getting a multi-factor prediction for a water heater"""
    # Configure the mock to return the prediction
    mock_get_prediction.return_value = mock_multi_factor_prediction
    
    # Make the request
    response = client.get("/api/predictions/water-heaters/test-wh-123/multi-factor")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == "test-wh-123"
    assert data["prediction_type"] == "multi_factor"
    assert len(data["recommended_actions"]) > 0
    assert "combined_factors" in data["raw_details"]
    assert "environmental_impact" in data["raw_details"]
    assert "component_interactions" in data["raw_details"]
    assert "overall_evaluation" in data["raw_details"]

@patch("src.api.predictions.PredictionService.get_prediction")
def test_get_all_predictions(mock_get_prediction, mock_lifespan_prediction, mock_anomaly_detection_prediction, 
                               mock_usage_pattern_prediction, mock_multi_factor_prediction):
    """Test getting all predictions for a water heater"""
    # Configure the mock to return different predictions based on prediction_type
    mock_get_prediction.side_effect = None  # Clear any previous side effects
    
    # Create a mapping of prediction types to their mock results
    prediction_map = {
        "lifespan_estimation": mock_lifespan_prediction,
        "anomaly_detection": mock_anomaly_detection_prediction,
        "usage_patterns": mock_usage_pattern_prediction,
        "multi_factor": mock_multi_factor_prediction
    }
    
    # Create a side effect function that returns the appropriate mock
    def side_effect(device_id, prediction_type, force_refresh=False):
        return prediction_map.get(prediction_type, None)
    
    mock_get_prediction.side_effect = side_effect
    
    # Make the request
    response = client.get("/api/predictions/water-heaters/test-wh-123/all")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    prediction_types = [pred["prediction_type"] for pred in data]
    assert "lifespan_estimation" in prediction_types
    assert "anomaly_detection" in prediction_types
    assert "usage_patterns" in prediction_types
    assert "multi_factor" in prediction_types
