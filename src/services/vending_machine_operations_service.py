"""
Vending machine operations service implementation
"""
import random
import uuid
from datetime import datetime, timedelta
from statistics import mean
from typing import Any, Dict, List, Optional, Union

from src.models.device import DeviceStatus, DeviceType
from src.models.vending_machine import (
    VendingMachine,
    VendingMachineReading,
    VendingMachineStatus,
)
from src.models.vending_machine_operations import (  # New models for Polar Delight Ice Cream Machines
    AlertModel,
    AlertSeverity,
    AssetHealth,
    DayOfWeek,
    GaugeData,
    GaugeIndicators,
    IceCreamInventoryItem,
    LocationPerformance,
    MachineStatus,
    MaintenanceEvent,
    MaintenanceHistory,
    MaintenanceType,
    OperationalStatus,
    OperationsSummary,
    ProductSale,
    RefillEvent,
    RefillHistory,
    RefillItem,
    SalesData,
    SalesPeriod,
    ServiceTicket,
    TemperatureReading,
    TemperatureTrends,
    TimeOfDay,
    UsagePattern,
)


class VendingMachineOperationsService:
    """Service for Polar Delight Ice Cream Machine operations and monitoring"""

    def __init__(self, vending_machine_service, db=None):
        """Initialize vending machine operations service

        Args:
            vending_machine_service: Vending machine service
            db: Optional database instance for persistence
        """
        self.vending_machine_service = vending_machine_service
        self.db = db

    def get_operations_summary(self, machine_id: str) -> OperationsSummary:
        """Get operations summary for a vending machine

        Args:
            machine_id: Vending machine ID

        Returns:
            Operations summary

        Raises:
            ValueError: If vending machine not found
        """
        # Verify machine exists
        machine = self.vending_machine_service.get_vending_machine(machine_id)
        if not machine:
            raise ValueError(f"Vending machine {machine_id} not found")

        # Get sales data
        sales_data = self.get_sales_data(machine_id)
        # Get usage patterns
        usage_patterns = self.get_usage_patterns(machine_id)
        # Get maintenance history
        maintenance_history = self.get_maintenance_history(machine_id)
        # Get refill history
        refill_history = self.get_refill_history(machine_id)
        # Get temperature trends
        temperature_trends = self.get_temperature_trends(machine_id)

        # Combine all data into operations summary
        return OperationsSummary(
            machine_id=machine_id,
            sales_data=sales_data,
            usage_patterns=usage_patterns,
            maintenance_history=maintenance_history,
            refill_history=refill_history,
            temperature_trends=temperature_trends,
            alerts=self._get_alerts(machine, sales_data, temperature_trends),
        )

    def get_sales_data(
        self, machine_id: str, period: Optional[SalesPeriod] = None
    ) -> SalesData:
        """Get sales data for a vending machine

        Args:
            machine_id: Vending machine ID
            period: Sales period to get data for

        Returns:
            Sales data

        Raises:
            ValueError: If vending machine not found
        """
        # Verify machine exists
        machine = self.vending_machine_service.get_vending_machine(machine_id)
        if not machine:
            raise ValueError(f"Vending machine {machine_id} not found")

        # In a real implementation, we would query the database for sales data
        # Here, we'll generate mock data for testing
        return self._generate_mock_sales_data(machine, period)

    def get_usage_patterns(self, machine_id: str) -> UsagePattern:
        """Get usage patterns for a vending machine

        Args:
            machine_id: Vending machine ID

        Returns:
            Usage patterns

        Raises:
            ValueError: If vending machine not found
        """
        # Verify machine exists
        machine = self.vending_machine_service.get_vending_machine(machine_id)
        if not machine:
            raise ValueError(f"Vending machine {machine_id} not found")

        # In a real implementation, we would query the database for usage patterns
        # Here, we'll generate mock data for testing
        return self._generate_mock_usage_patterns(machine)

    def get_maintenance_history(self, machine_id: str) -> MaintenanceHistory:
        """Get maintenance history for a vending machine

        Args:
            machine_id: Vending machine ID

        Returns:
            Maintenance history

        Raises:
            ValueError: If vending machine not found
        """
        # Verify machine exists
        machine = self.vending_machine_service.get_vending_machine(machine_id)
        if not machine:
            raise ValueError(f"Vending machine {machine_id} not found")

        # In a real implementation, we would query the database for maintenance history
        # Here, we'll generate mock data for testing
        return self._generate_mock_maintenance_history(machine)

    def get_refill_history(self, machine_id: str) -> RefillHistory:
        """Get refill history for a vending machine

        Args:
            machine_id: Vending machine ID

        Returns:
            Refill history

        Raises:
            ValueError: If vending machine not found
        """
        # Verify machine exists
        machine = self.vending_machine_service.get_vending_machine(machine_id)
        if not machine:
            raise ValueError(f"Vending machine {machine_id} not found")

        # In a real implementation, we would query the database for refill history
        # Here, we'll generate mock data for testing
        return self._generate_mock_refill_history(machine)

    def get_temperature_trends(self, machine_id: str) -> TemperatureTrends:
        """Get temperature trends for a vending machine

        Args:
            machine_id: Vending machine ID

        Returns:
            Temperature trends

        Raises:
            ValueError: If vending machine not found
        """
        # Verify machine exists
        machine = self.vending_machine_service.get_vending_machine(machine_id)
        if not machine:
            raise ValueError(f"Vending machine {machine_id} not found")

        # In a real implementation, we would query the database for temperature readings
        # Here, we'll generate mock data for testing
        return self._generate_mock_temperature_trends(machine)

    def get_operational_status(self, machine_id: str) -> OperationalStatus:
        """Get real-time operational status for a Polar Delight ice cream machine

        Args:
            machine_id: Ice cream machine ID

        Returns:
            Real-time operational status data

        Raises:
            ValueError: If ice cream machine not found
        """
        # Verify machine exists
        machine = self.vending_machine_service.get_vending_machine(machine_id)
        if not machine:
            raise ValueError(f"Ice cream machine {machine_id} not found")

        # Get related data
        temp_trends = self._generate_mock_temperature_trends(machine)
        inventory = self._get_ice_cream_inventory(machine_id)

        # Set up consistent random seed based on machine ID
        # Use hash of the ID string to avoid issues with UUID format
        random.seed(hash(machine_id))

        # Format data for operational monitoring display
        return OperationalStatus(
            machine_id=machine_id,
            machine_status="Online"
            if machine.status == DeviceStatus.ONLINE
            else "Offline",
            last_updated=datetime.now(),
            # Status indicators
            cap_position={
                "capPosition": "Down",
                "status": "OK" if random.random() > 0.2 else "FAULT",
            },
            ram_position={
                "min": "55",
                "max": "95",
                "ramPosition": str(random.randint(60, 90)),
                "status": "OK" if random.random() > 0.3 else "FAULT",
            },
            cup_detect="Yes" if random.random() > 0.5 else "No",
            pod_bin_door="Closed" if random.random() > 0.2 else "Open",
            customer_door="Closed" if random.random() > 0.3 else "Open",
            pod_code=str(random.randint(80000, 89999)),
            cycle_status={
                "cycleStatus": "Complete" if random.random() > 0.3 else "In Progress",
                "status": "OK" if random.random() > 0.2 else "FAULT",
            },
            # Gauge metrics
            dispense_pressure={
                "min": "5",
                "max": "40",
                "needleValue": random.randint(30, 50),
                "dispensePressure": str(random.randint(30, 50)),
            },
            freezer_temperature={
                "freezerTemperature": str(temp_trends.current_temperature),
                "min": "-50",
                "needleValue": temp_trends.current_temperature,
                "max": "5",
            },
            max_ram_load={
                "min": "10",
                "max": "25",
                "ramLoad": str(random.randint(40, 60)),
                "status": "OK" if random.random() > 0.3 else "FAULT",
            },
            cycle_time={
                "cycleTime": str(random.randint(8, 15)),
                "min": "5",
                "needleValue": random.randint(8, 15),
                "max": "60",
            },
            # Inventory and location
            ice_cream_inventory=inventory,
            location=machine.location or "Unknown",
        )

    def _get_ice_cream_inventory(self, machine_id: str) -> List[IceCreamInventoryItem]:
        """Get ice cream inventory for a machine

        Args:
            machine_id: Machine ID

        Returns:
            List of ice cream inventory items
        """
        # Standard ice cream flavors with inventory levels
        # Use hash of machine_id for consistent randomization instead of the ID directly
        # This prevents issues when machine_id contains non-numeric characters
        random.seed(hash(machine_id))  # Consistent randomization

        flavors = [
            {"name": "Vanilla", "level": random.randint(1, 10)},
            {"name": "Strawberry ShortCake", "level": random.randint(1, 10)},
            {"name": "Chocolate", "level": random.randint(1, 10)},
            {"name": "Mint & Chocolate", "level": random.randint(1, 10)},
            {"name": "Cookies & Cream", "level": random.randint(1, 10)},
            {"name": "Salty Caramel", "level": random.randint(1, 10)},
        ]

        # Convert to model instances
        return [
            IceCreamInventoryItem(
                name=flavor["name"],
                current_level=flavor["level"],
                max_level=10,
                status="OK" if flavor["level"] > 3 else "Low",
            )
            for flavor in flavors
        ]

    def _get_alerts(
        self,
        machine: VendingMachine,
        sales_data: SalesData,
        temperature_trends: TemperatureTrends,
    ) -> List[AlertModel]:
        """Get alerts for a vending machine

        Args:
            machine: Vending machine
            sales_data: Sales data for the machine
            temperature_trends: Temperature trends for the machine

        Returns:
            List of alerts
        """
        alerts = []

        # Check if machine needs restocking
        # Add more sophisticated decision logic in a real implementation
        if machine.machine_status == VendingMachineStatus.NEEDS_RESTOCK:
            alerts.append(
                AlertModel(
                    alert_id=str(uuid.uuid4()),
                    alert_type=AlertType.INVENTORY,
                    severity=AlertSeverity.MEDIUM,
                    message="Machine needs restocking",
                    timestamp=datetime.now(),
                )
            )

        # Check if machine needs maintenance
        if machine.machine_status == VendingMachineStatus.MAINTENANCE_REQUIRED:
            alerts.append(
                AlertModel(
                    alert_id=str(uuid.uuid4()),
                    alert_type=AlertType.MAINTENANCE,
                    severity=AlertSeverity.HIGH,
                    message="Machine needs maintenance",
                    timestamp=datetime.now(),
                )
            )

        # Check temperature trends
        if (
            temperature_trends
            and temperature_trends.current_temperature is not None
            and temperature_trends.current_temperature > 5
        ):
            alerts.append(
                AlertModel(
                    alert_id=str(uuid.uuid4()),
                    alert_type=AlertType.TEMPERATURE,
                    severity=AlertSeverity.HIGH,
                    message=f"Temperature too high: {temperature_trends.current_temperature}°C",
                    timestamp=datetime.now(),
                )
            )

        # Check sales data
        if (
            sales_data
            and sales_data.total_sales is not None
            and sales_data.total_sales == 0
        ):
            alerts.append(
                AlertModel(
                    alert_id=str(uuid.uuid4()),
                    alert_type=AlertType.SALES,
                    severity=AlertSeverity.LOW,
                    message="No sales in the current period",
                    timestamp=datetime.now(),
                )
            )

        return alerts

    def _generate_mock_sales_data(
        self, machine: VendingMachine, period: Optional[SalesPeriod] = None
    ) -> SalesData:
        """Generate mock sales data for a vending machine

        Args:
            machine: Vending machine
            period: Sales period to generate data for

        Returns:
            Mock sales data
        """
        if not period:
            period = SalesPeriod.WEEK

        # Set up random seed based on machine ID for consistent randomization
        # Use hash of the ID string to avoid issues with UUID format
        random.seed(hash(machine.id))

        # Generate different ranges based on period
        if period == SalesPeriod.DAY:
            total_sales = random.randint(10, 50)
            start_date = datetime.now() - timedelta(days=1)
        elif period == SalesPeriod.WEEK:
            total_sales = random.randint(50, 200)
            start_date = datetime.now() - timedelta(weeks=1)
        elif period == SalesPeriod.MONTH:
            total_sales = random.randint(200, 800)
            start_date = datetime.now() - timedelta(days=30)
        else:  # YEAR
            total_sales = random.randint(2000, 10000)
            start_date = datetime.now() - timedelta(days=365)

        # Generate total revenue
        avg_price = 2.5  # Average price per item
        total_revenue = (
            total_sales * avg_price * (0.9 + 0.2 * random.random())
        )  # Add some variation

        # Generate mock product sales
        product_sales = []
        if machine.products:
            # If machine has products, use them
            for product in machine.products:
                sales_count = int(
                    total_sales * random.random() * 0.5
                )  # Random portion of total sales
                product_sales.append(
                    ProductSale(
                        product_id=product.product_id,
                        product_name=product.name,
                        sales_count=sales_count,
                        sales_revenue=sales_count * product.price,
                    )
                )
        else:
            # Otherwise generate generic products
            product_names = [
                "Ice Cream - Vanilla",
                "Ice Cream - Chocolate",
                "Ice Cream - Strawberry",
                "Ice Cream - Mint",
                "Ice Cream - Cookie Dough",
            ]
            remaining_sales = total_sales
            for i, name in enumerate(product_names):
                # Last product gets all remaining sales
                if i == len(product_names) - 1:
                    sales_count = remaining_sales
                else:
                    sales_count = int(remaining_sales * random.random() * 0.5)
                    remaining_sales -= sales_count

                product_price = (
                    2.0 + random.random() * 1.5
                )  # Random price between $2.00 and $3.50
                product_sales.append(
                    ProductSale(
                        product_id=f"P{i+1}",
                        product_name=name,
                        sales_count=sales_count,
                        sales_revenue=sales_count * product_price,
                    )
                )

        # Return sales data
        return SalesData(
            period=period,
            total_sales=total_sales,
            total_revenue=total_revenue,
            product_sales=product_sales,
            start_date=start_date,
            end_date=datetime.now(),
        )

    def _generate_mock_usage_patterns(self, machine: VendingMachine) -> UsagePattern:
        """Generate mock usage patterns for a vending machine

        Args:
            machine: Vending machine

        Returns:
            Mock usage patterns
        """
        # Set up random seed based on machine ID for consistent randomization
        # Use hash of the ID string to avoid issues with UUID format
        random.seed(hash(machine.id))

        # Generate time of day distribution
        time_of_day = {
            TimeOfDay.MORNING: 20 + random.randint(0, 15),
            TimeOfDay.AFTERNOON: 35 + random.randint(0, 15),
            TimeOfDay.EVENING: 25 + random.randint(0, 15),
            TimeOfDay.NIGHT: 5 + random.randint(0, 10),
        }

        # Normalize to 100%
        total = sum(time_of_day.values())
        for key in time_of_day:
            time_of_day[key] = int(time_of_day[key] * 100 / total)

        # Ensure total is exactly 100%
        diff = 100 - sum(time_of_day.values())
        if diff != 0:
            # Add/subtract the difference from the largest value
            largest_key = max(time_of_day, key=time_of_day.get)
            time_of_day[largest_key] += diff

        # Generate day of week distribution
        day_of_week = {
            DayOfWeek.MONDAY: 10 + random.randint(0, 10),
            DayOfWeek.TUESDAY: 10 + random.randint(0, 10),
            DayOfWeek.WEDNESDAY: 15 + random.randint(0, 10),
            DayOfWeek.THURSDAY: 15 + random.randint(0, 10),
            DayOfWeek.FRIDAY: 20 + random.randint(0, 10),
            DayOfWeek.SATURDAY: 15 + random.randint(0, 10),
            DayOfWeek.SUNDAY: 10 + random.randint(0, 10),
        }

        # Normalize to 100%
        total = sum(day_of_week.values())
        for key in day_of_week:
            day_of_week[key] = int(day_of_week[key] * 100 / total)

        # Ensure total is exactly 100%
        diff = 100 - sum(day_of_week.values())
        if diff != 0:
            # Add/subtract the difference from the largest value
            largest_key = max(day_of_week, key=day_of_week.get)
            day_of_week[largest_key] += diff

        # Generate peak hours
        peak_hours = []
        # Morning peak
        peak_hours.append(7 + random.randint(0, 2))
        # Lunch peak
        peak_hours.append(12 + random.randint(0, 1))
        # Afternoon peak
        peak_hours.append(15 + random.randint(0, 2))
        # Evening peak
        peak_hours.append(18 + random.randint(0, 2))

        # Return usage pattern
        return UsagePattern(
            time_of_day=time_of_day,
            day_of_week=day_of_week,
            peak_hours=peak_hours,
            average_transaction_time=random.randint(15, 60),  # seconds
        )

    def _generate_mock_maintenance_history(
        self, machine: VendingMachine
    ) -> MaintenanceHistory:
        """Generate mock maintenance history for a vending machine

        Args:
            machine: Vending machine

        Returns:
            Mock maintenance history
        """
        # Set up random seed based on machine ID for consistent randomization
        # Use hash of the ID string to avoid issues with UUID format
        random.seed(hash(machine.id))

        # Generate maintenance events
        events = []
        # Start date for maintenance history
        start_date = datetime.now() - timedelta(days=365)

        # Generate random maintenance events
        num_events = random.randint(3, 8)
        for i in range(num_events):
            # Random date between start_date and now
            event_date = start_date + timedelta(days=random.randint(0, 365))
            if event_date > datetime.now():
                event_date = datetime.now() - timedelta(days=random.randint(1, 30))

            # Random maintenance type
            maintenance_type = random.choice(list(MaintenanceType))

            # Generate event
            events.append(
                MaintenanceEvent(
                    event_id=str(uuid.uuid4()),
                    maintenance_type=maintenance_type,
                    technician=f"Tech {random.randint(1, 5)}",
                    notes=f"Routine {maintenance_type.value} maintenance",
                    duration=random.randint(15, 120),  # minutes
                    timestamp=event_date,
                )
            )

        # Sort events by date
        events.sort(key=lambda e: e.timestamp)

        # Return maintenance history
        return MaintenanceHistory(
            machine_id=machine.id,
            events=events,
            last_maintenance=events[-1].timestamp if events else None,
            next_scheduled_maintenance=datetime.now()
            + timedelta(days=random.randint(30, 90)),
        )

    def _generate_mock_refill_history(self, machine: VendingMachine) -> RefillHistory:
        """Generate mock refill history for a vending machine

        Args:
            machine: Vending machine

        Returns:
            Mock refill history
        """
        # Set up random seed based on machine ID for consistent randomization
        # Use hash of the ID string to avoid issues with UUID format
        random.seed(hash(machine.id))

        # Generate refill events
        events = []
        # Start date for refill history
        start_date = datetime.now() - timedelta(days=90)

        # Generate random refill events
        num_events = random.randint(5, 12)
        for i in range(num_events):
            # Random date between start_date and now
            event_date = start_date + timedelta(days=random.randint(0, 90))
            if event_date > datetime.now():
                event_date = datetime.now() - timedelta(days=random.randint(1, 10))

            # Generate refill items
            items = []
            if machine.products:
                # If machine has products, use them
                for product in machine.products:
                    if random.random() > 0.3:  # 70% chance to refill each product
                        items.append(
                            RefillItem(
                                product_id=product.product_id,
                                product_name=product.name,
                                quantity=random.randint(5, 20),
                            )
                        )
            else:
                # Otherwise generate generic products
                product_names = [
                    "Ice Cream - Vanilla",
                    "Ice Cream - Chocolate",
                    "Ice Cream - Strawberry",
                    "Ice Cream - Mint",
                    "Ice Cream - Cookie Dough",
                ]
                for i, name in enumerate(product_names):
                    if random.random() > 0.3:  # 70% chance to refill each product
                        items.append(
                            RefillItem(
                                product_id=f"P{i+1}",
                                product_name=name,
                                quantity=random.randint(5, 20),
                            )
                        )

            # Generate event
            events.append(
                RefillEvent(
                    event_id=str(uuid.uuid4()),
                    staff_member=f"Staff {random.randint(1, 5)}",
                    items=items,
                    notes="Regular refill"
                    if random.random() > 0.2
                    else "Emergency refill - low stock",
                    timestamp=event_date,
                )
            )

        # Sort events by date
        events.sort(key=lambda e: e.timestamp)

        # Calculate next scheduled refill
        next_scheduled_refill = datetime.now() + timedelta(days=random.randint(1, 10))

        # Return refill history
        return RefillHistory(
            machine_id=machine.id,
            events=events,
            last_refill=events[-1].timestamp if events else None,
            next_scheduled_refill=next_scheduled_refill,
        )

    def _generate_mock_temperature_trends(
        self, machine: VendingMachine
    ) -> TemperatureTrends:
        """Generate mock temperature trends for a vending machine

        Args:
            machine: Vending machine

        Returns:
            Mock temperature trends
        """
        # Set up random seed based on machine ID for consistent randomization
        # Use hash of the ID string to avoid issues with UUID format
        random.seed(hash(machine.id))

        # Generate temperature readings
        readings = []
        # Start date for temperature readings
        start_date = datetime.now() - timedelta(days=7)

        # Base temperature and fluctuation
        base_temp = -18 + random.randint(
            0, 4
        )  # Base temperature between -18°C and -14°C

        # Generate readings every hour for the past week
        current_date = start_date
        while current_date <= datetime.now():
            # Add some random fluctuation to the base temperature
            temp = base_temp + random.uniform(-2, 2)

            # Add daily cycle fluctuation (slightly warmer during the day)
            hour = current_date.hour
            if 8 <= hour <= 20:  # Daytime hours
                temp += random.uniform(0, 1)

            # Add some rare temperature spikes
            if random.random() < 0.02:  # 2% chance
                temp += random.uniform(3, 8)

            readings.append(
                TemperatureReading(timestamp=current_date, temperature=round(temp, 1))
            )

            # Increment by 1 hour
            current_date += timedelta(hours=1)

        # Calculate current temperature (latest reading)
        current_temperature = readings[-1].temperature if readings else base_temp

        # Calculate average temperature
        avg_temperature = (
            round(mean(r.temperature for r in readings), 1) if readings else base_temp
        )

        # Calculate min and max temperatures
        min_temperature = (
            round(min(r.temperature for r in readings), 1)
            if readings
            else base_temp - 2
        )
        max_temperature = (
            round(max(r.temperature for r in readings), 1)
            if readings
            else base_temp + 2
        )

        # Return temperature trends
        return TemperatureTrends(
            machine_id=machine.id,
            readings=readings,
            current_temperature=current_temperature,
            average_temperature=avg_temperature,
            min_temperature=min_temperature,
            max_temperature=max_temperature,
        )
