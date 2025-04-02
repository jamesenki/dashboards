"""
Vending machine data generator for creating synthetic test data.
"""
import json
import math
import os
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

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


class VendingMachineDataGenerator:
    """
    Generator for creating synthetic vending machine data for testing and development.
    """

    # Common product names for vending machines
    PRODUCT_NAMES = [
        "Polar Delight Classic",
        "Polar Delight Zero",
        "Polar Delight Cherry",
        "Polar Delight Lime",
        "Mountain Mist Original",
        "Mountain Mist Lemon",
        "Fizzy Pop Cola",
        "Fizzy Pop Diet",
        "Energy Surge",
        "Energy Surge Max",
        "Aqua Pure Water",
        "Chocolate Bliss",
        "Caramel Dream",
        "Nutty Delight",
        "Cheesy Crunch",
        "Savory Snack Mix",
        "Fruit Chews",
        "Sweet Cookies",
    ]

    PRODUCT_CATEGORIES = [
        "Beverages",
        "Snacks",
        "Candy",
        "Chips",
        "Chocolate",
        "Healthy Options",
    ]

    # Business names for locations
    BUSINESS_NAMES = [
        "Central Hospital",
        "City College",
        "Metro Station",
        "Office Tower",
        "Shopping Mall",
        "Community Center",
        "Industrial Park",
        "Tech Campus",
        "Fitness Center",
        "Public Library",
        "Convention Center",
        "Airport Terminal",
        "Business Park",
        "Medical Center",
        "Recreation Facility",
    ]

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the vending machine data generator with optional random seed.

        Args:
            seed: Optional random seed for reproducible data generation
        """
        self.seed = seed if seed is not None else 42  # Default seed for reproducibility
        self.rng = random.Random(self.seed)
        # Initialize numpy random with the same seed for distributions not in standard random
        np.random.seed(self.seed)

        # Dictionary to track properties of generated machines
        self._machine_properties = {}

    def generate_vending_machine(
        self,
        id: Optional[str] = None,
        usage_pattern: str = "high_traffic",
        stock_level: str = "normal",
    ) -> VendingMachine:
        """
        Generate a single vending machine with random but realistic properties.

        Args:
            id: Optional ID for the vending machine, will be auto-generated if None
            usage_pattern: Usage pattern type ("high_traffic", "low_traffic", "business_hours", "all_hours")
            stock_level: Stock level status ("full", "normal", "low", "empty")

        Returns:
            A vending machine instance with randomized properties
        """
        if id is None:
            id = f"vm-{uuid.uuid4().hex[:8]}"

        # Randomize location properties
        location_type = self.rng.choice(list(LocationType))
        location_business = self.rng.choice(self.BUSINESS_NAMES)
        sub_location = self.rng.choice(list(SubLocation))
        use_type = self.rng.choice(list(UseType))

        # Status depends on stock level
        if stock_level == "empty":
            machine_status = VendingMachineStatus.OUT_OF_STOCK
        elif stock_level == "low":
            machine_status = VendingMachineStatus.NEEDS_RESTOCK
        elif self.rng.random() < 0.1:  # 10% chance of maintenance needed
            machine_status = VendingMachineStatus.MAINTENANCE_REQUIRED
        else:
            machine_status = VendingMachineStatus.OPERATIONAL

        # Randomize machine properties
        name = f"Vending Machine {id}"
        model_number = f"PD-{self.rng.randint(1000, 9999)}"
        serial_number = f"SN{self.rng.randint(10000, 99999)}"
        capacity = self.rng.randint(40, 120)
        cash_capacity = self.rng.uniform(200, 500)
        current_cash = self.rng.uniform(0, cash_capacity / 2)
        temperature = self.rng.uniform(2, 7)  # Celsius for refrigerated items

        # Create the vending machine
        vending_machine = VendingMachine(
            id=id,
            name=name,
            status=DeviceStatus.ONLINE,
            location=f"{location_business} - {sub_location}",
            type=DeviceType.VENDING_MACHINE,
            model_number=model_number,
            serial_number=serial_number,
            machine_status=machine_status,
            mode=VendingMachineMode.NORMAL,
            temperature=round(temperature, 1),
            total_capacity=capacity,
            cash_capacity=round(cash_capacity, 2),
            current_cash=round(current_cash, 2),
            location_business_name=location_business,
            location_type=location_type,
            sub_location=sub_location,
            use_type=use_type,
        )

        # Generate maintenance information
        last_maintenance = datetime.now() - timedelta(days=self.rng.randint(10, 90))
        next_maintenance = last_maintenance + timedelta(days=self.rng.randint(90, 180))

        if vending_machine.machine_status == VendingMachineStatus.MAINTENANCE_REQUIRED:
            next_maintenance = datetime.now() - timedelta(days=self.rng.randint(1, 10))

        vending_machine.last_maintenance_date = last_maintenance
        vending_machine.next_maintenance_date = next_maintenance
        vending_machine.maintenance_partner = "TechServe Solutions"

        # We don't store these directly on the VendingMachine object since it's a Pydantic model with fixed fields
        # Instead we'll track them in our generator for internal use
        self._track_machine_properties(
            vending_machine.id,
            {"usage_pattern": usage_pattern, "stock_level": stock_level},
        )

        return vending_machine

    def generate_vending_machines(
        self, count: int = 5, usage_patterns: Optional[List[str]] = None
    ) -> List[VendingMachine]:
        """
        Generate multiple vending machines.

        Args:
            count: Number of vending machines to generate
            usage_patterns: Optional list of usage patterns to apply to the generated machines.
                           If provided, must have same length as count.

        Returns:
            List of vending machine instances
        """
        vending_machines = []

        if usage_patterns and len(usage_patterns) != count:
            raise ValueError(
                "If provided, usage_patterns must have same length as count"
            )

        for i in range(count):
            usage_pattern = "high_traffic"  # Default
            stock_level = "normal"  # Default

            if usage_patterns:
                usage_pattern = usage_patterns[i]
            else:
                # Random distribution of patterns
                pattern_choice = self.rng.choices(
                    ["high_traffic", "low_traffic", "business_hours", "all_hours"],
                    weights=[0.4, 0.2, 0.3, 0.1],
                    k=1,
                )[0]
                usage_pattern = pattern_choice

            # Randomize stock level
            stock_level_choice = self.rng.choices(
                ["full", "normal", "low", "empty"], weights=[0.2, 0.5, 0.2, 0.1], k=1
            )[0]

            vending_machine = self.generate_vending_machine(
                id=f"vm-{i+1:04d}",
                usage_pattern=usage_pattern,
                stock_level=stock_level_choice,
            )
            vending_machines.append(vending_machine)

        return vending_machines

    def generate_products(self, count: int = 10) -> List[ProductItem]:
        """
        Generate a list of product items with randomized properties.

        Args:
            count: Number of products to generate

        Returns:
            List of product items
        """
        products = []
        used_ids = set()

        for i in range(count):
            # Generate unique product ID
            product_id = f"PD{i+1:03d}"
            while product_id in used_ids:
                product_id = f"PD{self.rng.randint(100, 999)}"
            used_ids.add(product_id)

            # Randomize product properties
            name = self.rng.choice(self.PRODUCT_NAMES)
            price = round(self.rng.uniform(1.0, 4.5), 2)
            quantity = self.rng.randint(0, 15)
            category = self.rng.choice(self.PRODUCT_CATEGORIES)

            # Generate slot location: A1, B3, etc.
            row = chr(65 + self.rng.randint(0, 5))  # A-F
            col = self.rng.randint(1, 8)  # 1-8
            location = f"{row}{col}"

            # Create product
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
        self,
        vending_machine: VendingMachine,
        start_time: datetime,
        end_time: datetime,
        interval_minutes: int = 15,
        usage_pattern: Optional[str] = None,
    ) -> List[VendingMachineReading]:
        """
        Generate a series of readings for a vending machine over a time period.

        Args:
            vending_machine: The vending machine to generate readings for
            start_time: The starting timestamp
            end_time: The ending timestamp
            interval_minutes: Time between readings in minutes
            usage_pattern: Optional usage pattern override

        Returns:
            List of vending machine readings
        """
        readings = []
        current_time = start_time

        # Determine usage pattern if not provided
        if usage_pattern is None:
            # First try to get from tracked properties
            stored_pattern = self._get_machine_property(
                vending_machine.id, "usage_pattern"
            )
            if stored_pattern:
                usage_pattern = stored_pattern
            else:
                # Use the one implied from the location
                if vending_machine.location_type == LocationType.HOSPITAL:
                    usage_pattern = "all_hours"
                elif vending_machine.location_type in [
                    LocationType.OFFICE,
                    LocationType.SCHOOL,
                ]:
                    usage_pattern = "business_hours"
                elif vending_machine.location_type in [
                    LocationType.TRANSPORTATION,
                    LocationType.RETAIL,
                ]:
                    usage_pattern = "high_traffic"
                else:
                    usage_pattern = "low_traffic"

        # Set baseline values based on machine type and location
        base_temp = 5.0  # Celsius
        base_power = 120.0  # Watts
        cash_increment_rate = 0.0  # Cash accumulation per reading
        sales_rate = 0.0  # Average sales per reading

        # Adjust based on usage pattern
        if usage_pattern == "high_traffic":
            base_power = 150.0
            cash_increment_rate = 3.0
            sales_rate = 3.0  # Increased from 2.0 to ensure sufficient total sales
        elif usage_pattern == "business_hours":
            base_power = 130.0
            cash_increment_rate = 2.0
            sales_rate = 1.5
        elif usage_pattern == "all_hours":
            base_power = 140.0
            cash_increment_rate = 2.5
            sales_rate = 1.0
        else:  # low_traffic
            base_power = 110.0
            cash_increment_rate = 1.0
            sales_rate = 0.5

        # Track current cash level
        current_cash = vending_machine.current_cash or 0
        total_sales = 0
        door_open_events = []  # Track when door was opened for restocking/maintenance

        # Generate realistic door open events (for restocking, etc.)
        if (end_time - start_time).total_seconds() > 24 * 3600:  # If period > 24 hours
            # Generate some door open events
            num_events = self.rng.randint(1, 5)
            for _ in range(num_events):
                event_time = start_time + timedelta(
                    seconds=self.rng.uniform(0, (end_time - start_time).total_seconds())
                )
                event_duration = self.rng.randint(3, 15)  # minutes door is open
                door_open_events.append((event_time, event_duration))

        # Generate readings at specified intervals
        while current_time <= end_time:
            # Generate usage patterns based on time of day
            hour_factor = self._get_time_of_day_factor(current_time, usage_pattern)

            # Door status logic
            door_status = "CLOSED"
            for open_time, duration in door_open_events:
                if open_time <= current_time <= open_time + timedelta(minutes=duration):
                    door_status = "OPEN"
                    break

            # Calculate randomized values
            temperature = base_temp + self.rng.uniform(-1.0, 1.0)
            if door_status == "OPEN":
                temperature += self.rng.uniform(
                    1.0, 3.0
                )  # Temperature rises when door is open

            # Power consumption varies with usage and door status
            power_consumption = base_power * hour_factor
            if door_status == "OPEN":
                power_consumption *= (
                    0.8  # Reduced when door is open (cooling less effective)
                )

            # Sales count depends on time of day and usage pattern
            sales_count = None
            if hour_factor > 0.3:  # Some activity
                # Use numpy's poisson distribution
                sales_count = int(np.random.poisson(sales_rate * hour_factor))
                if sales_count > 0:
                    current_cash += sales_count * self.rng.uniform(
                        1.5, 3.5
                    )  # Average sale value
                    total_sales += sales_count

            # Create the reading
            reading = VendingMachineReading(
                timestamp=current_time,
                temperature=round(temperature, 1)
                if self.rng.random() > 0.05
                else None,  # Occasionally missing temperature
                power_consumption=round(power_consumption, 1)
                if self.rng.random() > 0.08
                else None,  # Occasionally missing power
                door_status=door_status
                if self.rng.random() > 0.02
                else None,  # Rarely missing door status
                cash_level=round(current_cash, 2)
                if self.rng.random() > 0.1
                else None,  # Sometimes missing cash level
                sales_count=sales_count,  # Can be None if no sales in period
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
            Factor between 0.3 and 1.5 representing activity level
        """
        hour = timestamp.hour
        weekday = timestamp.weekday()  # 0-6, where 0 is Monday
        is_weekend = weekday >= 5

        if usage_pattern == "high_traffic":
            # High traffic: peaks during typical meal times and afternoons
            if is_weekend:
                if 11 <= hour < 19:  # Weekend shopping hours
                    return 1.3 + self.rng.uniform(-0.1, 0.2)
                elif 8 <= hour < 11 or 19 <= hour < 22:
                    return 0.8 + self.rng.uniform(-0.1, 0.1)
                else:
                    return 0.4 + self.rng.uniform(-0.1, 0.1)
            else:  # Weekday
                if 11 <= hour < 13:  # Lunch rush
                    return 1.5 + self.rng.uniform(-0.1, 0.1)
                elif 15 <= hour < 18:  # Afternoon rush
                    return 1.4 + self.rng.uniform(-0.1, 0.1)
                elif 8 <= hour < 11 or 13 <= hour < 15 or 18 <= hour < 20:
                    return 1.0 + self.rng.uniform(-0.1, 0.1)
                else:
                    return 0.5 + self.rng.uniform(-0.1, 0.1)

        elif usage_pattern == "business_hours":
            # Business hours: consistent during weekday working hours
            if is_weekend:
                return 0.4 + self.rng.uniform(-0.1, 0.1)  # Minimal weekend activity
            elif 9 <= hour < 17:  # Standard business hours
                return 1.2 + self.rng.uniform(-0.2, 0.2)
            elif 7 <= hour < 9 or 17 <= hour < 19:  # Before/after hours
                return 0.7 + self.rng.uniform(-0.1, 0.1)
            else:
                return 0.3 + self.rng.uniform(-0.1, 0.1)

        elif usage_pattern == "all_hours":
            # All hours: active 24/7 with some variation (hospitals, transportation)
            if 8 <= hour < 18:  # Daytime
                return 1.1 + self.rng.uniform(-0.2, 0.2)
            else:  # Nighttime
                return 0.8 + self.rng.uniform(-0.2, 0.1)

        else:  # low_traffic
            # Low traffic: occasional usage
            if is_weekend:
                return 0.3 + self.rng.uniform(-0.1, 0.1)  # Very low weekend
            elif 9 <= hour < 17:  # Business hours
                return 0.7 + self.rng.uniform(-0.2, 0.2)
            else:
                return 0.3 + self.rng.uniform(-0.1, 0.1)

    def apply_readings_to_vending_machine(
        self, vending_machine: VendingMachine, readings: List[VendingMachineReading]
    ) -> None:
        """
        Apply a series of readings to a vending machine, updating its current state.

        Args:
            vending_machine: The vending machine to update
            readings: The readings to apply
        """
        if not readings:
            return

        # Sort readings by timestamp to ensure correct order
        sorted_readings = sorted(readings, key=lambda r: r.timestamp)

        # Apply each reading
        for reading in sorted_readings:
            vending_machine.add_reading(reading)

            # Update current temperature if available
            if reading.temperature is not None:
                vending_machine.temperature = reading.temperature

            # Update current cash if available
            if reading.cash_level is not None:
                vending_machine.current_cash = reading.cash_level

            # Update product quantities based on sales
            if (
                reading.sales_count
                and reading.sales_count > 0
                and vending_machine.products
            ):
                # Distribute sales across products
                self._update_product_quantities(vending_machine, reading.sales_count)

    def _update_product_quantities(
        self, vending_machine: VendingMachine, num_sales: int
    ) -> None:
        """
        Update product quantities based on sales count.

        Args:
            vending_machine: The vending machine to update
            num_sales: Number of sales to distribute across products
        """
        if not vending_machine.products or num_sales <= 0:
            return

        # Get products with quantity > 0
        available_products = [p for p in vending_machine.products if p.quantity > 0]
        if not available_products:
            return

        # Distribute sales across products based on weighted random selection
        for _ in range(num_sales):
            if not available_products:
                break

            # Calculate weights based on quantity and position (lower positions more likely)
            weights = []
            for product in available_products:
                # Extract position - assume format like 'A1', 'B3', etc.
                try:
                    row_char = product.location[0].upper()
                    col = int(product.location[1:]) if len(product.location) > 1 else 1
                    position_weight = 1.0 / (ord(row_char) - ord("A") + 1) + 1.0 / col
                except (IndexError, ValueError):
                    position_weight = 1.0

                # Combine quantity and position weight
                weight = (
                    0.7
                    * (product.quantity / max(p.quantity for p in available_products))
                    + 0.3 * position_weight
                )
                weights.append(weight)

            # Select a product to decrement
            selected_idx = self.rng.choices(
                range(len(available_products)), weights=weights, k=1
            )[0]
            selected_product = available_products[selected_idx]

            # Update quantity
            product_idx = vending_machine.products.index(selected_product)
            vending_machine.products[product_idx].quantity -= 1

            # Remove from available products if now empty
            if vending_machine.products[product_idx].quantity == 0:
                available_products = [p for p in available_products if p.quantity > 0]

        # Update machine status based on product levels
        self._update_machine_status(vending_machine)

    def _update_machine_status(self, vending_machine: VendingMachine) -> None:
        """
        Update machine status based on product inventory levels.

        Args:
            vending_machine: The vending machine to update
        """
        if not vending_machine.products:
            vending_machine.machine_status = VendingMachineStatus.OUT_OF_STOCK
            return

        total_items = sum(p.quantity for p in vending_machine.products)
        num_empty = sum(1 for p in vending_machine.products if p.quantity == 0)
        num_low = sum(1 for p in vending_machine.products if 0 < p.quantity <= 2)

        # Check for out of stock condition
        if total_items == 0:
            vending_machine.machine_status = VendingMachineStatus.OUT_OF_STOCK
            return

        # For low stock level machines, set status to NEEDS_RESTOCK
        stock_level = self._get_machine_property(vending_machine.id, "stock_level")
        if stock_level == "low":
            vending_machine.machine_status = VendingMachineStatus.NEEDS_RESTOCK
            return

        # For normal machines, check thresholds
        if (
            num_empty > len(vending_machine.products) * 0.3
            or num_low > len(vending_machine.products) * 0.5
        ):
            vending_machine.machine_status = VendingMachineStatus.NEEDS_RESTOCK
        else:
            # Only change to operational if not in maintenance
            if (
                vending_machine.machine_status
                != VendingMachineStatus.MAINTENANCE_REQUIRED
            ):
                vending_machine.machine_status = VendingMachineStatus.OPERATIONAL

    def add_products_to_vending_machine(
        self,
        vending_machine: VendingMachine,
        products: List[ProductItem],
        stock_level: str = "normal",
    ) -> None:
        """
        Add products to a vending machine with appropriate stock levels.

        Args:
            vending_machine: The vending machine to add products to
            products: The products to add
            stock_level: Stock level to apply ("full", "normal", "low", "empty")
        """
        # Set quantity ranges based on stock level
        if stock_level == "full":
            min_qty, max_qty = 8, 15
        elif stock_level == "normal":
            min_qty, max_qty = 3, 10
        elif stock_level == "low":
            min_qty, max_qty = 0, 3
        else:  # empty
            min_qty, max_qty = 0, 1

        # Reset products if adding a complete set
        if vending_machine.products and len(products) > 3:
            vending_machine.products = []

        # Add each product with appropriate quantity
        for product in products:
            # Adjust quantity based on stock level
            if stock_level == "full":
                # When full, ensure all products have high quantities (>5)
                product.quantity = self.rng.randint(6, max_qty)
            elif stock_level == "empty":
                # When empty, 70% chance of 0 quantity
                product.quantity = 0 if self.rng.random() < 0.7 else 1
            elif stock_level == "low":
                # When low, ensure some products are empty or very low
                product.quantity = (
                    0
                    if self.rng.random() < 0.3
                    else self.rng.randint(min_qty, min(3, max_qty))
                )
            else:  # normal
                product.quantity = self.rng.randint(min_qty, max_qty)

            # Add to vending machine
            vending_machine.add_product(product)

        # Update machine status based on stock levels
        self._update_machine_status(vending_machine)

    def add_maintenance_history(
        self,
        vending_machine: VendingMachine,
        num_events: int = 3,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> None:
        """
        Add maintenance history to a vending machine.

        Args:
            vending_machine: The vending machine to update
            num_events: Number of maintenance events to generate
            start_date: Start date for maintenance history (default: 6 months ago)
            end_date: End date for maintenance history (default: today)
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=180)  # 6 months ago

        if end_date is None:
            end_date = datetime.now()

        # Generate maintenance dates from oldest to newest
        maintenance_dates = []
        for i in range(num_events):
            # Distribute events across the time range
            event_time = start_date + (end_date - start_date) * (i / num_events)
            # Add some randomness
            randomized_time = event_time + timedelta(days=self.rng.uniform(-15, 15))
            # Ensure dates stay in range
            randomized_time = max(start_date, min(end_date, randomized_time))
            maintenance_dates.append(randomized_time)

        # Sort dates
        maintenance_dates.sort()

        # Set last maintenance date to most recent event
        if maintenance_dates:
            vending_machine.last_maintenance_date = maintenance_dates[-1]

            # Schedule next maintenance 3-6 months in the future
            next_maintenance = vending_machine.last_maintenance_date + timedelta(
                days=self.rng.randint(90, 180)
            )
            vending_machine.next_maintenance_date = next_maintenance

            # Set status to maintenance required if next_maintenance is in the past
            if vending_machine.next_maintenance_date < datetime.now():
                vending_machine.machine_status = (
                    VendingMachineStatus.MAINTENANCE_REQUIRED
                )

    def save_to_file(
        self, vending_machines: List[VendingMachine], filename: str
    ) -> None:
        """
        Save vending machines to a JSON file.

        Args:
            vending_machines: List of vending machines to save
            filename: File to save to
        """
        # Convert vending machines to JSON serializable format with tracked properties
        vending_machines_json = []
        for vm in vending_machines:
            # Start with the standard model data
            vm_data = vm.model_dump()

            # Add tracked properties if they exist
            if vm.id in self._machine_properties:
                vm_data.update(self._machine_properties[vm.id])

            vending_machines_json.append(vm_data)

        # Write to file
        with open(filename, "w") as f:
            json.dump(vending_machines_json, f, indent=2, default=str)

    def _track_machine_properties(
        self, machine_id: str, properties: Dict[str, Any]
    ) -> None:
        """
        Track properties for a specific vending machine.

        Args:
            machine_id: The ID of the vending machine
            properties: Dictionary of properties to track
        """
        if machine_id not in self._machine_properties:
            self._machine_properties[machine_id] = {}

        # Update properties
        self._machine_properties[machine_id].update(properties)

    def _get_machine_property(
        self, machine_id: str, property_name: str, default_value: Any = None
    ) -> Any:
        """
        Get a property for a specific vending machine.

        Args:
            machine_id: The ID of the vending machine
            property_name: The name of the property to retrieve
            default_value: Default value if property doesn't exist

        Returns:
            The property value or default_value if not found
        """
        if machine_id not in self._machine_properties:
            return default_value

        return self._machine_properties[machine_id].get(property_name, default_value)

    def load_from_file(self, filename: str) -> List[VendingMachine]:
        """
        Load vending machines from a JSON file.

        Args:
            filename: File to load from

        Returns:
            List of vending machine instances
        """
        with open(filename, "r") as f:
            vending_machines_json = json.load(f)

        # Convert JSON to vending machine instances
        vending_machines = []
        for vm_data in vending_machines_json:
            # Parse datetimes
            for key in ["last_maintenance_date", "next_maintenance_date"]:
                if key in vm_data and vm_data[key]:
                    vm_data[key] = datetime.fromisoformat(
                        vm_data[key].replace("Z", "+00:00")
                    )

            # Parse readings
            if "readings" in vm_data:
                for reading in vm_data["readings"]:
                    if "timestamp" in reading:
                        reading["timestamp"] = datetime.fromisoformat(
                            reading["timestamp"].replace("Z", "+00:00")
                        )

            # Extract custom properties before creating the instance
            custom_properties = {}
            for prop in ["usage_pattern", "stock_level"]:
                if prop in vm_data:
                    custom_properties[prop] = vm_data.pop(prop)

            # Create vending machine instance
            vending_machine = VendingMachine(**vm_data)
            vending_machines.append(vending_machine)

            # Track custom properties
            if custom_properties and vending_machine.id:
                self._track_machine_properties(vending_machine.id, custom_properties)

        return vending_machines
