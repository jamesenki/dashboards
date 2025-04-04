"""
Water heater maintenance prediction tools for AI agent.

This module integrates water heater maintenance prediction capabilities
into the AI agent system, replacing the standalone ML components with
integrated functionality within the AI framework.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast

from src.ai.agent.tools.water_heater_tools import execute_service_call, get_service
from src.services.water_heater_maintenance import WaterHeaterMaintenanceService

logger = logging.getLogger(__name__)


def get_water_heater_maintenance_prediction(device_id: str) -> str:
    """
    Get maintenance prediction information for a specific water heater.

    This function predicts when the water heater will need maintenance,
    what components may need attention, and provides confidence scores.

    Args:
        device_id: The ID of the water heater to analyze

    Returns:
        A formatted string with maintenance prediction information

    Raises:
        ValueError: If the water heater doesn't exist or prediction fails
    """
    logger.info(f"Getting maintenance prediction for water heater {device_id}")

    # Get water heater maintenance service
    service = get_service(WaterHeaterMaintenanceService)

    try:
        # Get the maintenance prediction from the service
        prediction = execute_service_call(service.get_maintenance_prediction, device_id)

        # Format the response
        result = [
            f"Water Heater Maintenance Prediction for {device_id}:",
            f"Days until maintenance: {prediction['days_until_maintenance']}",
            f"Confidence: {int(prediction['confidence'] * 100)}%",
            f"Next maintenance date: {prediction['next_maintenance_date']}",
            "",
            "Component Risks:",
        ]

        # Add component risks
        for component, risk in prediction["component_risks"].items():
            risk_percent = int(risk * 100)
            component_name = component.replace("_", " ").title()
            result.append(f"  - {component_name}: {risk_percent}% risk")

        # Add recommended actions if available
        if "recommended_actions" in prediction and prediction["recommended_actions"]:
            result.append("")
            result.append("Recommended Actions:")
            for action in prediction["recommended_actions"]:
                result.append(f"  - {action}")

        return "\n".join(result)

    except Exception as e:
        logger.error(f"Error getting maintenance prediction: {str(e)}")
        return f"Error retrieving maintenance prediction for water heater {device_id}: {str(e)}"


def get_water_heater_efficiency_analysis(device_id: str) -> str:
    """
    Get efficiency analysis for a specific water heater.

    This function analyzes the water heater's current efficiency,
    estimates costs, and provides recommendations to improve efficiency.

    Args:
        device_id: The ID of the water heater to analyze

    Returns:
        A formatted string with efficiency analysis information

    Raises:
        ValueError: If the water heater doesn't exist or analysis fails
    """
    logger.info(f"Getting efficiency analysis for water heater {device_id}")

    # Get water heater maintenance service
    service = get_service(WaterHeaterMaintenanceService)

    try:
        # Get the efficiency analysis from the service
        analysis = execute_service_call(service.get_efficiency_analysis, device_id)

        # Format the response
        result = [
            f"Water Heater Efficiency Analysis for {device_id}:",
            f"Current Efficiency: {int(analysis['current_efficiency'] * 100)}%",
            f"Estimated Annual Cost: ${analysis['estimated_annual_cost']:.2f}",
        ]

        # Add potential savings if available
        if "potential_savings" in analysis and analysis["potential_savings"]:
            result.append(
                f"Potential Annual Savings: ${analysis['potential_savings']:.2f}"
            )

        # Add recommendations if available
        if "recommendations" in analysis and analysis["recommendations"]:
            result.append("")
            result.append("Recommendations to Improve Efficiency:")
            for recommendation in analysis["recommendations"]:
                result.append(f"  - {recommendation}")

        return "\n".join(result)

    except Exception as e:
        logger.error(f"Error getting efficiency analysis: {str(e)}")
        return f"Error retrieving efficiency analysis for water heater {device_id}: {str(e)}"


def analyze_water_heater_telemetry(device_id: str, hours: int = 24) -> str:
    """
    Analyze recent telemetry data for a specific water heater.

    This function examines recent sensor readings to identify patterns,
    anomalies, and usage characteristics.

    Args:
        device_id: The ID of the water heater to analyze
        hours: Number of hours of telemetry to analyze (default: 24)

    Returns:
        A formatted string with telemetry analysis information

    Raises:
        ValueError: If the water heater doesn't exist or analysis fails
    """
    logger.info(f"Analyzing {hours} hours of telemetry for water heater {device_id}")

    # Get water heater maintenance service
    service = get_service(WaterHeaterMaintenanceService)

    try:
        # Get the telemetry analysis from the service
        analysis = execute_service_call(
            service.analyze_telemetry, device_id, hours=hours
        )

        # Format the response
        result = [
            f"Water Heater Telemetry Analysis for {device_id} (past {hours} hours):",
            f"Telemetry Health: {analysis['telemetry_health'].title()}",
        ]

        # Add estimated usage if available
        if "estimated_daily_usage" in analysis:
            result.append(
                f"Estimated Daily Usage: {analysis['estimated_daily_usage']} gallons"
            )

        # Add peak usage time if available
        if "peak_usage_time" in analysis:
            result.append(f"Peak Usage Time: {analysis['peak_usage_time']}")

        # Add patterns if available
        if "patterns" in analysis and analysis["patterns"]:
            result.append("")
            result.append("Usage Patterns Detected:")
            for pattern in analysis["patterns"]:
                result.append(f"  - {pattern}")

        # Add anomalies if available
        if "anomalies_detected" in analysis and analysis["anomalies_detected"]:
            result.append("")
            result.append("Anomalies Detected:")
            for anomaly in analysis["anomalies_detected"]:
                severity = anomaly.get("severity", "unknown").upper()
                param = anomaly.get("parameter", "").replace("_", " ").title()
                desc = anomaly.get("description", "No description available")
                action = anomaly.get("recommended_action", "No action specified")

                result.append(f"  - {severity} ANOMALY: {param}")
                result.append(f"    Description: {desc}")
                result.append(f"    Recommended Action: {action}")

        return "\n".join(result)

    except Exception as e:
        logger.error(f"Error analyzing telemetry: {str(e)}")
        return f"Error analyzing telemetry for water heater {device_id}: {str(e)}"
