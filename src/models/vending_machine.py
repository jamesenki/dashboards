"""
Polar Delight vending machine device model
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Literal, Dict, Any

from pydantic import BaseModel, Field

from src.models.device import Device, DeviceType

class VendingMachineStatus(str, Enum):
    """Vending machine operational status"""
    OPERATIONAL = "OPERATIONAL"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    NEEDS_RESTOCK = "NEEDS_RESTOCK"
    MAINTENANCE_REQUIRED = "MAINTENANCE_REQUIRED"

class LocationType(str, Enum):
    """Type of location where vending machine is installed"""
    FAST_FOOD = "FAST_FOOD"
    HOSPITAL = "HOSPITAL"
    STUDENT_CENTER = "STUDENT_CENTER"
    OFFICE = "OFFICE"
    SPECIALTY_SHOP = "SPECIALTY_SHOP"
    RETAIL = "RETAIL"
    TRANSPORTATION = "TRANSPORTATION"
    SCHOOL = "SCHOOL"
    OTHER = "OTHER"
    
class UseType(str, Enum):
    """Type of vending machine usage"""
    SERVICED = "SERVICED"
    SELF_SERVE = "SELF_SERVE"
    PUBLIC = "PUBLIC"
    EMPLOYEE = "EMPLOYEE"
    CUSTOMER = "CUSTOMER"
    STUDENT = "STUDENT"
    PATIENT = "PATIENT"
    OTHER = "OTHER"
    
class SubLocation(str, Enum):
    """Specific area within the location where vending machine is placed"""
    HALLWAY = "HALLWAY"
    LOBBY = "LOBBY"
    CAFETERIA = "CAFETERIA"
    DINING_AREA = "DINING_AREA"
    BREAK_ROOM = "BREAK_ROOM"
    WAITING_AREA = "WAITING_AREA"

class VendingMachineMode(str, Enum):
    """Vending machine operational mode"""
    NORMAL = "NORMAL"
    POWER_SAVE = "POWER_SAVE"
    CLEANING = "CLEANING"

class ProductItem(BaseModel):
    """Product item stocked in vending machine"""
    product_id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price")
    quantity: int = Field(0, description="Current stock quantity")
    category: Optional[str] = Field(None, description="Product category")
    location: Optional[str] = Field(None, description="Location in vending machine (slot/row)")

class VendingMachineReading(BaseModel):
    """Vending machine sensor reading"""
    timestamp: datetime = Field(..., description="Time of the reading")
    temperature: Optional[float] = Field(None, description="Internal temperature in Celsius")
    power_consumption: Optional[float] = Field(None, description="Power consumption in watts")
    door_status: Optional[str] = Field(None, description="Door status (OPEN/CLOSED)")
    cash_level: Optional[float] = Field(None, description="Current cash level")
    sales_count: Optional[int] = Field(None, description="Number of sales in this reading period")

class VendingMachine(Device):
    """Polar Delight vending machine device model"""
    type: Literal[DeviceType.VENDING_MACHINE] = Field(DeviceType.VENDING_MACHINE, description="Device type")
    
    # Machine specifications
    model_number: Optional[str] = Field(None, description="Vending machine model number")
    serial_number: Optional[str] = Field(None, description="Vending machine serial number")
    machine_status: VendingMachineStatus = Field(VendingMachineStatus.OPERATIONAL, description="Current operational status")
    mode: VendingMachineMode = Field(VendingMachineMode.NORMAL, description="Current operational mode")
    
    # Operational settings
    temperature: Optional[float] = Field(None, description="Current internal temperature in Celsius")
    total_capacity: Optional[int] = Field(None, description="Total product capacity")
    cash_capacity: Optional[float] = Field(None, description="Maximum cash capacity")
    current_cash: Optional[float] = Field(None, description="Current cash amount")
    
    # Location information
    location_business_name: Optional[str] = Field(None, description="Business name where machine is located")
    location_type: Optional[LocationType] = Field(None, description="Type of location (fast food, hospital, etc.)")
    sub_location: Optional[SubLocation] = Field(None, description="Specific area within the location (hallway, lobby, etc.)")
    use_type: Optional[UseType] = Field(None, description="Type of usage (serviced, self-serve, etc.)")
    
    # Data generation properties
    usage_pattern: Optional[str] = Field(None, description="Usage pattern for data generation (e.g., high_traffic, business_hours)")
    stock_level: Optional[str] = Field(None, description="Stock level for data generation (e.g., full, low)")
    
    # Maintenance information
    maintenance_partner: Optional[str] = Field(None, description="Service provider for maintenance")
    last_maintenance_date: Optional[datetime] = Field(None, description="Date of last maintenance")
    next_maintenance_date: Optional[datetime] = Field(None, description="Scheduled date for next maintenance")
    
    # Inventory
    products: List[ProductItem] = Field(default_factory=list, description="Products currently in stock")
    
    # Sensor readings history
    readings: List[VendingMachineReading] = Field(default_factory=list, description="Historical sensor readings")
    
    def add_reading(self, reading: VendingMachineReading) -> None:
        """Add a sensor reading to history
        
        Args:
            reading: The reading to add
        """
        self.readings.append(reading)
    
    def add_product(self, product: ProductItem) -> None:
        """Add a product to inventory or update existing product
        
        Args:
            product: The product to add or update
        """
        # Check if product already exists
        for i, existing_product in enumerate(self.products):
            if existing_product.product_id == product.product_id:
                # Update quantity of existing product
                self.products[i].quantity += product.quantity
                return
        
        # Add new product
        self.products.append(product)
    
    def update_product_quantity(self, product_id: str, quantity_change: int) -> None:
        """Update the quantity of a product
        
        Args:
            product_id: The ID of the product to update
            quantity_change: The change in quantity (positive for increase, negative for decrease)
        """
        # Find product
        for i, product in enumerate(self.products):
            if product.product_id == product_id:
                # Update quantity
                self.products[i].quantity += quantity_change
                
                # Check if machine needs restocking
                if self.products[i].quantity <= 1:  # Low stock threshold
                    self.machine_status = VendingMachineStatus.NEEDS_RESTOCK
                
                # Check if product is out of stock
                if self.products[i].quantity == 0:
                    # Check if all products are out of stock
                    all_out = True
                    for p in self.products:
                        if p.quantity > 0:
                            all_out = False
                            break
                    
                    if all_out:
                        self.machine_status = VendingMachineStatus.OUT_OF_STOCK
                
                return
