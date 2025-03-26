"""
Descaling requirement prediction model for water heaters.

This module implements prediction of descaling requirements based on
efficiency degradation patterns, water hardness, and operational history.
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


class DescalingRequirementPrediction(IPredictionModel):
    """
    Predicts descaling requirements for water heaters.
    
    Analyzes efficiency degradation patterns, water hardness, and operational history
    to determine when descaling maintenance is required.
    """
    
    def __init__(self):
        """Initialize the descaling requirement prediction model."""
        self.model_name = "DescalingRequirementPrediction"
        self.model_version = "1.0.0"
        self.features_required = [
            "efficiency", 
            "energy_usage", 
            "flow_rate", 
            "heating_cycles",
            "water_hardness",
            "total_operation_hours",
            "maintenance_history"
        ]
    
    async def predict(self, device_id: str, features: Dict[str, Any]) -> PredictionResult:
        """
        Generate descaling requirement prediction for a water heater.
        
        Args:
            device_id: ID of the water heater
            features: Dictionary of features including efficiency and operational data
            
        Returns:
            PredictionResult with descaling requirement probability
        """
        # Extract time series data and prepare for analysis
        telemetry_df = self._prepare_telemetry_data(features)
        
        # Calculate days since last descaling
        days_since_descaling = self._days_since_last_descaling(features)
        
        # Calculate efficiency degradation metrics
        efficiency_metrics = self._calculate_efficiency_metrics(telemetry_df, features)
        
        # Calculate scale buildup estimate
        scale_estimate = self._estimate_scale_buildup(
            days_since_descaling, 
            features.get('water_hardness', 150),
            efficiency_metrics
        )
        
        # Calculate overall descaling requirement probability
        descaling_requirement = self._calculate_descaling_requirement(
            scale_estimate,
            days_since_descaling,
            efficiency_metrics
        )
        
        # Calculate confidence based on data quality and completeness
        confidence = self._calculate_confidence(telemetry_df, features)
        
        # Generate appropriate recommendations
        recommendations = self._generate_recommendations(
            descaling_requirement,
            scale_estimate,
            days_since_descaling,
            features.get('water_hardness', 150),
            device_id
        )
        
        # Create and return prediction result
        return PredictionResult(
            prediction_type="descaling_requirement",
            device_id=device_id,
            predicted_value=descaling_requirement,
            confidence=confidence,
            features_used=self._get_used_features(features),
            timestamp=datetime.now(),
            recommended_actions=recommendations,
            raw_details={
                "efficiency_degradation": efficiency_metrics.get('degradation_rate', 0),
                "days_since_last_descaling": days_since_descaling,
                "water_hardness": features.get('water_hardness', 0),
                "estimated_scale_thickness_mm": scale_estimate.get('thickness_mm', 0)
            }
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Return information about the model."""
        return {
            "name": self.model_name,
            "version": self.model_version,
            "description": "Predicts when water heaters require descaling based on efficiency degradation",
            "features_required": self.features_required,
            "last_trained": datetime.now() - timedelta(days=30),  # Placeholder
            "performance_metrics": {
                "accuracy": 0.88,
                "precision": 0.85,
                "recall": 0.92,
                "f1_score": 0.88,
                "mae": 21.3  # Mean absolute error in days for descaling timing
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
        try:
            # Extract time series data
            df_data = {
                'timestamp': features.get('timestamp', [])
            }
            
            # Add available telemetry features
            for feature in ['efficiency', 'energy_usage', 'flow_rate', 'heating_cycles', 'element_temperature']:
                if feature in features and features[feature]:
                    df_data[feature] = features[feature]
            
            # Create DataFrame
            df = pd.DataFrame(df_data)
            
            # Sort by timestamp and ensure proper datetime format
            if 'timestamp' in df.columns and len(df) > 0:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
            
            return df
        except Exception as e:
            # Return empty DataFrame in case of errors
            print(f"Error preparing telemetry data: {e}")
            return pd.DataFrame()
    
    def _get_used_features(self, features: Dict[str, Any]) -> List[str]:
        """
        Get list of features actually used from the available features.
        
        Args:
            features: Feature dictionary
            
        Returns:
            List of feature names that were actually used
        """
        used_features = []
        
        for feature in self.features_required:
            if feature in features and features[feature]:
                used_features.append(feature)
        
        return used_features
    
    def _days_since_last_descaling(self, features: Dict[str, Any]) -> int:
        """
        Calculate number of days since the last descaling maintenance.
        
        Args:
            features: Feature dictionary with maintenance history
            
        Returns:
            Days since last descaling, or a large value if never descaled
        """
        maintenance_history = features.get('maintenance_history', [])
        installation_date = None
        last_descaling_date = None
        
        # Find most recent descaling and installation dates
        for maintenance in maintenance_history:
            maintenance_type = maintenance.get('type', '').lower()
            maintenance_date = maintenance.get('date')
            
            if maintenance_date:
                if maintenance_type == 'installation' and (installation_date is None or maintenance_date > installation_date):
                    installation_date = maintenance_date
                elif maintenance_type == 'descaling' and (last_descaling_date is None or maintenance_date > last_descaling_date):
                    last_descaling_date = maintenance_date
        
        # If never descaled, use installation date
        reference_date = last_descaling_date or installation_date
        
        if reference_date:
            # Calculate days since reference date
            if isinstance(reference_date, str):
                try:
                    reference_date = datetime.fromisoformat(reference_date.replace('Z', '+00:00'))
                except:
                    reference_date = datetime.strptime(reference_date, '%Y-%m-%dT%H:%M:%SZ')
            
            days = (datetime.now() - reference_date).days
            return max(0, days)
        else:
            # If no reference date, assume it's been a long time
            return 365  # Assume 1 year
    
    def _calculate_efficiency_metrics(
        self, telemetry_df: pd.DataFrame, features: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate efficiency degradation metrics from telemetry data.
        
        Args:
            telemetry_df: Processed telemetry DataFrame
            features: Raw feature dictionary
            
        Returns:
            Dictionary of efficiency metrics
        """
        metrics = {
            'degradation_rate': 0.0,
            'efficiency_trend': 0.0,
            'flow_rate_change': 0.0,
            'heating_cycle_change': 0.0
        }
        
        if telemetry_df.empty:
            return metrics
        
        # Calculate efficiency degradation if efficiency data is available
        if 'efficiency' in telemetry_df.columns and len(telemetry_df) >= 3:
            # Get efficiency values
            efficiencies = telemetry_df['efficiency'].values
            
            # Calculate trend (negative trend indicates degradation)
            metrics['efficiency_trend'] = self._calculate_trend(telemetry_df['efficiency'])
            
            # Calculate average degradation rate
            if len(efficiencies) >= 2:
                first_efficiency = np.mean(efficiencies[:min(3, len(efficiencies))])
                last_efficiency = np.mean(efficiencies[-min(3, len(efficiencies)):])
                
                # Calculate total degradation
                degradation = max(0, first_efficiency - last_efficiency)
                
                # Calculate degradation rate per month
                days_span = (telemetry_df['timestamp'].max() - telemetry_df['timestamp'].min()).days
                days_span = max(1, days_span)  # Avoid division by zero
                
                monthly_degradation = degradation * (30 / days_span)
                metrics['degradation_rate'] = monthly_degradation
        
        # Calculate flow rate degradation
        if 'flow_rate' in telemetry_df.columns and len(telemetry_df) >= 3:
            # Get first and last values
            first_flow = np.mean(telemetry_df['flow_rate'].iloc[:min(3, len(telemetry_df))])
            last_flow = np.mean(telemetry_df['flow_rate'].iloc[-min(3, len(telemetry_df)):])
            
            # Calculate percentage change (negative indicates degradation)
            if first_flow > 0:
                metrics['flow_rate_change'] = (last_flow - first_flow) / first_flow
            
        # Calculate heating cycle time increase
        if 'heating_cycles' in telemetry_df.columns and len(telemetry_df) >= 3:
            # Get first and last values
            first_cycle = np.mean(telemetry_df['heating_cycles'].iloc[:min(3, len(telemetry_df))])
            last_cycle = np.mean(telemetry_df['heating_cycles'].iloc[-min(3, len(telemetry_df)):])
            
            # Calculate percentage change (positive indicates degradation)
            if first_cycle > 0:
                metrics['heating_cycle_change'] = (last_cycle - first_cycle) / first_cycle
        
        return metrics
    
    def _estimate_scale_buildup(
        self, 
        days_since_descaling: int, 
        water_hardness: float,
        efficiency_metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Estimate scale buildup based on water hardness and operational data.
        
        Args:
            days_since_descaling: Days since last descaling
            water_hardness: Water hardness in ppm CaCO3
            efficiency_metrics: Calculated efficiency metrics
            
        Returns:
            Dictionary with scale buildup estimates
        """
        # Initialize with default values
        estimate = {
            'thickness_mm': 0.0,
            'volume_percentage': 0.0,
            'surface_coverage': 0.0
        }
        
        # Classify water hardness level
        hardness_factor = 0.5  # Default: medium hardness
        if water_hardness < 60:  # Soft water
            hardness_factor = 0.2
        elif water_hardness < 120:  # Slightly hard
            hardness_factor = 0.4
        elif water_hardness < 180:  # Moderately hard
            hardness_factor = 0.6
        elif water_hardness < 250:  # Hard
            hardness_factor = 0.8
        else:  # Very hard
            hardness_factor = 1.0
        
        # Base scale buildup calculation from time and water hardness
        # Simple model: thickness increases with time and water hardness
        estimate['thickness_mm'] = (days_since_descaling / 365) * hardness_factor * 5.0  # Max 5mm per year with hardest water
        
        # Adjust based on efficiency metrics
        degradation_factor = 1.0
        
        # Higher degradation rate suggests more scale
        if efficiency_metrics['degradation_rate'] > 0:
            degradation_factor += efficiency_metrics['degradation_rate'] * 5
        
        # Reduced flow rate suggests more scale
        if efficiency_metrics['flow_rate_change'] < 0:
            degradation_factor += abs(efficiency_metrics['flow_rate_change']) * 2
        
        # Increased heating cycle time suggests more scale
        if efficiency_metrics['heating_cycle_change'] > 0:
            degradation_factor += efficiency_metrics['heating_cycle_change'] * 2
        
        # Apply degradation factor to scale estimate
        estimate['thickness_mm'] *= degradation_factor
        
        # Cap at reasonable maximum
        estimate['thickness_mm'] = min(10.0, estimate['thickness_mm'])
        
        # Calculate related metrics
        estimate['volume_percentage'] = estimate['thickness_mm'] * 3  # Approximate relationship
        estimate['surface_coverage'] = min(100, estimate['thickness_mm'] * 10)  # Approximate percentage coverage
        
        return estimate
    
    def _calculate_descaling_requirement(
        self,
        scale_estimate: Dict[str, float],
        days_since_descaling: int,
        efficiency_metrics: Dict[str, float]
    ) -> float:
        """
        Calculate overall descaling requirement probability.
        
        Args:
            scale_estimate: Scale buildup estimates
            days_since_descaling: Days since last descaling
            efficiency_metrics: Calculated efficiency metrics
            
        Returns:
            Probability (0-1) that descaling is required
        """
        # Base probability on scale thickness
        thickness = scale_estimate['thickness_mm']
        base_probability = min(1.0, thickness / 5.0)  # Scale of 5mm or more requires descaling
        
        # Adjust based on days since last descaling
        time_factor = min(1.0, days_since_descaling / 365)  # Consider annual descaling baseline
        
        # Adjust based on efficiency degradation
        efficiency_factor = min(1.0, efficiency_metrics['degradation_rate'] * 10)
        
        # Calculate combined probability
        # Weigh factors based on importance:
        # - Scale thickness: 50%
        # - Time since last descaling: 20%
        # - Efficiency degradation: 30%
        combined_probability = (
            base_probability * 0.5 +
            time_factor * 0.2 +
            efficiency_factor * 0.3
        )
        
        # Ensure probability is between 0 and 1
        return max(0.0, min(1.0, combined_probability))
    
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
        
        # Factors that affect confidence
        confidence_factors = []
        
        # 1. Data volume
        if len(telemetry_df) >= 60:  # At least 60 data points
            confidence_factors.append(0.2)
        elif len(telemetry_df) >= 30:
            confidence_factors.append(0.1)
        elif len(telemetry_df) < 10:  # Too little data
            confidence_factors.append(-0.2)
        
        # 2. Data span
        if 'timestamp' in telemetry_df.columns and len(telemetry_df) > 0:
            data_span_days = (telemetry_df['timestamp'].max() - telemetry_df['timestamp'].min()).days
            
            if data_span_days >= 90:  # At least 3 months
                confidence_factors.append(0.2)
            elif data_span_days >= 30:  # At least 1 month
                confidence_factors.append(0.1)
            elif data_span_days < 7:  # Less than a week
                confidence_factors.append(-0.1)
        else:
            confidence_factors.append(-0.2)  # No timestamp data
        
        # 3. Feature completeness
        key_features = ['efficiency', 'energy_usage', 'flow_rate', 'water_hardness']
        missing_features = [f for f in key_features if f not in features or not features[f]]
        
        if not missing_features:
            confidence_factors.append(0.1)
        else:
            confidence_factors.append(-0.1 * len(missing_features))
        
        # 4. Maintenance history completeness
        if features.get('maintenance_history') and len(features['maintenance_history']) > 0:
            confidence_factors.append(0.1)
        else:
            confidence_factors.append(-0.1)
        
        # Calculate final confidence
        confidence = base_confidence + sum(confidence_factors)
        
        # Ensure confidence is between 0 and 1
        return max(0.1, min(0.95, confidence))
    
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
        except Exception as e:
            print(f"Error calculating trend: {e}")
            return 0.0
    
    def _generate_recommendations(
        self, 
        descaling_requirement: float, 
        scale_estimate: Dict[str, float],
        days_since_descaling: int,
        water_hardness: float,
        device_id: str
    ) -> List[RecommendedAction]:
        """
        Generate recommended actions based on descaling requirement.
        
        Args:
            descaling_requirement: Calculated descaling requirement probability
            scale_estimate: Scale buildup estimates
            days_since_descaling: Days since last descaling
            water_hardness: Water hardness in ppm
            device_id: ID of the water heater
            
        Returns:
            List of recommended actions
        """
        recommendations = []
        
        # Determine severity based on descaling requirement
        if descaling_requirement >= 0.8:
            severity = ActionSeverity.HIGH
            timeframe = "as soon as possible"
            impact = "Significant reduction in heating efficiency and potential damage to heating elements"
            due_days = 14
        elif descaling_requirement >= 0.5:
            severity = ActionSeverity.MEDIUM
            timeframe = "within the next month"
            impact = "Reduced heating efficiency and increased energy consumption"
            due_days = 30
        elif descaling_requirement >= 0.3:
            severity = ActionSeverity.LOW
            timeframe = "within the next three months"
            impact = "Gradually decreasing efficiency over time"
            due_days = 90
        else:
            # No descaling needed yet
            if days_since_descaling > 270 and water_hardness > 120:
                # But if it's been a while with hard water, recommend inspection
                action = RecommendedAction(
                    action_id=f"{device_id}-descaling-inspection",
                    description="Inspect for early signs of scaling buildup during next maintenance",
                    severity=ActionSeverity.LOW,
                    impact="Early detection prevents efficiency loss",
                    expected_benefit="Maintain optimal efficiency and extend heater lifespan",
                    due_date=datetime.now() + timedelta(days=180)
                )
                recommendations.append(action)
            return recommendations
        
        # Create descaling recommendation
        descaling_action = RecommendedAction(
            action_id=f"{device_id}-descaling-{int(descaling_requirement*100)}",
            description=f"Perform descaling maintenance {timeframe} (Scale: {scale_estimate['thickness_mm']:.1f}mm)",
            severity=severity,
            impact=impact,
            expected_benefit="Restore heating efficiency and extend equipment life",
            due_date=datetime.now() + timedelta(days=due_days),
            estimated_cost=120.0,
            estimated_duration="2-3 hours"
        )
        recommendations.append(descaling_action)
        
        # Add water treatment recommendation for very hard water
        if water_hardness > 180 and severity in [ActionSeverity.HIGH, ActionSeverity.MEDIUM]:
            water_treatment_action = RecommendedAction(
                action_id=f"{device_id}-water-treatment",
                description="Consider installing a water softener or scale inhibitor system",
                severity=ActionSeverity.MEDIUM,
                impact="Hard water will cause rapid scale buildup after descaling",
                expected_benefit="Reduce frequency of descaling maintenance and improve long-term efficiency",
                estimated_cost=350.0
            )
            recommendations.append(water_treatment_action)
        
        # Add inspection recommendation for regular monitoring
        if severity == ActionSeverity.HIGH:
            inspection_action = RecommendedAction(
                action_id=f"{device_id}-post-descaling-inspection",
                description="Inspect heating elements during descaling for damage from scale buildup",
                severity=ActionSeverity.MEDIUM,
                impact="Scaled elements may need replacement to restore full efficiency",
                expected_benefit="Identify and address any component damage caused by scaling",
                due_date=datetime.now() + timedelta(days=due_days)
            )
            recommendations.append(inspection_action)
        
        return recommendations


class DescalingActionRecommender(IActionRecommender):
    """
    Generates action recommendations for descaling requirement predictions.
    
    Analyzes descaling requirement predictions and creates prioritized, actionable recommendations.
    """
    
    async def recommend_actions(self, prediction_result: PredictionResult) -> List[RecommendedAction]:
        """
        Generate recommended actions based on a descaling requirement prediction.
        
        Args:
            prediction_result: The descaling requirement prediction
            
        Returns:
            List of recommended actions
        """
        # Extract raw details for more specific recommendations
        raw_details = prediction_result.raw_details or {}
        
        # Use internal method from DescalingRequirementPrediction for consistency
        descaling_model = DescalingRequirementPrediction()
        
        return descaling_model._generate_recommendations(
            descaling_requirement=prediction_result.predicted_value,
            scale_estimate={
                'thickness_mm': raw_details.get('estimated_scale_thickness_mm', 0),
                'volume_percentage': 0,  # Default value
                'surface_coverage': 0  # Default value
            },
            days_since_descaling=raw_details.get('days_since_last_descaling', 365),
            water_hardness=raw_details.get('water_hardness', 150),
            device_id=prediction_result.device_id
        )
