"""
Tests for the water heater predictions API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

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

@patch("src.api.predictions.PredictionService.get_prediction")
def test_get_lifespan_prediction(mock_get_prediction, mock_lifespan_prediction):
    """Test getting a lifespan prediction for a water heater"""
    # Configure the mock to return the prediction directly
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
