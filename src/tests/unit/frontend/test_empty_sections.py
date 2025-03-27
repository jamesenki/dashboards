"""
Unit tests for handling empty sections in the water heater predictions UI.

These tests verify that the predictions system properly handles missing or empty data
and displays appropriate messages in the UI rather than showing empty sections.
"""
import pytest
from unittest.mock import patch
from datetime import datetime

from src.predictions.interfaces import PredictionResult
from src.predictions.advanced.usage_patterns import UsagePatternPredictor
from src.predictions.advanced.anomaly_detection import AnomalyDetectionPredictor
from src.predictions.advanced.multi_factor import MultiFactorPredictor


class TestEmptySectionsHandling:
    """Test that empty sections in prediction results are handled gracefully in the UI."""
    
    def setup_method(self):
        """Set up test data."""
        self.device_id = "test-wh-001"
        self.standard_features = {
            "system_age": {"years": 3, "months": 2},
            "temperature_setting": 130,
            "heating_cycles_per_day": 8,
            "daily_usage_liters": 180,
            "usage_history": [
                {"date": "2024-12-29", "value": 170},
                {"date": "2024-12-30", "value": 185},
                {"date": "2024-12-31", "value": 155},
                {"date": "2025-01-01", "value": 210},
                {"date": "2025-01-02", "value": 126}
            ]
        }
    
    @pytest.mark.asyncio
    async def test_usage_pattern_with_empty_component_impacts(self):
        """Test that usage pattern prediction handles empty component impacts properly."""
        predictor = UsagePatternPredictor()
        
        # Patch the _calculate_component_impacts method to create empty impact_on_components
        with patch.object(UsagePatternPredictor, '_calculate_component_impacts', return_value=None):
            result = await predictor.predict(device_id=self.device_id, features=self.standard_features)
            
            assert isinstance(result, PredictionResult)
            # Check if impact_on_components exists, even if empty
            assert "impact_on_components" in result.raw_details
            
            # Verify that we still have recommendations despite empty component impacts
            assert len(result.recommended_actions) > 0
    
    @pytest.mark.asyncio
    async def test_usage_pattern_with_empty_optimizations(self):
        """Test that usage pattern prediction handles empty optimization data properly."""
        predictor = UsagePatternPredictor()
        
        # Patch the _generate_optimization_recommendations method to return empty recommendations
        with patch.object(UsagePatternPredictor, '_generate_optimization_recommendations', return_value=[]):
            result = await predictor.predict(device_id=self.device_id, features=self.standard_features)
            
            assert isinstance(result, PredictionResult)
            # Verify that we still have at least one recommendation despite empty optimizations
            assert len(result.recommended_actions) > 0
            
            # Verify that a fallback recommendation is provided
            assert any("general recommendation" in action.description.lower() for action in result.recommended_actions)
    
    @pytest.mark.asyncio
    async def test_anomaly_detection_with_no_anomalies(self):
        """Test that anomaly detection properly handles cases with no detected anomalies."""
        predictor = AnomalyDetectionPredictor()
        
        # Use minimal features to ensure no anomalies are detected
        minimal_features = {
            "temperature_readings": [
                {"timestamp": "2025-01-01T08:00:00", "value": 130.0},
                {"timestamp": "2025-01-01T10:00:00", "value": 131.0},
                {"timestamp": "2025-01-01T12:00:00", "value": 130.5},
                {"timestamp": "2025-01-01T14:00:00", "value": 130.2},
                {"timestamp": "2025-01-01T16:00:00", "value": 130.3}
            ]
        }
        
        result = await predictor.predict(device_id=self.device_id, features=minimal_features)
        
        assert isinstance(result, PredictionResult)
        assert "anomalies" in result.raw_details
        
        # If no anomalies, we should have a default recommendation
        assert len(result.recommended_actions) > 0
        assert "No anomalies detected" in result.recommended_actions[0].description
    
    @pytest.mark.asyncio
    async def test_multi_factor_with_empty_component_interactions(self):
        """Test that multi-factor prediction handles empty component interactions properly."""
        predictor = MultiFactorPredictor()
        
        minimal_features = {
            "system_age": {"years": 1},
            "temperature_setting": 125
        }
        
        result = await predictor.predict(device_id=self.device_id, features=minimal_features)
        
        assert isinstance(result, PredictionResult)
        assert "component_interactions" in result.raw_details
        assert len(result.recommended_actions) > 0
    
    @pytest.mark.asyncio
    async def test_all_predictions_provide_fallback_content(self):
        """Test that all prediction types provide fallback content when data is missing."""
        # Test each predictor type
        usage_predictor = UsagePatternPredictor()
        anomaly_predictor = AnomalyDetectionPredictor()
        multi_factor_predictor = MultiFactorPredictor()
        
        # Create very minimal features that might lead to limited prediction data
        minimal_features = {
            "system_age": {"years": 1},
            "temperature_setting": 125
        }
        
        # Test usage pattern predictor with minimal data
        with patch.object(UsagePatternPredictor, '_calculate_component_impacts', return_value={}):
            result = await usage_predictor.predict(device_id=self.device_id, features=minimal_features)
            
            # Verify we still have recommendations
            assert len(result.recommended_actions) > 0
            assert result.prediction_type == "usage_patterns"
            assert result.raw_details is not None
        
        # Test anomaly detection predictor with minimal data
        result = await anomaly_predictor.predict(device_id=self.device_id, features=minimal_features)
        
        # Verify we still have recommendations
        assert len(result.recommended_actions) > 0
        assert result.prediction_type == "anomaly_detection"
        assert result.raw_details is not None
        
        # Test multi-factor predictor with minimal data
        result = await multi_factor_predictor.predict(device_id=self.device_id, features=minimal_features)
        
        # Verify we still have recommendations
        assert len(result.recommended_actions) > 0
        assert result.prediction_type == "multi_factor"
        assert result.raw_details is not None
