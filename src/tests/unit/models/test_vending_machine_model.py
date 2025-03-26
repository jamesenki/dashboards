import pytest
from datetime import datetime
from enum import Enum

from src.models.device import DeviceType, DeviceStatus
# We'll be implementing these classes next:
from src.models.vending_machine import (
    VendingMachineStatus,
    VendingMachineMode,
    LocationType,
    UseType,
    VendingMachineReading,
    ProductItem,
    VendingMachine
)


class TestVendingMachineModel:
    """Test cases for vending machine models."""
    
    def test_vending_machine_status_enum(self):
        """Test the VendingMachineStatus enum has required values."""
        assert VendingMachineStatus.OPERATIONAL == "OPERATIONAL"
        assert VendingMachineStatus.OUT_OF_STOCK == "OUT_OF_STOCK"
        assert VendingMachineStatus.NEEDS_RESTOCK == "NEEDS_RESTOCK"
        assert VendingMachineStatus.MAINTENANCE_REQUIRED == "MAINTENANCE_REQUIRED"
        assert isinstance(VendingMachineStatus.OPERATIONAL, str)
    
    def test_vending_machine_mode_enum(self):
        """Test the VendingMachineMode enum has required values."""
        assert VendingMachineMode.NORMAL == "NORMAL"
        assert VendingMachineMode.POWER_SAVE == "POWER_SAVE"
        assert VendingMachineMode.CLEANING == "CLEANING"
        assert isinstance(VendingMachineMode.NORMAL, str)
        
    def test_location_type_enum(self):
        """Test the LocationType enum has required values."""
        assert LocationType.RETAIL == "RETAIL"
        assert LocationType.OFFICE == "OFFICE"
        assert LocationType.SCHOOL == "SCHOOL"
        assert LocationType.HOSPITAL == "HOSPITAL"
        assert LocationType.TRANSPORTATION == "TRANSPORTATION"
        assert LocationType.OTHER == "OTHER"
        assert isinstance(LocationType.RETAIL, str)
        
    def test_use_type_enum(self):
        """Test the UseType enum has required values."""
        assert UseType.PUBLIC == "PUBLIC"
        assert UseType.EMPLOYEE == "EMPLOYEE"
        assert UseType.CUSTOMER == "CUSTOMER"
        assert UseType.STUDENT == "STUDENT"
        assert UseType.PATIENT == "PATIENT"
        assert UseType.OTHER == "OTHER"
        assert isinstance(UseType.PUBLIC, str)
    
    def test_product_item_model(self):
        """Test the ProductItem model."""
        # Create a product item
        product = ProductItem(
            product_id="PD001",
            name="Polar Delight Classic",
            price=2.50,
            quantity=10,
            category="Beverages",
            location="A1"
        )
        
        # Assert properties
        assert product.product_id == "PD001"
        assert product.name == "Polar Delight Classic"
        assert product.price == 2.50
        assert product.quantity == 10
        assert product.category == "Beverages"
        assert product.location == "A1"
        
        # Test serialization/deserialization
        product_dict = product.model_dump()
        assert "product_id" in product_dict
        assert "name" in product_dict
        assert "price" in product_dict
        assert "quantity" in product_dict
        assert "category" in product_dict
        assert "location" in product_dict
    
    def test_vending_machine_reading_model(self):
        """Test the VendingMachineReading model."""
        # Create a vending machine reading
        reading = VendingMachineReading(
            timestamp=datetime.now(),
            temperature=4.5,
            power_consumption=120.5,
            door_status="CLOSED",
            cash_level=85.50,
            sales_count=12
        )
        
        # Assert properties
        assert reading.temperature == 4.5
        assert reading.power_consumption == 120.5
        assert reading.door_status == "CLOSED"
        assert reading.cash_level == 85.50
        assert reading.sales_count == 12
        
        # Test serialization/deserialization
        reading_dict = reading.model_dump()
        assert "temperature" in reading_dict
        assert "power_consumption" in reading_dict
        assert "door_status" in reading_dict
        assert "cash_level" in reading_dict
        assert "sales_count" in reading_dict
    
    def test_vending_machine_model(self):
        """Test the VendingMachine model."""
        # Create product inventory
        products = [
            ProductItem(
                product_id="PD001",
                name="Polar Delight Classic",
                price=2.50,
                quantity=10,
                category="Beverages",
                location="A1"
            ),
            ProductItem(
                product_id="PD002",
                name="Polar Delight Zero",
                price=2.75,
                quantity=8,
                category="Beverages",
                location="A2"
            )
        ]
        
        # Create a vending machine
        vending_machine = VendingMachine(
            id="vm-001",
            name="Campus Center VM",
            type=DeviceType.VENDING_MACHINE,
            status=DeviceStatus.ONLINE,
            location="Building B, Floor 1",
            model_number="PD-2000",
            serial_number="PD2023-12345",
            machine_status=VendingMachineStatus.OPERATIONAL,
            mode=VendingMachineMode.NORMAL,
            temperature=4.0,
            total_capacity=50,
            cash_capacity=500.0,
            current_cash=125.50,
            location_business_name="Sheetz",
            location_type=LocationType.RETAIL,
            sub_location="Entrance",
            use_type=UseType.CUSTOMER,
            maintenance_partner="ColdFix Solutions",
            last_maintenance_date=datetime(2024, 12, 15, 10, 30),
            next_maintenance_date=datetime(2025, 6, 15, 10, 30),
            products=products
        )
        
        # Assert base properties
        assert vending_machine.name == "Campus Center VM"
        assert vending_machine.type == DeviceType.VENDING_MACHINE
        assert vending_machine.status == DeviceStatus.ONLINE
        assert vending_machine.location == "Building B, Floor 1"
        
        # Assert vending machine specific properties
        assert vending_machine.model_number == "PD-2000"
        assert vending_machine.serial_number == "PD2023-12345"
        assert vending_machine.machine_status == VendingMachineStatus.OPERATIONAL
        assert vending_machine.mode == VendingMachineMode.NORMAL
        assert vending_machine.temperature == 4.0
        assert vending_machine.total_capacity == 50
        assert vending_machine.cash_capacity == 500.0
        assert vending_machine.current_cash == 125.50
        assert len(vending_machine.products) == 2
        assert vending_machine.products[0].name == "Polar Delight Classic"
        assert vending_machine.products[1].name == "Polar Delight Zero"
        
        # Assert new location fields
        assert vending_machine.location_business_name == "Sheetz"
        assert vending_machine.location_type == LocationType.RETAIL
        assert vending_machine.sub_location == "Entrance"
        assert vending_machine.use_type == UseType.CUSTOMER
        
        # Assert new maintenance fields
        assert vending_machine.maintenance_partner == "ColdFix Solutions"
        assert vending_machine.last_maintenance_date == datetime(2024, 12, 15, 10, 30)
        assert vending_machine.next_maintenance_date == datetime(2025, 6, 15, 10, 30)
        
        # Test serialization/deserialization
        vm_dict = vending_machine.model_dump()
        assert "model_number" in vm_dict
        assert "location_business_name" in vm_dict
        assert "location_type" in vm_dict
        assert "sub_location" in vm_dict
        assert "use_type" in vm_dict
        assert "maintenance_partner" in vm_dict
        assert "last_maintenance_date" in vm_dict
        assert "next_maintenance_date" in vm_dict
        assert "serial_number" in vm_dict
        assert "machine_status" in vm_dict
        assert "mode" in vm_dict
        assert "temperature" in vm_dict
        assert "products" in vm_dict
    
    def test_vending_machine_add_reading(self):
        """Test adding a reading to a vending machine."""
        # Create a vending machine
        vending_machine = VendingMachine(
            id="vm-001",
            name="Campus Center VM",
            type=DeviceType.VENDING_MACHINE,
            status=DeviceStatus.ONLINE,
            location="Building B, Floor 1",
            model_number="PD-2000",
            serial_number="PD2023-12345",
            machine_status=VendingMachineStatus.OPERATIONAL,
            mode=VendingMachineMode.NORMAL,
            temperature=4.0,
            total_capacity=50,
            cash_capacity=500.0,
            current_cash=125.50,
            products=[]
        )
        
        # Create a reading
        reading = VendingMachineReading(
            timestamp=datetime.now(),
            temperature=4.5,
            power_consumption=120.5,
            door_status="CLOSED",
            cash_level=85.50,
            sales_count=12
        )
        
        # Add reading
        vending_machine.add_reading(reading)
        
        # Assert reading was added
        assert len(vending_machine.readings) == 1
        assert vending_machine.readings[0].temperature == 4.5
        assert vending_machine.readings[0].power_consumption == 120.5
        
        # Add another reading
        reading2 = VendingMachineReading(
            timestamp=datetime.now(),
            temperature=4.2,
            power_consumption=110.0,
            door_status="OPEN",
            cash_level=75.50,
            sales_count=15
        )
        
        vending_machine.add_reading(reading2)
        
        # Assert both readings are present
        assert len(vending_machine.readings) == 2
        assert vending_machine.readings[1].temperature == 4.2
        assert vending_machine.readings[1].door_status == "OPEN"
    
    def test_vending_machine_add_product(self):
        """Test adding a product to a vending machine."""
        # Create a vending machine with no products
        vending_machine = VendingMachine(
            id="vm-001",
            name="Campus Center VM",
            type=DeviceType.VENDING_MACHINE,
            status=DeviceStatus.ONLINE,
            location="Building B, Floor 1",
            model_number="PD-2000",
            serial_number="PD2023-12345",
            machine_status=VendingMachineStatus.OPERATIONAL,
            mode=VendingMachineMode.NORMAL,
            temperature=4.0,
            total_capacity=50,
            cash_capacity=500.0,
            current_cash=125.50,
            products=[]
        )
        
        # Create a product
        product = ProductItem(
            product_id="PD001",
            name="Polar Delight Classic",
            price=2.50,
            quantity=10,
            category="Beverages",
            location="A1"
        )
        
        # Add product
        vending_machine.add_product(product)
        
        # Assert product was added
        assert len(vending_machine.products) == 1
        assert vending_machine.products[0].product_id == "PD001"
        assert vending_machine.products[0].name == "Polar Delight Classic"
        
        # Try to add same product (should update quantity)
        product_update = ProductItem(
            product_id="PD001",
            name="Polar Delight Classic",
            price=2.50,
            quantity=5,
            category="Beverages",
            location="A1"
        )
        
        vending_machine.add_product(product_update)
        
        # Assert product was updated not added
        assert len(vending_machine.products) == 1
        assert vending_machine.products[0].quantity == 15  # 10 + 5
    
    def test_vending_machine_update_product_quantity(self):
        """Test updating a product quantity."""
        # Create a product
        product = ProductItem(
            product_id="PD001",
            name="Polar Delight Classic",
            price=2.50,
            quantity=10,
            category="Beverages",
            location="A1"
        )
        
        # Create a vending machine with one product
        vending_machine = VendingMachine(
            id="vm-001",
            name="Campus Center VM",
            type=DeviceType.VENDING_MACHINE,
            status=DeviceStatus.ONLINE,
            location="Building B, Floor 1",
            model_number="PD-2000",
            serial_number="PD2023-12345",
            machine_status=VendingMachineStatus.OPERATIONAL,
            mode=VendingMachineMode.NORMAL,
            temperature=4.0,
            total_capacity=50,
            cash_capacity=500.0,
            current_cash=125.50,
            products=[product]
        )
        
        # Update product quantity
        vending_machine.update_product_quantity("PD001", -3)  # Simulate sale of 3 items
        
        # Assert quantity was updated
        assert vending_machine.products[0].quantity == 7  # 10 - 3
        
        # Update machine status if stock gets low
        vending_machine.update_product_quantity("PD001", -6)  # Only 1 left
        
        # Assert status was updated to needs restock
        assert vending_machine.products[0].quantity == 1
        assert vending_machine.machine_status == VendingMachineStatus.NEEDS_RESTOCK
