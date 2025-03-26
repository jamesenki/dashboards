"""
Tests for the prediction service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.services.prediction import PredictionService
from src.predictions.interfaces import PredictionResult

# Apply class-level patches for test isolation
@pytest.mark.asyncio
@patch('src.services.water_heater.WaterHeaterService')
async def test_get_prediction_handles_missing_installation_date(mock_water_heater_svc):
    """
    Test that the prediction service properly handles a water heater without an installation_date
    """
    # Set up our mocks
    mock_water_heater_instance = AsyncMock()
    mock_water_heater_svc.return_value = mock_water_heater_instance
    
    # Create the prediction service
    prediction_service = PredictionService()
    
    # Mock the internal methods needed for the test
    async def mock_get_water_heater_lifespan_data(device_id):
        return {
            "device_id": device_id,
            "installation_date": None,  # This is what we're testing - missing installation date
            "model": "Test Model",
            "temperature_settings": 65.0,
            "total_operation_hours": 8760,  # 1 year
            "water_hardness": 7.5,
            "efficiency_degradation_rate": 0.05
        }
    
    # Apply the mock
    prediction_service._get_water_heater_lifespan_data = mock_get_water_heater_lifespan_data


    # Create a mock for the lifespan prediction result
    async def mock_generate_lifespan_prediction(device_id, features):
        from src.predictions.interfaces import ActionSeverity, RecommendedAction
        
        return PredictionResult(
            device_id=device_id,
            prediction_type="lifespan_estimation",
            predicted_value=0.75,  # 75% of expected lifespan remaining
            confidence=0.9,  # 90% confidence
            features_used=["installation_date", "model", "water_hardness"],
            timestamp=datetime.now(),
            recommended_actions=[
                RecommendedAction(
                    action_id=f"{device_id}_descaling",
                    description="Schedule descaling maintenance",
                    severity=ActionSeverity.MEDIUM,
                    impact="Prevent efficiency loss due to scale buildup",
                    expected_benefit="Extended lifespan and improved energy efficiency"
                )
            ],
            raw_details={
                "estimated_remaining_years": 8,
                "total_expected_lifespan": 13,
                "current_age": 5,
                "water_hardness_impact": "medium"
            }
        )
    
    # We're not going to mock _generate_lifespan_prediction anymore
    # This will test the actual implementation with the problematic temperature_settings as a float
    
    # Act: Get a prediction
    result = await prediction_service.get_prediction("wh-test-123", "lifespan_estimation")
    
    # Assert: Verify prediction is successful despite missing installation_date 
    # and temperature_settings being a float instead of a list
    assert result is not None
    assert isinstance(result, PredictionResult)
    assert result.device_id == "wh-test-123"
    assert result.prediction_type == "lifespan_estimation"
    # The actual values aren't important, just that we get a valid result without 500 error
    assert isinstance(result.predicted_value, float)
    assert isinstance(result.confidence, float)
    assert len(result.recommended_actions) > 0
