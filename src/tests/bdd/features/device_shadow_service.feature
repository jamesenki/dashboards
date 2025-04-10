# This feature file follows Test-Driven Development principles:
# - @red: Tests that are expected to fail (functionality not yet implemented)
# - @green: Tests that are expected to pass (minimum implementation complete)
# - @refactor: Tests after code refactoring (improved implementation)

Feature: Device Shadow Service API
  As an IoTSphere backend service
  I want to provide shadow state management capabilities
  So that device state can be monitored and controlled remotely

  # RED PHASE: This test defines the expected behavior before implementation
  @api @current @device-operation @red
  Scenario: Get device shadow state
    Given a device with ID "test-device-001" exists in the system
    When a client requests the shadow state for device "test-device-001"
    Then the response should be successful
    And the shadow document should contain "reported" and "desired" sections
    And the response should include the device ID "test-device-001"

  # RED PHASE: This test defines expected update behavior before implementation
  @api @current @device-operation @red
  Scenario: Update device shadow desired state
    Given a device with ID "test-device-001" exists in the system
    When a client updates the desired state with:
      | property          | value |
      | target_temperature | 125   |
    Then the response should be successful
    And the updated shadow should contain the new desired property "target_temperature" with value "125"

  # RED PHASE: This test defines expected error handling before implementation
  @api @current @device-operation @red
  Scenario: Device shadow does not exist
    Given a device with ID "non-existent-device" does not exist in the system
    When a client requests the shadow state for device "non-existent-device"
    Then the response should indicate the resource was not found

  # RED PHASE: This test defines WebSocket behavior before implementation
  @api @current @device-operation @websocket @red
  Scenario: Receive real-time shadow updates via WebSocket
    Given a device with ID "test-device-001" exists in the system
    And a WebSocket connection is established for device "test-device-001"
    When the device reports a state change to:
      | property    | value |
      | temperature | 130   |
      | status      | ONLINE|
    Then the WebSocket client should receive a shadow update
    And the update should contain the new reported values
