"""
Vending machine API endpoints
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field

# Using absolute imports to ensure consistency
from src.models.device import DeviceType, DeviceStatus
from src.models.vending_machine import (
    VendingMachineMode, 
    VendingMachineStatus,
    VendingMachineReading,
    ProductItem,
    VendingMachine,
    LocationType,
    UseType
)
from src.services.vending_machine import VendingMachineService


# API Models
class ProductItemCreate(BaseModel):
    """API model for creating a product item"""
    product_id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price")
    quantity: int = Field(0, description="Current stock quantity")
    category: Optional[str] = Field(None, description="Product category")
    location: Optional[str] = Field(None, description="Location in vending machine (slot/row)")

class ProductQuantityUpdate(BaseModel):
    """API model for updating product quantity"""
    quantity_change: int = Field(..., description="Change in quantity (positive for increase, negative for decrease)")

class VendingMachineReadingCreate(BaseModel):
    """API model for creating a vending machine reading"""
    temperature: Optional[float] = Field(None, description="Internal temperature in Celsius")
    power_consumption: Optional[float] = Field(None, description="Power consumption in watts")
    door_status: Optional[str] = Field(None, description="Door status (OPEN/CLOSED)")
    cash_level: Optional[float] = Field(None, description="Current cash level")
    sales_count: Optional[int] = Field(None, description="Number of sales in this reading period")

class VendingMachineCreate(BaseModel):
    """API model for creating a vending machine"""
    name: str = Field(..., description="Vending machine name")
    location: Optional[str] = Field(None, description="Physical location")
    model_number: Optional[str] = Field(None, description="Model number")
    serial_number: Optional[str] = Field(None, description="Serial number")
    temperature: Optional[float] = Field(None, description="Internal temperature in Celsius")
    total_capacity: Optional[int] = Field(None, description="Total product capacity")
    cash_capacity: Optional[float] = Field(None, description="Maximum cash capacity")
    current_cash: Optional[float] = Field(None, description="Initial cash amount")
    location_business_name: Optional[str] = Field(None, description="Business name where machine is located")
    location_type: Optional[LocationType] = Field(None, description="Type of location (retail, office, etc.)")
    sub_location: Optional[str] = Field(None, description="Specific area within the location")
    use_type: Optional[UseType] = Field(None, description="Type of usage (public, employee, etc.)")
    maintenance_partner: Optional[str] = Field(None, description="Service provider for maintenance")
    last_maintenance_date: Optional[str] = Field(None, description="Date of last maintenance")
    next_maintenance_date: Optional[str] = Field(None, description="Scheduled date for next maintenance")

class VendingMachineUpdate(BaseModel):
    """API model for updating a vending machine"""
    name: Optional[str] = Field(None, description="Vending machine name")
    location: Optional[str] = Field(None, description="Physical location")
    model_number: Optional[str] = Field(None, description="Model number")
    serial_number: Optional[str] = Field(None, description="Serial number")
    machine_status: Optional[VendingMachineStatus] = Field(None, description="Current operational status")
    mode: Optional[VendingMachineMode] = Field(None, description="Current operational mode")
    temperature: Optional[float] = Field(None, description="Internal temperature in Celsius")
    total_capacity: Optional[int] = Field(None, description="Total product capacity")
    cash_capacity: Optional[float] = Field(None, description="Maximum cash capacity")
    current_cash: Optional[float] = Field(None, description="Current cash amount")

# Service dependency
def get_vending_machine_service():
    """Get vending machine service instance"""
    from src.utils.dummy_data import dummy_data
    return VendingMachineService(dummy_data)

# Create router
router = APIRouter(prefix="/vending-machines", tags=["vending-machines"])

@router.get("", response_model=List[dict])
async def get_all_vending_machines(
    service: VendingMachineService = Depends(get_vending_machine_service),
    format_names: bool = Query(False, description="Format machine names with pipe-delimited location info")
):
    """Get all vending machines"""
    import logging
    machines = service.get_all_vending_machines()
    logging.error(f"API returning {len(machines)} machines: {[m.id for m in machines]}")
    
    # Helper function to format enum values for display
    def format_enum_value(value):
        if not value:
            return "Unknown"
        # Convert from enum value like "RETAIL" to "Retail"
        value_str = str(value.value) if hasattr(value, 'value') else str(value)
        return value_str.replace('_', ' ').title()
    
    # Transform to the enhanced format with location information for the frontend dropdown
    enhanced_machines = []
    for machine in machines:
        # Build the formatted name with pipe delimiters when format_names is True
        formatted_name = machine.name
        
        if format_names:
            # Create name with pipe-delimited format: NAME | BUSINESS | LOCATION_TYPE | SUB_LOCATION
            formatted_name = f"{machine.name} | {machine.location_business_name or 'Unknown'} | {format_enum_value(machine.location_type)} | {format_enum_value(machine.sub_location)}"
            logging.error(f"Formatted machine name: {formatted_name}")
            
        enhanced_machines.append({
            "id": machine.id, 
            "name": formatted_name,  # Use the formatted name that includes location info
            "location_business_name": machine.location_business_name,
            "location_type": str(machine.location_type.value) if machine.location_type else None,
            "sub_location": str(machine.sub_location.value) if machine.sub_location else None,
            "location": machine.location,
            "status": str(machine.machine_status.value) if machine.machine_status else "UNKNOWN"
        })
    
    logging.error(f"Enhanced machine data for frontend: {enhanced_machines[:2]}...")
    return enhanced_machines

@router.get("/{vm_id}", response_model=VendingMachine)
async def get_vending_machine(
    vm_id: str = Path(..., description="Vending machine ID"),
    service: VendingMachineService = Depends(get_vending_machine_service)
):
    """Get a vending machine by ID"""
    # No need for try/except here since the service has its own fallback mechanism
    # that will generate mock data for non-existent machines
    return service.get_vending_machine(vm_id)

@router.post("", response_model=VendingMachine, status_code=status.HTTP_201_CREATED)
async def create_vending_machine(
    vending_machine: VendingMachineCreate,
    service: VendingMachineService = Depends(get_vending_machine_service)
):
    """Create a new vending machine"""
    return service.create_vending_machine(
        name=vending_machine.name,
        location=vending_machine.location,
        model_number=vending_machine.model_number,
        serial_number=vending_machine.serial_number,
        temperature=vending_machine.temperature,
        total_capacity=vending_machine.total_capacity,
        cash_capacity=vending_machine.cash_capacity,
        current_cash=vending_machine.current_cash,
        location_business_name=vending_machine.location_business_name,
        location_type=vending_machine.location_type,
        sub_location=vending_machine.sub_location,
        use_type=vending_machine.use_type,
        maintenance_partner=vending_machine.maintenance_partner,
        last_maintenance_date=vending_machine.last_maintenance_date,
        next_maintenance_date=vending_machine.next_maintenance_date
    )

@router.patch("/{vm_id}", response_model=VendingMachine)
async def update_vending_machine(
    vm_id: str = Path(..., description="Vending machine ID"),
    vending_machine: VendingMachineUpdate = None,
    service: VendingMachineService = Depends(get_vending_machine_service)
):
    """Update a vending machine"""
    try:
        return service.update_vending_machine(
            vm_id=vm_id,
            name=vending_machine.name if vending_machine else None,
            location=vending_machine.location if vending_machine else None,
            model_number=vending_machine.model_number if vending_machine else None,
            serial_number=vending_machine.serial_number if vending_machine else None,
            machine_status=vending_machine.machine_status if vending_machine else None,
            mode=vending_machine.mode if vending_machine else None,
            temperature=vending_machine.temperature if vending_machine else None,
            total_capacity=vending_machine.total_capacity if vending_machine else None,
            cash_capacity=vending_machine.cash_capacity if vending_machine else None,
            current_cash=vending_machine.current_cash if vending_machine else None
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/{vm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vending_machine(
    vm_id: str = Path(..., description="Vending machine ID"),
    service: VendingMachineService = Depends(get_vending_machine_service)
):
    """Delete a vending machine"""
    result = service.delete_vending_machine(vm_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vending machine not found")
    return None

@router.post("/{vm_id}/products", response_model=VendingMachine)
async def add_product(
    vm_id: str = Path(..., description="Vending machine ID"),
    product: ProductItemCreate = None,
    service: VendingMachineService = Depends(get_vending_machine_service)
):
    """Add a product to a vending machine"""
    try:
        product_item = ProductItem(
            product_id=product.product_id,
            name=product.name,
            price=product.price,
            quantity=product.quantity,
            category=product.category,
            location=product.location
        )
        return service.add_product(vm_id, product_item)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/{vm_id}/products/{product_id}/quantity", response_model=VendingMachine)
async def update_product_quantity(
    vm_id: str = Path(..., description="Vending machine ID"),
    product_id: str = Path(..., description="Product ID"),
    quantity_update: ProductQuantityUpdate = None,
    service: VendingMachineService = Depends(get_vending_machine_service)
):
    """Update product quantity in a vending machine"""
    try:
        return service.update_product_quantity(
            vm_id,
            product_id,
            quantity_update.quantity_change if quantity_update else 0
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/{vm_id}/readings", response_model=VendingMachine)
async def add_reading(
    vm_id: str = Path(..., description="Vending machine ID"),
    reading: VendingMachineReadingCreate = None,
    service: VendingMachineService = Depends(get_vending_machine_service)
):
    """Add a reading to a vending machine"""
    try:
        vm_reading = VendingMachineReading(
            timestamp=datetime.now(),
            temperature=reading.temperature if reading else None,
            power_consumption=reading.power_consumption if reading else None,
            door_status=reading.door_status if reading else None,
            cash_level=reading.cash_level if reading else None,
            sales_count=reading.sales_count if reading else None
        )
        return service.add_reading(vm_id, vm_reading)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/{vm_id}/readings", response_model=List[VendingMachineReading])
async def get_readings(
    vm_id: str = Path(..., description="Vending machine ID"),
    service: VendingMachineService = Depends(get_vending_machine_service)
):
    """Get readings for a vending machine"""
    try:
        return service.get_readings(vm_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
