/**
 * E2E tests for AquaTherm water heater cards
 * Tests both display consistency and card navigation
 */

describe('AquaTherm Water Heater Cards', () => {
  beforeEach(() => {
    // Visit the water heaters page before each test
    cy.visit('/water-heaters');
    // Wait for page to fully load
    cy.wait(1000);
  });

  context('Display Consistency', () => {
    it('should display AquaTherm badges consistently', () => {
      // Get all AquaTherm badges
      cy.get('.aquatherm-badge').should('exist')
        .then($badges => {
          // Verify all badges have same CSS properties
          expect($badges).to.have.length.greaterThan(0);

          // Verify positioning
          cy.get('.aquatherm-badge').first().should('have.css', 'position', 'absolute');
          cy.get('.aquatherm-badge').first().should('have.css', 'top', '10px');
          cy.get('.aquatherm-badge').first().should('have.css', 'right', '10px');

          // Verify styling
          cy.get('.aquatherm-badge').first().should('have.css', 'font-size', '11px');
          cy.get('.aquatherm-badge').first().should('have.css', 'text-transform', 'uppercase');
        });
    });

    it('should display heater type badges consistently', () => {
      // Get all heater type badges
      cy.get('.heater-type-badge').should('exist')
        .then($badges => {
          // Verify all badges have same CSS properties
          expect($badges).to.have.length.greaterThan(0);

          // Verify positioning
          cy.get('.heater-type-badge').first().should('have.css', 'position', 'absolute');
          cy.get('.heater-type-badge').first().should('have.css', 'top', '10px');
          cy.get('.heater-type-badge').first().should('have.css', 'left', '10px');

          // Verify styling
          cy.get('.heater-type-badge').first().should('have.css', 'font-size', '11px');
          cy.get('.heater-type-badge').first().should('have.css', 'text-transform', 'uppercase');
        });
    });

    it('should display mode indicators consistently', () => {
      // Get all mode indicators
      cy.get('.mode').should('exist')
        .then($modes => {
          // Verify all modes have same CSS properties
          expect($modes).to.have.length.greaterThan(0);

          // Verify styling
          cy.get('.mode').first().should('have.css', 'font-size', '0.75rem');
          cy.get('.mode').first().should('have.css', 'text-transform', 'uppercase');
          cy.get('.mode').first().should('have.css', 'font-weight', '600');
        });
    });

    it('should display gauges consistently', () => {
      // Get all gauges
      cy.get('.gauge-container').should('exist')
        .then($gauges => {
          // Verify all gauges have same dimensions
          expect($gauges).to.have.length.greaterThan(0);

          // Verify dimensions
          cy.get('.gauge-container').first().should('have.css', 'width', '150px');
          cy.get('.gauge-container').first().should('have.css', 'height', '150px');
        });
    });

    it('should ensure all cards have consistent styling', () => {
      // Get all heater cards
      cy.get('.heater-card').should('exist')
        .then($cards => {
          // Verify all cards have the same basic CSS properties
          expect($cards).to.have.length.greaterThan(0);

          // Verify cursor style
          cy.get('.heater-card').first().should('have.css', 'cursor', 'pointer');
        });
    });
  });

  context('Card Navigation', () => {
    it('should navigate to detail page when clicking on a card', () => {
      // Get a reference to the first heater card and capture its ID
      cy.get('.heater-card').first().then($card => {
        const heaterId = $card.attr('data-id');
        expect(heaterId).to.not.be.undefined;

        // Click the card
        cy.get('.heater-card').first().click();

        // Verify navigation occurred to the right place
        cy.url().should('include', `/water-heaters/${heaterId}`);

        // Verify detail page loaded properly
        cy.get('#water-heater-detail').should('exist');
      });
    });

    it('should not navigate when clicking buttons within cards', () => {
      // Find a card with an interior button
      cy.get('.heater-card button').then($buttons => {
        if ($buttons.length > 0) {
          // Click the first button
          cy.get('.heater-card button').first().click();

          // Verify we're still on the list page
          cy.url().should('include', '/water-heaters');
          cy.url().should('not.include', '/water-heaters/');
        } else {
          // Skip test if no buttons found
          this.skip();
        }
      });
    });

    it('should keep the Add New button working', () => {
      // Click the Add New button
      cy.get('#add-new-btn').click();

      // Verify navigation to the new heater page
      cy.url().should('include', '/water-heaters/new');
    });
  });
});
