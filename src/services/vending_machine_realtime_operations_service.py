"""
Service for vending machine real-time operations data
"""
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from src.models.vending_machine_realtime_operations import (
    VendingMachineOperationsData,
    AssetHealthData,
    FreezerTemperatureData,
    DispensePressureData,
    CycleTimeData,
    RamLoadData,
    FlavorInventory
)
from src.services.vending_machine import VendingMachineService


class VendingMachineRealtimeOperationsService:
    """Service for vending machine real-time operations data"""

    def __init__(self, vending_machine_service):
        """Initialize service with vending machine service"""
        self.vending_machine_service = vending_machine_service

    def get_operations_data(self, machine_id: str) -> VendingMachineOperationsData:
        """Get real-time operations data for a vending machine"""
        # First check if machine exists
        try:
            machine = self.vending_machine_service.get_vending_machine(machine_id)
        except ValueError:
            raise ValueError(f"Vending machine not found with ID: {machine_id}")
        
        # Generate realistic operation data
        return VendingMachineOperationsData(
            assetId=machine_id,
            assetLocation=machine.location,
            machineStatus="Online" if machine.status == "ONLINE" else "Offline",
            podCode=f"PD_{random.randint(1, 99):02d}",
            cupDetect="Yes" if random.random() > 0.1 else "No",
            podBinDoor="Closed" if random.random() > 0.05 else "Open",
            customerDoor="Closed" if random.random() > 0.05 else "Open",
            
            # Asset health gauge
            assetHealthData=AssetHealthData(
                assetHealth=f"{random.randint(70, 99)}%",
                needleValue=random.randint(70, 99)
            ),
            
            # Freezer temperature gauge
            freezerTemperatureData=FreezerTemperatureData(
                freezerTemperature=round(machine.temperature, 1),
                min=-25.0,
                max=0.0,
                needleValue=self._calculate_gauge_value(
                    machine.temperature, -25.0, 0.0
                )
            ),
            
            # Dispense pressure gauge
            dispensePressureData=DispensePressureData(
                dispensePressure=round(random.uniform(3.0, 7.0), 1),
                min=2.0,
                max=8.0,
                needleValue=random.randint(40, 80)
            ),
            
            # Cycle time gauge
            cycleTimeData=CycleTimeData(
                cycleTime=round(random.uniform(10.0, 25.0), 1),
                min=8.0,
                max=30.0,
                needleValue=random.randint(30, 80)
            ),
            
            # RAM load card
            maxRamLoadData=RamLoadData(
                ramLoad=round(random.uniform(5.0, 15.0), 1),
                min=0.0,
                max=20.0,
                status="OK" if random.random() > 0.1 else "Warning"
            ),
            
            # Freezer inventory
            freezerInventory=self._generate_inventory_data()
        )
    
    def _calculate_gauge_value(
        self, current: float, min_val: float, max_val: float
    ) -> float:
        """Calculate gauge needle value (0-100) based on current, min and max values"""
        if max_val == min_val:
            return 50.0  # Avoid division by zero
        
        # Calculate percentage within range and convert to 0-100 scale
        percentage = (current - min_val) / (max_val - min_val)
        return round(percentage * 100, 1)
    
    def _generate_inventory_data(self) -> List[FlavorInventory]:
        """Generate random inventory data for flavors"""
        flavors = [
            "Vanilla", 
            "Strawberry ShortCake", 
            "Chocolate", 
            "Mint & Chocolate", 
            "Cookies & Cream",
            "Salty Caramel"
        ]
        
        return [
            FlavorInventory(
                name=flavor,
                value=random.randint(1, 10)
            )
            for flavor in flavors
        ]
