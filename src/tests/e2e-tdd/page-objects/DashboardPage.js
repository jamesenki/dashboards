/**
 * Page Object Model for the Dashboard page
 * Following Clean Architecture principles by abstracting UI interactions
 */
class DashboardPage {
  /**
   * Navigate to the dashboard
   */
  visit() {
    cy.visit('/dashboard');
    // Ensure the page is fully loaded
    this.getWaterHeaterList().should('be.visible');
    return this;
  }

  /**
   * Get the water heater list container
   */
  getWaterHeaterList() {
    return cy.get('[data-testid="water-heater-list"]');
  }

  /**
   * Get a specific water heater by ID
   * @param {string} id - The water heater ID
   */
  getWaterHeaterById(id) {
    return cy.get(`[data-testid="water-heater-${id}"]`);
  }

  /**
   * Get alert indicators on the dashboard
   */
  getAlertIndicators() {
    return cy.get('[data-testid="alert-indicator"]');
  }

  /**
   * Check if there are any water heaters with the specified status
   * @param {string} status - The status to check for (e.g., 'warning', 'error')
   */
  hasWaterHeatersWithStatus(status) {
    return this.getAlertIndicators().filter(`.${status}`).its('length').then(length => length > 0);
  }

  /**
   * Select a water heater with an issue (alert status)
   * @param {string} status - The status to look for (e.g., 'warning', 'error')
   */
  selectWaterHeaterWithIssue(status = 'warning') {
    // Find a water heater with the specified status and click on it
    cy.get(`[data-testid="alert-indicator"].${status}`)
      .parents('[data-testid^="water-heater-"]')
      .first()
      .click();

    // Verify we're on the details page
    cy.url().should('include', '/water-heaters/');

    return this;
  }

  /**
   * Filter water heaters by various criteria
   * @param {string} filterType - The type of filter (e.g., 'manufacturer', 'status')
   * @param {string} value - The value to filter by
   */
  filterBy(filterType, value) {
    cy.get(`[data-testid="filter-${filterType}"]`).click();
    cy.get(`[data-testid="filter-option-${value}"]`).click();
    return this;
  }

  /**
   * Clear all active filters
   */
  clearFilters() {
    cy.get('[data-testid="clear-filters"]').click();
    return this;
  }

  /**
   * Get all visible water heaters on the current page
   */
  getVisibleWaterHeaters() {
    return cy.get('[data-testid="water-heater-card"]:visible');
  }

  /**
   * Get the total count of water heaters
   */
  getWaterHeaterCount() {
    return cy.get('[data-testid="water-heater-count"]')
      .invoke('text')
      .then(text => {
        const match = text.match(/Total: (\d+)/);
        return match ? parseInt(match[1]) : 0;
      });
  }

  /**
   * Get alert notifications panel
   */
  getAlertNotifications() {
    return cy.get('[data-testid="alert-notifications"]');
  }

  /**
   * Filter water heaters by model type
   * @param {string} modelType - The model type to filter by
   */
  filterByModelType(modelType) {
    return this.filterBy('model-type', modelType);
  }

  /**
   * Select the maintenance tab in the dashboard
   */
  selectMaintenanceTab() {
    cy.get('[data-testid="maintenance-tab"]').click();
    cy.get('[data-testid="maintenance-content"]').should('be.visible');
    return this;
  }

  /**
   * Get the predictive analytics section
   */
  getPredictiveAnalyticsSection() {
    return cy.get('[data-testid="predictive-analytics-section"]');
  }

  /**
   * Get water heaters that need maintenance
   */
  getWaterHeatersNeedingMaintenance() {
    return cy.get('[data-testid="maintenance-needed-item"]');
  }

  /**
   * Select a water heater for maintenance by index
   * @param {number} index - The index of the water heater in the list
   */
  selectWaterHeaterForMaintenance(index) {
    this.getWaterHeatersNeedingMaintenance().eq(index).click();
    return this;
  }

  /**
   * Get maintenance recommendation details
   */
  getMaintenanceRecommendation() {
    return cy.get('[data-testid="maintenance-recommendation"]');
  }

  /**
   * Open the maintenance scheduler
   */
  openMaintenanceScheduler() {
    cy.get('[data-testid="schedule-maintenance-button"]').click();
    cy.get('[data-testid="maintenance-scheduler"]').should('be.visible');
    return this;
  }

  /**
   * Select a maintenance date
   * @param {string} dateOption - The date option (e.g., 'next-week', 'next-month')
   */
  selectMaintenanceDate(dateOption) {
    cy.get(`[data-testid="date-option-${dateOption}"]`).click();
    return this;
  }

  /**
   * Select a maintenance technician
   * @param {string} techName - The technician name
   */
  selectMaintenanceTechnician(techName) {
    cy.get('[data-testid="technician-dropdown"]').click();
    cy.contains('[data-testid="technician-option"]', techName).click();
    return this;
  }

  /**
   * Schedule the maintenance task
   */
  scheduleMaintenanceTask() {
    cy.get('[data-testid="confirm-schedule-button"]').click();
    return this;
  }

  /**
   * Get the schedule confirmation message
   */
  getScheduleConfirmation() {
    return cy.get('[data-testid="schedule-confirmation"]');
  }
}

export default new DashboardPage();
