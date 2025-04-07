/**
 * Step definitions for telemetry monitoring scenarios
 */
const { Given, When, Then } = require('@cucumber/cucumber');
// Using async import for Chai (ES module)
let expect;
import('chai').then(chai => {
  expect = chai.expect;
});

/**
 * Setup and device preparation
 */
Given('a registered water heater device with ID {string}', async function(deviceId) {
  // Check if device exists, otherwise create a test device
  const device = await this.deviceRepository.findDeviceById(deviceId);

  if (!device) {
    const newDevice = {
      id: deviceId,
      type: 'water-heater',
      name: 'Test Water Heater',
      manufacturer: 'Test Manufacturer',
      model: 'Test Model',
      serialNumber: 'TEST-SERIAL-123',
      firmwareVersion: '1.0.0'
    };

    await this.deviceRepository.registerDevice(newDevice);
  }

  this.testContext.currentDeviceId = deviceId;
});

Given('the device is reporting telemetry data', async function() {
  const deviceId = this.testContext.currentDeviceId;

  // Generate sample telemetry data
  const telemetryData = {
    temperature: 120,
    pressure: 40,
    energyConsumed: 5.2,
    mode: 'STANDARD'
  };

  // Add telemetry data to the mock service
  await this.telemetryService.addTelemetryData(deviceId, telemetryData);

  // Verify telemetry was added
  const currentTelemetry = await this.telemetryService.getCurrentTelemetry(deviceId);
  expect(currentTelemetry).to.not.be.null;
});

Given('the device has been reporting telemetry for {string}', async function(timeframe) {
  const deviceId = this.testContext.currentDeviceId;

  // Parse timeframe to determine how much historical data to generate
  let hoursToGenerate = 24;
  if (timeframe.includes('hours')) {
    hoursToGenerate = parseInt(timeframe.split(' ')[0]);
  } else if (timeframe.includes('days')) {
    hoursToGenerate = parseInt(timeframe.split(' ')[0]) * 24;
  }

  // Generate historical telemetry data
  const now = new Date();
  for (let i = hoursToGenerate; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - (i * 60 * 60 * 1000));

    // Create realistic fluctuating values
    const telemetryData = {
      timestamp,
      temperature: 120 + (Math.sin(i) * 5), // Fluctuate between 115-125
      pressure: 40 + (Math.cos(i) * 2),     // Fluctuate between 38-42
      energyConsumed: 5.2 + (i * 0.2),      // Gradually increase
      mode: i % 8 === 0 ? 'ECO' : 'STANDARD' // Occasional mode change
    };

    await this.telemetryService.addHistoricalTelemetry(deviceId, telemetryData);
  }

  // Verify historical data was created
  const history = await this.telemetryService.getHistoricalTelemetry(
    deviceId,
    new Date(now.getTime() - (hoursToGenerate * 60 * 60 * 1000)),
    now
  );

  expect(history.length).to.be.at.least(hoursToGenerate);
});

Given('an end user with access to device {string}', async function(deviceId) {
  // Set up an end user with access to the specified device
  const user = await this.userService.createUser({
    id: 'test-end-user',
    username: 'enduser',
    roles: ['END_USER'],
    deviceAccess: [deviceId]
  });

  this.testContext.currentUser = user;
  this.testContext.currentDeviceId = deviceId;
});

Given('the device has a temperature spike to {string}', async function(temperature) {
  const deviceId = this.testContext.currentDeviceId;
  const temperatureValue = parseFloat(temperature.replace('°F', ''));

  // Create anomalous telemetry data
  const telemetryData = {
    timestamp: new Date(),
    temperature: temperatureValue,
    pressure: 40,
    energyConsumed: 5.2,
    mode: 'STANDARD'
  };

  await this.telemetryService.addTelemetryData(deviceId, telemetryData);
});

Given('a group of {int} water heaters in the same facility', async function(count) {
  this.testContext.deviceGroup = [];

  for (let i = 0; i < count; i++) {
    const deviceId = `test-water-heater-${i+1}`;

    // Register device
    const device = await this.deviceRepository.registerDevice({
      id: deviceId,
      type: 'water-heater',
      name: `Test Water Heater ${i+1}`,
      manufacturer: 'Test Manufacturer',
      model: 'Test Model',
      serialNumber: `TEST-SERIAL-${i+1}`,
      firmwareVersion: '1.0.0',
      metadata: {
        facility: 'Test Facility'
      }
    });

    // Add normal telemetry data
    const telemetryData = {
      temperature: 120,
      pressure: 40,
      energyConsumed: 5.0,
      mode: 'STANDARD'
    };

    await this.telemetryService.addTelemetryData(deviceId, telemetryData);
    this.testContext.deviceGroup.push(device);
  }

  expect(this.testContext.deviceGroup.length).to.equal(count);
});

/**
 * User actions
 */
When('a user with {string} role requests current telemetry', async function(role) {
  // Set up a user with the specified role
  const user = await this.userService.getUserByRole(role);
  expect(user).to.not.be.null;

  const deviceId = this.testContext.currentDeviceId;

  try {
    // Get current telemetry
    const telemetry = await this.telemetryService.getCurrentTelemetry(deviceId);
    this.testContext.currentTelemetry = telemetry;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('a user with {string} role requests historical telemetry', async function(role) {
  // Set up a user with the specified role
  const user = await this.userService.getUserByRole(role);
  expect(user).to.not.be.null;

  this.testContext.currentRole = role;
});

When('specifies a time range of {string}', function(timeRange) {
  // Parse the time range
  let hoursToLookBack = 24;

  if (timeRange.includes('last')) {
    if (timeRange.includes('hours')) {
      hoursToLookBack = parseInt(timeRange.split(' ')[1]);
    } else if (timeRange.includes('days')) {
      hoursToLookBack = parseInt(timeRange.split(' ')[1]) * 24;
    }
  }

  const now = new Date();
  this.testContext.telemetryQuery = {
    startTime: new Date(now.getTime() - (hoursToLookBack * 60 * 60 * 1000)),
    endTime: now
  };
});

When('selects {string} as the telemetry type', async function(telemetryType) {
  const deviceId = this.testContext.currentDeviceId;
  const query = this.testContext.telemetryQuery;

  try {
    // Get historical telemetry for the specified type
    const telemetry = await this.telemetryService.getHistoricalTelemetry(
      deviceId,
      query.startTime,
      query.endTime,
      telemetryType
    );

    this.testContext.historicalTelemetry = telemetry;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('the user views the device dashboard', async function() {
  const deviceId = this.testContext.currentDeviceId;
  const user = this.testContext.currentUser;

  try {
    // Simulate user viewing the dashboard
    const dashboardData = await this.telemetryService.getDashboardDataForUser(
      deviceId,
      user.id
    );

    this.testContext.dashboardData = dashboardData;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('the system processes the incoming telemetry', async function() {
  const deviceId = this.testContext.currentDeviceId;

  try {
    // Trigger the analytics engine to process telemetry
    const result = await this.analyticsEngine.processTelemetry(deviceId);
    this.testContext.processingResult = result;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('{int} of the water heaters show increased energy consumption', async function(count) {
  const deviceGroup = this.testContext.deviceGroup;

  // Modify telemetry for some devices to show increased consumption
  for (let i = 0; i < count; i++) {
    const deviceId = deviceGroup[i].id;

    // Create higher energy consumption telemetry
    const telemetryData = {
      temperature: 120,
      pressure: 40,
      energyConsumed: 8.5, // Higher than normal
      mode: 'STANDARD'
    };

    await this.telemetryService.addTelemetryData(deviceId, telemetryData);
  }

  try {
    // Process the group telemetry
    const result = await this.analyticsEngine.processGroupTelemetry(
      deviceGroup.map(d => d.id)
    );

    this.testContext.groupAnalysisResult = result;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

/**
 * Verification steps
 */
Then('the system should return the following telemetry data:', function(dataTable) {
  const expectedTypes = dataTable.rows();
  const telemetry = this.testContext.currentTelemetry;

  expect(telemetry).to.not.be.null;

  // Verify each expected telemetry type
  for (const [dataType, dataFormat] of expectedTypes) {
    expect(telemetry).to.have.property(dataType);

    if (dataFormat === 'numeric') {
      expect(typeof telemetry[dataType]).to.equal('number');
    } else if (dataFormat === 'string') {
      expect(typeof telemetry[dataType]).to.equal('string');
    }
  }
});

Then('all telemetry values should have timestamps', function() {
  const telemetry = this.testContext.currentTelemetry;

  expect(telemetry).to.have.property('timestamp');
  expect(telemetry.timestamp).to.be.an.instanceOf(Date);
});

Then('all telemetry values should have appropriate units of measurement', function() {
  const telemetry = this.testContext.currentTelemetry;

  // Verify units exist for numeric values
  expect(telemetry).to.have.property('units');
  expect(telemetry.units).to.have.property('temperature');
  expect(telemetry.units).to.have.property('pressure');
  expect(telemetry.units).to.have.property('energyConsumed');
});

Then('the system should return temperature readings for the specified time period', function() {
  const telemetry = this.testContext.historicalTelemetry;

  expect(telemetry).to.be.an('array');
  expect(telemetry.length).to.be.greaterThan(0);

  // Verify each item has temperature data
  for (const reading of telemetry) {
    expect(reading).to.have.property('temperature');
    expect(typeof reading.temperature).to.equal('number');
  }
});

Then('the data should be presented in chronological order', function() {
  const telemetry = this.testContext.historicalTelemetry;

  // Verify timestamps are in ascending order
  for (let i = 1; i < telemetry.length; i++) {
    expect(telemetry[i].timestamp.getTime()).to.be.greaterThan(
      telemetry[i-1].timestamp.getTime()
    );
  }
});

Then('the data should include at least {int} data points', function(count) {
  const telemetry = this.testContext.historicalTelemetry;
  expect(telemetry.length).to.be.at.least(count);
});

Then('all data points should have valid timestamps', function() {
  const telemetry = this.testContext.historicalTelemetry;

  for (const reading of telemetry) {
    expect(reading).to.have.property('timestamp');
    expect(reading.timestamp).to.be.an.instanceOf(Date);
    expect(reading.timestamp.getTime()).to.be.lessThan(Date.now());
  }
});

Then('all temperature values should be within the range of {int}-{int}°F', function(min, max) {
  const telemetry = this.testContext.historicalTelemetry;

  for (const reading of telemetry) {
    expect(reading.temperature).to.be.at.least(min);
    expect(reading.temperature).to.be.at.most(max);
  }
});

Then('they should see the current temperature', function() {
  const data = this.testContext.dashboardData;

  expect(data).to.have.property('temperature');
  expect(typeof data.temperature).to.equal('number');
});

Then('they should see the current operational mode', function() {
  const data = this.testContext.dashboardData;

  expect(data).to.have.property('mode');
  expect(typeof data.mode).to.equal('string');
});

Then('they should not see detailed pressure readings', function() {
  const data = this.testContext.dashboardData;

  // For end users, the detailed pressure shouldn't be visible
  expect(data).to.not.have.property('pressure');
});

Then('they should not see detailed energy consumption data', function() {
  const data = this.testContext.dashboardData;

  // End users should only see simplified energy info, not detailed data
  expect(data).to.not.have.property('energyConsumed');

  // But they might see a simplified version
  if (data.energySummary) {
    expect(data.energySummary).to.be.a('string');
  }
});

Then('it should detect an anomaly in the temperature readings', function() {
  const result = this.testContext.processingResult;

  expect(result).to.have.property('anomalies');
  expect(result.anomalies.length).to.be.at.least(1);

  // At least one anomaly should be related to temperature
  const tempAnomaly = result.anomalies.find(a => a.type === 'temperature');
  expect(tempAnomaly).to.not.be.undefined;
});

Then('it should calculate the deviation from normal operation', function() {
  const result = this.testContext.processingResult;
  const tempAnomaly = result.anomalies.find(a => a.type === 'temperature');

  expect(tempAnomaly).to.have.property('deviation');
  expect(typeof tempAnomaly.deviation).to.equal('number');
});

Then('it should generate an alert for the facility manager', function() {
  const result = this.testContext.processingResult;

  expect(result).to.have.property('alerts');
  expect(result.alerts.length).to.be.at.least(1);

  // Verify the alert is intended for facility managers
  const facilityAlert = result.alerts.find(a =>
    a.targetRoles.includes('FACILITY_MANAGER')
  );

  expect(facilityAlert).to.not.be.undefined;
});

Then('the alert should include the anomaly type, severity, and timestamp', function() {
  const result = this.testContext.processingResult;
  const alert = result.alerts[0];

  expect(alert).to.have.property('anomalyType');
  expect(alert).to.have.property('severity');
  expect(alert).to.have.property('timestamp');
});

Then('the system should detect the cross-device consumption pattern', function() {
  const result = this.testContext.groupAnalysisResult;

  expect(result).to.have.property('patterns');
  expect(result.patterns.length).to.be.at.least(1);

  // Look for a consumption pattern
  const consumptionPattern = result.patterns.find(p =>
    p.type === 'consumption' || p.type === 'energy'
  );

  expect(consumptionPattern).to.not.be.undefined;
});

Then('it should analyze environmental and usage factors', function() {
  const result = this.testContext.groupAnalysisResult;
  const pattern = result.patterns[0];

  expect(pattern).to.have.property('factors');
  expect(pattern.factors).to.be.an('array');
});

Then('it should determine if the pattern indicates a systemic issue', function() {
  const result = this.testContext.groupAnalysisResult;
  const pattern = result.patterns[0];

  expect(pattern).to.have.property('isSystemic');
  expect(typeof pattern.isSystemic).to.equal('boolean');
});

Then('it should generate an insight with a confidence score', function() {
  const result = this.testContext.groupAnalysisResult;

  expect(result).to.have.property('insights');
  expect(result.insights.length).to.be.at.least(1);

  const insight = result.insights[0];
  expect(insight).to.have.property('confidence');
  expect(typeof insight.confidence).to.equal('number');
  expect(insight.confidence).to.be.within(0, 1);
});
