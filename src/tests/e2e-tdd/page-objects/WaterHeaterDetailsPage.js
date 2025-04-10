/**
 * Page Object Model for the Water Heater Details page
 * Following Clean Architecture principles by abstracting UI interactions
 */
class WaterHeaterDetailsPage {
  /**
   * Navigate to a specific water heater's details page
   * @param {string} id - The water heater ID
   */
  visit(id) {
    cy.visit(`/water-heaters/${id}`);
    // Ensure the page is fully loaded
    this.getHeaterName().should('be.visible');
    return this;
  }

  /**
   * Get the water heater name element
   */
  getHeaterName() {
    return cy.get('[data-testid="heater-name"]');
  }

  /**
   * Get the water heater status element
   */
  getHeaterStatus() {
    return cy.get('[data-testid="heater-status"]');
  }

  /**
   * Navigate to a specific tab
   * @param {string} tabName - The name of the tab (e.g., 'operations', 'details', 'history')
   */
  selectTab(tabName) {
    cy.get(`[data-testid="${tabName}-tab"]`).click();
    // Verify the tab content is visible
    cy.get(`[data-testid="${tabName}-content"]`).should('be.visible');
    return this;
  }

  /**
   * Get the temperature gauge element
   */
  getTemperatureGauge() {
    return cy.get('[data-testid="temperature-gauge"]');
  }

  /**
   * Get the temperature value element
   */
  getTemperatureValue() {
    return cy.get('[data-testid="temperature-value"]');
  }

  /**
   * Get the temperature status element
   */
  getTemperatureStatus() {
    return cy.get('[data-testid="temperature-status"]');
  }

  /**
   * Click the adjust temperature button
   */
  clickAdjustTemperature() {
    cy.get('[data-testid="adjust-temperature-btn"]').click();
    // Verify the dialog appears
    cy.get('[data-testid="temperature-adjustment-dialog"]').should('be.visible');
    return this;
  }

  /**
   * Set a new target temperature
   * @param {number} temperature - The new target temperature
   */
  setTargetTemperature(temperature) {
    cy.get('[data-testid="target-temperature-input"]').clear().type(temperature.toString());
    return this;
  }

  /**
   * Confirm the temperature adjustment
   */
  confirmTemperatureAdjustment() {
    cy.get('[data-testid="confirm-adjustment-btn"]').click();
    // Verify the confirmation appears
    cy.get('[data-testid="adjustment-confirmation"]').should('be.visible');
    return this;
  }

  /**
   * Get the command status element
   */
  getCommandStatus() {
    return cy.get('[data-testid="command-status"]');
  }

  /**
   * Wait for the temperature adjustment to complete
   * @param {number} timeout - Maximum time to wait in milliseconds
   */
  waitForAdjustmentComplete(timeout = 15000) {
    this.getCommandStatus({ timeout }).should('contain', 'Temperature adjustment applied');
    return this;
  }

  /**
   * Perform a complete temperature adjustment
   * @param {number} temperature - The new target temperature
   */
  adjustTemperature(temperature) {
    this.clickAdjustTemperature()
        .setTargetTemperature(temperature)
        .confirmTemperatureAdjustment();
    return this;
  }
  /**
   * Get the temperature gauge element
   */
  getTemperatureGauge() {
    return cy.get('[data-testid="temperature-gauge"]');
  }

  /**
   * Get the current temperature value
   */
  getTemperatureValue() {
    return cy.get('[data-testid="temperature-value"]');
  }

  /**
   * Get the temperature status element
   */
  getTemperatureStatus() {
    return cy.get('[data-testid="temperature-status"]');
  }

  /**
   * Adjust the water heater temperature
   * @param {number} temperature - The target temperature to set
   */
  adjustTemperature(temperature) {
    cy.get('[data-testid="temperature-slider"]').invoke('val', temperature).trigger('change');
    cy.get('[data-testid="apply-temperature-button"]').click();
    return this;
  }

  /**
   * Get the command status element
   */
  getCommandStatus() {
    return cy.get('[data-testid="command-status"]');
  }

  /**
   * Wait for temperature adjustment to complete
   */
  waitForAdjustmentComplete() {
    cy.get('[data-testid="adjustment-in-progress"]', { timeout: 10000 }).should('not.exist');
    cy.get('[data-testid="adjustment-complete"]').should('be.visible');
    return this;
  }

  /**
   * Get the manufacturer information element
   */
  getManufacturerInfo() {
    return cy.get('[data-testid="manufacturer-info"]');
  }

  /**
   * Get the model information element
   */
  getModelInfo() {
    return cy.get('[data-testid="model-info"]');
  }

  /**
   * Get a specific specification value
   * @param {string} name - The specification name
   */
  getSpecification(name) {
    return cy.contains('[data-testid="spec-name"]', name)
      .parents('[data-testid="specification-item"]')
      .find('[data-testid="spec-value"]');
  }

  /**
   * Get emergency actions container
   */
  getEmergencyActions() {
    return cy.get('[data-testid="emergency-actions"]');
  }

  /**
   * Initiate emergency shutdown procedure
   */
  initiateEmergencyShutdown() {
    cy.get('[data-testid="emergency-shutdown-button"]').click();
    return this;
  }

  /**
   * Get confirmation dialog element
   */
  getConfirmationDialog() {
    return cy.get('[data-testid="confirmation-dialog"]');
  }

  /**
   * Confirm action in dialog
   */
  confirmAction() {
    cy.get('[data-testid="confirm-button"]').click();
    return this;
  }

  /**
   * Get action status element
   */
  getActionStatus() {
    return cy.get('[data-testid="action-status"]');
  }
}

export default new WaterHeaterDetailsPage();
