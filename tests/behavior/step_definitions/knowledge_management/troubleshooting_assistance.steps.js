/**
 * Step definitions for AI-assisted troubleshooting scenarios
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
Given('a water heater with an error code {string}', async function(errorCode) {
  const deviceId = 'troubleshooting-test-device';

  // Register device if not exists
  let device = await this.deviceRepository.findDeviceById(deviceId);

  if (!device) {
    device = await this.deviceRepository.registerDevice({
      id: deviceId,
      type: 'water-heater',
      name: 'Troubleshooting Test Device',
      manufacturer: 'Test Manufacturer',
      model: 'Test Model',
      serialNumber: 'TROUBLE-TEST-1',
      firmwareVersion: '1.0.0'
    });
  }

  this.testContext.currentDeviceId = deviceId;

  // Add error code to device
  await this.deviceRepository.addDeviceErrorCode(deviceId, errorCode);

  // Verify error code was added
  const deviceState = await this.deviceRepository.getDeviceState(deviceId);
  expect(deviceState.errorCode).to.equal(errorCode);
});

Given('multiple service records for similar issues across devices', async function() {
  // Create several devices with similar error conditions
  this.testContext.serviceDevices = [];

  for (let i = 0; i < 5; i++) {
    const deviceId = `service-history-device-${i}`;

    // Register device
    const device = await this.deviceRepository.registerDevice({
      id: deviceId,
      type: 'water-heater',
      name: `Service History Device ${i}`,
      manufacturer: 'Test Manufacturer',
      model: 'Test Model',
      serialNumber: `SERVICE-${i}`,
      firmwareVersion: '1.0.0'
    });

    // Create 3 service records for each device
    for (let j = 0; j < 3; j++) {
      // Alternate between successful and unsuccessful approaches
      const wasSuccessful = j % 2 === 0;

      const serviceRecord = {
        id: `service-${deviceId}-${j}`,
        deviceId,
        date: new Date(Date.now() - ((j + 1) * 30 * 24 * 60 * 60 * 1000)), // 1-3 months ago
        technician: `Technician ${j % 3}`,
        errorCode: 'E-41',
        issue: 'Heating element failure',
        approachTaken: wasSuccessful ?
          'Replaced heating element and cleaned connections' :
          'Replaced thermostat only',
        outcome: wasSuccessful ? 'Issue resolved' : 'Issue persisted',
        wasSuccessful: wasSuccessful
      };

      await this.analyticsEngine.addServiceRecord(deviceId, serviceRecord);
    }

    this.testContext.serviceDevices.push(device);
  }

  // Verify service records were created
  const records = await this.analyticsEngine.getServiceRecords(this.testContext.serviceDevices[0].id);
  expect(records.length).to.be.greaterThan(0);
});

Given('information about which repair approaches were successful', function() {
  // Already set up in previous step
  expect(this.testContext.serviceDevices.length).to.be.greaterThan(0);
});

Given('a new device type is added to the system', async function() {
  const deviceId = 'new-device-type';

  // Register a new device type
  const device = await this.deviceRepository.registerDevice({
    id: deviceId,
    type: 'new-smart-appliance',
    name: 'New Smart Appliance',
    manufacturer: 'Test Manufacturer',
    model: 'Model X',
    serialNumber: 'NEW-TYPE-1',
    firmwareVersion: '1.0.0',
    capabilities: ['TEMPERATURE_CONTROL', 'POWER_MANAGEMENT', 'REMOTE_CONTROL']
  });

  this.testContext.newDeviceType = device;

  // Verify device was created
  expect(device).to.not.be.null;
  expect(device.type).to.equal('new-smart-appliance');
});

Given('it shares capabilities with existing device types', async function() {
  const device = this.testContext.newDeviceType;

  // Verify capabilities overlap with existing devices
  const capabilities = await this.deviceRepository.getDeviceCapabilities(device.id);

  // Get capabilities of a water heater for comparison
  const waterHeaterId = this.testContext.currentDeviceId || 'troubleshooting-test-device';
  const waterHeaterCapabilities = await this.deviceRepository.getDeviceCapabilities(waterHeaterId);

  // Find shared capabilities
  this.testContext.sharedCapabilities = capabilities.filter(cap =>
    waterHeaterCapabilities.some(wc => wc.id === cap.id)
  );

  expect(this.testContext.sharedCapabilities.length).to.be.greaterThan(0);
});

Given('a device with unusual telemetry patterns', async function() {
  const deviceId = 'predictive-troubleshooting-device';

  // Register device if not exists
  let device = await this.deviceRepository.findDeviceById(deviceId);

  if (!device) {
    device = await this.deviceRepository.registerDevice({
      id: deviceId,
      type: 'water-heater',
      name: 'Predictive Troubleshooting Device',
      manufacturer: 'Test Manufacturer',
      model: 'Test Model',
      serialNumber: 'PREDICT-1',
      firmwareVersion: '1.0.0'
    });
  }

  this.testContext.currentDeviceId = deviceId;

  // Generate unusual telemetry patterns
  const now = new Date();

  // Create 7 days of normal telemetry
  for (let i = 30; i > 7; i--) {
    const day = new Date(now);
    day.setDate(now.getDate() - i);

    for (let hour = 0; hour < 24; hour += 3) {
      const timestamp = new Date(day);
      timestamp.setHours(hour);

      const telemetryData = {
        timestamp,
        temperature: 120 + (Math.random() * 4 - 2),
        pressure: 40 + (Math.random() * 2 - 1),
        energyConsumed: 5.0 + (Math.random() * 0.5),
        mode: 'STANDARD'
      };

      await this.telemetryService.addHistoricalTelemetry(deviceId, telemetryData);
    }
  }

  // Create 7 days of increasingly abnormal telemetry
  for (let i = 7; i >= 0; i--) {
    const day = new Date(now);
    day.setDate(now.getDate() - i);

    // Abnormality increases as we get closer to present
    const abnormalityFactor = 1 + ((7 - i) * 0.2);

    for (let hour = 0; hour < 24; hour += 3) {
      const timestamp = new Date(day);
      timestamp.setHours(hour);

      const telemetryData = {
        timestamp,
        temperature: 120 + (Math.sin(hour) * 3 * abnormalityFactor), // Increasing oscillation
        pressure: 40 + (Math.cos(hour) * abnormalityFactor), // Increasing oscillation
        energyConsumed: 5.0 + (abnormalityFactor * 0.5), // Increasing consumption
        mode: 'STANDARD'
      };

      await this.telemetryService.addHistoricalTelemetry(deviceId, telemetryData);
    }
  }

  // Verify telemetry was created
  const telemetry = await this.telemetryService.getHistoricalTelemetry(
    deviceId,
    new Date(now.getTime() - (30 * 24 * 60 * 60 * 1000)),
    now
  );

  expect(telemetry.length).to.be.greaterThan(30);
});

/**
 * User actions
 */
When('a service technician requests troubleshooting assistance', async function() {
  const deviceId = this.testContext.currentDeviceId;

  try {
    // Request troubleshooting assistance
    const assistance = await this.analyticsEngine.getTroubleshootingAssistance(deviceId);
    this.testContext.troubleshootingAssistance = assistance;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('the knowledge system processes this historical data', async function() {
  const deviceIds = this.testContext.serviceDevices.map(d => d.id);

  try {
    // Process service records to extract knowledge
    const knowledgeResults = await this.analyticsEngine.processServiceRecordsForKnowledge(deviceIds);
    this.testContext.knowledgeResults = knowledgeResults;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('a user encounters an issue with the new device type', async function() {
  const deviceId = this.testContext.newDeviceType.id;

  // Add an error code to the new device
  await this.deviceRepository.addDeviceErrorCode(deviceId, 'E-TEMP-1');

  try {
    // Request troubleshooting assistance for new device type
    const assistance = await this.analyticsEngine.getTroubleshootingAssistance(deviceId);
    this.testContext.newDeviceAssistance = assistance;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('the predictive maintenance system detects a developing issue', async function() {
  const deviceId = this.testContext.currentDeviceId;

  try {
    // Analyze telemetry for developing issues
    const analysis = await this.analyticsEngine.analyzeTelemetryForDevelopingIssues(deviceId);
    this.testContext.predictiveAnalysis = analysis;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

/**
 * Verification steps
 */
Then('the system should provide:', function(dataTable) {
  const expectedInfo = dataTable.rowsHash();
  const assistance = this.testContext.troubleshootingAssistance;

  expect(assistance).to.not.be.null;

  // Verify each expected piece of information
  for (const [infoType] of Object.entries(expectedInfo)) {
    // Convert to camelCase
    const propertyName = infoType
      .toLowerCase()
      .replace(/[^a-z0-9]+(.)/g, (match, chr) => chr.toUpperCase());

    expect(assistance).to.have.property(propertyName);
  }
});

Then('the assistance should be specific to the device model', function() {
  const assistance = this.testContext.troubleshootingAssistance;

  expect(assistance).to.have.property('deviceSpecificInformation');
  expect(assistance.deviceSpecificInformation).to.be.an('object');
  expect(assistance.deviceSpecificInformation).to.have.property('model');
  expect(assistance.deviceSpecificInformation).to.have.property('manufacturer');
});

Then('the information should include diagrams or visual guides', function() {
  const assistance = this.testContext.troubleshootingAssistance;

  expect(assistance).to.have.property('visualGuides');
  expect(assistance.visualGuides).to.be.an('array');
  expect(assistance.visualGuides.length).to.be.greaterThan(0);

  // Each guide should have visual information
  for (const guide of assistance.visualGuides) {
    expect(guide).to.have.property('type');
    expect(guide).to.have.property('content');
  }
});

Then('solutions should be ranked by probability of resolving the issue', function() {
  const assistance = this.testContext.troubleshootingAssistance;

  expect(assistance).to.have.property('solutions');
  expect(assistance.solutions).to.be.an('array');
  expect(assistance.solutions.length).to.be.greaterThan(0);

  // Each solution should have a resolution probability
  for (const solution of assistance.solutions) {
    expect(solution).to.have.property('resolutionProbability');
    expect(solution.resolutionProbability).to.be.a('number');
    expect(solution.resolutionProbability).to.be.within(0, 1);
  }

  // Solutions should be ordered by probability (highest first)
  for (let i = 1; i < assistance.solutions.length; i++) {
    expect(assistance.solutions[i-1].resolutionProbability).to.be.at.least(
      assistance.solutions[i].resolutionProbability
    );
  }
});

Then('it should identify the most effective repair procedures', function() {
  const results = this.testContext.knowledgeResults;

  expect(results).to.have.property('effectiveRepairProcedures');
  expect(results.effectiveRepairProcedures).to.be.an('array');
  expect(results.effectiveRepairProcedures.length).to.be.greaterThan(0);

  // Each procedure should have effectiveness metrics
  for (const procedure of results.effectiveRepairProcedures) {
    expect(procedure).to.have.property('effectiveness');
    expect(procedure.effectiveness).to.be.a('number');
    expect(procedure.effectiveness).to.be.within(0, 1);
  }
});

Then('it should update its recommendations based on success rates', function() {
  const results = this.testContext.knowledgeResults;

  expect(results).to.have.property('updatedRecommendations');
  expect(results.updatedRecommendations).to.be.an('array');
  expect(results.updatedRecommendations.length).to.be.greaterThan(0);

  // Compare updated recommendations to previous ones if available
  if (results.previousRecommendations) {
    expect(results.updatedRecommendations).to.not.deep.equal(results.previousRecommendations);
  }
});

Then('it should detect patterns in successful troubleshooting approaches', function() {
  const results = this.testContext.knowledgeResults;

  expect(results).to.have.property('successPatterns');
  expect(results.successPatterns).to.be.an('array');
  expect(results.successPatterns.length).to.be.greaterThan(0);
});

Then('future recommendations should prioritize approaches with higher success rates', function() {
  const results = this.testContext.knowledgeResults;

  // Check if prioritization is happening
  expect(results).to.have.property('prioritization');
  expect(results.prioritization).to.be.an('object');
  expect(results.prioritization).to.have.property('bySuccessRate');
  expect(results.prioritization.bySuccessRate).to.be.true;
});

Then('the system should apply relevant knowledge from similar capabilities', function() {
  const assistance = this.testContext.newDeviceAssistance;

  expect(assistance).to.have.property('knowledgeTransfer');
  expect(assistance.knowledgeTransfer).to.be.an('object');
  expect(assistance.knowledgeTransfer).to.have.property('sourceCapabilities');
  expect(assistance.knowledgeTransfer.sourceCapabilities).to.be.an('array');
  expect(assistance.knowledgeTransfer.sourceCapabilities.length).to.be.greaterThan(0);
});

Then('it should adapt troubleshooting procedures from other device types', function() {
  const assistance = this.testContext.newDeviceAssistance;

  expect(assistance).to.have.property('adaptedProcedures');
  expect(assistance.adaptedProcedures).to.be.an('array');
  expect(assistance.adaptedProcedures.length).to.be.greaterThan(0);

  // Each procedure should include information about its source
  for (const procedure of assistance.adaptedProcedures) {
    expect(procedure).to.have.property('sourceDeviceType');
    expect(procedure).to.have.property('adaptationDetails');
  }
});

Then('it should identify which aspects are device-specific', function() {
  const assistance = this.testContext.newDeviceAssistance;

  expect(assistance).to.have.property('deviceSpecificAspects');
  expect(assistance.deviceSpecificAspects).to.be.an('array');
  expect(assistance.deviceSpecificAspects.length).to.be.greaterThan(0);
});

Then('it should generate appropriate guidance despite limited historical data', function() {
  const assistance = this.testContext.newDeviceAssistance;

  expect(assistance).to.have.property('confidenceLevel');
  // Even with limited data, should provide some guidance
  expect(assistance.solutions).to.be.an('array');
  expect(assistance.solutions.length).to.be.greaterThan(0);
});

Then('it should proactively generate troubleshooting guidance', function() {
  const analysis = this.testContext.predictiveAnalysis;

  expect(analysis).to.have.property('troubleshootingGuidance');
  expect(analysis.troubleshootingGuidance).to.be.an('object');
  expect(analysis.troubleshootingGuidance).to.have.property('steps');
  expect(analysis.troubleshootingGuidance.steps).to.be.an('array');
  expect(analysis.troubleshootingGuidance.steps.length).to.be.greaterThan(0);
});

Then('the guidance should address the specific emerging issue', function() {
  const analysis = this.testContext.predictiveAnalysis;

  expect(analysis).to.have.property('detectedIssue');
  expect(analysis.troubleshootingGuidance).to.have.property('targetIssue');
  expect(analysis.troubleshootingGuidance.targetIssue).to.equal(analysis.detectedIssue.type);
});

Then('it should include preventative steps to avoid failure', function() {
  const analysis = this.testContext.predictiveAnalysis;

  expect(analysis.troubleshootingGuidance).to.have.property('preventativeSteps');
  expect(analysis.troubleshootingGuidance.preventativeSteps).to.be.an('array');
  expect(analysis.troubleshootingGuidance.preventativeSteps.length).to.be.greaterThan(0);
});

Then('it should estimate the urgency of intervention', function() {
  const analysis = this.testContext.predictiveAnalysis;

  expect(analysis).to.have.property('urgencyAssessment');
  expect(analysis.urgencyAssessment).to.be.an('object');
  expect(analysis.urgencyAssessment).to.have.property('level');
  expect(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']).to.include(analysis.urgencyAssessment.level);
  expect(analysis.urgencyAssessment).to.have.property('timeframe');
});

Then('it should recommend optimal timing for maintenance', function() {
  const analysis = this.testContext.predictiveAnalysis;

  expect(analysis).to.have.property('maintenanceRecommendation');
  expect(analysis.maintenanceRecommendation).to.be.an('object');
  expect(analysis.maintenanceRecommendation).to.have.property('recommendedDate');
  expect(analysis.maintenanceRecommendation).to.have.property('maintenanceWindow');
});

Then('it should estimate resource requirements for resolution', function() {
  const analysis = this.testContext.predictiveAnalysis;

  expect(analysis).to.have.property('resourceRequirements');
  expect(analysis.resourceRequirements).to.be.an('object');
  expect(analysis.resourceRequirements).to.have.property('estimatedTime');
  expect(analysis.resourceRequirements).to.have.property('requiredParts');
  expect(analysis.resourceRequirements).to.have.property('skillLevel');
});
