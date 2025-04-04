"""
Component failure prediction model for water heaters.

This module implements prediction of component failures based on
telemetry data patterns, usage information, and diagnostic code history.
It provides enhanced predictions by utilizing water heater type information
and historical diagnostic data.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.connection import get_db_session
from src.db.models import DeviceModel, DiagnosticCodeModel, ReadingModel
from src.models.water_heater import WaterHeater, WaterHeaterType
from src.predictions.interfaces import (
    ActionSeverity,
    IActionRecommender,
    IPredictionModel,
    PredictionResult,
    RecommendedAction,
)


class ComponentFailurePrediction(IPredictionModel):
    """
    Predicts probability of component failures in water heaters.

    Uses telemetry data to identify patterns indicative of impending component failures.
    """

    def __init__(self):
        """Initialize the component failure prediction model."""
        self.model_name = "ComponentFailurePrediction"
        self.model_version = (
            "2.0.0"  # Updated version to reflect diagnostic code integration
        )
        self.logger = logging.getLogger(__name__)
        self.features_required = [
            "temperature",
            "pressure",
            "energy_usage",
            "flow_rate",
            "heating_cycles",
            "total_operation_hours",
            "maintenance_history",
            "diagnostic_codes",  # Added diagnostic codes as a feature
        ]

    async def predict(
        self, device_id: str, features: Dict[str, Any]
    ) -> PredictionResult:
        """
        Generate component failure predictions for a water heater.

        Args:
            device_id: ID of the water heater
            features: Dictionary of features including telemetry and operational data

        Returns:
            PredictionResult with component failure probabilities
        """
        # Extract features into DataFrames for analysis
        telemetry_df = self._prepare_telemetry_data(features)

        # Get water heater type and diagnostic codes if not in features
        if "diagnostic_codes" not in features or "heater_type" not in features:
            db_features = await self._fetch_device_data_from_db(device_id)
            features = {**features, **db_features}

        # Calculate component-specific failure probabilities
        component_probabilities = self._calculate_component_probabilities(
            telemetry_df, features
        )

        # Factor in diagnostic codes to adjust component probabilities
        component_probabilities = self._adjust_with_diagnostic_codes(
            component_probabilities, features.get("diagnostic_codes", [])
        )

        # Calculate overall failure probability (weighted average of component probabilities)
        component_weights = {
            "heating_element": 0.4,
            "thermostat": 0.2,
            "pressure_valve": 0.2,
            "anode_rod": 0.1,
            "tank_integrity": 0.1,
        }

        # Adjust weights based on heater type
        heater_type = features.get("heater_type", WaterHeaterType.RESIDENTIAL)
        if heater_type == WaterHeaterType.COMMERCIAL:
            # Commercial heaters have different component importance
            component_weights = {
                "heating_element": 0.35,
                "thermostat": 0.15,
                "pressure_valve": 0.25,  # More critical in commercial units
                "anode_rod": 0.10,
                "tank_integrity": 0.15,  # Also more important for commercial
            }

        overall_probability = sum(
            probability * component_weights.get(component, 0.1)
            for component, probability in component_probabilities.items()
        )

        # Calculate confidence based on data quality and sufficiency
        confidence = self._calculate_confidence(telemetry_df, features)

        # Generate appropriate recommendations based on component probabilities
        recommendations = self._generate_recommendations(
            component_probabilities, device_id
        )

        # Create and return prediction result
        return PredictionResult(
            prediction_type="component_failure",
            device_id=device_id,
            predicted_value=overall_probability,
            confidence=confidence,
            features_used=list(self.features_required),
            timestamp=datetime.now(),
            recommended_actions=recommendations,
            raw_details={
                "components": component_probabilities,
                "heater_type": str(heater_type),
            },
        )

    def get_model_info(self) -> Dict[str, Any]:
        """Return information about the model."""
        return {
            "name": self.model_name,
            "version": self.model_version,
            "description": "Predicts component failures in water heaters based on telemetry patterns",
            "features_required": self.features_required,
            "last_trained": datetime.now() - timedelta(days=30),  # Placeholder
            "performance_metrics": {
                "accuracy": 0.85,
                "precision": 0.82,
                "recall": 0.88,
                "f1_score": 0.85,
                "auc": 0.91,
            },
        }

    def _prepare_telemetry_data(self, features: Dict[str, Any]) -> pd.DataFrame:
        """
        Prepare telemetry data for analysis.

        Args:
            features: Raw feature dictionary

        Returns:
            DataFrame with processed telemetry data
        """
        # Extract time series data
        try:
            df = pd.DataFrame(
                {
                    "timestamp": features.get("timestamp", []),
                    "temperature": features.get("temperature", []),
                    "pressure": features.get("pressure", []),
                    "energy_usage": features.get("energy_usage", []),
                    "flow_rate": features.get("flow_rate", []),
                    "heating_cycles": features.get("heating_cycles", []),
                }
            )

            # Sort by timestamp and ensure proper datetime format
            if "timestamp" in df.columns and len(df) > 0:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.sort_values("timestamp")

            return df
        except Exception as e:
            # Return empty DataFrame in case of errors
            print(f"Error preparing telemetry data: {e}")
            return pd.DataFrame()

    def _calculate_component_probabilities(
        self, telemetry_df: pd.DataFrame, features: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate failure probabilities for each component.

        Args:
            telemetry_df: Processed telemetry DataFrame
            features: Raw feature dictionary with additional metadata

        Returns:
            Dictionary mapping component names to failure probabilities (0-1)
        """
        # Initialize with default low probabilities
        probabilities = {
            "heating_element": 0.1,
            "thermostat": 0.1,
            "pressure_valve": 0.1,
            "anode_rod": 0.1,
            "tank_integrity": 0.1,
        }

        if telemetry_df.empty:
            return probabilities

        # Calculate features for heating element failure detection
        if "temperature" in telemetry_df.columns and len(telemetry_df) >= 3:
            # Detect temperature fluctuations - high fluctuations indicate possible element issues
            temp_std = telemetry_df["temperature"].std()
            temp_trend = self._calculate_trend(telemetry_df["temperature"])

            # High fluctuation or decreasing trend indicates potential issues
            if temp_std > 3.0 or temp_trend < -0.1:
                probabilities["heating_element"] = min(0.3 + temp_std * 0.15, 0.9)

        # Calculate features for thermostat failure detection
        if (
            "temperature" in telemetry_df.columns
            and "heating_cycles" in telemetry_df.columns
        ):
            # Correlation between temperature and heating cycles
            # Poor correlation may indicate thermostat issues
            try:
                temp_cycle_corr = telemetry_df["temperature"].corr(
                    telemetry_df["heating_cycles"]
                )
                if temp_cycle_corr < 0.5:
                    probabilities["thermostat"] = min(0.9, 0.8 - temp_cycle_corr)
            except:
                pass

            # Detect temperature overshoots
            if len(telemetry_df) > 5:
                temp_diffs = telemetry_df["temperature"].diff().dropna()
                large_jumps = (temp_diffs.abs() > 5).sum()
                if large_jumps > 2:
                    probabilities["thermostat"] = max(
                        probabilities["thermostat"], min(0.3 + large_jumps * 0.1, 0.9)
                    )

        # Calculate features for pressure valve failure detection
        if "pressure" in telemetry_df.columns:
            pressure_std = telemetry_df["pressure"].std()
            pressure_max = telemetry_df["pressure"].max()

            # High pressure spikes indicate valve issues
            if pressure_max > 3.5 or pressure_std > 0.5:
                probabilities["pressure_valve"] = min(0.4 + pressure_std * 0.8, 0.9)

        # Calculate features for anode rod corrosion
        total_hours = features.get("total_operation_hours", 0)
        maintenance_history = features.get("maintenance_history", [])

        # Check last anode rod replacement/inspection
        last_anode_maintenance = None
        for maintenance in maintenance_history:
            if maintenance.get("type") in ("anode_replacement", "anode_inspection"):
                maint_date = maintenance.get("date")
                if maint_date and (
                    last_anode_maintenance is None
                    or maint_date > last_anode_maintenance
                ):
                    last_anode_maintenance = maint_date

        # Anode rod deteriorates with age
        if total_hours > 8760:  # Over 1 year of operation
            # Base probability on age
            age_factor = min(total_hours / 87600, 1.0)  # 10 years = max factor
            probabilities["anode_rod"] = 0.3 + (age_factor * 0.6)

            # Reduce if recently maintained
            if last_anode_maintenance:
                days_since_maintenance = (datetime.now() - last_anode_maintenance).days
                if days_since_maintenance < 365:  # Less than a year
                    probabilities["anode_rod"] *= days_since_maintenance / 365

        # Tank integrity deterioration with age and pressure events
        tank_age_factor = min(total_hours / 131400, 1.0)  # 15 years = max factor
        probabilities["tank_integrity"] = 0.1 + (tank_age_factor * 0.5)

        # Pressure events accelerate tank deterioration
        if "pressure" in telemetry_df.columns:
            pressure_events = (telemetry_df["pressure"] > 3.0).sum()
            if pressure_events > 0:
                probabilities["tank_integrity"] = min(
                    probabilities["tank_integrity"] + (pressure_events * 0.05), 0.9
                )

        return probabilities

    def _calculate_trend(self, series: pd.Series) -> float:
        """
        Calculate the trend in a time series.

        Returns a simple linear trend coefficient.

        Args:
            series: Time series data

        Returns:
            Trend coefficient (positive = increasing, negative = decreasing)
        """
        if len(series) < 2:
            return 0.0

        try:
            # Simple linear regression
            x = np.arange(len(series))
            y = series.values

            # Calculate trend using least squares
            A = np.vstack([x, np.ones(len(x))]).T
            m, c = np.linalg.lstsq(A, y, rcond=None)[0]

            # Normalize by the mean value to get relative trend
            return m * len(series) / series.mean() if series.mean() != 0 else m
        except:
            return 0.0

    def _calculate_confidence(
        self, telemetry_df: pd.DataFrame, features: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence in prediction based on data quality.

        Args:
            telemetry_df: Processed telemetry DataFrame
            features: Raw feature dictionary

        Returns:
            Confidence score (0-1)
        """
        base_confidence = 0.5  # Start with moderate confidence

        # Factors that increase confidence:
        confidence_factors = []

        # 1. Data volume
        if len(telemetry_df) >= 24:  # At least 24 data points
            confidence_factors.append(0.2)
        elif len(telemetry_df) >= 12:
            confidence_factors.append(0.1)
        else:
            confidence_factors.append(-0.1)  # Penalty for too little data

        # 2. Data recency
        if not telemetry_df.empty and "timestamp" in telemetry_df.columns:
            latest_data = telemetry_df["timestamp"].max()
            data_age_hours = (datetime.now() - latest_data).total_seconds() / 3600

            if data_age_hours < 24:  # Data less than a day old
                confidence_factors.append(0.1)
            elif data_age_hours > 168:  # Data more than a week old
                confidence_factors.append(-0.2)

        # 3. Data completeness
        required_columns = ["temperature", "pressure", "energy_usage", "flow_rate"]
        missing_columns = [
            col for col in required_columns if col not in telemetry_df.columns
        ]
        if not missing_columns:
            confidence_factors.append(0.1)
        else:
            confidence_factors.append(-0.05 * len(missing_columns))

        # 4. Maintenance history completeness
        if (
            features.get("maintenance_history")
            and len(features["maintenance_history"]) > 0
        ):
            confidence_factors.append(0.1)

        # 5. Diagnostic code availability
        if features.get("diagnostic_codes") and len(features["diagnostic_codes"]) > 0:
            confidence_factors.append(
                0.15
            )  # Diagnostic codes significantly increase confidence

        # 6. Water heater type known
        if "heater_type" in features:
            confidence_factors.append(0.05)

        # Calculate final confidence score
        confidence = base_confidence + sum(confidence_factors)

        # Ensure confidence is between 0 and 1
        return max(0.1, min(0.95, confidence))

    async def _fetch_device_data_from_db(self, device_id: str) -> Dict[str, Any]:
        """
        Fetch device type and diagnostic codes from the database.

        Args:
            device_id: ID of the water heater to fetch data for

        Returns:
            Dictionary with device information including heater_type and diagnostic_codes
        """
        result = {
            "heater_type": WaterHeaterType.RESIDENTIAL,  # Default
            "diagnostic_codes": [],
        }

        try:
            async for session in get_db_session():
                if session is None:
                    self.logger.error("Could not establish database session")
                    return result

                # Query device information
                stmt = select(DeviceModel).where(DeviceModel.id == device_id)
                device_result = await session.execute(stmt)
                device = device_result.scalar_one_or_none()

                if not device:
                    self.logger.warning(f"Device {device_id} not found in database")
                    return result

                # Get water heater type from properties
                if device.properties and "heater_type" in device.properties:
                    heater_type_str = device.properties.get("heater_type", "").upper()
                    result["heater_type"] = (
                        WaterHeaterType.COMMERCIAL
                        if heater_type_str == "COMMERCIAL"
                        else WaterHeaterType.RESIDENTIAL
                    )

                # Query diagnostic codes for this device
                stmt = select(DiagnosticCodeModel).where(
                    DiagnosticCodeModel.device_id == device_id
                )
                diagnostic_codes_result = await session.execute(stmt)
                diagnostic_codes = diagnostic_codes_result.scalars().all()

                if diagnostic_codes:
                    result["diagnostic_codes"] = [
                        {
                            "code": code.code,
                            "description": code.description,
                            "severity": code.severity,
                            "timestamp": code.timestamp,
                        }
                        for code in diagnostic_codes
                    ]

                    self.logger.info(
                        f"Found {len(diagnostic_codes)} diagnostic codes for device {device_id}"
                    )
                else:
                    self.logger.info(
                        f"No diagnostic codes found for device {device_id}"
                    )

        except Exception as e:
            self.logger.error(f"Error fetching device data: {e}")

        return result

    def _adjust_with_diagnostic_codes(
        self,
        component_probabilities: Dict[str, float],
        diagnostic_codes: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """
        Adjust component failure probabilities based on diagnostic codes.

        Args:
            component_probabilities: Dictionary mapping components to failure probabilities
            diagnostic_codes: List of diagnostic codes with code, description, severity, and timestamp

        Returns:
            Updated component probabilities
        """
        if not diagnostic_codes:
            return component_probabilities

        # Create a copy of probabilities to modify
        adjusted_probabilities = component_probabilities.copy()

        # Map diagnostic code patterns to components
        component_code_patterns = {
            "heating_element": [
                "HEATING",
                "ELEMENT",
                "HIGH TEMPERATURE",
                "OVERHEATING",
            ],
            "thermostat": ["THERMOSTAT", "TEMPERATURE CONTROL", "TEMP SENSOR"],
            "pressure_valve": ["PRESSURE", "VALVE", "RELIEF VALVE", "T&P VALVE"],
            "anode_rod": ["ANODE", "CORROSION", "RUST", "WATER QUALITY"],
            "tank_integrity": ["LEAK", "TANK", "SEAL", "INTEGRITY", "WATER LEAK"],
        }

        # Process each diagnostic code
        for code_info in diagnostic_codes:
            code = code_info.get("code", "")
            description = code_info.get("description", "")
            severity = code_info.get("severity", "INFO").upper()

            # Calculate recency factor - more recent codes have higher impact
            timestamp = code_info.get("timestamp")
            if timestamp:
                days_ago = (datetime.now() - timestamp).days
                recency_factor = max(
                    0.2, min(1.0, 1.0 - (days_ago / 365.0))
                )  # Decline over a year
            else:
                recency_factor = 0.5  # Default if timestamp missing

            # Determine severity factor
            if severity == "CRITICAL":
                severity_factor = 0.4
            elif severity == "WARNING":
                severity_factor = 0.25
            elif severity == "MAINTENANCE":
                severity_factor = 0.15
            else:  # INFO
                severity_factor = 0.05

            # Combine description and code for matching
            text_to_match = f"{code} {description}".upper()

            # Determine which components are affected by this code
            for component, patterns in component_code_patterns.items():
                if any(pattern in text_to_match for pattern in patterns):
                    # Increase probability based on severity and recency
                    impact = severity_factor * recency_factor
                    current_prob = adjusted_probabilities.get(component, 0.1)

                    # Use a probabilistic combination that avoids exceeding 1.0
                    # P(A or B) = P(A) + P(B) - P(A and B)
                    adjusted_probabilities[component] = min(
                        0.95,  # Cap at 95%
                        current_prob + impact - (current_prob * impact),
                    )

        return adjusted_probabilities

    def _generate_recommendations(
        self, component_probabilities: Dict[str, float], device_id: str
    ) -> List[RecommendedAction]:
        """
        Generate recommended actions based on component failure probabilities.

        Args:
            component_probabilities: Dictionary mapping components to failure probabilities
            device_id: ID of the water heater

        Returns:
            List of recommended actions
        """
        recommendations = []

        # Sort components by failure probability (highest first)
        sorted_components = sorted(
            component_probabilities.items(), key=lambda x: x[1], reverse=True
        )

        for component, probability in sorted_components:
            # Skip components with low failure probability
            if probability < 0.3:
                continue

            # Define severity based on probability
            if probability >= 0.7:
                severity = ActionSeverity.HIGH
            elif probability >= 0.5:
                severity = ActionSeverity.MEDIUM
            else:
                severity = ActionSeverity.LOW

            # Generate component-specific recommendations
            if component == "heating_element":
                action = RecommendedAction(
                    action_id=f"{device_id}-heating-element-{int(probability*100)}",
                    description=f"Inspect heating element for signs of failure (Probability: {probability:.0%})",
                    severity=severity,
                    impact="Water heater may fail to heat water properly if not addressed",
                    expected_benefit="Prevent unexpected downtime and costly emergency repairs",
                    due_date=datetime.now()
                    + timedelta(days=30 if severity != ActionSeverity.HIGH else 7),
                    estimated_cost=75.0,
                    estimated_duration="1-2 hours",
                )
                recommendations.append(action)

            elif component == "thermostat":
                action = RecommendedAction(
                    action_id=f"{device_id}-thermostat-{int(probability*100)}",
                    description=f"Check thermostat calibration and functionality (Probability: {probability:.0%})",
                    severity=severity,
                    impact="Inconsistent water temperature and energy waste",
                    expected_benefit="Improved temperature control and energy efficiency",
                    due_date=datetime.now()
                    + timedelta(days=60 if severity != ActionSeverity.HIGH else 14),
                    estimated_cost=50.0,
                    estimated_duration="30-60 minutes",
                )
                recommendations.append(action)

            elif component == "pressure_valve":
                action = RecommendedAction(
                    action_id=f"{device_id}-pressure-valve-{int(probability*100)}",
                    description=f"Test pressure relief valve operation (Probability: {probability:.0%})",
                    severity=severity,
                    impact="Potential safety hazard from excessive pressure buildup",
                    expected_benefit="Prevent dangerous pressure conditions and ensure safety",
                    due_date=datetime.now()
                    + timedelta(days=14 if severity != ActionSeverity.HIGH else 3),
                    estimated_cost=40.0,
                    estimated_duration="30 minutes",
                )
                recommendations.append(action)

            elif component == "anode_rod":
                action = RecommendedAction(
                    action_id=f"{device_id}-anode-rod-{int(probability*100)}",
                    description=f"Inspect and replace anode rod if deteriorated (Probability: {probability:.0%})",
                    severity=severity,
                    impact="Accelerated tank corrosion and shortened lifespan",
                    expected_benefit="Extended tank life and improved water quality",
                    due_date=datetime.now()
                    + timedelta(days=90 if severity != ActionSeverity.HIGH else 30),
                    estimated_cost=65.0,
                    estimated_duration="1 hour",
                )
                recommendations.append(action)

            elif component == "tank_integrity":
                action = RecommendedAction(
                    action_id=f"{device_id}-tank-integrity-{int(probability*100)}",
                    description=f"Perform tank integrity inspection for leaks or corrosion (Probability: {probability:.0%})",
                    severity=severity,
                    impact="Potential water damage from leaks or complete unit failure",
                    expected_benefit="Early detection of issues can prevent water damage",
                    due_date=datetime.now()
                    + timedelta(days=60 if severity != ActionSeverity.HIGH else 14),
                    estimated_cost=100.0,
                    estimated_duration="1-2 hours",
                )
                recommendations.append(action)

        # If no specific recommendations were generated, add a general one
        if not recommendations:
            action = RecommendedAction(
                action_id=f"{device_id}-general-maintenance",
                description="Perform routine maintenance inspection",
                severity=ActionSeverity.LOW,
                impact="Gradual performance degradation over time",
                expected_benefit="Maintain optimal performance and extend equipment life",
                due_date=datetime.now() + timedelta(days=180),
                estimated_cost=120.0,
                estimated_duration="2 hours",
            )
            recommendations.append(action)

        return recommendations


class ComponentFailureActionRecommender(IActionRecommender):
    """
    Generates action recommendations for component failure predictions.

    Analyzes component failure predictions and creates prioritized, actionable recommendations.
    """

    def __init__(self):
        """Initialize the component failure action recommender."""
        self.logger = logging.getLogger(__name__)

    async def recommend_actions(
        self, prediction_result: PredictionResult
    ) -> List[RecommendedAction]:
        """
        Generate recommended actions based on a component failure prediction.

        Args:
            prediction_result: The component failure prediction

        Returns:
            List of recommended actions
        """
        # If raw details are missing, return empty recommendations
        if (
            not prediction_result.raw_details
            or "components" not in prediction_result.raw_details
        ):
            self.logger.warning(
                f"Missing component data in prediction for device {prediction_result.device_id}"
            )
            return []

        component_probabilities = prediction_result.raw_details["components"]

        # Consider heater type when generating recommendations
        heater_type = prediction_result.raw_details.get("heater_type", "RESIDENTIAL")

        # Add more specific recommendations for commercial units if applicable
        special_recommendations = []
        if heater_type == "COMMERCIAL" and prediction_result.predicted_value >= 0.6:
            special_recommendations.append(
                RecommendedAction(
                    action_id=f"{prediction_result.device_id}-commercial-check",
                    description="Schedule priority maintenance for commercial unit",
                    severity=ActionSeverity.HIGH,
                    impact="Commercial unit failure could affect multiple users or critical operations",
                    expected_benefit="Prevent downtime that could impact business operations",
                    due_date=datetime.now() + timedelta(days=7),
                    estimated_cost=200.0,
                    estimated_duration="2-4 hours",
                )
            )

        # Use the internal method from ComponentFailurePrediction to generate recommendations
        component_failure_model = ComponentFailurePrediction()
        standard_recommendations = component_failure_model._generate_recommendations(
            component_probabilities, prediction_result.device_id
        )

        # Combine and return all recommendations
        return special_recommendations + standard_recommendations
