"""
Tests for the component failure prediction UI component.
"""
from datetime import datetime, timedelta

import pytest
from bs4 import BeautifulSoup

from src.predictions.interfaces import (
    ActionSeverity,
    PredictionResult,
    RecommendedAction,
)
from src.web.templates.component_failure_prediction import (
    ComponentFailurePredictionComponent,
)


class TestComponentFailurePredictionComponent:
    """Test suite for component failure prediction UI component."""

    @pytest.fixture
    def sample_prediction_data(self):
        """Create sample prediction data for testing."""
        # Create a realistic prediction result
        return PredictionResult(
            prediction_type="component_failure",
            device_id="wh-123456",
            predicted_value=0.65,  # 65% overall failure probability
            confidence=0.85,
            features_used=[
                "temperature",
                "pressure",
                "energy_usage",
                "diagnostic_codes",
            ],
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
                    estimated_duration="1-2 hours",
                ),
                RecommendedAction(
                    action_id="wh-123456-pressure-valve-60",
                    description="Test pressure relief valve operation",
                    severity=ActionSeverity.MEDIUM,
                    impact="Potential safety hazard from excessive pressure buildup",
                    expected_benefit="Prevent dangerous pressure conditions and ensure safety",
                    due_date=datetime.now() + timedelta(days=14),
                    estimated_cost=40.0,
                    estimated_duration="30 minutes",
                ),
            ],
            raw_details={
                "components": {
                    "heating_element": 0.8,
                    "thermostat": 0.4,
                    "pressure_valve": 0.6,
                    "anode_rod": 0.3,
                    "tank_integrity": 0.2,
                },
                "heater_type": "COMMERCIAL",
            },
        )

    def test_component_rendering(self, sample_prediction_data):
        """Test that the component renders correctly with sample data."""
        component = ComponentFailurePredictionComponent(sample_prediction_data)
        html = component.render()

        # Parse HTML for testing
        soup = BeautifulSoup(html, "html.parser")

        # Test basic structure
        assert soup.select(".component-failure-prediction-card")
        assert soup.select(".health-indicator")

        # Test overall probability display
        prob_element = soup.select_one(".overall-probability")
        assert prob_element
        assert "65%" in prob_element.text

        # Test components are displayed
        component_list = soup.select(".component-item")
        assert len(component_list) >= 5  # Should show all components

        # Test recommendations are displayed
        action_items = soup.select(".action-item")
        assert len(action_items) == 2

        # Verify high severity actions have correct styling
        high_severity_items = soup.select(".action-item.high-severity")
        assert len(high_severity_items) == 1

    def test_empty_prediction_data(self):
        """Test that the component handles empty prediction data gracefully."""
        empty_prediction = PredictionResult(
            prediction_type="component_failure",
            device_id="wh-empty",
            predicted_value=0.0,
            confidence=0.0,
            features_used=[],
            timestamp=datetime.now(),
            recommended_actions=[],
            raw_details={"components": {}},
        )

        component = ComponentFailurePredictionComponent(empty_prediction)
        html = component.render()

        # Parse HTML for testing
        soup = BeautifulSoup(html, "html.parser")

        # Should still render basic structure
        assert soup.select(".component-failure-prediction-card")

        # Should show a message about no predictions
        no_data_element = soup.select_one(".no-prediction-data")
        assert no_data_element
        assert "No component failure prediction data available" in no_data_element.text

    def test_health_indicator_color(self, sample_prediction_data):
        """Test that health indicator changes color based on probability."""
        # Test high probability (red)
        high_prob_prediction = sample_prediction_data.copy(
            update={"predicted_value": 0.8}
        )
        component = ComponentFailurePredictionComponent(high_prob_prediction)
        html = component.render()
        soup = BeautifulSoup(html, "html.parser")
        assert soup.select_one(".health-indicator.critical")

        # Test medium probability (yellow)
        med_prob_prediction = sample_prediction_data.copy(
            update={"predicted_value": 0.5}
        )
        component = ComponentFailurePredictionComponent(med_prob_prediction)
        html = component.render()
        soup = BeautifulSoup(html, "html.parser")
        assert soup.select_one(".health-indicator.warning")

        # Test low probability (green)
        low_prob_prediction = sample_prediction_data.copy(
            update={"predicted_value": 0.2}
        )
        component = ComponentFailurePredictionComponent(low_prob_prediction)
        html = component.render()
        soup = BeautifulSoup(html, "html.parser")
        assert soup.select_one(".health-indicator.healthy")
