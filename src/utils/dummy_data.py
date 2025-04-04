"""
Utility to generate dummy data for testing the application
"""
import logging
import random
import uuid
from datetime import datetime, timedelta

# Import AquaTherm water heater data
from src.utils.aquatherm_data import get_aquatherm_water_heaters

# Set up logging
logger = logging.getLogger(__name__)

from src.models.device import DeviceStatus, DeviceType
from src.models.vending_machine import (
    LocationType,
    ProductItem,
    SubLocation,
    UseType,
    VendingMachine,
    VendingMachineMode,
    VendingMachineReading,
    VendingMachineStatus,
)
from src.models.water_heater import (
    WaterHeater,
    WaterHeaterDiagnosticCode,
    WaterHeaterMode,
    WaterHeaterReading,
    WaterHeaterStatus,
    WaterHeaterType,
)

# Constants for generating realistic data
WATER_HEATER_BRANDS = [
    "SmartTemp",
    "EcoHeat",
    "AquaWarm",
    "ThermoGuard",
    "HydroHeat",
    "EnergyMax",
    "ComfortFlow",
    "WaterSteward",
    "HeatMaster",
    "EcoFlow",
]

VENDING_MACHINE_BRANDS = [
    "PolarDelight",
    "VendTech",
    "RefreshMax",
    "SnackMaster",
    "CoolServe",
    "QuickBite",
    "AutoVend",
    "SnackWave",
    "ChillDispense",
    "FreshVending",
]

WATER_HEATER_MODELS = [
    "Pro",
    "Elite",
    "Plus",
    "Smart",
    "Ultra",
    "MaxEco",
    "Platinum",
    "Industrial",
    "Commercial",
    "Residential",
    "Advanced",
    "Compact",
]

VENDING_MACHINE_MODELS = [
    "MK-500",
    "VX-1000",
    "SmartDispense",
    "AutoSell",
    "CoolVend",
    "FrostyPlus",
    "QuickServe",
    "SuperVend",
    "MaxCapacity",
    "EcoVend",
]

WATER_HEATER_SIZES = ["50L", "80L", "100L", "120L", "150L", "200L"]

BUILDINGS = [
    "Building A",
    "Building B",
    "Building C",
    "North Wing",
    "South Wing",
    "East Tower",
    "West Tower",
    "Main Office",
    "Factory Floor",
    "R&D Lab",
    "Warehouse",
    "Apartment 101",
    "Apartment 202",
    "Apartment 303",
]

LOCATIONS = [
    "Kitchen",
    "Bathroom",
    "Garage",
    "Basement",
    "Utility Room",
    "Master Bathroom",
    "Guest Bathroom",
    "Laundry Room",
    "Break Room",
    "Staff Kitchen",
    "Shower Room",
    "Janitor Closet",
    "Boiler Room",
    "Maintenance Area",
    "Suite 101",
    "Suite 202",
    "Manufacturing Floor",
]

# Business names for location data by type
BUSINESS_NAMES = {
    LocationType.FAST_FOOD: [
        "McDonald's",
        "Burger King",
        "Wendy's",
        "Subway",
        "Taco Bell",
        "KFC",
        "Pizza Hut",
        "Chipotle",
        "Panera Bread",
        "Five Guys",
    ],
    LocationType.HOSPITAL: [
        "Mercy Hospital",
        "Cleveland Clinic",
        "Mayo Medical Center",
        "St. Luke's Hospital",
        "Mount Sinai Medical",
        "Johns Hopkins Hospital",
        "Northwestern Memorial",
        "NYU Medical Center",
        "UCLA Medical Center",
        "Massachusetts General",
    ],
    LocationType.STUDENT_CENTER: [
        "UC Berkeley Student Union",
        "Ohio State Union",
        "Michigan Student Center",
        "Stanford Tresidder",
        "NYU Kimmel Center",
        "UCLA Ackerman Union",
        "Harvard Smith Center",
        "Penn State HUB",
        "MIT Stratton Center",
        "Georgia Tech Student Center",
    ],
    LocationType.SCHOOL: [
        "Lincoln High School",
        "Washington Elementary",
        "Jefferson Middle School",
        "Roosevelt Academy",
        "Kennedy High",
        "Madison Elementary",
        "Adams Middle School",
        "Franklin Academy",
        "Monroe School",
        "Oakwood Elementary",
    ],
    LocationType.OFFICE: [
        "Google Campus",
        "Microsoft Headquarters",
        "Apple Park",
        "Amazon Offices",
        "Facebook HQ",
        "IBM Building",
        "Oracle Tower",
        "Intel Campus",
        "Salesforce Tower",
        "Adobe Offices",
    ],
    LocationType.SPECIALTY_SHOP: [
        "Whole Foods Market",
        "Trader Joe's",
        "REI Co-op",
        "Barnes & Noble",
        "Best Buy",
        "GameStop",
        "Sephora",
        "Lululemon",
        "Apple Store",
        "Nordstrom",
    ],
    LocationType.RETAIL: [
        "Westfield Mall",
        "Galleria Shopping Center",
        "Fashion Valley",
        "King of Prussia Mall",
        "Mall of America",
        "South Coast Plaza",
        "Tysons Corner Center",
        "Aventura Mall",
        "Roosevelt Field Mall",
        "Ala Moana Center",
    ],
    LocationType.TRANSPORTATION: [
        "Grand Central Terminal",
        "Union Station",
        "Penn Station",
        "O'Hare Airport",
        "JFK International Airport",
        "LAX Terminal",
        "Port Authority Bus Terminal",
        "Atlanta Airport",
        "Denver International Airport",
        "San Francisco Airport",
    ],
    LocationType.OTHER: [
        "Central Park",
        "Golden Gate Park",
        "Disney World",
        "Universal Studios",
        "SeaWorld",
        "Lincoln Center",
        "Madison Square Garden",
        "Metropolitan Museum",
        "Hollywood Bowl",
        "Red Rocks Amphitheater",
    ],
}

# Maintenance partners
MAINTENANCE_PARTNERS = [
    "PolarCare Services Inc.",
    "IceTech Maintenance Co.",
    "CoolServe Technicians",
    "FrostyFix Solutions",
    "ChillMasters Repair",
    "VendingCare Partners",
    "MachineHealth Experts",
    "TechnoChill Services",
    "VendingFix Professionals",
    "ColdStream Maintenance",
]


def random_date(start_date, end_date):
    """Generate a random date between start_date and end_date"""
    time_delta = end_date - start_date
    random_days = random.randrange(time_delta.days)
    return start_date + timedelta(days=random_days)


def generate_water_heater_readings(
    count=24, base_temp=45.0, variance=5.0, timestamp_hours_ago=24
):
    """Generate random temperature readings over a period of time"""
    now = datetime.now()
    readings = []

    for i in range(count):
        # Generate timestamp, going backward in time
        hours_back = (timestamp_hours_ago / count) * (count - i)
        timestamp = now - timedelta(hours=hours_back)

        # Generate temperature with some variance and a trend
        trend_factor = i / count  # 0 to 1
        temp = base_temp + (random.random() * variance) - (variance / 2)

        # Add some cyclical patterns to simulate day/night
        hour_of_day = timestamp.hour
        if 8 <= hour_of_day <= 18:  # Daytime
            temp += 2.0  # Slightly warmer during the day

        # Generate other metrics
        pressure = round(random.uniform(1.5, 3.0), 1)  # bar
        energy_usage = round(random.uniform(800, 2500), 0)  # watts
        flow_rate = (
            round(random.uniform(0.0, 12.0), 1) if random.random() > 0.3 else 0.0
        )  # L/min

        reading = WaterHeaterReading(
            timestamp=timestamp,
            temperature=round(temp, 1),
            pressure=pressure,
            energy_usage=energy_usage,
            flow_rate=flow_rate,
        )
        readings.append(reading)

    return readings


# Product categories and names for vending machines
PRODUCT_CATEGORIES = ["Beverages", "Snacks", "Candy", "Meals", "Healthy Options"]

PRODUCT_NAMES = {
    "Beverages": [
        "Polar Chill Water",
        "Arctic Blast Soda",
        "Mountain Fresh Juice",
        "Iced Coffee",
        "Energy Shot",
        "Sparkling Water",
        "Fruit Smoothie",
        "Iced Tea",
    ],
    "Snacks": [
        "Crunchy Chips",
        "Pretzel Twists",
        "Trail Mix",
        "Cheese Crackers",
        "Popcorn",
        "Protein Bar",
        "Nuts Mix",
        "Rice Crisps",
    ],
    "Candy": [
        "Chocolate Bar",
        "Gummy Bears",
        "Mints",
        "Caramel Chews",
        "Sour Candy",
        "Licorice",
        "Hard Candy",
        "Chocolate Cookies",
    ],
    "Meals": [
        "Sandwich",
        "Pasta Cup",
        "Instant Noodles",
        "Burrito",
        "Salad Bowl",
        "Soup Cup",
        "Wrap",
        "Rice Bowl",
    ],
    "Healthy Options": [
        "Fruit Cup",
        "Veggie Chips",
        "Protein Snack",
        "Granola Bar",
        "Mixed Nuts",
        "Dried Fruit",
        "Greek Yogurt",
        "Hummus & Crackers",
    ],
}

# Commercial and residential water heater models with their specs
COMMERCIAL_WATER_HEATER_MODELS = [
    {"name": "EcoHeat C-1000", "capacity": 1000, "max_temp": 85.0, "efficiency": 0.93},
    {
        "name": "ThermoGuard Industrial-1500",
        "capacity": 1500,
        "max_temp": 85.0,
        "efficiency": 0.95,
    },
    {
        "name": "HydroHeat Commercial-2000",
        "capacity": 2000,
        "max_temp": 85.0,
        "efficiency": 0.97,
    },
    {
        "name": "SmartTemp Enterprise-3000",
        "capacity": 3000,
        "max_temp": 85.0,
        "efficiency": 0.98,
    },
]

RESIDENTIAL_WATER_HEATER_MODELS = [
    {"name": "SmartTemp Home-50", "capacity": 50, "max_temp": 75.0, "efficiency": 0.85},
    {"name": "EcoHeat Family-80", "capacity": 80, "max_temp": 75.0, "efficiency": 0.88},
    {
        "name": "AquaWarm Comfort-100",
        "capacity": 100,
        "max_temp": 75.0,
        "efficiency": 0.90,
    },
    {
        "name": "ThermoGuard Premium-150",
        "capacity": 150,
        "max_temp": 75.0,
        "efficiency": 0.92,
    },
]

# Diagnostic codes for each water heater type
COMMERCIAL_DIAGNOSTIC_CODES = [
    {"code": "C001", "description": "High temperature warning", "severity": "Warning"},
    {
        "code": "C002",
        "description": "Critical high temperature",
        "severity": "Critical",
    },
    {"code": "C003", "description": "Low pressure warning", "severity": "Warning"},
    {"code": "C004", "description": "High pressure warning", "severity": "Warning"},
    {"code": "C005", "description": "Critical high pressure", "severity": "Critical"},
    {
        "code": "C006",
        "description": "Control board communication error",
        "severity": "Warning",
    },
    {
        "code": "C007",
        "description": "Temperature sensor failure",
        "severity": "Critical",
    },
    {"code": "C008", "description": "Pressure sensor failure", "severity": "Critical"},
    {"code": "C009", "description": "Flow meter error", "severity": "Warning"},
    {"code": "C010", "description": "Heating element failure", "severity": "Critical"},
    {"code": "C011", "description": "Low flow rate", "severity": "Warning"},
    {"code": "C012", "description": "Anode rod depletion", "severity": "Maintenance"},
    {
        "code": "C013",
        "description": "Scale buildup detected",
        "severity": "Maintenance",
    },
    {"code": "C014", "description": "Network connectivity lost", "severity": "Warning"},
    {"code": "C015", "description": "Energy usage anomaly", "severity": "Warning"},
    {
        "code": "C016",
        "description": "Operating efficiency decline",
        "severity": "Maintenance",
    },
    {"code": "C017", "description": "Failed power relay", "severity": "Critical"},
    {
        "code": "C018",
        "description": "Multiple heating element failure",
        "severity": "Critical",
    },
    {"code": "C019", "description": "Water leakage detected", "severity": "Critical"},
    {
        "code": "C020",
        "description": "Temperature regulation failure",
        "severity": "Critical",
    },
]

RESIDENTIAL_DIAGNOSTIC_CODES = [
    {"code": "R001", "description": "High temperature warning", "severity": "Warning"},
    {
        "code": "R002",
        "description": "Critical high temperature",
        "severity": "Critical",
    },
    {"code": "R003", "description": "Low pressure warning", "severity": "Warning"},
    {"code": "R004", "description": "High pressure warning", "severity": "Warning"},
    {"code": "R005", "description": "Critical high pressure", "severity": "Critical"},
    {"code": "R006", "description": "Control system error", "severity": "Warning"},
    {"code": "R007", "description": "Temperature sensor error", "severity": "Critical"},
    {"code": "R008", "description": "Pressure sensor error", "severity": "Warning"},
    {"code": "R009", "description": "Water leak detected", "severity": "Critical"},
    {"code": "R010", "description": "Heating element failure", "severity": "Critical"},
    {"code": "R011", "description": "WiFi connection lost", "severity": "Info"},
    {
        "code": "R012",
        "description": "Scale buildup detected",
        "severity": "Maintenance",
    },
    {"code": "R013", "description": "Anode rod depletion", "severity": "Maintenance"},
    {"code": "R014", "description": "Efficiency reduced", "severity": "Warning"},
    {"code": "R015", "description": "Unusual usage pattern", "severity": "Info"},
    {"code": "R016", "description": "Vacation mode active", "severity": "Info"},
    {"code": "R017", "description": "Power outage recovery", "severity": "Info"},
    {"code": "R018", "description": "Multiple heating cycles", "severity": "Warning"},
    {"code": "R019", "description": "Long recovery time", "severity": "Warning"},
    {"code": "R020", "description": "Energy usage high", "severity": "Warning"},
]


def generate_random_diagnostic_codes(heater_type, count=2):
    """Generate random diagnostic codes for a water heater"""
    code_list = (
        COMMERCIAL_DIAGNOSTIC_CODES
        if heater_type == WaterHeaterType.COMMERCIAL
        else RESIDENTIAL_DIAGNOSTIC_CODES
    )
    selected_codes = random.sample(code_list, min(count, len(code_list)))

    diagnostic_codes = []
    for code_info in selected_codes:
        # 70% of codes are active, 30% resolved
        active = random.random() < 0.7

        # Create a diagnostic code with a random timestamp
        timestamp = random_date(
            datetime.now() - timedelta(days=7), datetime.now() - timedelta(minutes=5)
        )

        diagnostic_code = WaterHeaterDiagnosticCode(
            code=code_info["code"],
            description=code_info["description"],
            severity=code_info["severity"],
            timestamp=timestamp,
            active=active,
        )
        diagnostic_codes.append(diagnostic_code)

    return diagnostic_codes


def generate_water_heaters(count=5):
    """Generate random water heaters"""
    heaters = []

    # Ensure at least one water heater of each type
    commercial_count = max(1, count // 3)  # Approx 1/3 commercial
    residential_count = count - commercial_count

    # Generate commercial water heaters
    for i in range(commercial_count):
        # Generate basic properties
        id_suffix = str(uuid.uuid4())[:8]
        heater_id = f"wh-comm-{id_suffix}"

        # Select a commercial model
        model_info = random.choice(COMMERCIAL_WATER_HEATER_MODELS)
        brand = random.choice(WATER_HEATER_BRANDS)
        building = random.choice(BUILDINGS)
        location = random.choice(
            ["Boiler Room", "Utility Room", "Mechanical Room", "Basement"]
        )

        name = f"{building} {location} - {brand} {model_info['name']}"

        # Determine status - most should be online
        status = DeviceStatus.ONLINE if random.random() < 0.8 else DeviceStatus.OFFLINE

        # Generate temperatures
        target_temp = round(
            random.uniform(60.0, 75.0), 1
        )  # Commercial units run hotter
        current_temp = target_temp

        # If online, current temperature may vary from target
        if status == DeviceStatus.ONLINE:
            current_temp = round(target_temp + (random.random() * 5.0 - 2.5), 1)

        # Determine mode
        mode_choices = list(WaterHeaterMode)
        mode = random.choice(mode_choices)

        # Determine heater status
        if status == DeviceStatus.OFFLINE:
            heater_status = WaterHeaterStatus.STANDBY
        else:
            if current_temp < target_temp - 1.0:
                heater_status = WaterHeaterStatus.HEATING
            else:
                heater_status = WaterHeaterStatus.STANDBY

        # Create the commercial water heater with diagnostic codes
        heater = WaterHeater(
            id=heater_id,
            name=name,
            type=DeviceType.WATER_HEATER,
            status=status,
            location=f"{building} - {location}",
            last_seen=datetime.now()
            if status == DeviceStatus.ONLINE
            else random_date(
                datetime.now() - timedelta(days=7), datetime.now() - timedelta(hours=1)
            ),
            target_temperature=target_temp,
            current_temperature=current_temp,
            mode=mode,
            heater_status=heater_status,
            heater_type=WaterHeaterType.COMMERCIAL,
            capacity=model_info["capacity"],
            efficiency_rating=model_info["efficiency"],
            max_temperature=model_info["max_temp"],
            min_temperature=40.0,
            specification_link="/docs/specifications/water_heaters/commercial.md",
            readings=generate_water_heater_readings(
                count=random.randint(8, 24), base_temp=current_temp
            ),
            diagnostic_codes=generate_random_diagnostic_codes(
                WaterHeaterType.COMMERCIAL, random.randint(0, 3)
            ),
        )

        heaters.append(heater)

    # Generate residential water heaters
    for i in range(residential_count):
        # Generate basic properties
        id_suffix = str(uuid.uuid4())[:8]
        heater_id = f"wh-res-{id_suffix}"

        # Select a residential model
        model_info = random.choice(RESIDENTIAL_WATER_HEATER_MODELS)
        brand = random.choice(WATER_HEATER_BRANDS)
        building = random.choice(
            ["Apartment 101", "Apartment 202", "House 123", "Condo 456"]
        )
        location = random.choice(
            ["Bathroom", "Kitchen", "Utility Closet", "Garage", "Basement"]
        )

        name = f"{building} {location} - {brand} {model_info['name']}"

        # Determine status - most should be online
        status = DeviceStatus.ONLINE if random.random() < 0.8 else DeviceStatus.OFFLINE

        # Generate temperatures
        target_temp = round(
            random.uniform(45.0, 65.0), 1
        )  # Residential units run cooler
        current_temp = target_temp

        # If online, current temperature may vary from target
        if status == DeviceStatus.ONLINE:
            current_temp = round(target_temp + (random.random() * 5.0 - 2.5), 1)

        # Determine mode
        mode_choices = list(WaterHeaterMode)
        mode = random.choice(mode_choices)

        # Determine heater status
        if status == DeviceStatus.OFFLINE:
            heater_status = WaterHeaterStatus.STANDBY
        else:
            if current_temp < target_temp - 1.0:
                heater_status = WaterHeaterStatus.HEATING
            else:
                heater_status = WaterHeaterStatus.STANDBY

        # Create the residential water heater with diagnostic codes
        heater = WaterHeater(
            id=heater_id,
            name=name,
            type=DeviceType.WATER_HEATER,
            status=status,
            location=f"{building} - {location}",
            last_seen=datetime.now()
            if status == DeviceStatus.ONLINE
            else random_date(
                datetime.now() - timedelta(days=7), datetime.now() - timedelta(hours=1)
            ),
            target_temperature=target_temp,
            current_temperature=current_temp,
            mode=mode,
            heater_status=heater_status,
            heater_type=WaterHeaterType.RESIDENTIAL,
            capacity=model_info["capacity"],
            efficiency_rating=model_info["efficiency"],
            max_temperature=model_info["max_temp"],
            min_temperature=40.0,
            specification_link="/docs/specifications/water_heaters/residential.md",
            readings=generate_water_heater_readings(
                count=random.randint(8, 24), base_temp=current_temp
            ),
            diagnostic_codes=generate_random_diagnostic_codes(
                WaterHeaterType.RESIDENTIAL, random.randint(0, 3)
            ),
        )

        heaters.append(heater)

    return heaters


def generate_products(count=10):
    """Generate random products for vending machines"""
    products = []

    for i in range(count):
        # Select random category
        category = random.choice(PRODUCT_CATEGORIES)

        # Select random product name from that category
        name = random.choice(PRODUCT_NAMES[category])

        # Generate unique product ID
        product_id = f"prod-{str(uuid.uuid4())[:8]}"

        # Generate price (between $1.00 and $5.00)
        price = round(random.uniform(1.0, 5.0), 2)

        # Generate quantity (between 0 and 15)
        quantity = random.randint(0, 15)

        # Generate slot/row location
        row = random.choice(["A", "B", "C", "D", "E"])
        column = random.randint(1, 8)
        location = f"{row}{column}"

        product = ProductItem(
            product_id=product_id,
            name=name,
            price=price,
            quantity=quantity,
            category=category,
            location=location,
        )
        products.append(product)

    return products


def generate_vending_machine_readings(
    count=24, base_temp=3.5, variance=1.0, timestamp_hours_ago=24
):
    """Generate random vending machine readings over a period of time"""
    now = datetime.now()
    readings = []

    for i in range(count):
        # Generate timestamp, going backward in time
        hours_back = (timestamp_hours_ago / count) * (count - i)
        timestamp = now - timedelta(hours=hours_back)

        # Generate temperature with some variance and a trend
        trend_factor = i / count  # 0 to 1
        temp = base_temp + (random.random() * variance) - (variance / 2)

        # Add some cyclical patterns to simulate day/night
        hour_of_day = timestamp.hour
        if 8 <= hour_of_day <= 18:  # Daytime
            temp += 0.5  # Slightly warmer during the day

        # Generate other metrics
        power_consumption = round(random.uniform(100, 400), 1)  # watts
        door_status = "CLOSED" if random.random() > 0.1 else "OPEN"
        cash_level = round(random.uniform(20, 500), 2)  # dollars
        sales_count = random.randint(0, 5)  # sales in this period

        reading = VendingMachineReading(
            timestamp=timestamp,
            temperature=round(temp, 1),
            power_consumption=power_consumption,
            door_status=door_status,
            cash_level=cash_level,
            sales_count=sales_count,
        )
        readings.append(reading)

    return readings


def generate_vending_machines(count=30):
    """Generate random vending machines"""
    machines = []

    for i in range(count):
        # Generate basic properties
        id_suffix = str(uuid.uuid4())[:8]
        vm_id = f"vm-{id_suffix}"

        # Generate location type first (to match business name)
        location_type = random.choice(list(LocationType))

        # Generate more descriptive and unique name
        brand = random.choice(VENDING_MACHINE_BRANDS)
        model = random.choice(VENDING_MACHINE_MODELS)
        building = random.choice(BUILDINGS)
        location = random.choice(LOCATIONS)

        # Generate descriptive name based on location type
        name = f"PolarDelight - {model} {id_suffix[:4]}"

        # Generate specifications
        model_number = f"{model}-{random.randint(100, 999)}"
        serial_number = f"SN-{str(uuid.uuid4())[:10]}"
        temp = round(random.uniform(2.5, 5.0), 1)  # Celsius
        total_capacity = random.randint(30, 80)
        cash_capacity = float(random.randint(500, 2000))
        current_cash = round(random.uniform(50, cash_capacity), 2)

        # Generate status and mode
        status_weights = {
            VendingMachineStatus.OPERATIONAL: 0.7,
            VendingMachineStatus.NEEDS_RESTOCK: 0.15,
            VendingMachineStatus.OUT_OF_STOCK: 0.05,
            VendingMachineStatus.MAINTENANCE_REQUIRED: 0.1,
        }
        statuses = list(status_weights.keys())
        status_probabilities = list(status_weights.values())
        machine_status = random.choices(statuses, status_probabilities)[0]

        mode_weights = {
            VendingMachineMode.NORMAL: 0.8,
            VendingMachineMode.POWER_SAVE: 0.15,
            VendingMachineMode.CLEANING: 0.05,
        }
        modes = list(mode_weights.keys())
        mode_probabilities = list(mode_weights.values())
        mode = random.choices(modes, mode_probabilities)[0]

        # Generate products (5-15 products per machine)
        product_count = random.randint(5, 15)
        products = generate_products(product_count)

        # Generate device status based on machine status
        device_status = DeviceStatus.ONLINE
        if machine_status == VendingMachineStatus.MAINTENANCE_REQUIRED:
            # 50% chance of being offline if maintenance is required
            if random.random() < 0.5:
                device_status = DeviceStatus.OFFLINE

        # Generate location details based on location type
        location_business_name = random.choice(BUSINESS_NAMES[location_type])
        sub_location = random.choice(list(SubLocation))

        # For use type, focus on SERVICED and SELF_SERVE as requested
        use_type_weights = {UseType.SERVICED: 0.6, UseType.SELF_SERVE: 0.4}
        use_types = list(use_type_weights.keys())
        use_type_probabilities = list(use_type_weights.values())
        use_type = random.choices(use_types, use_type_probabilities)[0]

        # Add maintenance partner
        maintenance_partner = random.choice(MAINTENANCE_PARTNERS)

        # Create the vending machine
        vending_machine = VendingMachine(
            id=vm_id,
            name=name,
            type=DeviceType.VENDING_MACHINE,
            status=device_status,
            location=f"{building} - {location}",
            model_number=model_number,
            serial_number=serial_number,
            machine_status=machine_status,
            mode=mode,
            location_business_name=location_business_name,
            location_type=location_type,
            sub_location=sub_location,
            use_type=use_type,
            temperature=temp,
            total_capacity=total_capacity,
            cash_capacity=cash_capacity,
            current_cash=current_cash,
            maintenance_partner=maintenance_partner,
            products=products,
            readings=generate_vending_machine_readings(
                count=random.randint(8, 24), base_temp=temp
            ),
        )

        machines.append(vending_machine)

    return machines


import json
import os
from pathlib import Path


# Demo data repository
class DummyDataRepository:
    """Repository of dummy data for testing with JSON persistence"""

    _instance = None
    _data_dir = (
        Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "data"
    )
    _water_heaters_file = _data_dir / "water_heaters.json"
    _vending_machines_file = _data_dir / "vending_machines.json"

    def __new__(cls):
        import logging

        logging.error("DummyDataRepository.__new__ called")

        if cls._instance is None:
            logging.error("Creating new DummyDataRepository instance")
            cls._instance = super(DummyDataRepository, cls).__new__(cls)

            # Ensure data directory exists
            os.makedirs(cls._data_dir, exist_ok=True)

            # Initialize data containers
            cls._instance.water_heaters = {}
            cls._instance.vending_machines = {}

            # Initialize data (only if no persisted data exists)
            cls._instance.initialize()
        else:
            logging.error("Reusing existing DummyDataRepository instance")

        return cls._instance

    def initialize(self):
        """Initialize with dummy data, loading from JSON if available"""
        import logging

        logging.error("DummyDataRepository.initialize() called")

        # Try to load from persistent storage first
        data_loaded = self._load_persisted_data()

        if not data_loaded:
            # Generate water heaters if not loaded from JSON
            water_heaters = generate_water_heaters(count=8)
            self.water_heaters = {heater.id: heater for heater in water_heaters}
            logging.error(f"Generated {len(water_heaters)} water heaters")

            # Load AquaTherm water heaters
            try:
                aquatherm_heaters = get_aquatherm_water_heaters()
                aquatherm_ids = [h["id"] for h in aquatherm_heaters]
                logging.error(
                    f"Loading AquaTherm water heaters with IDs: {aquatherm_ids}"
                )

                # Convert dict to WaterHeater model objects
                for heater_data in aquatherm_heaters:
                    # Create a WaterHeater object
                    heater = WaterHeater(
                        id=heater_data["id"],
                        name=heater_data["name"],
                        type=DeviceType.WATER_HEATER,
                        manufacturer=heater_data["manufacturer"],
                        model=heater_data["model"],
                        status=DeviceStatus(heater_data["status"]),
                        heater_status=WaterHeaterStatus(heater_data["heater_status"]),
                        mode=WaterHeaterMode(heater_data["mode"]),
                        current_temperature=heater_data["current_temperature"],
                        target_temperature=heater_data["target_temperature"],
                        min_temperature=heater_data["min_temperature"],
                        max_temperature=heater_data["max_temperature"],
                        last_seen=datetime.now(),
                        last_updated=datetime.now(),
                        properties=heater_data.get("properties", {}),
                        readings=[],
                        heater_type=WaterHeaterType.RESIDENTIAL,
                    )

                    # Add to our water heaters dictionary
                    self.water_heaters[heater.id] = heater

                logging.error(
                    f"Successfully added {len(aquatherm_heaters)} AquaTherm water heaters"
                )
            except Exception as e:
                logging.error(f"Error loading AquaTherm test data: {str(e)}")

            # Generate vending machines if not loaded from JSON
            vending_machines = generate_vending_machines(count=30)
            logging.error(
                f"Generated {len(vending_machines)} vending machines with IDs: {[vm.id for vm in vending_machines]}"
            )
            self.vending_machines = {vm.id: vm for vm in vending_machines}

            # Save the generated data
            self._persist_data()

    def get_water_heaters(self):
        """Get all water heaters"""
        return list(self.water_heaters.values())

    def get_water_heater(self, heater_id):
        """Get a specific water heater by ID"""
        return self.water_heaters.get(heater_id)

    def add_water_heater(self, heater):
        """Add a new water heater"""
        self.water_heaters[heater.id] = heater
        self._persist_data()
        return heater

    def update_water_heater(self, heater_id, updates):
        """Update a water heater"""
        if heater_id not in self.water_heaters:
            return None

        heater = self.water_heaters[heater_id]
        updated_heater = heater.model_copy(update=updates)
        self.water_heaters[heater_id] = updated_heater
        return updated_heater

    def get_vending_machines(self):
        """Get all vending machines"""
        import logging

        machines = list(self.vending_machines.values())
        logging.error(
            f"DummyDataRepository.get_vending_machines() returning {len(machines)} machines with IDs: {[m.id for m in machines]}"
        )
        return machines

    def get_vending_machine(self, vm_id):
        """Get a specific vending machine by ID"""
        return self.vending_machines.get(vm_id)

    def add_vending_machine(self, machine):
        """Add a new vending machine"""
        self.vending_machines[machine.id] = machine
        self._persist_data()
        return machine

    def update_vending_machine(self, vm_id, updates):
        """Update a vending machine"""
        if vm_id not in self.vending_machines:
            return None

        machine = self.vending_machines[vm_id]
        updated_machine = machine.model_copy(update=updates)
        self.vending_machines[vm_id] = updated_machine
        return updated_machine

    def delete_vending_machine(self, vm_id):
        """Delete a vending machine"""
        if vm_id in self.vending_machines:
            del self.vending_machines[vm_id]
            self._persist_data()
            return True
        return False

    def _persist_data(self):
        """Save data to JSON files for persistence"""
        try:
            # Convert water heaters to JSON-serializable dictionaries
            water_heaters_data = {}
            for wh_id, wh in self.water_heaters.items():
                water_heaters_data[wh_id] = wh.model_dump()

            # Convert vending machines to JSON-serializable dictionaries
            vending_machines_data = {}
            for vm_id, vm in self.vending_machines.items():
                vending_machines_data[vm_id] = vm.model_dump()

            # Save water heaters
            with open(self._water_heaters_file, "w") as f:
                json.dump(water_heaters_data, f, indent=2, default=str)

            # Save vending machines
            with open(self._vending_machines_file, "w") as f:
                json.dump(vending_machines_data, f, indent=2, default=str)

            import logging

            logging.info(f"Persisted data to {self._data_dir}")
            return True
        except Exception as e:
            import logging

            logging.error(f"Error persisting data: {e}")
            return False

    def _load_persisted_data(self):
        """Load data from JSON files if they exist"""
        import logging

        try:
            if not os.path.exists(self._water_heaters_file) or not os.path.exists(
                self._vending_machines_file
            ):
                logging.info("No persisted data files found, will generate new data")
                return False

            # Load water heaters
            with open(self._water_heaters_file, "r") as f:
                water_heaters_data = json.load(f)

            # Load vending machines
            with open(self._vending_machines_file, "r") as f:
                vending_machines_data = json.load(f)

            # Convert JSON data back to models
            for wh_id, wh_data in water_heaters_data.items():
                # Convert string date-times back to datetime objects
                if "created_at" in wh_data and wh_data["created_at"]:
                    wh_data["created_at"] = datetime.fromisoformat(
                        wh_data["created_at"]
                    )
                if "updated_at" in wh_data and wh_data["updated_at"]:
                    wh_data["updated_at"] = datetime.fromisoformat(
                        wh_data["updated_at"]
                    )

                # Convert readings
                if "readings" in wh_data and wh_data["readings"]:
                    readings = []
                    for reading in wh_data["readings"]:
                        if "timestamp" in reading and reading["timestamp"]:
                            reading["timestamp"] = datetime.fromisoformat(
                                reading["timestamp"]
                            )
                        readings.append(WaterHeaterReading(**reading))
                    wh_data["readings"] = readings

                self.water_heaters[wh_id] = WaterHeater(**wh_data)

            # Similarly for vending machines
            for vm_id, vm_data in vending_machines_data.items():
                # Convert string date-times back to datetime objects
                if "created_at" in vm_data and vm_data["created_at"]:
                    vm_data["created_at"] = datetime.fromisoformat(
                        vm_data["created_at"]
                    )
                if "updated_at" in vm_data and vm_data["updated_at"]:
                    vm_data["updated_at"] = datetime.fromisoformat(
                        vm_data["updated_at"]
                    )

                # Convert readings
                if "readings" in vm_data and vm_data["readings"]:
                    readings = []
                    for reading in vm_data["readings"]:
                        if "timestamp" in reading and reading["timestamp"]:
                            reading["timestamp"] = datetime.fromisoformat(
                                reading["timestamp"]
                            )
                        readings.append(VendingMachineReading(**reading))
                    vm_data["readings"] = readings

                # Convert products
                if "products" in vm_data and vm_data["products"]:
                    products = []
                    for product in vm_data["products"]:
                        products.append(ProductItem(**product))
                    vm_data["products"] = products

                self.vending_machines[vm_id] = VendingMachine(**vm_data)

            logging.info(
                f"Loaded {len(self.water_heaters)} water heaters and {len(self.vending_machines)} vending machines from persisted data"
            )
            return True
        except Exception as e:
            logging.error(f"Error loading persisted data: {e}")
            return False


# Create a singleton instance
dummy_data = DummyDataRepository()
