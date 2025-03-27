"""
Vending machine operations service implementation
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
import random
from statistics import mean

from src.models.vending_machine import VendingMachine, VendingMachineReading
from src.models.vending_machine_operations import (
    SalesPeriod,
    ProductSale,
    SalesData,
    TimeOfDay,
    DayOfWeek, 
    UsagePattern,
    MaintenanceType,
    MaintenanceEvent,
    MaintenanceHistory,
    RefillItem,
    RefillEvent,
    RefillHistory,
    TemperatureReading,
    TemperatureTrends,
    OperationsSummary
)

class VendingMachineOperationsService:
    """Service for vending machine operations analysis and reporting"""
    
    def __init__(self, db, vending_machine_service):
        """Initialize service with database and vending machine service
        
        Args:
            db: Database instance for persistence
            vending_machine_service: VendingMachineService instance for accessing vending machine data
        """
        self.db = db
        self.vending_machine_service = vending_machine_service
    
    def get_operations_summary(self, machine_id: str) -> OperationsSummary:
        """Get complete operations summary for a vending machine
        
        Args:
            machine_id: Vending machine ID
            
        Returns:
            Operations summary
            
        Raises:
            ValueError: If vending machine not found
        """
        # Get vending machine to validate its existence
        machine = self.vending_machine_service.get_vending_machine(machine_id)
        
        # Get individual data components
        sales_data = self.get_sales_data(machine_id, period=SalesPeriod.WEEK)
        usage_pattern = self.get_usage_patterns(machine_id)
        maintenance_history = self.get_maintenance_history(machine_id)
        refill_history = self.get_refill_history(machine_id)
        temperature_trends = self.get_temperature_trends(machine_id)
        
        # Build complete operations summary
        summary = OperationsSummary(
            machine_id=machine_id,
            as_of=datetime.now(),
            sales=sales_data,
            usage=usage_pattern,
            maintenance=maintenance_history,
            refills=refill_history,
            temperature=temperature_trends
        )
        
        return summary
    
    def get_sales_data(self, machine_id: str, period: Union[str, SalesPeriod] = SalesPeriod.WEEK) -> SalesData:
        """Get sales data for a vending machine
        
        Args:
            machine_id: Vending machine ID
            period: Time period for data aggregation
            
        Returns:
            Sales data
            
        Raises:
            ValueError: If vending machine not found or period is invalid
        """
        # Validate vending machine existence
        machine = self.vending_machine_service.get_vending_machine(machine_id)
        
        # Convert string period to enum if needed
        if isinstance(period, str):
            try:
                period = SalesPeriod(period)
            except ValueError:
                raise ValueError(f"Invalid period: {period}")
        
        # Determine date range based on period
        end_date = datetime.now()
        if period == SalesPeriod.DAY:
            start_date = end_date - timedelta(days=1)
        elif period == SalesPeriod.WEEK:
            start_date = end_date - timedelta(weeks=1)
        elif period == SalesPeriod.MONTH:
            start_date = end_date - timedelta(days=30)
        elif period == SalesPeriod.QUARTER:
            start_date = end_date - timedelta(days=90)
        elif period == SalesPeriod.YEAR:
            start_date = end_date - timedelta(days=365)
        else:
            raise ValueError(f"Unsupported period: {period}")
        
        # Retrieve sales data from database or generate mock data
        # TODO: Replace with actual database calls in production
        sales_data = self._generate_mock_sales_data(machine, period, start_date, end_date)
        
        return sales_data
    
    def get_usage_patterns(self, machine_id: str) -> UsagePattern:
        """Get usage patterns for a vending machine
        
        Args:
            machine_id: Vending machine ID
            
        Returns:
            Usage pattern data
            
        Raises:
            ValueError: If vending machine not found
        """
        # Validate vending machine existence
        machine = self.vending_machine_service.get_vending_machine(machine_id)
        
        # Retrieve usage pattern data from database or generate mock data
        # TODO: Replace with actual database calls in production
        usage_pattern = self._generate_mock_usage_patterns(machine)
        
        return usage_pattern
    
    def get_maintenance_history(self, machine_id: str) -> MaintenanceHistory:
        """Get maintenance history for a vending machine
        
        Args:
            machine_id: Vending machine ID
            
        Returns:
            Maintenance history
            
        Raises:
            ValueError: If vending machine not found
        """
        # Validate vending machine existence
        machine = self.vending_machine_service.get_vending_machine(machine_id)
        
        # Retrieve maintenance history from database or generate mock data
        # TODO: Replace with actual database calls in production
        maintenance_history = self._generate_mock_maintenance_history(machine)
        
        return maintenance_history
    
    def get_refill_history(self, machine_id: str) -> RefillHistory:
        """Get refill history for a vending machine
        
        Args:
            machine_id: Vending machine ID
            
        Returns:
            Refill history
            
        Raises:
            ValueError: If vending machine not found
        """
        # Validate vending machine existence
        machine = self.vending_machine_service.get_vending_machine(machine_id)
        
        # Retrieve refill history from database or generate mock data
        # TODO: Replace with actual database calls in production
        refill_history = self._generate_mock_refill_history(machine)
        
        return refill_history
    
    def get_temperature_trends(self, machine_id: str) -> TemperatureTrends:
        """Get temperature trends for a vending machine
        
        Args:
            machine_id: Vending machine ID
            
        Returns:
            Temperature trends
            
        Raises:
            ValueError: If vending machine not found
        """
        # Validate vending machine existence
        machine = self.vending_machine_service.get_vending_machine(machine_id)
        
        # Get readings from machine
        readings = machine.readings
        
        # If readings exists, extract temperature data
        if readings:
            temp_readings = [
                TemperatureReading(
                    timestamp=reading.timestamp,
                    temperature=reading.temperature or 0.0,
                    is_normal=True if reading.temperature and -10 <= reading.temperature <= 10 else False
                )
                for reading in readings
                if reading.temperature is not None
            ]
            
            # Calculate statistics
            if temp_readings:
                temperatures = [r.temperature for r in temp_readings]
                avg_temp = mean(temperatures) if temperatures else None
                min_temp = min(temperatures) if temperatures else None
                max_temp = max(temperatures) if temperatures else None
                abnormal_count = sum(1 for r in temp_readings if not r.is_normal)
                
                trends = TemperatureTrends(
                    readings=temp_readings,
                    average_temperature=avg_temp,
                    min_temperature=min_temp,
                    max_temperature=max_temp,
                    abnormal_readings_count=abnormal_count
                )
            else:
                # No temperature readings available
                trends = self._generate_mock_temperature_trends(machine)
        else:
            # No readings available at all
            trends = self._generate_mock_temperature_trends(machine)
        
        return trends
    
    # ----- Helper Methods for Generating Mock Data -----
    # Note: These would be replaced with actual database calls in production
    
    def _generate_mock_sales_data(self, machine: VendingMachine, 
                                period: SalesPeriod, 
                                start_date: datetime, 
                                end_date: datetime) -> SalesData:
        """Generate mock sales data for development and testing
        
        Args:
            machine: Vending machine
            period: Time period
            start_date: Start date
            end_date: End date
            
        Returns:
            Mock sales data
        """
        # Get products from machine
        products = machine.products
        
        # Generate mock sales for each product
        total_sales = 0
        total_revenue = 0.0
        product_sales = []
        
        for product in products:
            # Mock quantities sold
            quantity_sold = random.randint(3, 20)
            revenue = quantity_sold * product.price
            
            product_sale = ProductSale(
                product_id=product.product_id,
                name=product.name,
                quantity_sold=quantity_sold,
                revenue=revenue,
                percentage_of_total=0.0  # Will calculate after total is known
            )
            
            product_sales.append(product_sale)
            total_sales += quantity_sold
            total_revenue += revenue
        
        # If no products, create some mock ones
        if not product_sales:
            mock_products = [
                ("Polar Ice", 12, 3.50),
                ("Arctic Freeze", 8, 4.00),
                ("Glacier Mint", 10, 3.75),
                ("Frosty Delight", 15, 2.50),
                ("Winter Blast", 5, 5.00)
            ]
            
            for name, qty, price in mock_products:
                revenue = qty * price
                product_id = f"mock-{uuid.uuid4()}"
                
                product_sale = ProductSale(
                    product_id=product_id,
                    name=name,
                    quantity_sold=qty,
                    revenue=revenue,
                    percentage_of_total=0.0  # Will calculate after total is known
                )
                
                product_sales.append(product_sale)
                total_sales += qty
                total_revenue += revenue
        
        # Calculate percentages
        for product_sale in product_sales:
            if total_revenue > 0:
                product_sale.percentage_of_total = (product_sale.revenue / total_revenue) * 100
            else:
                product_sale.percentage_of_total = 0.0
        
        # Create sales data
        sales_data = SalesData(
            period=period,
            start_date=start_date,
            end_date=end_date,
            total_sales=total_sales,
            total_revenue=total_revenue,
            product_sales=product_sales
        )
        
        return sales_data
    
    def _generate_mock_usage_patterns(self, machine: VendingMachine) -> UsagePattern:
        """Generate mock usage patterns for development and testing
        
        Args:
            machine: Vending machine
            
        Returns:
            Mock usage pattern data
        """
        # Mock time of day distribution
        time_of_day = {
            TimeOfDay.MORNING: random.randint(10, 30),
            TimeOfDay.MIDDAY: random.randint(20, 50),
            TimeOfDay.AFTERNOON: random.randint(15, 40),
            TimeOfDay.EVENING: random.randint(5, 25),
            TimeOfDay.NIGHT: random.randint(1, 10)
        }
        
        # Mock day of week distribution
        day_of_week = {
            DayOfWeek.MONDAY: random.randint(10, 30),
            DayOfWeek.TUESDAY: random.randint(10, 30),
            DayOfWeek.WEDNESDAY: random.randint(15, 35),
            DayOfWeek.THURSDAY: random.randint(15, 35),
            DayOfWeek.FRIDAY: random.randint(20, 40),
            DayOfWeek.SATURDAY: random.randint(5, 15),
            DayOfWeek.SUNDAY: random.randint(5, 15)
        }
        
        # Get products from machine or use mock products
        products = machine.products
        if not products:
            mock_products = [
                ("Polar Ice", 12, 3.50),
                ("Arctic Freeze", 8, 4.00),
                ("Glacier Mint", 10, 3.75),
                ("Frosty Delight", 15, 2.50),
                ("Winter Blast", 5, 5.00)
            ]
            
            popular_products = []
            for name, qty, price in mock_products[:3]:  # Top 3 most popular
                product_id = f"mock-{uuid.uuid4()}"
                
                product_sale = ProductSale(
                    product_id=product_id,
                    name=name,
                    quantity_sold=qty,
                    revenue=qty * price,
                    percentage_of_total=random.uniform(15.0, 30.0)
                )
                
                popular_products.append(product_sale)
        else:
            # Use a subset of actual products
            popular_products = []
            for product in products[:min(3, len(products))]:
                quantity_sold = random.randint(10, 30)
                
                product_sale = ProductSale(
                    product_id=product.product_id,
                    name=product.name,
                    quantity_sold=quantity_sold,
                    revenue=quantity_sold * product.price,
                    percentage_of_total=random.uniform(15.0, 30.0)
                )
                
                popular_products.append(product_sale)
        
        # Peak hour and sales
        peak_hour = random.randint(11, 14)  # Most common peak is lunchtime
        peak_sales = random.randint(10, 25)
        
        # Create usage pattern
        usage_pattern = UsagePattern(
            time_of_day=time_of_day,
            day_of_week=day_of_week,
            popular_products=popular_products,
            peak_hour=peak_hour,
            peak_sales=peak_sales
        )
        
        return usage_pattern
    
    def _generate_mock_maintenance_history(self, machine: VendingMachine) -> MaintenanceHistory:
        """Generate mock maintenance history for development and testing
        
        Args:
            machine: Vending machine
            
        Returns:
            Mock maintenance history
        """
        # Generate a few mock maintenance events
        events = []
        
        # Maintenance types to simulate
        maintenance_types = [
            (MaintenanceType.CLEANING, "Routine cleaning", ["Filter", "Dispenser"], 45),
            (MaintenanceType.RESTOCK, "Product restocking", [], 30),
            (MaintenanceType.REPAIR, "Cooling system repair", ["Compressor", "Refrigerant"], 120),
            (MaintenanceType.INSPECTION, "Quarterly inspection", [], 60),
            (MaintenanceType.CASH_COLLECTION, "Cash collection", [], 15)
        ]
        
        # Generate events over the past 6 months
        now = datetime.now()
        num_events = random.randint(3, 8)
        
        for i in range(num_events):
            # Random date in past 6 months
            days_ago = random.randint(1, 180)
            event_date = now - timedelta(days=days_ago)
            
            # Random maintenance type
            maint_type, desc, parts, duration = random.choice(maintenance_types)
            
            event = MaintenanceEvent(
                event_id=str(uuid.uuid4()),
                event_type=maint_type,
                timestamp=event_date,
                technician=f"Tech {random.randint(1001, 9999)}",
                description=desc,
                parts_replaced=parts if maint_type == MaintenanceType.REPAIR else None,
                cost=random.uniform(50, 500) if maint_type == MaintenanceType.REPAIR else None,
                duration_minutes=duration
            )
            
            events.append(event)
        
        # Sort events by timestamp, newest first
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        # Calculate total downtime
        total_downtime = sum(e.duration_minutes for e in events)
        
        # Determine last maintenance and next scheduled
        last_maintenance = events[0].timestamp if events else None
        next_scheduled = now + timedelta(days=random.randint(7, 30))
        
        # Create maintenance history
        maintenance_history = MaintenanceHistory(
            events=events,
            last_maintenance=last_maintenance,
            next_scheduled=next_scheduled,
            total_downtime_minutes=total_downtime
        )
        
        return maintenance_history
    
    def _generate_mock_refill_history(self, machine: VendingMachine) -> RefillHistory:
        """Generate mock refill history for development and testing
        
        Args:
            machine: Vending machine
            
        Returns:
            Mock refill history
        """
        # Generate mock refill events
        events = []
        
        # Get products or use mock products
        products = machine.products
        if not products:
            mock_products = [
                ("Polar Ice", 12),
                ("Arctic Freeze", 8),
                ("Glacier Mint", 10),
                ("Frosty Delight", 15),
                ("Winter Blast", 5)
            ]
            
            product_list = []
            for name, qty in mock_products:
                product_list.append((f"mock-{uuid.uuid4()}", name, qty))
        else:
            product_list = [(p.product_id, p.name, p.quantity) for p in products]
        
        # Generate events over the past 3 months
        now = datetime.now()
        num_events = random.randint(2, 6)
        
        product_refill_counts = {}  # Track which products are refilled most
        
        for i in range(num_events):
            # Random date in past 3 months
            days_ago = random.randint(1, 90)
            event_date = now - timedelta(days=days_ago)
            
            # Randomly select products to refill
            num_products = random.randint(1, min(len(product_list), 4))
            refilled_products = random.sample(product_list, num_products)
            
            refill_items = []
            total_quantity = 0
            total_cost = 0.0
            
            for product_id, name, _ in refilled_products:
                quantity = random.randint(5, 20)
                cost = quantity * random.uniform(1.0, 3.0)  # Cost per item
                
                refill_item = RefillItem(
                    product_id=product_id,
                    name=name,
                    quantity=quantity,
                    cost=cost
                )
                
                refill_items.append(refill_item)
                total_quantity += quantity
                total_cost += cost
                
                # Track refill counts for determining most refilled product
                if product_id in product_refill_counts:
                    product_refill_counts[product_id] = (product_refill_counts[product_id][0] + quantity, name)
                else:
                    product_refill_counts[product_id] = (quantity, name)
            
            event = RefillEvent(
                refill_id=str(uuid.uuid4()),
                timestamp=event_date,
                operator=f"Operator {random.randint(101, 999)}",
                items=refill_items,
                total_quantity=total_quantity,
                total_cost=total_cost
            )
            
            events.append(event)
        
        # Sort events by timestamp, newest first
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        # Determine most refilled product
        most_refilled_product = None
        most_refilled_quantity = 0
        
        for product_id, (quantity, name) in product_refill_counts.items():
            if quantity > most_refilled_quantity:
                most_refilled_quantity = quantity
                most_refilled_product = name
        
        # Create refill history
        refill_history = RefillHistory(
            events=events,
            last_refill=events[0].timestamp if events else None,
            most_refilled_product=most_refilled_product
        )
        
        return refill_history
    
    def _generate_mock_temperature_trends(self, machine: VendingMachine) -> TemperatureTrends:
        """Generate mock temperature trends for development and testing
        
        Args:
            machine: Vending machine
            
        Returns:
            Mock temperature trends
        """
        # Generate mock temperature readings for past week
        now = datetime.now()
        readings = []
        
        # Set a base temperature (typical for a freezer)
        base_temp = -5.0
        
        # Generate a reading every 2 hours for past 7 days
        for hours in range(0, 24 * 7, 2):
            timestamp = now - timedelta(hours=hours)
            
            # Random variation around base temperature
            variation = random.uniform(-3.0, 3.0)
            temperature = base_temp + variation
            
            # Determine if temperature is normal
            is_normal = -10 <= temperature <= 0
            
            reading = TemperatureReading(
                timestamp=timestamp,
                temperature=temperature,
                is_normal=is_normal
            )
            
            readings.append(reading)
        
        # Sort readings by timestamp
        readings.sort(key=lambda r: r.timestamp)
        
        # Calculate statistics
        temperatures = [r.temperature for r in readings]
        avg_temp = mean(temperatures) if temperatures else None
        min_temp = min(temperatures) if temperatures else None
        max_temp = max(temperatures) if temperatures else None
        abnormal_count = sum(1 for r in readings if not r.is_normal)
        
        # Create temperature trends
        trends = TemperatureTrends(
            readings=readings,
            average_temperature=avg_temp,
            min_temperature=min_temp,
            max_temperature=max_temp,
            abnormal_readings_count=abnormal_count
        )
        
        return trends