"""
Service for handling water heater history data
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

from src.services.water_heater import WaterHeaterService

class WaterHeaterHistoryService:
    """Service for managing water heater history data"""
    
    async def get_temperature_history(self, heater_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Get temperature history data for a water heater
        
        Args:
            heater_id: ID of the water heater
            days: Number of days of history to retrieve (default: 7)
            
        Returns:
            Chart data for temperature history
        """
        # Get the water heater
        water_heater_service = WaterHeaterService()
        heater = await water_heater_service.get_water_heater(heater_id)
        
        # Filter readings to the specified time period
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_readings = [r for r in heater.readings if r.timestamp >= cutoff_date]
        
        # Sort readings by timestamp
        sorted_readings = sorted(filtered_readings, key=lambda r: r.timestamp)
        
        # Prepare chart data
        labels = [r.timestamp.strftime("%m/%d %H:%M") for r in sorted_readings]
        temperature_data = [r.temperature for r in sorted_readings]
        
        # Add target temperature as a separate line
        target_temperature_data = [heater.target_temperature] * len(labels)
        
        # Prepare datasets
        datasets = [
            {
                "label": "Temperature (°C)",
                "data": temperature_data,
                "borderColor": "#FF6384",
                "backgroundColor": "rgba(255, 99, 132, 0.2)",
                "borderWidth": 2,
                "fill": False,
                "tension": 0.4
            },
            {
                "label": "Target Temperature (°C)",
                "data": target_temperature_data,
                "borderColor": "#36A2EB",
                "backgroundColor": "rgba(54, 162, 235, 0.2)",
                "borderWidth": 2,
                "borderDash": [5, 5],
                "fill": False,
                "tension": 0
            }
        ]
        
        return {
            "labels": labels,
            "datasets": datasets
        }
    
    async def get_energy_usage_history(self, heater_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Get energy usage history data for a water heater
        
        Args:
            heater_id: ID of the water heater
            days: Number of days of history to retrieve (default: 7)
            
        Returns:
            Chart data for energy usage history
        """
        # Get the water heater
        water_heater_service = WaterHeaterService()
        heater = await water_heater_service.get_water_heater(heater_id)
        
        # Filter readings to the specified time period
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_readings = [r for r in heater.readings if r.timestamp >= cutoff_date]
        
        # Sort readings by timestamp
        sorted_readings = sorted(filtered_readings, key=lambda r: r.timestamp)
        
        # Prepare chart data
        labels = [r.timestamp.strftime("%m/%d %H:%M") for r in sorted_readings]
        energy_data = [r.energy_usage for r in sorted_readings]
        
        # Prepare datasets
        datasets = [
            {
                "label": "Energy Usage (W)",
                "data": energy_data,
                "borderColor": "#4BC0C0",
                "backgroundColor": "rgba(75, 192, 192, 0.2)",
                "borderWidth": 2,
                "fill": True,
                "tension": 0.4
            }
        ]
        
        return {
            "labels": labels,
            "datasets": datasets
        }
    
    async def get_pressure_flow_history(self, heater_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Get pressure and flow rate history data for a water heater
        
        Args:
            heater_id: ID of the water heater
            days: Number of days of history to retrieve (default: 7)
            
        Returns:
            Chart data for pressure and flow rate history
        """
        # Get the water heater
        water_heater_service = WaterHeaterService()
        heater = await water_heater_service.get_water_heater(heater_id)
        
        # Filter readings to the specified time period
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_readings = [r for r in heater.readings if r.timestamp >= cutoff_date]
        
        # Sort readings by timestamp
        sorted_readings = sorted(filtered_readings, key=lambda r: r.timestamp)
        
        # Prepare chart data
        labels = [r.timestamp.strftime("%m/%d %H:%M") for r in sorted_readings]
        pressure_data = [r.pressure for r in sorted_readings]
        flow_data = [r.flow_rate for r in sorted_readings]
        
        # Prepare datasets
        datasets = [
            {
                "label": "Pressure (bar)",
                "data": pressure_data,
                "borderColor": "#FFCD56",
                "backgroundColor": "rgba(255, 205, 86, 0.2)",
                "borderWidth": 2,
                "fill": False,
                "tension": 0.4,
                "yAxisID": "y"
            },
            {
                "label": "Flow Rate (L/min)",
                "data": flow_data,
                "borderColor": "#9966FF",
                "backgroundColor": "rgba(153, 102, 255, 0.2)",
                "borderWidth": 2,
                "fill": False,
                "tension": 0.4,
                "yAxisID": "y1"
            }
        ]
        
        return {
            "labels": labels,
            "datasets": datasets
        }
    
    async def get_history_dashboard(self, heater_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Get complete history dashboard data for a water heater
        
        Args:
            heater_id: ID of the water heater
            days: Number of days of history to retrieve (default: 7)
            
        Returns:
            Complete history dashboard data
        """
        # Get all chart data
        temperature_history = await self.get_temperature_history(heater_id, days)
        energy_usage_history = await self.get_energy_usage_history(heater_id, days)
        pressure_flow_history = await self.get_pressure_flow_history(heater_id, days)
        
        # Return combined dashboard data
        return {
            "temperature": temperature_history,
            "energy_usage": energy_usage_history,
            "pressure_flow": pressure_flow_history
        }
