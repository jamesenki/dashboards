"""
Service for vending machine operations that retrieves data from the database and uses Redis for caching.
This implementation focuses on real-time operational monitoring to match the original Angular implementation.
"""
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Depends

from src.db.adapters.operations_cache import OperationsDashboardCache
from src.db.adapters.redis_cache import RedisCache, get_redis_cache
from src.db.repository import DeviceRepository
from src.models.device import DeviceStatus
from src.models.device_reading import DeviceReading
from src.models.vending_machine import VendingMachine

logger = logging.getLogger(__name__)


class VendingMachineOperationsServiceDB:
    """
    Service for vending machine operations that uses database persistence and Redis caching.
    This is aligned with the original Angular implementation that focuses on real-time
    operational monitoring.
    """

    def __init__(
        self,
        device_repo: DeviceRepository,
        operations_cache: Optional[OperationsDashboardCache] = None,
        redis_cache: Optional[RedisCache] = None,
    ):
        """
        Initialize the service with database repository and caches

        Args:
            device_repo: Repository for device data access
            operations_cache: Cache for operations dashboard data
            redis_cache: General Redis cache for device data
        """
        self.repo = device_repo
        self.redis = redis_cache

        # If operations_cache is not provided, create one using the redis_cache
        if operations_cache is None and redis_cache is not None:
            self.ops_cache = OperationsDashboardCache(redis_cache)
        else:
            self.ops_cache = operations_cache

    async def get_vm_operations(self, vm_id: str) -> Dict[str, Any]:
        """
        Get real-time operational data for a vending machine.
        Tries cache first, falls back to database if needed.

        Args:
            vm_id: Vending machine ID

        Returns:
            Dict of operational dashboard data
        """
        # Try to get from cache first
        if self.ops_cache:
            cached_data = await self.ops_cache.get_vending_machine_operations(vm_id)
            if cached_data:
                logger.info(f"Cache hit for vending machine operations: {vm_id}")
                return cached_data

        # Cache miss, get from database
        logger.info(f"Cache miss for vending machine operations: {vm_id}")
        vm = await self.repo.get_device(vm_id)

        if not vm or not isinstance(vm, VendingMachine):
            logger.error(f"Vending machine not found or invalid type: {vm_id}")
            raise ValueError(f"Vending machine not found: {vm_id}")

        # Get the latest readings
        latest_readings = {}
        if hasattr(vm, "readings") and vm.readings:
            # Sort readings by timestamp (descending) and get the most recent one
            sorted_readings = sorted(
                vm.readings, key=lambda r: r.timestamp, reverse=True
            )
            latest_reading = sorted_readings[0]

            # Extract metrics from the latest reading
            latest_readings = {
                "temperature": latest_reading.temperature,
                "power_consumption": latest_reading.power_consumption,
                "door_status": latest_reading.door_status,
                "cash_level": latest_reading.cash_level,
                "sales_count": latest_reading.sales_count,
            }

        # Build the operations dashboard data
        operations_data = {
            "machine_id": vm.id,
            "name": vm.name,
            "machine_status": vm.machine_status,
            "last_updated": datetime.utcnow().isoformat(),
            "location": vm.location,
            "mode": vm.mode,
            **latest_readings,
            "inventory": [
                {
                    "name": product.name,
                    "level": product.quantity,
                    "max": vm.total_capacity // len(vm.products) if vm.products else 10,
                    "status": "Low" if product.quantity < 3 else "OK",
                }
                for product in vm.products
            ],
        }

        # Cache the result
        if self.ops_cache:
            await self.ops_cache.cache_vending_machine_operations(
                vm_id, operations_data
            )

        return operations_data

    async def get_ice_cream_operations(self, machine_id: str) -> Dict[str, Any]:
        """
        Get real-time operational data specifically formatted for ice cream machines.
        This matches the original Angular implementation's operational focus.

        Args:
            machine_id: Ice cream machine ID

        Returns:
            Dict of ice cream machine operational dashboard data
        """
        # Try to get from cache first
        if self.ops_cache:
            cached_data = await self.ops_cache.get_ice_cream_machine_operations(
                machine_id
            )
            if cached_data:
                logger.info(f"Cache hit for ice cream machine operations: {machine_id}")
                return cached_data

        # Cache miss, get from database
        logger.info(f"Cache miss for ice cream machine operations: {machine_id}")
        vm = await self.repo.get_device(machine_id)

        if not vm or not isinstance(vm, VendingMachine):
            logger.error(f"Ice cream machine not found or invalid type: {machine_id}")
            raise ValueError(f"Ice cream machine not found: {machine_id}")

        # Get the latest temperature reading for freezer temperature
        latest_temp = -18.0  # Default freezer temperature
        if hasattr(vm, "readings") and vm.readings:
            # Sort readings by timestamp (descending) and get the most recent one
            sorted_readings = sorted(
                vm.readings, key=lambda r: r.timestamp, reverse=True
            )
            if sorted_readings and hasattr(sorted_readings[0], "temperature"):
                # Convert regular temperature to freezer temperature (much colder)
                latest_temp = sorted_readings[0].temperature - 20.0

        # For ice cream machines, we need to transform the products into ice cream flavors
        ice_cream_inventory = []
        for product in vm.products:
            # Only consider products that could be ice cream flavors
            if "ice cream" in product.name.lower() or product.category.lower() in [
                "dessert",
                "frozen",
                "ice cream",
            ]:
                flavor_name = product.name
            else:
                # Convert regular product to ice cream flavor
                flavor_words = [
                    "Vanilla",
                    "Chocolate",
                    "Strawberry",
                    "Mint",
                    "Cookies & Cream",
                    "Caramel",
                    "Butterscotch",
                    "Blueberry",
                    "Mango",
                    "Coffee",
                ]
                descriptor_words = [
                    "Creamy",
                    "Deluxe",
                    "Premium",
                    "Rich",
                    "Smooth",
                    "Classic",
                    "Swirl",
                ]

                # Use product name as seed for deterministic randomness
                random.seed(product.name)
                flavor = random.choice(flavor_words)
                if random.random() > 0.5:
                    descriptor = random.choice(descriptor_words)
                    flavor_name = f"{descriptor} {flavor}"
                else:
                    flavor_name = flavor

            max_level = 10
            current_level = min(product.quantity, max_level)

            ice_cream_inventory.append(
                {
                    "name": flavor_name,
                    "current_level": current_level,
                    "max_level": max_level,
                    "status": "Low" if current_level <= 2 else "OK",
                    "amount": current_level,
                }
            )

        # Generate simulated operational metrics based on machine state
        door_closed = True
        if hasattr(vm, "readings") and vm.readings:
            latest_reading = sorted(
                vm.readings, key=lambda r: r.timestamp, reverse=True
            )[0]
            door_closed = latest_reading.door_status == "CLOSED"

        # Build the operations dashboard data matching the original Angular structure
        operations_data = {
            "machine_id": vm.id,
            "machine_status": "Online"
            if vm.status == DeviceStatus.ONLINE
            else "Offline",
            "last_updated": datetime.utcnow().isoformat(),
            "cap_position": {
                "capPosition": "Down" if door_closed else "Up",
                "status": "OK",
            },
            "ram_position": {
                "min": "55",
                "max": "95",
                "ramPosition": str(random.randint(60, 90)),
                "status": "OK",
            },
            "cup_detect": "Yes" if random.random() > 0.2 else "No",
            "pod_bin_door": "Closed" if door_closed else "Open",
            "customer_door": "Closed" if door_closed else "Open",
            "pod_code": str(random.randint(10000, 99999)),
            "cycle_status": {
                "cycleStatus": "Complete",
                "status": "OK" if random.random() > 0.15 else "FAULT",
            },
            "dispense_pressure": {
                "min": "5",
                "max": "40",
                "needleValue": random.randint(5, 45),
                "dispensePressure": str(random.randint(5, 40)),
            },
            "freezer_temperature": {
                "freezerTemperature": str(round(latest_temp, 1)),
                "min": "-50",
                "needleValue": latest_temp,
                "max": "5",
            },
            "max_ram_load": {
                "min": "10",
                "max": "25",
                "ramLoad": str(random.randint(10, 50)),
                "status": "OK" if random.random() > 0.2 else "WARN",
            },
            "cycle_time": {
                "cycleTime": str(random.randint(5, 20)),
                "min": "5",
                "needleValue": random.randint(5, 60),
                "max": "60",
            },
            "ice_cream_inventory": ice_cream_inventory,
            "location": vm.location,
        }

        # Cache the result
        if self.ops_cache:
            await self.ops_cache.cache_ice_cream_machine_operations(
                machine_id, operations_data
            )

        return operations_data

    async def update_vm_operations(self, vm_id: str, update_data: Dict) -> None:
        """
        Update vending machine operational data and invalidate cache.

        Args:
            vm_id: Vending machine ID
            update_data: Updated operational data
        """
        # Update the device in the database
        await self.repo.update_device(vm_id, update_data)

        # Invalidate cache
        if self.ops_cache:
            await self.ops_cache.invalidate_operations_cache(vm_id, "vending_machine")
            await self.ops_cache.publish_operations_update(vm_id, "vending_machine")

        logger.info(f"Updated vending machine operations for {vm_id}")

    async def get_fleet_operations(self) -> Dict[str, Any]:
        """
        Get fleet-wide operations overview data.

        Returns:
            Dict of fleet operations data
        """
        # Get all vending machines
        vms = await self.repo.get_devices(type_filter="vending_machine")

        # Calculate overall statistics
        total_machines = len(vms)
        online_count = sum(1 for vm in vms if vm.status == DeviceStatus.ONLINE)
        offline_count = total_machines - online_count

        # Group by location
        locations = {}
        for vm in vms:
            if vm.location not in locations:
                locations[vm.location] = {"total": 0, "online": 0, "offline": 0}

            locations[vm.location]["total"] += 1
            if vm.status == DeviceStatus.ONLINE:
                locations[vm.location]["online"] += 1
            else:
                locations[vm.location]["offline"] += 1

        # Build response
        return {
            "total_machines": total_machines,
            "online_count": online_count,
            "offline_count": offline_count,
            "operational_percentage": (online_count / total_machines * 100)
            if total_machines > 0
            else 0,
            "locations": locations,
            "last_updated": datetime.utcnow().isoformat(),
        }
