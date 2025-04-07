/**
 * Step definitions for customer segmentation scenarios
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
Given('data from multiple devices across different customer segments', async function() {
  // Create a diverse dataset of customer segments with different devices
  this.testContext.customerSegments = [
    {
      name: 'Enterprise Industrial',
      industries: ['Manufacturing', 'Food Processing', 'Pharmaceuticals'],
      size: 'Enterprise',
      deviceTypes: ['water-heater', 'hvac', 'industrial-refrigeration'],
      deviceCount: 50,
      averageDeviceAge: 3.2, // years
      utilizationPatterns: {
        dailyOperatingHours: 18,
        weekendUsage: 'High',
        seasonalVariation: 'Low'
      },
      economicData: {
        annualRevenue: '$500M-1B',
        employeeCount: '1000-5000',
        growthRate: '5-7%'
      }
    },
    {
      name: 'Mid-Market Commercial',
      industries: ['Hospitality', 'Healthcare', 'Retail'],
      size: 'Mid-Market',
      deviceTypes: ['water-heater', 'hvac'],
      deviceCount: 15,
      averageDeviceAge: 2.5, // years
      utilizationPatterns: {
        dailyOperatingHours: 16,
        weekendUsage: 'Medium',
        seasonalVariation: 'Medium'
      },
      economicData: {
        annualRevenue: '$50M-250M',
        employeeCount: '250-1000',
        growthRate: '8-12%'
      }
    },
    {
      name: 'Small Business',
      industries: ['Restaurants', 'Small Retail', 'Services'],
      size: 'Small Business',
      deviceTypes: ['water-heater'],
      deviceCount: 3,
      averageDeviceAge: 4.1, // years
      utilizationPatterns: {
        dailyOperatingHours: 12,
        weekendUsage: 'High',
        seasonalVariation: 'Medium'
      },
      economicData: {
        annualRevenue: '$1M-10M',
        employeeCount: '10-50',
        growthRate: '3-15%'
      }
    },
    {
      name: 'Educational Institutions',
      industries: ['Higher Education', 'K-12 Schools'],
      size: 'Varied',
      deviceTypes: ['water-heater', 'hvac'],
      deviceCount: 25,
      averageDeviceAge: 5.8, // years
      utilizationPatterns: {
        dailyOperatingHours: 14,
        weekendUsage: 'Low',
        seasonalVariation: 'High'
      },
      economicData: {
        annualRevenue: 'Non-profit',
        employeeCount: '500-2000',
        growthRate: '1-2%'
      }
    },
    {
      name: 'Public Sector',
      industries: ['Government Facilities', 'Municipal Buildings'],
      size: 'Large',
      deviceTypes: ['water-heater', 'hvac'],
      deviceCount: 35,
      averageDeviceAge: 6.5, // years
      utilizationPatterns: {
        dailyOperatingHours: 10,
        weekendUsage: 'Low',
        seasonalVariation: 'Medium'
      },
      economicData: {
        annualRevenue: 'Budget-based',
        employeeCount: '1000+',
        growthRate: '0-1%'
      }
    }
  ];

  // Generate device data for each segment
  for (const segment of this.testContext.customerSegments) {
    segment.devices = [];

    // Create devices for this segment
    for (let i = 0; i < segment.deviceCount; i++) {
      const deviceType = segment.deviceTypes[i % segment.deviceTypes.length];
      const deviceId = `${segment.name.toLowerCase().replace(/\s+/g, '-')}-${deviceType}-${i+1}`;

      // Register the device
      const device = await this.deviceRepository.registerDevice({
        id: deviceId,
        type: deviceType,
        name: `${segment.name} ${deviceType} ${i+1}`,
        manufacturer: ['Alpha Inc', 'Beta Corp', 'Gamma Industries'][i % 3],
        model: `Model ${String.fromCharCode(65 + (i % 5))}`, // Model A through E
        serialNumber: `SN-${segment.name.substring(0, 3).toUpperCase()}-${1000 + i}`,
        firmwareVersion: `${Math.floor(Math.random() * 2) + 1}.${Math.floor(Math.random() * 10)}.${Math.floor(Math.random() * 10)}`,
        metadata: {
          segment: segment.name,
          industry: segment.industries[i % segment.industries.length],
          installationDate: new Date(Date.now() - (segment.averageDeviceAge * 365 * 24 * 60 * 60 * 1000) - (Math.random() * 180 * 24 * 60 * 60 * 1000)),
          location: `${segment.name} Location ${Math.floor(i/5) + 1}`
        }
      });

      // Generate telemetry based on segment patterns
      await this.generateSegmentBasedTelemetry(deviceId, deviceType, segment.utilizationPatterns);

      segment.devices.push(device);
    }
  }

  // Verify devices were created
  const totalDeviceCount = this.testContext.customerSegments.reduce(
    (sum, segment) => sum + segment.devices.length, 0
  );
  expect(totalDeviceCount).to.be.at.least(100); // Should have at least 100 devices across all segments
});

Given('customer demographic and firmographic data', async function() {
  // Create additional business and customer data
  this.testContext.customerData = {
    demographics: {
      regions: ['Northeast', 'Southeast', 'Midwest', 'Southwest', 'West'],
      urbanDensity: ['Urban', 'Suburban', 'Rural'],
      climateZones: ['Hot-Humid', 'Mixed-Humid', 'Hot-Dry', 'Mixed-Dry', 'Cold', 'Very Cold', 'Subarctic']
    },
    businessAttributes: {
      growthStages: ['Startup', 'Growth', 'Mature', 'Declining', 'Renewing'],
      techAdoption: ['Early Adopter', 'Early Majority', 'Late Majority', 'Laggard'],
      decisionFactors: ['Cost', 'Reliability', 'Efficiency', 'Service Quality', 'Innovation', 'Sustainability']
    }
  };

  // Assign these attributes to each segment
  for (const segment of this.testContext.customerSegments) {
    // Add firmographic data to each segment
    segment.firmographic = {
      region: this.getRandomSubset(this.testContext.customerData.demographics.regions, 2),
      urbanDensity: this.getRandomSubset(this.testContext.customerData.demographics.urbanDensity, 2),
      climateZone: this.getRandomSubset(this.testContext.customerData.demographics.climateZones, 2),
      growthStage: this.getRandomSubset(this.testContext.customerData.businessAttributes.growthStages, 1)[0],
      techAdoption: this.getRandomSubset(this.testContext.customerData.businessAttributes.techAdoption, 1)[0],
      decisionFactors: this.getRandomSubset(this.testContext.customerData.businessAttributes.decisionFactors, 3)
    };
  }
});

/**
 * User actions
 */
When('the business analytics system performs customer segmentation analysis', async function() {
  try {
    // Perform customer segmentation analysis
    const segmentationResults = await this.analyticsEngine.performCustomerSegmentation({
      segments: this.testContext.customerSegments,
      customerData: this.testContext.customerData,
      analysisDepth: 'comprehensive'
    });

    this.testContext.segmentationResults = segmentationResults;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

/**
 * Verification steps
 */
Then('it should identify distinct customer segments based on usage patterns', function() {
  const results = this.testContext.segmentationResults;

  expect(results).to.have.property('identifiedSegments');
  expect(results.identifiedSegments).to.be.an('array');
  expect(results.identifiedSegments.length).to.be.at.least(3); // Should identify at least 3 distinct segments

  // Each segment should have a distinct usage pattern profile
  const usagePatterns = results.identifiedSegments.map(segment =>
    JSON.stringify(segment.usagePattern)
  );

  // Check for uniqueness - all patterns should be different
  const uniquePatterns = new Set(usagePatterns);
  expect(uniquePatterns.size).to.equal(usagePatterns.length);
});

Then('it should quantify the size and value of each segment', function() {
  const results = this.testContext.segmentationResults;

  for (const segment of results.identifiedSegments) {
    expect(segment).to.have.property('marketSize');
    expect(segment.marketSize).to.be.an('object');
    expect(segment.marketSize).to.have.property('estimatedCustomerCount');
    expect(segment.marketSize).to.have.property('estimatedDeviceCount');

    expect(segment).to.have.property('economicValue');
    expect(segment.economicValue).to.be.an('object');
    expect(segment.economicValue).to.have.property('customerLifetimeValue');
    expect(segment.economicValue).to.have.property('annualRevenuePotential');
    expect(segment.economicValue).to.have.property('acquisitionCost');
  }
});

Then('it should identify underserved segments with high growth potential', function() {
  const results = this.testContext.segmentationResults;

  expect(results).to.have.property('growthOpportunities');
  expect(results.growthOpportunities).to.be.an('array');
  expect(results.growthOpportunities.length).to.be.at.least(1);

  // Each growth opportunity should have specific attributes
  for (const opportunity of results.growthOpportunities) {
    expect(opportunity).to.have.property('segment');
    expect(opportunity).to.have.property('currentPenetration');
    expect(opportunity).to.have.property('growthPotential');
    expect(opportunity).to.have.property('competitiveIntensity');
    expect(opportunity).to.have.property('strategy');
  }
});

Then('it should provide firmographic profiles of each segment', function() {
  const results = this.testContext.segmentationResults;

  for (const segment of results.identifiedSegments) {
    expect(segment).to.have.property('firmographicProfile');
    expect(segment.firmographicProfile).to.be.an('object');

    // Each profile should have specific attributes
    expect(segment.firmographicProfile).to.have.property('industryComposition');
    expect(segment.firmographicProfile).to.have.property('companySize');
    expect(segment.firmographicProfile).to.have.property('regionDistribution');
    expect(segment.firmographicProfile).to.have.property('techAdoption');
    expect(segment.firmographicProfile).to.have.property('purchasingBehavior');
  }
});

Then('it should recommend targeting approaches for high-value segments', function() {
  const results = this.testContext.segmentationResults;

  expect(results).to.have.property('targetingRecommendations');
  expect(results.targetingRecommendations).to.be.an('object');

  // Should have recommendations for high-value segments
  for (const segment of results.identifiedSegments) {
    if (segment.economicValue.customerLifetimeValue > 100000) { // Arbitrary threshold for high-value
      const segmentId = segment.id;
      expect(results.targetingRecommendations).to.have.property(segmentId);

      const recommendation = results.targetingRecommendations[segmentId];
      expect(recommendation).to.have.property('marketingChannels');
      expect(recommendation).to.have.property('messagingThemes');
      expect(recommendation).to.have.property('salesApproach');
      expect(recommendation).to.have.property('productFeatures');
      expect(recommendation).to.have.property('pricingStrategy');
    }
  }
});
