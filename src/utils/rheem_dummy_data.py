"""
Utility to generate realistic Rheem water heater dummy data for testing and development.
"""
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.models.device import DeviceStatus
from src.models.rheem_water_heater import (
    RheemProductSeries,
    RheemWaterHeater,
    RheemWaterHeaterMode,
    RheemWaterHeaterReading,
    RheemWaterHeaterType,
    WaterHeaterDiagnosticCode,
    WaterHeaterStatus,
)

# Constants for generating realistic Rheem data
RHEEM_TANK_MODELS = {
    RheemProductSeries.CLASSIC: [
        "XE40M06ST45U1",
        "XG40T06EC36U1",
        "XE50T06ST45U1",
        "XG50T06EC36U1",
    ],
    RheemProductSeries.CLASSIC_PLUS: [
        "XE40M09ST45U1",
        "XG40T09EC36U1",
        "XE50T09ST45U1",
        "XG50T09EC36U1",
    ],
    RheemProductSeries.PRESTIGE: [
        "XE50T12ST45U1",
        "XG50T12DH45U1",
        "XE65T12ST45U1",
        "XG65T12DH45U1",
    ],
    RheemProductSeries.PROFESSIONAL: [
        "PROD50-38N RH95",
        "PROG50-38N RH95",
        "PROE50-38N RH95",
        "PRSE50-38N RH95",
    ],
}

RHEEM_TANKLESS_MODELS = {
    RheemProductSeries.PERFORMANCE: [
        "RTGH-84DVLN",
        "RTGH-84XLN",
        "RTGH-84DVLN-2",
        "RTGH-84XLP",
    ],
    RheemProductSeries.PERFORMANCE_PLATINUM: [
        "RTGH-95DVLN",
        "RTGH-95XLN",
        "RTGH-95DVLP",
        "RTGH-95XLP",
    ],
}

RHEEM_HYBRID_MODELS = {
    RheemProductSeries.PROTERRA: [
        "HPWH-235",
        "HPWH-250",
        "HPWH-265",
        "HPWH-280",
        "PROPH50 T2 RH350",
        "PROPH65 T2 RH350",
        "PROPH80 T2 RH350",
    ],
}

# UEF ratings by series and type
UEF_RATINGS = {
    RheemProductSeries.CLASSIC: (2.0, 2.5),
    RheemProductSeries.CLASSIC_PLUS: (2.5, 3.0),
    RheemProductSeries.PRESTIGE: (3.0, 3.5),
    RheemProductSeries.PROFESSIONAL: (3.3, 3.7),
    RheemProductSeries.PERFORMANCE: (0.82, 0.87),
    RheemProductSeries.PERFORMANCE_PLATINUM: (0.93, 0.96),
    RheemProductSeries.PROTERRA: (3.75, 4.0),
}

# Tank capacities (in gallons) by model type
TANK_CAPACITIES = {
    RheemWaterHeaterType.TANK: [30, 40, 50, 65, 75, 80],
    RheemWaterHeaterType.HYBRID: [40, 50, 65, 80],
    RheemWaterHeaterType.TANKLESS: None,  # tankless doesn't have a tank capacity
}

# Realistic diagnostic codes for Rheem water heaters
RHEEM_DIAGNOSTIC_CODES = [
    {"code": "E01", "description": "Inlet Thermistor Error", "severity": "Critical"},
    {"code": "E02", "description": "Outlet Thermistor Error", "severity": "Critical"},
    {"code": "E03", "description": "Water Leak Detected", "severity": "Critical"},
    {"code": "E04", "description": "Dry Fire Error", "severity": "Critical"},
    {"code": "E05", "description": "Heat Exchanger Overheat", "severity": "Critical"},
    {"code": "W01", "description": "Scale Build-up Warning", "severity": "Warning"},
    {"code": "W02", "description": "Low Flow Rate", "severity": "Warning"},
    {"code": "W03", "description": "Anode Rod Degradation", "severity": "Warning"},
    {"code": "W04", "description": "Filter Replacement Due", "severity": "Warning"},
    {"code": "I01", "description": "WiFi Signal Weak", "severity": "Info"},
    {"code": "I02", "description": "Firmware Update Available", "severity": "Info"},
    {"code": "M01", "description": "Annual Maintenance Due", "severity": "Maintenance"},
    {"code": "M02", "description": "Descaling Recommended", "severity": "Maintenance"},
]

# Model features by series
SERIES_FEATURES = {
    RheemProductSeries.CLASSIC: {
        "eco_net_enabled": False,
        "leak_guard": False,
        "warranty_years": 6,
        "energy_star_certified": False,
    },
    RheemProductSeries.CLASSIC_PLUS: {
        "eco_net_enabled": True,
        "leak_guard": False,
        "warranty_years": 8,
        "energy_star_certified": True,
    },
    RheemProductSeries.PRESTIGE: {
        "eco_net_enabled": True,
        "leak_guard": True,
        "warranty_years": 10,
        "energy_star_certified": True,
    },
    RheemProductSeries.PROFESSIONAL: {
        "eco_net_enabled": True,
        "leak_guard": True,
        "warranty_years": 12,
        "energy_star_certified": True,
    },
    RheemProductSeries.PERFORMANCE: {
        "eco_net_enabled": True,
        "leak_guard": False,
        "warranty_years": 8,
        "energy_star_certified": True,
    },
    RheemProductSeries.PERFORMANCE_PLATINUM: {
        "eco_net_enabled": True,
        "leak_guard": True,
        "warranty_years": 12,
        "energy_star_certified": True,
    },
    RheemProductSeries.PROTERRA: {
        "eco_net_enabled": True,
        "leak_guard": True,
        "warranty_years": 10,
        "energy_star_certified": True,
    },
}


def random_date(start_date, end_date):
    """Generate a random date between start_date and end_date."""
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return start_date + timedelta(days=random_days)


def generate_rheem_diagnostic_codes(heater_type, count=2):
    """Generate random diagnostic codes for a Rheem water heater."""
    codes = []
    selected_codes = random.sample(
        RHEEM_DIAGNOSTIC_CODES, min(count, len(RHEEM_DIAGNOSTIC_CODES))
    )

    for code_data in selected_codes:
        # 70% of codes should be inactive (resolved)
        active = random.random() > 0.7

        # Generate random timestamps within the last 6 months
        now = datetime.now()
        timestamp = random_date(now - timedelta(days=180), now)

        code = WaterHeaterDiagnosticCode(
            code=code_data["code"],
            description=code_data["description"],
            severity=code_data["severity"],
            timestamp=timestamp,
            active=active,
            metadata={
                "detected_by": "EcoNet"
                if "eco_net_enabled" in SERIES_FEATURES.get(heater_type, {})
                else "Local Sensor",
                "action_taken": "Automatic reset" if not active else None,
            },
        )
        codes.append(code)

    return codes


def generate_rheem_water_heater_readings(
    count=24,
    base_temp=45.0,
    variance=5.0,
    is_hybrid=False,
    smart_enabled=False,
    timestamp_hours_ago=24,
):
    """Generate random temperature readings over a period of time for Rheem water heaters."""
    readings = []
    current_time = datetime.now()

    # Generate a realistic temperature pattern
    for i in range(count):
        # Calculate timestamp
        hours_ago = (timestamp_hours_ago / count) * (count - i - 1)
        timestamp = current_time - timedelta(hours=hours_ago)

        # Generate more realistic temperature variations
        # Lower temperatures in early morning, higher in evening
        hour_of_day = timestamp.hour
        time_factor = 0

        # Temperature typically lower at night, higher during day
        if 0 <= hour_of_day < 6:  # Night
            time_factor = -2
        elif 6 <= hour_of_day < 10:  # Morning
            time_factor = 1
        elif 10 <= hour_of_day < 16:  # Midday
            time_factor = 2
        elif 16 <= hour_of_day < 22:  # Evening
            time_factor = 1
        else:  # Late night
            time_factor = -1

        # Add some random variation
        random_factor = random.uniform(-variance, variance)
        temperature = base_temp + time_factor + random_factor

        # Generate other reading values
        pressure = random.uniform(1.8, 2.5)
        energy_usage = random.uniform(100, 500)
        flow_rate = (
            random.uniform(0, 8.0) if random.random() > 0.3 else 0
        )  # 30% chance of no flow

        # Rheem-specific readings
        inlet_temp = temperature - random.uniform(25, 35)  # Much cooler incoming water
        outlet_temp = temperature - random.uniform(
            0.5, 2.0
        )  # Slightly cooler than tank
        ambient_temp = random.uniform(18, 25)  # Room temperature
        humidity = random.uniform(30, 60)  # Ambient humidity

        heating_element_status = "ON" if temperature < base_temp else "OFF"
        compressor_status = "ON" if is_hybrid and temperature < base_temp else "OFF"

        power_source = None
        if is_hybrid:
            if temperature < base_temp - 2:
                power_source = "ELECTRIC"  # Use electric when need to heat quickly
            else:
                power_source = "HEAT_PUMP"  # Use heat pump for efficiency

        wifi_signal_strength = random.randint(60, 95) if smart_enabled else None
        total_energy_used = (
            1000 + (i * 10) + random.uniform(0, 20)
        )  # Cumulative energy usage

        reading = RheemWaterHeaterReading(
            id=str(uuid.uuid4()),
            timestamp=timestamp,
            temperature=temperature,
            pressure=pressure,
            energy_usage=energy_usage,
            flow_rate=flow_rate,
            inlet_temperature=inlet_temp,
            outlet_temperature=outlet_temp,
            ambient_temperature=ambient_temp,
            humidity=humidity,
            heating_element_status=heating_element_status,
            compressor_status=compressor_status,
            power_source=power_source,
            wifi_signal_strength=wifi_signal_strength,
            total_energy_used=total_energy_used,
        )
        readings.append(reading)

    return readings


def generate_rheem_water_heaters(count=5):
    """Generate random Rheem water heaters with realistic specifications."""
    water_heaters = []

    for i in range(count):
        # Randomly select water heater type
        heater_type_choices = [
            (RheemWaterHeaterType.TANK, 0.5),  # 50% chance
            (RheemWaterHeaterType.TANKLESS, 0.2),  # 20% chance
            (RheemWaterHeaterType.HYBRID, 0.3),  # 30% chance
        ]
        heater_type = random.choices(
            [choice[0] for choice in heater_type_choices],
            weights=[choice[1] for choice in heater_type_choices],
            k=1,
        )[0]

        # Select series based on type
        if heater_type == RheemWaterHeaterType.TANK:
            series_choices = [
                RheemProductSeries.CLASSIC,
                RheemProductSeries.CLASSIC_PLUS,
                RheemProductSeries.PRESTIGE,
                RheemProductSeries.PROFESSIONAL,
            ]
            series = random.choice(series_choices)
            models = RHEEM_TANK_MODELS[series]
        elif heater_type == RheemWaterHeaterType.TANKLESS:
            series_choices = [
                RheemProductSeries.PERFORMANCE,
                RheemProductSeries.PERFORMANCE_PLATINUM,
            ]
            series = random.choice(series_choices)
            models = RHEEM_TANKLESS_MODELS[series]
        else:  # HYBRID
            series = RheemProductSeries.PROTERRA
            models = RHEEM_HYBRID_MODELS[series]

        model_number = random.choice(models)

        # Get features based on series
        features = SERIES_FEATURES[series]
        smart_enabled = features.get("eco_net_enabled", False)
        leak_detection = features.get("leak_guard", False)

        # Generate random installation date (1-5 years ago)
        now = datetime.now()
        install_date = random_date(
            now - timedelta(days=365 * 5), now - timedelta(days=30)
        )

        # Last maintenance is typically within the last year
        last_maintenance = random_date(
            now - timedelta(days=365), now - timedelta(days=1)
        )

        # Set temperature properties
        if heater_type == RheemWaterHeaterType.TANKLESS:
            min_temp = 35.0
            max_temp = 60.0
        else:
            min_temp = 35.0
            max_temp = 80.0

        target_temp = random.uniform(45.0, 55.0)
        current_temp = target_temp + random.uniform(-2.0, 2.0)

        # Set operating mode based on type
        if heater_type == RheemWaterHeaterType.HYBRID:
            mode_choices = [
                RheemWaterHeaterMode.ENERGY_SAVER,
                RheemWaterHeaterMode.HEAT_PUMP,
                RheemWaterHeaterMode.ELECTRIC,
                RheemWaterHeaterMode.HIGH_DEMAND,
                RheemWaterHeaterMode.VACATION,
            ]
        else:
            mode_choices = [
                RheemWaterHeaterMode.ENERGY_SAVER,
                RheemWaterHeaterMode.HIGH_DEMAND,
                RheemWaterHeaterMode.VACATION,
            ]
        mode = random.choice(mode_choices)

        # Set capacity based on type
        capacity = None
        if heater_type != RheemWaterHeaterType.TANKLESS:
            capacities = TANK_CAPACITIES[heater_type]
            capacity = random.choice(capacities)

        # Set UEF rating
        uef_range = UEF_RATINGS[series]
        uef_rating = random.uniform(uef_range[0], uef_range[1])

        # Generate heater status
        if current_temp < target_temp:
            heater_status = WaterHeaterStatus.HEATING
        else:
            heater_status = WaterHeaterStatus.STANDBY

        # Create water heater
        heater = RheemWaterHeater(
            id=f"rheem-{uuid.uuid4()}",
            name=f"Rheem {series.value} {capacity or ''} {heater_type.value}",
            location=random.choice(
                [
                    "Basement",
                    "Garage",
                    "Utility Room",
                    "Laundry Room",
                    "Attic",
                    "Closet",
                ]
            ),
            status=DeviceStatus.ONLINE,
            manufacturer="Rheem",
            model_number=model_number,
            series=series,
            target_temperature=target_temp,
            current_temperature=current_temp,
            min_temperature=min_temp,
            max_temperature=max_temp,
            mode=mode,
            heater_status=heater_status,
            heater_type=heater_type,
            smart_enabled=smart_enabled,
            leak_detection=leak_detection,
            capacity=capacity,
            uef_rating=uef_rating,
            installation_date=install_date,
            last_maintenance_date=last_maintenance,
            warranty_info={
                "years": features.get("warranty_years", 6),
                "extended": random.choice([True, False]),
                "expiration": (
                    install_date
                    + timedelta(days=365 * features.get("warranty_years", 6))
                ).isoformat(),
            },
        )

        # Add diagnostic codes
        for code in generate_rheem_diagnostic_codes(series, count=random.randint(0, 3)):
            heater.add_diagnostic_code(code)

        # Add readings
        is_hybrid = heater_type == RheemWaterHeaterType.HYBRID
        readings = generate_rheem_water_heater_readings(
            count=24,
            base_temp=target_temp,
            variance=3.0,
            is_hybrid=is_hybrid,
            smart_enabled=smart_enabled,
            timestamp_hours_ago=24,
        )
        for reading in readings:
            heater.add_reading(reading)

        water_heaters.append(heater)

    return water_heaters


def update_existing_water_heaters_to_rheem():
    """
    Update existing water heaters in the database to match Rheem specifications.
    This function would be used for migrating existing data.
    """
    # This function would interact with the repository to update existing water heaters
    # Implementation would depend on the specific repository interface
    pass
