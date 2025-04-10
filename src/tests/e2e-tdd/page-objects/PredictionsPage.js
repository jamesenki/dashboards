/**
 * Page Object Model for the Water Heater Predictions tab
 * Following Clean Architecture principles by abstracting UI interactions
 */
class PredictionsPage {
  /**
   * Get the main predictions content container
   */
  getPredictionsContent() {
    return cy.get('[data-testid="predictions-content"]');
  }

  /**
   * Get the lifespan prediction section
   */
  getLifespanPrediction() {
    return cy.get('[data-testid="lifespan-prediction-section"]');
  }

  /**
   * Get the remaining days element from lifespan prediction
   */
  getLifespanRemainingDays() {
    return cy.get('[data-testid="lifespan-remaining-days"]');
  }

  /**
   * Get the confidence level element from lifespan prediction
   */
  getLifespanConfidence() {
    return cy.get('[data-testid="lifespan-confidence"]');
  }

  /**
   * Get the anomaly detection section
   */
  getAnomalyDetection() {
    return cy.get('[data-testid="anomaly-detection-section"]');
  }

  /**
   * Get the anomaly list element
   */
  getAnomalyList() {
    return cy.get('[data-testid="anomaly-list"]');
  }

  /**
   * Get the usage patterns section
   */
  getUsagePatterns() {
    return cy.get('[data-testid="usage-patterns-section"]');
  }

  /**
   * Get the usage pattern chart element
   */
  getUsagePatternChart() {
    return cy.get('[data-testid="usage-pattern-chart"]');
  }

  /**
   * Get the multi-factor analysis section
   */
  getMultiFactorAnalysis() {
    return cy.get('[data-testid="multi-factor-section"]');
  }

  /**
   * Get the maintenance recommendation element
   */
  getMaintenanceRecommendation() {
    return cy.get('[data-testid="maintenance-recommendation"]');
  }

  /**
   * Click the refresh button for predictions
   */
  clickRefreshButton() {
    cy.get('[data-testid="refresh-predictions-btn"]').click();
    return this;
  }

  /**
   * Get the refresh indicator (loading spinner) element
   */
  getRefreshIndicator() {
    return cy.get('[data-testid="predictions-loading"]');
  }

  /**
   * Expand the recommendation details panel
   */
  expandRecommendationDetails() {
    cy.get('[data-testid="expand-recommendation-btn"]').click();
    return this;
  }

  /**
   * Get the recommendation details panel
   */
  getRecommendationDetails() {
    return cy.get('[data-testid="recommendation-details"]');
  }

  /**
   * Get the schedule maintenance button
   */
  getScheduleMaintenanceButton() {
    return cy.get('[data-testid="schedule-maintenance-btn"]');
  }

  /**
   * Get the dismiss recommendation button
   */
  getDismissRecommendationButton() {
    return cy.get('[data-testid="dismiss-recommendation-btn"]');
  }

  /**
   * Click the schedule maintenance button
   */
  clickScheduleMaintenanceButton() {
    this.getScheduleMaintenanceButton().click();
    return this;
  }

  /**
   * Get the maintenance scheduling dialog
   */
  getMaintenanceSchedulingDialog() {
    return cy.get('[data-testid="maintenance-scheduling-dialog"]');
  }

  /**
   * Select a maintenance date
   * @param {string} option - The date option to select (e.g., 'next-available', 'specific-date')
   */
  selectMaintenanceDate(option) {
    cy.get(`[data-testid="${option}-option"]`).click();
    return this;
  }

  /**
   * Confirm the maintenance scheduling
   */
  confirmMaintenanceScheduling() {
    cy.get('[data-testid="confirm-scheduling-btn"]').click();
    return this;
  }

  /**
   * Get the confirmation message
   */
  getConfirmationMessage() {
    return cy.get('[data-testid="confirmation-message"]');
  }
}

export default new PredictionsPage();
