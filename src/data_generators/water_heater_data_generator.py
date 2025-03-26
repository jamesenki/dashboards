"""
Water heater data generator for creating synthetic test data.
"""
from datetime import datetime, timedelta
import random
import json
import math
import os
from typing import List, Dict, Any, Optional, Tuple
import uuid

from src.models.water_heater import WaterHeater, WaterHeaterReading, WaterHeaterMode, WaterHeaterStatus
from src.models.device import DeviceStatus, DeviceType

class WaterHeaterDataGenerator:
    """
    Generator for creating synthetic water heater data for testing and development.
    """
    
    # Common names and locations for water heaters
    NAMES = [
        "Water Heater", "Hot Water System", "Electric Heater", "Tankless Heater",
        "SmartTemp Heater", "EcoWarm System", "Commercial Heater"
    ]
    
    LOCATIONS = [
        "Building A, Floor 1", "Building A, Floor 2", "Building B, Basement",
        "Central Plant", "Main Office", "Utility Room", "Mechanical Room", 
        "Kitchen Area", "Facility 1", "East Wing", "West Wing", "Residential Zone",
        "Commercial Zone", "Industrial Plant"
    ]
    
    def __init__(self):
        """Initialize the water heater data generator."""
        self.rng = random.Random()
        self.rng.seed(42)  # For reproducibility
    
    def generate_water_heater(self, id: Optional[str] = None, usage_pattern: str = "commercial") -> WaterHeater:
        """
        Generate a single water heater with random but realistic properties.
        
        Args:
            id: Optional ID for the water heater, will be auto-generated if None
            usage_pattern: The usage pattern affecting parameter ranges 
                           ("residential", "commercial", or "industrial")
                           
        Returns:
            A water heater instance with randomized properties
        """
        if id is None:
            id = f"wh-{uuid.uuid4().hex[:8]}"
        
        # Set property ranges based on usage pattern
        if usage_pattern == "residential":
            capacity_range = (40, 120)
            temp_range = (45, 65)
            efficiency_range = (0.7, 0.95)
        elif usage_pattern == "industrial":
            capacity_range = (200, 800)
            temp_range = (60, 85)
            efficiency_range = (0.6, 0.9)
        else:  # commercial
            capacity_range = (100, 300)
            temp_range = (50, 75)
            efficiency_range = (0.65, 0.92)
        
        # Randomize device properties
        name = f"{self.rng.choice(self.NAMES)} {id}"
        location = self.rng.choice(self.LOCATIONS)
        target_temp = self.rng.uniform(temp_range[0], temp_range[1])
        current_temp = target_temp + self.rng.uniform(-5, 5)  # Random deviation from target
        
        # Create the water heater
        water_heater = WaterHeater(
            id=id,
            name=name,
            status=DeviceStatus.ONLINE,
            location=location,
            type=DeviceType.WATER_HEATER,
            target_temperature=round(target_temp, 1),
            current_temperature=round(current_temp, 1),
            capacity=round(self.rng.uniform(capacity_range[0], capacity_range[1]), 1),
            efficiency_rating=round(self.rng.uniform(efficiency_range[0], efficiency_range[1]), 2),
            mode=self.rng.choice(list(WaterHeaterMode)),
            min_temperature=40.0,
            max_temperature=85.0
        )
        
        # Set heater status based on temperatures
        if water_heater.current_temperature >= water_heater.target_temperature:
            water_heater.heater_status = WaterHeaterStatus.STANDBY
        else:
            water_heater.heater_status = WaterHeaterStatus.HEATING
        
        return water_heater
    
    def generate_water_heaters(self, count: int = 5, usage_patterns: Optional[List[str]] = None) -> List[WaterHeater]:
        """
        Generate multiple water heaters.
        
        Args:
            count: Number of water heaters to generate
            usage_patterns: Optional list of usage patterns to apply to the generated heaters.
                           If provided, must have same length as count.
                           
        Returns:
            List of water heater instances
        """
        water_heaters = []
        
        if usage_patterns and len(usage_patterns) != count:
            raise ValueError("If provided, usage_patterns must have same length as count")
        
        for i in range(count):
            usage_pattern = "commercial"  # Default
            if usage_patterns:
                usage_pattern = usage_patterns[i]
            else:
                # Random distribution of patterns
                pattern_weights = [0.3, 0.5, 0.2]  # residential, commercial, industrial
                pattern_choice = self.rng.choices(
                    ["residential", "commercial", "industrial"], 
                    weights=pattern_weights, 
                    k=1
                )[0]
                usage_pattern = pattern_choice
                
            water_heater = self.generate_water_heater(id=f"wh-{i+1:04d}", usage_pattern=usage_pattern)
            water_heaters.append(water_heater)
            
        return water_heaters
    
    def generate_water_heater_readings(
        self, 
        water_heater: WaterHeater,
        start_time: datetime,
        end_time: datetime,
        interval_minutes: int = 15,
        usage_pattern: Optional[str] = None
    ) -> List[WaterHeaterReading]:
        """
        Generate a series of readings for a water heater over a time period.
        
        Args:
            water_heater: The water heater to generate readings for
            start_time: The starting timestamp
            end_time: The ending timestamp
            interval_minutes: Time between readings in minutes
            usage_pattern: Optional usage pattern override
                          
        Returns:
            List of water heater readings
        """
        readings = []
        current_time = start_time
        
        # Determine usage pattern if not provided
        if usage_pattern is None:
            # Guess from capacity
            if water_heater.capacity and water_heater.capacity <= 120:
                usage_pattern = "residential"
            elif water_heater.capacity and water_heater.capacity >= 200:
                usage_pattern = "industrial"
            else:
                usage_pattern = "commercial"
        
        # Set baseline values based on usage pattern
        if usage_pattern == "residential":
            base_temp = water_heater.target_temperature - 2
            base_pressure = 2.0
            base_energy = 1200  # watts
            base_flow = 0.0  # L/min, normally zero
            temp_variance = 8  # Higher variance
        elif usage_pattern == "industrial":
            base_temp = water_heater.target_temperature - 1
            base_pressure = 3.5
            base_energy = 4500  # watts
            base_flow = 2.0  # L/min, some constant flow
            temp_variance = 4  # Lower variance
        else:  # commercial
            base_temp = water_heater.target_temperature - 1.5
            base_pressure = 2.8
            base_energy = 2800  # watts
            base_flow = 1.0  # L/min
            temp_variance = 6  # Medium variance
        
        # Generate readings at specified intervals
        while current_time <= end_time:
            # Generate usage patterns based on time of day
            hour_factor = self._get_time_of_day_factor(current_time, usage_pattern)
            
            # Calculate randomized values
            temperature = self._generate_temperature(base_temp, temp_variance, hour_factor, current_time)
            pressure = base_pressure * (1 + self.rng.uniform(-0.1, 0.1) * hour_factor)
            energy_usage = base_energy * hour_factor * (1 + self.rng.uniform(-0.2, 0.3))
            
            # Flow rate depends on usage - higher at peak usage times
            flow_multiplier = max(0, hour_factor - 0.5) * 2  # Only high during usage
            flow_rate = base_flow + (10 * flow_multiplier * self.rng.uniform(0, 1))
            
            # Create the reading
            reading = WaterHeaterReading(
                timestamp=current_time,
                temperature=round(temperature, 1),
                pressure=round(pressure, 2) if self.rng.random() > 0.1 else None,  # Occasional missing pressure
                energy_usage=round(energy_usage, 1) if self.rng.random() > 0.05 else None,  # Rare missing energy
                flow_rate=round(flow_rate, 2) if flow_rate > 0.1 else 0
            )
            readings.append(reading)
            
            # Move to next interval
            current_time += timedelta(minutes=interval_minutes)
        
        return readings
    
    def _get_time_of_day_factor(self, timestamp: datetime, usage_pattern: str) -> float:
        """
        Calculate a usage factor based on time of day and usage pattern.
        
        Args:
            timestamp: The timestamp to calculate factor for
            usage_pattern: The usage pattern
            
        Returns:
            Factor between 0.4 and 1.5 representing activity level
        """
        hour = timestamp.hour
        weekday = timestamp.weekday()  # 0-6, where 0 is Monday
        is_weekend = weekday >= 5
        
        if usage_pattern == "residential":
            # Residential: morning peak (6-9), evening peak (18-22)
            if 6 <= hour < 9:
                return 1.2 + self.rng.uniform(-0.1, 0.1)
            elif 18 <= hour < 22:
                return 1.3 + self.rng.uniform(-0.1, 0.2)
            elif 22 <= hour < 24 or 0 <= hour < 5:
                return 0.5 + self.rng.uniform(-0.1, 0.1)
            else:
                return 0.8 + self.rng.uniform(-0.1, 0.1)
                
        elif usage_pattern == "industrial":
            # Industrial: constant during work hours
            if is_weekend:
                return 0.6 + self.rng.uniform(-0.1, 0.1)  # Low weekend usage
            elif 8 <= hour < 18:
                return 1.2 + self.rng.uniform(-0.1, 0.2)  # Work hours
            elif 18 <= hour < 22:
                return 0.9 + self.rng.uniform(-0.1, 0.1)  # Evening shift
            else:
                return 0.7 + self.rng.uniform(-0.1, 0.1)  # Night shift (reduced)
                
        else:  # commercial
            # Commercial: business hours (9-17)
            if is_weekend:
                if 10 <= hour < 16:
                    return 0.9 + self.rng.uniform(-0.1, 0.1)  # Weekend business hours
                else:
                    return 0.5 + self.rng.uniform(-0.1, 0.1)  # Off hours
            elif 9 <= hour < 17:
                return 1.2 + self.rng.uniform(-0.1, 0.2)  # Business hours
            elif 17 <= hour < 20:
                return 0.9 + self.rng.uniform(-0.1, 0.1)  # Evening
            else:
                return 0.5 + self.rng.uniform(-0.1, 0.1)  # Off hours
    
    def _generate_temperature(
        self, 
        base_temp: float, 
        variance: float, 
        hour_factor: float, 
        timestamp: datetime
    ) -> float:
        """
        Generate a realistic temperature value with cyclical patterns.
        
        Args:
            base_temp: The baseline temperature
            variance: Maximum temperature variance
            hour_factor: Usage factor for the current hour
            timestamp: Current timestamp
            
        Returns:
            A realistic temperature value
        """
        # Daily cycle - subtle temperature changes following a sine wave
        day_of_year = timestamp.timetuple().tm_yday
        hour_of_day = timestamp.hour + timestamp.minute / 60.0
        
        # Daily cycle (24 hour period)
        daily_cycle = math.sin(hour_of_day * math.pi / 12) * variance / 4
        
        # Seasonal effect (yearly cycle) - subtle
        seasonal_effect = math.sin(day_of_year * 2 * math.pi / 365) * variance / 6
        
        # Usage effect - temperature drops when water is used, then recovers
        usage_drop = (hour_factor - 0.7) * variance / 2
        
        # Random noise
        noise = self.rng.uniform(-variance/4, variance/4)
        
        # Combine effects
        temperature = base_temp + daily_cycle + seasonal_effect - usage_drop + noise
        
        return max(35, min(90, temperature))  # Ensure temperature stays in realistic range
    
    def apply_readings_to_water_heater(self, water_heater: WaterHeater, readings: List[WaterHeaterReading]) -> None:
        """
        Apply a series of readings to a water heater, updating its current state.
        
        Args:
            water_heater: The water heater to update
            readings: The readings to apply
        """
        if not readings:
            return
            
        # Sort readings by timestamp to ensure correct order
        sorted_readings = sorted(readings, key=lambda r: r.timestamp)
        
        # Apply each reading
        for reading in sorted_readings:
            water_heater.add_reading(reading)
    
    def save_to_file(self, water_heaters: List[WaterHeater], filename: str) -> None:
        """
        Save water heaters to a JSON file.
        
        Args:
            water_heaters: List of water heaters to save
            filename: File to save to
        """
        # Convert water heaters to JSON serializable format
        water_heaters_json = [wh.model_dump() for wh in water_heaters]
        
        # Write to file
        with open(filename, 'w') as f:
            json.dump(water_heaters_json, f, indent=2, default=str)
    
    def load_from_file(self, filename: str) -> List[WaterHeater]:
        """
        Load water heaters from a JSON file.
        
        Args:
            filename: File to load from
            
        Returns:
            List of water heater instances
        """
        with open(filename, 'r') as f:
            water_heaters_json = json.load(f)
        
        # Convert JSON to water heater instances
        water_heaters = []
        for wh_data in water_heaters_json:
            # Parse datetimes in readings
            if 'readings' in wh_data:
                for reading in wh_data['readings']:
                    if 'timestamp' in reading:
                        reading['timestamp'] = datetime.fromisoformat(reading['timestamp'].replace('Z', '+00:00'))
            
            # Create water heater instance
            water_heater = WaterHeater(**wh_data)
            water_heaters.append(water_heater)
            
        return water_heaters
