Feature: Device Shadow Document
  As an IoTSphere user
  I want to see device shadow data in the UI
  So that I can monitor the current state of devices

  Background:
    Given the IoTSphere application is running
    And I am logged in as an administrator

  # RED phase - this scenario will initially fail
  Scenario: View device shadow data on details page
    When I navigate to the water heater with ID "wh-test-001"
    Then I should see the device shadow information
    And the temperature should be displayed
    And the status indicators should reflect current device state

  Scenario: View temperature history with shadow data
    When I navigate to the water heater with ID "wh-test-001"
    And I click on the History tab
    Then I should see the temperature history chart
    And the chart should display historical temperature data

  Scenario: Show appropriate error when shadow document is missing
    When I navigate to the water heater with ID "wh-missing-shadow"
    Then I should see an error message about missing shadow document
    And the error message should clearly explain the issue
