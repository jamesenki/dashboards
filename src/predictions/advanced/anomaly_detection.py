"""
Anomaly detection predictor for water heater telemetry data.

This module implements pattern recognition and anomaly detection in water heater
telemetry data to predict potential future issues before they manifest.
"""
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from src.predictions.interfaces import PredictionResult, ActionSeverity, RecommendedAction


class AnomalyDetectionPredictor:
    """
    Predicts potential future issues based on pattern recognition and anomaly detection
    in water heater telemetry data.
    
    This predictor analyzes time-series data to identify:
    - Unusual patterns in temperature fluctuations
    - Pressure anomalies that may indicate valve issues
    - Trend analysis to project when components might reach critical levels
    """
    
    def __init__(self):
        """Initialize the anomaly detection predictor."""
        # Define thresholds for various measurements
        self._thresholds = {
            'temperature_rate_of_change': 0.5,  # degrees per day
            'pressure_spike': 10,  # kPa
            'pressure_deviation': 5,  # percent from baseline
            'heating_cycle_variation': 20,  # percent
        }
        
        # Component mapping for anomalies
        self._anomaly_component_mapping = {
            'temperature': ['thermostat', 'heating_element'],
            'pressure': ['pressure_valve', 'tank_integrity'],
            'heating_cycle': ['thermostat', 'heating_element'],
        }
    
    def predict(self, device_id: str, features: Dict[str, Any]) -> PredictionResult:
        """
        Generate predictions based on anomaly detection in telemetry data.
        
        Args:
            device_id: Identifier for the water heater
            features: Dictionary containing telemetry time-series data
            
        Returns:
            PredictionResult containing detected anomalies and recommended actions
        """
        # Initialize prediction result
        result = PredictionResult(
            device_id=device_id,
            prediction_type="anomaly_detection",
            predicted_value=0.0,  # Will be updated based on anomaly detection
            confidence=0.85,  # Initial confidence, may be updated based on data quality
            features_used=[key for key in features.keys()],
            timestamp=datetime.now(),
            recommended_actions=[],  # Will be populated later
            raw_details={
                "detected_anomalies": [],
                "trend_analysis": {},
            }
        )
        
        # Detect anomalies in different measurement types
        if 'temperature_readings' in features:
            self._analyze_temperature(features['temperature_readings'], result)
        
        if 'pressure_readings' in features:
            self._analyze_pressure(features['pressure_readings'], result)
        
        if 'heating_cycle_data' in features:
            self._analyze_heating_cycles(features.get('heating_cycle_data', []), result)
        
        # Generate recommended actions based on detected anomalies
        self._generate_recommendations(result)
        
        # Calculate overall anomaly score (0-1)
        anomaly_count = len(result.raw_details["detected_anomalies"])
        trend_count = len(result.raw_details["trend_analysis"])
        
        if anomaly_count > 0 or trend_count > 0:
            # Higher score means more anomalies detected
            max_expected_anomalies = 5  # Normalize based on expected maximum
            result.predicted_value = min(
                1.0, 
                (anomaly_count * 0.15 + trend_count * 0.05) / max_expected_anomalies
            )
        
        return result
    
    def _analyze_temperature(self, temperature_readings: List[Dict], result: PredictionResult) -> None:
        """
        Analyze temperature readings for anomalies and trends.
        
        Args:
            temperature_readings: List of temperature readings with timestamp and value
            result: PredictionResult to update with findings
        """
        if not temperature_readings or len(temperature_readings) < 3:
            return
        
        # Sort readings by timestamp
        sorted_readings = sorted(temperature_readings, key=lambda x: x['timestamp'])
        
        # Check for overall trend
        first_reading = sorted_readings[0]['value']
        last_reading = sorted_readings[-1]['value']
        time_span = (sorted_readings[-1]['timestamp'] - sorted_readings[0]['timestamp']).days
        
        if time_span < 1:
            time_span = 1  # Avoid division by zero
            
        rate_of_change = (last_reading - first_reading) / time_span
        
        # Detect significant temperature trend
        if abs(rate_of_change) > self._thresholds['temperature_rate_of_change']:
            trend_direction = "increasing" if rate_of_change > 0 else "decreasing"
            days_until_critical = self._calculate_days_until_critical(
                current_value=last_reading,
                rate_of_change=rate_of_change,
                critical_threshold=160 if rate_of_change > 0 else 110
            )
            
            component = "thermostat" if trend_direction == "increasing" else "heating_element"
            probability = min(0.95, 0.6 + abs(rate_of_change) / 2)
            
            result.raw_details["trend_analysis"]["temperature"] = {
                "trend_direction": trend_direction,
                "rate_of_change_per_day": rate_of_change,
                "component_affected": component,
                "probability": probability,
                "days_until_critical": days_until_critical
            }
        
        # Check for unusual spikes or drops
        for i in range(1, len(sorted_readings) - 1):
            prev_value = sorted_readings[i-1]['value']
            curr_value = sorted_readings[i]['value']
            next_value = sorted_readings[i+1]['value']
            
            # Detect spike pattern (up then down)
            if curr_value > prev_value + 5 and curr_value > next_value + 5:
                result.raw_details["detected_anomalies"].append({
                    "measurement_type": "temperature",
                    "anomaly_type": "spike",
                    "timestamp": sorted_readings[i]['timestamp'].isoformat(),
                    "value": curr_value,
                    "baseline": (prev_value + next_value) / 2,
                    "deviation_percent": (curr_value / ((prev_value + next_value) / 2) - 1) * 100,
                    "potential_components": self._anomaly_component_mapping["temperature"],
                    "probability": 0.8
                })
    
    def _analyze_pressure(self, pressure_readings: List[Dict], result: PredictionResult) -> None:
        """
        Analyze pressure readings for anomalies and trends.
        
        Args:
            pressure_readings: List of pressure readings with timestamp and value
            result: PredictionResult to update with findings
        """
        if not pressure_readings or len(pressure_readings) < 2:
            return
        
        # Sort readings by timestamp
        sorted_readings = sorted(pressure_readings, key=lambda x: x['timestamp'])
        
        # Calculate baseline pressure (average of first 3 readings or all if fewer)
        baseline_count = min(3, len(sorted_readings))
        baseline_pressure = sum(r['value'] for r in sorted_readings[:baseline_count]) / baseline_count
        
        # Check for pressure spikes or unusual patterns
        for i in range(1, len(sorted_readings)):
            prev_value = sorted_readings[i-1]['value']
            curr_value = sorted_readings[i]['value']
            
            # Check for significant pressure change
            if abs(curr_value - prev_value) > self._thresholds['pressure_spike']:
                probability = min(0.95, 0.7 + abs(curr_value - prev_value) / 50)
                
                result.raw_details["detected_anomalies"].append({
                    "measurement_type": "pressure",
                    "anomaly_type": "spike",
                    "timestamp": sorted_readings[i]['timestamp'].isoformat(),
                    "value": curr_value,
                    "previous_value": prev_value,
                    "change_magnitude": abs(curr_value - prev_value),
                    "potential_components": self._anomaly_component_mapping["pressure"],
                    "probability": probability
                })
            
            # Check for sustained deviation from baseline
            deviation_percent = abs(curr_value / baseline_pressure - 1) * 100
            if deviation_percent > self._thresholds['pressure_deviation']:
                direction = "high" if curr_value > baseline_pressure else "low"
                
                # Only add if not already detected as a spike
                if not any(a.get("timestamp") == sorted_readings[i]['timestamp'].isoformat() 
                         for a in result.raw_details["detected_anomalies"]):
                    result.raw_details["detected_anomalies"].append({
                        "measurement_type": "pressure",
                        "anomaly_type": "sustained_" + direction,
                        "timestamp": sorted_readings[i]['timestamp'].isoformat(),
                        "value": curr_value,
                        "baseline": baseline_pressure,
                        "deviation_percent": deviation_percent,
                        "potential_components": ["pressure_valve"] if direction == "high" else ["tank_integrity"],
                        "probability": min(0.9, 0.5 + deviation_percent / 20)
                    })
    
    def _analyze_heating_cycles(self, heating_cycle_data: List[Dict], result: PredictionResult) -> None:
        """
        Analyze heating cycle data for anomalies.
        
        Args:
            heating_cycle_data: List of heating cycle records
            result: PredictionResult to update with findings
        """
        if not heating_cycle_data or len(heating_cycle_data) < 3:
            return
        
        # Sort data by timestamp
        sorted_data = sorted(heating_cycle_data, key=lambda x: x.get('timestamp', x.get('date')))
        
        # Calculate average cycle duration and frequency
        durations = [cycle.get('duration_minutes', 0) for cycle in sorted_data if 'duration_minutes' in cycle]
        
        if durations:
            avg_duration = sum(durations) / len(durations)
            
            # Check the most recent cycles against average
            recent_cycles = sorted_data[-3:]
            recent_durations = [cycle.get('duration_minutes', 0) for cycle in recent_cycles if 'duration_minutes' in cycle]
            
            if recent_durations:
                recent_avg = sum(recent_durations) / len(recent_durations)
                percent_change = (recent_avg / avg_duration - 1) * 100
                
                if abs(percent_change) > self._thresholds['heating_cycle_variation']:
                    cycle_trend = "longer" if percent_change > 0 else "shorter"
                    affected_component = "heating_element" if cycle_trend == "longer" else "thermostat"
                    
                    result.raw_details["trend_analysis"]["heating_cycle"] = {
                        "trend": cycle_trend,
                        "percent_change": percent_change,
                        "component_affected": affected_component,
                        "probability": min(0.9, 0.6 + abs(percent_change) / 30),
                        "days_until_critical": self._estimate_days_until_critical_cycle_change(percent_change)
                    }
    
    def _calculate_days_until_critical(self, current_value: float, rate_of_change: float, 
                                      critical_threshold: float) -> int:
        """
        Calculate days until a measurement reaches a critical threshold based on its rate of change.
        
        Args:
            current_value: The current measurement value
            rate_of_change: The daily rate of change (can be positive or negative)
            critical_threshold: The threshold considered critical
            
        Returns:
            Estimated number of days until critical threshold is reached
        """
        if rate_of_change == 0:
            return 9999  # Effectively never
            
        days = (critical_threshold - current_value) / rate_of_change
        
        # Only return positive values - if already critical or moving away from critical, 
        # this doesn't apply
        if days <= 0:
            return 9999
            
        return int(days)
    
    def _estimate_days_until_critical_cycle_change(self, percent_change: float) -> int:
        """
        Estimate days until heating cycle changes become critical.
        
        Args:
            percent_change: Percent change in cycle duration
            
        Returns:
            Estimated number of days until critical impact
        """
        # Assuming more severe changes progress faster
        severity = abs(percent_change)
        
        if severity < 25:
            return 60
        elif severity < 40:
            return 30
        elif severity < 60:
            return 14
        else:
            return 7
    
    def _generate_recommendations(self, result: PredictionResult) -> None:
        """
        Generate recommended actions based on detected anomalies.
        
        Args:
            result: PredictionResult to update with recommendations
        """
        recommendations = []
        
        # Process temperature trend recommendations
        if "temperature" in result.raw_details["trend_analysis"]:
            temp_trend = result.raw_details["trend_analysis"]["temperature"]
            component = temp_trend["component_affected"]
            probability = temp_trend["probability"]
            days = temp_trend["days_until_critical"]
            
            direction = "increasing" if temp_trend["rate_of_change_per_day"] > 0 else "decreasing"
            
            severity = ActionSeverity.MEDIUM
            if days < 14:
                severity = ActionSeverity.HIGH
            elif days > 45:
                severity = ActionSeverity.LOW
                
            action = RecommendedAction(
                action_id=f"temp_trend_{component}_{datetime.now().strftime('%Y%m%d')}",
                description=f"Investigate {component} due to {direction} temperature trend",
                impact=f"Temperature pattern indicates {probability:.0%} probability of {component} " +
                       f"issues within {days} days",
                expected_benefit=f"Prevent potential {component} failure and extend water heater lifespan",
                severity=severity,
                due_date=datetime.now() + timedelta(days=min(days-5, 30)),
                estimated_cost=75 if component == "thermostat" else 150,
                estimated_duration="1-2 hours"
            )
            recommendations.append(action)
        
        # Process pressure anomaly recommendations
        pressure_anomalies = [a for a in result.raw_details["detected_anomalies"] 
                             if a["measurement_type"] == "pressure"]
        
        if pressure_anomalies:
            # Get the most severe pressure anomaly
            max_probability = max(a["probability"] for a in pressure_anomalies)
            most_severe = next(a for a in pressure_anomalies if a["probability"] == max_probability)
            
            components = most_severe["potential_components"]
            component_text = " and ".join(components)
            anomaly_type = most_severe["anomaly_type"]
            
            due_days = 14
            if max_probability > 0.8:
                severity = ActionSeverity.HIGH
                due_days = 7
            elif max_probability > 0.6:
                severity = ActionSeverity.MEDIUM
            else:
                severity = ActionSeverity.LOW
                due_days = 30
                
            action = RecommendedAction(
                action_id=f"pressure_anom_{components[0]}_{datetime.now().strftime('%Y%m%d')}",
                description=f"Inspect {component_text} due to pressure anomalies",
                impact=f"Unusual pressure readings indicate {max_probability:.0%} probability of " +
                       f"developing {component_text} issues within 2-3 weeks",
                expected_benefit=f"Prevent pressure-related failures and potential water damage",
                severity=severity,
                due_date=datetime.now() + timedelta(days=due_days),
                estimated_cost=100,
                estimated_duration="1-3 hours"
            )
            recommendations.append(action)
        
        # Process heating cycle recommendations
        if "heating_cycle" in result.raw_details["trend_analysis"]:
            cycle_trend = result.raw_details["trend_analysis"]["heating_cycle"]
            component = cycle_trend["component_affected"]
            probability = cycle_trend["probability"]
            days = cycle_trend["days_until_critical"]
            trend = cycle_trend["trend"]
            
            severity = ActionSeverity.MEDIUM
            if days < 14:
                severity = ActionSeverity.HIGH
            elif days > 30:
                severity = ActionSeverity.LOW
                
            action = RecommendedAction(
                action_id=f"heating_cycle_{component}_{datetime.now().strftime('%Y%m%d')}",
                description=f"Check {component} efficiency due to {trend} heating cycles",
                impact=f"Heating cycle anomalies indicate {probability:.0%} probability of " +
                       f"reduced efficiency within {days} days",
                expected_benefit=f"Restore optimal efficiency and reduce energy consumption",
                severity=severity,
                due_date=datetime.now() + timedelta(days=min(days-3, 25)),
                estimated_cost=85,
                estimated_duration="1 hour"
            )
            recommendations.append(action)
        
        # Add recommendations to result
        result.recommended_actions.extend(recommendations)
