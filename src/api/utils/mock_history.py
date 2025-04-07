"""
Mock history data generators for the IoTSphere API.

This module provides functions for generating realistic mock data
for water heater history endpoints, supporting multiple device types
in line with the IoTSphere platform's device-agnostic architecture.
"""
import math
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List


def create_mock_history_dashboard(device_id: str, days: int) -> Dict[str, Any]:
    """
    Create mock history dashboard data for testing and development
    
    Args:
        device_id: The device ID to create mock data for
        days: Number of days of history to generate
        
    Returns:
        Mock dashboard data dictionary
    """
    return {
        "summary": {
            "average_temperature": round(random.uniform(115, 125), 1),
            "temperature_variation": round(random.uniform(3, 8), 1),
            "energy_consumption": round(random.uniform(15, 25), 1),
            "energy_efficiency": round(random.uniform(85, 95), 1),
            "water_usage": round(random.uniform(350, 450), 1)
        },
        "period": {
            "start_date": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d"),
            "days": days
        },
        "device_id": device_id,
        "generated_at": datetime.now().isoformat(),
        "has_anomalies": random.choice([True, False]),
        "anomalies": [
            {
                "type": "temperature_spike",
                "timestamp": (datetime.now() - timedelta(days=random.randint(1, days-1))).isoformat(),
                "value": round(random.uniform(135, 150), 1),
                "severity": "medium"
            } if random.choice([True, False]) else None,
            {
                "type": "energy_surge",
                "timestamp": (datetime.now() - timedelta(days=random.randint(1, days-1))).isoformat(),
                "value": round(random.uniform(2500, 3000), 1),
                "severity": "low"
            } if random.choice([True, False]) else None
        ]
    }


def create_mock_temperature_history(device_id: str, days: int) -> Dict[str, Any]:
    """
    Create mock temperature history data in Chart.js format
    
    Args:
        device_id: The device ID to create mock data for
        days: Number of days of history to generate
        
    Returns:
        Mock temperature history data in Chart.js format
    """
    # Generate dates for the past 'days' days
    end_date = datetime.now()
    dates = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)][::-1]
    
    # Generate mock temperature data with some realistic patterns
    base_temp = 120  # Base temperature in Fahrenheit
    day_temps = []  # Average daily temperatures
    min_temps = []   # Daily minimum temperatures
    max_temps = []   # Daily maximum temperatures
    
    for i in range(days):
        # Create a slight trend over time with some randomness
        daily_variation = random.uniform(-5, 5)
        daily_avg = base_temp + daily_variation + math.sin(i/7 * math.pi) * 3
        day_temps.append(round(daily_avg, 1))
        
        # Create min/max with some reasonable variation
        daily_range = random.uniform(2, 8)
        min_temps.append(round(daily_avg - daily_range/2, 1))
        max_temps.append(round(daily_avg + daily_range/2, 1))
    
    # Format data for Chart.js
    chart_data = {
        "labels": dates,
        "datasets": [
            {
                "label": "Average Temperature",
                "data": day_temps,
                "fill": False,
                "borderColor": "rgba(75, 192, 192, 1)",
                "tension": 0.1
            },
            {
                "label": "Min Temperature",
                "data": min_temps,
                "fill": False,
                "borderColor": "rgba(54, 162, 235, 0.7)",
                "borderDash": [5, 5],
                "tension": 0.1
            },
            {
                "label": "Max Temperature",
                "data": max_temps,
                "fill": False,
                "borderColor": "rgba(255, 99, 132, 0.7)",
                "borderDash": [5, 5],
                "tension": 0.1
            }
        ]
    }
    
    # Add metadata for the API response
    return {
        "device_id": device_id,
        "metric": "temperature",
        "unit": "°F",
        "period_days": days,
        "labels": chart_data["labels"],
        "datasets": chart_data["datasets"]
    }


def create_mock_energy_history(device_id: str, days: int) -> Dict[str, Any]:
    """
    Create mock energy usage history data in Chart.js format
    
    Args:
        device_id: The device ID to create mock data for
        days: Number of days of history to generate
        
    Returns:
        Mock energy usage history data in Chart.js format
    """
    # Generate dates for the past 'days' days
    end_date = datetime.now()
    dates = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)][::-1]
    
    # Generate mock energy usage data with realistic patterns
    # More energy used on weekends, with some random variation
    daily_usage = []
    cumulative_usage = []
    running_total = 0
    
    for i in range(days):
        # Determine if this is a weekend (higher usage)
        is_weekend = (end_date - timedelta(days=days-i-1)).weekday() >= 5
        base_usage = 3.5 if is_weekend else 2.8  # kWh base usage
        
        # Add some randomness and a slight weekly pattern
        daily = base_usage + random.uniform(-0.5, 0.5) + math.sin(i/7 * math.pi) * 0.3
        daily_usage.append(round(daily, 2))
        
        # Update cumulative usage
        running_total += daily
        cumulative_usage.append(round(running_total, 2))
    
    # Format data for Chart.js
    chart_data = {
        "labels": dates,
        "datasets": [
            {
                "label": "Daily Energy Usage",
                "data": daily_usage,
                "type": "bar",
                "backgroundColor": "rgba(54, 162, 235, 0.5)",
                "borderColor": "rgba(54, 162, 235, 1)",
                "borderWidth": 1,
                "yAxisID": "y"
            },
            {
                "label": "Cumulative Usage",
                "data": cumulative_usage,
                "type": "line",
                "fill": False,
                "borderColor": "rgba(255, 99, 132, 1)",
                "tension": 0.1,
                "yAxisID": "y1"
            }
        ]
    }
    
    # Add metadata for the API response
    return {
        "device_id": device_id,
        "metric": "energy_usage",
        "unit": "kWh",
        "period_days": days,
        "labels": chart_data["labels"],
        "datasets": chart_data["datasets"],
        "totals": {
            "daily_average": round(sum(daily_usage) / len(daily_usage), 2),
            "total_usage": round(sum(daily_usage), 2),
            "estimated_cost": round(sum(daily_usage) * 0.15, 2)  # Assume $0.15 per kWh
        }
    }


def create_mock_pressure_flow_history(device_id: str, days: int) -> Dict[str, Any]:
    """
    Create mock pressure and flow rate history data in Chart.js format
    
    Args:
        device_id: The device ID to create mock data for
        days: Number of days of history to generate
        
    Returns:
        Mock pressure and flow rate history data in Chart.js format
    """
    # Generate dates for the past 'days' days
    end_date = datetime.now()
    dates = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)][::-1]
    
    # Generate mock pressure data with realistic patterns
    pressure_data = []
    flow_rate_data = []
    
    for i in range(days):
        # Generate pressure data (PSI) - should be relatively stable with minor fluctuations
        base_pressure = 50  # Base pressure in PSI
        daily_pressure = base_pressure + random.uniform(-3, 3) + math.sin(i/5 * math.pi) * 1.5
        pressure_data.append(round(daily_pressure, 1))
        
        # Generate flow rate data (GPM) - more variable based on usage patterns
        base_flow = 2.5  # Base flow rate in GPM
        # Flow rate varies more on weekends
        is_weekend = (end_date - timedelta(days=days-i-1)).weekday() >= 5
        flow_multiplier = 1.3 if is_weekend else 1.0
        daily_flow = base_flow * flow_multiplier + random.uniform(-0.5, 0.5)
        flow_rate_data.append(round(daily_flow, 1))
    
    # Format data for Chart.js
    chart_data = {
        "labels": dates,
        "datasets": [
            {
                "label": "Pressure (PSI)",
                "data": pressure_data,
                "fill": False,
                "borderColor": "rgba(75, 192, 192, 1)",
                "tension": 0.1,
                "yAxisID": "y"
            },
            {
                "label": "Flow Rate (GPM)",
                "data": flow_rate_data,
                "fill": False,
                "borderColor": "rgba(255, 159, 64, 1)",
                "tension": 0.1,
                "yAxisID": "y1"
            }
        ]
    }
    
    # Add metadata for the API response
    return {
        "device_id": device_id,
        "metrics": ["pressure", "flow_rate"],
        "units": {"pressure": "PSI", "flow_rate": "GPM"},
        "period_days": days,
        "labels": chart_data["labels"],
        "datasets": chart_data["datasets"],
        "averages": {
            "pressure": round(sum(pressure_data) / len(pressure_data), 1),
            "flow_rate": round(sum(flow_rate_data) / len(flow_rate_data), 1)
        }
    }
