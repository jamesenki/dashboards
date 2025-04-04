"""
Tool registration functions for the Agent Framework.
Handles registering different types of tools with the Tool Registry.
"""

import logging
from typing import Any

from src.ai.agent.tool_registry import ToolRegistry
from src.ai.agent.tools.water_heater_maintenance_tools import (
    analyze_water_heater_telemetry,
    get_water_heater_efficiency_analysis,
    get_water_heater_maintenance_prediction,
)
from src.ai.agent.tools.water_heater_tools import (
    get_water_heater_info,
    get_water_heater_list,
    get_water_heater_maintenance_info,
    get_water_heater_telemetry,
    set_water_heater_mode,
    set_water_heater_temperature,
)

logger = logging.getLogger(__name__)


def register_water_heater_tools(registry: ToolRegistry) -> None:
    """
    Register all water heater related tools with the Tool Registry.

    Args:
        registry: The Tool Registry to register the tools with
    """
    logger.info("Registering water heater tools")

    # Register information retrieval tools
    registry.register_tool(
        name="get_water_heater_info",
        description="Get detailed information about a specific water heater by ID. Parameters: device_id (string)",
        func=get_water_heater_info,
    )

    registry.register_tool(
        name="get_water_heater_list",
        description="Get a list of all water heaters in the system with their basic information. No parameters required.",
        func=get_water_heater_list,
        requires_params=False,
    )

    registry.register_tool(
        name="get_water_heater_telemetry",
        description="Get telemetry data for a specific water heater for a specified time period. Parameters: device_id (string), hours (integer, optional, default=24)",
        func=get_water_heater_telemetry,
    )

    # Register control tools
    registry.register_tool(
        name="set_water_heater_temperature",
        description="Set the target temperature for a water heater. Parameters: device_id (string), temperature (float, 30.0-85.0)",
        func=set_water_heater_temperature,
    )

    registry.register_tool(
        name="set_water_heater_mode",
        description="Set the operating mode for a water heater. Parameters: device_id (string), mode (string, one of: eco, high_demand, vacation, energy_saver)",
        func=set_water_heater_mode,
    )

    # Register maintenance tools
    registry.register_tool(
        name="get_water_heater_maintenance_info",
        description="Get maintenance information and recommendations for a specific water heater. Parameters: device_id (string)",
        func=get_water_heater_maintenance_info,
    )

    # Register maintenance prediction tools
    registry.register_tool(
        name="get_water_heater_maintenance_prediction",
        description="Get maintenance prediction information for a specific water heater, including when maintenance will be needed and component risks. Parameters: device_id (string)",
        func=get_water_heater_maintenance_prediction,
    )

    registry.register_tool(
        name="get_water_heater_efficiency_analysis",
        description="Get efficiency analysis for a specific water heater, including current efficiency rating, estimated costs, and recommendations. Parameters: device_id (string)",
        func=get_water_heater_efficiency_analysis,
    )

    registry.register_tool(
        name="analyze_water_heater_telemetry",
        description="Analyze recent telemetry data for patterns, anomalies, and usage characteristics. Parameters: device_id (string), hours (integer, optional, default=24)",
        func=analyze_water_heater_telemetry,
    )


def register_all_tools(registry: ToolRegistry) -> None:
    """
    Register all available tools with the Tool Registry.

    Args:
        registry: The Tool Registry to register the tools with
    """
    logger.info("Registering all tools")

    # Register water heater tools
    register_water_heater_tools(registry)

    # Register other tool categories as they become available
    # register_weather_tools(registry)
    # register_energy_tools(registry)
    # register_maintenance_tools(registry)
    # etc.

    logger.info("All tools registered successfully")
