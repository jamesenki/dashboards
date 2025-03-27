"""
Service for handling prediction operations
"""
from typing import Dict, Any, Optional
import logging
import os
from datetime import datetime, timedelta

from src.predictions.interfaces import PredictionResult
from src.predictions.maintenance.lifespan_estimation import LifespanEstimationPrediction
from src.predictions.advanced.anomaly_detection import AnomalyDetectionPredictor
from src.predictions.advanced.usage_patterns import UsagePatternPredictor
from src.predictions.advanced.multi_factor import MultiFactorPredictor
from src.services.water_heater import WaterHeaterService

logger = logging.getLogger(__name__)

class PredictionService:
    """
    Service for handling prediction operations across the system
    """
    
    def __init__(self):
        self.water_heater_service = WaterHeaterService()
        
        # Initialize prediction models
        self.prediction_models = {
            "lifespan_estimation": LifespanEstimationPrediction(),
            "anomaly_detection": AnomalyDetectionPredictor(),
            "usage_patterns": UsagePatternPredictor(),
            "multi_factor": MultiFactorPredictor()
        }
        
        # Cache for predictions to avoid unnecessary recalculations
        self._prediction_cache = {}
    
    async def get_prediction(
        self, 
        device_id: str, 
        prediction_type: str,
        force_refresh: bool = False
    ) -> Optional[PredictionResult]:
        """
        Get a prediction for a specific device
        
        Args:
            device_id: ID of the device to get prediction for
            prediction_type: Type of prediction to generate
            force_refresh: If True, invalidate cache and recalculate prediction
            
        Returns:
            PredictionResult if successful, None otherwise
        """
        cache_key = f"{device_id}_{prediction_type}"
        
        # Return cached prediction if available and refresh not requested
        if not force_refresh and cache_key in self._prediction_cache:
            logger.info(f"Returning cached prediction for {cache_key}")
            return self._prediction_cache[cache_key]
        
        # Get the appropriate prediction model
        if prediction_type not in self.prediction_models:
            logger.error(f"Unknown prediction type: {prediction_type}")
            return None
        
        prediction_model = self.prediction_models[prediction_type]
        
        # Get device data for prediction
        device_data = await self._get_device_data(device_id, prediction_type)
        if not device_data:
            logger.error(f"Failed to get device data for prediction: {device_id}")
            return None
        
        # Generate prediction
        try:
            # Default values for the prediction (used for fallback in case of errors)
            default_prediction = self._create_default_prediction(device_id, prediction_type)
            
            # All prediction models should have async predict methods according to IPredictionModel
            # interface, but we need to make sure we await the result properly
            prediction = await prediction_model.predict(device_id, device_data)
            
            # Cache the prediction
            self._prediction_cache[cache_key] = prediction
            
            return prediction
        except Exception as e:
            logger.error(f"Failed to generate prediction for {prediction_type}: {str(e)}")
            # For testing purposes, if we're in development mode, return a default prediction
            # This allows the UI to still function even if the models have issues
            if os.getenv('ENVIRONMENT', 'development') == 'development':
                logger.info(f"Returning default prediction for {prediction_type} in development mode")
                return self._create_default_prediction(device_id, prediction_type)
            return None
    
    def _create_default_prediction(self, device_id: str, prediction_type: str) -> PredictionResult:
        """
        Create a default prediction result for development and testing
        
        Args:
            device_id: ID of the device
            prediction_type: Type of prediction
            
        Returns:
            A default PredictionResult for the given prediction type
        """
        from src.predictions.interfaces import ActionSeverity, RecommendedAction
        
        # Create a basic prediction result with reasonable defaults
        current_time = datetime.now()
        due_date = current_time + timedelta(days=30)
        
        if prediction_type == "anomaly_detection":
            return PredictionResult(
                prediction_type="anomaly_detection",
                device_id=device_id,
                predicted_value=0.01,  # Very low anomaly probability
                confidence=0.95,
                features_used=["telemetry", "expected_ranges"],
                timestamp=current_time,
                recommended_actions=[
                    RecommendedAction(
                        action_id=f"monitor_{device_id}_{current_time.strftime('%Y%m%d')}",
                        description="Monitor system for any unusual behavior",
                        severity=ActionSeverity.LOW,
                        impact="Continued monitoring will ensure early detection of potential issues",
                        expected_benefit="Early detection of potential anomalies",
                        due_date=due_date,
                        estimated_cost=0.0,
                        estimated_duration="15 minutes"
                    )
                ],
                raw_details={
                    "detected_anomalies": [],
                    "trend_analysis": {
                        "temperature": {
                            "trend_direction": "stable",
                            "rate_of_change_per_day": 0.0,
                            "component_affected": "none",
                            "probability": 0.0,
                            "days_until_critical": 999
                        }
                    }
                }
            )
        elif prediction_type == "usage_patterns":
            return PredictionResult(
                prediction_type="usage_pattern",
                device_id=device_id,
                predicted_value=0.5,  # Medium usage
                confidence=0.9,
                features_used=["usage_history", "user_preferences"],
                timestamp=current_time,
                recommended_actions=[],
                raw_details={
                    "usage_patterns": {},
                    "impact_on_components": {
                        "heating_element": {
                            "wear_acceleration_factor": 1.0,
                            "days_until_significant_impact": 180,
                            "efficiency_impact_percent": 0,
                            "contributing_factors": {
                                "usage_level": "normal",
                                "temperature_setting": "medium"
                            }
                        }
                    },
                    "efficiency_projections": {
                        "baseline_decline_rate_yearly": 5.0,
                        "30_day_projected_decline": 0.4
                    },
                    "usage_classification": "normal"
                }
            )
        elif prediction_type == "multi_factor":
            return PredictionResult(
                prediction_type="multi_factor",
                device_id=device_id,
                predicted_value=0.75,  # Good health score
                confidence=0.85,
                features_used=["telemetry_series", "component_health", "maintenance_history"],
                timestamp=current_time,
                recommended_actions=[
                    RecommendedAction(
                        action_id=f"routine_maint_{device_id}_{current_time.strftime('%Y%m%d')}",
                        description="Schedule routine maintenance check",
                        severity=ActionSeverity.MEDIUM,
                        impact="Regular maintenance will extend the lifespan of your water heater",
                        expected_benefit="Improved efficiency and extended equipment life",
                        due_date=due_date,
                        estimated_cost=120.0,
                        estimated_duration="1 hour"
                    )
                ],
                raw_details={
                    "factor_scores": {
                        "water_quality": 0.8,
                        "ambient_conditions": 0.9,
                        "usage_patterns": 0.7,
                        "maintenance_history": 0.6,
                        "component_interactions": 0.8
                    },
                    "component_interactions": [
                        {
                            "components": ["heating_element", "thermostat"],
                            "description": "Normal interaction between heating element and thermostat.",
                            "impact_level": "Low"
                        },
                        {
                            "components": ["anode_rod", "tank_integrity"],
                            "description": "Anode rod is providing normal protection for the tank.",
                            "impact_level": "Low"
                        }
                    ],
                    "environment_impacts": {},
                    "environmental_impact": {},
                    "diagnostic_progression": {},
                    "overall_evaluation": {
                        "health_score": 0.75,
                        "risk_level": "low",
                        "recommended_inspection_interval_days": 90
                    },
                    "combined_factors": True
                }
            )
        else:  # Default for lifespan_estimation or any other type
            return PredictionResult(
                prediction_type=prediction_type,
                device_id=device_id,
                predicted_value=3650.0,  # 10 years in days
                confidence=0.75,
                features_used=["device_specs", "usage_data"],
                timestamp=current_time,
                recommended_actions=[],
                raw_details={}
            )
    
    async def _get_device_data(self, device_id: str, prediction_type: str) -> Optional[Dict[str, Any]]:
        """
        Get device data needed for a specific prediction type
        
        Args:
            device_id: ID of the device to get data for
            prediction_type: Type of prediction to generate
            
        Returns:
            Dict with device data if successful, None otherwise
        """
        # Support different prediction types
        if prediction_type == "lifespan_estimation":
            return await self._get_water_heater_lifespan_data(device_id)
        elif prediction_type in ["anomaly_detection", "usage_patterns", "multi_factor"]:
            # For advanced prediction models, share the same data source with extended features
            return await self._get_advanced_prediction_data(device_id, prediction_type)
        
        logger.error(f"Unknown prediction type for data gathering: {prediction_type}")
        return None
        
    async def _get_advanced_prediction_data(self, device_id: str, prediction_type: str) -> Optional[Dict[str, Any]]:
        """
        Get extended water heater data needed for advanced prediction models
        
        Args:
            device_id: ID of the water heater
            prediction_type: Type of prediction to generate
            
        Returns:
            Dict with advanced water heater data if successful, None otherwise
        """
        # Start with base water heater data
        base_data = await self._get_water_heater_lifespan_data(device_id)
        if not base_data:
            return None
            
        # Get water heater from service for additional details
        water_heater = await self.water_heater_service.get_water_heater(device_id)
        if not water_heater:
            return None
            
        # Add advanced features based on prediction type
        if prediction_type == "anomaly_detection":
            # Add telemetry data with timestamps for pattern recognition
            base_data["telemetry_series"] = [
                {"timestamp": reading.timestamp, 
                 "temperature": reading.temperature,
                 "pressure": reading.pressure,
                 "energy_usage": reading.energy_usage,
                 "flow_rate": reading.flow_rate}
                for reading in water_heater.readings
            ]
            
            # Add expected operating ranges
            base_data["expected_ranges"] = {
                "temperature": (water_heater.min_temperature, water_heater.max_temperature),
                "pressure": (1.0, 3.5),  # Normal pressure range in bar
                "energy_usage": (0, 3000)  # Normal energy usage range in watts
            }
            
        elif prediction_type == "usage_patterns":
            # Add usage pattern data
            # Convert the readings objects to dictionaries for consistent processing
            base_data["usage_history"] = [
                {"timestamp": reading.timestamp, 
                 "temperature": reading.temperature,
                 "pressure": reading.pressure,
                 "energy_usage": reading.energy_usage,
                 "flow_rate": reading.flow_rate}
                for reading in water_heater.readings
            ]
            base_data["installation_location"] = getattr(water_heater, "location", "Unknown")
            base_data["user_preferences"] = {
                "target_temperature": water_heater.target_temperature,
                "mode": getattr(water_heater, "mode", "AUTO")
            }
            
        elif prediction_type == "multi_factor":
            # Include all available data for multi-factor analysis
            base_data["telemetry_series"] = [
                {"timestamp": reading.timestamp, 
                 "temperature": reading.temperature,
                 "pressure": reading.pressure,
                 "energy_usage": reading.energy_usage,
                 "flow_rate": reading.flow_rate}
                for reading in water_heater.readings
            ]
            base_data["installation_location"] = getattr(water_heater, "location", "Unknown")
            base_data["heater_type"] = getattr(water_heater, "heater_type", "Residential")
            base_data["status"] = getattr(water_heater, "status", "ONLINE")
            base_data["efficiency_rating"] = getattr(water_heater, "efficiency_rating", 0.9)
            
        return base_data
    
    async def _get_water_heater_lifespan_data(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get water heater data needed for lifespan prediction
        
        Args:
            device_id: ID of the water heater
            
        Returns:
            Dict with water heater data if successful, None otherwise
        """
        # Get water heater from service
        water_heater = await self.water_heater_service.get_water_heater(device_id)
        if not water_heater:
            return None
        
        # Get history data - handle case where get_history method doesn't exist
        try:
            if hasattr(self.water_heater_service, 'get_history'):
                history = await self.water_heater_service.get_history(device_id)
            else:
                # Fallback to default history when method isn't available
                logger.info(f"get_history method not available, using default history for {device_id}")
                history = []
        except Exception as e:
            logger.error(f"Error getting history data: {str(e)}")
            history = []
        
        # Construct features for prediction
        features = {
            "device_id": device_id,
            "installation_date": getattr(water_heater, 'installation_date', None),
            "model": getattr(water_heater, 'model_name', water_heater.name),  # Use name as fallback
            "temperature_settings": water_heater.target_temperature,
            "total_operation_hours": getattr(water_heater, 'total_operation_hours', 8760),  # Default to 1 year if not available
            "water_hardness": getattr(water_heater, 'water_hardness', 7.0),  # Default to medium hardness if not available
            "efficiency_degradation_rate": 0.05,  # Default value, can be calculated from history
        }
        
        # Add component health if available
        if hasattr(water_heater, "component_health") and water_heater.component_health:
            features["component_health"] = water_heater.component_health
        
        # Add maintenance history if available
        if hasattr(water_heater, "maintenance_history") and water_heater.maintenance_history:
            features["maintenance_history"] = water_heater.maintenance_history
        
        # Add usage patterns from history data if available
        if history:
            # Calculate average daily cycles
            if len(history) >= 7:  # At least a week of data
                # This is simplified - in a real system, we'd do more sophisticated analysis
                features["heating_cycles_per_day"] = len(history) / 7
                
                # Calculate average usage intensity based on temperature fluctuations
                if "temperature_readings" in history[0]:
                    temp_variations = [
                        max(day["temperature_readings"]) - min(day["temperature_readings"])
                        for day in history if "temperature_readings" in day and day["temperature_readings"]
                    ]
                    if temp_variations:
                        avg_variation = sum(temp_variations) / len(temp_variations)
                        features["usage_intensity"] = avg_variation / 10  # Normalize to 0-1 scale
        
        return features
