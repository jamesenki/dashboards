"""
Generate a fleet of Polar Delight vending machines with realistic randomized data.
This script will create a large set of vending machines and save them to the dummy data repository.
"""

import sys
import os
import random
from datetime import datetime, timedelta
import uuid

# Add the parent directory to path so we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.vending_machine import (
    VendingMachine, VendingMachineStatus, VendingMachineMode, 
    ProductItem, VendingMachineReading, LocationType, UseType
)
from models.device import DeviceStatus, DeviceType
from utils.dummy_data import DummyDataRepository

# Configuration
NUM_MACHINES = 30  # Number of vending machines to generate
NUM_READINGS_PER_MACHINE = 48  # Number of readings per machine (e.g., 2 days worth of hourly readings)
PRODUCTS_PER_MACHINE_MIN = 8  # Minimum products per machine
PRODUCTS_PER_MACHINE_MAX = 20  # Maximum products per machine

# Data for generating realistic vending machines
CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", 
    "San Antonio", "San Diego", "Dallas", "San Jose", "Boston", "Atlanta", 
    "Miami", "Denver", "Portland", "Detroit", "Seattle", "Pittsburgh"
]

BUSINESS_NAMES = [
    "Sheetz", "Wawa", "7-Eleven", "Kroger", "Target", "Walmart", "Costco", 
    "BestBuy", "Office Depot", "University Medical", "Central Hospital", 
    "TechCorp", "MegaSoft", "Airport Terminal", "Train Station", "City Hall",
    "Community College", "State University", "Tech Institute", "Mall Plaza",
    "Business Center", "Fitness Center", "Sports Arena", "Library"
]

PRODUCT_FLAVORS = [
    "Classic", "Zero", "Berry", "Citrus", "Mint", "Cherry", 
    "Vanilla", "Chocolate", "Caramel", "Peach", "Apple", 
    "Strawberry", "Blueberry", "Coffee", "Lemon"
]

PRODUCT_TYPES = [
    "Polar Delight", "Icy Treat", "FrozenJoy", "CoolScoop", "Arctic Delight"
]

LOCATION_DETAILS = {
    LocationType.RETAIL: {
        "sub_locations": ["Entrance", "Checkout Area", "Food Court", "Electronics Dept", "Home Goods", "Customer Service"],
        "use_type": UseType.CUSTOMER
    },
    LocationType.OFFICE: {
        "sub_locations": ["Lobby", "Break Room", "Cafeteria", "Conference Area", "Main Office", "Reception"],
        "use_type": UseType.EMPLOYEE
    },
    LocationType.SCHOOL: {
        "sub_locations": ["Student Center", "Gymnasium", "Library", "Administration Building", "Cafeteria", "Dormitory"],
        "use_type": UseType.STUDENT
    },
    LocationType.HOSPITAL: {
        "sub_locations": ["Main Lobby", "ER Waiting Room", "Cafeteria", "Staff Lounge", "Patient Floor", "Visitor Area"],
        "use_type": UseType.PATIENT
    },
    LocationType.TRANSPORTATION: {
        "sub_locations": ["Main Terminal", "Waiting Area", "Ticketing Area", "Food Court", "Departure Gate", "Arrivals"],
        "use_type": UseType.PUBLIC
    },
    LocationType.OTHER: {
        "sub_locations": ["Main Area", "Lounge", "Entrance", "Public Space", "Common Area", "Recreation Zone"],
        "use_type": UseType.OTHER
    }
}

MAINTENANCE_PARTNERS = ["PolarService Co.", "ColdFix Solutions", "IceCream Tech", "FreezeMasters", "Arctic Maintenance"]

def generate_product(product_id):
    """Generate a random product item"""
    product_type = random.choice(PRODUCT_TYPES)
    flavor = random.choice(PRODUCT_FLAVORS)
    
    # Price tiers based on product type
    price_ranges = {
        "Polar Delight": (2.5, 4.0),
        "Icy Treat": (2.0, 3.5),
        "FrozenJoy": (3.0, 4.5),
        "CoolScoop": (2.8, 4.2),
        "Arctic Delight": (3.2, 4.8)
    }
    
    price_range = price_ranges.get(product_type, (2.0, 4.0))
    price = round(random.uniform(price_range[0], price_range[1]), 2)
    
    # Generate a gridded location for the product (e.g., A1, B3, etc.)
    row = chr(65 + random.randint(0, 5))  # A through F
    col = random.randint(1, 8)
    location = f"{row}{col}"
    
    # Randomize quantity with some products potentially out of stock
    quantity_weights = [(0, 0.05), (1, 0.05), (2, 0.1), (3, 0.1), (4, 0.15), 
                       (5, 0.15), (6, 0.1), (7, 0.1), (8, 0.1), (9, 0.05), (10, 0.05)]
    quantity = random.choices(
        [q[0] for q in quantity_weights],
        weights=[q[1] for q in quantity_weights],
        k=1
    )[0]
    
    category = "Beverages"  # All Polar Delight products are beverages
    
    return ProductItem(
        product_id=f"product-{product_id}",
        name=f"{product_type} {flavor}",
        price=price,
        quantity=quantity,
        category=category,
        location=location
    )

def generate_reading(vm_id, timestamp, is_recent=False):
    """Generate a random vending machine reading"""
    
    # Realistic temperature range for frozen treats
    temperature = round(random.uniform(-6.5, -2.5), 1)
    
    # Power consumption varies based on time of day
    hour = timestamp.hour
    if 9 <= hour <= 18:  # Higher during business hours
        power_consumption = round(random.uniform(120.0, 160.0), 1)
    else:  # Lower at night
        power_consumption = round(random.uniform(90.0, 120.0), 1)
    
    # Door status is mostly closed, occasionally open
    # Recent readings are more likely to have door activity
    door_probability = 0.02
    if is_recent:
        door_probability = 0.1
    
    door_status = "OPEN" if random.random() < door_probability else "CLOSED"
    
    # Cash level increases over time with sales
    # For random readings, we'll just pick a random value
    cash_level = round(random.uniform(50.0, 450.0), 2)
    
    # Sales count varies by time of day
    if 7 <= hour <= 9 or 11 <= hour <= 13 or 16 <= hour <= 18:  # Peak times
        sales_count = random.randint(2, 8)
    else:  # Off-peak
        sales_count = random.randint(0, 3)
    
    return VendingMachineReading(
        id=f"{vm_id}-reading-{uuid.uuid4().hex[:8]}",
        timestamp=timestamp,
        temperature=temperature,
        power_consumption=power_consumption,
        door_status=door_status,
        cash_level=cash_level,
        sales_count=sales_count
    )

def generate_vending_machine(index):
    """Generate a random vending machine with realistic data"""
    vm_id = f"vm-{100 + index}"
    
    # Create a deterministic random seed for consistent mock data
    random.seed(sum(ord(c) for c in vm_id) + index)
    
    # Randomize location type and details
    location_type = random.choice(list(LocationType))
    sub_location = random.choice(LOCATION_DETAILS[location_type]["sub_locations"])
    use_type = LOCATION_DETAILS[location_type]["use_type"]
    
    # Select a business name and format location
    business_name = random.choice(BUSINESS_NAMES)
    city = random.choice(CITIES)
    location = f"{business_name}, {city}"
    
    # Realistic model and serial numbers
    year = random.choice([2021, 2022, 2023, 2024])
    model_number = f"PD-{year}-{5000 + random.randint(0, 999)}"
    serial_number = f"SN{year}{random.randint(10000, 99999)}"
    
    # Maintenance details
    maintenance_partner = random.choice(MAINTENANCE_PARTNERS)
    last_maintenance = datetime.now() - timedelta(days=random.randint(10, 90))
    next_maintenance = datetime.now() + timedelta(days=random.randint(30, 180))
    
    # Machine status based on randomized factors
    status_weights = [
        (VendingMachineStatus.OPERATIONAL, 0.7),
        (VendingMachineStatus.NEEDS_RESTOCK, 0.15),
        (VendingMachineStatus.OUT_OF_STOCK, 0.05),
        (VendingMachineStatus.MAINTENANCE_REQUIRED, 0.1)
    ]
    
    machine_status = random.choices(
        [status[0] for status in status_weights],
        weights=[status[1] for status in status_weights],
        k=1
    )[0]
    
    # Generate products
    num_products = random.randint(PRODUCTS_PER_MACHINE_MIN, PRODUCTS_PER_MACHINE_MAX)
    products = [generate_product(i) for i in range(num_products)]
    
    # Check for out of stock condition
    total_quantity = sum(p.quantity for p in products)
    if total_quantity == 0:
        machine_status = VendingMachineStatus.OUT_OF_STOCK
    elif total_quantity < num_products * 2:
        machine_status = VendingMachineStatus.NEEDS_RESTOCK
    
    # Generate historical readings over the past 2 days
    now = datetime.now()
    readings = []
    for i in range(NUM_READINGS_PER_MACHINE):
        timestamp = now - timedelta(hours=NUM_READINGS_PER_MACHINE - i)
        is_recent = (i >= NUM_READINGS_PER_MACHINE - 4)  # Last 4 readings are "recent"
        readings.append(generate_reading(vm_id, timestamp, is_recent))
    
    # Use latest reading for current values
    latest_reading = readings[-1]
    
    # Current cash is based on latest reading
    current_cash = latest_reading.cash_level
    
    # Create the vending machine
    vending_machine = VendingMachine(
        id=vm_id,
        name=f"Polar Delight #{100 + index}",
        type=DeviceType.VENDING_MACHINE,
        status=DeviceStatus.ONLINE if random.random() < 0.9 else DeviceStatus.OFFLINE,
        location=location,
        model_number=model_number,
        serial_number=serial_number,
        machine_status=machine_status,
        mode=VendingMachineMode.NORMAL,
        temperature=latest_reading.temperature,
        total_capacity=50,
        cash_capacity=500.0,
        location_business_name=business_name,
        location_type=location_type,
        sub_location=sub_location,
        use_type=use_type,
        maintenance_partner=maintenance_partner,
        last_maintenance_date=last_maintenance,
        next_maintenance_date=next_maintenance,
        current_cash=current_cash,
        products=products,
        readings=readings
    )
    
    return vending_machine

def main():
    """Generate fleet data and update the dummy data repository"""
    print(f"Generating {NUM_MACHINES} Polar Delight vending machines...")
    
    # Both update the repository directly and update the server
    # 1. Update the repository directly for local access
    repository = DummyDataRepository()
    repository.vending_machines = {}  # Clear existing machines
    
    machines = []
    # Generate vending machines
    for i in range(NUM_MACHINES):
        machine = generate_vending_machine(i)
        repository.vending_machines[machine.id] = machine
        machines.append(machine)
        print(f"  Created {machine.name} ({machine.id}) at {machine.location_business_name}, {machine.sub_location}")
    
    print(f"\nSuccessfully generated {NUM_MACHINES} vending machines with realistic data")
    print(f"Total number of readings generated: {NUM_MACHINES * NUM_READINGS_PER_MACHINE}")
    print("\nData is ready for viewing in the dashboard!")
    
    # 2. Restart the server to pick up changes
    print("\nRestarting server to refresh data...")
    try:
        import psutil
        import os
        import signal
        import time
        
        # Find FastAPI process
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['name'] == 'python' and any('src.main' in arg for arg in proc.info['cmdline'] if arg):
                pid = proc.info['pid']
                print(f"Found server process with PID {pid}, restarting...")
                # Send SIGTERM to gracefully shutdown the process
                os.kill(pid, signal.SIGTERM)
                # Wait for process to terminate
                time.sleep(2)
                print("Server stopped. Restarting...")
                # Start the server again
                os.system('cd /Users/lisasimon/repos/IoTSphereAngular/IoTSphere-Refactor && python -m src.main &')
                time.sleep(3)
                print("Server restarted successfully!")
                break
        else:
            print("Server process not found. No restart needed.")
    except Exception as e:
        print(f"Failed to restart server: {e}")
    
    print("\nAll done! The vending machines should now be visible in the dropdown.")

if __name__ == "__main__":
    main()
