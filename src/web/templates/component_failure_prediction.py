"""
Component Failure Prediction UI component.

This module provides the HTML component for displaying component failure prediction results
for water heaters, including health indicators and recommended actions.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.predictions.interfaces import ActionSeverity, PredictionResult


class ComponentFailurePredictionComponent:
    """UI component for displaying component failure prediction results."""

    def __init__(self, prediction_data: PredictionResult):
        """
        Initialize the component with prediction data.

        Args:
            prediction_data: The component failure prediction result
        """
        self.prediction = prediction_data
        self.component_order = [
            "heating_element",
            "thermostat",
            "pressure_valve",
            "anode_rod",
            "tank_integrity",
        ]
        self.component_labels = {
            "heating_element": "Heating Element",
            "thermostat": "Thermostat",
            "pressure_valve": "Pressure Valve",
            "anode_rod": "Anode Rod",
            "tank_integrity": "Tank Integrity",
        }

    def render(self) -> str:
        """
        Render the component failure prediction component as HTML.

        Returns:
            HTML string representation of the component
        """
        has_prediction_data = (
            self.prediction.raw_details
            and "components" in self.prediction.raw_details
            and len(self.prediction.raw_details["components"]) > 0
        )

        html = f"""
        <div class="component-failure-prediction-card card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="card-title mb-0">
                    <i class="fas fa-tools me-2"></i>Component Health
                </h5>
                <div class="health-indicator {self._get_health_indicator_class()}">
                    {self._format_probability(self.prediction.predicted_value)}
                </div>
            </div>
            <div class="card-body">
        """

        if has_prediction_data:
            # Display overall probability
            html += f"""
                <div class="overall-health mb-4">
                    <h6>Overall Component Health</h6>
                    <div class="d-flex align-items-center">
                        <div class="progress flex-grow-1" style="height: 15px;">
                            <div class="progress-bar {self._get_progress_bar_class()}"
                                 role="progressbar"
                                 style="width: {self.prediction.predicted_value * 100}%"
                                 aria-valuenow="{self.prediction.predicted_value * 100}"
                                 aria-valuemin="0"
                                 aria-valuemax="100"></div>
                        </div>
                        <span class="ms-2 overall-probability">
                            {self._format_probability(self.prediction.predicted_value)}
                        </span>
                    </div>
                    <div class="text-muted small mt-1">
                        <span class="me-2">Confidence: {self._format_probability(self.prediction.confidence)}</span>
                        <span class="text-nowrap">
                            <i class="far fa-calendar-alt me-1"></i>
                            {self.prediction.timestamp.strftime('%Y-%m-%d')}
                        </span>
                    </div>
                </div>

                <h6 class="mt-4">Component Health Details</h6>
                <div class="component-health-details">
            """

            # Display individual component probabilities
            components = self.prediction.raw_details.get("components", {})

            # Sort components by failure probability (highest first)
            sorted_components = sorted(
                [
                    (comp, prob)
                    for comp, prob in components.items()
                    if comp in self.component_order
                ],
                key=lambda x: x[1],
                reverse=True,
            )

            for component, probability in sorted_components:
                label = self.component_labels.get(
                    component, component.replace("_", " ").title()
                )
                progress_class = self._get_progress_bar_class(probability)

                html += f"""
                    <div class="component-item mb-3">
                        <div class="d-flex justify-content-between mb-1">
                            <span>{label}</span>
                            <span class="probability-value">{self._format_probability(probability)}</span>
                        </div>
                        <div class="progress" style="height: 10px;">
                            <div class="progress-bar {progress_class}"
                                 role="progressbar"
                                 style="width: {probability * 100}%"
                                 aria-valuenow="{probability * 100}"
                                 aria-valuemin="0"
                                 aria-valuemax="100"></div>
                        </div>
                    </div>
                """

            html += "</div>"  # Close component-health-details

            # Display recommended actions if any
            if self.prediction.recommended_actions:
                html += """
                <h6 class="mt-4">Recommended Actions</h6>
                <div class="recommended-actions">
                """

                for action in self.prediction.recommended_actions:
                    severity_class = f"{action.severity.value}-severity"
                    due_date = action.due_date.strftime("%Y-%m-%d")

                    html += f"""
                    <div class="action-item card mb-2 {severity_class}">
                        <div class="card-body py-2">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <div class="action-description">{action.description}</div>
                                    <div class="action-details text-muted small">
                                        <span class="me-2">Impact: {action.impact}</span>
                                    </div>
                                </div>
                                <div class="text-end">
                                    <div class="action-severity badge bg-{self._get_severity_badge_color(action.severity)}">
                                        {action.severity.value.upper()}
                                    </div>
                                    <div class="action-due-date text-muted small">
                                        <i class="far fa-calendar-alt me-1"></i>Due: {due_date}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """

                html += "</div>"  # Close recommended-actions
        else:
            # Display a message when no prediction data is available
            html += """
                <div class="no-prediction-data text-center py-4">
                    <i class="fas fa-exclamation-circle fa-3x mb-3 text-muted"></i>
                    <p>No component failure prediction data available</p>
                </div>
            """

        html += """
            </div>
        </div>
        """

        return html

    def _format_probability(self, value: float) -> str:
        """Format probability as percentage."""
        return f"{int(value * 100)}%"

    def _get_health_indicator_class(self) -> str:
        """Get CSS class for the health indicator based on prediction value."""
        value = self.prediction.predicted_value

        if value >= 0.7:
            return "critical"
        elif value >= 0.4:
            return "warning"
        else:
            return "healthy"

    def _get_progress_bar_class(self, value: Optional[float] = None) -> str:
        """Get CSS class for progress bar based on prediction value."""
        if value is None:
            value = self.prediction.predicted_value

        if value >= 0.7:
            return "bg-danger"
        elif value >= 0.4:
            return "bg-warning"
        else:
            return "bg-success"

    def _get_severity_badge_color(self, severity: ActionSeverity) -> str:
        """Get bootstrap color for severity badge."""
        if severity == ActionSeverity.CRITICAL:
            return "danger"
        elif severity == ActionSeverity.HIGH:
            return "danger"
        elif severity == ActionSeverity.MEDIUM:
            return "warning"
        else:
            return "info"
