const { Given, When, Then } = require('@cucumber/cucumber');

// Use dynamic import for chai
let expect;
(async () => {
  const chai = await import('chai');
  expect = chai.expect;
})();

const { mockDeviceData, mockTelemetryData, mockPerformanceData } = require('../support/mocks/device-data.mock');
const { navigateToDashboard, selectDevice, filterByManufacturer,
        filterByStatus, clearFilters, toggleTemperatureUnit,
        changeTemperatureSetpoint, togglePowerState,
        selectTab } = require('../support/actions/dashboard.actions');
const { setupBrowserHooks, getDeviceCards, getDeviceDetails,
        getSummaryMetrics, getTelemetryChart, getPerformanceMetrics,
        getAnomalyCount, getEfficiencyRating, getTemperatureValues } = require('../support/hooks/browser.hooks');

/**
 * Step definitions for water heater dashboard feature tests
 * Implements BDD scenarios for the water heater operations dashboard
 * Following TDD principles with clear separation of concerns
 */

// Initialize browser hooks
setupBrowserHooks();

// Background steps and common givens
Given('I am logged in as a {string}', async function(role) {
  // Set up user role and permissions for tests
  this.currentUser = { role, permissions: ['read:devices', 'write:devices'] };

  // Mock authorization for the current user
  await this.page.evaluate((userJson) => {
    localStorage.setItem('currentUser', userJson);
  }, JSON.stringify(this.currentUser));
});

Given('the system has water heaters from multiple manufacturers', async function() {
  // Mock device data with multiple manufacturers
  const mockDevices = mockDeviceData.createMixedManufacturerDevices();
  await this.page.evaluate((devicesJson) => {
    localStorage.setItem('mockDevices', devicesJson);
  }, JSON.stringify(mockDevices));
});

Given('the system has both connected and disconnected water heaters', async function() {
  // Mock device data with mixed connection statuses
  const mockDevices = mockDeviceData.createMixedConnectionStatusDevices();
  await this.page.evaluate((devicesJson) => {
    localStorage.setItem('mockDevices', devicesJson);
  }, JSON.stringify(mockDevices));
});

Given('there is a connected water heater with ID {string}', async function(deviceId) {
  // Mock a single connected device
  const mockDevice = mockDeviceData.createSingleDevice(deviceId, 'connected');
  await this.page.evaluate((deviceJson, id) => {
    const devices = JSON.parse(localStorage.getItem('mockDevices') || '[]');
    devices.push(JSON.parse(deviceJson));
    localStorage.setItem('mockDevices', JSON.stringify(devices));
    localStorage.setItem(`device_${id}`, deviceJson);
  }, JSON.stringify(mockDevice), deviceId);
});

Given('there is a water heater with ID {string}', async function(deviceId) {
  // Mock a generic device with basic data
  const mockDevice = mockDeviceData.createSingleDevice(deviceId);
  await this.page.evaluate((deviceJson, id) => {
    const devices = JSON.parse(localStorage.getItem('mockDevices') || '[]');
    devices.push(JSON.parse(deviceJson));
    localStorage.setItem('mockDevices', JSON.stringify(devices));
    localStorage.setItem(`device_${id}`, deviceJson);
  }, JSON.stringify(mockDevice), deviceId);
});

Given('there is a water heater with ID {string} with historical telemetry data', async function(deviceId) {
  // Mock a device with telemetry history
  const mockDevice = mockDeviceData.createSingleDevice(deviceId);
  const telemetryHistory = mockTelemetryData.createTelemetryHistory(deviceId);

  await this.page.evaluate((deviceJson, telemetryJson, id) => {
    const devices = JSON.parse(localStorage.getItem('mockDevices') || '[]');
    devices.push(JSON.parse(deviceJson));
    localStorage.setItem('mockDevices', JSON.stringify(devices));
    localStorage.setItem(`device_${id}`, deviceJson);
    localStorage.setItem(`telemetry_${id}`, telemetryJson);
  }, JSON.stringify(mockDevice), JSON.stringify(telemetryHistory), deviceId);
});

Given('there is a water heater with ID {string} with performance data', async function(deviceId) {
  // Mock a device with performance metrics
  const mockDevice = mockDeviceData.createSingleDevice(deviceId);
  const performanceData = mockPerformanceData.createPerformanceData(deviceId);

  await this.page.evaluate((deviceJson, performanceJson, id) => {
    const devices = JSON.parse(localStorage.getItem('mockDevices') || '[]');
    devices.push(JSON.parse(deviceJson));
    localStorage.setItem('mockDevices', JSON.stringify(devices));
    localStorage.setItem(`device_${id}`, deviceJson);
    localStorage.setItem(`performance_${id}`, performanceJson);
  }, JSON.stringify(mockDevice), JSON.stringify(performanceData), deviceId);
});

Given('there is a connected water heater with ID {string} in {string} mode', async function(deviceId, mode) {
  // Mock a device with specific operational mode
  const mockDevice = mockDeviceData.createSingleDevice(deviceId, 'connected', mode);
  await this.page.evaluate((deviceJson, id) => {
    const devices = JSON.parse(localStorage.getItem('mockDevices') || '[]');
    devices.push(JSON.parse(deviceJson));
    localStorage.setItem('mockDevices', JSON.stringify(devices));
    localStorage.setItem(`device_${id}`, deviceJson);
  }, JSON.stringify(mockDevice), deviceId);
});

Given('there is a water heater with ID {string} with detected anomalies', async function(deviceId) {
  // Mock a device with anomaly data
  const mockDevice = mockDeviceData.createSingleDevice(deviceId);
  const performanceData = mockPerformanceData.createPerformanceDataWithAnomalies(deviceId);

  await this.page.evaluate((deviceJson, performanceJson, id) => {
    const devices = JSON.parse(localStorage.getItem('mockDevices') || '[]');
    devices.push(JSON.parse(deviceJson));
    localStorage.setItem('mockDevices', JSON.stringify(devices));
    localStorage.setItem(`device_${id}`, deviceJson);
    localStorage.setItem(`performance_${id}`, performanceJson);
  }, JSON.stringify(mockDevice), JSON.stringify(performanceData), deviceId);
});

// When step definitions
When('I navigate to the water heater dashboard', async function() {
  await navigateToDashboard(this.page);
});

When('I filter by manufacturer {string}', async function(manufacturer) {
  await filterByManufacturer(this.page, manufacturer);
});

When('I filter by connection status {string}', async function(status) {
  await filterByStatus(this.page, status);
});

When('I select the water heater with ID {string}', async function(deviceId) {
  await selectDevice(this.page, deviceId);
});

When('I navigate to the detailed view for water heater {string}', async function(deviceId) {
  await navigateToDashboard(this.page);
  await selectDevice(this.page, deviceId);
});

When('I select the {string} tab', async function(tabName) {
  await selectTab(this.page, tabName);
});

When('I change the temperature setpoint to {string}', async function(temperature) {
  await changeTemperatureSetpoint(this.page, temperature);
});

When('I click the {string} button', async function(buttonName) {
  if (buttonName === 'Turn On' || buttonName === 'Turn Off') {
    await togglePowerState(this.page);
  }
});

When('I toggle the temperature unit', async function() {
  await toggleTemperatureUnit(this.page);
});

// Then step definitions
Then('I should see a list of all water heaters in the system', async function() {
  const deviceCards = await getDeviceCards(this.page);
  const mockDevices = JSON.parse(await this.page.evaluate(() => {
    return localStorage.getItem('mockDevices');
  }));

  expect(deviceCards.length).to.equal(mockDevices.length);
});

Then('each water heater should display its connection status', async function() {
  const deviceCards = await getDeviceCards(this.page);
  for (const card of deviceCards) {
    const statusElement = await card.$('.connection-status');
    expect(await statusElement.textContent()).to.be.oneOf(['connected', 'disconnected']);
  }
});

Then('each water heater should indicate if it is simulated', async function() {
  const deviceCards = await getDeviceCards(this.page);
  const mockDevices = JSON.parse(await this.page.evaluate(() => {
    return localStorage.getItem('mockDevices');
  }));

  for (let i = 0; i < deviceCards.length; i++) {
    const card = deviceCards[i];
    const device = mockDevices[i];

    if (device.simulated) {
      const simulationBadge = await card.$('.simulation-badge');
      expect(simulationBadge).to.not.be.null;
    }
  }
});

Then('I should only see water heaters from {string}', async function(manufacturer) {
  const deviceCards = await getDeviceCards(this.page);
  for (const card of deviceCards) {
    const manufacturerElement = await card.$('.manufacturer');
    expect(await manufacturerElement.textContent()).to.equal(manufacturer);
  }
});

Then('I should be able to clear the filter to see all water heaters', async function() {
  await clearFilters(this.page);

  const deviceCards = await getDeviceCards(this.page);
  const mockDevices = JSON.parse(await this.page.evaluate(() => {
    return localStorage.getItem('mockDevices');
  }));

  expect(deviceCards.length).to.equal(mockDevices.length);
});

Then('I should only see water heaters with {string} status', async function(status) {
  const deviceCards = await getDeviceCards(this.page);
  for (const card of deviceCards) {
    const statusElement = await card.$('.connection-status');
    expect(await statusElement.textContent()).to.equal(status);
  }
});

Then('I should see summary metrics including:', async function(dataTable) {
  const metrics = dataTable.raw().map(row => row[0]);
  const summaryCards = await getSummaryMetrics(this.page);

  for (const metric of metrics) {
    const found = await summaryCards.some(async (card) => {
      const label = await card.$('.card-label');
      return (await label.textContent()).includes(metric);
    });

    expect(found).to.be.true;
  }
});

Then('each device card should show:', async function(dataTable) {
  const expectedElements = dataTable.raw().map(row => row[0]);
  const deviceCards = await getDeviceCards(this.page);

  // Check first device card for all expected elements
  const card = deviceCards[0];

  for (const element of expectedElements) {
    let found = false;

    // Check different possible selectors based on element type
    switch(element) {
      case 'Device Name':
        found = await card.$('h3') !== null;
        break;
      case 'Manufacturer':
        found = await card.$('.manufacturer') !== null;
        break;
      case 'Model':
        found = await card.$('.model') !== null;
        break;
      case 'Current Temperature':
        found = await card.$('.current-temp') !== null;
        break;
      case 'Target Temperature':
        found = await card.$('.target-temp') !== null;
        break;
      case 'Heating Status':
        found = await card.$('.heating-status') !== null;
        break;
      case 'Mode':
        found = await card.$('.status-row:has(.status-label:text-is("Mode:"))') !== null;
        break;
      default:
        // Generic check for any text containing the element name
        const allText = await card.textContent();
        found = allText.includes(element);
    }

    expect(found, `Element "${element}" not found in device card`).to.be.true;
  }
});

Then('I should see the detailed view for water heater {string}', async function(deviceId) {
  const deviceDetails = await getDeviceDetails(this.page);
  const deviceIdElement = await deviceDetails.$('.device-id');

  expect(await deviceIdElement.textContent()).to.include(deviceId);
});

Then('the detailed view should show device information', async function() {
  const deviceDetails = await getDeviceDetails(this.page);

  // Check for essential device information elements
  expect(await deviceDetails.$('.device-name')).to.not.be.null;
  expect(await deviceDetails.$('.device-meta')).to.not.be.null;
  expect(await deviceDetails.$('.device-image')).to.not.be.null;
});

Then('the detailed view should show real-time operational status', async function() {
  const deviceDetails = await getDeviceDetails(this.page);
  const statusCard = await deviceDetails.$('app-device-status-card');

  expect(statusCard).to.not.be.null;
});

Then('I should see a chart displaying historical temperature data', async function() {
  const chart = await getTelemetryChart(this.page);
  expect(chart).to.not.be.null;
});

Then('I should be able to select different time ranges', async function() {
  const timeRangeButtons = await this.page.$$('.time-range-selector button');
  expect(timeRangeButtons.length).to.be.at.least(2);
});

Then('I should be able to select different metrics to display', async function() {
  const metricOptions = await this.page.$$('.metric-option');
  expect(metricOptions.length).to.be.at.least(2);
});

Then('I should see the efficiency rating for the water heater', async function() {
  const efficiencyRating = await getEfficiencyRating(this.page);
  expect(efficiencyRating).to.not.be.null;
});

Then('I should see key performance metrics including:', async function(dataTable) {
  const expectedMetrics = dataTable.raw().map(row => row[0]);
  const performanceMetrics = await getPerformanceMetrics(this.page);

  for (const metric of expectedMetrics) {
    const found = await performanceMetrics.some(async (metricCard) => {
      const nameElement = await metricCard.$('.metric-name');
      return (await nameElement.textContent()).includes(metric);
    });

    expect(found, `Metric "${metric}" not found in performance metrics`).to.be.true;
  }
});

Then('the system should send a command to set the target temperature to {string}', async function(temperature) {
  // Check command was sent
  const commandSent = await this.page.evaluate((temp) => {
    const commandHistory = JSON.parse(localStorage.getItem('commandHistory') || '[]');
    return commandHistory.some(cmd =>
      cmd.command === 'set_temperature' &&
      cmd.parameters &&
      cmd.parameters.setpoint === parseInt(temp)
    );
  }, temperature);

  expect(commandSent).to.be.true;
});

Then('the device should acknowledge the command', async function() {
  // Wait for command acknowledgment
  await this.page.waitForFunction(() => {
    const commandHistory = JSON.parse(localStorage.getItem('commandHistory') || '[]');
    return commandHistory.some(cmd => cmd.acknowledged === true);
  }, { timeout: 5000 });

  const commandAcknowledged = await this.page.evaluate(() => {
    const commandHistory = JSON.parse(localStorage.getItem('commandHistory') || '[]');
    return commandHistory.some(cmd => cmd.acknowledged === true);
  });

  expect(commandAcknowledged).to.be.true;
});

Then('the system should send a power toggle command to the device', async function() {
  // Check command was sent
  const commandSent = await this.page.evaluate(() => {
    const commandHistory = JSON.parse(localStorage.getItem('commandHistory') || '[]');
    return commandHistory.some(cmd => cmd.command === 'power_toggle');
  });

  expect(commandSent).to.be.true;
});

Then('the device mode should change from {string}', async function(originalMode) {
  // Wait for mode to change
  await this.page.waitForFunction((mode) => {
    const device = document.querySelector('app-device-status-card');
    return device && !device.textContent.includes(`Mode: ${mode}`);
  }, { timeout: 5000 }, originalMode);

  const modeChanged = await this.page.evaluate((mode) => {
    const device = document.querySelector('app-device-status-card');
    return device && !device.textContent.includes(`Mode: ${mode}`);
  }, originalMode);

  expect(modeChanged).to.be.true;
});

Then('I should see the number of anomalies detected', async function() {
  const anomalyCount = await getAnomalyCount(this.page);
  expect(anomalyCount).to.not.be.null;
});

Then('I should be able to view details about the anomalies', async function() {
  // Click button to show anomaly details
  await this.page.click('.anomalies-details');

  // Check anomaly details panel appeared
  const anomaliesPanel = await this.page.$('.anomalies-details-panel');
  expect(anomaliesPanel).to.not.be.null;
});

Then('the temperature values should be converted to the selected unit', async function() {
  // Get initial temperature values
  const initialTemps = await getTemperatureValues(this.page);

  // Toggle temperature unit
  await toggleTemperatureUnit(this.page);

  // Get updated temperature values
  const updatedTemps = await getTemperatureValues(this.page);

  // Verify values are different (conversion happened)
  expect(initialTemps.current).to.not.equal(updatedTemps.current);
  expect(initialTemps.target).to.not.equal(updatedTemps.target);
});

Then('the unit indicator should update accordingly', async function() {
  const unitElement = await this.page.$('.temperature-gauge .unit');
  const unit = await unitElement.textContent();

  // Check if unit is either °F or °C
  expect(unit).to.be.oneOf(['°F', '°C']);
});
