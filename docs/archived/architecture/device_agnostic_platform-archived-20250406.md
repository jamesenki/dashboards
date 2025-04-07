# IoTSphere Device-Agnostic Platform Architecture

## 1. Executive Summary

This document outlines the target architecture for transforming IoTSphere from a water-heater-focused application into a fully device-agnostic IoT platform capable of supporting diverse device types (water heaters, vending machines, robots, vehicles, etc.) while maximizing code reuse and maintaining a consistent user experience.

## 2. Architecture Principles

- **Modular Design**: Components should be self-contained with clear interfaces
- **Capability-Based Modeling**: Devices defined by capabilities, not just types
- **Progressive Enhancement**: Existing water heater functionality remains uninterrupted
- **Separation of Concerns**: Clear boundaries between device-agnostic and device-specific code
- **Future-Proof Extensibility**: New device types can be added without architectural changes

## 3. Core System Components

### 3.1 Device Registry

The Device Registry manages device identity, status, and capability registration:

```
┌─────────────────────────────────────────┐
│ Core Device Registry                    │
├─────────────────────────────────────────┤
│ - Unique device identification          │
│ - Capability registration               │
│ - Status tracking                       │
│ - Authentication and security           │
│ - Ownership and access control          │
└─────────────────────────────────────────┘
```

### 3.2 Data Model Framework

A hierarchical data model with a base device schema and device-specific extensions:

```
┌─────────────────────────────────────────────────────────┐
│ Core Device Schema                                      │
├─────────────────────────────────────────────────────────┤
│ BaseDevice                                              │
│ {                                                       │
│   id: string,                                           │
│   name: string,                                         │
│   type: string,                                         │
│   manufacturer: string,                                 │
│   model: string,                                        │
│   firmware_version: string,                             │
│   connection_status: string,                            │
│   last_connected: timestamp,                            │
│   location: {lat: number, lng: number},                 │
│   capabilities: string[],                               │
│   metadata: object                                      │
│ }                                                       │
└─────────────────────────────────────────────────────────┘
                ▲
                │
    ┌───────────┼───────────┐
    │           │           │
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ WaterHeater     │ │ VendingMachine  │ │ Robot          │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ - tankSize      │ │ - inventory     │ │ - armCount     │
│ - temperature   │ │ - transactions  │ │ - movementRange│
│ - pressureRating│ │ - cashBalance   │ │ - batteryLevel │
│ - energyMode    │ │ - slotCount     │ │ - sensorArray  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 3.3 Capability Framework

Devices are modeled by their capabilities, allowing feature sharing across device types:

```
┌─────────────────────────────────────────────────────────┐
│ Core Capabilities                                       │
├─────────────────────────────────────────────────────────┤
│ Capability                                              │
│ {                                                       │
│   name: string,                                         │
│   version: string,                                      │
│   requiredAttributes: string[],                         │
│   supportedCommands: string[],                          │
│   supportedEvents: string[]                             │
│ }                                                       │
└─────────────────────────────────────────────────────────┘
                ▲
                │
    ┌───────────┼───────────┐
    │           │           │
┌───────────────┐ ┌──────────────┐ ┌───────────────────┐
│ Temperature   │ │ Inventory    │ │ Mobility         │
│ Control       │ │ Management   │ │ Control          │
├───────────────┤ ├──────────────┤ ├───────────────────┤
│ getTemp()     │ │ getStock()   │ │ getPosition()    │
│ setTemp()     │ │ addItem()    │ │ moveTo()         │
│ tempAlert()   │ │ removeItem() │ │ planPath()       │
└───────────────┘ └──────────────┘ └───────────────────┘
```

### 3.4 Service Architecture

Core services that apply to all devices, with device-specific service extensions:

```
┌───────────────────────────────────────────────────────────────┐
│ Device-Agnostic Core Services                                 │
├───────────────────────────────────────────────────────────────┤
│ - DeviceRegistryService                                       │
│ - CapabilityManagerService                                    │
│ - TelemetryProcessingService                                  │
│ - CommandDispatchService                                      │
│ - EventProcessingService                                      │
│ - NotificationService                                         │
│ - UserManagementService                                       │
└───────────────────────────────────────────────────────────────┘
                ▲
                │
    ┌───────────┼───────────┐
    │           │           │
┌───────────────────┐ ┌──────────────────┐ ┌───────────────────┐
│ WaterHeaterService│ │VendingMachService│ │ RobotService      │
├───────────────────┤ ├──────────────────┤ ├───────────────────┤
│ - tempControl     │ │ - inventory      │ │ - pathPlanning    │
│ - energyMgmt      │ │ - transactions   │ │ - taskOrchestration│
│ - maintenancePred │ │ - alerting       │ │ - sensorFusion    │
└───────────────────┘ └──────────────────┘ └───────────────────┘
```

### 3.5 API Structure

Layered API design with device-agnostic core and device-specific extensions:

```
┌───────────────────────────────────────────────────────────────┐
│ Core REST API Layer                                           │
├───────────────────────────────────────────────────────────────┤
│ - /api/devices                                                │
│ - /api/telemetry                                              │
│ - /api/commands                                               │
│ - /api/events                                                 │
│ - /api/capabilities                                           │
└───────────────────────────────────────────────────────────────┘
                ▲
                │
    ┌───────────┼───────────┐
    │           │           │
┌───────────────────┐ ┌──────────────────┐ ┌───────────────────┐
│ WaterHeater API   │ │VendingMachine API│ │ Robot API         │
├───────────────────┤ ├──────────────────┤ ├───────────────────┤
│ - /water-heaters  │ │ - /vending       │ │ - /robots         │
│ - /temperatures   │ │ - /inventory     │ │ - /navigation     │
│ - /maintenance    │ │ - /transactions  │ │ - /tasks          │
└───────────────────┘ └──────────────────┘ └───────────────────┘
```

### 3.6 Protocol Adapter Framework

Pluggable communication protocols for diverse device connectivity:

```
┌────────────────────────────────────────────────────────┐
│ Protocol Adapter Interface                             │
├────────────────────────────────────────────────────────┤
│ {                                                      │
│   connect(): Promise,                                  │
│   disconnect(): Promise,                               │
│   sendCommand(device, command): Promise,               │
│   subscribeTelemetry(device, callback): Subscription   │
│ }                                                      │
└────────────────────────────────────────────────────────┘
                ▲
                │
    ┌───────────┼───────────┐
    │           │           │
┌─────────────┐ ┌───────────────┐ ┌───────────────┐
│ MQTT        │ │ HTTP/REST     │ │ MODBUS        │
│ Adapter     │ │ Adapter       │ │ Adapter       │
└─────────────┘ └───────────────┘ └───────────────┘
```

### 3.7 UI Framework

Reusable UI components with device-specific extensions:

```
┌─────────────────────────────────────────────────────────┐
│ Core UI Component Library                               │
├─────────────────────────────────────────────────────────┤
│ - DeviceCard                                            │
│ - StatusIndicator                                       │
│ - CommandPanel                                          │
│ - TelemetryDisplay                                      │
│ - AlertNotification                                     │
│ - DeviceRegistry                                        │
│ - TimeSeriesChart                                       │
└─────────────────────────────────────────────────────────┘
                ▲
                │
    ┌───────────┼───────────┐
    │           │           │
┌─────────────┐ ┌───────────────┐ ┌───────────────┐
│ WaterHeater │ │ VendingMachine│ │ Robot         │
│ UI Module   │ │ UI Module     │ │ UI Module     │
└─────────────┘ └───────────────┘ └───────────────┘
```

### 3.8 Database Schema

Relational schema with core tables and device-specific extensions:

```sql
-- Core Tables
CREATE TABLE devices (
  id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  type VARCHAR NOT NULL,
  manufacturer VARCHAR NOT NULL,
  model VARCHAR,
  firmware_version VARCHAR,
  connection_status VARCHAR,
  last_connected TIMESTAMP,
  location JSONB,
  capabilities JSONB,
  metadata JSONB
);

CREATE TABLE telemetry (
  id SERIAL PRIMARY KEY,
  device_id VARCHAR REFERENCES devices(id),
  timestamp TIMESTAMP,
  data JSONB
);

-- Device-Specific Extension Tables
CREATE TABLE water_heater_attributes (
  device_id VARCHAR PRIMARY KEY REFERENCES devices(id),
  tank_size FLOAT,
  temperature FLOAT,
  pressure_rating FLOAT,
  energy_mode VARCHAR,
  additional_data JSONB
);

CREATE TABLE vending_machine_attributes (
  device_id VARCHAR PRIMARY KEY REFERENCES devices(id),
  inventory JSONB,
  cash_balance FLOAT,
  slot_count INT,
  additional_data JSONB
);
```

## 4. Action Plan: Phased Implementation

### Phase 1: Foundation Building (Minimal Impact on Water Heater Dev)
**Goal**: Create the core architecture foundations while allowing parallel water heater development to continue uninterrupted.

**Tasks**:

#### Core Device Models (Weeks 1-2)
- Define BaseDevice interface
- Create capability interfaces
- Implement device registry service
- Unit tests for core models

#### Database Preparation (Weeks 2-3)
- Design core device tables
- Create database migration scripts
- Establish versioning strategy
- Set up data access layer

#### Service Layer Foundation (Weeks 3-4)
- Implement device-agnostic services
- Create protocol abstraction layer
- Set up event processing pipeline
- Develop command dispatch system

#### Core UI Components (Weeks 4-5)
- Design component library architecture
- Implement shared UI components
- Create pluggable dashboard framework
- Develop styleguide and component documentation

### Phase 2: Water Heater Adaptation (Parallel to Ongoing Development)
**Goal**: Gradually migrate water heater functionality to leverage the new architecture while completing remaining water heater features.

**Tasks**:

#### Data Model Transition (Weeks 6-7)
- Create WaterHeater extension of BaseDevice
- Implement adapters to transform existing data
- Verify data integrity and performance
- Set up dual-mode operation during transition

#### API Restructuring (Weeks 7-8)
- Refactor existing water heater API routes
- Add capability-based endpoints
- Ensure backward compatibility
- Performance testing of new structure

#### UI Component Extraction (Weeks 8-9)
- Identify reusable elements in water heater UI
- Refactor to use core component library
- Create water heater specific components
- Ensure consistent styling and behavior

#### Service Layer Integration (Weeks 9-10)
- Connect water heater service to core services
- Implement water heater specific capabilities
- Ensure telemetry flow works in new architecture
- Validate command handling

### Phase 3: Capability Expansion (After Water Heaters Complete)
**Goal**: Enhance the platform with a rich set of capabilities that can be used across device types.

**Tasks**:

#### Temperature Management (Week 11)
- Implement generic temperature capability
- Add heating/cooling controls
- Create temperature monitoring visualization
- Set up temperature alerts and thresholds

#### Inventory Management (Week 12)
- Develop inventory tracking capability
- Create stock level visualization
- Implement inventory alerts
- Add reorder/refill workflow

#### Mobility & Navigation (Week 13)
- Create position tracking capability
- Implement path planning interfaces
- Develop movement visualization
- Add geofencing capability

#### Diagnostics & Maintenance (Week 14)
- Build generic diagnostics framework
- Implement predictive maintenance modeling
- Create maintenance scheduling system
- Develop service history tracking

### Phase 4: New Device Integration (Future Expansion)
**Goal**: Demonstrate the extensibility of the platform by adding new device types.

**Tasks**:

#### Vending Machine Integration (Weeks 15-16)
- Define vending machine data model
- Implement inventory and transaction capabilities
- Create vending machine UI
- Integrate with payment systems

#### Robot Integration (Weeks 17-18)
- Define robot data model
- Implement movement and sensor capabilities
- Create robot control UI
- Add task programming interface

#### Vehicle/Automotive (Weeks 19-20)
- Define vehicle data model
- Implement tracking and diagnostics capabilities
- Create vehicle dashboard
- Add route optimization functionality

### 5. Immediate Next Steps (Next 2 Weeks)
- Complete current water heater fixes and features
- Create draft interfaces for core device model
- Design database migration strategy
- Identify reusable components in current water heater UI
- Document capability requirements for water heaters

### 6. Implementation Notes
- **Parallel Development**: Core architecture development can proceed without disrupting water heater feature completion
- **Incremental Migration**: Water heater components will transition to the new architecture gradually
- **Backward Compatibility**: All existing functionality will be maintained throughout the transition
- **Testing Strategy**: Comprehensive unit and integration tests will validate each component

## 7. Conclusion

This architecture provides a robust foundation for expanding IoTSphere from a water-heater-focused application to a comprehensive IoT platform supporting diverse device types. By implementing a capability-based approach with a clean separation between core functionality and device-specific extensions, we can achieve maximum code reuse while maintaining the flexibility to support unique device features.

The water heater implementation will serve as our reference model and validate the architecture before expanding to additional device types. This phased approach ensures we can continue development on water heater features while laying the groundwork for future expansion.

## 8. Developer Experience

A key strength of this architecture is how it simplifies extending the platform for both new brands of existing device types and entirely new device categories. This section outlines the developer and customer experience for platform extension.

### 8.1 Adding a New Brand of Device (Same Device Type)

When adding a new brand of water heater (or any existing device type), the process would be:

#### For Developers:

1. **Create a Manufacturer Adapter**:
   ```python
   class NewBrandAdapter(ManufacturerAdapter):
       def transform_telemetry(self, raw_data):
           # Transform manufacturer-specific telemetry format to canonical model
           return {
               "temperature": raw_data.get("temp_celsius") or raw_data.get("water_temp"),
               "pressure": raw_data.get("water_pressure_kpa") or raw_data.get("pressure_reading"),
               # Map other fields based on manufacturer's data format
           }

       def transform_command(self, canonical_command):
           # Transform canonical commands to manufacturer-specific format
           if canonical_command["type"] == "set_temperature":
               return {"cmd": "TEMP_SET", "value": canonical_command["value"]}
   ```

2. **Register Protocol Handlers** (if using a different protocol):
   ```python
   # If the new brand uses a proprietary protocol
   newbrand_protocol = NewBrandProtocolAdapter()
   protocol_registry.register("newbrand", newbrand_protocol)
   ```

3. **Add Brand-Specific UI Theming** (optional):
   ```javascript
   // Define brand-specific styling or behavior extensions
   const newBrandTheme = {
     primaryColor: '#00457C',
     logoUrl: '/assets/brands/newbrand-logo.svg',
     // Brand-specific customizations
   };

   brandRegistry.register('NewBrand', newBrandTheme);
   ```

#### For Customers/Admins:

1. **Register the New Brand** in the admin dashboard
2. **Define Mapping Rules** for the brand's data format (if UI-based configuration is available)
3. **Upload Brand Assets** (logos, documentation links, support contact info)
4. **Configure Authentication** methods for the brand's devices

The system handles all the heavy lifting through the adapter pattern, capability framework, and transformation layer.

### 8.2 Adding a New Type of IoT Device

For entirely new device types (e.g., adding vending machines when only water heaters existed), the process involves:

#### For Developers:

1. **Create Device Type Extension**:
   ```python
   # Define the new device type model extending the base device
   class VendingMachine(BaseDevice):
       inventory = JSONField()
       cash_balance = FloatField()
       slot_count = IntegerField()

       class Meta:
           capabilities = ['inventory', 'payment', 'temperature', 'security']
   ```

2. **Implement Required Capabilities**:
   ```python
   @register_capability('inventory')
   class InventoryCapability(BaseCapability):
       def get_stock(self, device_id):
           # Implementation

       def update_stock(self, device_id, item_id, quantity):
           # Implementation

       def alert_low_stock(self, threshold=5):
           # Implementation
   ```

3. **Create Device-Specific API Extensions**:
   ```python
   @router.register('/vending-machines/{device_id}/inventory')
   async def get_inventory(device_id: str):
       # Implementation

   @router.register('/vending-machines/{device_id}/transactions', methods=['POST'])
   async def record_transaction(device_id: str, data: dict):
       # Implementation
   ```

4. **Develop UI Components**:
   ```javascript
   // Create specialized UI components for the device type
   class VendingMachineInventory extends CoreDevicePanel {
     renderItems() {
       // Render inventory slots
     }

     handlePurchase(itemId) {
       // Handle purchase action
     }
   }

   // Register the component
   componentRegistry.register('vending-machine', 'inventory', VendingMachineInventory);
   ```

5. **Create Database Extensions**:
   ```sql
   -- Add device-specific tables
   CREATE TABLE vending_machine_attributes (
     device_id VARCHAR PRIMARY KEY REFERENCES devices(id),
     inventory JSONB,
     cash_balance FLOAT,
     slot_count INT,
     additional_data JSONB
   );

   CREATE TABLE vending_transactions (
     id SERIAL PRIMARY KEY,
     device_id VARCHAR REFERENCES devices(id),
     item_id VARCHAR,
     price FLOAT,
     timestamp TIMESTAMP,
     status VARCHAR
   );
   ```

#### For Customers/Admins:

1. **Enable the New Device Type** in the admin dashboard
2. **Configure Device Type Settings** (default values, thresholds, etc.)
3. **Assign User Permissions** for the new device type
4. **Set Up Dashboards** for monitoring the new devices
5. **Create Notification Rules** specific to the device type

### 8.3 Key Benefits of the Architecture

1. **Reuse of Core Components**: The device-agnostic core handles authentication, telemetry processing, command dispatching, and user management for all device types.

2. **Capability Sharing**: Devices that share capabilities (e.g., both water heaters and vending machines have temperature sensors) can reuse capability implementations.

3. **Consistent API Patterns**: All device types follow the same API design patterns, making integration straightforward.

4. **Unified UI Framework**: New device types plug into the existing dashboard structure with consistent styling and behavior.

5. **Extensible Without Code Changes**: The registry and adapter patterns allow new devices to be added without modifying core code.
