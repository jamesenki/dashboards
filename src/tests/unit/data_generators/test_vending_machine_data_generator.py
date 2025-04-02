"""
Test cases for vending machine data generator.
Following TDD principles, this file defines expected behavior before implementation.
"""
import os
import random
import sys
from datetime import datetime, timedelta

import pytest

# Import the data generator module (now implemented)
from src.data_generators.vending_machine_data_generator import (
    VendingMachineDataGenerator,
)
from src.models.device import DeviceStatus, DeviceType

# Import the models
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


class TestVendingMachineDataGenerator:
    """Test cases for vending machine data generator."""

    def test_generator_initialization(self):
        """Test that the generator can be initialized."""
        generator = VendingMachineDataGenerator()
        assert hasattr(generator, "generate_vending_machine")
        assert hasattr(generator, "generate_vending_machine_readings")
        assert hasattr(generator, "generate_products")

    def test_generate_single_vending_machine(self):
        """Test generating a single vending machine."""
        generator = VendingMachineDataGenerator()
        vending_machine = generator.generate_vending_machine(id="test-vm-1")

        assert vending_machine.id == "test-vm-1"
        assert vending_machine.type == DeviceType.VENDING_MACHINE
        assert vending_machine.machine_status in list(VendingMachineStatus)
        assert vending_machine.mode in list(VendingMachineMode)
        assert (
            vending_machine.location_type in list(LocationType)
            or vending_machine.location_type is None
        )
        assert (
            vending_machine.use_type in list(UseType)
            or vending_machine.use_type is None
        )

    def test_generate_multiple_vending_machines(self):
        """Test generating multiple vending machines."""
        generator = VendingMachineDataGenerator()
        vending_machines = generator.generate_vending_machines(count=5)

        assert len(vending_machines) == 5
        assert all(isinstance(vm, VendingMachine) for vm in vending_machines)

        # Check unique IDs
        ids = [vm.id for vm in vending_machines]
        assert len(ids) == len(set(ids)), "IDs should be unique"

        # Check that they have different locations
        locations = [vm.location for vm in vending_machines]
        assert len(set(locations)) > 1, "Should have different locations"

    def test_generate_products(self):
        """Test generating products for a vending machine."""
        generator = VendingMachineDataGenerator()
        products = generator.generate_products(count=10)

        assert len(products) == 10
        assert all(isinstance(p, ProductItem) for p in products)

        # Check product properties
        for product in products:
            assert product.product_id.startswith("PD")
            assert len(product.name) > 0
            assert product.price > 0
            assert product.quantity >= 0
            assert product.category is not None

    def test_generate_vending_machine_readings(self):
        """Test generating readings for a vending machine."""
        generator = VendingMachineDataGenerator()
        vending_machine = generator.generate_vending_machine(id="test-vm-1")

        # Generate 24 hours of readings at 15-minute intervals
        start_time = datetime.now() - timedelta(days=1)
        end_time = datetime.now()
        readings = generator.generate_vending_machine_readings(
            vending_machine=vending_machine,
            start_time=start_time,
            end_time=end_time,
            interval_minutes=15,
        )

        # Should have approximately 96 readings (24h * 4 per hour)
        assert 90 <= len(readings) <= 100

        # Check that readings are in time order
        timestamps = [r.timestamp for r in readings]
        assert timestamps == sorted(timestamps)

        # Check reading values are realistic
        for reading in readings:
            assert reading.temperature is None or (
                1 <= reading.temperature <= 10
            )  # Celsius for refrigerated
            assert reading.power_consumption is None or (
                0 <= reading.power_consumption <= 500
            )  # watts
            assert reading.door_status in [None, "OPEN", "CLOSED"]
            assert reading.cash_level is None or reading.cash_level >= 0
            assert reading.sales_count is None or reading.sales_count >= 0

    def test_apply_readings_to_vending_machine(self):
        """Test applying generated readings to a vending machine."""
        generator = VendingMachineDataGenerator()
        vending_machine = generator.generate_vending_machine(id="test-vm-1")
        assert len(vending_machine.readings) == 0

        # Generate 10 readings
        start_time = datetime.now() - timedelta(hours=2)
        end_time = datetime.now()
        readings = generator.generate_vending_machine_readings(
            vending_machine=vending_machine,
            start_time=start_time,
            end_time=end_time,
            interval_minutes=15,
        )

        # Apply readings to vending machine
        generator.apply_readings_to_vending_machine(vending_machine, readings)

        # Check readings were added
        assert len(vending_machine.readings) > 0
        assert len(vending_machine.readings) == len(readings)

        # Check vending machine temperature updated to latest reading if present
        if readings[-1].temperature is not None:
            assert vending_machine.temperature == readings[-1].temperature

    def test_generate_vending_machine_with_usage_pattern(self):
        """Test generating a vending machine with a specific usage pattern."""
        # Usage patterns could be: 'high_traffic', 'low_traffic', 'business_hours', 'all_hours'
        generator = VendingMachineDataGenerator()

        # Test high traffic pattern
        vending_machine = generator.generate_vending_machine(
            id="test-vm-high-traffic", usage_pattern="high_traffic"
        )
        readings = generator.generate_vending_machine_readings(
            vending_machine=vending_machine,
            start_time=datetime.now() - timedelta(days=1),
            end_time=datetime.now(),
            interval_minutes=15,
            usage_pattern="high_traffic",
        )

        # High traffic should have higher sales counts
        total_sales = sum(r.sales_count or 0 for r in readings)
        assert total_sales >= 200  # Reasonable threshold for high traffic

        # Test business hours pattern
        vending_machine = generator.generate_vending_machine(
            id="test-vm-business", usage_pattern="business_hours"
        )
        readings = generator.generate_vending_machine_readings(
            vending_machine=vending_machine,
            start_time=datetime.now() - timedelta(days=1),
            end_time=datetime.now(),
            interval_minutes=15,
            usage_pattern="business_hours",
        )

        # Business hours should have most sales between 9am-5pm
        business_hours_readings = [r for r in readings if 9 <= r.timestamp.hour < 17]
        non_business_readings = [
            r for r in readings if r.timestamp.hour < 9 or r.timestamp.hour >= 17
        ]

        business_sales = sum(r.sales_count or 0 for r in business_hours_readings)
        non_business_sales = sum(r.sales_count or 0 for r in non_business_readings)

        # More sales during business hours
        assert business_sales > non_business_sales

    def test_generate_vending_machine_with_maintenance_events(self):
        """Test generating a vending machine with maintenance events."""
        generator = VendingMachineDataGenerator()
        vending_machine = generator.generate_vending_machine(id="test-vm-maintenance")

        # Generate vending machine with maintenance history
        generator.add_maintenance_history(
            vending_machine=vending_machine,
            num_events=3,
            start_date=datetime.now() - timedelta(days=90),
            end_date=datetime.now(),
        )

        # Check maintenance dates
        assert vending_machine.last_maintenance_date is not None
        assert vending_machine.next_maintenance_date is not None

        # Last maintenance should be in the past
        assert vending_machine.last_maintenance_date <= datetime.now()

        # Next maintenance should be in the future
        assert vending_machine.next_maintenance_date > datetime.now()

    def test_generate_vending_machine_with_stock_levels(self):
        """Test generating a vending machine with various stock levels."""
        generator = VendingMachineDataGenerator()

        # Fully stocked machine
        full_machine = generator.generate_vending_machine(
            id="test-vm-full", stock_level="full"
        )
        products = generator.generate_products(count=10)
        generator.add_products_to_vending_machine(
            full_machine, products, stock_level="full"
        )

        # Check all products well stocked
        assert len(full_machine.products) > 0
        assert all(p.quantity > 5 for p in full_machine.products)
        assert full_machine.machine_status == VendingMachineStatus.OPERATIONAL

        # Nearly empty machine
        empty_machine = generator.generate_vending_machine(
            id="test-vm-empty", stock_level="low"
        )
        products = generator.generate_products(count=10)
        generator.add_products_to_vending_machine(
            empty_machine, products, stock_level="low"
        )

        # Check products low stocked
        assert len(empty_machine.products) > 0
        assert any(p.quantity <= 1 for p in empty_machine.products)
        assert empty_machine.machine_status in [
            VendingMachineStatus.NEEDS_RESTOCK,
            VendingMachineStatus.OUT_OF_STOCK,
        ]

    def test_save_and_load_data(self):
        """Test saving and loading generated data."""
        generator = VendingMachineDataGenerator()
        vending_machines = generator.generate_vending_machines(count=3)

        # Generate readings for each vending machine
        for vm in vending_machines:
            readings = generator.generate_vending_machine_readings(
                vending_machine=vm,
                start_time=datetime.now() - timedelta(days=1),
                end_time=datetime.now(),
                interval_minutes=30,
            )
            generator.apply_readings_to_vending_machine(vm, readings)

        # Save to temporary file
        temp_file = "temp_vending_machines.json"
        generator.save_to_file(vending_machines, temp_file)

        # Load back
        loaded_machines = generator.load_from_file(temp_file)

        # Check data integrity
        assert len(loaded_machines) == len(vending_machines)

        # Check ids match
        original_ids = [vm.id for vm in vending_machines]
        loaded_ids = [vm.id for vm in loaded_machines]
        assert set(original_ids) == set(loaded_ids)

        # Check readings loaded correctly
        for vm in loaded_machines:
            assert len(vm.readings) > 0

        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
