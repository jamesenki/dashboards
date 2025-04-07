# IoTSphere Domain Events

This document defines the key domain events within the IoTSphere platform. Domain events represent significant occurrences within the system that other components may need to react to.

## Core Domain Events

### Device Management Context Events

#### DeviceRegisteredEvent
- **Description:** Triggered when a new device is successfully registered in the system
- **Source Aggregate:** DeviceAggregate
- **Payload:**
  - `deviceId` (String)
  - `deviceType` (String)
  - `manufacturer` (String)
  - `capabilities` (List of String)
  - `registrationTime` (DateTime)
  - `registeredBy` (String)

#### DeviceConfigurationUpdatedEvent
- **Description:** Triggered when a device's configuration is changed
- **Source Aggregate:** DeviceAggregate
- **Payload:**
  - `deviceId` (String)
  - `updatedProperties` (Map of key-value pairs)
  - `previousValues` (Map of key-value pairs)
  - `updateTime` (DateTime)
  - `updatedBy` (String)

#### DeviceCapabilityAddedEvent
- **Description:** Triggered when a capability is added to a device
- **Source Aggregate:** DeviceAggregate
- **Payload:**
  - `deviceId` (String)
  - `capabilityCode` (String)
  - `capabilityVersion` (String)
  - `addedTime` (DateTime)
  - `addedBy` (String)

#### DeviceCapabilityRemovedEvent
- **Description:** Triggered when a capability is removed from a device
- **Source Aggregate:** DeviceAggregate
- **Payload:**
  - `deviceId` (String)
  - `capabilityCode` (String)
  - `removedTime` (DateTime)
  - `removedBy` (String)

#### DeviceFirmwareUpdatedEvent
- **Description:** Triggered when a device's firmware is updated
- **Source Aggregate:** DeviceAggregate
- **Payload:**
  - `deviceId` (String)
  - `previousVersion` (String)
  - `newVersion` (String)
  - `updateTime` (DateTime)
  - `updatedBy` (String)
  - `updateStatus` (String)

#### DeviceDecommissionedEvent
- **Description:** Triggered when a device is decommissioned
- **Source Aggregate:** DeviceAggregate
- **Payload:**
  - `deviceId` (String)
  - `reason` (String)
  - `decommissionTime` (DateTime)
  - `decommissionedBy` (String)
  - `archivalStatus` (String)

### Device Operation Context Events

#### DeviceStateChangedEvent
- **Description:** Triggered when a device's operational state changes
- **Source Aggregate:** DeviceStateAggregate
- **Payload:**
  - `deviceId` (String)
  - `previousState` (String)
  - `newState` (String)
  - `changeTime` (DateTime)
  - `changeTrigger` (String)

#### TelemetryReceivedEvent
- **Description:** Triggered when telemetry is received from a device
- **Source Aggregate:** DeviceStateAggregate
- **Payload:**
  - `deviceId` (String)
  - `telemetryType` (String)
  - `value` (Object)
  - `unit` (String)
  - `timestamp` (DateTime)
  - `quality` (String)

#### CommandSentEvent
- **Description:** Triggered when a command is sent to a device
- **Source Aggregate:** DeviceStateAggregate
- **Payload:**
  - `deviceId` (String)
  - `commandId` (String)
  - `commandType` (String)
  - `parameters` (Map of key-value pairs)
  - `sentTime` (DateTime)
  - `sentBy` (String)
  - `expiryTime` (DateTime)

#### CommandResponseReceivedEvent
- **Description:** Triggered when a response to a command is received from a device
- **Source Aggregate:** DeviceStateAggregate
- **Payload:**
  - `deviceId` (String)
  - `commandId` (String)
  - `status` (String)
  - `responsePayload` (Object)
  - `responseTime` (DateTime)
  - `executionDuration` (Integer)

#### DeviceConnectionStatusChangedEvent
- **Description:** Triggered when a device's connection status changes
- **Source Aggregate:** DeviceStateAggregate
- **Payload:**
  - `deviceId` (String)
  - `previousStatus` (String)
  - `newStatus` (String)
  - `changeTime` (DateTime)
  - `lastConnectedTime` (DateTime)

#### AlertTriggeredEvent
- **Description:** Triggered when an alert condition is detected
- **Source Aggregate:** DeviceStateAggregate
- **Payload:**
  - `deviceId` (String)
  - `alertId` (String)
  - `alertType` (String)
  - `severity` (String)
  - `message` (String)
  - `triggerTime` (DateTime)
  - `relatedTelemetry` (Map of key-value pairs)

#### AlertClearedEvent
- **Description:** Triggered when an alert condition is no longer present
- **Source Aggregate:** DeviceStateAggregate
- **Payload:**
  - `deviceId` (String)
  - `alertId` (String)
  - `clearTime` (DateTime)
  - `clearReason` (String)
  - `clearAction` (String)
  - `clearActionBy` (String)

### Maintenance Management Context Events

#### MaintenanceRecordCreatedEvent
- **Description:** Triggered when a new maintenance record is created
- **Source Aggregate:** MaintenanceRecordAggregate
- **Payload:**
  - `recordId` (String)
  - `deviceId` (String)
  - `maintenanceType` (String)
  - `scheduledTime` (DateTime)
  - `priority` (String)
  - `createdBy` (String)

#### MaintenanceCompletedEvent
- **Description:** Triggered when a maintenance activity is completed
- **Source Aggregate:** MaintenanceRecordAggregate
- **Payload:**
  - `recordId` (String)
  - `deviceId` (String)
  - `completionTime` (DateTime)
  - `technicianId` (String)
  - `outcome` (String)
  - `actions` (List of MaintenanceAction)
  - `followUpNeeded` (Boolean)

#### ComponentReplacedEvent
- **Description:** Triggered when a component is replaced during maintenance
- **Source Aggregate:** MaintenanceRecordAggregate
- **Payload:**
  - `recordId` (String)
  - `deviceId` (String)
  - `componentType` (String)
  - `oldPartNumber` (String)
  - `newPartNumber` (String)
  - `replacementTime` (DateTime)
  - `replacedBy` (String)
  - `reason` (String)

#### HealthAssessmentCreatedEvent
- **Description:** Triggered when a new health assessment is created
- **Source Aggregate:** HealthAssessmentAggregate
- **Payload:**
  - `assessmentId` (String)
  - `deviceId` (String)
  - `overallScore` (Integer)
  - `assessmentTime` (DateTime)
  - `assessmentType` (String)

#### CriticalHealthIssueDetectedEvent
- **Description:** Triggered when a critical health issue is detected
- **Source Aggregate:** HealthAssessmentAggregate
- **Payload:**
  - `assessmentId` (String)
  - `deviceId` (String)
  - `issueType` (String)
  - `affectedComponent` (String)
  - `severity` (String)
  - `detectionTime` (DateTime)
  - `recommendedAction` (String)
  - `timeToFailure` (Duration)

#### MaintenanceRecommendationCreatedEvent
- **Description:** Triggered when a new maintenance recommendation is created
- **Source Aggregate:** HealthAssessmentAggregate
- **Payload:**
  - `recommendationId` (String)
  - `deviceId` (String)
  - `recommendationType` (String)
  - `priority` (String)
  - `dueDate` (DateTime)
  - `estimatedDuration` (Duration)
  - `requiredParts` (List of String)
  - `justification` (String)

### Energy Management Context Events

#### EnergyConsumptionRecordedEvent
- **Description:** Triggered when energy consumption data is recorded
- **Source Aggregate:** EnergyConsumptionAggregate
- **Payload:**
  - `recordId` (String)
  - `deviceId` (String)
  - `startTime` (DateTime)
  - `endTime` (DateTime)
  - `energyConsumed` (Float)
  - `energyUnit` (String)
  - `cost` (Float)
  - `currency` (String)

#### AbnormalConsumptionDetectedEvent
- **Description:** Triggered when abnormal energy consumption is detected
- **Source Aggregate:** EnergyConsumptionAggregate
- **Payload:**
  - `recordId` (String)
  - `deviceId` (String)
  - `consumptionValue` (Float)
  - `expectedValue` (Float)
  - `deviation` (Float)
  - `detectionTime` (DateTime)
  - `potentialCauses` (List of String)

#### EfficiencyRatingChangedEvent
- **Description:** Triggered when a device's efficiency rating changes
- **Source Aggregate:** EnergyConsumptionAggregate
- **Payload:**
  - `deviceId` (String)
  - `previousRating` (Float)
  - `newRating` (Float)
  - `changeTime` (DateTime)
  - `changeFactors` (List of String)
  - `potentialSavings` (Float)

### Water Heater Specific Events

#### WaterHeaterRegisteredEvent
- **Description:** Triggered when a new water heater is registered in the system
- **Source Aggregate:** WaterHeaterAggregate
- **Payload:**
  - `deviceId` (String)
  - `manufacturer` (String)
  - `model` (String)
  - `tankCapacity` (Float)
  - `heatingElementCount` (Integer)
  - `heatingElementWattage` (List of Integer)
  - `fuelType` (String)
  - `registrationTime` (DateTime)

#### WaterTemperatureChangedEvent
- **Description:** Triggered when a water heater's temperature setting changes
- **Source Aggregate:** WaterHeaterAggregate
- **Payload:**
  - `deviceId` (String)
  - `previousTemperature` (Float)
  - `newTemperature` (Float)
  - `unit` (String)
  - `changeTime` (DateTime)
  - `changeMethod` (String)
  - `changedBy` (String)

#### HeatingElementActivatedEvent
- **Description:** Triggered when a heating element is activated
- **Source Aggregate:** WaterHeaterAggregate
- **Payload:**
  - `deviceId` (String)
  - `elementId` (String)
  - `activationTime` (DateTime)
  - `waterTemperature` (Float)
  - `targetTemperature` (Float)
  - `powerLevel` (Float)

#### HeatingElementDeactivatedEvent
- **Description:** Triggered when a heating element is deactivated
- **Source Aggregate:** WaterHeaterAggregate
- **Payload:**
  - `deviceId` (String)
  - `elementId` (String)
  - `deactivationTime` (DateTime)
  - `activeTime` (Duration)
  - `waterTemperature` (Float)
  - `energyConsumed` (Float)

#### WaterHeaterModeChangedEvent
- **Description:** Triggered when a water heater's operational mode changes
- **Source Aggregate:** WaterHeaterAggregate
- **Payload:**
  - `deviceId` (String)
  - `previousMode` (String)
  - `newMode` (String)
  - `changeTime` (DateTime)
  - `changedBy` (String)
  - `estimatedImpact` (String)

#### LeakDetectedEvent
- **Description:** Triggered when a potential leak is detected
- **Source Aggregate:** WaterHeaterAggregate
- **Payload:**
  - `deviceId` (String)
  - `detectionTime` (DateTime)
  - `confidence` (Float)
  - `sensorId` (String)
  - `detectionMethod` (String)
  - `recommendedAction` (String)

## Event Handling

### Event Processing Patterns

The IoTSphere platform uses the following patterns for event processing:

1. **Event Sourcing**
   - Storing the complete history of domain events
   - Reconstructing aggregate state from event streams
   - Maintaining temporal queries over historical states

2. **Event-Driven Architecture**
   - Loose coupling between event producers and consumers
   - Asynchronous processing for scalability
   - Event propagation across bounded contexts

3. **CQRS (Command Query Responsibility Segregation)**
   - Separation of command and query models
   - Optimized query projections built from events
   - Event handlers updating read models

### Event Handling Responsibilities

Each bounded context has specific event handling responsibilities:

#### Device Management Context
- Handling device registration and configuration events
- Updating device registries and indices
- Propagating device capability changes to other contexts

#### Device Operation Context
- Processing telemetry events for state updates
- Triggering alerts based on state change events
- Updating operational dashboards from state events

#### Maintenance Management Context
- Scheduling maintenance based on health events
- Updating health models from maintenance events
- Generating maintenance reports from history

#### Energy Management Context
- Calculating efficiency metrics from consumption events
- Detecting patterns from historical consumption
- Updating dashboards and reports with energy data
