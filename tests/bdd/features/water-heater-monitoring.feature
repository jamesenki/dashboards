Feature: Water Heater Monitoring Dashboard
  As a facility manager
  I want to monitor and control water heaters remotely
  So that I can ensure optimal operation and energy efficiency

  Background:
    Given the user is authenticated
    And the user has access to water heater devices

  @current
  Scenario: View water heater dashboard
    When the user navigates to the water heater dashboard
    Then the user should see a list of all connected water heaters
    And the dashboard should display a summary of water heater status
    And the dashboard should show any active alerts

  @current
  Scenario: Filter water heaters by status
    Given the user is viewing the water heater dashboard
    When the user filters the list by "status" with value "active"
    Then only water heaters with "active" status should be displayed
    And the dashboard summary should update to reflect the filtered devices

  @current
  Scenario: View detailed water heater information
    Given the user is viewing the water heater dashboard
    When the user selects a specific water heater
    Then the user should see detailed information about the water heater
    And the details should include current water temperature
    And the details should include current operating mode
    And the details should include energy consumption metrics

  @current
  Scenario: Control water heater temperature
    Given the user is viewing a specific water heater's details
    When the user adjusts the temperature setting to "130°F"
    Then the system should send the temperature command to the device
    And the user should see a confirmation message
    And the device telemetry should eventually update to reflect the new setting

  @current
  Scenario: View water heater event history
    Given the user is viewing a specific water heater's details
    When the user navigates to the "Events" tab
    Then the user should see a chronological list of device events
    And the events should include status changes, alerts, and user actions
    And the user should be able to filter events by type

  @current
  Scenario: Toggle water heater operating mode
    Given the user is viewing a specific water heater's details
    When the user changes the operating mode to "eco"
    Then the system should send the mode change command to the device
    And the user should see a confirmation message
    And the device status should eventually update to reflect the new mode

  @current
  Scenario: Receive alert for anomalous behavior
    Given a water heater is operating with unusual temperature patterns
    When the anomaly detection system identifies the pattern
    Then an alert should be generated on the water heater dashboard
    And the alert should appear in the device's anomaly alerts panel
    And the alert should contain information about the detected anomaly

  @planned @ai-capability
  Scenario: Receive predictive maintenance notification
    Given a water heater has been in operation for an extended period
    When the predictive maintenance system detects potential issues based on telemetry data
    Then a maintenance recommendation should be generated
    And the recommendation should appear in the device's maintenance panel
    And the recommendation should include the likelihood of failure and recommended actions

  @planned @business-intelligence
  Scenario: View energy efficiency insights
    Given a user is viewing the water heater dashboard
    When the user navigates to the "Insights" section
    Then the system should display energy efficiency metrics for all water heaters
    And the insights should include comparative analysis against industry benchmarks
    And the insights should include recommendations for improving energy efficiency
    And the insights should include potential cost savings estimates

  @future @cross-device
  Scenario: Coordinate water heater operations across a facility
    Given a facility has multiple water heaters
    When peak demand times are approaching
    Then the system should suggest an optimal operation schedule
    And the schedule should balance hot water availability with energy costs
    And the user should be able to approve and implement the suggested schedule
