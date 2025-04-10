# This feature file follows Test-Driven Development principles:
# - @red: Tests that are expected to fail (functionality not yet implemented)
# - @green: Tests that are expected to pass (minimum implementation complete)
# - @refactor: Tests after code refactoring (improved implementation)

Feature: IoT Device Registration and Management
  As a system administrator
  I want to register and manage IoT devices in the platform
  So that I can monitor and control them centrally

  # RED PHASE: Define expected behavior for device registration
  @current @device-management @red
  Scenario: Register a new water heater device
    Given I am logged in as a "system_administrator"
    When I navigate to the device management page
    And I select "Add New Device"
    And I enter the following device information:
      | field               | value                       |
      | name                | Test Water Heater           |
      | manufacturer        | AquaTech                    |
      | model               | AT-5000                     |
      | serial_number       | AT5K-12345                  |
      | location            | Building A, Basement        |
      | device_type         | water_heater                |
    And I submit the device registration form
    Then the device should be successfully registered in the system
    And I should see the new device in the device list
    And the device should have status "PENDING_ACTIVATION"

  # RED PHASE: Define expected behavior for device activation
  @current @device-management @red
  Scenario: Activate a newly registered device
    Given I am logged in as a "system_administrator"
    And a device with name "Test Water Heater" exists with status "PENDING_ACTIVATION"
    When I navigate to the device management page
    And I select the device with name "Test Water Heater"
    And I select "Activate Device"
    And I enter the following activation information:
      | field          | value                          |
      | activation_key | AT5K-12345-ACT-KEY             |
      | connection_url | mqtts://iot.iotsphere.com:8883 |
    And I submit the activation form
    Then the device should have status "ACTIVE"
    And the system should generate device credentials
    And I should see the device connection information

  # RED PHASE: Define expected behavior for device update
  @current @device-management @red
  Scenario: Update device information
    Given I am logged in as a "system_administrator"
    And a device with name "Test Water Heater" exists with status "ACTIVE"
    When I navigate to the device management page
    And I select the device with name "Test Water Heater"
    And I select "Edit Device"
    And I update the following information:
      | field    | value                    |
      | name     | Main Building Water Heater |
      | location | Building A, Utility Room |
    And I save the changes
    Then the device details should be updated in the system
    And I should see the updated information in the device list

  # RED PHASE: Define expected behavior for device deactivation
  @current @device-management @red
  Scenario: Deactivate a device
    Given I am logged in as a "system_administrator"
    And a device with name "Test Water Heater" exists with status "ACTIVE"
    When I navigate to the device management page
    And I select the device with name "Test Water Heater"
    And I select "Deactivate Device"
    And I confirm the deactivation
    Then the device should have status "INACTIVE"
    And the device should no longer receive commands
    And the device should no longer report telemetry

  # RED PHASE: Define expected behavior for device removal
  @current @device-management @red
  Scenario: Remove a device from the system
    Given I am logged in as a "system_administrator"
    And a device with name "Test Water Heater" exists with status "INACTIVE"
    When I navigate to the device management page
    And I select the device with name "Test Water Heater"
    And I select "Remove Device"
    And I enter "DELETE" in the confirmation field
    And I confirm the removal
    Then the device should be permanently removed from the system
    And I should not see the device in the device list
    And I should see a confirmation message

  # RED PHASE: Define expected behavior for manufacturer-agnostic registration
  @future @device-management @cross-device @red
  Scenario: Register a device using manufacturer-agnostic template
    Given I am logged in as a "system_administrator"
    When I navigate to the device management page
    And I select "Add New Device"
    And I select device type "Generic Water Heater"
    And I enter the following device information:
      | field         | value                  |
      | name          | Generic Water Heater   |
      | manufacturer  | NewVendor              |
      | model         | NV-100                 |
      | serial_number | NV100-9876             |
      | location      | Building B, Basement   |
    And I map the following capabilities:
      | standard_capability | manufacturer_capability  |
      | temperature         | water_temp               |
      | heating_status      | heater_state             |
      | set_temperature     | temp_setpoint            |
    And I submit the device registration form
    Then the device should be successfully registered in the system
    And the system should create a capability mapping for the device
    And I should see the standard capabilities in the device details
