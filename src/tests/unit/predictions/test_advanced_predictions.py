"""
Unit tests for advanced water heater prediction models.

Tests the implementation of anomaly detection, usage pattern analysis,
and multi-factor prediction models.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.predictions.interfaces import PredictionResult, ActionSeverity, RecommendedAction
from src.predictions.advanced.anomaly_detection import AnomalyDetectionPredictor
from src.predictions.advanced.usage_patterns import UsagePatternPredictor
from src.predictions.advanced.multi_factor import MultiFactorPredictor


class TestAnomalyDetectionPredictor:
    """Tests for the anomaly detection prediction model."""
    
    def test_initialization(self):
        """Test that the anomaly detection predictor can be initialized."""
        predictor = AnomalyDetectionPredictor()
        assert predictor is not None
    
    def test_anomaly_detection_prediction(self):
        """Test that anomaly detection generates predictions based on telemetry patterns."""
        # Arrange
        predictor = AnomalyDetectionPredictor()
        mock_telemetry = {
            'temperature_readings': [
                {'timestamp': datetime.now() - timedelta(days=30), 'value': 140},
                {'timestamp': datetime.now() - timedelta(days=25), 'value': 142},
                {'timestamp': datetime.now() - timedelta(days=20), 'value': 145},
                {'timestamp': datetime.now() - timedelta(days=15), 'value': 148},
                {'timestamp': datetime.now() - timedelta(days=10), 'value': 151},
                {'timestamp': datetime.now() - timedelta(days=5), 'value': 155},
                {'timestamp': datetime.now(), 'value': 159},
            ],
            'pressure_readings': [
                {'timestamp': datetime.now() - timedelta(days=30), 'value': 50},
                {'timestamp': datetime.now() - timedelta(days=20), 'value': 52},
                {'timestamp': datetime.now() - timedelta(days=10), 'value': 58},
                {'timestamp': datetime.now() - timedelta(days=5), 'value': 63},
                {'timestamp': datetime.now(), 'value': 68},
            ]
        }
        
        # Act
        result = predictor.predict(device_id='test_device', features=mock_telemetry)
        
        # Assert
        assert isinstance(result, PredictionResult)
        assert result.prediction_type == "anomaly_detection"
        assert result.device_id == "test_device"
        assert 0 <= result.predicted_value <= 1
        
        # Check that the result contains anomaly detections
        assert "detected_anomalies" in result.raw_details
        assert len(result.raw_details["detected_anomalies"]) > 0
        
        # Verify recommended actions
        assert len(result.recommended_actions) > 0
        action = result.recommended_actions[0]
        assert isinstance(action, RecommendedAction)
        assert "anomaly" in action.description.lower() or "pattern" in action.description.lower()
    
    def test_temperature_trend_analysis(self):
        """Test that the predictor can detect temperature trends."""
        predictor = AnomalyDetectionPredictor()
        # Simulate rising temperature trend
        mock_telemetry = {
            'temperature_readings': [
                {'timestamp': datetime.now() - timedelta(days=30), 'value': 140},
                {'timestamp': datetime.now() - timedelta(days=25), 'value': 142},
                {'timestamp': datetime.now() - timedelta(days=20), 'value': 144},
                {'timestamp': datetime.now() - timedelta(days=15), 'value': 146},
                {'timestamp': datetime.now() - timedelta(days=10), 'value': 148},
                {'timestamp': datetime.now() - timedelta(days=5), 'value': 150},
                {'timestamp': datetime.now(), 'value': 152},
            ]
        }
        
        result = predictor.predict(device_id='test_device', features=mock_telemetry)
        
        # Verify trend detection
        assert "trend_analysis" in result.raw_details
        assert "temperature" in result.raw_details["trend_analysis"]
        assert "probability" in result.raw_details["trend_analysis"]["temperature"]
        assert "days_until_critical" in result.raw_details["trend_analysis"]["temperature"]
    
    def test_pressure_anomaly_detection(self):
        """Test that the predictor can detect pressure anomalies."""
        predictor = AnomalyDetectionPredictor()
        # Simulate pressure spike
        mock_telemetry = {
            'pressure_readings': [
                {'timestamp': datetime.now() - timedelta(days=30), 'value': 50},
                {'timestamp': datetime.now() - timedelta(days=25), 'value': 51},
                {'timestamp': datetime.now() - timedelta(days=20), 'value': 50},
                {'timestamp': datetime.now() - timedelta(days=15), 'value': 52},
                {'timestamp': datetime.now() - timedelta(days=10), 'value': 51},
                {'timestamp': datetime.now() - timedelta(days=5), 'value': 65},  # Spike
                {'timestamp': datetime.now(), 'value': 53},
            ]
        }
        
        result = predictor.predict(device_id='test_device', features=mock_telemetry)
        
        # Verify anomaly detection
        assert "detected_anomalies" in result.raw_details
        pressure_anomalies = [a for a in result.raw_details["detected_anomalies"] 
                             if a["measurement_type"] == "pressure"]
        assert len(pressure_anomalies) > 0
        assert "probability" in pressure_anomalies[0]


class TestUsagePatternPredictor:
    """Tests for the usage pattern prediction model."""
    
    def test_initialization(self):
        """Test that the usage pattern predictor can be initialized."""
        predictor = UsagePatternPredictor()
        assert predictor is not None
    
    def test_usage_pattern_prediction(self):
        """Test that usage pattern analysis generates predictions based on water usage."""
        # Arrange
        predictor = UsagePatternPredictor()
        mock_usage_data = {
            'daily_usage_liters': [
                {'date': datetime.now() - timedelta(days=30), 'value': 150},
                {'date': datetime.now() - timedelta(days=29), 'value': 160},
                {'date': datetime.now() - timedelta(days=28), 'value': 145},
                # Weekend pattern
                {'date': datetime.now() - timedelta(days=27), 'value': 200},
                {'date': datetime.now() - timedelta(days=26), 'value': 220},
                # Weekday pattern repeats
                {'date': datetime.now() - timedelta(days=25), 'value': 155},
                {'date': datetime.now() - timedelta(days=24), 'value': 165},
                {'date': datetime.now() - timedelta(days=23), 'value': 152},
                {'date': datetime.now() - timedelta(days=22), 'value': 148},
                {'date': datetime.now() - timedelta(days=21), 'value': 150},
                # Weekend pattern
                {'date': datetime.now() - timedelta(days=20), 'value': 210},
                {'date': datetime.now() - timedelta(days=19), 'value': 225},
            ],
            'heating_cycles_per_day': [
                {'date': datetime.now() - timedelta(days=30), 'value': 5},
                {'date': datetime.now() - timedelta(days=20), 'value': 6},
                {'date': datetime.now() - timedelta(days=10), 'value': 7},
                {'date': datetime.now() - timedelta(days=5), 'value': 8},
                {'date': datetime.now(), 'value': 9},
            ],
            'average_temperature_setting': 140,
            'installation_date': datetime.now() - timedelta(days=365)
        }
        
        # Act
        result = predictor.predict(device_id='test_device', features=mock_usage_data)
        
        # Assert
        assert isinstance(result, PredictionResult)
        assert result.prediction_type == "usage_pattern"
        assert result.device_id == "test_device"
        
        # Check that the result contains usage pattern analysis
        assert "usage_patterns" in result.raw_details
        assert "impact_on_components" in result.raw_details
        
        # Verify component impacts
        impact_data = result.raw_details["impact_on_components"]
        assert "heating_element" in impact_data
        assert "wear_acceleration_factor" in impact_data["heating_element"]
        
        # Verify recommended actions
        assert len(result.recommended_actions) > 0
        action = result.recommended_actions[0]
        assert isinstance(action, RecommendedAction)
        assert "usage" in action.description.lower() or "pattern" in action.description.lower()
    
    def test_heavy_usage_detection(self):
        """Test that the predictor can detect heavy usage patterns."""
        predictor = UsagePatternPredictor()
        # Simulate heavy usage pattern
        mock_usage_data = {
            'daily_usage_liters': [
                {'date': datetime.now() - timedelta(days=10), 'value': 250},
                {'date': datetime.now() - timedelta(days=9), 'value': 245},
                {'date': datetime.now() - timedelta(days=8), 'value': 260},
                {'date': datetime.now() - timedelta(days=7), 'value': 255},
                {'date': datetime.now() - timedelta(days=6), 'value': 265},
                {'date': datetime.now() - timedelta(days=5), 'value': 250},
                {'date': datetime.now() - timedelta(days=4), 'value': 270},
                {'date': datetime.now() - timedelta(days=3), 'value': 265},
                {'date': datetime.now() - timedelta(days=2), 'value': 255},
                {'date': datetime.now() - timedelta(days=1), 'value': 260},
            ],
            'heating_cycles_per_day': [
                {'date': datetime.now() - timedelta(days=10), 'value': 10},
                {'date': datetime.now() - timedelta(days=5), 'value': 12},
                {'date': datetime.now(), 'value': 13},
            ],
            'average_temperature_setting': 145,
            'installation_date': datetime.now() - timedelta(days=180)
        }
        
        result = predictor.predict(device_id='test_device', features=mock_usage_data)
        
        # Verify heavy usage detection
        assert "usage_classification" in result.raw_details
        assert result.raw_details["usage_classification"] == "heavy"
        
        # Verify wear acceleration is reported
        assert "impact_on_components" in result.raw_details
        assert "heating_element" in result.raw_details["impact_on_components"]
        assert result.raw_details["impact_on_components"]["heating_element"]["wear_acceleration_factor"] > 1.0


class TestMultiFactorPredictor:
    """Tests for the multi-factor prediction model."""
    
    def test_initialization(self):
        """Test that the multi-factor predictor can be initialized."""
        predictor = MultiFactorPredictor()
        assert predictor is not None
    
    def test_multi_factor_prediction(self):
        """Test that multi-factor analysis generates predictions from multiple data sources."""
        # Arrange
        predictor = MultiFactorPredictor()
        mock_features = {
            'water_hardness': 'high',  # Environmental factor
            'average_temperature_setting': 145,  # User setting
            'scale_buildup_mm': 2.3,  # Current condition
            'heating_element_efficiency': 0.85,  # Component state
            'diagnostic_codes': ['W012', 'W045'],  # Diagnostic data
            'heating_cycles_per_day': 8,  # Usage pattern
            'installation_date': datetime.now() - timedelta(days=730),  # Age
            'tank_pressure_kpa': 420,  # Current reading
            'last_maintenance_date': datetime.now() - timedelta(days=180)  # Maintenance history
        }
        
        # Act
        result = predictor.predict(device_id='test_device', features=mock_features)
        
        # Assert
        assert isinstance(result, PredictionResult)
        assert result.prediction_type == "multi_factor"
        assert result.device_id == "test_device"
        
        # Check that the result contains multi-factor analysis
        assert "combined_factors" in result.raw_details
        assert "component_interactions" in result.raw_details
        assert "environmental_impact" in result.raw_details
        
        # Verify scale buildup prediction
        assert "scale_buildup" in result.raw_details["environmental_impact"]
        assert "days_until_critical" in result.raw_details["environmental_impact"]["scale_buildup"]
        
        # Verify diagnostic projection
        assert "diagnostic_progression" in result.raw_details
        assert "current_severity" in result.raw_details["diagnostic_progression"]
        assert "projected_severity" in result.raw_details["diagnostic_progression"]
        assert "days_until_escalation" in result.raw_details["diagnostic_progression"]
        
        # Verify recommended actions
        assert len(result.recommended_actions) > 0
        action = result.recommended_actions[0]
        assert isinstance(action, RecommendedAction)
    
    def test_environmental_impact_modeling(self):
        """Test that the predictor can model environmental impacts on the water heater."""
        predictor = MultiFactorPredictor()
        # Simulate hard water conditions and high temperature
        mock_features = {
            'water_hardness': 'very_high',
            'average_temperature_setting': 155,
            'scale_buildup_mm': 1.8,
            'installation_date': datetime.now() - timedelta(days=365),
            'last_maintenance_date': datetime.now() - timedelta(days=90)
        }
        
        result = predictor.predict(device_id='test_device', features=mock_features)
        
        # Verify environmental impact modeling
        assert "environmental_impact" in result.raw_details
        assert "scale_buildup" in result.raw_details["environmental_impact"]
        assert result.raw_details["environmental_impact"]["scale_buildup"]["days_until_critical"] < 60  # Should predict rapid scaling
    
    def test_component_interaction_predictions(self):
        """Test that the predictor can predict component interactions."""
        predictor = MultiFactorPredictor()
        # Simulate thermostat inefficiency affecting heating element
        mock_features = {
            'thermostat_efficiency': 0.75,  # Inefficient thermostat
            'heating_element_efficiency': 0.92,  # Currently good heating element
            'heating_cycles_per_day': 9,
            'tank_pressure_kpa': 410,
            'average_temperature_setting': 140,
            'installation_date': datetime.now() - timedelta(days=730)
        }
        
        result = predictor.predict(device_id='test_device', features=mock_features)
        
        # Verify component interaction predictions
        assert "component_interactions" in result.raw_details
        assert "thermostat_heating_element" in result.raw_details["component_interactions"]
        interaction = result.raw_details["component_interactions"]["thermostat_heating_element"]
        assert "stress_increase_percent" in interaction
        assert interaction["stress_increase_percent"] > 0  # Should predict increased stress
        assert "days_until_impact" in interaction
