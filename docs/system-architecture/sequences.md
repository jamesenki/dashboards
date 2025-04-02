# IoTSphere Sequence Diagrams

This document provides comprehensive sequence diagrams that illustrate key system flows including error handling and recovery scenarios. Following our Test-Driven Development principles, these diagrams define expected behaviors that drive implementation.

## Device Data Flow

```plantuml
@startuml
!define PLANTUML_SERVER_URL https://www.plantuml.com/plantuml
participant "IoT Device" as device
participant "API Server" as api
participant "Device Management" as deviceMgmt
participant "Telemetry Processor" as telemetry
database "TimescaleDB" as tsdb
database "Main Database" as db

== Successful Device Telemetry Flow ==

device -> api: Send telemetry data (HTTPS/MQTT)
activate api

api -> deviceMgmt: Verify device authenticity
activate deviceMgmt
deviceMgmt -> db: Query device credentials
activate db
db --> deviceMgmt: Device verified
deactivate db
deviceMgmt --> api: Device authorized
deactivate deviceMgmt

api -> telemetry: Process telemetry data
activate telemetry
telemetry -> telemetry: Validate data format
telemetry -> telemetry: Pre-process readings
telemetry -> tsdb: Store time-series data
activate tsdb
tsdb --> telemetry: Confirm storage
deactivate tsdb
telemetry -> telemetry: Check for threshold violations

telemetry -> db: Update device last_seen timestamp
activate db
db --> telemetry: Confirm update
deactivate db

telemetry --> api: Processing complete
deactivate telemetry

api --> device: 200 OK Response
deactivate api

== Error Handling: Device Authentication Failure ==

device -> api: Send telemetry data (invalid auth)
activate api

api -> deviceMgmt: Verify device authenticity
activate deviceMgmt
deviceMgmt -> db: Query device credentials
activate db
db --> deviceMgmt: No matching device/invalid credentials
deactivate db
deviceMgmt --> api: Authentication failed
deactivate deviceMgmt

api -> api: Log authentication failure
api -> api: Rate limit check for security

api --> device: 401 Unauthorized
deactivate api

== Error Handling: Data Processing Failure ==

device -> api: Send telemetry data (malformed)
activate api

api -> deviceMgmt: Verify device authenticity
activate deviceMgmt
deviceMgmt -> db: Query device credentials
activate db
db --> deviceMgmt: Device verified
deactivate db
deviceMgmt --> api: Device authorized
deactivate deviceMgmt

api -> telemetry: Process telemetry data
activate telemetry
telemetry -> telemetry: Validate data format
note right: Schema validation fails
telemetry -> telemetry: Log data format error
telemetry -> db: Record validation error
activate db
db --> telemetry: Error recorded
deactivate db
telemetry --> api: Processing failed: Invalid format
deactivate telemetry

api --> device: 400 Bad Request (with error details)
deactivate api

@enduml
```

## User Dashboard Flow

```plantuml
@startuml
!define PLANTUML_SERVER_URL https://www.plantuml.com/plantuml
actor "User" as user
participant "Browser" as browser
participant "API Server" as api
participant "Auth Service" as auth
participant "Monitoring Service" as monitor
database "Database" as db

== Successful Dashboard Flow ==

user -> browser: Navigate to dashboard
activate browser

browser -> api: GET /api/dashboard
activate api

api -> auth: Validate JWT token
activate auth
auth -> auth: Decode and verify token
auth --> api: Token valid
deactivate auth

api -> monitor: Request dashboard data
activate monitor
monitor -> db: Query dashboard configuration
activate db
db --> monitor: Dashboard config
deactivate db

monitor -> db: Query device status
activate db
db --> monitor: Device data
deactivate db

monitor -> db: Query alerts
activate db
db --> monitor: Active alerts
deactivate db

monitor -> monitor: Assemble dashboard data
monitor --> api: Complete dashboard data
deactivate monitor

api --> browser: 200 OK with dashboard JSON
deactivate api

browser -> browser: Render dashboard
browser --> user: Display dashboard
deactivate browser

== Error Handling: Authentication Failure ==

user -> browser: Navigate to dashboard (expired token)
activate browser

browser -> api: GET /api/dashboard
activate api

api -> auth: Validate JWT token
activate auth
auth -> auth: Decode and verify token
note right: Token expired
auth --> api: Token invalid/expired
deactivate auth

api --> browser: 401 Unauthorized
deactivate api

browser -> browser: Redirect to login page
browser --> user: Show login screen
deactivate browser

== Error Handling: Data Retrieval Failure ==

user -> browser: Navigate to dashboard
activate browser

browser -> api: GET /api/dashboard
activate api

api -> auth: Validate JWT token
activate auth
auth -> auth: Decode and verify token
auth --> api: Token valid
deactivate auth

api -> monitor: Request dashboard data
activate monitor
monitor -> db: Query dashboard configuration
activate db
note right: Database connection failure
db --> monitor: Connection error
deactivate db

monitor -> monitor: Log database error
monitor -> monitor: Attempt retry (max 3)
monitor --> api: Error retrieving data
deactivate monitor

api -> api: Log error with details
api --> browser: 503 Service Unavailable
deactivate api

browser -> browser: Show error message
browser -> browser: Enable retry button
browser --> user: Display friendly error
deactivate browser

@enduml
```

## Model Monitoring Alert Flow

```plantuml
@startuml
!define PLANTUML_SERVER_URL https://www.plantuml.com/plantuml
actor "Data Scientist" as user
participant "Frontend" as frontend
participant "API Server" as api
participant "Monitoring Service" as monitor
participant "Alert Manager" as alertMgr
participant "Notification Service" as notify
database "Database" as db

== Alert Rule Creation ==

user -> frontend: Create alert rule
activate frontend
frontend -> frontend: Validate rule parameters
frontend -> api: POST /api/monitoring/alert_rules
activate api

api -> monitor: Create alert rule
activate monitor
monitor -> alertMgr: Create rule
activate alertMgr

alertMgr -> alertMgr: Validate rule configuration
alertMgr -> db: Insert alert rule
activate db
db --> alertMgr: Rule created
deactivate db

alertMgr --> monitor: Rule created successfully
deactivate alertMgr
monitor --> api: Return rule details
deactivate monitor

api --> frontend: 200 OK with rule details
deactivate api
frontend --> user: Show success message
deactivate frontend

== Alert Triggering ==

note over db: Model metric exceeds threshold

monitor -> alertMgr: Check for rule violations
activate monitor
activate alertMgr

alertMgr -> db: Query active rules
activate db
db --> alertMgr: List of rules
deactivate db

alertMgr -> db: Query latest metrics
activate db
db --> alertMgr: Recent metrics
deactivate db

alertMgr -> alertMgr: Evaluate rules against metrics
note right: Threshold exceeded

alertMgr -> db: Create alert event
activate db
db --> alertMgr: Alert created
deactivate db

alertMgr -> notify: Send notification
activate notify
notify -> notify: Format notification
notify -> notify: Send via configured channels
notify --> alertMgr: Notification sent
deactivate notify

alertMgr --> monitor: Alert triggered
deactivate alertMgr
deactivate monitor

== Error Handling: Failed Notification ==

monitor -> alertMgr: Check for rule violations
activate monitor
activate alertMgr

alertMgr -> alertMgr: Evaluate rules against metrics
note right: Threshold exceeded

alertMgr -> db: Create alert event
activate db
db --> alertMgr: Alert created
deactivate db

alertMgr -> notify: Send notification
activate notify
notify -> notify: Format notification
notify -> notify: Attempt to send notification
note right: Email service unavailable

notify -> notify: Log failure
notify -> notify: Queue for retry
notify --> alertMgr: Notification queued for retry
deactivate notify

alertMgr -> db: Update alert with notification status
activate db
db --> alertMgr: Alert updated
deactivate db

alertMgr --> monitor: Alert triggered, notification pending
deactivate alertMgr
deactivate monitor

@enduml
```

These sequence diagrams align with our Test-Driven Development approach by:

1. **Defining Expected Behavior**: The diagrams clearly document how components should interact in both successful and failure scenarios
2. **Guiding Implementation**: Developers can use these flows as specifications to implement components that satisfy the expected behaviors
3. **Supporting Testing**: Each interaction in the diagram can be validated through tests
4. **Documenting Error Handling**: Clear illustration of how the system should gracefully handle failures
