"""
Water Heater tools for the Agent Framework.
Provides tools for interacting with water heater devices.
"""

import asyncio
import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Union

from src.api.dependencies import get_water_heater_service
from src.models.water_heater import WaterHeaterMode
from src.services.water_heater import WaterHeaterService
from src.services.water_heater_maintenance import WaterHeaterMaintenanceService

logger = logging.getLogger(__name__)


def execute_service_call(service_method: Callable, *args, **kwargs) -> Any:
    """
    Execute a service method that may be async or sync.
    Handles both coroutines (from async methods) and direct return values (from sync methods or mocks).

    Args:
        service_method: The service method to call
        *args: Positional arguments to pass to the method
        **kwargs: Keyword arguments to pass to the method

    Returns:
        The result of the service method call
    """
    try:
        # Call the method with the provided arguments
        result = service_method(*args, **kwargs)

        # Check if the result is a coroutine (async method)
        if inspect.iscoroutine(result):
            # Run the coroutine in a new event loop
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(result)
            finally:
                loop.close()

        # If it's not a coroutine, return directly (e.g., from a mock in tests)
        return result
    except Exception as e:
        logger.error(f"Error executing service call: {e}")
        raise


def get_water_heater_info(device_id: str) -> str:
    """
    Get information about a specific water heater.

    Args:
        device_id: The ID of the water heater

    Returns:
        A formatted string containing the water heater information
    """
    logger.info(f"Getting information for water heater: {device_id}")

    try:
        # Get the service (this will be a mock in tests)
        service = get_water_heater_service()

        # Get the water heater - uses our utility function to handle both async and sync methods
        water_heater = execute_service_call(service.get_water_heater, device_id)

        if not water_heater:
            return f"Water heater with ID {device_id} not found"

        # Format the response - try direct dictionary access first for test mocks
        try:
            # This approach works better with test mocks which return dictionaries
            info = f"""
            Water Heater Information:
            ------------------------
            ID: {water_heater.get('id', 'N/A')}
            Name: {water_heater.get('name', 'N/A')}
            Model: {water_heater.get('model', 'N/A')}

            Status: {water_heater.get('status', 'N/A')}
            Current Temperature: {water_heater.get('current_temperature', 'N/A')}°C
            Target Temperature: {water_heater.get('target_temperature', 'N/A')}°C
            Mode: {water_heater.get('mode', 'N/A')}

            Energy Usage: {water_heater.get('energy_usage', 'N/A')} W
            Last Maintenance: {water_heater.get('last_maintenance_date', 'N/A')}
            """
        except (AttributeError, TypeError):
            # Fallback to object attribute access for actual DB objects
            info = f"""
            Water Heater Information:
            ------------------------
            ID: {getattr(water_heater, 'id', 'N/A')}
            Name: {getattr(water_heater, 'name', 'N/A')}
            Model: {getattr(water_heater, 'model', 'N/A')}

            Status: {getattr(water_heater, 'status', 'N/A')}
            Current Temperature: {getattr(water_heater, 'current_temperature', 'N/A')}°C
            Target Temperature: {getattr(water_heater, 'target_temperature', 'N/A')}°C
            Mode: {getattr(water_heater, 'mode', 'N/A')}

            Energy Usage: {getattr(water_heater, 'energy_usage', 'N/A')} W
            Last Maintenance: {getattr(water_heater, 'last_maintenance_date', 'N/A')}
            """

        return info.strip()

    except Exception as e:
        logger.error(f"Error getting water heater info: {str(e)}")
        return f"Error retrieving water heater information: {str(e)}"


def get_water_heater_list() -> str:
    """
    Get a list of all water heaters in the system.

    Returns:
        A formatted string containing the list of water heaters
    """
    logger.info("Getting list of water heaters")

    try:
        # Get the service
        service = get_water_heater_service()

        # Get the water heaters - uses our utility function to handle both async and sync methods
        water_heaters = execute_service_call(service.get_water_heaters)

        # Format the response
        if not water_heaters:
            return "No water heaters found in the system."

        result = "Water Heaters:\n"
        for idx, wh in enumerate(water_heaters, 1):
            # Try dictionary access first (for test mocks)
            try:
                name = wh.get("name", "Unknown")
                wh_id = wh.get("id", "Unknown")
                status = wh.get("status", "N/A")
            except (AttributeError, TypeError):
                # Fall back to object attribute access
                name = getattr(wh, "name", "Unknown")
                wh_id = getattr(wh, "id", "Unknown")
                status = getattr(wh, "status", "N/A")

            result += f"{idx}. {name} (ID: {wh_id}) - Status: {status}\n"

        return result.strip()

    except Exception as e:
        logger.error(f"Error listing water heaters: {str(e)}")
        return f"Error retrieving water heater list: {str(e)}"


def get_water_heater_telemetry(device_id: str, hours: int = 24) -> str:
    """
    Get telemetry data for a specific water heater.

    Args:
        device_id: The ID of the water heater
        hours: Number of hours of data to retrieve (default: 24)

    Returns:
        A formatted string containing the telemetry data
    """
    logger.info(f"Getting telemetry for water heater: {device_id} (last {hours} hours)")

    try:
        # Get the service
        service = get_water_heater_service()

        # Get the readings using our utility function
        readings = execute_service_call(service.get_readings, device_id, hours=hours)

        # Format the response
        if not readings:
            return f"No telemetry data available for water heater {device_id} in the last {hours} hours."

        result = f"Water Heater Telemetry (Last {hours} Hours):\n"
        result += f"Device ID: {device_id}\n\n"

        for reading in readings:
            # Try dictionary access first (for test mocks)
            try:
                timestamp = reading.get("timestamp", "N/A")
                temp = reading.get("temperature", "N/A")
                pressure = reading.get("pressure", "N/A")
                energy = reading.get("energy_usage", "N/A")
                flow = reading.get("flow_rate", "N/A")
            except (AttributeError, TypeError):
                # Fall back to object attribute access
                timestamp = getattr(reading, "timestamp", "N/A")
                temp = getattr(reading, "temperature", "N/A")
                pressure = getattr(reading, "pressure", "N/A")
                energy = getattr(reading, "energy_usage", "N/A")
                flow = getattr(reading, "flow_rate", "N/A")

            result += f"Time: {timestamp}\n"
            result += f"  Temperature: {temp}°C\n"
            if pressure != "N/A":
                result += f"  Pressure: {pressure} bar\n"
            if energy != "N/A":
                result += f"  Energy Usage: {energy} W\n"
            if flow != "N/A":
                result += f"  Flow Rate: {flow} L/min\n"
            result += "\n"

        return result.strip()

    except Exception as e:
        logger.error(f"Error getting water heater telemetry: {str(e)}")
        return f"Error retrieving telemetry data: {str(e)}"


def set_water_heater_temperature(device_id: str, temperature: float) -> str:
    """
    Set the target temperature for a water heater.

    Args:
        device_id: The ID of the water heater
        temperature: The new target temperature in Celsius

    Returns:
        A confirmation message
    """
    logger.info(f"Setting temperature for water heater: {device_id} to {temperature}°C")

    try:
        # Get the service
        service = get_water_heater_service()

        # Update the temperature using our utility function
        result = execute_service_call(
            service.update_target_temperature, device_id, temperature
        )

        if not result:
            return f"Failed to update temperature for water heater {device_id}"

        # Get the name safely
        def safe_get(obj, key, default="Unknown"):
            try:
                return getattr(obj, key, default)
            except (AttributeError, TypeError):
                return obj.get(key, default) if isinstance(obj, dict) else default

        name = safe_get(result, "name")

        return f"Temperature for water heater '{name}' has been successfully updated to {temperature}°C"

    except Exception as e:
        logger.error(f"Error setting water heater temperature: {str(e)}")
        return f"Error updating water heater temperature: {str(e)}"


def set_water_heater_mode(device_id: str, mode: str) -> str:
    """
    Set the operating mode for a water heater.

    Args:
        device_id: The ID of the water heater
        mode: The new operating mode (eco, high_demand, vacation, energy_saver)

    Returns:
        A confirmation message
    """
    logger.info(f"Setting mode for water heater: {device_id} to {mode}")

    try:
        # Convert mode string to enum
        # Handle case-insensitive mode strings and normalize
        mode_upper = mode.upper()
        if mode_upper == "ECO" or mode_upper == "ECONOMY":
            mode_enum = WaterHeaterMode.ECO
        elif mode_upper == "HIGH_DEMAND" or mode_upper == "HIGH DEMAND":
            mode_enum = WaterHeaterMode.HIGH_DEMAND
        elif mode_upper == "VACATION":
            mode_enum = WaterHeaterMode.VACATION
        elif mode_upper == "ENERGY_SAVER" or mode_upper == "ENERGY SAVER":
            mode_enum = WaterHeaterMode.ENERGY_SAVER
        else:
            raise ValueError(
                f"Invalid mode: {mode}. Valid modes are: eco, high_demand, vacation, energy_saver"
            )

        # Get the service
        service = get_water_heater_service()

        # Update the mode using our utility function
        result = execute_service_call(service.update_mode, device_id, mode_enum)

        if not result:
            return f"Failed to update mode for water heater {device_id}"

        # Function to safely get a value from either an object or a dict
        def safe_get(obj, key, default="Unknown"):
            try:
                return getattr(obj, key, default)
            except (AttributeError, TypeError):
                return obj.get(key, default) if isinstance(obj, dict) else default

        name = safe_get(result, "name")
        updated_mode = safe_get(result, "mode", mode_enum)

        return f"Mode for water heater '{name}' has been successfully updated to {updated_mode}"

    except Exception as e:
        logger.error(f"Error setting water heater mode: {str(e)}")
        return f"Error updating water heater mode: {str(e)}"


def get_water_heater_maintenance_info(device_id: str) -> str:
    """
    Get maintenance information for a specific water heater.

    Args:
        device_id: The ID of the water heater

    Returns:
        A formatted string containing maintenance information
    """
    logger.info(f"Getting maintenance info for water heater: {device_id}")

    try:
        # Get the service
        service = get_water_heater_service()

        # Get the maintenance info using our utility function
        info = execute_service_call(service.get_maintenance_info, device_id)

        if not info:
            return f"No maintenance information available for water heater {device_id}"

        # Try dictionary access first (for test mocks)
        try:
            last_maint = info.get("last_maintenance_date", "N/A")
            next_maint = info.get("next_maintenance_due", "N/A")
            tasks = info.get("maintenance_tasks", [])
            efficiency = info.get("efficiency_score")
            recommendations = info.get("recommendations", [])
        except (AttributeError, TypeError):
            # Fall back to object attribute access
            last_maint = getattr(info, "last_maintenance_date", "N/A")
            next_maint = getattr(info, "next_maintenance_due", "N/A")
            tasks = getattr(info, "maintenance_tasks", [])
            efficiency = getattr(info, "efficiency_score", None)
            recommendations = getattr(info, "recommendations", [])

        # Build the response
        result = "Water Heater Maintenance Information:\n"
        result += f"Device ID: {device_id}\n\n"
        result += f"Last Maintenance Date: {last_maint}\n"
        result += f"Next Maintenance Due: {next_maint}\n\n"

        result += "Maintenance Tasks:\n"
        for task in tasks:
            result += f"- {task}\n"

        if efficiency is not None and efficiency != "N/A":
            result += f"\nEfficiency Score: {efficiency}/100\n"

        if recommendations:
            result += "\nRecommendations:\n"
            for rec in recommendations:
                result += f"- {rec}\n"

        return result.strip()

    except Exception as e:
        logger.error(f"Error getting water heater maintenance info: {str(e)}")
        return f"Error retrieving maintenance information: {str(e)}"
