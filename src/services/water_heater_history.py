"""
Service for handling water heater history data
"""
import logging
import math
import os
import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from src.services.water_heater import WaterHeaterService


class WaterHeaterHistoryService:
    """Service for managing water heater history data"""

    async def get_temperature_history(
        self, heater_id: str, days: int = 7
    ) -> Dict[str, Any]:
        """
        Get temperature history data for a water heater

        Args:
            heater_id: ID of the water heater
            days: Number of days of history to retrieve (default: 7)

        Returns:
            Chart data for temperature history
        """
        try:
            # Import the shadow service here to avoid circular imports
            from src.services.device_shadow import DeviceShadowService

            # Get device shadow service
            shadow_service = DeviceShadowService()

            try:
                # Get the shadow and shadow history
                shadow = await shadow_service.get_device_shadow(heater_id)
                shadow_history = await shadow_service.get_shadow_history(
                    heater_id, limit=100
                )

                # Filter history to the specified time period
                # Use timezone-aware datetime to avoid comparison issues
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                filtered_history = []

                for entry in shadow_history:
                    try:
                        # Parse the timestamp and ensure it's timezone-aware
                        entry_time = datetime.fromisoformat(
                            entry["timestamp"].replace("Z", "+00:00")
                        )
                        # Ensure both datetimes are timezone-aware for comparison
                        if (
                            entry_time >= cutoff_date
                            and "reported" in entry
                            and "temperature" in entry["reported"]
                        ):
                            filtered_history.append(
                                {
                                    "temperature": entry["reported"]["temperature"],
                                    "timestamp": entry_time,
                                }
                            )
                    except Exception as e:
                        logging.error(f"Error parsing timestamp: {e}")

                # Sort by timestamp (oldest first)
                filtered_history.sort(key=lambda x: x["timestamp"])

                # Return mock data if no shadow history found
                if not filtered_history:
                    if os.getenv("IOTSPHERE_ENV", "development") == "development":
                        logging.info(
                            f"No shadow history found, generating mock temperature history for {heater_id}"
                        )
                        return self._generate_mock_temperature_history(heater_id, days)
                    return None

                # Prepare chart data
                labels = [
                    entry["timestamp"].strftime("%m/%d %H:%M")
                    for entry in filtered_history
                ]
                temperature_data = [entry["temperature"] for entry in filtered_history]

                # Add target temperature as a separate line
                # Get target temperature from current shadow if available
                target_temperature = 120  # Default
                if (
                    shadow
                    and "desired" in shadow
                    and "target_temperature" in shadow["desired"]
                ):
                    target_temperature = shadow["desired"]["target_temperature"]
                elif (
                    shadow
                    and "reported" in shadow
                    and "target_temperature" in shadow["reported"]
                ):
                    target_temperature = shadow["reported"]["target_temperature"]

                target_temperature_data = [target_temperature] * len(labels)

                # Prepare datasets
                datasets = [
                    {
                        "label": "Temperature (°C)",
                        "data": temperature_data,
                        "borderColor": "#FF6384",
                        "backgroundColor": "rgba(255, 99, 132, 0.2)",
                        "borderWidth": 2,
                        "fill": False,
                        "tension": 0.4,
                    },
                    {
                        "label": "Target Temperature (°C)",
                        "data": target_temperature_data,
                        "borderColor": "#36A2EB",
                        "backgroundColor": "rgba(54, 162, 235, 0.2)",
                        "borderWidth": 2,
                        "borderDash": [5, 5],
                        "fill": False,
                        "tension": 0,
                    },
                ]

                # Format data for chart with source information
                chart_data = {
                    "labels": labels,
                    "datasets": datasets,
                    "source": "device_shadow",
                }

                return chart_data

            except ValueError as e:
                # Shadow document doesn't exist error - provide informative error
                logging.error(f"Shadow document error for {heater_id}: {str(e)}")
                # Re-raise to allow proper error handling in the API
                raise ValueError(f"No shadow document exists for device {heater_id}")

        except Exception as e:
            logging.error(
                f"Error getting temperature history for {heater_id}: {str(e)}"
            )
            # Return mock data in development mode on error
            if os.getenv("IOTSPHERE_ENV", "development") == "development":
                logging.info(
                    f"Falling back to mock temperature history for {heater_id} due to error"
                )
                return self._generate_mock_temperature_history(heater_id, days)
            return None

    def _generate_mock_temperature_history(
        self, heater_id: str, days: int
    ) -> Dict[str, Any]:
        """
        Generate mock temperature history data for development mode

        Args:
            heater_id: ID of the water heater
            days: Number of days of history to retrieve

        Returns:
            Mock chart data for temperature history
        """
        current_time = datetime.now()
        labels = []
        temperature_data = []
        target_temperature_data = []

        # Base values
        base_temp = 120.0
        target_temp = 125.0

        # Generate data points (one per hour for requested days)
        hours = days * 24
        for i in range(hours):
            # Calculate timestamp (going backwards from now)
            point_time = current_time - timedelta(hours=hours - i)
            labels.append(point_time.strftime("%m/%d %H:%M"))

            # Add daily cycle (hotter during day, cooler at night)
            hour = point_time.hour
            time_factor = (
                math.sin(hour * math.pi / 12) * 3
            )  # ±3 degree variation by time of day

            # Add some randomness
            random_factor = random.uniform(-1.5, 1.5)

            # Calculate temperature
            temp = base_temp + time_factor + random_factor
            temperature_data.append(round(temp, 1))

            # Target temperature is constant
            target_temperature_data.append(target_temp)

        # Prepare datasets
        datasets = [
            {
                "label": "Temperature (°C)",
                "data": temperature_data,
                "borderColor": "#FF6384",
                "backgroundColor": "rgba(255, 99, 132, 0.2)",
                "borderWidth": 2,
                "fill": False,
                "tension": 0.4,
            },
            {
                "label": "Target Temperature (°C)",
                "data": target_temperature_data,
                "borderColor": "#36A2EB",
                "backgroundColor": "rgba(54, 162, 235, 0.2)",
                "borderWidth": 2,
                "borderDash": [5, 5],
                "fill": False,
                "tension": 0,
            },
        ]

        return {"labels": labels, "datasets": datasets}

    async def get_energy_usage_history(
        self, heater_id: str, days: int = 7
    ) -> Dict[str, Any]:
        """
        Get energy usage history data for a water heater

        Args:
            heater_id: ID of the water heater
            days: Number of days of history to retrieve (default: 7)

        Returns:
            Chart data for energy usage history
        """
        try:
            # Get the water heater
            water_heater_service = WaterHeaterService()
            heater = await water_heater_service.get_water_heater(heater_id)

            if not heater or not hasattr(heater, "readings") or not heater.readings:
                # Return mock data in development mode
                if os.getenv("IOTSPHERE_ENV", "development") == "development":
                    logging.info(
                        f"Generating mock energy usage history for {heater_id}"
                    )
                    return self._generate_mock_energy_history(heater_id, days)
                return None

            # Filter readings to the specified time period
            cutoff_date = datetime.now() - timedelta(days=days)
            filtered_readings = [
                r for r in heater.readings if r.timestamp >= cutoff_date
            ]

            if not filtered_readings:
                # Return mock data in development mode if no readings found
                if os.getenv("IOTSPHERE_ENV", "development") == "development":
                    logging.info(
                        f"No readings found, generating mock energy usage history for {heater_id}"
                    )
                    return self._generate_mock_energy_history(heater_id, days)
                return None

            # Sort readings by timestamp
            sorted_readings = sorted(filtered_readings, key=lambda r: r.timestamp)

            # Prepare chart data
            labels = [r.timestamp.strftime("%m/%d %H:%M") for r in sorted_readings]
            energy_data = [
                getattr(r, "energy_usage", 0) for r in sorted_readings
            ]  # Default to 0 if not set

            # Prepare datasets
            datasets = [
                {
                    "label": "Energy Usage (W)",
                    "data": energy_data,
                    "borderColor": "#4BC0C0",
                    "backgroundColor": "rgba(75, 192, 192, 0.2)",
                    "borderWidth": 2,
                    "fill": True,
                    "tension": 0.4,
                }
            ]

            return {"labels": labels, "datasets": datasets}
        except Exception as e:
            logging.error(
                f"Error getting energy usage history for {heater_id}: {str(e)}"
            )
            # Return mock data in development mode on error
            if os.getenv("IOTSPHERE_ENV", "development") == "development":
                logging.info(
                    f"Falling back to mock energy usage history for {heater_id} due to error"
                )
                return self._generate_mock_energy_history(heater_id, days)
            return None

    def _generate_mock_energy_history(
        self, heater_id: str, days: int
    ) -> Dict[str, Any]:
        """
        Generate mock energy usage history data for development mode

        Args:
            heater_id: ID of the water heater
            days: Number of days of history to retrieve

        Returns:
            Mock chart data for energy usage history
        """
        current_time = datetime.now()
        labels = []
        energy_data = []

        # Base values with daily and weekly patterns
        base_energy = 4000.0  # Base energy in watts

        # Generate data points (one per hour for requested days)
        hours = days * 24
        for i in range(hours):
            # Calculate timestamp (going backwards from now)
            point_time = current_time - timedelta(hours=hours - i)
            labels.append(point_time.strftime("%m/%d %H:%M"))

            # Add daily cycle (more usage in morning and evening)
            hour = point_time.hour
            # Lower usage at night (0-5), peaks at morning (6-9) and evening (17-22)
            if 0 <= hour < 5:  # Night
                time_factor = 0.6  # 60% of base
            elif 6 <= hour < 9:  # Morning peak
                time_factor = 1.4  # 140% of base
            elif 17 <= hour < 22:  # Evening peak
                time_factor = 1.3  # 130% of base
            else:  # Normal daytime
                time_factor = 1.0  # 100% of base

            # Add weekly pattern (more usage on weekends)
            day_of_week = point_time.weekday()  # 0-6 (Monday-Sunday)
            if day_of_week >= 5:  # Weekend
                day_factor = 1.2  # 120% usage on weekends
            else:
                day_factor = 1.0

            # Add some randomness (±10% variation)
            random_factor = random.uniform(0.9, 1.1)

            # Calculate energy usage
            energy = base_energy * time_factor * day_factor * random_factor
            energy_data.append(round(energy, 1))

        # Prepare datasets
        datasets = [
            {
                "label": "Energy Usage (W)",
                "data": energy_data,
                "borderColor": "#4BC0C0",
                "backgroundColor": "rgba(75, 192, 192, 0.2)",
                "borderWidth": 2,
                "fill": True,
                "tension": 0.4,
            }
        ]

        return {"labels": labels, "datasets": datasets}

    async def get_pressure_flow_history(
        self, heater_id: str, days: int = 7
    ) -> Dict[str, Any]:
        """
        Get pressure and flow rate history data for a water heater

        Args:
            heater_id: ID of the water heater
            days: Number of days of history to retrieve (default: 7)

        Returns:
            Chart data for pressure and flow rate history
        """
        try:
            # Get the water heater
            water_heater_service = WaterHeaterService()
            heater = await water_heater_service.get_water_heater(heater_id)

            if not heater or not hasattr(heater, "readings") or not heater.readings:
                # Return mock data in development mode
                if os.getenv("IOTSPHERE_ENV", "development") == "development":
                    logging.info(
                        f"Generating mock pressure flow history for {heater_id}"
                    )
                    return self._generate_mock_pressure_flow_history(heater_id, days)
                return None

            # Filter readings to the specified time period
            cutoff_date = datetime.now() - timedelta(days=days)
            filtered_readings = [
                r for r in heater.readings if r.timestamp >= cutoff_date
            ]

            if not filtered_readings:
                # Return mock data in development mode if no readings found
                if os.getenv("IOTSPHERE_ENV", "development") == "development":
                    logging.info(
                        f"No readings found, generating mock pressure flow history for {heater_id}"
                    )
                    return self._generate_mock_pressure_flow_history(heater_id, days)
                return None

            # Sort readings by timestamp
            sorted_readings = sorted(filtered_readings, key=lambda r: r.timestamp)

            # Prepare chart data
            labels = [r.timestamp.strftime("%m/%d %H:%M") for r in sorted_readings]
            pressure_data = [
                getattr(r, "pressure", 0) for r in sorted_readings
            ]  # Default to 0 if not set
            flow_data = [
                getattr(r, "flow_rate", 0) for r in sorted_readings
            ]  # Default to 0 if not set

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
                    "yAxisID": "y",
                },
                {
                    "label": "Flow Rate (L/min)",
                    "data": flow_data,
                    "borderColor": "#9966FF",
                    "backgroundColor": "rgba(153, 102, 255, 0.2)",
                    "borderWidth": 2,
                    "fill": False,
                    "tension": 0.4,
                    "yAxisID": "y1",
                },
            ]

            return {"labels": labels, "datasets": datasets}
        except Exception as e:
            logging.error(
                f"Error getting pressure flow history for {heater_id}: {str(e)}"
            )
            # Return mock data in development mode on error
            if os.getenv("IOTSPHERE_ENV", "development") == "development":
                logging.info(
                    f"Falling back to mock pressure flow history for {heater_id} due to error"
                )
                return self._generate_mock_pressure_flow_history(heater_id, days)
            return None

    def _generate_mock_pressure_flow_history(
        self, heater_id: str, days: int
    ) -> Dict[str, Any]:
        """
        Generate mock pressure and flow rate history data for development mode

        Args:
            heater_id: ID of the water heater
            days: Number of days of history to retrieve

        Returns:
            Mock chart data for pressure and flow rate history
        """
        current_time = datetime.now()
        labels = []
        pressure_data = []
        flow_data = []

        # Base values
        base_pressure = 2.5  # Base pressure in bar
        base_flow = 12.0  # Base flow rate in L/min

        # Generate data points (one per hour for requested days)
        hours = days * 24
        for i in range(hours):
            # Calculate timestamp (going backwards from now)
            point_time = current_time - timedelta(hours=hours - i)
            labels.append(point_time.strftime("%m/%d %H:%M"))

            # Add daily cycle (more usage/pressure in morning and evening)
            hour = point_time.hour
            # Usage patterns affect both pressure and flow
            if 6 <= hour < 9:  # Morning usage
                pressure_factor = 0.9  # Pressure drops with usage
                flow_factor = 1.8  # Flow increases with usage
            elif 17 <= hour < 22:  # Evening usage
                pressure_factor = 0.85  # Pressure drops with usage
                flow_factor = 1.6  # Flow increases with usage
            else:  # Low usage times
                pressure_factor = 1.0
                flow_factor = 0.8

            # Add some randomness (±5% for pressure, ±15% for flow)
            pressure_random = random.uniform(0.95, 1.05)
            flow_random = random.uniform(0.85, 1.15)

            # Calculate values
            pressure = base_pressure * pressure_factor * pressure_random
            flow = base_flow * flow_factor * flow_random

            pressure_data.append(round(pressure, 2))
            flow_data.append(round(flow, 1))

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
                "yAxisID": "y",
            },
            {
                "label": "Flow Rate (L/min)",
                "data": flow_data,
                "borderColor": "#9966FF",
                "backgroundColor": "rgba(153, 102, 255, 0.2)",
                "borderWidth": 2,
                "fill": False,
                "tension": 0.4,
                "yAxisID": "y1",
            },
        ]

        return {"labels": labels, "datasets": datasets}

    async def get_history_dashboard(
        self, heater_id: str, days: int = 7
    ) -> Dict[str, Any]:
        """
        Get complete history dashboard data for a water heater

        Args:
            heater_id: ID of the water heater
            days: Number of days of history to retrieve (default: 7)

        Returns:
            Complete history dashboard data
        """
        try:
            logging.info(
                f"Generating history dashboard for water heater {heater_id} over {days} days"
            )

            # Get all chart data, handling each separately to prevent one failure from affecting others
            temperature_history = None
            energy_usage_history = None
            pressure_flow_history = None

            try:
                temperature_history = await self.get_temperature_history(
                    heater_id, days
                )
            except Exception as e:
                logging.error(f"Error retrieving temperature history: {str(e)}")
                # Will fall back to mock data in development mode
                if os.getenv("IOTSPHERE_ENV", "development") == "development":
                    temperature_history = self._generate_mock_temperature_history(
                        heater_id, days
                    )

            try:
                energy_usage_history = await self.get_energy_usage_history(
                    heater_id, days
                )
            except Exception as e:
                logging.error(f"Error retrieving energy usage history: {str(e)}")
                # Will fall back to mock data in development mode
                if os.getenv("IOTSPHERE_ENV", "development") == "development":
                    energy_usage_history = self._generate_mock_energy_history(
                        heater_id, days
                    )

            try:
                pressure_flow_history = await self.get_pressure_flow_history(
                    heater_id, days
                )
            except Exception as e:
                logging.error(f"Error retrieving pressure/flow history: {str(e)}")
                # Will fall back to mock data in development mode
                if os.getenv("IOTSPHERE_ENV", "development") == "development":
                    pressure_flow_history = self._generate_mock_pressure_flow_history(
                        heater_id, days
                    )

            # Check if we have any data to return
            if not any(
                [temperature_history, energy_usage_history, pressure_flow_history]
            ):
                logging.warning(
                    f"No history data available for water heater {heater_id}"
                )
                if os.getenv("IOTSPHERE_ENV", "development") != "development":
                    return None

            # Ensure we have mock data for any missing components in development mode
            if os.getenv("IOTSPHERE_ENV", "development") == "development":
                if not temperature_history:
                    temperature_history = self._generate_mock_temperature_history(
                        heater_id, days
                    )
                if not energy_usage_history:
                    energy_usage_history = self._generate_mock_energy_history(
                        heater_id, days
                    )
                if not pressure_flow_history:
                    pressure_flow_history = self._generate_mock_pressure_flow_history(
                        heater_id, days
                    )

            # Return combined dashboard data
            return {
                "temperature": temperature_history,
                "energy_usage": energy_usage_history,
                "pressure_flow": pressure_flow_history,
            }

        except Exception as e:
            logging.error(
                f"Error generating history dashboard for {heater_id}: {str(e)}"
            )

            # In development mode, return complete mock data
            if os.getenv("IOTSPHERE_ENV", "development") == "development":
                logging.info(
                    f"Returning complete mock history dashboard for {heater_id}"
                )
                return {
                    "temperature": self._generate_mock_temperature_history(
                        heater_id, days
                    ),
                    "energy_usage": self._generate_mock_energy_history(heater_id, days),
                    "pressure_flow": self._generate_mock_pressure_flow_history(
                        heater_id, days
                    ),
                }

            return None
