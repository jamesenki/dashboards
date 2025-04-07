Feature: Manufacturer-Agnostic Water Heater API
  As an integrator or developer
  I want to interact with water heaters from any manufacturer using a standard API
  So that I can build consistent interfaces regardless of underlying device type

  @current @context-devicemgmt @persona-bmsintegrator @smoke
  Scenario: Get water heaters across multiple manufacturers
    Given multiple water heaters from different manufacturers are registered:
      | manufacturer   | count |
      | Rheem          | 3     |
      | AO Smith       | 2     |
      | Bradford White | 4     |
    When a user sends a GET request to "/api/manufacturer/water-heaters"
    Then the system should return all registered water heaters
    And each water heater should have manufacturer information
    And the response should use the standardized data model
    And the response should include pagination information

  @current @context-devicemgmt @persona-bmsintegrator
  Scenario: Filter water heaters by manufacturer
    Given multiple water heaters from different manufacturers are registered
    When a user sends a GET request to "/api/manufacturer/water-heaters?manufacturer=Rheem"
    Then the system should return only water heaters from "Rheem"
    And the response should use the standardized data model
    And the count of returned devices should match the number of registered Rheem devices

  @current @context-devicemgmt @persona-bmsintegrator
  Scenario: Get individual water heater details by ID
    Given a registered water heater with ID "wh-123" from manufacturer "AO Smith"
    When a user sends a GET request to "/api/manufacturer/water-heaters/wh-123"
    Then the system should return the water heater details
    And the response should include:
      | id              | The unique identifier for the water heater    |
      | manufacturer    | "AO Smith"                                    |
      | model           | The water heater model                        |
      | serialNumber    | The water heater serial number                |
      | capabilities    | List of device capabilities                   |
      | status          | Current operational status                    |
      | connectionState | Current connection state                      |
      | currentSettings | Current operational settings                  |

  @current @context-devicemgmt @context-maintenance @persona-bmsintegrator
  Scenario: Get operational summary including maintenance predictions
    Given a registered water heater with ID "wh-123" with operational history
    When a user sends a GET request to "/api/manufacturer/water-heaters/wh-123/summary"
    Then the system should return an operational summary including:
      | averageUsage       | Average daily water usage                   |
      | energyConsumption  | Energy consumption statistics               |
      | healthScore        | Current health assessment score             |
      | maintenanceNeeded  | Whether maintenance is currently needed     |
      | predictedIssues    | Any predicted upcoming issues               |
      | nextMaintenanceDate| Recommended next maintenance date           |
    And the response should follow the standardized format regardless of manufacturer

  @current @context-deviceop @persona-bmsintegrator
  Scenario: Update water heater operational mode
    Given a registered water heater with ID "wh-123"
    When a user sends a PUT request to "/api/manufacturer/water-heaters/wh-123/mode"
    And includes the mode "ECO" in the request body
    Then the system should translate the request to the manufacturer-specific format
    And the water heater mode should be updated to "ECO"
    And the response should include the updated water heater state
    And the standardized response format should be the same regardless of manufacturer

  @current @context-devicemgmt @persona-bmsintegrator
  Scenario: Get list of supported manufacturers
    When a user sends a GET request to "/api/manufacturer/water-heaters/manufacturers"
    Then the system should return a list of all supported manufacturers
    And each manufacturer should include:
      | name            | The manufacturer name                        |
      | supportedModels | List of supported model families             |
      | capabilities    | List of supported capabilities               |
    And the response should include any recently added manufacturers

  @future @device-agnostic @context-devicemgmt @persona-bmsintegrator
  Scenario: Unified API across different device types
    Given the following registered devices:
      | deviceId  | type           | manufacturer |
      | wh-123    | water-heater   | Rheem        |
      | vm-456    | vending-machine| VendCorp     |
      | rb-789    | robot          | RoboTech     |
    When a user sends a GET request to "/api/devices"
    Then the system should return all devices regardless of type
    And each device should use its type-specific data model
    And all devices should share common base fields:
      | id              | The unique identifier for the device         |
      | type            | The device type                              |
      | manufacturer    | The device manufacturer                      |
      | capabilities    | List of device capabilities                  |
      | status          | Current operational status                   |
      | connectionState | Current connection state                     |
    And the response should maintain backward compatibility with existing clients
