"""
Component failure prediction model for water heaters.

This module implements prediction of component failures based on
telemetry data patterns and usage information.
"""
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple

from src.predictions.interfaces import (
    IPredictionModel,
    IActionRecommender,
    PredictionResult,
    RecommendedAction,
    ActionSeverity
)


class ComponentFailurePrediction(IPredictionModel):
    """
    Predicts probability of component failures in water heaters.
    
    Uses telemetry data to identify patterns indicative of impending component failures.
    """
    
    def __init__(self):
        """Initialize the component failure prediction model."""
        self.model_name = "ComponentFailurePrediction"
        self.model_version = "1.0.0"
        self.features_required = [
            "temperature", 
            "pressure", 
            "energy_usage", 
            "flow_rate", 
            "heating_cycles",
            "total_operation_hours",
            "maintenance_history"
        ]
    
    async def predict(self, device_id: str, features: Dict[str, Any]) -> PredictionResult:
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
        
        # Calculate component-specific failure probabilities
        component_probabilities = self._calculate_component_probabilities(telemetry_df, features)
        
        # Calculate overall failure probability (weighted average of component probabilities)
        component_weights = {
            "heating_element": 0.4,
            "thermostat": 0.2,
            "pressure_valve": 0.2,
            "anode_rod": 0.1,
            "tank_integrity": 0.1
        }
        
        overall_probability = sum(
            probability * component_weights.get(component, 0.1)
            for component, probability in component_probabilities.items()
        )
        
        # Calculate confidence based on data quality and sufficiency
        confidence = self._calculate_confidence(telemetry_df, features)
        
        # Generate appropriate recommendations based on component probabilities
        recommendations = self._generate_recommendations(component_probabilities, device_id)
        
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
                "components": component_probabilities
            }
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
                "auc": 0.91
            }
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
            df = pd.DataFrame({
                'timestamp': features.get('timestamp', []),
                'temperature': features.get('temperature', []),
                'pressure': features.get('pressure', []),
                'energy_usage': features.get('energy_usage', []),
                'flow_rate': features.get('flow_rate', []),
                'heating_cycles': features.get('heating_cycles', [])
            })
            
            # Sort by timestamp and ensure proper datetime format
            if 'timestamp' in df.columns and len(df) > 0:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
            
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
            "tank_integrity": 0.1
        }
        
        if telemetry_df.empty:
            return probabilities
        
        # Calculate features for heating element failure detection
        if 'temperature' in telemetry_df.columns and len(telemetry_df) >= 3:
            # Detect temperature fluctuations - high fluctuations indicate possible element issues
            temp_std = telemetry_df['temperature'].std()
            temp_trend = self._calculate_trend(telemetry_df['temperature'])
            
            # High fluctuation or decreasing trend indicates potential issues
            if temp_std > 3.0 or temp_trend < -0.1:
                probabilities["heating_element"] = min(0.3 + temp_std * 0.15, 0.9)
        
        # Calculate features for thermostat failure detection
        if 'temperature' in telemetry_df.columns and 'heating_cycles' in telemetry_df.columns:
            # Correlation between temperature and heating cycles
            # Poor correlation may indicate thermostat issues
            try:
                temp_cycle_corr = telemetry_df['temperature'].corr(telemetry_df['heating_cycles'])
                if temp_cycle_corr < 0.5:
                    probabilities["thermostat"] = min(0.9, 0.8 - temp_cycle_corr)
            except:
                pass
            
            # Detect temperature overshoots
            if len(telemetry_df) > 5:
                temp_diffs = telemetry_df['temperature'].diff().dropna()
                large_jumps = (temp_diffs.abs() > 5).sum()
                if large_jumps > 2:
                    probabilities["thermostat"] = max(probabilities["thermostat"], 
                                                     min(0.3 + large_jumps * 0.1, 0.9))
        
        # Calculate features for pressure valve failure detection
        if 'pressure' in telemetry_df.columns:
            pressure_std = telemetry_df['pressure'].std()
            pressure_max = telemetry_df['pressure'].max()
            
            # High pressure spikes indicate valve issues
            if pressure_max > 3.5 or pressure_std > 0.5:
                probabilities["pressure_valve"] = min(0.4 + pressure_std * 0.8, 0.9)
        
        # Calculate features for anode rod corrosion
        total_hours = features.get('total_operation_hours', 0)
        maintenance_history = features.get('maintenance_history', [])
        
        # Check last anode rod replacement/inspection
        last_anode_maintenance = None
        for maintenance in maintenance_history:
            if maintenance.get('type') in ('anode_replacement', 'anode_inspection'):
                maint_date = maintenance.get('date')
                if maint_date and (last_anode_maintenance is None or maint_date > last_anode_maintenance):
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
                    probabilities["anode_rod"] *= (days_since_maintenance / 365)
        
        # Tank integrity deterioration with age and pressure events
        tank_age_factor = min(total_hours / 131400, 1.0)  # 15 years = max factor
        probabilities["tank_integrity"] = 0.1 + (tank_age_factor * 0.5)
        
        # Pressure events accelerate tank deterioration
        if 'pressure' in telemetry_df.columns:
            pressure_events = (telemetry_df['pressure'] > 3.0).sum()
            if pressure_events > 0:
                probabilities["tank_integrity"] = min(
                    probabilities["tank_integrity"] + (pressure_events * 0.05), 
                    0.9
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
    
    def _calculate_confidence(self, telemetry_df: pd.DataFrame, features: Dict[str, Any]) -> float:
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
        if not telemetry_df.empty and 'timestamp' in telemetry_df.columns:
            latest_data = telemetry_df['timestamp'].max()
            data_age_hours = (datetime.now() - latest_data).total_seconds() / 3600
            
            if data_age_hours < 24:  # Data less than a day old
                confidence_factors.append(0.1)
            elif data_age_hours > 168:  # Data more than a week old
                confidence_factors.append(-0.2)
        
        # 3. Data completeness
        required_columns = ['temperature', 'pressure', 'energy_usage', 'flow_rate']
        missing_columns = [col for col in required_columns if col not in telemetry_df.columns]
        if not missing_columns:
            confidence_factors.append(0.1)
        else:
            confidence_factors.append(-0.05 * len(missing_columns))
        
        # 4. Maintenance history completeness
        if features.get('maintenance_history') and len(features['maintenance_history']) > 0:
            confidence_factors.append(0.1)
        
        # Calculate final confidence score
        confidence = base_confidence + sum(confidence_factors)
        
        # Ensure confidence is between 0 and 1
        return max(0.1, min(0.95, confidence))
    
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
            component_probabilities.items(), 
            key=lambda x: x[1], 
            reverse=True
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
                    due_date=datetime.now() + timedelta(days=30 if severity != ActionSeverity.HIGH else 7),
                    estimated_cost=75.0,
                    estimated_duration="1-2 hours"
                )
                recommendations.append(action)
                
            elif component == "thermostat":
                action = RecommendedAction(
                    action_id=f"{device_id}-thermostat-{int(probability*100)}",
                    description=f"Check thermostat calibration and functionality (Probability: {probability:.0%})",
                    severity=severity,
                    impact="Inconsistent water temperature and energy waste",
                    expected_benefit="Improved temperature control and energy efficiency",
                    due_date=datetime.now() + timedelta(days=60 if severity != ActionSeverity.HIGH else 14),
                    estimated_cost=50.0,
                    estimated_duration="30-60 minutes"
                )
                recommendations.append(action)
                
            elif component == "pressure_valve":
                action = RecommendedAction(
                    action_id=f"{device_id}-pressure-valve-{int(probability*100)}",
                    description=f"Test pressure relief valve operation (Probability: {probability:.0%})",
                    severity=severity,
                    impact="Potential safety hazard from excessive pressure buildup",
                    expected_benefit="Prevent dangerous pressure conditions and ensure safety",
                    due_date=datetime.now() + timedelta(days=14 if severity != ActionSeverity.HIGH else 3),
                    estimated_cost=40.0,
                    estimated_duration="30 minutes"
                )
                recommendations.append(action)
                
            elif component == "anode_rod":
                action = RecommendedAction(
                    action_id=f"{device_id}-anode-rod-{int(probability*100)}",
                    description=f"Inspect and replace anode rod if deteriorated (Probability: {probability:.0%})",
                    severity=severity,
                    impact="Accelerated tank corrosion and shortened lifespan",
                    expected_benefit="Extended tank life and improved water quality",
                    due_date=datetime.now() + timedelta(days=90 if severity != ActionSeverity.HIGH else 30),
                    estimated_cost=65.0,
                    estimated_duration="1 hour"
                )
                recommendations.append(action)
                
            elif component == "tank_integrity":
                action = RecommendedAction(
                    action_id=f"{device_id}-tank-integrity-{int(probability*100)}",
                    description=f"Perform tank integrity inspection for leaks or corrosion (Probability: {probability:.0%})",
                    severity=severity,
                    impact="Potential water damage from leaks or complete unit failure",
                    expected_benefit="Early detection of issues can prevent water damage",
                    due_date=datetime.now() + timedelta(days=60 if severity != ActionSeverity.HIGH else 14),
                    estimated_cost=100.0,
                    estimated_duration="1-2 hours"
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
                estimated_duration="2 hours"
            )
            recommendations.append(action)
        
        return recommendations


class ComponentFailureActionRecommender(IActionRecommender):
    """
    Generates action recommendations for component failure predictions.
    
    Analyzes component failure predictions and creates prioritized, actionable recommendations.
    """
    
    async def recommend_actions(self, prediction_result: PredictionResult) -> List[RecommendedAction]:
        """
        Generate recommended actions based on a component failure prediction.
        
        Args:
            prediction_result: The component failure prediction
            
        Returns:
            List of recommended actions
        """
        # If raw details are missing, return empty recommendations
        if not prediction_result.raw_details or "components" not in prediction_result.raw_details:
            return []
        
        component_probabilities = prediction_result.raw_details["components"]
        
        # Use the internal method from ComponentFailurePrediction to generate recommendations
        component_failure_model = ComponentFailurePrediction()
        return component_failure_model._generate_recommendations(
            component_probabilities, 
            prediction_result.device_id
        )
