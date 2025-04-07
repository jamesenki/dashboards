/**
 * Step definitions for energy consumption monitoring and optimization scenarios
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
Given('the device has been reporting energy consumption data', async function() {
  const deviceId = this.testContext.currentDeviceId;
  const now = new Date();

  // Generate energy consumption data for the past 30 days
  for (let i = 30; i >= 0; i--) {
    const day = new Date(now);
    day.setDate(now.getDate() - i);

    // Generate multiple readings per day
    for (let hour = 0; hour < 24; hour += 3) {
      const timestamp = new Date(day);
      timestamp.setHours(hour);

      // Create realistic energy consumption pattern with day/night variation
      const isNighttime = hour < 6 || hour > 20;
      const baseConsumption = isNighttime ? 0.15 : 0.25; // kWh per hour
      const variation = Math.random() * 0.05; // Small random variation

      const telemetryData = {
        timestamp,
        energyConsumed: baseConsumption + variation,
        temperature: 120 + (Math.random() * 5 - 2.5),
        pressure: 40 + (Math.random() * 2 - 1),
        mode: hour % 12 === 0 ? (Math.random() > 0.7 ? 'ECO' : 'STANDARD') : undefined
      };

      await this.telemetryService.addHistoricalTelemetry(deviceId, telemetryData);
    }
  }

  // Verify the energy data was created
  const recentData = await this.telemetryService.getHistoricalTelemetry(
    deviceId,
    new Date(now.getTime() - (30 * 24 * 60 * 60 * 1000)),
    now
  );

  expect(recentData.length).to.be.greaterThan(0);
  expect(recentData[0]).to.have.property('energyConsumed');
});

Given('a facility with {int} registered water heaters', async function(count) {
  // Create a group of water heaters for a facility
  this.testContext.facilityDevices = [];

  for (let i = 0; i < count; i++) {
    const deviceId = `energy-test-device-${i}`;

    // Register device
    const device = await this.deviceRepository.registerDevice({
      id: deviceId,
      type: 'water-heater',
      name: `Energy Test Device ${i}`,
      manufacturer: 'Test Manufacturer',
      model: 'Test Model',
      serialNumber: `ENERGY-${i}`,
      firmwareVersion: '1.0.0',
      metadata: {
        facility: 'Test Facility',
        building: 'Building A',
        floor: Math.floor(i / 2) + 1
      }
    });

    // Generate varying energy consumption patterns for each device
    // Some devices are more efficient than others
    const efficiencyFactor = 0.8 + (i * 0.05); // Each device is 5% less efficient than previous

    const now = new Date();
    for (let j = 30; j >= 0; j--) {
      const day = new Date(now);
      day.setDate(now.getDate() - j);

      // One reading per day (simplified)
      const baseConsumption = 5.0; // kWh per day
      const consumption = baseConsumption * efficiencyFactor;

      const telemetryData = {
        timestamp: day,
        energyConsumed: consumption,
        dailyEnergyUsage: consumption, // Explicit daily usage
        costEstimate: consumption * 0.12 // Assuming $0.12 per kWh
      };

      await this.telemetryService.addDailyEnergyData(deviceId, telemetryData);
    }

    this.testContext.facilityDevices.push(device);
  }

  expect(this.testContext.facilityDevices.length).to.equal(count);
});

Given('all devices have been reporting energy consumption data', async function() {
  const facilityDevices = this.testContext.facilityDevices;

  // Verify each device has energy data
  for (const device of facilityDevices) {
    const energyData = await this.telemetryService.getEnergyConsumptionData(
      device.id,
      30 // Days
    );

    expect(energyData.length).to.be.greaterThan(0);
  }
});

Given('the device has {int} months of energy consumption history', async function(months) {
  const deviceId = this.testContext.currentDeviceId;
  const now = new Date();

  // Calculate start date
  const startDate = new Date(now);
  startDate.setMonth(now.getMonth() - months);

  // Generate daily energy data
  let totalDays = Math.round((now - startDate) / (1000 * 60 * 60 * 24));

  for (let i = totalDays; i >= 0; i--) {
    const day = new Date(now);
    day.setDate(now.getDate() - i);

    // Create realistic energy consumption with some seasonal variation
    // Summer months use more energy for cooling water
    const month = day.getMonth();
    const isSummer = month >= 5 && month <= 8;
    const baseConsumption = isSummer ? 5.5 : 5.0; // kWh per day
    const variation = Math.random() * 0.5; // Random daily variation

    // Apply some weekly patterns (weekends vs weekdays)
    const dayOfWeek = day.getDay();
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
    const weekendFactor = isWeekend ? 1.2 : 1.0;

    const consumption = baseConsumption * weekendFactor + variation;

    const telemetryData = {
      timestamp: day,
      energyConsumed: consumption,
      dailyEnergyUsage: consumption,
      costEstimate: consumption * 0.12 // Assuming $0.12 per kWh
    };

    await this.telemetryService.addDailyEnergyData(deviceId, telemetryData);
  }

  // Verify the energy history was created
  const energyHistory = await this.telemetryService.getEnergyConsumptionData(
    deviceId,
    totalDays
  );

  expect(energyHistory.length).to.be.greaterThan(months * 28); // At least months * 28 days of data
});

Given('a facility with diverse device types:', async function(dataTable) {
  const deviceData = dataTable.hashes();
  this.testContext.diverseDevices = [];

  for (const device of deviceData) {
    // Register device
    const registeredDevice = await this.deviceRepository.registerDevice({
      id: device.deviceId,
      type: device.type,
      name: `Test ${device.type}`,
      manufacturer: 'Test Manufacturer',
      model: 'Test Model',
      serialNumber: device.deviceId,
      firmwareVersion: '1.0.0',
      metadata: {
        facility: 'Test Facility'
      }
    });

    // Generate energy consumption data based on device type
    const now = new Date();
    for (let i = 30; i >= 0; i--) {
      const day = new Date(now);
      day.setDate(now.getDate() - i);

      // Different device types have different consumption patterns
      let baseConsumption;
      switch (device.type) {
        case 'water-heater':
          baseConsumption = 5.0;
          break;
        case 'vending-machine':
          baseConsumption = 3.5;
          break;
        case 'hvac':
          baseConsumption = 12.0;
          break;
        default:
          baseConsumption = 4.0;
      }

      const variation = Math.random() * 0.5;
      const consumption = baseConsumption + variation;

      const telemetryData = {
        timestamp: day,
        energyConsumed: consumption,
        dailyEnergyUsage: consumption
      };

      await this.telemetryService.addDailyEnergyData(device.deviceId, telemetryData);
    }

    this.testContext.diverseDevices.push(registeredDevice);
  }

  expect(this.testContext.diverseDevices.length).to.equal(deviceData.length);
});

Given('a facility with historical energy consumption data', async function() {
  // Create facility with historical data - reuse diverse devices if they exist
  if (!this.testContext.diverseDevices) {
    this.testContext.diverseDevices = [];

    // Create a few devices with historical data
    const deviceTypes = ['water-heater', 'vending-machine', 'hvac'];

    for (let i = 0; i < deviceTypes.length; i++) {
      const deviceId = `energy-history-device-${i}`;
      const deviceType = deviceTypes[i];

      // Register device
      const device = await this.deviceRepository.registerDevice({
        id: deviceId,
        type: deviceType,
        name: `Energy History Device ${i}`,
        manufacturer: 'Test Manufacturer',
        model: 'Test Model',
        serialNumber: deviceId,
        firmwareVersion: '1.0.0'
      });

      // Generate 12 months of energy data
      await this.generateHistoricalEnergyData(deviceId, 12);

      this.testContext.diverseDevices.push(device);
    }
  }

  // Verify historical data exists
  for (const device of this.testContext.diverseDevices) {
    const energyData = await this.telemetryService.getEnergyConsumptionData(
      device.id,
      365 // Days
    );

    expect(energyData.length).to.be.greaterThan(0);
  }
});

Given('a set of proposed energy optimization measures:', async function(dataTable) {
  const measures = dataTable.hashes();
  this.testContext.optimizationMeasures = measures;

  // Process each measure
  for (const measure of measures) {
    // Convert cost string to number
    measure.initialCost = parseFloat(measure.initialCost.replace('$', ''));

    // Convert expected savings to decimal
    measure.expectedSavings = parseFloat(measure.expectedSavings) / 100;
  }
});

/**
 * User actions
 */
When('a user with {string} role views the energy dashboard', async function(role) {
  // Set up a user with the specified role
  const user = await this.userService.getUserByRole(role);
  expect(user).to.not.be.null;

  const deviceId = this.testContext.currentDeviceId;

  try {
    // Get energy dashboard data
    const dashboardData = await this.telemetryService.getEnergyDashboard(deviceId);
    this.testContext.energyDashboard = dashboardData;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('a user with {string} role views the energy comparison report', async function(role) {
  // Set up a user with the specified role
  const user = await this.userService.getUserByRole(role);
  expect(user).to.not.be.null;

  const deviceIds = this.testContext.facilityDevices.map(d => d.id);

  try {
    // Get energy comparison report
    const report = await this.analyticsEngine.compareEnergyConsumption(deviceIds);
    this.testContext.energyComparison = report;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('the user views the energy section of their dashboard', async function() {
  const deviceId = this.testContext.currentDeviceId;
  const user = this.testContext.currentUser;

  try {
    // Get energy section data for end user
    const energyData = await this.telemetryService.getEndUserEnergyView(
      deviceId,
      user.id
    );

    this.testContext.endUserEnergyView = energyData;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('a user with {string} role requests optimization recommendations', async function(role) {
  // Set up a user with the specified role
  const user = await this.userService.getUserByRole(role);
  expect(user).to.not.be.null;

  const deviceId = this.testContext.currentDeviceId;

  try {
    // Get energy optimization recommendations
    const recommendations = await this.analyticsEngine.getEnergyOptimizationRecommendations(deviceId);
    this.testContext.energyRecommendations = recommendations;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('the energy optimization system analyzes consumption patterns', async function() {
  const deviceIds = this.testContext.diverseDevices.map(d => d.id);

  try {
    // Analyze cross-device energy optimization opportunities
    const analysis = await this.analyticsEngine.analyzeCrossDeviceEnergyOptimization(deviceIds);
    this.testContext.crossDeviceAnalysis = analysis;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('the business intelligence system analyzes the measures', async function() {
  const measures = this.testContext.optimizationMeasures;
  const facilityId = 'Test Facility';

  try {
    // Analyze ROI for energy measures
    const analysis = await this.analyticsEngine.analyzeEnergyMeasuresROI(
      facilityId,
      measures
    );

    this.testContext.roiAnalysis = analysis;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('the system compares predicted vs. actual savings', async function() {
  // Setup scenario with some measures already implemented
  const deviceId = this.testContext.diverseDevices[0].id;

  // Create historical recommendations with outcomes
  const historicalRecommendations = [
    {
      id: 'rec-1',
      deviceId,
      action: 'Temperature tune',
      predictedSavings: 0.05, // 5%
      actualSavings: 0.037, // 3.7%
      implementationDate: new Date(Date.now() - (60 * 24 * 60 * 60 * 1000)) // 60 days ago
    },
    {
      id: 'rec-2',
      deviceId,
      action: 'Schedule optimize',
      predictedSavings: 0.10, // 10%
      actualSavings: 0.085, // 8.5%
      implementationDate: new Date(Date.now() - (45 * 24 * 60 * 60 * 1000)) // 45 days ago
    },
    {
      id: 'rec-3',
      deviceId,
      action: 'Insulation improvement',
      predictedSavings: 0.15, // 15%
      actualSavings: 0.16, // 16%
      implementationDate: new Date(Date.now() - (30 * 24 * 60 * 60 * 1000)) // 30 days ago
    }
  ];

  // Add historical recommendations to the system
  for (const rec of historicalRecommendations) {
    await this.analyticsEngine.addHistoricalRecommendation(rec);
  }

  try {
    // Analyze prediction accuracy and adjust models
    const learningResults = await this.analyticsEngine.evaluateAndImproveEnergyModels();
    this.testContext.learningResults = learningResults;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

/**
 * Verification steps
 */
Then('the system should display:', function(dataTable) {
  const expectedTypes = dataTable.rowsHash();
  const dashboard = this.testContext.energyDashboard;

  expect(dashboard).to.not.be.null;

  // Verify each expected data type
  for (const [dataType] of Object.entries(expectedTypes)) {
    expect(dashboard).to.have.property(dataType);
  }
});

Then('consumption data should be displayed with appropriate visualizations', function() {
  const dashboard = this.testContext.energyDashboard;

  expect(dashboard).to.have.property('visualizations');
  expect(dashboard.visualizations).to.be.an('array');
  expect(dashboard.visualizations.length).to.be.greaterThan(0);
});

Then('historical trends should be visible', function() {
  const dashboard = this.testContext.energyDashboard;

  expect(dashboard).to.have.property('trends');
  expect(dashboard.trends).to.be.an('object');
  expect(dashboard.trends).to.have.property('daily');
  expect(dashboard.trends).to.have.property('weekly');
  expect(dashboard.trends).to.have.property('monthly');
});

Then('the system should rank devices by energy efficiency', function() {
  const comparison = this.testContext.energyComparison;

  expect(comparison).to.have.property('deviceRankings');
  expect(comparison.deviceRankings).to.be.an('array');
  expect(comparison.deviceRankings.length).to.equal(this.testContext.facilityDevices.length);

  // Verify rankings are in order (most efficient first)
  for (let i = 1; i < comparison.deviceRankings.length; i++) {
    expect(comparison.deviceRankings[i-1].efficiencyScore).to.be.at.least(
      comparison.deviceRankings[i].efficiencyScore
    );
  }
});

Then('it should calculate the average consumption per device', function() {
  const comparison = this.testContext.energyComparison;

  expect(comparison).to.have.property('averageConsumption');
  expect(comparison.averageConsumption).to.be.a('number');
});

Then('it should identify the most and least efficient devices', function() {
  const comparison = this.testContext.energyComparison;

  expect(comparison).to.have.property('mostEfficientDevice');
  expect(comparison).to.have.property('leastEfficientDevice');

  expect(comparison.mostEfficientDevice).to.be.an('object');
  expect(comparison.leastEfficientDevice).to.be.an('object');

  expect(comparison.mostEfficientDevice.id).to.equal(comparison.deviceRankings[0].id);
  expect(comparison.leastEfficientDevice.id).to.equal(
    comparison.deviceRankings[comparison.deviceRankings.length - 1].id
  );
});

Then('it should provide comparative visualizations', function() {
  const comparison = this.testContext.energyComparison;

  expect(comparison).to.have.property('visualizations');
  expect(comparison.visualizations).to.be.an('array');
  expect(comparison.visualizations.length).to.be.greaterThan(0);
});

Then('they should see their current month\'s energy consumption', function() {
  const energyView = this.testContext.endUserEnergyView;

  expect(energyView).to.have.property('currentMonthConsumption');
  expect(energyView.currentMonthConsumption).to.be.a('number');
});

Then('they should see a comparison to typical usage', function() {
  const energyView = this.testContext.endUserEnergyView;

  expect(energyView).to.have.property('comparisonToTypical');
  expect(energyView.comparisonToTypical).to.be.an('object');
  expect(energyView.comparisonToTypical).to.have.property('percentage');
  expect(energyView.comparisonToTypical).to.have.property('descriptor');
});

Then('they should see estimated cost information', function() {
  const energyView = this.testContext.endUserEnergyView;

  expect(energyView).to.have.property('costEstimate');
  expect(energyView.costEstimate).to.be.a('number');
});

Then('they should see energy-saving recommendations', function() {
  const energyView = this.testContext.endUserEnergyView;

  expect(energyView).to.have.property('savingTips');
  expect(energyView.savingTips).to.be.an('array');
  expect(energyView.savingTips.length).to.be.greaterThan(0);
});

Then('the system should provide specific energy-saving recommendations', function() {
  const recommendations = this.testContext.energyRecommendations;

  expect(recommendations).to.not.be.null;
  expect(recommendations).to.be.an('array');
  expect(recommendations.length).to.be.greaterThan(0);
});

Then('each recommendation should include:', function(dataTable) {
  const expectedFields = dataTable.rowsHash();
  const recommendations = this.testContext.energyRecommendations;

  // Check each recommendation has all expected fields
  for (const rec of recommendations) {
    for (const [field] of Object.entries(expectedFields)) {
      expect(rec).to.have.property(field);
    }
  }
});

Then('recommendations should be ordered by potential impact', function() {
  const recommendations = this.testContext.energyRecommendations;

  // Verify recommendations are ordered by potential savings (highest first)
  for (let i = 1; i < recommendations.length; i++) {
    expect(recommendations[i-1].potentialSavings).to.be.at.least(
      recommendations[i].potentialSavings
    );
  }
});

Then('it should identify cross-device optimization opportunities', function() {
  const analysis = this.testContext.crossDeviceAnalysis;

  expect(analysis).to.have.property('opportunities');
  expect(analysis.opportunities).to.be.an('array');
  expect(analysis.opportunities.length).to.be.greaterThan(0);
});

Then('it should recommend load balancing strategies', function() {
  const analysis = this.testContext.crossDeviceAnalysis;

  expect(analysis).to.have.property('loadBalancingStrategies');
  expect(analysis.loadBalancingStrategies).to.be.an('array');
  expect(analysis.loadBalancingStrategies.length).to.be.greaterThan(0);
});

Then('it should suggest optimal operational schedules', function() {
  const analysis = this.testContext.crossDeviceAnalysis;

  expect(analysis).to.have.property('operationalSchedules');
  expect(analysis.operationalSchedules).to.be.an('object');
  expect(analysis.operationalSchedules).to.have.property('peakHours');
  expect(analysis.operationalSchedules).to.have.property('offPeakHours');
});

Then('it should calculate facility-wide potential savings', function() {
  const analysis = this.testContext.crossDeviceAnalysis;

  expect(analysis).to.have.property('facilitySavings');
  expect(analysis.facilitySavings).to.be.an('object');
  expect(analysis.facilitySavings).to.have.property('percentage');
  expect(analysis.facilitySavings).to.have.property('kWh');
  expect(analysis.facilitySavings).to.have.property('cost');
});

Then('it should prioritize recommendations by impact and ease of implementation', function() {
  const analysis = this.testContext.crossDeviceAnalysis;

  expect(analysis).to.have.property('prioritizedRecommendations');
  expect(analysis.prioritizedRecommendations).to.be.an('array');
  expect(analysis.prioritizedRecommendations.length).to.be.greaterThan(0);

  // Each recommendation should have impact and ease scores
  for (const rec of analysis.prioritizedRecommendations) {
    expect(rec).to.have.property('impact');
    expect(rec).to.have.property('ease');
    expect(rec).to.have.property('priority');
  }
});

Then('it should calculate the ROI for each measure', function() {
  const analysis = this.testContext.roiAnalysis;

  expect(analysis).to.have.property('measures');
  expect(analysis.measures).to.be.an('array');
  expect(analysis.measures.length).to.equal(this.testContext.optimizationMeasures.length);

  // Each measure should have ROI information
  for (const measure of analysis.measures) {
    expect(measure).to.have.property('roi');
    expect(measure.roi).to.be.a('number');
  }
});

Then('it should determine the optimal implementation sequence', function() {
  const analysis = this.testContext.roiAnalysis;

  expect(analysis).to.have.property('implementationSequence');
  expect(analysis.implementationSequence).to.be.an('array');
  expect(analysis.implementationSequence.length).to.equal(this.testContext.optimizationMeasures.length);
});

Then('it should project cumulative savings over {int}, {int}, and {int} years', function(year1, year3, year5) {
  const analysis = this.testContext.roiAnalysis;

  expect(analysis).to.have.property('projectedSavings');
  expect(analysis.projectedSavings).to.be.an('object');

  expect(analysis.projectedSavings).to.have.property(`${year1}year`);
  expect(analysis.projectedSavings).to.have.property(`${year3}year`);
  expect(analysis.projectedSavings).to.have.property(`${year5}year`);
});

Then('it should account for energy price trends in projections', function() {
  const analysis = this.testContext.roiAnalysis;

  expect(analysis).to.have.property('assumptions');
  expect(analysis.assumptions).to.be.an('object');
  expect(analysis.assumptions).to.have.property('energyPriceTrend');
});

Then('it should recommend the measures with the best ROI', function() {
  const analysis = this.testContext.roiAnalysis;

  expect(analysis).to.have.property('topRecommendations');
  expect(analysis.topRecommendations).to.be.an('array');
  expect(analysis.topRecommendations.length).to.be.greaterThan(0);
});

Then('it should adjust its energy prediction models to improve accuracy', function() {
  const results = this.testContext.learningResults;

  expect(results).to.have.property('modelAdjustments');
  expect(results.modelAdjustments).to.be.an('array');
  expect(results.modelAdjustments.length).to.be.greaterThan(0);
});

Then('it should refine future recommendations based on actual results', function() {
  const results = this.testContext.learningResults;

  expect(results).to.have.property('refinedRecommendations');
  expect(results.refinedRecommendations).to.be.an('array');
});

Then('it should identify patterns in recommendation effectiveness', function() {
  const results = this.testContext.learningResults;

  expect(results).to.have.property('effectivenessPatterns');
  expect(results.effectivenessPatterns).to.be.an('array');
  expect(results.effectivenessPatterns.length).to.be.greaterThan(0);
});

Then('it should generate an optimization strategy that maximizes proven results', function() {
  const results = this.testContext.learningResults;

  expect(results).to.have.property('optimizedStrategy');
  expect(results.optimizedStrategy).to.be.an('object');
  expect(results.optimizedStrategy).to.have.property('recommendations');
  expect(results.optimizedStrategy).to.have.property('expectedSavings');
  expect(results.optimizedStrategy).to.have.property('confidence');
});
