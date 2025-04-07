/**
 * Step definitions for cross-device fleet-wide optimization scenarios
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
Given('a diverse fleet of connected devices across multiple facilities', async function() {
  // Create diverse device fleet across facilities
  this.testContext.fleetDevices = {
    'Facility A': [],
    'Facility B': [],
    'Facility C': []
  };

  // Device types to create across facilities
  const deviceTypes = [
    { type: 'water-heater', count: 3 },
    { type: 'vending-machine', count: 2 },
    { type: 'hvac', count: 2 }
  ];

  // Create devices for each facility
  for (const [facility, devices] of Object.entries(this.testContext.fleetDevices)) {
    for (const deviceType of deviceTypes) {
      for (let i = 0; i < deviceType.count; i++) {
        const deviceId = `${facility.toLowerCase().replace(/\s+/g, '-')}-${deviceType.type}-${i+1}`;

        // Register device
        const device = await this.deviceRepository.registerDevice({
          id: deviceId,
          type: deviceType.type,
          name: `${facility} ${deviceType.type} ${i+1}`,
          manufacturer: 'Test Manufacturer',
          model: 'Test Model',
          serialNumber: deviceId,
          firmwareVersion: '1.0.0',
          metadata: {
            facility: facility,
            building: `Building ${facility.slice(-1)}`,
            floor: Math.floor(i / 2) + 1
          }
        });

        // Generate basic telemetry appropriate for device type
        let telemetryData;

        switch (deviceType.type) {
          case 'water-heater':
            telemetryData = {
              temperature: 120 + (Math.random() * 10 - 5),
              pressure: 40 + (Math.random() * 4 - 2),
              energyConsumed: 5.0 + (Math.random() * 1),
              mode: Math.random() > 0.3 ? 'STANDARD' : 'ECO'
            };
            break;
          case 'vending-machine':
            telemetryData = {
              temperature: 38 + (Math.random() * 6 - 3),
              doorStatus: 'CLOSED',
              stockLevel: Math.floor(Math.random() * 30) + 70,
              cashBalance: Math.floor(Math.random() * 100) + 50
            };
            break;
          case 'hvac':
            telemetryData = {
              temperature: 68 + (Math.random() * 6 - 3),
              humidity: 45 + (Math.random() * 10 - 5),
              energyConsumed: 10.0 + (Math.random() * 2),
              mode: Math.random() > 0.5 ? 'COOLING' : 'HEATING'
            };
            break;
          default:
            telemetryData = {
              status: 'ONLINE',
              lastActivity: new Date()
            };
        }

        await this.telemetryService.addTelemetryData(deviceId, telemetryData);

        // Generate some operational history (30 days)
        const now = new Date();
        const startDate = new Date(now);
        startDate.setDate(now.getDate() - 30);

        await this.generateDeviceTypeSpecificHistory(deviceId, deviceType.type, startDate, now);

        this.testContext.fleetDevices[facility].push(device);
      }
    }
  }

  // Verify fleet was created
  let totalDevices = 0;
  for (const facilityDevices of Object.values(this.testContext.fleetDevices)) {
    totalDevices += facilityDevices.length;
  }

  const expectedTotal = deviceTypes.reduce((sum, dt) => sum + dt.count, 0) * 3; // 3 facilities
  expect(totalDevices).to.equal(expectedTotal);
});

Given('operational data for all devices', function() {
  // Already set up in previous step
  let totalDevices = 0;
  for (const facilityDevices of Object.values(this.testContext.fleetDevices)) {
    totalDevices += facilityDevices.length;
  }
  expect(totalDevices).to.be.greaterThan(0);
});

Given('a facility with operational and financial data', async function() {
  if (!this.testContext.fleetDevices) {
    // Create a facility with devices if not already created
    this.testContext.facilityData = {
      name: 'Financial Analysis Facility',
      devices: [],
      financialData: {
        energyCost: 0.12, // $ per kWh
        laborCost: 85, // $ per hour
        maintenanceBudget: 25000, // $ annual
        deviceReplacementBudget: 50000 // $ annual
      }
    };

    // Create diverse device types
    const deviceTypes = [
      { type: 'water-heater', count: 5 },
      { type: 'vending-machine', count: 3 },
      { type: 'hvac', count: 4 }
    ];

    for (const deviceType of deviceTypes) {
      for (let i = 0; i < deviceType.count; i++) {
        const deviceId = `financial-${deviceType.type}-${i+1}`;

        // Register device with age and efficiency data
        const ageYears = Math.floor(Math.random() * 8) + 1; // 1-8 years old
        const efficiency = Math.max(0.6, 1 - (ageYears * 0.05)); // Efficiency decreases with age

        const device = await this.deviceRepository.registerDevice({
          id: deviceId,
          type: deviceType.type,
          name: `Financial ${deviceType.type} ${i+1}`,
          manufacturer: 'Test Manufacturer',
          model: 'Test Model',
          serialNumber: deviceId,
          firmwareVersion: '1.0.0',
          installationDate: new Date(Date.now() - (ageYears * 365 * 24 * 60 * 60 * 1000)),
          metadata: {
            facility: this.testContext.facilityData.name,
            efficiency: efficiency,
            replacementCost: deviceType.type === 'water-heater' ? 1200 :
                             deviceType.type === 'vending-machine' ? 3500 :
                             5000
          }
        });

        // Generate operational history
        const now = new Date();
        const startDate = new Date(now);
        startDate.setMonth(now.getMonth() - 12); // 1 year of data

        await this.generateDeviceTypeSpecificHistory(deviceId, deviceType.type, startDate, now);

        this.testContext.facilityData.devices.push(device);
      }
    }
  }

  // Verify facility data was created
  expect(this.testContext.facilityData.devices.length).to.be.greaterThan(0);
});

/**
 * User actions
 */
When('the business intelligence system performs a fleet-wide analysis', async function() {
  // Gather all device IDs across facilities
  const allDeviceIds = [];
  for (const facilityDevices of Object.values(this.testContext.fleetDevices)) {
    allDeviceIds.push(...facilityDevices.map(d => d.id));
  }

  try {
    // Perform fleet-wide analysis
    const analysisResults = await this.analyticsEngine.performFleetOptimizationAnalysis(allDeviceIds);
    this.testContext.fleetAnalysis = analysisResults;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('a user with {string} role conducts a {string} analysis', async function(role, analysisType) {
  // Set up user with specified role
  const user = await this.userService.getUserByRole(role);
  expect(user).to.not.be.null;

  // Store analysis type
  this.testContext.analysisType = analysisType;
});

When('selects parameters:', async function(dataTable) {
  const parameters = dataTable.rowsHash();

  // Process parameters to appropriate types
  const processedParams = {};
  for (const [param, value] of Object.entries(parameters)) {
    // Process value based on format
    if (value.includes('%')) {
      processedParams[param] = parseFloat(value) / 100;
    } else if (!isNaN(value)) {
      processedParams[param] = parseFloat(value);
    } else {
      processedParams[param] = value;
    }
  }

  try {
    // Perform what-if analysis
    const deviceIds = this.testContext.facilityData.devices.map(d => d.id);
    const analysisResults = await this.analyticsEngine.generateScenarioProjection(
      processedParams
    );

    this.testContext.scenarioAnalysis = analysisResults;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

/**
 * Verification steps
 */
Then('it should identify optimization opportunities across device types', function() {
  const analysis = this.testContext.fleetAnalysis;

  expect(analysis).to.have.property('opportunities');
  expect(analysis.opportunities).to.be.an('array');
  expect(analysis.opportunities.length).to.be.greaterThan(0);

  // Check if opportunities span multiple device types
  const deviceTypes = new Set();
  for (const opportunity of analysis.opportunities) {
    expect(opportunity).to.have.property('affectedDevices');

    for (const device of opportunity.affectedDevices) {
      deviceTypes.add(device.type);
    }
  }

  // Should have opportunities for at least 2 different device types
  expect(deviceTypes.size).to.be.greaterThan(1);
});

Then('it should quantify the potential impact of each opportunity', function() {
  const analysis = this.testContext.fleetAnalysis;

  for (const opportunity of analysis.opportunities) {
    expect(opportunity).to.have.property('potentialImpact');
    expect(opportunity.potentialImpact).to.be.an('object');
    expect(opportunity.potentialImpact).to.have.property('financial');
    expect(opportunity.potentialImpact).to.have.property('operational');
    expect(opportunity.potentialImpact).to.have.property('environmental');
  }
});

Then('it should prioritize recommendations based on:', function(dataTable) {
  const criteria = dataTable.rowsHash();
  const analysis = this.testContext.fleetAnalysis;

  expect(analysis).to.have.property('prioritizedRecommendations');
  expect(analysis.prioritizedRecommendations).to.be.an('array');
  expect(analysis.prioritizedRecommendations.length).to.be.greaterThan(0);

  // Check each recommendation has all criteria
  for (const recommendation of analysis.prioritizedRecommendations) {
    for (const [criterion] of Object.entries(criteria)) {
      // Convert to camelCase
      const propertyName = criterion
        .toLowerCase()
        .replace(/[^a-z0-9]+(.)/g, (match, chr) => chr.toUpperCase());

      expect(recommendation).to.have.property(propertyName);
    }
  }

  // Check recommendations are actually sorted by priority
  for (let i = 1; i < analysis.prioritizedRecommendations.length; i++) {
    const prevPriority = analysis.prioritizedRecommendations[i-1].priority;
    const currPriority = analysis.prioritizedRecommendations[i].priority;

    expect(prevPriority).to.be.at.least(currPriority);
  }
});

Then('it should provide implementation guidance for top recommendations', function() {
  const analysis = this.testContext.fleetAnalysis;

  expect(analysis).to.have.property('implementationGuidance');
  expect(analysis.implementationGuidance).to.be.an('object');

  // Check guidance for top recommendations
  const topRecommendations = analysis.prioritizedRecommendations.slice(0, 3);

  for (const rec of topRecommendations) {
    expect(analysis.implementationGuidance).to.have.property(rec.id);
    expect(analysis.implementationGuidance[rec.id]).to.be.an('object');
    expect(analysis.implementationGuidance[rec.id]).to.have.property('steps');
    expect(analysis.implementationGuidance[rec.id]).to.have.property('resources');
    expect(analysis.implementationGuidance[rec.id]).to.have.property('timeline');
  }
});

Then('the system should generate a {int}-year projection model', function(years) {
  const analysis = this.testContext.scenarioAnalysis;

  expect(analysis).to.have.property('projectionYears');
  expect(analysis.projectionYears).to.equal(years);
  expect(analysis).to.have.property('projectionData');
  expect(analysis.projectionData).to.be.an('object');

  // Should have data for each year
  for (let i = 1; i <= years; i++) {
    expect(analysis.projectionData).to.have.property(`year${i}`);
  }
});

Then('the model should include:', function(dataTable) {
  const expectedElements = dataTable.rowsHash();
  const analysis = this.testContext.scenarioAnalysis;

  // Check each year has all expected elements
  for (let i = 1; i <= analysis.projectionYears; i++) {
    const yearData = analysis.projectionData[`year${i}`];

    for (const [element] of Object.entries(expectedElements)) {
      // Convert to camelCase
      const propertyName = element
        .toLowerCase()
        .replace(/[^a-z0-9]+(.)/g, (match, chr) => chr.toUpperCase());

      expect(yearData).to.have.property(propertyName);
    }
  }
});

Then('the model should compare against baseline scenarios', function() {
  const analysis = this.testContext.scenarioAnalysis;

  expect(analysis).to.have.property('baselineComparison');
  expect(analysis.baselineComparison).to.be.an('object');

  // Check comparison metrics
  expect(analysis.baselineComparison).to.have.property('costDifference');
  expect(analysis.baselineComparison).to.have.property('reliabilityDifference');
  expect(analysis.baselineComparison).to.have.property('energyDifference');
});

Then('sensitivity analysis should be provided for key variables', function() {
  const analysis = this.testContext.scenarioAnalysis;

  expect(analysis).to.have.property('sensitivityAnalysis');
  expect(analysis.sensitivityAnalysis).to.be.an('object');
  expect(analysis.sensitivityAnalysis).to.have.property('variables');
  expect(analysis.sensitivityAnalysis.variables).to.be.an('array');
  expect(analysis.sensitivityAnalysis.variables.length).to.be.greaterThan(0);

  // Each variable should have sensitivity data
  for (const variable of analysis.sensitivityAnalysis.variables) {
    expect(variable).to.have.property('name');
    expect(variable).to.have.property('impact');
    expect(variable).to.have.property('elasticity');
  }
});
