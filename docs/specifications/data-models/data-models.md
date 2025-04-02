# IoTSphere Data Models

## Overview

This document describes the data models used in the IoTSphere application. These models define the structure of data throughout the system, from database storage to API responses and frontend representation.

## Backend Models

### Core Models

#### VendingMachine

The central model representing a Polar Delight vending machine.

```python
class VendingMachine(Base):
    __tablename__ = "vending_machine"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    model = Column(String(50), nullable=False)
    location = Column(String(200))
    installation_date = Column(Date)
    last_maintenance_date = Column(DateTime)
    firmware_version = Column(String(20))
    status = Column(Enum("ONLINE", "OFFLINE", "MAINTENANCE", name="machine_status"))

    # Relationships
    readings = relationship("MachineReading", back_populates="machine")
    alerts = relationship("Alert", back_populates="machine")
    inventory = relationship("Inventory", back_populates="machine")
```

#### MachineReading

Records sensor readings and operational data from a machine.

```python
class MachineReading(Base):
    __tablename__ = "machine_reading"

    id = Column(String(36), primary_key=True)
    machine_id = Column(String(36), ForeignKey("vending_machine.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    reading_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20))

    # Relationships
    machine = relationship("VendingMachine", back_populates="readings")
```

#### Inventory

Tracks product inventory in a vending machine.

```python
class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(String(36), primary_key=True)
    machine_id = Column(String(36), ForeignKey("vending_machine.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("product.id"), nullable=False)
    current_level = Column(Integer, nullable=False)
    max_capacity = Column(Integer, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    machine = relationship("VendingMachine", back_populates="inventory")
    product = relationship("Product")
```

#### Product

Defines available products.

```python
class Product(Base):
    __tablename__ = "product"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    product_type = Column(String(50))
    unit_price = Column(Numeric(10, 2))
    active = Column(Boolean, default=True)
```

#### User

Represents a user of the system.

```python
class User(Base):
    __tablename__ = "user"

    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    role = Column(Enum("ADMIN", "OPERATOR", "VIEWER", name="user_role"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
```

#### Alert

Records system alerts and notifications.

```python
class Alert(Base):
    __tablename__ = "alert"

    id = Column(String(36), primary_key=True)
    machine_id = Column(String(36), ForeignKey("vending_machine.id"))
    alert_type = Column(String(50), nullable=False)
    severity = Column(Enum("LOW", "MEDIUM", "HIGH", "CRITICAL", name="alert_severity"), nullable=False)
    status = Column(Enum("ACTIVE", "ACKNOWLEDGED", "RESOLVED", name="alert_status"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String(36), ForeignKey("user.id"))
    resolved_at = Column(DateTime)
    resolved_by = Column(String(36), ForeignKey("user.id"))
    resolution_notes = Column(Text)

    # Relationships
    machine = relationship("VendingMachine", back_populates="alerts")
```

### Operations Models

#### VendingMachineOperationsData

Contains real-time operational data for the Operations Dashboard.

```python
class VendingMachineOperationsData:
    def __init__(self, machine_id, machine_status, pod_code=None, cup_detect=None,
                 customer_door=None, dispense_pressure=None, freezer_temperature=None,
                 cycle_time=None, asset_health=None, ice_cream_inventory=None):
        self.machine_id = machine_id
        self.machine_status = machine_status
        self.pod_code = pod_code
        self.cup_detect = cup_detect
        self.customer_door = customer_door
        self.dispense_pressure = dispense_pressure
        self.freezer_temperature = freezer_temperature
        self.cycle_time = cycle_time
        self.asset_health = asset_health
        self.ice_cream_inventory = ice_cream_inventory

    def to_dict(self):
        return {
            "machine_id": self.machine_id,
            "machine_status": self.machine_status,
            "pod_code": self.pod_code,
            "cup_detect": self.cup_detect,
            "customer_door": self.customer_door,
            "dispense_pressure": self.dispense_pressure.to_dict() if self.dispense_pressure else None,
            "freezer_temperature": self.freezer_temperature.to_dict() if self.freezer_temperature else None,
            "cycle_time": self.cycle_time.to_dict() if self.cycle_time else None,
            "asset_health": self.asset_health.to_dict() if self.asset_health else None,
            "ice_cream_inventory": [item.to_dict() for item in self.ice_cream_inventory] if self.ice_cream_inventory else []
        }
```

#### GaugeData Models

Base class for gauge-type metrics.

```python
class GaugeData:
    def __init__(self, value, min_value, max_value):
        self.value = value
        self.min = min_value
        self.max = max_value

    def to_dict(self):
        return {
            "value": self.value,
            "min": self.min,
            "max": self.max
        }
```

Specific gauge data models:

```python
class DispensePressureData(GaugeData):
    def to_dict(self):
        return {
            "dispensePressure": self.value,
            "min": self.min,
            "max": self.max
        }

class FreezerTemperatureData(GaugeData):
    def to_dict(self):
        return {
            "freezerTemperature": self.value,
            "min": self.min,
            "max": self.max
        }

class CycleTimeData(GaugeData):
    def to_dict(self):
        return {
            "cycleTime": self.value,
            "min": self.min,
            "max": self.max
        }

class AssetHealthData(GaugeData):
    def to_dict(self):
        return {
            "assetHealth": self.value,
            "min": self.min,
            "max": self.max
        }
```

#### InventoryItem

Represents a single inventory item with level information.

```python
class InventoryItem:
    def __init__(self, name, level, max_capacity=None):
        self.name = name
        self.level = level
        self.max_capacity = max_capacity

    def to_dict(self):
        result = {
            "name": self.name,
            "level": self.level
        }
        if self.max_capacity is not None:
            result["max_capacity"] = self.max_capacity
        return result
```

## API Data Models

The following examples show the JSON structure for API responses:

### Machine List Response

```json
{
  "machines": [
    {
      "id": "machine-001",
      "name": "Ice Cream Machine 1",
      "location": "Main Floor",
      "status": "ONLINE"
    },
    {
      "id": "machine-002",
      "name": "Ice Cream Machine 2",
      "location": "Food Court",
      "status": "OFFLINE"
    }
  ]
}
```

### Real-time Operations Data Response

```json
{
  "machine_id": "machine-001",
  "machine_status": "Online",
  "pod_code": "12345",
  "cup_detect": "Yes",
  "customer_door": "Closed",
  "dispense_pressure": {
    "dispensePressure": "35.5",
    "min": "10",
    "max": "50"
  },
  "freezer_temperature": {
    "freezerTemperature": "-15.2",
    "min": "-20",
    "max": "0"
  },
  "cycle_time": {
    "cycleTime": "18.3",
    "min": "15",
    "max": "25"
  },
  "ice_cream_inventory": [
    {
      "name": "Vanilla",
      "level": 75,
      "max_capacity": 100
    },
    {
      "name": "Chocolate",
      "level": 60,
      "max_capacity": 100
    },
    {
      "name": "Strawberry",
      "level": 30,
      "max_capacity": 100
    },
    {
      "name": "Mint",
      "level": 85,
      "max_capacity": 100
    }
  ]
}
```

## Frontend Data Structures

### JavaScript Object Models

The frontend uses JavaScript objects to represent data received from the API and manage UI state:

#### Machine Object

```javascript
{
  id: "machine-001",
  name: "Ice Cream Machine 1",
  location: "Main Floor",
  status: "ONLINE",
  displayName: "Ice Cream Machine 1 (Main Floor)"
}
```

#### Operations Data Object

```javascript
{
  machine_id: "machine-001",
  machine_status: "Online",
  pod_code: "12345",
  cup_detect: "Yes",
  customer_door: "Closed",
  dispense_pressure: {
    dispensePressure: "35.5",
    min: "10",
    max: "50"
  },
  freezer_temperature: {
    freezerTemperature: "-15.2",
    min: "-20",
    max: "0"
  },
  cycle_time: {
    cycleTime: "18.3",
    min: "15",
    max: "25"
  },
  ice_cream_inventory: [
    {
      name: "Vanilla",
      level: 75,
      max_capacity: 100
    },
    {
      name: "Chocolate",
      level: 60,
      max_capacity: 100
    },
    {
      name: "Strawberry",
      level: 30,
      max_capacity: 100
    },
    {
      name: "Mint",
      level: 85,
      max_capacity: 100
    }
  ]
}
```

## Data Flow

### Operations Dashboard Data Flow

1. **Machine List Request**:
   - Frontend calls `fetchMachineList()`
   - API endpoint: `GET /api/vending-machines`
   - Response contains list of available machines

2. **Machine Selection**:
   - User selects a machine from dropdown
   - Frontend stores selection in `window.machineId`
   - Frontend calls `loadOperationsData(machineId)`

3. **Operations Data Request**:
   - Frontend calls `fetchVendingMachineOperations(machineId)`
   - API endpoint: `GET /api/vending-machines/{machine_id}/operations-realtime`
   - Backend processes real-time data from `VendingMachineRealtimeOperationsService`
   - Response contains operational metrics and status

4. **UI Updates**:
   - Frontend calls `updateOperationsDashboard(data)`
   - Status cards are updated with current values
   - Gauge charts are updated with current metrics
   - Inventory levels are displayed with visual indicators

### Data Transformation

The following transformations occur in the data flow:

1. **Backend to API**:
   - Python model objects are converted to dictionaries
   - Dictionaries serialized to JSON
   - Consistent property naming enforced

2. **API to Frontend**:
   - JSON parsed to JavaScript objects
   - Property access abstracted with fallbacks for different naming conventions
   - Data validation ensures missing properties don't cause UI errors

3. **Frontend to UI**:
   - JavaScript objects mapped to DOM elements
   - Numerical values formatted for display
   - Status indicators assigned appropriate CSS classes

## Data Validation

### Backend Validation

- SQLAlchemy model constraints enforce data types and relationships
- Service-layer validation ensures complete and consistent data
- API layer validates request parameters and formats

### Frontend Validation

- Input data checked for required properties
- Fallbacks provided for missing or malformed data
- Data transformations handle inconsistent property names
- UI gracefully handles empty data sets

## Schema Evolution

IoTSphere's data models evolve following these principles:

1. **Backward Compatibility**: New fields are optional
2. **Versioned APIs**: Breaking changes create new API versions
3. **Migration Strategy**: Data migrations preserve historical data
4. **Progressive Enhancement**: UI adapts to available data properties

## Data Security

1. **Access Control**: Models include ownership and access rules
2. **Data Encryption**: Sensitive data encrypted at rest
3. **Input Validation**: Prevents injection attacks
4. **Auditing**: Changes to critical data are logged

## Conclusion

IoTSphere's data models provide a structured, consistent foundation for the application. The separation between backend models, API representations, and frontend data structures allows each layer to evolve independently while maintaining compatibility through well-defined interfaces.
