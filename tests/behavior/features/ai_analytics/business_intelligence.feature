Feature: Business Intelligence and Advanced Analytics
  As a facility manager or executive
  I want data-driven business insights across my device fleet
  So that I can make informed operational and financial decisions

  @current @ai-capability @ai-business-intelligence @persona-facilityman
  Scenario: View operational efficiency analytics for water heaters
    Given a fleet of water heaters with 6 months of operational data
    When a user with "FACILITY_MANAGER" role views the operational analytics dashboard
    Then the analytics dashboard should display:
      | reliabilityMetrics    | Uptime and reliability statistics           |
      | maintenanceEfficiency | Effectiveness of maintenance activities     |
      | performanceTrends     | Trends in device performance over time      |
      | costBreakdown         | Operational cost analysis                   |
    And the metrics should be based on actual operational data
    And comparative benchmarks should be provided where available

  @current @ai-capability @ai-business-intelligence @persona-facilityman
  Scenario: Generate ROI report for maintenance activities
    Given a water heater with completed maintenance records
    And historical performance data before and after maintenance
    When a user with "FACILITY_MANAGER" role requests a maintenance ROI report
    Then the system should calculate:
      | maintenanceCosts      | Total costs of maintenance activities       |
      | performanceImprovement| Quantified improvement in performance       |
      | energySavings         | Energy savings attributed to maintenance    |
      | lifespanExtension     | Estimated extension of useful life          |
      | downtimeReduction     | Reduction in unplanned downtime             |
    And it should present an overall ROI figure with supporting data
    And it should include confidence levels for the calculations

  @future @ai-capability @ai-business-intelligence @persona-facilityman
  Scenario: Generate cross-device fleet-wide optimization recommendations
    Given a diverse fleet of connected devices across multiple facilities
    And operational data for all devices
    When the business intelligence system performs a fleet-wide analysis
    Then it should identify optimization opportunities across device types
    And it should quantify the potential impact of each opportunity
    And it should prioritize recommendations based on:
      | financialImpact       | Estimated financial benefit                |
      | implementationEffort  | Resources required to implement            |
      | confidenceLevel       | Statistical confidence in the prediction   |
      | timeToBenefit         | Expected timeframe to realize benefits     |
    And it should provide implementation guidance for top recommendations

  @future @ai-capability @ai-business-intelligence @ai-learning @persona-facilityman
  Scenario: AI-driven operational scenario modeling
    Given a facility with operational and financial data
    When a user with "FACILITY_MANAGER" role conducts a "what-if" analysis
    And selects parameters:
      | deviceReplacementRate | 15% per year                             |
      | energyCosts           | Projected to increase 8% annually        |
      | maintenanceApproach   | Predictive with 80% compliance           |
      | operationalHours      | Extended by 2 hours daily                |
    Then the system should generate a 5-year projection model
    And the model should include:
      | capitalExpenditure    | Projected device replacement costs        |
      | operationalCosts      | Projected operational costs               |
      | reliability           | Expected system reliability metrics       |
      | energyConsumption     | Projected consumption patterns            |
      | totalCostOfOwnership  | Comprehensive TCO analysis                |
    And the model should compare against baseline scenarios
    And sensitivity analysis should be provided for key variables

  @future @ai-capability @ai-cross-device @ai-learning @persona-facilityman
  Scenario: Intelligent device fleet optimization
    Given a facility with multiple device types with varying:
      | age                   | Range from new to end-of-life              |
      | efficiency            | Range from high to low efficiency          |
      | reliability           | Range from reliable to problematic         |
      | utilization           | Range from high to low usage               |
    When the AI optimization system analyzes the entire fleet
    Then it should recommend an optimal device replacement strategy
    And it should suggest device redeployment based on usage patterns
    And it should identify candidates for:
      | immediateReplacement  | Devices with negative value retention      |
      | upgrades              | Devices where upgrades exceed replacement  |
      | redeployment          | Devices better suited to different locations |
      | retention             | Devices performing optimally               |
    And it should provide a phased implementation plan
    And it should calculate expected ROI for the overall strategy

  @future @ai-capability @ai-business-intelligence @persona-manufacturer
  Scenario: Manufacturer insights on device performance
    Given a manufacturer with devices deployed across multiple customers
    And anonymous performance data from the device fleet
    When a user with "MANUFACTURER" role views the product analytics
    Then the system should provide insights on:
      | fieldPerformance      | How devices perform in real-world settings |
      | failurePatterns       | Common failure modes and frequencies       |
      | usagePatterns         | How customers typically use the devices    |
      | featureUtilization    | Which features are most/least used         |
      | customerSatisfaction  | Derived satisfaction metrics               |
    And all data should be anonymized to protect customer privacy
    And insights should be categorized by device model and environment
    And product improvement recommendations should be generated
