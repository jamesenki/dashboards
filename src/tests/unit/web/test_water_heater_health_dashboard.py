"""
Tests for the combined Water Heater Health Dashboard component.

This dashboard will display both the Component Failure Prediction and
Lifespan Estimation in a unified view.
"""
import pytest
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from src.predictions.interfaces import PredictionResult, RecommendedAction, ActionSeverity
from src.web.templates.water_heater_health_dashboard import WaterHeaterHealthDashboard


class TestWaterHeaterHealthDashboard:
    """Test suite for water heater health dashboard UI component."""
    
    @pytest.fixture
    def sample_component_failure_prediction(self):
        """Create sample component failure prediction data for testing."""
        return PredictionResult(
            prediction_type="component_failure",
            device_id="wh-123456",
            predicted_value=0.65,  # 65% overall failure probability
            confidence=0.85,
            features_used=["temperature", "pressure", "energy_usage", "diagnostic_codes"],
            timestamp=datetime.now(),
            recommended_actions=[
                RecommendedAction(
                    action_id="wh-123456-heating-element-80",
                    description="Inspect heating element for signs of failure",
                    severity=ActionSeverity.HIGH,
                    impact="Water heater may fail to heat water properly if not addressed",
                    expected_benefit="Prevent unexpected downtime and costly emergency repairs",
                    due_date=datetime.now() + timedelta(days=7),
                    estimated_cost=75.0,
                    estimated_duration="1-2 hours"
                )
            ],
            raw_details={
                "components": {
                    "heating_element": 0.8,
                    "thermostat": 0.4,
                    "pressure_valve": 0.6,
                    "anode_rod": 0.3,
                    "tank_integrity": 0.2
                },
                "heater_type": "COMMERCIAL"
            }
        )
    
    @pytest.fixture
    def sample_lifespan_prediction(self):
        """Create sample lifespan estimation prediction data for testing."""
        return PredictionResult(
            prediction_type="lifespan_estimation",
            device_id="wh-123456",
            predicted_value=0.75,  # 75% remaining lifespan
            confidence=0.90,
            features_used=["installation_date", "water_hardness", "temperature_setting", "usage_intensity"],
            timestamp=datetime.now(),
            recommended_actions=[
                RecommendedAction(
                    action_id="wh-123456-anode-rod-check",
                    description="Inspect and potentially replace anode rod",
                    severity=ActionSeverity.MEDIUM,
                    impact="Extend tank lifespan by preventing internal corrosion",
                    expected_benefit="Add 2-3 years to tank life expectancy",
                    due_date=datetime.now() + timedelta(days=30),
                    estimated_cost=60.0,
                    estimated_duration="1 hour"
                )
            ],
            raw_details={
                "current_age_years": 2.5,
                "total_expected_lifespan_years": 10.0,
                "estimated_end_of_life_date": (datetime.now() + timedelta(days=365*7.5)).isoformat(),
                "factors_affecting_lifespan": [
                    "Water temperature: Higher temperatures reduce lifespan",
                    "Water hardness: Hard water reduces lifespan due to scale buildup",
                    "Maintenance frequency: Regular maintenance extends lifespan"
                ]
            }
        )
    
    def test_dashboard_rendering(self, sample_component_failure_prediction, sample_lifespan_prediction):
        """Test that the dashboard renders correctly with both prediction types."""
        dashboard = WaterHeaterHealthDashboard(
            device_id="wh-123456",
            device_name="Test Water Heater",
            component_failure_prediction=sample_component_failure_prediction,
            lifespan_prediction=sample_lifespan_prediction
        )
        html = dashboard.render()
        
        # Parse HTML for testing
        soup = BeautifulSoup(html, 'html.parser')
        
        # Test basic structure
        assert soup.select('.water-heater-health-dashboard')
        
        # Test that both prediction components are present
        assert soup.select('.component-failure-prediction-card')
        assert soup.select('.lifespan-estimation-card')
        
        # Test component failure specific elements
        assert soup.select('.component-health-details')
        
        # Test lifespan specific elements
        assert soup.select('.remaining-lifespan-indicator')
        assert soup.select('.expected-end-of-life')
        assert soup.select('.lifespan-factors')
    
    def test_time_to_failure_predictions(self, sample_component_failure_prediction, sample_lifespan_prediction):
        """Test that time-to-failure predictions are displayed correctly."""
        dashboard = WaterHeaterHealthDashboard(
            device_id="wh-123456",
            device_name="Test Water Heater",
            component_failure_prediction=sample_component_failure_prediction,
            lifespan_prediction=sample_lifespan_prediction
        )
        html = dashboard.render()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check that component lifespan timeline is displayed
        timeline_element = soup.select_one('.component-lifespan-timeline')
        assert timeline_element
        
        # Check component failure dates are displayed
        failure_date_elements = soup.select('.component-failure-date')
        assert failure_date_elements
        
        # Verify we have time-based projection elements
        assert soup.select('.time-to-failure')
        assert "days until" in html
    
    def test_combined_recommendations(self, sample_component_failure_prediction, sample_lifespan_prediction):
        """Test that recommendations from both predictions are combined and prioritized."""
        dashboard = WaterHeaterHealthDashboard(
            device_id="wh-123456",
            device_name="Test Water Heater",
            component_failure_prediction=sample_component_failure_prediction,
            lifespan_prediction=sample_lifespan_prediction
        )
        html = dashboard.render()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check combined recommendations section exists
        recommendations_section = soup.select_one('.combined-recommendations')
        assert recommendations_section
        
        # Should have both types of recommendations
        action_items = soup.select('.action-item')
        assert len(action_items) >= 2  # At least one from each prediction
        
        # Check for prioritization indication
        assert soup.select('.priority-indicator')
    
    def test_empty_predictions(self):
        """Test that the dashboard handles empty prediction data gracefully."""
        dashboard = WaterHeaterHealthDashboard(
            device_id="wh-empty",
            device_name="Empty Test Water Heater",
            component_failure_prediction=None,
            lifespan_prediction=None
        )
        html = dashboard.render()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Should still render basic structure
        assert soup.select('.water-heater-health-dashboard')
        
        # Should show messages about no predictions
        no_data_elements = soup.select('.no-prediction-data')
        assert len(no_data_elements) >= 2  # One for each prediction type
    
    def test_interactive_elements(self, sample_component_failure_prediction, sample_lifespan_prediction):
        """Test that the dashboard includes interactive elements."""
        dashboard = WaterHeaterHealthDashboard(
            device_id="wh-123456",
            device_name="Test Water Heater",
            component_failure_prediction=sample_component_failure_prediction,
            lifespan_prediction=sample_lifespan_prediction
        )
        html = dashboard.render()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Should have tabs or toggles for different views
        assert soup.select('.dashboard-tabs') or soup.select('.dashboard-toggle')
        
        # Should have at least one interactive element
        assert soup.select('button') or soup.select('select') or soup.select('input')
