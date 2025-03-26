"""
Water heater operations service for retrieving and processing operations data
"""
from typing import Dict, Any, List
from datetime import datetime

from src.services.water_heater import WaterHeaterService


class WaterHeaterOperationsService:
    """Service for water heater operations data retrieval and processing."""
    
    def __init__(self):
        """Initialize the service."""
        self.water_heater_service = WaterHeaterService()
    
    async def get_operations_dashboard(self, heater_id: str) -> Dict[str, Any]:
        """
        Retrieve and process operations dashboard data for a water heater.
        
        Args:
            heater_id: ID of the water heater to get data for
            
        Returns:
            Dictionary containing formatted operations dashboard data
        """
        # Get water heater data
        water_heater = await self.water_heater_service.get_water_heater(heater_id)
        
        if not water_heater:
            return None
        
        # Get the latest reading
        latest_reading = water_heater.readings[-1] if water_heater.readings else None
        
        # Prepare dashboard data
        dashboard_data = {
            "machine_status": water_heater.status.value,
            "heater_status": water_heater.heater_status.value,
            "current_temperature": water_heater.current_temperature,
            "target_temperature": water_heater.target_temperature,
            "mode": water_heater.mode.value,
            "gauges": {}
        }
        
        # Process gauge data
        dashboard_data["gauges"]["temperature"] = self._transform_temperature_gauge_data(
            water_heater.current_temperature,
            water_heater.target_temperature,
            water_heater.min_temperature,
            water_heater.max_temperature
        )
        
        # Process other gauge data if we have readings
        if latest_reading:
            dashboard_data["gauges"]["pressure"] = self._transform_pressure_gauge_data(
                latest_reading.pressure if latest_reading.pressure is not None else 0.0
            )
            
            dashboard_data["gauges"]["energy_usage"] = self._transform_energy_usage_gauge_data(
                latest_reading.energy_usage if latest_reading.energy_usage is not None else 0
            )
            
            dashboard_data["gauges"]["flow_rate"] = self._transform_flow_rate_gauge_data(
                latest_reading.flow_rate if latest_reading.flow_rate is not None else 0.0
            )
        
        # Calculate and add asset health
        dashboard_data["asset_health"] = self._calculate_asset_health(
            water_heater.current_temperature,
            water_heater.target_temperature,
            latest_reading.pressure if latest_reading and latest_reading.pressure is not None else 0.0,
            latest_reading.energy_usage if latest_reading and latest_reading.energy_usage is not None else 0,
            latest_reading.flow_rate if latest_reading and latest_reading.flow_rate is not None else 0.0
        )
        
        return dashboard_data
    
    def _transform_temperature_gauge_data(
        self, current_temp: float, target_temp: float, min_temp: float, max_temp: float
    ) -> Dict[str, Any]:
        """
        Transform temperature data for gauge display.
        
        Args:
            current_temp: Current temperature reading
            target_temp: Target temperature setting
            min_temp: Minimum allowed temperature
            max_temp: Maximum allowed temperature
            
        Returns:
            Formatted gauge data
        """
        # Calculate percentage for gauge display (based on range)
        if max_temp == min_temp:  # Avoid division by zero
            percentage = 0
        else:
            percentage = round(((current_temp - min_temp) / (max_temp - min_temp)) * 100, 1)
        
        return {
            "value": current_temp,
            "min": min_temp,
            "max": max_temp,
            "unit": "°C",
            "percentage": percentage,
            "target": target_temp
        }
    
    def _transform_pressure_gauge_data(self, current_pressure: float) -> Dict[str, Any]:
        """
        Transform pressure data for gauge display.
        
        Args:
            current_pressure: Current pressure reading in bar
            
        Returns:
            Formatted gauge data
        """
        # Define range for pressure (typical range 0-5 bar for residential systems)
        min_pressure = 0.0
        max_pressure = 5.0
        
        # Calculate percentage for gauge display
        percentage = round((current_pressure / max_pressure) * 100, 1)
        
        return {
            "value": current_pressure,
            "min": min_pressure,
            "max": max_pressure,
            "unit": "bar",
            "percentage": percentage
        }
    
    def _transform_energy_usage_gauge_data(self, current_energy: float) -> Dict[str, Any]:
        """
        Transform energy usage data for gauge display.
        
        Args:
            current_energy: Current energy usage in watts
            
        Returns:
            Formatted gauge data
        """
        # Define range for energy usage (typical range 0-3000W for residential systems)
        min_energy = 0
        max_energy = 3000
        
        # Calculate percentage for gauge display
        percentage = round((current_energy / max_energy) * 100, 1)
        
        return {
            "value": current_energy,
            "min": min_energy,
            "max": max_energy,
            "unit": "W",
            "percentage": percentage
        }
    
    def _transform_flow_rate_gauge_data(self, current_flow_rate: float) -> Dict[str, Any]:
        """
        Transform flow rate data for gauge display.
        
        Args:
            current_flow_rate: Current flow rate in liters per minute
            
        Returns:
            Formatted gauge data
        """
        # Define range for flow rate (typical range 0-10 L/min for residential systems)
        min_flow_rate = 0.0
        max_flow_rate = 10.0
        
        # Calculate percentage for gauge display
        percentage = round((current_flow_rate / max_flow_rate) * 100, 1)
        
        return {
            "value": current_flow_rate,
            "min": min_flow_rate,
            "max": max_flow_rate,
            "unit": "L/min",
            "percentage": percentage
        }
    
    def _calculate_asset_health(
        self, temperature: float, target_temperature: float, 
        pressure: float, energy_usage: float, flow_rate: float
    ) -> float:
        """
        Calculate overall asset health score based on sensor readings.
        
        Args:
            temperature: Current temperature reading
            target_temperature: Target temperature setting
            pressure: Current pressure reading
            energy_usage: Current energy usage
            flow_rate: Current flow rate
            
        Returns:
            Asset health score (0-100)
        """
        # Initialize health score at 100 (perfect health)
        health_score = 100.0
        
        # Deduct points based on how far temperature is from target
        temp_diff = abs(temperature - target_temperature)
        if temp_diff > 10:
            health_score -= 30
        elif temp_diff > 5:
            health_score -= 15
        elif temp_diff > 2:
            health_score -= 5
        
        # Deduct points for abnormal pressure (too low or too high)
        if pressure < 1.0 or pressure > 4.0:
            health_score -= 15
        elif pressure < 1.5 or pressure > 3.5:
            health_score -= 5
        
        # Deduct points for high energy usage
        if energy_usage > 2500:
            health_score -= 20
        elif energy_usage > 2000:
            health_score -= 10
        
        # Deduct points for abnormal flow rate
        if flow_rate < 1.0 or flow_rate > 8.0:
            health_score -= 10
        
        # Ensure health score is between 0 and 100
        return max(0, min(100, health_score))
