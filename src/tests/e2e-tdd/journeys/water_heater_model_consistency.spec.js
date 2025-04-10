/**
 * @file Water Heater Model Consistency E2E Test
 * @description Tests that all water heaters have consistent model information
 * @phase red - This test defines the expected behavior but will fail until implemented
 */

// Import page objects
import DashboardPage from '../page-objects/DashboardPage';
import WaterHeaterDetailsPage from '../page-objects/WaterHeaterDetailsPage';
import WaterHeaterListPage from '../page-objects/WaterHeaterListPage';

// @red - Test in RED phase of TDD cycle
describe('Water Heater Model Consistency Journey', () => {
  beforeEach(() => {
    // Load and use the facility manager fixture
    cy.fixture('users/facility_manager.json').as('user');
    cy.login('@user');
  });

  it('should verify all water heaters are AquaTherm models', () => {
    // ======= API VERIFICATION =======
    // First verify via API call that all heaters are AquaTherm models
    cy.request('/api/water-heaters/').then((response) => {
      expect(response.status).to.eq(200);
      expect(response.body).to.have.length.greaterThan(0);

      // All water heaters should be AquaTherm (Rheem) models
      const allAquaTherm = response.body.every(heater =>
        heater.manufacturer === 'AquaTherm' || heater.manufacturer === 'Rheem');
      expect(allAquaTherm).to.be.true;

      // Compare model numbers against known patterns
      const validModelPattern = /^(PR|HP|HE|EE)\d{4}/;
      const allValidModels = response.body.every(heater =>
        validModelPattern.test(heater.model));
      expect(allValidModels).to.be.true;
    });

    // ======= UI VERIFICATION =======
    // Navigate to the water heater list page
    WaterHeaterListPage.visit();

    // Verify water heaters are displayed
    WaterHeaterListPage.getWaterHeaterCards().should('be.visible');

    // Verify all displayed cards show AquaTherm/Rheem as manufacturer
    WaterHeaterListPage.getWaterHeaterCards().each(($card) => {
      cy.wrap($card).find('[data-testid="manufacturer-label"]')
        .should('contain.text', 'AquaTherm')
        .or('contain.text', 'Rheem');
    });

    // Click on the first water heater to view details
    WaterHeaterListPage.getWaterHeaterCards().first().click();

    // Verify details page shows consistent model information
    WaterHeaterDetailsPage.getManufacturerInfo()
      .should('contain.text', 'AquaTherm')
      .or('contain.text', 'Rheem');

    WaterHeaterDetailsPage.getModelInfo()
      .invoke('text')
      .should('match', /^(PR|HP|HE|EE)\d{4}/);

    // ======= MODEL SPECIFICATION VERIFICATION =======
    // Navigate to specifications tab
    WaterHeaterDetailsPage.selectTab('specifications');

    // Verify specifications are consistent with AquaTherm models
    WaterHeaterDetailsPage.getSpecification('Tank Material')
      .should('contain.text', 'Stainless Steel');

    WaterHeaterDetailsPage.getSpecification('Warranty')
      .should('contain.text', '10 year');
  });

  it('should verify water heater filtering works correctly for model types', () => {
    // ======= DASHBOARD FILTERING =======
    // Navigate to dashboard
    DashboardPage.visit();

    // Filter by model type "Performance"
    DashboardPage.filterByModelType('Performance');

    // Verify only Performance (PR) models are shown
    DashboardPage.getVisibleWaterHeaters().each(($heater) => {
      cy.wrap($heater).find('[data-testid="model-label"]')
        .invoke('text')
        .should('match', /^PR\d{4}/);
    });

    // Clear the filter
    DashboardPage.clearFilters();

    // Verify all water heaters are now shown
    DashboardPage.getWaterHeaterCount().then((totalCount) => {
      cy.get('[data-testid="water-heater-card"]').should('have.length', totalCount);
    });
  });
});
