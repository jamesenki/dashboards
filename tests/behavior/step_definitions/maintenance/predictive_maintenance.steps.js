/**
 * Step definitions for predictive maintenance and health assessment scenarios
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
Given('the device has {int} months of operational history', async function(months) {
  const deviceId = this.testContext.currentDeviceId;

  // Calculate the start date
  const now = new Date();
  const startDate = new Date(now);
  startDate.setMonth(now.getMonth() - months);

  // Generate simulated operational history
  await this.generateOperationalHistory(deviceId, startDate, now);

  // Verify the history was created
  const history = await this.telemetryService.getHistoricalTelemetry(
    deviceId,
    startDate,
    now
  );

  expect(history.length).to.be.greaterThan(0);
});

Given('the device has shown increasing temperature fluctuations', async function() {
  const deviceId = this.testContext.currentDeviceId;
  const now = new Date();

  // Generate telemetry with increasing fluctuations over time
  // Last 7 days with increasing fluctuations
  for (let i = 7; i >= 0; i--) {
    const day = new Date(now);
    day.setDate(now.getDate() - i);

    // Multiple readings per day with increasing fluctuations
    for (let hour = 0; hour < 24; hour += 3) {
      const timestamp = new Date(day);
      timestamp.setHours(hour);

      // Fluctuation amplitude increases as we get closer to current date
      const fluctuationAmplitude = 2 + ((7 - i) * 0.5);
      const temperatureBase = 120;
      const temperature = temperatureBase + (Math.sin(hour) * fluctuationAmplitude);

      const telemetryData = {
        timestamp,
        temperature,
        pressure: 40 + (Math.random() * 2 - 1),
        energyConsumed: 5.2 + (hour * 0.05),
        mode: 'STANDARD'
      };

      await this.telemetryService.addHistoricalTelemetry(deviceId, telemetryData);
    }
  }

  // Verify the fluctuating data was created
  const recentData = await this.telemetryService.getHistoricalTelemetry(
    deviceId,
    new Date(now.getTime() - (7 * 24 * 60 * 60 * 1000)),
    now
  );

  expect(recentData.length).to.be.greaterThan(40); // At least some hourly readings
});

Given('the device has a health assessment with a score of {string}', async function(score) {
  const deviceId = this.testContext.currentDeviceId;
  const healthScore = parseInt(score);

  // Generate a health assessment with the specified score
  const assessment = {
    deviceId,
    overallScore: healthScore,
    componentScores: {
      heatingElement: healthScore - 5,
      thermostat: healthScore + 10,
      pressureRelief: healthScore - 2,
      tankIntegrity: healthScore + 5
    },
    estimatedLifespan: `${Math.max(1, Math.floor(healthScore / 10))} years`,
    confidenceLevel: 0.85,
    timestamp: new Date()
  };

  // Store the assessment in the analytics engine
  await this.analyticsEngine.saveHealthAssessment(deviceId, assessment);

  // Verify the assessment was created
  const savedAssessment = await this.analyticsEngine.getHealthAssessment(deviceId);
  expect(savedAssessment).to.not.be.null;
  expect(savedAssessment.overallScore).to.equal(healthScore);
});

Given('multiple water heaters with completed maintenance records', async function() {
  // Create a group of test devices with maintenance history
  this.testContext.deviceGroup = [];

  for (let i = 0; i < 5; i++) {
    const deviceId = `maintenance-test-device-${i}`;

    // Register device
    const device = await this.deviceRepository.registerDevice({
      id: deviceId,
      type: 'water-heater',
      name: `Maintenance Test Device ${i}`,
      manufacturer: 'Test Manufacturer',
      model: 'Test Model',
      serialNumber: `MAINT-${i}`,
      firmwareVersion: '1.0.0'
    });

    // Add maintenance records
    const maintenanceRecords = [];
    const now = new Date();

    // Add 3 maintenance records per device
    for (let j = 0; j < 3; j++) {
      const date = new Date(now);
      date.setMonth(now.getMonth() - (j * 2));

      const record = {
        id: `record-${deviceId}-${j}`,
        deviceId,
        date,
        type: j === 0 ? 'PREVENTIVE' : (j === 1 ? 'REACTIVE' : 'INSPECTION'),
        technician: 'Test Technician',
        description: `Maintenance activity ${j}`,
        findings: 'Normal wear and tear',
        actions: 'Standard maintenance performed',
        parts: j === 1 ? ['Heating element', 'Thermostat'] : [],
        cost: j === 1 ? 250 : 100,
        downtime: j === 1 ? 4 : 1 // hours
      };

      maintenanceRecords.push(record);
    }

    // Store maintenance records
    for (const record of maintenanceRecords) {
      await this.analyticsEngine.addMaintenanceRecord(deviceId, record);
    }

    // Add predictions for each maintenance event
    for (const record of maintenanceRecords) {
      // Create a prediction that would have been made before the maintenance
      const predictionDate = new Date(record.date);
      predictionDate.setMonth(record.date.getMonth() - 1);

      const prediction = {
        deviceId,
        date: predictionDate,
        predictedIssue: record.type === 'REACTIVE' ? 'Heating element failure' : 'Routine maintenance',
        recommendedDate: record.date,
        actualDate: record.date,
        confidence: 0.75,
        accuracy: Math.random() * 0.3 + 0.7 // Random accuracy between 70-100%
      };

      await this.analyticsEngine.addMaintenancePrediction(deviceId, prediction);
    }

    this.testContext.deviceGroup.push(device);
  }

  expect(this.testContext.deviceGroup.length).to.equal(5);
});

Given('previous predictions exist for each maintenance event', async function() {
  // Already set up in the previous step
  const deviceGroup = this.testContext.deviceGroup;

  // Verify predictions exist
  for (const device of deviceGroup) {
    const predictions = await this.analyticsEngine.getMaintenancePredictions(device.id);
    expect(predictions.length).to.be.greaterThan(0);
  }
});

Given('a facility with multiple devices of the same type', async function() {
  // Create a group of test devices with different maintenance approaches
  this.testContext.facilityDevices = {
    preventive: [],
    reactive: []
  };

  // Create preventive maintenance devices
  for (let i = 0; i < 5; i++) {
    const deviceId = `preventive-device-${i}`;

    // Register device
    const device = await this.deviceRepository.registerDevice({
      id: deviceId,
      type: 'water-heater',
      name: `Preventive Device ${i}`,
      manufacturer: 'Test Manufacturer',
      model: 'Test Model',
      serialNumber: `PREV-${i}`,
      firmwareVersion: '1.0.0',
      metadata: {
        facility: 'Test Facility',
        maintenanceStrategy: 'PREVENTIVE'
      }
    });

    // Add maintenance history - regular preventive maintenance
    const now = new Date();
    for (let j = 0; j < 6; j++) {
      const date = new Date(now);
      date.setMonth(now.getMonth() - j * 2);

      const record = {
        id: `prev-record-${deviceId}-${j}`,
        deviceId,
        date,
        type: 'PREVENTIVE',
        description: 'Scheduled preventive maintenance',
        cost: 100,
        downtime: 1 // hours
      };

      await this.analyticsEngine.addMaintenanceRecord(deviceId, record);
    }

    this.testContext.facilityDevices.preventive.push(device);
  }

  // Create reactive maintenance devices
  for (let i = 0; i < 5; i++) {
    const deviceId = `reactive-device-${i}`;

    // Register device
    const device = await this.deviceRepository.registerDevice({
      id: deviceId,
      type: 'water-heater',
      name: `Reactive Device ${i}`,
      manufacturer: 'Test Manufacturer',
      model: 'Test Model',
      serialNumber: `REACT-${i}`,
      firmwareVersion: '1.0.0',
      metadata: {
        facility: 'Test Facility',
        maintenanceStrategy: 'REACTIVE'
      }
    });

    // Add maintenance history - less frequent but more costly reactive maintenance
    const now = new Date();
    for (let j = 0; j < 3; j++) {
      const date = new Date(now);
      date.setMonth(now.getMonth() - j * 4);

      const record = {
        id: `react-record-${deviceId}-${j}`,
        deviceId,
        date,
        type: 'REACTIVE',
        description: 'Emergency repair after failure',
        cost: 350,
        downtime: 8 // hours
      };

      await this.analyticsEngine.addMaintenanceRecord(deviceId, record);
    }

    this.testContext.facilityDevices.reactive.push(device);
  }

  expect(this.testContext.facilityDevices.preventive.length).to.equal(5);
  expect(this.testContext.facilityDevices.reactive.length).to.equal(5);
});

Given('some devices follow preventive maintenance schedules', function() {
  // Already set up in previous step
  expect(this.testContext.facilityDevices.preventive.length).to.be.greaterThan(0);
});

Given('others follow reactive maintenance approaches', function() {
  // Already set up in previous step
  expect(this.testContext.facilityDevices.reactive.length).to.be.greaterThan(0);
});

/**
 * User actions
 */
When('a user with {string} role requests a health assessment', async function(role) {
  // Set up a user with the specified role
  const user = await this.userService.getUserByRole(role);
  expect(user).to.not.be.null;

  const deviceId = this.testContext.currentDeviceId;

  try {
    // Request a health assessment
    const assessment = await this.analyticsEngine.generateHealthAssessment(deviceId);
    this.testContext.healthAssessment = assessment;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('the predictive maintenance system analyzes the device', async function() {
  const deviceId = this.testContext.currentDeviceId;

  try {
    // Analyze the device for potential failures
    const prediction = await this.analyticsEngine.predictComponentFailures(deviceId);
    this.testContext.failurePrediction = prediction;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('a user with {string} role views maintenance recommendations', async function(role) {
  // Set up a user with the specified role
  const user = await this.userService.getUserByRole(role);
  expect(user).to.not.be.null;

  const deviceId = this.testContext.currentDeviceId;

  try {
    // Get maintenance recommendations
    const recommendations = await this.analyticsEngine.getMaintenanceRecommendations(deviceId);
    this.testContext.maintenanceRecommendations = recommendations;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('the system analyzes prediction accuracy against actual outcomes', async function() {
  const deviceGroup = this.testContext.deviceGroup;
  const deviceIds = deviceGroup.map(d => d.id);

  try {
    // Analyze prediction accuracy
    const accuracy = await this.analyticsEngine.analyzePredictionAccuracy(deviceIds);
    this.testContext.accuracyAnalysis = accuracy;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('the business intelligence system compares maintenance outcomes', async function() {
  const facilityDevices = this.testContext.facilityDevices;
  const preventiveIds = facilityDevices.preventive.map(d => d.id);
  const reactiveIds = facilityDevices.reactive.map(d => d.id);

  try {
    // Compare maintenance approaches
    const comparison = await this.analyticsEngine.compareMaintenanceApproaches(
      preventiveIds,
      reactiveIds
    );

    this.testContext.maintenanceComparison = comparison;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

/**
 * Verification steps
 */
Then('the system should generate a health assessment with:', function(dataTable) {
  const expectedFields = dataTable.rowsHash();
  const assessment = this.testContext.healthAssessment;

  expect(assessment).to.not.be.null;

  // Verify each field in the assessment
  for (const [field, description] of Object.entries(expectedFields)) {
    expect(assessment).to.have.property(field);
  }

  // Check specific field types
  expect(typeof assessment.overallScore).to.equal('number');
  expect(assessment.overallScore).to.be.within(0, 100);

  expect(assessment.componentScores).to.be.an('object');
  expect(Object.keys(assessment.componentScores).length).to.be.greaterThan(0);

  expect(assessment.estimatedLifespan).to.be.a('string');
  expect(assessment.confidenceLevel).to.be.a('number');
  expect(assessment.confidenceLevel).to.be.within(0, 1);
});

Then('the assessment should be based on actual operational data', function() {
  const assessment = this.testContext.healthAssessment;

  expect(assessment).to.have.property('dataPoints');
  expect(assessment.dataPoints).to.be.a('number');
  expect(assessment.dataPoints).to.be.greaterThan(0);
});

Then('the results should be displayed with appropriate visualizations', function() {
  const assessment = this.testContext.healthAssessment;

  expect(assessment).to.have.property('visualizations');
  expect(assessment.visualizations).to.be.an('array');
  expect(assessment.visualizations.length).to.be.greaterThan(0);
});

Then('it should identify potential heating element failure', function() {
  const prediction = this.testContext.failurePrediction;

  expect(prediction).to.not.be.null;
  expect(prediction.componentsAtRisk).to.be.an('array');

  const heatingElementPrediction = prediction.componentsAtRisk.find(
    c => c.component.toLowerCase().includes('heating') ||
         c.component.toLowerCase().includes('element')
  );

  expect(heatingElementPrediction).to.not.be.undefined;
});

Then('it should predict when the failure is likely to occur', function() {
  const prediction = this.testContext.failurePrediction;
  const heatingElementPrediction = prediction.componentsAtRisk.find(
    c => c.component.toLowerCase().includes('heating') ||
         c.component.toLowerCase().includes('element')
  );

  expect(heatingElementPrediction).to.have.property('estimatedTimeToFailure');
  expect(heatingElementPrediction.estimatedTimeToFailure).to.be.a('string');
});

Then('it should specify the confidence level of the prediction', function() {
  const prediction = this.testContext.failurePrediction;
  const heatingElementPrediction = prediction.componentsAtRisk.find(
    c => c.component.toLowerCase().includes('heating') ||
         c.component.toLowerCase().includes('element')
  );

  expect(heatingElementPrediction).to.have.property('confidence');
  expect(heatingElementPrediction.confidence).to.be.a('number');
  expect(heatingElementPrediction.confidence).to.be.within(0, 1);
});

Then('it should recommend preventative maintenance actions', function() {
  const prediction = this.testContext.failurePrediction;

  expect(prediction).to.have.property('recommendedActions');
  expect(prediction.recommendedActions).to.be.an('array');
  expect(prediction.recommendedActions.length).to.be.greaterThan(0);
});

Then('the system should provide specific maintenance actions', function() {
  const recommendations = this.testContext.maintenanceRecommendations;

  expect(recommendations).to.not.be.null;
  expect(recommendations).to.be.an('array');
  expect(recommendations.length).to.be.greaterThan(0);

  // Check that each recommendation has an action
  for (const rec of recommendations) {
    expect(rec).to.have.property('action');
    expect(rec.action).to.be.a('string');
    expect(rec.action.length).to.be.greaterThan(0);
  }
});

Then('each maintenance recommendation should include:', function(dataTable) {
  const expectedFields = dataTable.rowsHash();
  const recommendations = this.testContext.maintenanceRecommendations;

  // Check each recommendation has all expected fields
  for (const rec of recommendations) {
    for (const [field, description] of Object.entries(expectedFields)) {
      expect(rec).to.have.property(field);
    }
  }
});

Then('recommendations should be ordered by priority', function() {
  const recommendations = this.testContext.maintenanceRecommendations;

  // Priority order mapping (same as in the mock implementation)
  const priorityOrder = {
    'high': 1,
    'medium-high': 2,
    'medium': 3,
    'medium-low': 4,
    'low': 5
  };

  // Verify priorities are in correct order (highest priority first)
  for (let i = 1; i < recommendations.length; i++) {
    const priorityA = priorityOrder[recommendations[i-1].priority] || 999;
    const priorityB = priorityOrder[recommendations[i].priority] || 999;

    // Lower values in the mapping mean higher priority
    expect(priorityA).to.be.at.most(priorityB,
      `Expected recommendation at index ${i-1} with priority ${recommendations[i-1].priority} to be higher priority than ` +
      `recommendation at index ${i} with priority ${recommendations[i].priority}`);
  }
});

Then('it should adjust its prediction models to improve accuracy', function() {
  const analysis = this.testContext.accuracyAnalysis;

  expect(analysis).to.have.property('modelAdjustments');
  expect(analysis.modelAdjustments).to.be.an('array');
  expect(analysis.modelAdjustments.length).to.be.greaterThan(0);
});

Then('it should generate a model improvement report showing:', function(dataTable) {
  const expectedFields = dataTable.rowsHash();
  const analysis = this.testContext.accuracyAnalysis;

  expect(analysis).to.have.property('improvementReport');
  const report = analysis.improvementReport;

  // Verify report has all expected fields
  for (const [field, description] of Object.entries(expectedFields)) {
    expect(report).to.have.property(field);
  }

  // Check specific field types
  expect(report.previousAccuracy).to.be.a('number');
  expect(report.newAccuracy).to.be.a('number');
  expect(report.improvementRate).to.be.a('number');
  expect(report.keyFactors).to.be.an('array');
});

Then('subsequent predictions should demonstrate improved accuracy', function() {
  const analysis = this.testContext.accuracyAnalysis;

  expect(analysis.improvementReport.newAccuracy).to.be.greaterThan(
    analysis.improvementReport.previousAccuracy
  );
});

Then('it should calculate the ROI of preventive vs. reactive maintenance', function() {
  const comparison = this.testContext.maintenanceComparison;

  expect(comparison).to.have.property('roi');
  expect(comparison.roi).to.be.an('object');
  expect(comparison.roi).to.have.property('value');
  expect(comparison.roi.value).to.be.a('number');
});

Then('it should quantify:', function(dataTable) {
  const expectedFields = dataTable.rowsHash();
  const comparison = this.testContext.maintenanceComparison;

  // Verify comparison has all expected fields
  for (const [field, description] of Object.entries(expectedFields)) {
    expect(comparison).to.have.property(field);
  }
});

Then('it should recommend the most cost-effective maintenance strategy', function() {
  const comparison = this.testContext.maintenanceComparison;

  expect(comparison).to.have.property('recommendedStrategy');
  expect(comparison.recommendedStrategy).to.be.a('string');
  expect(['PREVENTIVE', 'REACTIVE', 'HYBRID']).to.include(comparison.recommendedStrategy);
});
