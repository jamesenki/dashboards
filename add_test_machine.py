import json
import os
import sys
import time
from datetime import datetime

import requests


# Add script to modify the service to create a vending machine with a specific ID
def add_test_machine():
    # Define test machine data with the specific ID
    test_machine = {
        "name": "Polar Delight Test Machine",
        "location": "Building A, Floor 1",
        "model_number": "PD-2000",
        "serial_number": "SN12345",
        "machine_status": "OPERATIONAL",
        "mode": "NORMAL",
        "temperature": -5.0,
        "total_capacity": 100,
        "cash_capacity": 1000.0,
        "current_cash": 450.0,
    }

    try:
        # First, create the vending machine
        response = requests.post(
            "http://localhost:8007/api/vending-machines", json=test_machine
        )
        response.raise_for_status()

        vm_data = response.json()
        vm_id = vm_data["id"]
        print(f"Created vending machine with ID: {vm_id}")

        # Now add some products to it
        products = [
            {
                "product_id": "product-1",
                "name": "Polar Ice Cream",
                "price": 3.50,
                "quantity": 15,
                "category": "Ice Cream",
                "location": "A1",
            },
            {
                "product_id": "product-2",
                "name": "Arctic Freeze",
                "price": 4.00,
                "quantity": 10,
                "category": "Ice Cream",
                "location": "A2",
            },
            {
                "product_id": "product-3",
                "name": "Glacier Mint",
                "price": 3.75,
                "quantity": 12,
                "category": "Ice Cream",
                "location": "B1",
            },
        ]

        for product in products:
            response = requests.post(
                f"http://localhost:8007/api/vending-machines/{vm_id}/products",
                json=product,
            )
            response.raise_for_status()
            print(f"Added product: {product['name']}")

        # Add a reading to the machine
        reading = {
            "temperature": -5.2,
            "power_consumption": 120.5,
            "door_status": "CLOSED",
            "cash_level": 450.0,
            "sales_count": 5,
        }

        response = requests.post(
            f"http://localhost:8007/api/vending-machines/{vm_id}/readings", json=reading
        )
        response.raise_for_status()
        print("Added machine reading")

        print("\nTest data has been loaded successfully!")
        print(
            f"You can now access the operations summary at: http://localhost:8007/vending-machines/{vm_id}"
        )

        # Get all machines to see what's available
        response = requests.get("http://localhost:8007/api/vending-machines")
        machines = response.json()
        print("\nAvailable vending machines:")
        for machine in machines:
            print(f"ID: {machine['id']}, Name: {machine['name']}")

        return vm_id

    except requests.exceptions.RequestException as e:
        print(f"Error creating test data: {e}")
        return None


if __name__ == "__main__":
    vm_id = add_test_machine()
    if vm_id:
        print(f"\nTry accessing these URLs:")
        print(f"1. Main machine page: http://localhost:8007/vending-machines/{vm_id}")
        print(
            f"2. Operations API: http://localhost:8007/api/vending-machines/{vm_id}/operations"
        )
