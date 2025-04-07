/**
 * Step definitions for intelligent device fleet optimization scenarios
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
Given('a facility with multiple device types with varying:', async function(dataTable) {
  // Extract properties that vary across devices
  const variableProperties = dataTable.rowsHash();

  // Create a diverse set of devices with varying properties
  this.testContext.optimizationDevices = [];

  // Define device types to create
  const deviceTypes = ['water-heater', 'vending-machine', 'hvac', 'robot'];
  const deviceCounts = {
    'water-heater': 6,
    'vending-machine': 4,
    'hvac': 5,
    'robot': 3
  };

  for (const deviceType of deviceTypes) {
    for (let i = 0; i < deviceCounts[deviceType]; i++) {
      const deviceId = `opt-${deviceType}-${i+1}`;

      // Generate varying values for each property
      const age = generateVariedValue('age', i, deviceCounts[deviceType]);
      const efficiency = generateVariedValue('efficiency', i, deviceCounts[deviceType]);
      const reliability = generateVariedValue('reliability', i, deviceCounts[deviceType]);
      const utilization = generateVariedValue('utilization', i, deviceCounts[deviceType]);

      // Register device
      const device = await this.deviceRepository.registerDevice({
        id: deviceId,
        type: deviceType,
        name: `${deviceType.charAt(0).toUpperCase() + deviceType.slice(1)} ${i+1}`,
        manufacturer: 'Test Manufacturer',
        model: 'Test Model',
        serialNumber: deviceId,
        firmwareVersion: '1.0.0',
        installationDate: calculateInstallationDate(age),
        metadata: {
          facility: 'Optimization Facility',
          building: 'Main Building',
          floor: Math.floor(i / 2) + 1,
          efficiency: efficiency,
          reliability: reliability,
          utilization: utilization
        }
      });

      // Add device-specific telemetry and operational data
      await this.generateDeviceTypeSpecificHistory(
        deviceId,
        deviceType,
        new Date(Date.now() - (90 * 24 * 60 * 60 * 1000)), // 90 days ago
        new Date()
      );

      this.testContext.optimizationDevices.push(device);
    }
  }

  // Helper function to generate varied values for each property
  function generateVariedValue(property, index, totalCount) {
    // Distribute values across the range specified in the step
    const position = index / (totalCount - 1); // 0 to 1 based on position in array

    switch(property) {
      case 'age':
        // Range from new to end-of-life (0-10 years)
        return position * 10;
      case 'efficiency':
        // Range from high to low efficiency (0.9-0.4)
        return 0.9 - (position * 0.5);
      case 'reliability':
        // Range from reliable to problematic (0.99-0.6)
        return 0.99 - (position * 0.39);
      case 'utilization':
        // Range from high to low usage (0.9-0.1)
        return 0.9 - (position * 0.8);
      default:
        return 0.5; // Default mid-range value
    }
  }

  // Helper function to calculate installation date based on age in years
  function calculateInstallationDate(ageYears) {
    const now = new Date();
    const installDate = new Date(now);
    installDate.setFullYear(now.getFullYear() - Math.floor(ageYears));
    installDate.setMonth(now.getMonth() - Math.round((ageYears % 1) * 12));
    return installDate;
  }

  // Verify devices were created
  expect(this.testContext.optimizationDevices.length).to.equal(
    Object.values(deviceCounts).reduce((a, b) => a + b, 0)
  );
});

/**
 * User actions
 */
When('the AI optimization system analyzes the entire fleet', async function() {
  const deviceIds = this.testContext.optimizationDevices.map(d => d.id);

  try {
    // Analyze the fleet for optimization
    const optimizationResults = await this.analyticsEngine.analyzeFleetForOptimization(deviceIds);
    this.testContext.fleetOptimization = optimizationResults;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

/**
 * Verification steps
 */
Then('it should recommend an optimal device replacement strategy', function() {
  const optimization = this.testContext.fleetOptimization;

  expect(optimization).to.have.property('replacementStrategy');
  expect(optimization.replacementStrategy).to.be.an('object');
  expect(optimization.replacementStrategy).to.have.property('overview');
  expect(optimization.replacementStrategy).to.have.property('deviceRecommendations');
  expect(optimization.replacementStrategy.deviceRecommendations).to.be.an('array');
  expect(optimization.replacementStrategy.deviceRecommendations.length).to.be.greaterThan(0);
});

Then('it should suggest device redeployment based on usage patterns', function() {
  const optimization = this.testContext.fleetOptimization;

  expect(optimization).to.have.property('redeploymentSuggestions');
  expect(optimization.redeploymentSuggestions).to.be.an('array');
  expect(optimization.redeploymentSuggestions.length).to.be.greaterThan(0);

  // Each suggestion should include source and target locations
  for (const suggestion of optimization.redeploymentSuggestions) {
    expect(suggestion).to.have.property('deviceId');
    expect(suggestion).to.have.property('currentLocation');
    expect(suggestion).to.have.property('suggestedLocation');
    expect(suggestion).to.have.property('rationale');
  }
});

Then('it should identify candidates for:', function(dataTable) {
  const categories = dataTable.rowsHash();
  const optimization = this.testContext.fleetOptimization;

  expect(optimization).to.have.property('deviceCategories');
  expect(optimization.deviceCategories).to.be.an('object');

  // Check each category exists
  for (const [category] of Object.entries(categories)) {
    // Convert to camelCase
    const propertyName = category
      .toLowerCase()
      .replace(/[^a-z0-9]+(.)/g, (match, chr) => chr.toUpperCase());

    expect(optimization.deviceCategories).to.have.property(propertyName);
    expect(optimization.deviceCategories[propertyName]).to.be.an('array');
    expect(optimization.deviceCategories[propertyName].length).to.be.greaterThan(0);
  }
});

Then('it should provide a phased implementation plan', function() {
  const optimization = this.testContext.fleetOptimization;

  expect(optimization).to.have.property('implementationPlan');
  expect(optimization.implementationPlan).to.be.an('object');
  expect(optimization.implementationPlan).to.have.property('phases');
  expect(optimization.implementationPlan.phases).to.be.an('array');
  expect(optimization.implementationPlan.phases.length).to.be.greaterThan(0);

  // Each phase should have specific content
  for (const phase of optimization.implementationPlan.phases) {
    expect(phase).to.have.property('phaseNumber');
    expect(phase).to.have.property('name');
    expect(phase).to.have.property('duration');
    expect(phase).to.have.property('activities');
    expect(phase.activities).to.be.an('array');
    expect(phase.activities.length).to.be.greaterThan(0);
  }
});

Then('it should calculate expected ROI for the overall strategy', function() {
  const optimization = this.testContext.fleetOptimization;

  expect(optimization).to.have.property('roi');
  expect(optimization.roi).to.be.an('object');
  expect(optimization.roi).to.have.property('overallROI');
  expect(optimization.roi.overallROI).to.be.a('number');

  // Should include financial projections
  expect(optimization.roi).to.have.property('financialProjections');
  expect(optimization.roi.financialProjections).to.be.an('object');
  expect(optimization.roi.financialProjections).to.have.property('initialInvestment');
  expect(optimization.roi.financialProjections).to.have.property('annualSavings');
  expect(optimization.roi.financialProjections).to.have.property('paybackPeriod');
  expect(optimization.roi.financialProjections).to.have.property('npv');
});
