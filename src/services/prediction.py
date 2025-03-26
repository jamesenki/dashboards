"""
Service for handling prediction operations
"""
from typing import Dict, Any, Optional
import logging

from src.predictions.interfaces import PredictionResult
from src.predictions.maintenance.lifespan_estimation import LifespanEstimationPrediction
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
            "lifespan_estimation": LifespanEstimationPrediction()
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
            prediction = await prediction_model.predict(device_id, device_data)
            
            # Cache the prediction
            self._prediction_cache[cache_key] = prediction
            
            return prediction
        except Exception as e:
            logger.error(f"Failed to generate prediction: {str(e)}")
            return None
    
    async def _get_device_data(self, device_id: str, prediction_type: str) -> Optional[Dict[str, Any]]:
        """
        Get device data needed for a specific prediction type
        
        Args:
            device_id: ID of the device to get data for
            prediction_type: Type of prediction to generate
            
        Returns:
            Dict with device data if successful, None otherwise
        """
        # Currently only water heater predictions are supported
        if prediction_type == "lifespan_estimation":
            return await self._get_water_heater_lifespan_data(device_id)
        
        logger.error(f"Unknown prediction type for data gathering: {prediction_type}")
        return None
    
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
