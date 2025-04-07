# IoTSphere Domain Entities and Value Objects

This document defines the key entities and value objects within the IoTSphere domain model, following Domain-Driven Design principles.

## Core Entities

### Device
- **Definition:** A connected physical asset that can be monitored and controlled by the platform.
- **Bounded Context:** Device Management
- **Identifier:** Globally unique identifier (UUID)
- **Lifecycle:**
  - Created during device registration
  - Updated when configuration changes
  - Archived when decommissioned
- **Attributes:**
  - `id` (Identifier)
  - `name` (String)
  - `type` (DeviceType)
  - `manufacturer` (String)
  - `model` (String)
  - `firmwareVersion` (String)
  - `capabilities` (Set of Capability)
  - `status` (DeviceStatus)
  - `location` (Location)
  - `metadata` (JSON)
- **Behavior:**
  - Register in the system
  - Update configuration
  - Add/remove capabilities
  - Update firmware
  - Change operational status

### DeviceType
- **Definition:** Classification of devices sharing common characteristics and capabilities.
- **Bounded Context:** Device Management
- **Identifier:** Type code (String)
- **Subtypes:**
  - WaterHeater
  - VendingMachine
  - Robot
  - Vehicle
  - Generic
- **Attributes:**
  - `code` (String)
  - `name` (String)
  - `description` (String)
  - `defaultCapabilities` (Set of Capability)
  - `requiredAttributes` (Set of String)
- **Behavior:**
  - Define common capabilities
  - Provide type-specific validation rules
  - Supply default configurations

### Capability
- **Definition:** A functional ability that a device possesses.
- **Bounded Context:** Device Management
- **Identifier:** Capability code (String)
- **Examples:**
  - Temperature Control
  - Inventory Management
  - Mobility
  - Energy Monitoring
- **Attributes:**
  - `code` (String)
  - `name` (String)
  - `version` (String)
  - `commands` (Set of CommandDefinition)
  - `telemetryTypes` (Set of TelemetryTypeDefinition)
- **Behavior:**
  - Define supported commands
  - Define expected telemetry
  - Validate capability requirements
  - Check version compatibility

### DeviceState
- **Definition:** The current operational state of a device.
- **Bounded Context:** Device Operation
- **Identifier:** Device ID + timestamp
- **Attributes:**
  - `deviceId` (String)
  - `timestamp` (DateTime)
  - `connectionStatus` (ConnectionStatus)
  - `operationalStatus` (OperationalStatus)
  - `mode` (OperationalMode)
  - `attributes` (Map of key-value pairs)
  - `lastTelemetry` (Map of key-value pairs)
  - `lastUpdatedBy` (String)
- **Behavior:**
  - Reflect current device status
  - Track historical state changes
  - Validate state transitions
  - Notify on significant changes

### MaintenanceRecord
- **Definition:** A record of maintenance performed on a device.
- **Bounded Context:** Maintenance Management
- **Identifier:** Record ID (UUID)
- **Attributes:**
  - `id` (Identifier)
  - `deviceId` (String)
  - `performedAt` (DateTime)
  - `completedAt` (DateTime)
  - `technician` (ServiceTechnician)
  - `type` (MaintenanceType)
  - `actions` (List of MaintenanceAction)
  - `replacedComponents` (List of ReplacedComponent)
  - `notes` (String)
  - `followUpNeeded` (Boolean)
- **Behavior:**
  - Document maintenance activities
  - Track component replacements
  - Update device health metrics
  - Schedule follow-up maintenance

### HealthAssessment
- **Definition:** An evaluation of a device's operational health and predicted maintenance needs.
- **Bounded Context:** Maintenance Management
- **Identifier:** Device ID + assessment date
- **Attributes:**
  - `deviceId` (String)
  - `assessmentDate` (DateTime)
  - `overallScore` (Integer, 0-100)
  - `componentScores` (Map of component to score)
  - `estimatedLifespan` (Duration)
  - `predictedIssues` (List of PredictedIssue)
  - `maintenanceRecommendations` (List of MaintenanceRecommendation)
  - `confidenceLevel` (Float, 0-1)
- **Behavior:**
  - Assess device health
  - Predict maintenance needs
  - Track health trends over time
  - Generate alerts for degradation

### EnergyConsumption
- **Definition:** Record of energy used by a device over a specific time period.
- **Bounded Context:** Energy Management
- **Identifier:** Device ID + time period
- **Attributes:**
  - `deviceId` (String)
  - `startTime` (DateTime)
  - `endTime` (DateTime)
  - `energyConsumed` (Measurement<Energy>)
  - `peakConsumption` (Measurement<Power>)
  - `averageConsumption` (Measurement<Power>)
  - `cost` (Money)
  - `efficiencyRating` (Float, 0-1)
- **Behavior:**
  - Calculate consumption metrics
  - Compare to baseline consumption
  - Identify optimization opportunities
  - Track cost implications

### User
- **Definition:** Person who interacts with the IoTSphere platform.
- **Bounded Context:** User Management (cross-cutting)
- **Identifier:** User ID (UUID)
- **Attributes:**
  - `id` (Identifier)
  - `username` (String)
  - `email` (Email)
  - `roles` (Set of Role)
  - `permissions` (Set of Permission)
  - `preferences` (UserPreferences)
  - `lastLogin` (DateTime)
- **Behavior:**
  - Authenticate to the system
  - Perform authorized actions
  - Receive notifications
  - Configure preferences

## Value Objects

### Location
- **Definition:** Physical location information.
- **Attributes:**
  - `latitude` (Float)
  - `longitude` (Float)
  - `altitude` (Float, optional)
  - `address` (Address, optional)
  - `area` (String, optional)
  - `building` (String, optional)
  - `floor` (String, optional)
  - `room` (String, optional)

### Address
- **Definition:** Postal address information.
- **Attributes:**
  - `street` (String)
  - `city` (String)
  - `state` (String)
  - `postalCode` (String)
  - `country` (String)

### Measurement<T>
- **Definition:** A quantity with a unit of measure.
- **Attributes:**
  - `value` (Float)
  - `unit` (Unit<T>)
  - `precision` (Float, optional)

### Money
- **Definition:** Monetary value with currency.
- **Attributes:**
  - `amount` (Decimal)
  - `currency` (CurrencyCode)

### MaintenanceAction
- **Definition:** A specific action taken during maintenance.
- **Attributes:**
  - `type` (ActionType)
  - `description` (String)
  - `result` (String)
  - `duration` (Duration)

### ReplacedComponent
- **Definition:** Information about a component replaced during maintenance.
- **Attributes:**
  - `componentType` (String)
  - `oldPartNumber` (String)
  - `newPartNumber` (String)
  - `reason` (String)
  - `manufacturer` (String)

### PredictedIssue
- **Definition:** A potential future problem identified through predictive analytics.
- **Attributes:**
  - `issueType` (String)
  - `probability` (Float, 0-1)
  - `expectedTimeframe` (DateRange)
  - `affectedComponent` (String)
  - `severity` (IssueSeverity)
  - `recommendedAction` (String)

### MaintenanceRecommendation
- **Definition:** Suggested maintenance action based on device health.
- **Attributes:**
  - `actionType` (MaintenanceType)
  - `priority` (Priority)
  - `recommendedTimeframe` (DateRange)
  - `estimatedDuration` (Duration)
  - `requiredParts` (List of String)
  - `estimatedCost` (Money, optional)

### CommandDefinition
- **Definition:** Definition of a command that can be sent to a device.
- **Attributes:**
  - `name` (String)
  - `description` (String)
  - `parameters` (List of ParameterDefinition)
  - `requiredCapabilities` (Set of String)
  - `responseSchema` (Schema)

### TelemetryTypeDefinition
- **Definition:** Definition of a type of telemetry that can be received from a device.
- **Attributes:**
  - `name` (String)
  - `description` (String)
  - `dataType` (DataType)
  - `unit` (String, optional)
  - `minValue` (Float, optional)
  - `maxValue` (Float, optional)
  - `precision` (Float, optional)
  - `frequency` (Frequency, optional)

## Enumerations

### DeviceStatus
- ONLINE
- OFFLINE
- MAINTENANCE
- FAULT
- DECOMMISSIONED

### ConnectionStatus
- CONNECTED
- DISCONNECTED
- INTERMITTENT
- UNKNOWN

### OperationalStatus
- NORMAL
- WARNING
- ERROR
- STANDBY
- STARTUP
- SHUTDOWN

### OperationalMode
- STANDARD
- ECO
- HIGH_PERFORMANCE
- VACATION
- CUSTOM

### MaintenanceType
- PREVENTIVE
- CORRECTIVE
- PREDICTIVE
- INSPECTION
- UPGRADE

### IssueSeverity
- CRITICAL
- HIGH
- MEDIUM
- LOW
- INFO

### Priority
- URGENT
- HIGH
- MEDIUM
- LOW

### DataType
- INTEGER
- FLOAT
- BOOLEAN
- STRING
- ENUM
- OBJECT
- ARRAY
