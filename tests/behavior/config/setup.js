/**
 * IoTSphere BDD Test Setup
 *
 * This file configures the test environment for BDD tests.
 * It handles dependency injection, mocking, and any other setup needed
 * for the test environment.
 */

const { setWorldConstructor, setDefaultTimeout, After, Before } = require('@cucumber/cucumber');
const { mockDeviceRepository } = require('../support/mocks/device-repository.mock');
const { mockTelemetryService } = require('../support/mocks/telemetry-service.mock');
const { mockUserService } = require('../support/mocks/user-service.mock');
const { mockAnalyticsEngine } = require('../support/mocks/analytics-engine.mock');

/**
 * Custom world object that provides context for step definitions
 */
class IoTSphereWorld {
  constructor() {
    // Services used by step definitions
    this.deviceRepository = mockDeviceRepository();
    this.telemetryService = mockTelemetryService();
    this.userService = mockUserService();
    this.analyticsEngine = mockAnalyticsEngine();

    // Test context variables
    this.testContext = {
      authenticatedUser: null,
      currentDevice: null,
      deviceRegistrationData: null,
      commandResults: null,
      telemetryData: null,
      lastResponse: null,
      errors: []
    };
  }

  /**
   * Helper methods to make step definitions cleaner
   */
  async authenticateUser(role) {
    this.testContext.authenticatedUser = await this.userService.authenticate({ role });
    return this.testContext.authenticatedUser;
  }

  async registerDevice(deviceData) {
    try {
      this.testContext.deviceRegistrationData = deviceData;
      this.testContext.currentDevice = await this.deviceRepository.registerDevice(deviceData);
      return this.testContext.currentDevice;
    } catch (error) {
      this.testContext.errors.push(error);
      throw error;
    }
  }
}

// Configure cucumber
setWorldConstructor(IoTSphereWorld);
setDefaultTimeout(60 * 1000); // 60 seconds

// Reset test state before each scenario
Before(function() {
  // Clear any mocked data and reset state
  this.deviceRepository.reset();
  this.telemetryService.reset();
  this.userService.reset();
  this.analyticsEngine.reset();

  // Clear test context
  this.testContext = {
    authenticatedUser: null,
    currentDevice: null,
    deviceRegistrationData: null,
    commandResults: null,
    telemetryData: null,
    lastResponse: null,
    errors: []
  };
});

// Cleanup after each scenario
After(function() {
  // Any cleanup needed
});
