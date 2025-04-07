/**
 * Step definitions for manufacturer-agnostic water heater API scenarios
 */
const { Given, When, Then } = require('@cucumber/cucumber');
// Using async import for Chai (ES module)
let expect;
import('chai').then(chai => {
  expect = chai.expect;
});

/**
 * Setup and data preparation
 */
Given('multiple water heaters from different manufacturers are registered:', async function(dataTable) {
  const manufacturers = dataTable.hashes();
  this.testContext.registeredManufacturers = {};
  
  // Register water heaters for each manufacturer
  for (const item of manufacturers) {
    const manufacturer = item.manufacturer;
    const count = parseInt(item.count);
    
    this.testContext.registeredManufacturers[manufacturer] = [];
    
    for (let i = 0; i < count; i++) {
      const deviceId = `${manufacturer.toLowerCase().replace(/\s+/g, '-')}-${i+1}`;
      
      // Register device
      const device = await this.deviceRepository.registerDevice({
        id: deviceId,
        type: 'water-heater',
        name: `${manufacturer} Water Heater ${i+1}`,
        manufacturer: manufacturer,
        model: `Model ${String.fromCharCode(65 + i)}`, // Model A, B, C, etc.
        serialNumber: `${manufacturer.substring(0, 2).toUpperCase()}${1000 + i}`,
        firmwareVersion: '1.0.0'
      });
      
      // Add basic telemetry
      const telemetryData = {
        temperature: 120 + (Math.random() * 10 - 5),
        pressure: 40 + (Math.random() * 4 - 2),
        energyConsumed: 5.0 + (Math.random() * 1),
        mode: Math.random() > 0.3 ? 'STANDARD' : 'ECO'
      };
      
      await this.telemetryService.addTelemetryData(deviceId, telemetryData);
      
      this.testContext.registeredManufacturers[manufacturer].push(device);
    }
  }
  
  // Verify all manufacturers and devices were registered
  for (const [manufacturer, devices] of Object.entries(this.testContext.registeredManufacturers)) {
    const expectedCount = manufacturers.find(m => m.manufacturer === manufacturer).count;
    expect(devices.length).to.equal(parseInt(expectedCount));
  }
});

Given('a registered water heater with ID {string} from manufacturer {string}', async function(deviceId, manufacturer) {
  // Check if device exists
  let device = await this.deviceRepository.findDeviceById(deviceId);
  
  if (!device) {
    // Create a new water heater device
    device = await this.deviceRepository.registerDevice({
      id: deviceId,
      type: 'water-heater',
      name: `${manufacturer} Test Water Heater`,
      manufacturer,
      model: 'Test Model',
      serialNumber: `${manufacturer.substring(0, 2).toUpperCase()}12345`,
      firmwareVersion: '1.0.0'
    });
    
    // Add basic telemetry
    const telemetryData = {
      temperature: 120,
      pressure: 40,
      energyConsumed: 5.0,
      mode: 'STANDARD'
    };
    
    await this.telemetryService.addTelemetryData(deviceId, telemetryData);
  } else {
    // Ensure manufacturer matches
    if (device.manufacturer !== manufacturer) {
      device.manufacturer = manufacturer;
      await this.deviceRepository.updateDevice(device);
    }
  }
  
  this.testContext.currentDeviceId = deviceId;
  this.testContext.currentDevice = device;
});

Given('a registered water heater with ID {string} with operational history', async function(deviceId) {
  // Check if device exists
  let device = await this.deviceRepository.findDeviceById(deviceId);
  
  if (!device) {
    // Create a new water heater device
    device = await this.deviceRepository.registerDevice({
      id: deviceId,
      type: 'water-heater',
      name: 'Test Water Heater with History',
      manufacturer: 'Test Manufacturer',
      model: 'Test Model',
      serialNumber: 'TEST12345',
      firmwareVersion: '1.0.0'
    });
  }
  
  this.testContext.currentDeviceId = deviceId;
  this.testContext.currentDevice = device;
  
  // Generate operational history - last 30 days
  const now = new Date();
  const startDate = new Date(now);
  startDate.setDate(now.getDate() - 30);
  
  // Generate telemetry history
  await this.generateOperationalHistory(deviceId, startDate, now);
  
  // Generate a health assessment
  const assessment = {
    deviceId,
    overallScore: 85,
    componentScores: {
      heatingElement: 80,
      thermostat: 90,
      pressureRelief: 88,
      tankIntegrity: 85
    },
    estimatedLifespan: '8 years',
    confidenceLevel: 0.85,
    timestamp: new Date()
  };
  
  await this.analyticsEngine.saveHealthAssessment(deviceId, assessment);
  
  // Create some maintenance predictions
  const prediction = {
    deviceId,
    predictedIssue: 'Heating element degradation',
    recommendedDate: new Date(now.getTime() + (90 * 24 * 60 * 60 * 1000)), // 90 days in future
    confidence: 0.75,
    severity: 'MEDIUM',
    estimatedCost: 230
  };
  
  await this.analyticsEngine.addMaintenancePrediction(deviceId, prediction);
  
  // Verify history was created
  const history = await this.telemetryService.getHistoricalTelemetry(
    deviceId,
    startDate,
    now
  );
  
  expect(history.length).to.be.greaterThan(0);
});

Given('the following registered devices:', async function(dataTable) {
  const deviceData = dataTable.hashes();
  this.testContext.unifiedDevices = [];
  
  for (const device of deviceData) {
    // Register device
    const registeredDevice = await this.deviceRepository.registerDevice({
      id: device.deviceId,
      type: device.type,
      name: `Test ${device.type}`,
      manufacturer: device.manufacturer || 'Test Manufacturer',
      model: 'Test Model',
      serialNumber: device.deviceId,
      firmwareVersion: '1.0.0'
    });
    
    // Add some basic telemetry appropriate for device type
    let telemetryData;
    
    switch (device.type) {
      case 'water-heater':
        telemetryData = {
          temperature: 120,
          pressure: 40,
          energyConsumed: 5.0,
          mode: 'STANDARD'
        };
        break;
      case 'vending-machine':
        telemetryData = {
          temperature: 38,
          doorStatus: 'CLOSED',
          stockLevel: 85,
          cashBalance: 125.50
        };
        break;
      case 'robot':
        telemetryData = {
          batteryLevel: 87,
          status: 'STANDBY',
          position: { x: 10, y: 15, z: 0 },
          errorCount: 0
        };
        break;
      default:
        telemetryData = {
          status: 'ONLINE',
          lastActivity: new Date()
        };
    }
    
    await this.telemetryService.addTelemetryData(device.deviceId, telemetryData);
    this.testContext.unifiedDevices.push(registeredDevice);
  }
  
  expect(this.testContext.unifiedDevices.length).to.equal(deviceData.length);
});

/**
 * API request actions
 */
When('a user sends a GET request to {string}', async function(endpoint) {
  try {
    // Make API request
    const response = await this.apiClient.get(endpoint);
    this.testContext.apiResponse = response;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('a user sends a GET request to {string} with param {string} = {string}', async function(endpoint, paramName, paramValue) {
  try {
    // Make API request with parameters
    const response = await this.apiClient.get(endpoint, { [paramName]: paramValue });
    this.testContext.apiResponse = response;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('a user sends a GET request to {string} with manufacturer {string}', async function(endpoint, manufacturer) {
  try {
    // Make API request with query parameter
    const response = await this.apiClient.get(endpoint, { manufacturer });
    this.testContext.apiResponse = response;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('a user sends a PUT request to {string}', async function(endpoint) {
  this.testContext.requestEndpoint = endpoint;
});

When('includes the mode {string} in the request body', async function(mode) {
  const endpoint = this.testContext.requestEndpoint;
  const requestBody = { mode };
  
  try {
    // Make PUT request
    const response = await this.apiClient.put(endpoint, requestBody);
    this.testContext.apiResponse = response;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

/**
 * Verification steps
 */
Then('the system should return all registered water heaters', function() {
  const response = this.testContext.apiResponse;
  
  expect(response).to.not.be.null;
  expect(response.status).to.equal(200);
  
  // Count total number of expected devices
  let totalDevices = 0;
  for (const devices of Object.values(this.testContext.registeredManufacturers)) {
    totalDevices += devices.length;
  }
  
  expect(response.data.waterHeaters.length).to.equal(totalDevices);
});

Then('each water heater should have manufacturer information', function() {
  const response = this.testContext.apiResponse;
  const waterHeaters = response.data.waterHeaters;
  
  for (const waterHeater of waterHeaters) {
    expect(waterHeater).to.have.property('manufacturer');
    expect(waterHeater.manufacturer).to.be.a('string');
    expect(waterHeater.manufacturer.length).to.be.greaterThan(0);
  }
});

Then('the response should use the standardized data model', function() {
  const response = this.testContext.apiResponse;
  const data = response.data;
  
  // Check for standardized data structure
  if (data.waterHeaters) {
    // List response
    expect(data).to.have.property('waterHeaters');
    expect(data.waterHeaters).to.be.an('array');
    
    if (data.waterHeaters.length > 0) {
      const waterHeater = data.waterHeaters[0];
      expect(waterHeater).to.have.property('id');
      expect(waterHeater).to.have.property('manufacturer');
      expect(waterHeater).to.have.property('model');
      expect(waterHeater).to.have.property('status');
    }
  } else if (data.id) {
    // Single device response
    expect(data).to.have.property('id');
    expect(data).to.have.property('manufacturer');
    expect(data).to.have.property('model');
    expect(data).to.have.property('serialNumber');
    expect(data).to.have.property('status');
    expect(data).to.have.property('capabilities');
  }
});

Then('the response should include pagination information', function() {
  const response = this.testContext.apiResponse;
  const data = response.data;
  
  expect(data).to.have.property('pagination');
  expect(data.pagination).to.have.property('total');
  expect(data.pagination).to.have.property('page');
  expect(data.pagination).to.have.property('pageSize');
  expect(data.pagination).to.have.property('pages');
});

Then('the system should return only water heaters from {string}', function(manufacturer) {
  const response = this.testContext.apiResponse;
  const waterHeaters = response.data.waterHeaters;
  
  expect(waterHeaters.length).to.be.greaterThan(0);
  
  for (const waterHeater of waterHeaters) {
    expect(waterHeater.manufacturer).to.equal(manufacturer);
  }
});

Then('the count of returned devices should match the number of registered {word} devices', function(manufacturer) {
  const response = this.testContext.apiResponse;
  const waterHeaters = response.data.waterHeaters;
  
  const expectedCount = this.testContext.registeredManufacturers[manufacturer].length;
  expect(waterHeaters.length).to.equal(expectedCount);
});

Then('the system should return the water heater details', function() {
  const response = this.testContext.apiResponse;
  
  expect(response).to.not.be.null;
  expect(response.status).to.equal(200);
  expect(response.data).to.be.an('object');
  expect(response.data.id).to.equal(this.testContext.currentDeviceId);
});

Then('the response should include:', function(dataTable) {
  const expectedFields = dataTable.rowsHash();
  const response = this.testContext.apiResponse;
  const waterHeater = response.data;
  
  // Verify all expected fields
  for (const [field] of Object.entries(expectedFields)) {
    expect(waterHeater).to.have.property(field);
  }
  
  // Check specific field values if specified
  for (const [field, description] of Object.entries(expectedFields)) {
    if (description.startsWith('"') && description.endsWith('"')) {
      const expectedValue = description.substring(1, description.length - 1);
      expect(waterHeater[field]).to.equal(expectedValue);
    }
  }
});

Then('the system should return an operational summary including:', function(dataTable) {
  const expectedFields = dataTable.rowsHash();
  const response = this.testContext.apiResponse;
  
  expect(response).to.not.be.null;
  expect(response.status).to.equal(200);
  
  const summary = response.data;
  expect(summary).to.be.an('object');
  
  // Verify all expected fields
  for (const [field] of Object.entries(expectedFields)) {
    expect(summary).to.have.property(field);
  }
});

Then('the response should follow the standardized format regardless of manufacturer', function() {
  const response = this.testContext.apiResponse;
  
  expect(response).to.not.be.null;
  expect(response.data).to.be.an('object');
  
  // The format should include standard fields
  const data = response.data;
  
  if (data.waterHeaters) {
    // Check waterHeaters list format
    expect(data.waterHeaters[0]).to.have.property('id');
    expect(data.waterHeaters[0]).to.have.property('manufacturer');
    expect(data.waterHeaters[0]).to.have.property('status');
  } else {
    // Check individual device format
    expect(data).to.have.property('id');
    expect(data).to.have.property('manufacturer');
  }
});

Then('the system should translate the request to the manufacturer-specific format', function() {
  const response = this.testContext.apiResponse;
  
  expect(response).to.not.be.null;
  expect(response.status).to.equal(200);
  
  // The mock API client should record that a translation happened
  expect(this.apiClient.lastRequestTranslated).to.be.true;
});

Then('the water heater mode should be updated to {string}', async function(mode) {
  const deviceId = this.testContext.currentDeviceId;
  
  // Get the current device state
  const deviceState = await this.deviceRepository.getDeviceState(deviceId);
  
  expect(deviceState).to.have.property('mode');
  expect(deviceState.mode).to.equal(mode);
});

Then('the response should include the updated water heater state', function() {
  const response = this.testContext.apiResponse;
  
  expect(response).to.not.be.null;
  expect(response.data).to.have.property('currentState');
  expect(response.data.currentState).to.have.property('mode');
});

Then('the standardized response format should be the same regardless of manufacturer', function() {
  // This is verified by checking the response format is standardized
  expect(this.apiClient.responseStandardized).to.be.true;
});

Then('the system should return a list of all supported manufacturers', function() {
  const response = this.testContext.apiResponse;
  
  expect(response).to.not.be.null;
  expect(response.status).to.equal(200);
  
  expect(response.data).to.have.property('manufacturers');
  expect(response.data.manufacturers).to.be.an('array');
  expect(response.data.manufacturers.length).to.be.greaterThan(0);
});

Then('each manufacturer should include:', function(dataTable) {
  const expectedFields = dataTable.rowsHash();
  const response = this.testContext.apiResponse;
  const manufacturers = response.data.manufacturers;
  
  // Check each manufacturer has the expected fields
  for (const manufacturer of manufacturers) {
    for (const [field] of Object.entries(expectedFields)) {
      expect(manufacturer).to.have.property(field);
    }
  }
});

Then('the response should include any recently added manufacturers', function() {
  const response = this.testContext.apiResponse;
  const manufacturers = response.data.manufacturers;
  
  // Get manufacturers we registered in earlier steps
  const registeredManufacturers = Object.keys(this.testContext.registeredManufacturers || {});
  
  for (const manufacturer of registeredManufacturers) {
    const found = manufacturers.find(m => m.name === manufacturer);
    expect(found).to.not.be.undefined;
  }
});

Then('the system should return all devices regardless of type', function() {
  const response = this.testContext.apiResponse;
  
  expect(response).to.not.be.null;
  expect(response.status).to.equal(200);
  
  expect(response.data).to.have.property('devices');
  expect(response.data.devices).to.be.an('array');
  
  // Should include all registered unified devices
  expect(response.data.devices.length).to.equal(this.testContext.unifiedDevices.length);
});

Then('each device should use its type-specific data model', function() {
  const response = this.testContext.apiResponse;
  const devices = response.data.devices;
  
  // Check device-specific properties
  for (const device of devices) {
    expect(device).to.have.property('type');
    
    if (device.type === 'water-heater') {
      expect(device).to.have.property('temperature');
    } else if (device.type === 'vending-machine') {
      expect(device).to.have.property('stockLevel');
    } else if (device.type === 'robot') {
      expect(device).to.have.property('batteryLevel');
    }
  }
});

Then('all devices should share common base fields:', function(dataTable) {
  const expectedFields = dataTable.rowsHash();
  const response = this.testContext.apiResponse;
  const devices = response.data.devices;
  
  // Check all devices have common fields
  for (const device of devices) {
    for (const [field] of Object.entries(expectedFields)) {
      expect(device).to.have.property(field);
    }
  }
});

Then('the response should maintain backward compatibility with existing clients', function() {
  const response = this.testContext.apiResponse;
  
  // The mock API client should set a flag if the response is backward compatible
  expect(this.apiClient.backwardCompatible).to.be.true;
});
