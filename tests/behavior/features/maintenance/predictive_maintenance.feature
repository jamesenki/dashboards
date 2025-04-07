Feature: Predictive Maintenance and Health Assessment
  As a Facility Manager or Service Technician
  I want to predict maintenance needs and assess device health
  So that I can prevent failures and optimize maintenance schedules

  @current @context-maintenance @ai-capability @ai-predictive @persona-facilityman
  Scenario: Generate health assessment for a water heater
    Given a registered water heater device with ID "water-heater-123"
    And the device has 3 months of operational history
    When a user with "FACILITY_MANAGER" role requests a health assessment
    Then the system should generate a health assessment with:
      | overallScore     | A numeric score between 0-100                |
      | componentScores  | Individual scores for key components         |
      | estimatedLifespan| Predicted remaining useful life              |
      | confidenceLevel  | Confidence score for the prediction          |
    And the assessment should be based on actual operational data
    And the results should be displayed with appropriate visualizations

  @current @context-maintenance @ai-capability @ai-predictive @persona-technician
  Scenario: Predict water heater component failures
    Given a registered water heater device with ID "water-heater-123"
    And the device has shown increasing temperature fluctuations
    When the predictive maintenance system analyzes the device
    Then it should identify potential heating element failure
    And it should predict when the failure is likely to occur
    And it should specify the confidence level of the prediction
    And it should recommend preventative maintenance actions

  @current @context-maintenance @ai-capability @persona-facilityman
  Scenario: View maintenance recommendations for a water heater
    Given a registered water heater device with ID "water-heater-123"
    And the device has a health assessment with a score of "65"
    When a user with "FACILITY_MANAGER" role views maintenance recommendations
    Then the system should provide specific maintenance actions
    And each maintenance recommendation should include:
      | priority        | The urgency of the maintenance            |
      | timeframe       | Recommended timeframe for action          |
      | estimatedCost   | Projected cost of the maintenance         |
      | potentialImpact | Impact of performing or skipping maintenance |
    And recommendations should be ordered by priority

  @future @device-agnostic @context-maintenance @ai-capability @ai-learning @persona-technician
  Scenario: Self-improving maintenance predictions
    Given multiple water heaters with completed maintenance records
    And previous predictions exist for each maintenance event
    When the system analyzes prediction accuracy against actual outcomes
    Then it should adjust its prediction models to improve accuracy
    And it should generate a model improvement report showing:
      | previousAccuracy | Accuracy before model adjustment        |
      | newAccuracy      | Accuracy after model adjustment         |
      | improvementRate  | Percentage improvement in accuracy      |
      | keyFactors       | Factors that improved model performance |
    And subsequent predictions should demonstrate improved accuracy

  @future @device-agnostic @context-maintenance @ai-capability @ai-business-intelligence @persona-facilityman
  Scenario: Calculate ROI for maintenance strategies
    Given a facility with multiple devices of the same type
    And some devices follow preventive maintenance schedules
    And others follow reactive maintenance approaches
    When the business intelligence system compares maintenance outcomes
    Then it should calculate the ROI of preventive vs. reactive maintenance
    And it should quantify:
      | preventiveCosts     | Total costs of preventive maintenance     |
      | reactiveCosts       | Total costs of reactive maintenance       |
      | downtimeComparison  | Comparison of device downtime             |
      | reliabilityImpact   | Impact on overall device reliability      |
      | projectedSavings    | Projected savings from optimal strategy   |
    And it should recommend the most cost-effective maintenance strategy

  @future @device-agnostic @context-maintenance @ai-capability @ai-cross-device @persona-facilityman
  Scenario: Coordinate maintenance across multiple device types
    Given a facility with diverse device types
    And multiple devices require maintenance in the next month
    When the maintenance orchestration system analyzes the requirements
    Then it should generate an optimized maintenance schedule
    And the schedule should:
      | minimizeDowntime    | Group maintenance to reduce facility impact   |
      | optimizeTechnicianTime | Efficiently use technician availability     |
      | prioritizeCritical   | Address critical issues first                 |
      | groupSimilarTasks    | Combine similar maintenance tasks             |
    And it should provide a cost-benefit analysis of the optimized schedule
