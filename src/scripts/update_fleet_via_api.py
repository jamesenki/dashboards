"""
This script updates the vending machine fleet by sending the data directly to the API.
This ensures that the running server will have access to the new data.
"""

import sys
import os
import json
import requests
from datetime import datetime, timedelta
import random
import uuid

# Add the parent directory to path so we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.vending_machine import (
    VendingMachine, VendingMachineStatus, VendingMachineMode, 
    ProductItem, VendingMachineReading, LocationType, UseType
)
from models.device import DeviceStatus, DeviceType

# Configuration
NUM_MACHINES = 30  # Number of vending machines to generate
API_URL = "http://localhost:8006/api/vending-machines"

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

def prepare_vending_machine_for_api(index):
    """Create a vending machine data dictionary ready for API submission"""
    vm_id = f"vm-{100 + index}"
    
    # Create a deterministic random seed for consistent mock data
    random.seed(sum(ord(c) for c in vm_id) + index)
    
    # Randomize location type
    location_type = random.choice(list(LocationType)).value
    
    # Randomize location details based on location type
    if location_type == LocationType.RETAIL:
        sub_locations = ["Entrance", "Checkout Area", "Food Court", "Electronics Dept", "Home Goods", "Customer Service"]
        use_type = UseType.CUSTOMER.value
    elif location_type == LocationType.OFFICE:
        sub_locations = ["Lobby", "Break Room", "Cafeteria", "Conference Area", "Main Office", "Reception"]
        use_type = UseType.EMPLOYEE.value
    elif location_type == LocationType.SCHOOL:
        sub_locations = ["Student Center", "Gymnasium", "Library", "Administration Building", "Cafeteria", "Dormitory"]
        use_type = UseType.STUDENT.value
    elif location_type == LocationType.HOSPITAL:
        sub_locations = ["Main Lobby", "ER Waiting Room", "Cafeteria", "Staff Lounge", "Patient Floor", "Visitor Area"]
        use_type = UseType.PATIENT.value
    elif location_type == LocationType.TRANSPORTATION:
        sub_locations = ["Main Terminal", "Waiting Area", "Ticketing Area", "Food Court", "Departure Gate", "Arrivals"]
        use_type = UseType.PUBLIC.value
    else:
        sub_locations = ["Main Area", "Lounge", "Entrance", "Public Space", "Common Area", "Recreation Zone"]
        use_type = UseType.OTHER.value
    
    sub_location = random.choice(sub_locations)
    
    # Select a business name and format location
    business_name = random.choice(BUSINESS_NAMES)
    city = random.choice(CITIES)
    location = f"{business_name}, {city}"
    
    # Realistic model and serial numbers
    year = random.choice([2021, 2022, 2023, 2024])
    model_number = f"PD-{year}-{5000 + random.randint(0, 999)}"
    serial_number = f"SN{year}{random.randint(10000, 99999)}"
    
    # Maintenance details - convert to string format for API
    maintenance_partner = random.choice([
        "PolarService Co.", "ColdFix Solutions", "IceCream Tech", "FreezeMasters", "Arctic Maintenance"
    ])
    last_maintenance = (datetime.now() - timedelta(days=random.randint(10, 90))).isoformat()
    next_maintenance = (datetime.now() + timedelta(days=random.randint(30, 180))).isoformat()
    
    # Machine status based on randomized factors
    status_weights = [
        (VendingMachineStatus.OPERATIONAL.value, 0.7),
        (VendingMachineStatus.NEEDS_RESTOCK.value, 0.15),
        (VendingMachineStatus.OUT_OF_STOCK.value, 0.05),
        (VendingMachineStatus.MAINTENANCE_REQUIRED.value, 0.1)
    ]
    
    machine_status = random.choices(
        [status[0] for status in status_weights],
        weights=[status[1] for status in status_weights],
        k=1
    )[0]
    
    # Current temperature (for frozen treats)
    temperature = round(random.uniform(-6.5, -2.5), 1)
    
    # Device status
    device_status = DeviceStatus.ONLINE.value if random.random() < 0.9 else DeviceStatus.OFFLINE.value
    
    # Create vending machine data for API
    vm_data = {
        "name": f"Polar Delight #{100 + index}",
        "location": location,
        "model_number": model_number,
        "serial_number": serial_number,
        "temperature": temperature,
        "total_capacity": 50,
        "cash_capacity": 500.0,
        "current_cash": round(random.uniform(50.0, 450.0), 2),
        "location_business_name": business_name,
        "location_type": location_type,
        "sub_location": sub_location,
        "use_type": use_type,
        "maintenance_partner": maintenance_partner,
        "last_maintenance_date": last_maintenance,
        "next_maintenance_date": next_maintenance,
        "machine_status": machine_status,
        "mode": VendingMachineMode.NORMAL.value,
        "status": device_status
    }
    
    return vm_data

def main():
    """Create new vending machines directly via the API"""
    print(f"Creating {NUM_MACHINES} Polar Delight vending machines via API...")
    
    # First, delete all existing vending machines
    try:
        # Get existing machines
        response = requests.get(API_URL)
        if response.status_code == 200:
            existing_machines = response.json()
            
            # Delete each machine
            for machine in existing_machines:
                vm_id = machine.get("id")
                if vm_id:
                    delete_response = requests.delete(f"{API_URL}/{vm_id}")
                    if delete_response.status_code == 204:
                        print(f"  Deleted existing machine {vm_id}")
                    else:
                        print(f"  Failed to delete machine {vm_id}: {delete_response.status_code}")
        else:
            print(f"Failed to get existing machines: {response.status_code}")
    except Exception as e:
        print(f"Error during deletion: {e}")
    
    # Create new machines
    success_count = 0
    for i in range(NUM_MACHINES):
        vm_data = prepare_vending_machine_for_api(i)
        
        try:
            response = requests.post(API_URL, json=vm_data)
            if response.status_code == 201:
                machine = response.json()
                print(f"  Created {machine['name']} ({machine['id']}) at {machine['location_business_name']}")
                success_count += 1
            else:
                print(f"  Failed to create machine {i}: {response.status_code}")
                print(f"  Response: {response.text}")
        except Exception as e:
            print(f"  Error creating machine {i}: {e}")
    
    print(f"\nSuccessfully created {success_count} of {NUM_MACHINES} vending machines")
    print("\nThe new vending machines should now be visible in the dropdown!")

if __name__ == "__main__":
    main()
