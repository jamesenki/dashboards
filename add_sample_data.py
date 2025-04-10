#!/usr/bin/env python3
"""
Script to add sample temperature readings to the timeseries database for testing
"""

import os
import random
import sys
from datetime import datetime, timedelta

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models.water_heater import TemperatureReading
from src.repositories.timeseries_repository import TimeseriesRepository


def add_sample_data():
    """Add sample temperature data for demo and testing"""
    repo = TimeseriesRepository()
    heater_id = "wh-001"

    # Add current reading
    current_reading = TemperatureReading(
        heater_id=heater_id,
        timestamp=datetime.now().isoformat(),
        temperature=round(120 + random.uniform(-5, 5), 1),
    )
    repo.add_reading(current_reading)
    print(
        f"Added current reading: {current_reading.temperature}°F at {current_reading.timestamp}"
    )

    # Add 7 days of historical readings at 3-hour intervals
    for days_ago in range(1, 8):
        for hours in range(0, 24, 3):
            timestamp = datetime.now() - timedelta(days=days_ago, hours=hours)
            temperature = round(120 + random.uniform(-10, 10), 1)
            reading = TemperatureReading(
                heater_id=heater_id,
                timestamp=timestamp.isoformat(),
                temperature=temperature,
            )
            repo.add_reading(reading)

    print(f"Added 7 days of historical data at 3-hour intervals")

    # Add some data that should be archived (older than 30 days)
    for days_ago in range(35, 60, 5):
        timestamp = datetime.now() - timedelta(days=days_ago)
        temperature = round(115 + random.uniform(-15, 15), 1)
        reading = TemperatureReading(
            heater_id=heater_id,
            timestamp=timestamp.isoformat(),
            temperature=temperature,
        )
        repo.add_reading(reading)

    print(f"Added older data that should be archived")

    # Now archive data older than 30 days
    cutoff_date = datetime.now() - timedelta(days=30)
    archived_count = repo.archive_old_readings(cutoff_date)
    print(f"Archived {archived_count} readings older than 30 days")


if __name__ == "__main__":
    add_sample_data()
