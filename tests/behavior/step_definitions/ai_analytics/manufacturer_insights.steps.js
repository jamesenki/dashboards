/**
 * Step definitions for manufacturer insights scenarios
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
Given('a manufacturer with devices deployed across multiple customers', async function() {
  // Create a manufacturer with devices across customers
  this.testContext.manufacturer = {
    name: 'Test Manufacturer',
    devices: [],
    customers: [
      'Customer A',
      'Customer B',
      'Customer C',
      'Customer D',
      'Customer E'
    ]
  };

  // Create devices for each customer
  for (const customer of this.testContext.manufacturer.customers) {
    // Each customer has 3 devices
    for (let i = 0; i < 3; i++) {
      const deviceId = `${customer.toLowerCase().replace(/\s+/g, '-')}-device-${i+1}`;

      // Register device
      const device = await this.deviceRepository.registerDevice({
        id: deviceId,
        type: 'water-heater',
        name: `${customer} Device ${i+1}`,
        manufacturer: this.testContext.manufacturer.name,
        model: `Model ${String.fromCharCode(65 + (i % 3))}`, // Model A, B, or C
        serialNumber: `${customer.substring(0, 1)}${1000 + i}`,
        firmwareVersion: '1.0.0',
        metadata: {
          customer: customer,
          location: `${customer} Facility`,
          installationDate: new Date(Date.now() - ((Math.random() * 365 * 2) + 30) * 24 * 60 * 60 * 1000) // 1 month to 2 years old
        }
      });

      // Generate varying telemetry data
      await this.generateRealisticDeviceHistory(deviceId, 'water-heater', customer, i);

      this.testContext.manufacturer.devices.push(device);
    }
  }

  // Verify devices were created
  expect(this.testContext.manufacturer.devices.length).to.equal(
    this.testContext.manufacturer.customers.length * 3
  );
});

Given('anonymous performance data from the device fleet', async function() {
  // Generate anonymized performance data
  this.testContext.anonymizedData = await this.analyticsEngine.generateAnonymizedPerformanceData(
    this.testContext.manufacturer.devices.map(d => d.id)
  );

  // Verify anonymized data was created
  expect(this.testContext.anonymizedData).to.be.an('object');
  expect(this.testContext.anonymizedData).to.have.property('devices');
  expect(this.testContext.anonymizedData.devices.length).to.equal(this.testContext.manufacturer.devices.length);

  // Verify data is truly anonymized (no customer names or identifying info)
  for (const deviceData of this.testContext.anonymizedData.devices) {
    expect(deviceData).to.not.have.property('customer');
    expect(deviceData).to.not.have.property('serialNumber');
    expect(deviceData).to.not.have.property('metadata');

    // Should have an anonymized ID instead
    expect(deviceData).to.have.property('anonymizedId');
    expect(deviceData.anonymizedId).to.be.a('string');
  }
});

/**
 * User actions
 */
When('a user with {string} role views the product analytics', async function(role) {
  if (role !== 'MANUFACTURER') {
    throw new Error(`This scenario is specifically for MANUFACTURER role, not ${role}`);
  }

  // Create manufacturer user
  const user = {
    id: 'manufacturer-user',
    username: 'manufacturer',
    role: 'MANUFACTURER',
    organization: this.testContext.manufacturer.name
  };

  // Set as current user
  this.testContext.currentUser = user;

  try {
    // Get manufacturer insights
    const insights = await this.analyticsEngine.getManufacturerInsights(
      user.organization,
      this.testContext.anonymizedData
    );

    this.testContext.manufacturerInsights = insights;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

/**
 * Verification steps
 */
Then('the system should provide insights on:', function(dataTable) {
  const expectedInsights = dataTable.rowsHash();
  const insights = this.testContext.manufacturerInsights;

  expect(insights).to.not.be.null;

  // Verify each expected insight category
  for (const [insightType] of Object.entries(expectedInsights)) {
    // Convert to camelCase
    const propertyName = insightType
      .toLowerCase()
      .replace(/[^a-z0-9]+(.)/g, (match, chr) => chr.toUpperCase());

    expect(insights).to.have.property(propertyName);
  }
});

Then('all data should be anonymized to protect customer privacy', function() {
  const insights = this.testContext.manufacturerInsights;

  // Check that insights don't contain customer identifiable information
  expect(insights).to.have.property('anonymizationVerification');
  expect(insights.anonymizationVerification).to.be.an('object');
  expect(insights.anonymizationVerification).to.have.property('compliant');
  expect(insights.anonymizationVerification.compliant).to.be.true;

  // Check there are no customer names in any strings
  for (const customer of this.testContext.manufacturer.customers) {
    // Convert insights to string for simple check
    const insightsStr = JSON.stringify(insights);
    expect(insightsStr).to.not.include(customer);
  }
});

Then('insights should be categorized by device model and environment', function() {
  const insights = this.testContext.manufacturerInsights;

  // Check model-specific insights
  expect(insights).to.have.property('modelSpecificInsights');
  expect(insights.modelSpecificInsights).to.be.an('object');

  // Should have entries for each model
  const models = ['Model A', 'Model B', 'Model C'];
  for (const model of models) {
    expect(insights.modelSpecificInsights).to.have.property(model.replace(/\s+/g, ''));
  }

  // Check environment-specific insights
  expect(insights).to.have.property('environmentAnalysis');
  expect(insights.environmentAnalysis).to.be.an('object');
  expect(insights.environmentAnalysis).to.have.property('categories');
  expect(insights.environmentAnalysis.categories).to.be.an('array');
  expect(insights.environmentAnalysis.categories.length).to.be.greaterThan(0);
});

Then('product improvement recommendations should be generated', function() {
  const insights = this.testContext.manufacturerInsights;

  expect(insights).to.have.property('productImprovements');
  expect(insights.productImprovements).to.be.an('array');
  expect(insights.productImprovements.length).to.be.greaterThan(0);

  // Each recommendation should have specific elements
  for (const improvement of insights.productImprovements) {
    expect(improvement).to.have.property('title');
    expect(improvement).to.have.property('description');
    expect(improvement).to.have.property('priority');
    expect(improvement).to.have.property('impact');
    expect(improvement).to.have.property('evidence');
    expect(improvement.evidence).to.be.an('array');
  }
});
