Feature: Device Telemetry Monitoring
  As a User of the IoTSphere platform
  I want to monitor telemetry data from devices
  So that I can understand their current state and performance

  @current @context-deviceop @persona-facilityman @smoke
  Scenario: View current telemetry from a water heater
    Given a registered water heater device with ID "water-heater-123"
    And the device is reporting telemetry data
    When a user with "FACILITY_MANAGER" role requests current telemetry
    Then the system should return the following telemetry data:
      | temperature    | numeric | The current water temperature    |
      | pressure       | numeric | The current water pressure       |
      | energyConsumed | numeric | Energy consumed since last reset |
      | mode           | string  | The current operational mode     |
    And all telemetry values should have timestamps
    And all telemetry values should have appropriate units of measurement

  @current @context-deviceop @persona-technician
  Scenario: View historical telemetry for a water heater
    Given a registered water heater device with ID "water-heater-123"
    And the device has been reporting telemetry for "24 hours"
    When a user with "SERVICE_TECHNICIAN" role requests historical telemetry
    And specifies a time range of "last 24 hours"
    And selects "temperature" as the telemetry type
    Then the system should return temperature readings for the specified time period
    And the data should be presented in chronological order
    And the data should include at least 12 data points
    And all data points should have valid timestamps
    And all temperature values should be within the range of 100-140°F

  @current @context-deviceop @persona-enduser
  Scenario: End user views basic telemetry for their water heater
    Given an end user with access to device "water-heater-123"
    And the device is reporting telemetry data
    When the user views the device dashboard
    Then they should see the current temperature
    And they should see the current operational mode
    But they should not see detailed pressure readings
    And they should not see detailed energy consumption data

  @future @device-agnostic @context-deviceop @persona-facilityman
  Scenario: View standardized telemetry across different device types
    Given the following registered devices:
      | deviceId           | type             |
      | water-heater-123   | water-heater     |
      | vending-machine-456| vending-machine  |
      | hvac-unit-789      | hvac             |
    When a user with "FACILITY_MANAGER" role views the unified dashboard
    Then the system should show standardized energy consumption for all devices
    And the system should show standardized temperature readings for all devices
    And the telemetry should be normalized to consistent units
    And the telemetry should be displayed with device-appropriate visualizations

  @current @ai-capability @context-deviceop @persona-facilityman
  Scenario: View anomaly detection for water heater telemetry
    Given a registered water heater device with ID "water-heater-123"
    And the device is reporting telemetry data
    And the device has a temperature spike to "175°F"
    When the system processes the incoming telemetry
    Then it should detect an anomaly in the temperature readings
    And it should calculate the deviation from normal operation
    And it should generate an alert for the facility manager
    And the alert should include the anomaly type, severity, and timestamp

  @future @ai-capability @context-deviceop @ai-cross-device
  Scenario: Detect patterns across multiple devices
    Given a group of 5 water heaters in the same facility
    And all devices are reporting telemetry data
    When 3 of the water heaters show increased energy consumption
    Then the system should detect the cross-device consumption pattern
    And it should analyze environmental and usage factors
    And it should determine if the pattern indicates a systemic issue
    And it should generate an insight with a confidence score
