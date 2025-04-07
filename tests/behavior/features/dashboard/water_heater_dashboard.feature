Feature: Water Heater Operations Dashboard
  As a facility manager
  I want to monitor water heater operations in real-time
  So that I can ensure optimal performance and respond to issues quickly

  @current @device-management @device-operation
  Scenario: View list of all water heaters with status indicators
    Given I am logged in as a "facility_manager"
    When I navigate to the water heater dashboard
    Then I should see a list of all water heaters in the system
    And each water heater should display its connection status
    And each water heater should indicate if it is simulated

  @current @device-operation
  Scenario: Filter water heaters by manufacturer
    Given I am logged in as a "facility_manager"
    And the system has water heaters from multiple manufacturers
    When I navigate to the water heater dashboard
    And I filter by manufacturer "AquaTech"
    Then I should only see water heaters from "AquaTech"
    And I should be able to clear the filter to see all water heaters

  @current @device-operation
  Scenario: Filter water heaters by connection status
    Given I am logged in as a "facility_manager"
    And the system has both connected and disconnected water heaters
    When I navigate to the water heater dashboard
    And I filter by connection status "connected"
    Then I should only see water heaters with "connected" status
    And I should be able to clear the filter to see all water heaters

  @current @device-operation @cross-device
  Scenario: View dashboard summary metrics
    Given I am logged in as a "facility_manager"
    When I navigate to the water heater dashboard
    Then I should see summary metrics including:
      | Total Devices      |
      | Connected Devices  |
      | Disconnected Devices |
      | Simulated Devices  |

  @current @device-operation
  Scenario: View detailed device status card
    Given I am logged in as a "facility_manager"
    And there is a connected water heater with ID "wh-001"
    When I navigate to the water heater dashboard
    Then each device card should show:
      | Device Name        |
      | Manufacturer       |
      | Model              |
      | Current Temperature |
      | Target Temperature |
      | Heating Status     |
      | Mode               |

  @current @device-operation
  Scenario: Access detailed device view from dashboard
    Given I am logged in as a "facility_manager"
    And there is a water heater with ID "wh-001"
    When I navigate to the water heater dashboard
    And I select the water heater with ID "wh-001"
    Then I should see the detailed view for water heater "wh-001"
    And the detailed view should show device information
    And the detailed view should show real-time operational status

  @current @device-operation @telemetry
  Scenario: View telemetry history chart for a specific device
    Given I am logged in as a "facility_manager"
    And there is a water heater with ID "wh-001" with historical telemetry data
    When I navigate to the detailed view for water heater "wh-001"
    And I select the "History" tab
    Then I should see a chart displaying historical temperature data
    And I should be able to select different time ranges
    And I should be able to select different metrics to display

  @current @device-operation @analytics @ai-capability
  Scenario: View device performance metrics with efficiency rating
    Given I am logged in as a "facility_manager"
    And there is a water heater with ID "wh-001" with performance data
    When I navigate to the detailed view for water heater "wh-001"
    And I select the "Performance" tab
    Then I should see the efficiency rating for the water heater
    And I should see key performance metrics including:
      | Energy Consumption |
      | Water Usage        |
      | Heating Cycles     |
      | Average Temperature |
      | Recovery Rate      |

  @current @device-operation
  Scenario: Change device temperature setpoint
    Given I am logged in as a "facility_manager"
    And there is a connected water heater with ID "wh-001"
    When I navigate to the detailed view for water heater "wh-001"
    And I change the temperature setpoint to "130"
    Then the system should send a command to set the target temperature to "130"
    And the device should acknowledge the command

  @current @device-operation
  Scenario: Toggle device power state
    Given I am logged in as a "facility_manager"
    And there is a connected water heater with ID "wh-001" in "standby" mode
    When I navigate to the detailed view for water heater "wh-001"
    And I click the "Turn On" button
    Then the system should send a power toggle command to the device
    And the device mode should change from "standby"

  @current @device-operation @anomaly-detection @ai-capability
  Scenario: View anomalies detected for a device
    Given I am logged in as a "facility_manager"
    And there is a water heater with ID "wh-001" with detected anomalies
    When I navigate to the detailed view for water heater "wh-001"
    And I select the "Performance" tab
    Then I should see the number of anomalies detected
    And I should be able to view details about the anomalies

  @current @device-operation @telemetry
  Scenario: Switch between temperature units
    Given I am logged in as a "facility_manager"
    And there is a water heater with ID "wh-001"
    When I navigate to the detailed view for water heater "wh-001"
    And I toggle the temperature unit
    Then the temperature values should be converted to the selected unit
    And the unit indicator should update accordingly

  @planned @cross-device @device-operation
  Scenario: Compare performance metrics between multiple water heaters
    Given I am logged in as a "facility_manager"
    And there are multiple water heaters with historical data
    When I navigate to the water heater dashboard
    And I select multiple devices for comparison
    Then I should see a comparison view of the selected devices
    And I should be able to compare key performance metrics

  @planned @predictive @ai-capability
  Scenario: View predictive maintenance recommendations
    Given I am logged in as a "facility_manager"
    And there is a water heater with ID "wh-001" with sufficient operational history
    When I navigate to the detailed view for water heater "wh-001"
    And I select the "Maintenance" tab
    Then I should see predictive maintenance recommendations
    And each recommendation should include expected benefits and priority

  @planned @business-intelligence @ai-capability
  Scenario: View energy optimization suggestions with ROI
    Given I am logged in as a "facility_manager"
    And there is a water heater with ID "wh-001" with operational history
    When I navigate to the detailed view for water heater "wh-001"
    And I select the "Performance" tab
    Then I should see energy optimization suggestions
    And each suggestion should include estimated ROI and implementation cost
