/**
 * Browser Hooks for IoTSphere BDD Tests
 * 
 * Provides browser setup and helper functions for interacting with UI elements
 * Designed to support device-agnostic approach with water heater reference implementation
 */

const { Before, After, BeforeAll, AfterAll } = require('@cucumber/cucumber');
const { chromium } = require('playwright');

// Base app URL - configurable from environment
const BASE_URL = process.env.TEST_APP_URL || 'http://localhost:4200';

/**
 * Initialize browser setup for BDD testing
 */
function setupBrowserHooks() {
  let browser;

  // Launch browser once before all tests
  BeforeAll(async function() {
    browser = await chromium.launch({
      headless: process.env.CI === 'true', // Headless in CI, otherwise with UI
      slowMo: 50 // Slow down execution for visualization during local development
    });
  });

  // Close browser after all tests complete
  AfterAll(async function() {
    await browser.close();
  });

  // Setup context and page before each scenario
  Before(async function() {
    this.context = await browser.newContext({
      viewport: { width: 1280, height: 720 }
    });
    this.page = await this.context.newPage();
    
    // Set up mock API interceptors
    await setupApiMocks(this.page);
  });

  // Cleanup after each scenario
  After(async function() {
    await this.page.close();
    await this.context.close();
  });
}

/**
 * Setup API mocks for the test environment
 */
async function setupApiMocks(page) {
  // Intercept device list API calls
  await page.route('**/api/devices', route => {
    return page.evaluate(() => {
      return localStorage.getItem('mockDevices') || '[]';
    }).then(devices => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: devices
      });
    });
  });

  // Intercept individual device API calls
  await page.route('**/api/devices/*', route => {
    const url = route.request().url();
    const deviceId = url.split('/').pop().split('?')[0];
    
    return page.evaluate(id => {
      return localStorage.getItem(`device_${id}`);
    }, deviceId).then(device => {
      if (device) {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: device
        });
      } else {
        route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Device not found' })
        });
      }
    });
  });

  // Intercept telemetry history API calls
  await page.route('**/api/telemetry/history/*', route => {
    const url = route.request().url();
    const deviceId = url.split('/').pop().split('?')[0];
    
    return page.evaluate(id => {
      return localStorage.getItem(`telemetry_${id}`);
    }, deviceId).then(telemetry => {
      if (telemetry) {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: telemetry
        });
      } else {
        route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Telemetry data not found' })
        });
      }
    });
  });

  // Intercept performance metrics API calls
  await page.route('**/api/devices/*/performance', route => {
    const url = route.request().url();
    const parts = url.split('/');
    const deviceId = parts[parts.indexOf('devices') + 1];
    
    return page.evaluate(id => {
      return localStorage.getItem(`performance_${id}`);
    }, deviceId).then(performance => {
      if (performance) {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: performance
        });
      } else {
        route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Performance data not found' })
        });
      }
    });
  });

  // Intercept command API calls to simulate device control
  await page.route('**/api/commands', async (route) => {
    const postData = route.request().postDataJSON();
    
    // Store command in history for verification
    await page.evaluate(commandData => {
      const commandHistory = JSON.parse(localStorage.getItem('commandHistory') || '[]');
      commandData.timestamp = new Date().toISOString();
      commandData.acknowledged = false;
      commandHistory.push(commandData);
      localStorage.setItem('commandHistory', JSON.stringify(commandHistory));
      
      // Simulate command acknowledgment after a delay
      setTimeout(() => {
        const history = JSON.parse(localStorage.getItem('commandHistory') || '[]');
        const index = history.findIndex(cmd => 
          cmd.timestamp === commandData.timestamp &&
          cmd.command === commandData.command
        );
        
        if (index >= 0) {
          history[index].acknowledged = true;
          localStorage.setItem('commandHistory', JSON.stringify(history));
        }
      }, 500);
    }, postData);
    
    route.fulfill({
      status: 202,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, message: 'Command accepted' })
    });
  });
}

/**
 * Helper functions for interacting with the dashboard UI
 */

// Get all device cards from the dashboard
async function getDeviceCards(page) {
  return page.$$('app-device-status-card');
}

// Get device details container
async function getDeviceDetails(page) {
  return page.$('.device-details-container');
}

// Get summary metrics cards
async function getSummaryMetrics(page) {
  return page.$$('.summary-metric-card');
}

// Get telemetry chart component
async function getTelemetryChart(page) {
  return page.$('app-telemetry-history-chart');
}

// Get performance metrics cards
async function getPerformanceMetrics(page) {
  return page.$$('.metric-card');
}

// Get efficiency rating element
async function getEfficiencyRating(page) {
  return page.$('.efficiency-rating');
}

// Get anomaly count element
async function getAnomalyCount(page) {
  return page.$('.anomaly-count');
}

// Get all temperature values (current and target)
async function getTemperatureValues(page) {
  const currentElement = await page.$('.current-temp .value');
  const targetElement = await page.$('.target-temp .value');
  
  return {
    current: await currentElement.textContent(),
    target: await targetElement.textContent()
  };
}

module.exports = {
  setupBrowserHooks,
  getDeviceCards,
  getDeviceDetails,
  getSummaryMetrics,
  getTelemetryChart,
  getPerformanceMetrics,
  getEfficiencyRating,
  getAnomalyCount,
  getTemperatureValues
};
