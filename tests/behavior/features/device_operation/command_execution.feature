Feature: Device Command Execution
  As a user of the IoTSphere platform
  I want to send commands to control devices
  So that I can manage their operation remotely

  @current @context-deviceop @persona-facilityman @smoke
  Scenario: Set temperature on a water heater
    Given a registered water heater device with ID "water-heater-123"
    And the device has the "TEMPERATURE_CONTROL" capability
    And the device is online
    When a user with "FACILITY_MANAGER" role sends a "setTemperature" command
    And provides a parameter "temperature" with value "125"
    Then the system should successfully dispatch the command
    And the command status should be "SENT"
    And when the command completes
    Then the command status should change to "COMPLETED"
    And the device state should reflect the new temperature setting
    And the command execution should be logged

  @current @context-deviceop @persona-enduser
  Scenario: End user changes operational mode on their water heater
    Given an end user with access to device "water-heater-123"
    And the device is online
    When the user sends a "setMode" command
    And selects the "ECO" mode
    Then the system should successfully dispatch the command
    And the device state should be updated to reflect the new mode
    And the user should receive confirmation of the mode change
    And the expected energy savings should be displayed

  @current @context-deviceop @persona-facilityman
  Scenario: Attempt to send command to an offline device
    Given a registered water heater device with ID "water-heater-123"
    And the device is offline
    When a user with "FACILITY_MANAGER" role sends a "setTemperature" command
    Then the system should queue the command for later execution
    And the command status should be "QUEUED"
    And the user should be notified that the device is offline
    And when the device comes online
    Then the system should attempt to execute the queued command

  @current @context-deviceop @persona-technician
  Scenario: Service technician runs diagnostic command
    Given a registered water heater device with ID "water-heater-123"
    And the device supports diagnostic commands
    When a user with "SERVICE_TECHNICIAN" role sends a "runDiagnostic" command
    Then the system should successfully dispatch the command
    And the diagnostic results should be returned
    And the results should include component status information
    And the diagnostic execution should be logged in the maintenance record

  @future @device-agnostic @context-deviceop @persona-facilityman
  Scenario: Execute capability-based command across different device types
    Given the following registered devices with "TEMPERATURE_CONTROL" capability:
      | deviceId           | type             |
      | water-heater-123   | water-heater     |
      | vending-machine-456| vending-machine  |
      | hvac-unit-789      | hvac             |
    When a user with "FACILITY_MANAGER" role sends a batch "setTemperature" command
    And provides a parameter "temperature" with value "68"
    Then the system should adapt the command for each device type
    And it should apply appropriate unit conversions
    And each device should receive a properly formatted command
    And the commands should be executed in parallel
    And the system should report individual command status for each device

  @future @device-agnostic @context-deviceop @ai-capability @persona-facilityman
  Scenario: AI-recommended command sequence optimization
    Given a facility with multiple connected devices
    And the devices have interdependent operations
    When a user requests to optimize system operation
    Then the AI should analyze the operational dependencies
    And it should generate an optimal command sequence
    And the sequence should minimize energy consumption
    And the sequence should maintain required performance levels
    And the system should execute the commands in the recommended sequence
    And it should monitor the effects and adjust if necessary

  @future @device-agnostic @context-deviceop @ai-learning @persona-sysadmin
  Scenario: Learning command patterns for automated routines
    Given a facility with established operational patterns
    And command history for the past 30 days
    When the system analyzes command patterns
    Then it should identify recurring command sequences
    And it should suggest automated routines based on:
      | timeOfDay          | Commands typically executed at specific times |
      | dayOfWeek          | Commands typically executed on specific days  |
      | externalConditions | Commands correlated with external factors     |
      | userRoles          | Commands typically executed by specific roles |
    And for each suggested routine, it should provide:
      | commandSequence    | The commands to be executed automatically     |
      | triggerConditions  | When the routine should be executed           |
      | expectedOutcomes   | What the routine is expected to achieve       |
      | overrideOptions    | How users can override if necessary           |
