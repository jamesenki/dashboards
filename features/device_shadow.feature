Feature: Device Shadow Service
  As an IoTSphere user
  I want to interact with device shadows
  So that I can monitor and control my devices remotely

  Background:
    Given the IoTSphere application is running
    And I am logged in as an administrator
    And there are registered devices in the system

  Scenario: View current device state
    When I navigate to the device details page for "wh-001"
    Then I should see the current temperature displayed
    And I should see the device status indicator
    And I should see the heater status indicator

  Scenario: Request device state change
    When I navigate to the device details page for "wh-001"
    And I change the target temperature to 130°F
    And I click the "Apply" button
    Then the system should confirm the request was submitted
    And the target temperature should show as "pending"
    And when the device responds, the pending status should clear

  Scenario: Receive real-time device updates
    When I navigate to the device details page for "wh-001"
    And the device sends a state update
    Then I should see the updated values without refreshing
    And the history chart should update with the new data point

  Scenario: View multiple water heaters
    When I navigate to the device details page for "wh-002"
    Then I should see the water heater details
    And I should see the current temperature displayed
    And I should see if the water heater is active or in standby
