Feature: Device Registration
  As a Facility Manager
  I want to register new devices in the system
  So that I can monitor and manage them through the platform

  @current @context-devicemgmt @persona-facilityman @smoke
  Scenario: Register a new water heater with manufacturer details
    Given a user with "FACILITY_MANAGER" role is authenticated
    When they register a new water heater with the following details:
      | name           | Smart Water Heater 001 |
      | type           | water-heater           |
      | manufacturer   | Rheem                  |
      | model          | PRO G50-38N            |
      | serialNumber   | WH12345                |
      | tankCapacity   | 50                     |
      | firmwareVersion| 1.2.0                  |
    Then the system should confirm successful registration
    And the water heater should appear in the device registry
    And the water heater should have the "TEMPERATURE_CONTROL" capability
    And the water heater should have the "ENERGY_MONITORING" capability
    And the water heater should have the "WATER_LEVEL" capability

  @current @context-devicemgmt @persona-facilityman
  Scenario: Register a water heater without all optional fields
    Given a user with "FACILITY_MANAGER" role is authenticated
    When they register a new water heater with minimum required details:
      | type           | water-heater          |
      | manufacturer   | AO Smith              |
      | model          | ProLine XE            |
    Then the system should confirm successful registration
    And the water heater should be assigned a default name
    And the water heater should appear in the device registry

  @current @context-devicemgmt @persona-facilityman
  Scenario: Attempt to register a water heater with missing required fields
    Given a user with "FACILITY_MANAGER" role is authenticated
    When they attempt to register a new water heater with incomplete details:
      | name           | Problem Heater        |
      | model          | Unknown               |
    Then the system should reject the registration
    And the system should indicate "manufacturer is required" as the reason
    And the water heater should not appear in the device registry

  @current @context-devicemgmt @persona-sysadmin
  Scenario: System administrator registers a water heater for a facility
    Given a user with "SYSTEM_ADMIN" role is authenticated
    When they register a new water heater on behalf of facility "Building A":
      | name           | Building A Heater 1   |
      | type           | water-heater          |
      | manufacturer   | Bradford White        |
      | model          | MI5036FBN             |
      | location       | Basement              |
    Then the system should confirm successful registration
    And the water heater should be associated with "Building A" facility
    And the water heater should appear in the device registry

  @future @device-agnostic @context-devicemgmt @persona-facilityman
  Scenario: Register a new vending machine with automatic capability detection
    Given a user with "FACILITY_MANAGER" role is authenticated
    When they register a new device with basic information:
      | name           | Lobby Vending         |
      | type           | vending-machine       |
      | manufacturer   | VendCorp              |
      | model          | VC-5000               |
      | protocol       | mqtt                  |
    Then the system should detect the device's capabilities
    And assign at least the capabilities:
      | INVENTORY_MANAGEMENT |
      | TEMPERATURE_CONTROL  |
      | ENERGY_MONITORING    |
    And the vending machine should appear in the device registry
    And the device type should be correctly identified as "vending-machine"

  @future @device-agnostic @context-devicemgmt @persona-sysadmin
  Scenario: Register a device with custom capabilities
    Given a user with "SYSTEM_ADMIN" role is authenticated
    When they register a new device with custom capabilities:
      | name           | Smart Robot           |
      | type           | robot                 |
      | manufacturer   | RoboTech              |
      | model          | RT-100                |
      | capabilities   | MOBILITY, TEMPERATURE_CONTROL, INVENTORY_MANAGEMENT |
    Then the system should confirm successful registration
    And the robot should have exactly the specified capabilities
    And the robot should appear in the device registry
