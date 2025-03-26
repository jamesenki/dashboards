"""
Polar Delight Ice Cream Machine operations models
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union

from pydantic import BaseModel, Field

# ------ Sales Data Models ------

class SalesPeriod(str, Enum):
    """Time period for sales data aggregation"""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

class ProductSale(BaseModel):
    """Individual ice cream flavor sale statistics"""
    product_id: str = Field(..., description="Unique ice cream flavor identifier")
    name: str = Field(..., description="Ice cream flavor name")
    quantity_sold: int = Field(..., description="Quantity sold in the period")
    revenue: float = Field(..., description="Revenue generated in the period")
    percentage_of_total: float = Field(..., description="Percentage of total sales")

class SalesData(BaseModel):
    """Aggregated sales data for a specific period"""
    period: SalesPeriod = Field(..., description="Time period for this data")
    start_date: datetime = Field(..., description="Start date of the period")
    end_date: datetime = Field(..., description="End date of the period")
    total_sales: int = Field(..., description="Total number of items sold")
    total_revenue: float = Field(..., description="Total revenue generated")
    product_sales: List[ProductSale] = Field(default_factory=list, description="Sales by product")
    
    class Config:
        """Pydantic config"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ------ Usage Pattern Models ------

class TimeOfDay(str, Enum):
    """Time of day categorization"""
    MORNING = "morning"      # 6am-11am
    MIDDAY = "midday"        # 11am-2pm
    AFTERNOON = "afternoon"  # 2pm-5pm
    EVENING = "evening"      # 5pm-9pm
    NIGHT = "night"          # 9pm-6am

class DayOfWeek(str, Enum):
    """Days of week"""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"

class UsagePattern(BaseModel):
    """Usage pattern statistics"""
    time_of_day: Dict[TimeOfDay, int] = Field(default_factory=dict, description="Sales by time of day")
    day_of_week: Dict[DayOfWeek, int] = Field(default_factory=dict, description="Sales by day of week")
    popular_products: List[ProductSale] = Field(default_factory=list, description="Most popular products")
    peak_hour: Optional[int] = Field(None, description="Hour with most sales (0-23)")
    peak_sales: Optional[int] = Field(None, description="Sales count during peak hour")

# ------ Maintenance Models ------

class MaintenanceType(str, Enum):
    """Type of maintenance event"""
    CLEANING = "cleaning"
    RESTOCK = "restock"
    REPAIR = "repair"
    INSPECTION = "inspection"
    CASH_COLLECTION = "cash_collection"

class MaintenanceEvent(BaseModel):
    """Maintenance event record"""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: MaintenanceType = Field(..., description="Type of maintenance event")
    timestamp: datetime = Field(..., description="When the event occurred")
    technician: Optional[str] = Field(None, description="Person who performed maintenance")
    description: Optional[str] = Field(None, description="Description of maintenance performed")
    parts_replaced: Optional[List[str]] = Field(None, description="Parts that were replaced")
    cost: Optional[float] = Field(None, description="Cost of maintenance")
    duration_minutes: Optional[int] = Field(None, description="Duration of maintenance in minutes")

class MaintenanceHistory(BaseModel):
    """Maintenance history for a vending machine"""
    events: List[MaintenanceEvent] = Field(default_factory=list, description="Maintenance events")
    last_maintenance: Optional[datetime] = Field(None, description="Last maintenance date")
    next_scheduled: Optional[datetime] = Field(None, description="Next scheduled maintenance")
    total_downtime_minutes: int = Field(0, description="Total downtime in minutes")

# ------ Refill History Models ------

class RefillItem(BaseModel):
    """Item refilled in a refill event"""
    product_id: str = Field(..., description="Product identifier")
    name: str = Field(..., description="Product name")
    quantity: int = Field(..., description="Quantity refilled")
    cost: Optional[float] = Field(None, description="Cost of refilled items")

class RefillEvent(BaseModel):
    """Refill event record"""
    refill_id: str = Field(..., description="Unique refill identifier")
    timestamp: datetime = Field(..., description="When the refill occurred")
    operator: Optional[str] = Field(None, description="Person who performed the refill")
    items: List[RefillItem] = Field(default_factory=list, description="Items refilled")
    total_quantity: int = Field(0, description="Total quantity of all items")
    total_cost: Optional[float] = Field(None, description="Total cost of refill")

class RefillHistory(BaseModel):
    """Refill history for a vending machine"""
    events: List[RefillEvent] = Field(default_factory=list, description="Refill events")
    last_refill: Optional[datetime] = Field(None, description="Last refill date")
    most_refilled_product: Optional[str] = Field(None, description="Most frequently refilled product")

# ------ Temperature Trend Models ------

class TemperatureReading(BaseModel):
    """Individual temperature reading"""
    timestamp: datetime = Field(..., description="When the reading was taken")
    temperature: float = Field(..., description="Temperature in Celsius")
    is_normal: bool = Field(True, description="Whether temperature is within normal range")

class TemperatureTrends(BaseModel):
    """Temperature trends for a vending machine"""
    readings: List[TemperatureReading] = Field(default_factory=list, description="Temperature readings")
    current_temperature: Optional[float] = Field(None, description="Current temperature (most recent reading)")
    average_temperature: Optional[float] = Field(None, description="Average temperature")
    min_temperature: Optional[float] = Field(None, description="Minimum temperature")
    max_temperature: Optional[float] = Field(None, description="Maximum temperature")
    abnormal_readings_count: int = Field(0, description="Count of abnormal readings")

# ------ Status Indicators Model ------

class MachineStatus(BaseModel):
    """Current status of ice cream machine components"""
    machine: str = Field("Online", description="Overall machine status (Online/Offline)")
    pod_code: str = Field("OK", description="POD code reader status")
    cup_detect: str = Field("Yes", description="Cup detection status (Yes/No)")
    pod_bin_door: str = Field("Closed", description="POD bin door status (Open/Closed)")
    customer_door: str = Field("Closed", description="Customer door status (Open/Closed)")

# ------ Gauge Indicators Model ------

class GaugeData(BaseModel):
    """Data for a single gauge indicator"""
    value: float = Field(..., description="Current value in native units")
    min: float = Field(..., description="Minimum value in native units")
    max: float = Field(..., description="Maximum value in native units")
    needle_value: float = Field(..., description="Percentage value for needle position (0-100)")
    display_suffix: Optional[str] = Field(None, description="Unit suffix for display (e.g., '°F', 'lb', 'sec')")
    status: Optional[str] = Field(None, description="Status indicator (e.g., 'Normal', 'Warning')")

class GaugeIndicators(BaseModel):
    """Gauge indicator values for the Polar Delight dashboard"""
    asset_health: GaugeData = Field(..., description="Asset health gauge data")
    freezer_temperature: GaugeData = Field(..., description="Freezer temperature gauge data")
    dispense_force: GaugeData = Field(..., description="Dispense force gauge data")
    cycle_time: GaugeData = Field(..., description="Cycle time gauge data")
    max_ram_load: Optional[GaugeData] = Field(None, description="Maximum RAM load data")

# ------ Alert Model ------

class AlertSeverity(str, Enum):
    """Severity level of an alert"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertModel(BaseModel):
    """Alert notification for vending machine"""
    id: str = Field(..., description="Unique alert identifier")
    timestamp: datetime = Field(..., description="When the alert was generated")
    severity: AlertSeverity = Field(..., description="Alert severity level")
    title: str = Field(..., description="Short alert title")
    message: str = Field(..., description="Detailed alert message")
    resolved: bool = Field(False, description="Whether the alert has been resolved")
    
    class Config:
        """Pydantic config"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ------ Ice Cream Inventory Model ------

class IceCreamInventoryItem(BaseModel):
    """Single ice cream flavor inventory item"""
    name: str = Field(..., description="Ice cream flavor name (e.g., 'Vanilla Pods')")
    current_level: int = Field(..., description="Current quantity available")
    max_level: int = Field(10, description="Maximum capacity")
    status: str = Field("Normal", description="Inventory status (OK, Low, Critical)")
    
    # Alias for compatibility with frontend expecting 'amount'
    amount: Optional[int] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        # Automatically set amount to match current_level for backward compatibility
        if self.amount is None and hasattr(self, 'current_level'):
            self.amount = self.current_level

# ------ Asset Health Model ------

class AssetHealth(BaseModel):
    """Comprehensive asset health data for a Polar Delight ice cream machine"""
    asset_id: str = Field(..., description="Unique identifier for the ice cream machine")
    machine_status: str = Field("Online", description="Overall machine status (Online/Offline)")
    pod_code: str = Field(..., description="POD code identifier")
    cup_detect: str = Field("Yes", description="Cup detection status (Yes/No)")
    pod_bin_door: str = Field("Closed", description="POD bin door status (Open/Closed)")
    customer_door: str = Field("Closed", description="Customer door status (Open/Closed)")
    
    # Gauge data
    asset_health: Dict[str, Any] = Field(..., description="Asset health gauge data")
    freezer_temperature: Dict[str, Any] = Field(..., description="Freezer temperature gauge data")
    dispense_force: Dict[str, Any] = Field(..., description="Dispense force gauge data")
    cycle_time: Dict[str, Any] = Field(..., description="Cycle time gauge data")
    max_ram_load: Dict[str, Any] = Field(..., description="Maximum RAM load data")
    
    # Location information
    asset_location: str = Field(..., description="Physical location of the machine")
    
    # Inventory data
    inventory: List[IceCreamInventoryItem] = Field(default_factory=list, description="Ice cream flavor inventory")

# ------ Location Performance Model ------

class LocationPerformance(BaseModel):
    """Performance metrics for a specific location"""
    location_name: str = Field(..., description="Location name (e.g., 'Sheetz North')")
    avg_service_cost: str = Field(..., description="Average monthly service cost")
    asset_count: int = Field(..., description="Number of ice cream machines at this location")
    online_count: int = Field(..., description="Number of online machines at this location")
    total_sales: float = Field(..., description="Total sales amount for this location")

# ------ Service Ticket Model ------

class ServiceTicket(BaseModel):
    """Service ticket for ice cream machine maintenance"""
    ticket_id: str = Field(..., description="Unique ticket identifier")
    vendor_id: str = Field(..., description="Vendor identifier")
    asset_id: str = Field(..., description="Ice cream machine identifier")
    issue_type: str = Field(..., description="Type of issue")
    status: str = Field(..., description="Ticket status (Open, In Progress, Closed)")
    date_created: str = Field(..., description="Date ticket was created")
    date_resolved: Optional[str] = Field(None, description="Date ticket was resolved")

# ------ Operations Summary Model ------

class OperationsSummary(BaseModel):
    """Fleet-wide operations summary for Polar Delight ice cream machines"""
    total_assets: int = Field(..., description="Total number of ice cream machines")
    total_assets_online: int = Field(..., description="Number of online ice cream machines")
    service_tickets_open: int = Field(..., description="Number of open service tickets")
    service_tickets_closed: int = Field(..., description="Number of closed service tickets")
    average_uptime: float = Field(..., description="Average uptime percentage")
    total_sales_today: float = Field(..., description="Total sales amount for today")
    average_sales_per_asset: float = Field(..., description="Average sales per ice cream machine")
    
    # Performance by location
    locations: List[LocationPerformance] = Field(default_factory=list, description="Performance metrics by location")
    
    # Open service tickets
    open_tickets: List[ServiceTicket] = Field(default_factory=list, description="List of open service tickets")
    
    # Sales data by ice cream flavor
    sales_by_flavor: Dict[str, float] = Field(default_factory=dict, description="Sales amount by ice cream flavor")
    
    # Summary statistics
    stats: Dict[str, Any] = Field(default_factory=dict, description="Additional summary statistics")
    
    class Config:
        """Pydantic config"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
# ------ Azure Digital Twins Integration Model ------

class ADTQueryRequest(BaseModel):
    """Azure Digital Twins query request model for compatibility with Angular frontend"""
    fromDate: Optional[str] = Field("", description="Start date for query filters")
    toDate: Optional[str] = Field("", description="End date for query filters")
    adtUrl: str = Field(..., description="Azure Digital Twins API URL")
    accessToken: str = Field(..., description="Azure Digital Twins access token")
    adtQuery: str = Field(..., description="Azure Digital Twins query string")


class OperationalStatus(BaseModel):
    """Real-time operational status data for a Polar Delight ice cream machine"""
    machine_id: str = Field(..., description="Ice cream machine ID")
    machine_status: str = Field(..., description="Machine status (Online, Offline)")
    last_updated: datetime = Field(..., description="Timestamp of the last status update")
    
    # Status indicators
    cap_position: Dict[str, Any] = Field(..., description="Cap position data")
    ram_position: Dict[str, Any] = Field(..., description="Ram position data")
    cup_detect: str = Field(..., description="Cup detection status (Yes, No)")
    pod_bin_door: str = Field(..., description="Pod bin door status (Open, Closed)")
    customer_door: str = Field(..., description="Customer door status (Open, Closed)")
    pod_code: str = Field(..., description="POD code identifier")
    cycle_status: Dict[str, Any] = Field(..., description="Cycle status data")
    
    # Gauge metrics
    dispense_pressure: Dict[str, Any] = Field(..., description="Dispense pressure data")
    freezer_temperature: Dict[str, Any] = Field(..., description="Freezer temperature data")
    max_ram_load: Dict[str, Any] = Field(..., description="Maximum RAM load data")
    cycle_time: Dict[str, Any] = Field(..., description="Cycle time data")
    
    # Inventory tracking
    ice_cream_inventory: List[IceCreamInventoryItem] = Field(default_factory=list, description="Ice cream flavor inventory")
    
    # Location information
    location: str = Field(..., description="Asset location")
