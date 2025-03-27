"""
Unit tests for advanced water heater prediction models.

Tests the implementation of anomaly detection, usage pattern analysis,
and multi-factor prediction models.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import copy

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
    """Test suite for the UsagePatternPredictor class."""
    
    def setup_method(self):
        """Set up test data."""
        self.device_id = "wh-test-123"
        self.predictor = UsagePatternPredictor()
        
        # Sample test features
        self.test_features = {
            "system_age": {"years": 3, "months": 2},
            "temperature_setting": 130,
            "heating_cycles_per_day": 8,
            "daily_usage_liters": [
                {"date": "2024-12-28", "value": 165},
                {"date": "2024-12-29", "value": 170},
                {"date": "2024-12-30", "value": 185},
                {"date": "2024-12-31", "value": 155},
                {"date": "2025-01-01", "value": 210},
                {"date": "2025-01-02", "value": 126}
            ],
            "usage_history": [
                {"date": "2024-12-28", "value": 165},
                {"date": "2024-12-29", "value": 170},
                {"date": "2024-12-30", "value": 185},
                {"date": "2024-12-31", "value": 155},
                {"date": "2025-01-01", "value": 210},
                {"date": "2025-01-02", "value": 126}
            ]
        }
    
    @pytest.mark.asyncio
    async def test_usage_pattern_prediction(self):
        """Test basic usage pattern prediction functionality."""
        # Generate prediction
        result = await self.predictor.predict(self.device_id, self.test_features)
        
        # Verify basic properties
        assert isinstance(result, PredictionResult)
        assert result.device_id == self.device_id
        assert result.prediction_type == "usage_patterns"
        assert result.predicted_value >= 0.0
        assert result.confidence > 0.0
        
        # Check raw details
        assert "usage_classification" in result.raw_details
        assert "impact_on_components" in result.raw_details
        
        # Check that we have recommendations
        assert len(result.recommended_actions) > 0
    
    @pytest.mark.asyncio
    async def test_heavy_usage_detection(self):
        """Test that heavy usage patterns are properly detected."""
        # Create features with heavy usage
        heavy_usage_features = copy.deepcopy(self.test_features)
        # Override with heavy usage data
        heavy_usage_features["daily_usage_liters"] = [
            {"date": "2024-12-28", "value": 280},
            {"date": "2024-12-29", "value": 290},
            {"date": "2024-12-30", "value": 310},
            {"date": "2024-12-31", "value": 295},
            {"date": "2025-01-01", "value": 320},
            {"date": "2025-01-02", "value": 305}
        ]
        heavy_usage_features["heating_cycles_per_day"] = 12  # Frequent cycles
        
        # Generate prediction
        result = await self.predictor.predict(self.device_id, heavy_usage_features)
        
        # Usage should be classified as "heavy"
        assert "usage_classification" in result.raw_details
        assert result.raw_details["usage_classification"] == "heavy"
        
        # Impact on components should reflect heavy usage with higher wear factors
        assert "impact_on_components" in result.raw_details
        for component, impact in result.raw_details["impact_on_components"].items():
            assert "wear_acceleration_factor" in impact
            assert impact["wear_acceleration_factor"] > 1.0


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
