Feature: Device Real-Time Updates
  As a water heater operations manager
  I want to see real-time updates from water heaters
  So that I can monitor their current status without refreshing the page

  Background:
    Given the IoTSphere application is running
    And I am logged in as an administrator

  Scenario: Receive real-time temperature updates
    When I navigate to the water heater with ID "wh-test-001"
    And the device sends a new temperature reading of "140°F"
    Then the temperature display should update to "140°F" automatically
    And the status indicator should show "connected"

  Scenario: Handle connection interruptions
    When I navigate to the water heater with ID "wh-test-001"
    And the WebSocket connection is interrupted
    Then the status indicator should show "disconnected"
    And I should see a reconnection attempt message
    When the connection is restored
    Then the status indicator should show "connected" again

  Scenario: Update history chart with real-time data
    When I navigate to the water heater with ID "wh-test-001"
    And I click on the History tab
    And the device sends new temperature readings
    Then the temperature history chart should update automatically
    And the new data points should appear on the chart
