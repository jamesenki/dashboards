"""
Water Heater Health Dashboard UI Component.

This module provides a unified dashboard displaying both component failure prediction
and lifespan estimation in a single, integrated view with predictive elements.
"""
import datetime
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.predictions.interfaces import (
    ActionSeverity,
    PredictionResult,
    RecommendedAction,
)
from src.web.templates.component_failure_prediction import (
    ComponentFailurePredictionComponent,
)


class WaterHeaterHealthDashboard:
    """
    UI component for displaying comprehensive water heater health predictions.

    This dashboard combines component failure prediction and lifespan estimation
    into a unified view with time-to-failure predictions, maintenance timelines,
    and prioritized recommendations.
    """

    def __init__(
        self,
        device_id: str,
        device_name: str,
        component_failure_prediction: Optional[PredictionResult] = None,
        lifespan_prediction: Optional[PredictionResult] = None,
    ):
        """
        Initialize the dashboard with prediction data.

        Args:
            device_id: Identifier for the water heater
            device_name: Display name for the water heater
            component_failure_prediction: Component failure prediction result
            lifespan_prediction: Lifespan estimation prediction result
        """
        self.device_id = device_id
        self.device_name = device_name
        self.component_failure_prediction = component_failure_prediction
        self.lifespan_prediction = lifespan_prediction

        # Component display names for better readability
        self.component_labels = {
            "heating_element": "Heating Element",
            "thermostat": "Thermostat",
            "pressure_valve": "Pressure Valve",
            "anode_rod": "Anode Rod",
            "tank_integrity": "Tank Integrity",
        }

        # Calculate time-to-failure for components (when component_failure_prediction is available)
        self.time_to_failure = self._calculate_time_to_failure()

        # Combine and prioritize recommendations from both predictions
        self.combined_recommendations = self._combine_recommendations()

    def render(self) -> str:
        """
        Render the water heater health dashboard as HTML.

        Returns:
            HTML string representation of the dashboard
        """
        # Use template strings to create HTML sections
        header = f"""
        <div class="water-heater-health-dashboard">
            <div class="dashboard-header mb-4">
                <h2 class="dashboard-title">{self.device_name}</h2>
                <div class="dashboard-subtitle text-muted">ID: {self.device_id}</div>

                <div class="dashboard-tabs mt-3">
                    <button class="tab-button active" onclick="switchTab('overview')">Overview</button>
                    <button class="tab-button" onclick="switchTab('details')">Detailed Projections</button>
                    <button class="tab-button" onclick="switchTab('recommendations')">Recommendations</button>
                </div>
            </div>
        """

        content = f"""
            <div class="dashboard-content">
                <div class="tab-pane active" id="overview">
                    <div class="row">
                        <div class="col-md-6">
                            {self._render_lifespan_overview()}
                        </div>
                        <div class="col-md-6">
                            {self._render_component_health_overview()}
                        </div>
                    </div>
                </div>

                <div class="tab-pane" id="details">
                    <div class="row">
                        <div class="col-md-12">
                            {self._render_time_to_failure_predictions()}
                        </div>
                    </div>
                </div>

                <div class="tab-pane" id="recommendations">
                    <div class="row">
                        <div class="col-md-12">
                            {self._render_combined_recommendations()}
                        </div>
                    </div>
                </div>
            </div>
        </div>"""

        # CSS styles as regular strings to avoid f-string escaping issues
        styles = """
        <style>
            .water-heater-health-dashboard {
                font-family: Arial, sans-serif;
                background-color: #f9f9f9;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            .dashboard-header {
                margin-bottom: 20px;
            }
            .dashboard-title {
                margin: 0;
                font-size: 24px;
            }
            .dashboard-subtitle {
                color: #6c757d;
                font-size: 14px;
            }
            .dashboard-tabs {
                display: flex;
                border-bottom: 1px solid #dee2e6;
                margin-top: 15px;
            }
            .tab-button {
                background: none;
                border: none;
                padding: 10px 15px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                color: #495057;
                border-bottom: 2px solid transparent;
            }
            .tab-button.active {
                color: #007bff;
                border-bottom-color: #007bff;
            }
            .tab-pane {
                display: none;
                padding: 15px 0;
            }
            .tab-pane.active {
                display: block;
            }
            .row {
                display: flex;
                flex-wrap: wrap;
                margin-right: -15px;
                margin-left: -15px;
            }
            .col-md-6, .col-md-12 {
                position: relative;
                width: 100%;
                padding-right: 15px;
                padding-left: 15px;
            }
            @media (min-width: 768px) {
                .col-md-6 {
                    flex: 0 0 50%;
                    max-width: 50%;
                }
                .col-md-12 {
                    flex: 0 0 100%;
                    max-width: 100%;
                }
            }
            .card {
                position: relative;
                display: flex;
                flex-direction: column;
                min-width: 0;
                word-wrap: break-word;
                background-color: #fff;
                background-clip: border-box;
                border: 1px solid rgba(0,0,0,.125);
                border-radius: 0.25rem;
                margin-bottom: 20px;
            }
            .card-header {
                padding: 0.75rem 1.25rem;
                margin-bottom: 0;
                background-color: rgba(0,0,0,.03);
                border-bottom: 1px solid rgba(0,0,0,.125);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .card-body {
                flex: 1 1 auto;
                padding: 1.25rem;
            }
            .text-muted {
                color: #6c757d;
            }
            .text-center {
                text-align: center;
            }
            .mb-4 {
                margin-bottom: 1.5rem;
            }
            .mt-3 {
                margin-top: 1rem;
            }
            .progress {
                display: flex;
                height: 16px;
                overflow: hidden;
                font-size: 0.75rem;
                background-color: #e9ecef;
                border-radius: 0.25rem;
                margin-bottom: 10px;
            }
            .progress-bar {
                display: flex;
                flex-direction: column;
                justify-content: center;
                color: #fff;
                text-align: center;
                white-space: nowrap;
                background-color: #007bff;
                transition: width 0.6s ease;
            }
            .bg-success { background-color: #28a745 !important; }
            .bg-warning { background-color: #ffc107 !important; }
            .bg-danger { background-color: #dc3545 !important; }
            .component-failure-date {
                border-left: 3px solid #dc3545;
                padding-left: 10px;
                margin-bottom: 10px;
            }
            .lifespan-estimation-card,
            .component-failure-prediction-card {
                height: 100%;
            }
            .priority-indicator {
                display: inline-block;
                width: 16px;
                height: 16px;
                border-radius: 50%;
                margin-right: 8px;
            }
            .priority-high { background-color: #dc3545; }
            .priority-medium { background-color: #ffc107; }
            .priority-low { background-color: #28a745; }
            .action-item {
                padding: 10px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-bottom: 10px;
            }
            .action-item.high-severity { border-left: 4px solid #dc3545; }
            .action-item.medium-severity { border-left: 4px solid #ffc107; }
            .action-item.low-severity { border-left: 4px solid #28a745; }
            .action-due-date {
                font-size: 0.85rem;
                color: #6c757d;
            }
            .remaining-lifespan-indicator {
                text-align: center;
                padding: 20px 0;
            }
            .lifespan-gauge {
                width: 150px;
                height: 150px;
                border-radius: 50%;
                background: conic-gradient(
                    var(--lifespan-color) var(--lifespan-percent),
                    #e9ecef var(--lifespan-percent)
                );
                position: relative;
                margin: 0 auto 20px;
            }
            .lifespan-gauge::after {
                content: "";
                position: absolute;
                top: 15px;
                left: 15px;
                right: 15px;
                bottom: 15px;
                border-radius: 50%;
                background: white;
            }
            .lifespan-gauge-text {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                z-index: 1;
                font-size: 24px;
                font-weight: bold;
            }
            .expected-end-of-life {
                margin-top: 10px;
                font-size: 0.9rem;
            }
            .timeline {
                position: relative;
                padding: 20px 0;
            }
            .timeline::before {
                content: "";
                position: absolute;
                top: 0;
                bottom: 0;
                left: 15px;
                width: 2px;
                background: #dee2e6;
            }
            .timeline-item {
                position: relative;
                padding-left: 40px;
                margin-bottom: 20px;
            }
            .timeline-dot {
                position: absolute;
                left: 9px;
                width: 14px;
                height: 14px;
                border-radius: 50%;
                background: #007bff;
            }
            .component-lifespan-timeline {
                margin-top: 20px;
            }
        </style>
        """

        # JavaScript for tab switching functionality
        script = f"""
        <script>
            function switchTab(tabId) {{
                // Hide all tab panes
                document.querySelectorAll('.tab-pane').forEach(pane => {{
                    pane.classList.remove('active');
                }});

                // Deactivate all tab buttons
                document.querySelectorAll('.tab-button').forEach(button => {{
                    button.classList.remove('active');
                }});

                // Show the selected tab pane
                document.getElementById(tabId).classList.add('active');

                // Activate the clicked tab button
                document.querySelector(`[onclick="switchTab('${{tabId}}')"]`).classList.add('active');
            }}
        </script>
        """

        # Combine all parts to create the full HTML
        html = header + content + styles + script

        return html

    def _render_lifespan_overview(self) -> str:
        """Render the lifespan estimation overview section."""
        if not self.lifespan_prediction:
            return """
            <div class="card lifespan-estimation-card">
                <div class="card-header">
                    <h5 class="card-title mb-0">Lifespan Estimation</h5>
                </div>
                <div class="card-body">
                    <div class="no-prediction-data text-center py-4">
                        <p>No lifespan prediction data available</p>
                    </div>
                </div>
            </div>
            """

        # Extract data from lifespan prediction
        remaining_percentage = self.lifespan_prediction.predicted_value
        remaining_years = 0
        end_of_life_date = datetime.now()

        if self.lifespan_prediction.raw_details:
            if "total_expected_lifespan_years" in self.lifespan_prediction.raw_details:
                remaining_years = (
                    remaining_percentage
                    * self.lifespan_prediction.raw_details[
                        "total_expected_lifespan_years"
                    ]
                )

            if "estimated_end_of_life_date" in self.lifespan_prediction.raw_details:
                try:
                    end_of_life_date = datetime.fromisoformat(
                        self.lifespan_prediction.raw_details[
                            "estimated_end_of_life_date"
                        ]
                    )
                except (ValueError, TypeError):
                    # If date parsing fails, calculate based on remaining percentage
                    end_of_life_date = datetime.now() + timedelta(
                        days=int(remaining_years * 365)
                    )

        # Determine lifespan color based on remaining percentage
        lifespan_color = "#28a745"  # green
        if remaining_percentage < 0.25:
            lifespan_color = "#dc3545"  # red
        elif remaining_percentage < 0.5:
            lifespan_color = "#ffc107"  # yellow

        lifespan_factors = []
        if (
            self.lifespan_prediction.raw_details
            and "factors_affecting_lifespan" in self.lifespan_prediction.raw_details
        ):
            lifespan_factors = self.lifespan_prediction.raw_details[
                "factors_affecting_lifespan"
            ]

        return f"""
        <div class="card lifespan-estimation-card">
            <div class="card-header">
                <h5 class="card-title mb-0">Lifespan Estimation</h5>
            </div>
            <div class="card-body">
                <div class="remaining-lifespan-indicator">
                    <div class="lifespan-gauge" style="--lifespan-percent: {remaining_percentage * 100}%; --lifespan-color: {lifespan_color};">
                        <div class="lifespan-gauge-text">{int(remaining_percentage * 100)}%</div>
                    </div>
                    <div class="remaining-lifespan-text">
                        <strong>Remaining Lifespan:</strong> {remaining_percentage:.0%}
                    </div>
                    <div class="expected-end-of-life text-muted">
                        <strong>Projected End of Life:</strong> {end_of_life_date.strftime('%Y-%m-%d')}
                        <div class="text-center mt-3">
                            <strong>Estimated {remaining_years:.1f} years remaining</strong>
                        </div>
                    </div>
                </div>

                <div class="lifespan-factors mt-3">
                    <h6>Factors Affecting Lifespan:</h6>
                    <ul>
                        {"".join([f"<li>{factor}</li>" for factor in lifespan_factors])}
                    </ul>
                </div>
            </div>
        </div>
        """

    def _render_component_health_overview(self) -> str:
        """Render the component health overview section."""
        if not self.component_failure_prediction:
            return """
            <div class="card component-failure-prediction-card">
                <div class="card-header">
                    <h5 class="card-title mb-0">Component Health</h5>
                </div>
                <div class="card-body">
                    <div class="no-prediction-data text-center py-4">
                        <p>No component health prediction data available</p>
                    </div>
                </div>
            </div>
            """

        # Use the existing ComponentFailurePredictionComponent for consistency
        component = ComponentFailurePredictionComponent(
            self.component_failure_prediction
        )
        return component.render()

    def _render_time_to_failure_predictions(self) -> str:
        """Render the time-to-failure predictions section with timeline."""
        if not self.time_to_failure:
            return """
            <div class="card">
                <div class="card-header">
                    <h5 class="card-title mb-0">Component Failure Timeline</h5>
                </div>
                <div class="card-body">
                    <div class="no-prediction-data text-center py-4">
                        <p>Insufficient data to generate component failure timeline</p>
                    </div>
                </div>
            </div>
            """

        # Sort components by expected failure date (earliest first)
        sorted_components = sorted(
            self.time_to_failure.items(), key=lambda x: x[1]["expected_failure_date"]
        )

        html = """
        <div class="card">
            <div class="card-header">
                <h5 class="card-title mb-0">Component Failure Timeline</h5>
            </div>
            <div class="card-body">
                <p class="text-muted">Projected timeline for component failures based on current condition and usage patterns:</p>

                <div class="component-lifespan-timeline timeline">
        """

        # Add timeline items for each component
        for component, failure_data in sorted_components:
            label = self.component_labels.get(
                component, component.replace("_", " ").title()
            )
            failure_date = failure_data["expected_failure_date"].strftime("%Y-%m-%d")
            days_until = failure_data["days_until_failure"]
            probability = failure_data["failure_probability"]

            # Determine color based on days until failure
            color_class = "bg-success"
            if days_until < 30:
                color_class = "bg-danger"
            elif days_until < 90:
                color_class = "bg-warning"

            html += f"""
                    <div class="timeline-item component-failure-date">
                        <div class="timeline-dot {color_class}"></div>
                        <div class="timeline-content">
                            <h6>{label}</h6>
                            <div class="time-to-failure">
                                <strong>Expected Failure:</strong> {failure_date}
                                <span class="text-muted">({days_until} days until failure)</span>
                            </div>
                            <div class="failure-probability text-muted">
                                Probability: {probability:.0%}
                            </div>
                        </div>
                    </div>
            """

        html += """
                </div>
            </div>
        </div>
        """

        return html

    def _render_combined_recommendations(self) -> str:
        """Render the combined and prioritized recommendations section."""
        if not self.combined_recommendations:
            return """
            <div class="card">
                <div class="card-header">
                    <h5 class="card-title mb-0">Maintenance Recommendations</h5>
                </div>
                <div class="card-body">
                    <div class="no-prediction-data text-center py-4">
                        <p>No maintenance recommendations available</p>
                    </div>
                </div>
            </div>
            """

        html = """
        <div class="card">
            <div class="card-header">
                <h5 class="card-title mb-0">Maintenance Recommendations</h5>
            </div>
            <div class="card-body">
                <p class="text-muted">Prioritized maintenance actions based on component health and lifespan projections:</p>

                <div class="combined-recommendations">
        """

        # Add each recommendation
        for i, action in enumerate(self.combined_recommendations):
            severity_class = f"{action.severity.value}-severity"
            priority_class = "high" if i < 3 else ("medium" if i < 6 else "low")
            due_date = (
                action.due_date.strftime("%Y-%m-%d")
                if action.due_date
                else "No date specified"
            )
            days_until_due = (
                (action.due_date - datetime.now()).days if action.due_date else 0
            )

            html += f"""
                    <div class="action-item {severity_class}">
                        <div class="action-header d-flex justify-content-between">
                            <div>
                                <span class="priority-indicator priority-{priority_class}"></span>
                                <strong>{action.description}</strong>
                            </div>
                            <div class="action-due-date">
                                Due: {due_date}
                                <span class="text-muted">({days_until_due} days)</span>
                            </div>
                        </div>
                        <div class="action-details mt-2">
                            <div class="impact text-muted">{action.impact}</div>
                            <div class="row mt-2">
                                <div class="col-md-6">
                                    <small class="text-muted">Estimated cost: ${action.estimated_cost or 'N/A'}</small>
                                </div>
                                <div class="col-md-6">
                                    <small class="text-muted">Duration: {action.estimated_duration or 'N/A'}</small>
                                </div>
                            </div>
                        </div>
                    </div>
            """

        html += """
                </div>
            </div>
        </div>
        """

        return html

    def _calculate_time_to_failure(self) -> Dict[str, Dict[str, Any]]:
        """
        Calculate projected time-to-failure for each component.

        Returns:
            Dictionary mapping component names to failure projection data
        """
        if (
            not self.component_failure_prediction
            or not self.component_failure_prediction.raw_details
        ):
            return {}

        # Get component probabilities
        components = self.component_failure_prediction.raw_details.get("components", {})
        if not components:
            return {}

        # Use lifespan information if available
        lifespan_details = {}
        if self.lifespan_prediction and self.lifespan_prediction.raw_details:
            lifespan_details = self.lifespan_prediction.raw_details

        total_expected_lifespan_years = lifespan_details.get(
            "total_expected_lifespan_years", 10
        )

        # Calculate time-to-failure for each component
        result = {}
        for component, failure_probability in components.items():
            # Calculate days until failure based on probability and lifespan
            # Higher probability = shorter time to failure
            relative_health = 1 - failure_probability

            # Base calculation on component type and expected lifespan
            component_max_years = total_expected_lifespan_years
            if component == "anode_rod":
                component_max_years = min(
                    total_expected_lifespan_years, 3
                )  # Typically 3-5 years
            elif component == "heating_element":
                component_max_years = min(
                    total_expected_lifespan_years, 5
                )  # Typically 4-6 years

            # Calculate days until projected failure
            days_until_failure = int(relative_health * component_max_years * 365)

            # Cap at maximum expected lifespan
            days_until_failure = min(days_until_failure, int(component_max_years * 365))

            # Calculate expected failure date
            expected_failure_date = datetime.now() + timedelta(days=days_until_failure)

            result[component] = {
                "failure_probability": failure_probability,
                "days_until_failure": days_until_failure,
                "expected_failure_date": expected_failure_date,
            }

        return result

    def _combine_recommendations(self) -> List[RecommendedAction]:
        """
        Combine and prioritize recommendations from both prediction types.

        Returns:
            Combined and prioritized list of recommended actions
        """
        all_actions = []

        # Add component failure recommendations
        if (
            self.component_failure_prediction
            and self.component_failure_prediction.recommended_actions
        ):
            all_actions.extend(self.component_failure_prediction.recommended_actions)

        # Add lifespan recommendations
        if self.lifespan_prediction and self.lifespan_prediction.recommended_actions:
            all_actions.extend(self.lifespan_prediction.recommended_actions)

        # Prioritize by severity, then by due date (if available)
        severity_order = {
            ActionSeverity.CRITICAL: 0,
            ActionSeverity.HIGH: 1,
            ActionSeverity.MEDIUM: 2,
            ActionSeverity.LOW: 3,
        }

        def priority_key(action):
            # First by severity
            severity_priority = severity_order.get(action.severity, 999)

            # Then by due date if available (sooner = higher priority)
            date_priority = (
                action.due_date.timestamp() if action.due_date else float("inf")
            )

            return (severity_priority, date_priority)

        return sorted(all_actions, key=priority_key)
