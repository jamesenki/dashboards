"""
Tests for the component failure prediction model.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
from typing import Dict, List, Any

from src.predictions.interfaces import (
    PredictionResult,
    RecommendedAction,
    ActionSeverity
)
from src.predictions.maintenance.component_failure import (
    ComponentFailurePrediction,
    ComponentFailureActionRecommender
)


class TestComponentFailurePrediction:
    """Test suite for component failure prediction model."""
    
    @pytest.fixture
    def component_failure_model(self):
        """Fixture for component failure prediction model."""
        return ComponentFailurePrediction()
    
    @pytest.fixture
    def component_failure_recommender(self):
        """Fixture for component failure action recommender."""
        return ComponentFailureActionRecommender()
    
    @pytest.fixture
    def sample_features(self):
        """Sample features for prediction testing."""
        # Create realistic-looking water heater telemetry
        timestamps = pd.date_range(end=datetime.now(), periods=30, freq='H')
        
        # Temperature pattern with fluctuations
        temperatures = np.linspace(60, 70, 30) + np.random.normal(0, 2, 30)
        
        # Pressure with occasional spikes
        pressures = np.ones(30) * 2.5 + np.random.normal(0, 0.2, 30)
        pressures[5] = 3.5  # Abnormal spike
        
        # Energy usage with pattern
        energy_usage = np.ones(30) * 1200 + np.random.normal(0, 50, 30)
        energy_usage[10:20] = energy_usage[10:20] * 1.3  # Increased usage period
        
        # Flow rate with degradation
        flow_rates = np.linspace(10, 8.5, 30) + np.random.normal(0, 0.3, 30)
        
        # Heating cycles - time to heat water
        heating_cycles = np.ones(30) * 15 + np.random.normal(0, 1, 30)
        heating_cycles[20:] = heating_cycles[20:] * 1.2  # Recent slower heating
        
        return {
            "device_id": "test-water-heater-1",
            "timestamp": timestamps.tolist(),
            "temperature": temperatures.tolist(),
            "pressure": pressures.tolist(),
            "energy_usage": energy_usage.tolist(),
            "flow_rate": flow_rates.tolist(),
            "heating_cycles": heating_cycles.tolist(),
            "total_operation_hours": 8760,  # 1 year
            "maintenance_history": [
                {"type": "regular", "date": datetime.now() - timedelta(days=180)},
                {"type": "descaling", "date": datetime.now() - timedelta(days=365)}
            ]
        }
    
    @pytest.mark.asyncio
    async def test_model_initialization(self, component_failure_model):
        """Test that the model initializes correctly."""
        model_info = component_failure_model.get_model_info()
        
        assert "name" in model_info
        assert "version" in model_info
        assert "features_required" in model_info
        assert "temperature" in model_info["features_required"]
        assert "pressure" in model_info["features_required"]
    
    @pytest.mark.asyncio
    async def test_component_failure_prediction(self, component_failure_model, sample_features):
        """Test component failure prediction."""
        # Perform prediction
        result = await component_failure_model.predict(
            sample_features["device_id"], 
            sample_features
        )
        
        # Verify structure and basic values
        assert result.prediction_type == "component_failure"
        assert result.device_id == "test-water-heater-1"
        assert 0 <= result.predicted_value <= 1  # Probability of failure
        assert 0 <= result.confidence <= 1
        assert "temperature" in result.features_used
        assert "pressure" in result.features_used
        
        # Raw details should include component-specific predictions
        assert "raw_details" in result.dict()
        if result.raw_details:
            assert "components" in result.raw_details
    
    @pytest.mark.asyncio
    async def test_action_recommendations(self, component_failure_recommender):
        """Test action recommendations for component failure prediction."""
        # Create a sample prediction result
        prediction = PredictionResult(
            prediction_type="component_failure",
            device_id="test-water-heater-1",
            predicted_value=0.75,  # High probability of failure
            confidence=0.8,
            features_used=["temperature", "pressure", "heating_cycles"],
            timestamp=datetime.now(),
            recommended_actions=[],
            raw_details={
                "components": {
                    "heating_element": 0.85,  # High failure probability
                    "thermostat": 0.35,  # Low failure probability
                    "pressure_valve": 0.65  # Medium failure probability
                }
            }
        )
        
        # Get recommendations
        actions = await component_failure_recommender.recommend_actions(prediction)
        
        # Verify recommendations
        assert len(actions) > 0
        
        # Should prioritize the heating element (highest probability)
        heating_element_actions = [a for a in actions if "heating element" in a.description.lower()]
        assert len(heating_element_actions) > 0
        
        # At least one action should be high severity since heating element has high probability
        high_severity_actions = [a for a in actions if a.severity == ActionSeverity.HIGH]
        assert len(high_severity_actions) > 0
    
    @pytest.mark.asyncio
    async def test_prediction_model_with_low_risk(self, component_failure_model):
        """Test prediction with features indicating low risk."""
        # Create features indicating a healthy water heater
        features = {
            "device_id": "test-water-heater-2",
            "timestamp": pd.date_range(end=datetime.now(), periods=30, freq='H').tolist(),
            "temperature": np.ones(30) * 65 + np.random.normal(0, 0.5, 30),  # Stable temperature
            "pressure": np.ones(30) * 2.5 + np.random.normal(0, 0.1, 30),  # Stable pressure
            "energy_usage": np.ones(30) * 1000 + np.random.normal(0, 20, 30),  # Stable energy
            "flow_rate": np.ones(30) * 10 + np.random.normal(0, 0.1, 30),  # Good flow rate
            "heating_cycles": np.ones(30) * 12 + np.random.normal(0, 0.5, 30),  # Fast heating
            "total_operation_hours": 1000,  # Relatively new
            "maintenance_history": [
                {"type": "regular", "date": datetime.now() - timedelta(days=30)}  # Recent maintenance
            ]
        }
        
        # Perform prediction
        result = await component_failure_model.predict(features["device_id"], features)
        
        # Should indicate low failure probability
        assert result.predicted_value < 0.3
        
        # Should have fewer or lower severity recommendations
        assert len(result.recommended_actions) < 3  # Fewer actions needed
        
        # No critical or high severity actions expected
        high_severity_actions = [a for a in result.recommended_actions if a.severity in 
                                (ActionSeverity.HIGH, ActionSeverity.CRITICAL)]
        assert len(high_severity_actions) == 0
