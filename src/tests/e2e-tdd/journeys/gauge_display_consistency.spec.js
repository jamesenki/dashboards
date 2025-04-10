/**
 * @file Gauge Display Consistency E2E Test
 * @description Tests that gauge displays are consistent and properly rendered
 * @phase red - This test defines the expected behavior but will fail until implemented
 */

// Import page objects
import WaterHeaterListPage from '../page-objects/WaterHeaterListPage';
import WaterHeaterDetailsPage from '../page-objects/WaterHeaterDetailsPage';

// @red - Test in RED phase of TDD cycle
describe('Water Heater Gauge Display Consistency Journey', () => {
  beforeEach(() => {
    // Load and use the facility manager fixture
    cy.fixture('users/facility_manager.json').as('user');
    cy.login('@user');
  });

  it('should display gauges with proper scaling and orientation', () => {
    // ======= LIST PAGE GAUGES =======
    // Navigate to the water heaters list page
    WaterHeaterListPage.visit();

    // Ensure water heater cards are visible
    WaterHeaterListPage.getWaterHeaterCards().should('be.visible');

    // Verify temperature gauges on list page
    cy.get('[data-testid="temperature-gauge"]').each(($gauge) => {
      // Verify gauge elements exist and have proper attributes
      cy.wrap($gauge).should('have.attr', 'aria-valuemin', '0');
      cy.wrap($gauge).should('have.attr', 'aria-valuemax', '100');

      // Get the current value and verify it's within valid range
      cy.wrap($gauge).invoke('attr', 'aria-valuenow').then(value => {
        const numValue = Number(value);
        expect(numValue).to.be.at.least(0);
        expect(numValue).to.be.at.most(100);
      });

      // Verify the gauge has proper style attributes
      cy.wrap($gauge).should('have.css', 'height').and('not.equal', '0px');
      cy.wrap($gauge).should('have.css', 'width').and('not.equal', '0px');
    });

    // ======= DETAILS PAGE GAUGES =======
    // Navigate to the first water heater details page
    WaterHeaterListPage.getWaterHeaterCards().first().click();

    // Verify we're on the details page
    WaterHeaterDetailsPage.getHeaterName().should('be.visible');

    // Navigate to the operations tab where gauges are displayed
    WaterHeaterDetailsPage.selectTab('operations');

    // Verify main temperature gauge
    WaterHeaterDetailsPage.getTemperatureGauge()
      .should('be.visible')
      .and('have.attr', 'aria-valuemin')
      .and('have.attr', 'aria-valuemax');

    // Verify gauge size is appropriate
    WaterHeaterDetailsPage.getTemperatureGauge()
      .should('have.css', 'height').and('not.equal', '0px');

    // Verify gauge has appropriate labels
    cy.get('[data-testid="gauge-min-label"]').should('be.visible');
    cy.get('[data-testid="gauge-max-label"]').should('be.visible');
    cy.get('[data-testid="gauge-current-value"]').should('be.visible');
  });

  it('should have consistent gauge colors and backgrounds', () => {
    // Navigate to water heater details page
    WaterHeaterListPage.visit();
    WaterHeaterListPage.getWaterHeaterCards().first().click();
    WaterHeaterDetailsPage.selectTab('operations');

    // Check normal temperature gauge color (expected to be green)
    cy.window().then(win => {
      cy.fixture('gauge_thresholds').then((thresholds) => {
        // Get the current temperature value
        WaterHeaterDetailsPage.getTemperatureValue().invoke('text').then((text) => {
          const temp = parseFloat(text);

          // Verify gauge color matches temperature state
          if (temp < thresholds.temperature.low) {
            // Too cold - should be blue
            WaterHeaterDetailsPage.getTemperatureGauge()
              .should('have.class', 'gauge-cold')
              .or('have.css', 'color', 'rgb(0, 0, 255)'); // Blue
          } else if (temp > thresholds.temperature.high) {
            // Too hot - should be red
            WaterHeaterDetailsPage.getTemperatureGauge()
              .should('have.class', 'gauge-hot')
              .or('have.css', 'color', 'rgb(255, 0, 0)'); // Red
          } else {
            // Normal - should be green
            WaterHeaterDetailsPage.getTemperatureGauge()
              .should('have.class', 'gauge-normal')
              .or('have.css', 'color', 'rgb(0, 128, 0)'); // Green
          }
        });
      });
    });

    // Check gauge backgrounds are consistent
    cy.get('[data-testid="gauge-background"]').each(($bg) => {
      // Background should be semi-transparent or consistent with design system
      cy.wrap($bg).should('have.css', 'background-color')
        .and('match', /rgba\(\d+, \d+, \d+, 0\.\d+\)/); // Semi-transparent background
    });

    // Check all gauges use the same styling pattern
    cy.get('[data-testid^="gauge-"]').then(($gauges) => {
      const firstGaugeClass = $gauges.first().attr('class');

      // All gauges should share a common class structure
      $gauges.each((i, gauge) => {
        const gaugeClass = Cypress.$(gauge).attr('class');
        // Should have some common class
        expect(gaugeClass).to.include('gauge-');
      });
    });
  });

  it('should maintain gauge accuracy when window is resized', () => {
    // Navigate to water heater details page
    WaterHeaterListPage.visit();
    WaterHeaterListPage.getWaterHeaterCards().first().click();
    WaterHeaterDetailsPage.selectTab('operations');

    // Get initial gauge values
    WaterHeaterDetailsPage.getTemperatureValue().invoke('text').then((initialText) => {
      const initialTemp = parseFloat(initialText);

      // Resize the viewport to mobile size
      cy.viewport('iphone-6');

      // Verify gauge still shows the same value
      WaterHeaterDetailsPage.getTemperatureValue().invoke('text').then((resizedText) => {
        const resizedTemp = parseFloat(resizedText);
        expect(resizedTemp).to.equal(initialTemp);
      });

      // Verify gauge is still visible and properly scaled
      WaterHeaterDetailsPage.getTemperatureGauge()
        .should('be.visible')
        .and('have.css', 'height').and('not.equal', '0px');

      // Return to desktop size
      cy.viewport(1280, 720);
    });
  });
});
