# IoTSphere Domain Aggregates

This document defines the key aggregates within the IoTSphere domain. Each aggregate represents a cluster of domain entities and value objects that can be treated as a single unit for data changes.

## Core Aggregates

### DeviceAggregate
- **Root Entity:** Device
- **Bounded Context:** Device Management
- **Invariants:**
  - Device must have a unique identifier
  - Device must have at least one capability
  - Device type must match capabilities
  - Firmware version must be compatible with device type
- **Contained Entities/Value Objects:**
  - Device (root)
  - DeviceConfiguration
  - Capability (references)
  - Location (value object)
  - DeviceMetadata (value object)
- **Commands:**
  - RegisterDevice
  - UpdateDeviceConfiguration
  - AddDeviceCapability
  - RemoveDeviceCapability
  - UpdateDeviceLocation
  - UpdateFirmware
  - DecommissionDevice
- **Events:**
  - DeviceRegistered
  - DeviceConfigurationUpdated
  - DeviceCapabilityAdded
  - DeviceCapabilityRemoved
  - DeviceLocationUpdated
  - DeviceFirmwareUpdated
  - DeviceDecommissioned
- **Repository:** DeviceRepository
- **Factory:** DeviceFactory

### DeviceStateAggregate
- **Root Entity:** DeviceState
- **Bounded Context:** Device Operation
- **Invariants:**
  - State must be associated with a registered device
  - State transitions must follow valid paths
  - Telemetry values must be within valid ranges for device type
  - Operational mode must be supported by device capabilities
- **Contained Entities/Value Objects:**
  - DeviceState (root)
  - TelemetryReading (collection)
  - Alert (collection)
  - OperationalMetrics (value object)
  - StateTransition (value object)
- **Commands:**
  - UpdateDeviceState
  - RecordTelemetry
  - ChangeOperationalMode
  - ReportConnectionStatus
  - CreateAlert
  - ClearAlert
- **Events:**
  - DeviceStateUpdated
  - TelemetryRecorded
  - OperationalModeChanged
  - ConnectionStatusChanged
  - AlertCreated
  - AlertCleared
- **Repository:** DeviceStateRepository
- **Factory:** DeviceStateFactory

### MaintenanceRecordAggregate
- **Root Entity:** MaintenanceRecord
- **Bounded Context:** Maintenance Management
- **Invariants:**
  - Maintenance record must be associated with a registered device
  - Completed maintenance must have a technician assigned
  - Replaced components must be compatible with device type
- **Contained Entities/Value Objects:**
  - MaintenanceRecord (root)
  - MaintenanceAction (collection)
  - ReplacedComponent (collection)
  - MaintenanceOutcome (value object)
  - MaintenanceCost (value object)
- **Commands:**
  - CreateMaintenanceRecord
  - AssignTechnician
  - RecordMaintenanceAction
  - AddReplacedComponent
  - CompleteMaintenanceRecord
  - ScheduleFollowUpMaintenance
- **Events:**
  - MaintenanceRecordCreated
  - TechnicianAssigned
  - MaintenanceActionRecorded
  - ComponentReplaced
  - MaintenanceCompleted
  - FollowUpMaintenanceScheduled
- **Repository:** MaintenanceRecordRepository
- **Factory:** MaintenanceRecordFactory

### HealthAssessmentAggregate
- **Root Entity:** HealthAssessment
- **Bounded Context:** Maintenance Management
- **Invariants:**
  - Health assessment must be associated with a registered device
  - Overall health score must be calculated from component scores
  - Predictions must include confidence levels
- **Contained Entities/Value Objects:**
  - HealthAssessment (root)
  - ComponentHealth (collection)
  - PredictedIssue (collection)
  - MaintenanceRecommendation (collection)
  - HealthTrend (value object)
- **Commands:**
  - CreateHealthAssessment
  - UpdateComponentHealth
  - AddPredictedIssue
  - AddMaintenanceRecommendation
  - FinalizeHealthAssessment
- **Events:**
  - HealthAssessmentCreated
  - ComponentHealthUpdated
  - PredictedIssueAdded
  - MaintenanceRecommendationAdded
  - HealthAssessmentFinalized
  - CriticalHealthIssueDetected
- **Repository:** HealthAssessmentRepository
- **Factory:** HealthAssessmentFactory

### EnergyConsumptionAggregate
- **Root Entity:** EnergyConsumptionRecord
- **Bounded Context:** Energy Management
- **Invariants:**
  - Consumption record must be associated with a registered device
  - Consumption period must have valid start and end times
  - Energy values must be non-negative
  - Efficiency rating must be within defined range (0-1)
- **Contained Entities/Value Objects:**
  - EnergyConsumptionRecord (root)
  - ConsumptionInterval (collection)
  - EfficiencyMetrics (value object)
  - EnergyCost (value object)
  - ConsumptionComparison (value object)
- **Commands:**
  - RecordEnergyConsumption
  - CalculateEfficiency
  - UpdateEnergyCost
  - FinalizeConsumptionRecord
- **Events:**
  - EnergyConsumptionRecorded
  - EfficiencyCalculated
  - EnergyCostUpdated
  - AbnormalConsumptionDetected
  - ConsumptionRecordFinalized
- **Repository:** EnergyConsumptionRepository
- **Factory:** EnergyConsumptionFactory

### WaterHeaterAggregate
- **Root Entity:** WaterHeater (extends Device)
- **Bounded Context:** Device Management (with specialization for water heaters)
- **Invariants:**
  - Water heater must have temperature control capability
  - Temperature settings must be within safe operating range
  - Water heater must have a defined tank capacity
  - Heating elements must have compatible power ratings
- **Contained Entities/Value Objects:**
  - WaterHeater (root)
  - HeatingElement (collection)
  - TankSpecification (value object)
  - TemperatureSettings (value object)
  - WaterHeaterConfiguration (value object)
- **Commands:**
  - RegisterWaterHeater
  - UpdateTemperatureSettings
  - RecordHeatingElementReplacement
  - ConfigureOperationalMode
  - RecordTankMaintenance
- **Events:**
  - WaterHeaterRegistered
  - TemperatureSettingsUpdated
  - HeatingElementReplaced
  - OperationalModeConfigured
  - TankMaintenanceRecorded
  - AbnormalTemperatureDetected
- **Repository:** WaterHeaterRepository
- **Factory:** WaterHeaterFactory

## Aggregate Relationships

### Relationship Map

The following describes the key relationships between our domain aggregates:

1. **DeviceAggregate ⟷ DeviceStateAggregate**
   - **Relationship Type:** One-to-Many
   - **Description:** A single device can have many state records over time
   - **Consistency Boundary:** Device identity and configuration are maintained in DeviceAggregate, while operational state is tracked in DeviceStateAggregate

2. **DeviceAggregate ⟷ MaintenanceRecordAggregate**
   - **Relationship Type:** One-to-Many
   - **Description:** A single device can have many maintenance records
   - **Consistency Boundary:** MaintenanceRecordAggregate references DeviceAggregate by ID

3. **DeviceAggregate ⟷ HealthAssessmentAggregate**
   - **Relationship Type:** One-to-Many
   - **Description:** A single device can have many health assessments over time
   - **Consistency Boundary:** HealthAssessmentAggregate references DeviceAggregate by ID

4. **DeviceAggregate ⟷ EnergyConsumptionAggregate**
   - **Relationship Type:** One-to-Many
   - **Description:** A single device can have many energy consumption records
   - **Consistency Boundary:** EnergyConsumptionAggregate references DeviceAggregate by ID

5. **DeviceAggregate ⟷ WaterHeaterAggregate**
   - **Relationship Type:** Inheritance/Specialization
   - **Description:** WaterHeaterAggregate is a specialized type of DeviceAggregate
   - **Consistency Boundary:** WaterHeaterAggregate extends DeviceAggregate with additional water heater-specific attributes and behaviors

6. **MaintenanceRecordAggregate ⟷ HealthAssessmentAggregate**
   - **Relationship Type:** Many-to-Many (through Device)
   - **Description:** Maintenance records affect health assessments; health assessments drive maintenance
   - **Consistency Boundary:** Both reference the same device by ID; events communicate changes
