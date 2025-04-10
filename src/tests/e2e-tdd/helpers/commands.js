/**
 * Custom Cypress commands for E2E testing
 * These commands help maintain clean tests that focus on business outcomes
 * rather than implementation details
 */

// Import page objects
import DashboardPage from '../page-objects/DashboardPage';
import WaterHeaterDetailsPage from '../page-objects/WaterHeaterDetailsPage';

/**
 * Command to log in a user
 * @param {string} userFixture - Path to the user fixture
 */
Cypress.Commands.add('login', (userFixture) => {
  // Get user data from fixture
  cy.get(userFixture).then((user) => {
    // Intercept API requests related to authentication
    cy.intercept('POST', '/api/auth/login', {
      statusCode: 200,
      body: {
        token: 'mock-jwt-token',
        user: user
      }
    }).as('loginRequest');

    // Store user in local storage as real app would
    window.localStorage.setItem('user', JSON.stringify(user));
    window.localStorage.setItem('token', 'mock-jwt-token');

    // Set auth header for all subsequent requests
    cy.wrap(user).as('currentUser');
  });
});

/**
 * Command to set up a test water heater with desired state
 * @param {string} waterHeaterFixture - Path to the water heater fixture
 */
Cypress.Commands.add('setupTestWaterHeater', (waterHeaterFixture) => {
  cy.get(waterHeaterFixture).then((waterHeater) => {
    // Intercept API requests for water heater list
    cy.intercept('GET', '/api/water-heaters', {
      statusCode: 200,
      body: [waterHeater]
    }).as('getWaterHeaters');

    // Intercept API requests for the specific water heater
    cy.intercept('GET', `/api/water-heaters/${waterHeater.id}`, {
      statusCode: 200,
      body: waterHeater
    }).as('getWaterHeaterDetails');

    // Intercept API requests for water heater operations
    cy.intercept('GET', `/api/water-heaters/${waterHeater.id}/operations`, {
      statusCode: 200,
      body: {
        temperature: waterHeater.telemetry.temperature,
        target_temperature: waterHeater.telemetry.target_temperature,
        heating_status: waterHeater.telemetry.heating_status,
        commands_history: []
      }
    }).as('getWaterHeaterOperations');

    // Store water heater for later use
    cy.wrap(waterHeater).as('testWaterHeater');
  });
});

/**
 * Command to navigate to the dashboard
 */
Cypress.Commands.add('goToDashboard', () => {
  DashboardPage.visit();
});

/**
 * Command to find a water heater with an issue
 */
Cypress.Commands.add('findWaterHeaterWithIssue', (status = 'warning') => {
  return DashboardPage.getAlertIndicators().filter(`.${status}`)
    .parents('[data-testid^="water-heater-"]')
    .first();
});

/**
 * Command to navigate to a water heater's details
 * @param {string} id - The water heater ID
 */
Cypress.Commands.add('goToWaterHeaterDetails', (id) => {
  WaterHeaterDetailsPage.visit(id);
});

/**
 * Command to select the operations tab
 */
Cypress.Commands.add('selectOperationsTab', () => {
  WaterHeaterDetailsPage.selectTab('operations');
});

/**
 * Command to adjust the water heater temperature
 * @param {number} temperature - The new target temperature
 */
Cypress.Commands.add('adjustTemperature', (temperature) => {
  // Intercept the temperature adjustment API request
  cy.get('@testWaterHeater').then((waterHeater) => {
    cy.intercept('POST', `/api/water-heaters/${waterHeater.id}/commands`, {
      statusCode: 200,
      body: {
        id: 'cmd-001',
        type: 'set_temperature',
        status: 'SENT',
        parameters: {
          temperature: temperature
        },
        timestamp: new Date().toISOString()
      }
    }).as('sendCommand');

    // Perform the temperature adjustment
    WaterHeaterDetailsPage.adjustTemperature(temperature);

    // Wait for the command to be sent
    cy.wait('@sendCommand');

    // Simulate command execution
    cy.wait(2000).then(() => {
      // Update command status to applied
      cy.intercept('GET', `/api/water-heaters/${waterHeater.id}/commands/cmd-001`, {
        statusCode: 200,
        body: {
          id: 'cmd-001',
          type: 'set_temperature',
          status: 'APPLIED',
          parameters: {
            temperature: temperature
          },
          timestamp: new Date().toISOString()
        }
      }).as('getCommandStatus');

      // Update the water heater telemetry
      const updatedWaterHeater = { ...waterHeater };
      updatedWaterHeater.telemetry.temperature = temperature;
      updatedWaterHeater.telemetry.target_temperature = temperature;

      // Update the water heater details response
      cy.intercept('GET', `/api/water-heaters/${waterHeater.id}`, {
        statusCode: 200,
        body: updatedWaterHeater
      }).as('getUpdatedWaterHeaterDetails');

      // Update the water heater operations response
      cy.intercept('GET', `/api/water-heaters/${waterHeater.id}/operations`, {
        statusCode: 200,
        body: {
          temperature: temperature,
          target_temperature: temperature,
          heating_status: 'IDLE',
          commands_history: [{
            id: 'cmd-001',
            type: 'set_temperature',
            status: 'APPLIED',
            parameters: {
              temperature: temperature
            },
            timestamp: new Date().toISOString()
          }]
        }
      }).as('getUpdatedWaterHeaterOperations');
    });
  });
});

/**
 * Command to verify a temperature adjustment was sent
 */
Cypress.Commands.add('verifyTemperatureAdjustmentSent', () => {
  WaterHeaterDetailsPage.getCommandStatus().should('contain', 'Temperature adjustment sent');
});

/**
 * Command to verify the status was updated
 * @param {string} status - The expected status text
 */
Cypress.Commands.add('verifyStatusUpdated', (status) => {
  WaterHeaterDetailsPage.getHeaterStatus().should('contain', status);
});
