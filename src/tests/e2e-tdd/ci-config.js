/**
 * CI Configuration for End-to-End Tests
 *
 * This file configures how E2E tests are run in the CI/CD pipeline
 * following our TDD principles and Clean Architecture.
 */

const { defineConfig } = require('cypress');

module.exports = defineConfig({
  // Base configuration
  e2e: {
    baseUrl: 'http://localhost:8006', // Will be overridden by CI environment variables
    specPattern: 'src/tests/e2e-tdd/journeys/**/*.spec.js',
    supportFile: 'src/tests/e2e-tdd/helpers/commands.js',
    viewportWidth: 1280,
    viewportHeight: 800,
    video: true,
    screenshotOnRunFailure: true,
    trashAssetsBeforeRuns: true,
  },

  // Environment variables specific to different TDD phases
  env: {
    // Default is the RED phase
    tddPhase: 'red',

    // Phase-specific configuration
    phaseConfig: {
      red: {
        // In RED phase, we expect tests to fail
        failOnStatusCode: false,
        // Allow uncaught exceptions in RED phase since implementation is incomplete
        uncaughtExceptionMode: 'warn',
      },
      green: {
        // In GREEN phase, we expect minimum implementation and tests to pass
        failOnStatusCode: true,
        // No uncaught exceptions allowed in GREEN phase
        uncaughtExceptionMode: 'fail',
      },
      refactor: {
        // In REFACTOR phase, all tests must pass with improved implementation
        failOnStatusCode: true,
        // No uncaught exceptions allowed in REFACTOR phase
        uncaughtExceptionMode: 'fail',
        // Enable code coverage in REFACTOR phase
        codeCoverage: true,
      },
    },
  },

  // Different project configurations for each TDD phase
  // This allows running specific phases in CI
  projectId: 'iotsphere-e2e',
  projects: [
    {
      name: 'red',
      testingType: 'e2e',
      env: {
        tddPhase: 'red',
        grepTags: '@red',
      },
    },
    {
      name: 'green',
      testingType: 'e2e',
      env: {
        tddPhase: 'green',
        grepTags: '@green',
      },
    },
    {
      name: 'refactor',
      testingType: 'e2e',
      env: {
        tddPhase: 'refactor',
        grepTags: '@refactor',
      },
    },
  ],

  // Reporter configuration for CI integration
  reporter: 'junit',
  reporterOptions: {
    mochaFile: 'results/e2e-tdd-[hash].xml',
    toConsole: true,
  },
});
