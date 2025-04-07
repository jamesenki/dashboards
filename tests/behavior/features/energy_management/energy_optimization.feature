Feature: Energy Consumption Monitoring and Optimization
  As an Energy Manager or Facility Manager
  I want to monitor and optimize energy consumption of devices
  So that I can reduce operational costs and environmental impact

  @current @context-energy @persona-energyman @smoke
  Scenario: Monitor energy consumption for a water heater
    Given a registered water heater device with ID "water-heater-123"
    And the device has been reporting energy consumption data
    When a user with "ENERGY_MANAGER" role views the energy dashboard
    Then the system should display:
      | dailyConsumption  | Energy consumed in the last 24 hours     |
      | weeklyConsumption | Energy consumed in the last 7 days       |
      | monthlyConsumption| Energy consumed in the last 30 days      |
      | costEstimate      | Estimated cost based on energy rates     |
    And consumption data should be displayed with appropriate visualizations
    And historical trends should be visible

  @current @context-energy @persona-facilityman
  Scenario: Compare energy consumption across multiple water heaters
    Given a facility with 5 registered water heaters
    And all devices have been reporting energy consumption data
    When a user with "FACILITY_MANAGER" role views the energy comparison report
    Then the system should rank devices by energy efficiency
    And it should calculate the average consumption per device
    And it should identify the most and least efficient devices
    And it should provide comparative visualizations

  @current @context-energy @persona-enduser
  Scenario: End user views energy consumption for their water heater
    Given an end user with access to device "water-heater-123"
    When the user views the energy section of their dashboard
    Then they should see their current month's energy consumption
    And they should see a comparison to typical usage
    And they should see estimated cost information
    And they should see energy-saving recommendations

  @current @context-energy @ai-capability @persona-energyman
  Scenario: Receive energy optimization recommendations for a water heater
    Given a registered water heater device with ID "water-heater-123"
    And the device has 3 months of energy consumption history
    When a user with "ENERGY_MANAGER" role requests optimization recommendations
    Then the system should provide specific energy-saving recommendations
    And each recommendation should include:
      | title            | Clear description of the recommendation    |
      | potentialSavings | Estimated energy/cost savings              |
      | implementation   | Difficulty of implementing the change      |
      | roi              | Estimated return on investment period      |
    And recommendations should be ordered by potential impact

  @future @device-agnostic @context-energy @ai-capability @ai-cross-device @persona-energyman
  Scenario: Optimize energy usage across multiple device types
    Given a facility with diverse device types:
      | deviceId           | type             |
      | water-heater-123   | water-heater     |
      | vending-machine-456| vending-machine  |
      | hvac-unit-789      | hvac             |
    When the energy optimization system analyzes consumption patterns
    Then it should identify cross-device optimization opportunities
    And it should recommend load balancing strategies
    And it should suggest optimal operational schedules
    And it should calculate facility-wide potential savings
    And it should prioritize recommendations by impact and ease of implementation

  @future @device-agnostic @context-energy @ai-capability @ai-business-intelligence @persona-facilityman
  Scenario: Generate energy efficiency ROI analysis
    Given a facility with historical energy consumption data
    And a set of proposed energy optimization measures:
      | measure          | initialCost | expectedSavings |
      | Temperature tune | $0          | 5% per month    |
      | Schedule optimize| $0          | 10% per month   |
      | Insulation       | $500        | 15% per month   |
      | Component upgrade| $1200       | 25% per month   |
    When the business intelligence system analyzes the measures
    Then it should calculate the ROI for each measure
    And it should determine the optimal implementation sequence
    And it should project cumulative savings over 1, 3, and 5 years
    And it should account for energy price trends in projections
    And it should recommend the measures with the best ROI

  @future @device-agnostic @context-energy @ai-capability @ai-learning @persona-energyman
  Scenario: Self-optimizing energy efficiency algorithms
    Given a facility with energy optimization recommendations implemented
    And actual savings have been measured for each recommendation
    When the system compares predicted vs. actual savings
    Then it should adjust its prediction models to improve accuracy
    And it should refine future recommendations based on actual results
    And it should identify patterns in recommendation effectiveness
    And it should generate an optimization strategy that maximizes proven results
