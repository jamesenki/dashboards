# This feature file follows Test-Driven Development principles:
# - @red: Tests that are expected to fail (functionality not yet implemented)
# - @green: Tests that are expected to pass (minimum implementation complete)
# - @refactor: Tests after code refactoring (improved implementation)

Feature: Water Heater Operations Dashboard
  As a facility manager
  I want to monitor water heater operations in real-time
  So that I can ensure optimal performance and respond to issues quickly

  # GREEN PHASE: This test now validates the implemented behavior for viewing water heaters
  @current @device-management @device-operation @green
  Scenario: View list of all water heaters with status indicators
    Given I am logged in as a "facility_manager"
    When I navigate to the water heater dashboard
    Then I should see a list of all water heaters in the system
    And each water heater should display its connection status
    And each water heater should indicate if it is simulated

  # GREEN PHASE: This test now validates the implemented behavior for filtering by manufacturer
  @current @device-operation @green
  Scenario: Filter water heaters by manufacturer
    Given I am logged in as a "facility_manager"
    And the system has water heaters from multiple manufacturers
    When I navigate to the water heater dashboard
    And I filter by manufacturer "AquaTech"
    Then I should only see water heaters from "AquaTech"
    And I should be able to clear the filter to see all water heaters

  # GREEN PHASE: This test now validates the implemented behavior for filtering by connection status
  @current @device-operation @green
  Scenario: Filter water heaters by connection status
    Given I am logged in as a "facility_manager"
    And the system has both connected and disconnected water heaters
    When I navigate to the water heater dashboard
    And I filter by connection status "connected"
    Then I should only see water heaters with "connected" status
    And I should be able to clear the filter to see all water heaters

  # GREEN PHASE: This test now validates the implemented behavior for navigating to device details
  @current @device-operation @green
  Scenario: Navigate to water heater details page
    Given I am logged in as a "facility_manager"
    When I navigate to the water heater dashboard
    And I click on the water heater with ID "wh-001"
    Then I should be redirected to the details page for water heater "wh-001"
    And I should see the current operating status
    And I should see the reported temperature

  # GREEN PHASE: This test now validates the implemented real-time update behavior
  @current @device-operation @websocket @green
  Scenario: Real-time updates of water heater status
    Given I am logged in as a "facility_manager"
    And I am viewing the water heater dashboard
    When a water heater changes status from "ONLINE" to "OFFLINE"
    Then I should see the status indicator update without refreshing the page
    And the status change should be visually highlighted
