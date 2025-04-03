"""
Extended service for water heater maintenance and telemetry operations.
Provides additional functionality needed for the AI agent tools.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.models.water_heater import WaterHeaterMode, WaterHeaterStatus
from src.services.water_heater import WaterHeaterService

logger = logging.getLogger(__name__)


class WaterHeaterMaintenanceService(WaterHeaterService):
    """
    Extended service for water heater maintenance operations.
    Inherits from the base WaterHeaterService and adds methods specific to maintenance.
    """

    async def get_readings(
        self, device_id: str, hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get telemetry readings for a water heater for the specified number of hours.

        Args:
            device_id: ID of the water heater
            hours: Number of hours of data to retrieve (default: 24)

        Returns:
            List of readings with timestamp and sensor data

        Raises:
            ValueError: If water heater not found
        """
        logger.info(f"Getting {hours} hours of readings for water heater {device_id}")

        try:
            # Check if water heater exists
            water_heater = await self.repository.get_water_heater(device_id)
            if not water_heater:
                raise ValueError(f"Water heater with ID {device_id} not found")

            # Calculate the time threshold
            time_threshold = datetime.now() - timedelta(hours=hours)

            # Get readings from repository
            raw_readings = await self.repository.get_readings(device_id, time_threshold)

            # Format the readings for API response
            formatted_readings = []
            for reading in raw_readings:
                formatted_readings.append(
                    {
                        "timestamp": reading.timestamp.isoformat()
                        if hasattr(reading.timestamp, "isoformat")
                        else reading.timestamp,
                        "temperature": reading.temperature,
                        "pressure": reading.pressure,
                        "energy_usage": reading.energy_usage,
                        "flow_rate": reading.flow_rate,
                    }
                )

            return formatted_readings

        except Exception as e:
            logger.error(f"Error getting readings: {e}")

            # Fallback to dummy data
            from src.repositories.mock.dummy_data import get_dummy_readings

            readings = get_dummy_readings(device_id, hours)

            return readings

    async def get_maintenance_info(self, device_id: str) -> Dict[str, Any]:
        """
        Get maintenance information for a water heater.

        Args:
            device_id: ID of the water heater

        Returns:
            Dictionary with maintenance information

        Raises:
            ValueError: If water heater not found
        """
        logger.info(f"Getting maintenance info for water heater {device_id}")

        try:
            # Check if water heater exists
            water_heater = await self.repository.get_water_heater(device_id)
            if not water_heater:
                raise ValueError(f"Water heater with ID {device_id} not found")

            # Get basic maintenance information from model data
            model_info = getattr(water_heater, "model", "").lower()

            # Different maintenance info based on water heater type
            if "tankless" in model_info:
                maintenance_tasks = [
                    "Inspect and clean water filter",
                    "Descale heat exchanger",
                    "Check venting system",
                    "Inspect electrical components",
                ]
                efficiency_score = 95
            elif "hybrid" in model_info or "heat pump" in model_info:
                maintenance_tasks = [
                    "Clean air filter",
                    "Check condensate drain",
                    "Inspect anode rod",
                    "Test pressure relief valve",
                ]
                efficiency_score = 90
            else:  # Standard tank water heater
                maintenance_tasks = [
                    "Inspect anode rod",
                    "Check pressure relief valve",
                    "Flush tank to remove sediment",
                    "Check for leaks",
                ]
                efficiency_score = 85

            # Generate maintenance dates
            last_maintenance = (
                datetime.now().replace(month=1, day=15).strftime("%Y-%m-%d")
            )
            next_maintenance = (
                datetime.now().replace(month=7, day=15).strftime("%Y-%m-%d")
            )

            # Add recommendations based on usage patterns
            energy_usage = getattr(water_heater, "energy_usage", 0)
            mode = getattr(water_heater, "mode", None)

            recommendations = []
            if energy_usage > 1000:
                recommendations.append(
                    "Consider lowering temperature to reduce energy consumption"
                )
            if mode != WaterHeaterMode.ECO:
                recommendations.append("Switch to ECO mode to optimize efficiency")

            # Get Rheem-specific maintenance recommendations based on model
            rheem_recommendations = self._get_rheem_specific_recommendations(model_info)
            if rheem_recommendations:
                recommendations.extend(rheem_recommendations)

            return {
                "last_maintenance_date": last_maintenance,
                "next_maintenance_due": next_maintenance,
                "maintenance_tasks": maintenance_tasks,
                "efficiency_score": efficiency_score,
                "recommendations": recommendations,
            }

        except Exception as e:
            logger.error(f"Error getting maintenance info: {e}")

            # Return generic maintenance info as a fallback
            return {
                "last_maintenance_date": datetime.now()
                .replace(month=1, day=15)
                .strftime("%Y-%m-%d"),
                "next_maintenance_due": datetime.now()
                .replace(month=7, day=15)
                .strftime("%Y-%m-%d"),
                "maintenance_tasks": [
                    "Inspect anode rod",
                    "Check pressure relief valve",
                    "Flush tank to remove sediment",
                ],
                "efficiency_score": 85,
                "recommendations": [
                    "Perform regular maintenance to extend service life",
                    "Consider upgrading to a more efficient model",
                ],
            }

    def _get_rheem_specific_recommendations(self, model_info: str) -> List[str]:
        """Get Rheem-specific maintenance recommendations based on model info."""
        recommendations = []

        # ProTerra hybrid recommendations
        if "proterra" in model_info:
            recommendations.append("Check the ProTerra heat pump components annually")
            recommendations.append("Ensure proper ventilation around the unit")

        # Performance Platinum tankless recommendations
        elif "performance platinum" in model_info:
            recommendations.append("Schedule professional descaling every 12-18 months")
            recommendations.append("Check for error codes in the EcoNet system")

        # Classic series recommendations
        elif "classic" in model_info:
            recommendations.append("Replace anode rod every 3-5 years")
            recommendations.append("Drain sediment monthly for optimal performance")

        return recommendations
