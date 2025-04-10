const { defineConfig } = require('cypress');

module.exports = defineConfig({
  e2e: {
    specPattern: 'src/tests/e2e-tdd/journeys/**/*.spec.js',
    supportFile: 'src/tests/e2e-tdd/helpers/commands.js',
    baseUrl: 'http://localhost:8006',
    viewportWidth: 1280,
    viewportHeight: 800,
    defaultCommandTimeout: 15000,
    video: true,
    screenshotOnRunFailure: true,
    setupNodeEvents(on, config) {
      // Register shadow tasks for E2E testing of real-time updates
      const { registerShadowTasks } = require('./cypress/plugins/shadow_tasks');
      registerShadowTasks(on);
      
      // Return configuration
      return config;
    },
  },
  env: {
    // Default to the GREEN phase since we're testing implementation
    tddPhase: 'green',
    phaseConfig: {
      green: {
        // In GREEN phase, we expect tests to pass
        failOnStatusCode: true,
        // No uncaught exceptions allowed in GREEN phase
        uncaughtExceptionMode: 'fail',
      }
    }
  }
});
