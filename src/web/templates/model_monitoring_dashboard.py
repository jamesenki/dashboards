"""
Model Monitoring Dashboard UI Component.

This module provides a dashboard for visualizing model performance metrics,
alerts, and drift detection.
"""
import json
from typing import Any, Dict, List, Optional


class ModelMonitoringDashboard:
    """
    UI component for displaying model performance metrics and monitoring.

    This dashboard shows model metrics, drift detection, and alert information
    in a user-friendly format with visualizations.
    """

    def __init__(self, monitoring_service=None):
        """
        Initialize the dashboard with the model monitoring service.

        Args:
            monitoring_service: Service for accessing model monitoring data
        """
        self.title = "Model Monitoring Dashboard"
        self.monitoring_service = monitoring_service
        self.models = []
        self.metrics = {}

        if monitoring_service:
            try:
                self.models = monitoring_service.get_monitored_models()
                # If models exist, get metrics for the first model's latest version
                if self.models and len(self.models) > 0:
                    model = self.models[0]
                    model_id = model.get("id")
                    model_version = model.get("versions", ["latest"])[0]
                    self.metrics = monitoring_service.get_latest_metrics(
                        model_id, model_version
                    )
            except Exception as e:
                print(f"Error fetching model data: {e}")

    def render(self) -> str:
        """
        Render the dashboard as HTML.

        Returns:
            HTML representation of the dashboard
        """
        html = f"""
        <div class="monitoring-dashboard">
            <h1>{self.title}</h1>

            <div class="dashboard-grid">
                <div class="dashboard-card models-list">
                    <h2>Monitored Models</h2>
                    <div class="models-container">
                        {self._render_models_list()}
                    </div>
                </div>

                <div class="dashboard-card metrics-card">
                    <h2>Latest Metrics</h2>
                    <div class="metrics-container">
                        {self._render_metrics()}
                    </div>
                </div>

                <div class="dashboard-card alerts-card">
                    <h2>Recent Alerts</h2>
                    <div class="alerts-container">
                        {self._render_alerts()}
                    </div>
                </div>

                <div class="dashboard-card drift-card">
                    <h2>Model Drift</h2>
                    <div class="drift-container">
                        {self._render_drift()}
                    </div>
                </div>
            </div>
        </div>
        """
        return html

    def _render_models_list(self) -> str:
        """Render the list of monitored models."""
        if not self.models or len(self.models) == 0:
            return "<p>No models currently being monitored.</p>"

        html = "<ul class='model-list'>"
        for model in self.models:
            model_id = model.get("id", "unknown")
            model_name = model.get("name", model_id)
            versions = model.get("versions", [])

            html += f"""
            <li class="model-item" data-model-id="{model_id}">
                <div class="model-name">{model_name}</div>
                <div class="model-versions">
                    <select class="version-select">
            """

            for version in versions:
                html += f'<option value="{version}">{version}</option>'

            html += """
                    </select>
                </div>
            </li>
            """

        html += "</ul>"
        return html

    def _render_metrics(self) -> str:
        """Render the metrics visualization."""
        if not self.metrics or len(self.metrics) == 0:
            return "<p>No metrics available for this model.</p>"

        html = "<div class='metrics-grid'>"
        for metric_name, metric_value in self.metrics.items():
            value_formatted = (
                f"{metric_value:.2f}"
                if isinstance(metric_value, float)
                else metric_value
            )
            html += f"""
            <div class="metric-item">
                <div class="metric-name">{metric_name}</div>
                <div class="metric-value">{value_formatted}</div>
            </div>
            """

        html += "</div>"
        return html

    def _render_alerts(self) -> str:
        """Render the alerts section."""
        return """
        <p>No recent alerts.</p>
        <button class="btn btn-primary">Configure Alerts</button>
        """

    def _render_drift(self) -> str:
        """Render the model drift visualization."""
        return """
        <p>No drift detected in the past 30 days.</p>
        <div class="drift-chart-placeholder">
            <img src="/static/assets/images/placeholder-chart.svg" alt="Drift Chart Placeholder">
        </div>
        """
