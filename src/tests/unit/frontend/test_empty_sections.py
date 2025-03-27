"""
Unit tests for handling empty sections in the water heater predictions UI.

These tests verify that the predictions system properly handles missing or empty data
and displays appropriate messages in the UI rather than showing empty sections.
"""
import pytest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup

from src.predictions.advanced.usage_patterns import UsagePatternPredictor
from src.predictions.advanced.anomaly_detection import AnomalyDetectionPredictor
from src.predictions.advanced.multi_factor import MultiFactorPredictor
from src.predictions.interfaces import PredictionResult


class TestEmptySectionsHandling:
    """Test that empty sections in prediction results are handled gracefully in the UI."""
    
    def setup_method(self):
        """Set up test data."""
        self.device_id = "test-device-123"
        self.standard_features = {
            "system_age": {"years": 3, "months": 2},
            "usage_history": [
                {"date": "2025-01-01", "gallons": 50},
                {"date": "2025-01-02", "gallons": 45}
            ],
            "temperature_history": [
                {"date": "2025-01-01", "value": 125},
                {"date": "2025-01-02", "value": 126}
            ]
        }
    
    def test_usage_pattern_with_empty_component_impacts(self):
        """Test that usage pattern prediction handles empty component impacts properly."""
        predictor = UsagePatternPredictor()
        
        # Patch the _calculate_component_impacts method to create empty impact_on_components
        with patch.object(UsagePatternPredictor, '_calculate_component_impacts', return_value=None):
            result = predictor.predict(device_id=self.device_id, features=self.standard_features)
            
            assert isinstance(result, PredictionResult)
            # Check if impact_on_components exists, even if empty
            assert "impact_on_components" in result.raw_details
            
            # Verify that we still have recommendations despite empty component impacts
            assert len(result.recommended_actions) > 0
    
    def test_usage_pattern_with_empty_optimizations(self):
        """Test that usage pattern prediction handles empty optimization recommendations properly."""
        predictor = UsagePatternPredictor()
        
        # Use minimal features to produce empty optimizations
        minimal_features = {
            "system_age": {"years": 1},
            "usage_history": []
        }
        
        result = predictor.predict(device_id=self.device_id, features=minimal_features)
        
        assert isinstance(result, PredictionResult)
        # Check if we still have recommendations despite minimal features
        assert len(result.recommended_actions) > 0
    
    def test_anomaly_detection_with_no_anomalies(self):
        """Test that anomaly detection properly handles cases with no detected anomalies."""
        predictor = AnomalyDetectionPredictor()
        
        # Use minimal features to ensure no anomalies are detected
        minimal_features = {
            "temperature_history": []
        }
        
        result = predictor.predict(device_id=self.device_id, features=minimal_features)
        
        assert isinstance(result, PredictionResult)
        # Verify that we still have at least one recommendation even with no data
        assert len(result.recommended_actions) > 0
        
        # Check for monitoring-related recommendation
        monitoring_exists = False
        for action in result.recommended_actions:
            if action.description and "monitor" in action.description.lower():
                monitoring_exists = True
                break
                
        assert monitoring_exists, "Should include a monitoring recommendation"
    
    def test_multi_factor_with_empty_component_interactions(self):
        """Test that multi-factor prediction handles empty component interactions properly."""
        predictor = MultiFactorPredictor()
        
        # Use minimal features to ensure empty component interactions
        minimal_features = {
            "system_age": {"years": 1}
        }
        
        result = predictor.predict(device_id=self.device_id, features=minimal_features)
        
        assert isinstance(result, PredictionResult)
        assert "component_interactions" in result.raw_details
        
        # Component interactions might be a list or dict depending on implementation
        # The important thing is that we handle empty values gracefully
        if isinstance(result.raw_details["component_interactions"], list):
            pass  # List is fine
        elif isinstance(result.raw_details["component_interactions"], dict):
            pass  # Dict is also fine
        else:
            assert False, f"component_interactions should be a list or dict, got {type(result.raw_details['component_interactions'])}"
            
        # Verify that we still have recommendations
        assert len(result.recommended_actions) > 0
    
    def test_all_predictions_provide_fallback_content(self):
        """Test that all prediction types provide fallback content for empty sections."""
        predictors = [
            UsagePatternPredictor(),
            AnomalyDetectionPredictor(),
            MultiFactorPredictor()
        ]
        
        for predictor in predictors:
            result = predictor.predict(device_id=self.device_id, features={})
            
            # All predictions should have at least one recommendation even with empty features
            assert len(result.recommended_actions) > 0
            
            # All predictions should have raw_details
            assert isinstance(result.raw_details, dict)
            assert len(result.raw_details) > 0
