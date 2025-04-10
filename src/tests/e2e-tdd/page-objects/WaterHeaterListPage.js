/**
 * Page Object Model for the Water Heater List page
 * Following Clean Architecture principles by abstracting UI interactions
 */
class WaterHeaterListPage {
  /**
   * Navigate to the water heater list page
   */
  visit() {
    cy.visit('/water-heaters');
    // Ensure the page is fully loaded
    this.getWaterHeaterCards().should('be.visible');
    return this;
  }

  /**
   * Get all water heater cards
   */
  getWaterHeaterCards() {
    return cy.get('[data-testid="water-heater-card"]');
  }

  /**
   * Get a specific water heater by ID
   * @param {string} id - The water heater ID
   */
  getWaterHeaterById(id) {
    return cy.get(`[data-testid="water-heater-${id}"]`);
  }

  /**
   * Filter water heaters by manufacturer
   * @param {string} manufacturer - The manufacturer name
   */
  filterByManufacturer(manufacturer) {
    cy.get('[data-testid="manufacturer-filter"]').click();
    cy.get(`[data-testid="manufacturer-option-${manufacturer}"]`).click();
    return this;
  }

  /**
   * Filter water heaters by model type
   * @param {string} modelType - The model type
   */
  filterByModelType(modelType) {
    cy.get('[data-testid="model-type-filter"]').click();
    cy.get(`[data-testid="model-type-option-${modelType}"]`).click();
    return this;
  }

  /**
   * Clear all applied filters
   */
  clearFilters() {
    cy.get('[data-testid="clear-filters-button"]').click();
    return this;
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
   * Sort water heaters by the specified criteria
   * @param {string} sortCriteria - The sort criteria (e.g., 'name', 'temperature', 'status')
   */
  sortBy(sortCriteria) {
    cy.get(`[data-testid="sort-by-${sortCriteria}"]`).click();
    return this;
  }
}

export default new WaterHeaterListPage();
