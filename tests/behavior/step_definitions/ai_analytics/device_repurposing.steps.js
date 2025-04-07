/**
 * Step definitions for device repurposing and reuse opportunities
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
Given('end-of-life product data and performance history', async function() {
  // Create end-of-life product data and performance history
  this.testContext.eolDevices = {
    devices: [
      {
        type: 'water-heater',
        model: 'Industrial 5000',
        count: 250,
        averageAge: 8.5, // years
        averageCondition: 'Fair', // Poor, Fair, Good, Excellent
        originalCost: 12000, // USD
        currentBookValue: 1500, // USD
        mainComponentsStatus: {
          tank: 'Good - 70% remaining life',
          heatingElement: 'Fair - 30% remaining life',
          controlSystem: 'Poor - requires replacement',
          sensors: 'Fair - partially functional'
        },
        usageHistory: {
          operatingHours: 25000,
          cycleCount: 15000,
          maintenanceEvents: 12,
          majorRepairs: 2
        }
      },
      {
        type: 'water-heater',
        model: 'Commercial 3000',
        count: 350,
        averageAge: 7.2, // years
        averageCondition: 'Good', // Poor, Fair, Good, Excellent
        originalCost: 8500, // USD
        currentBookValue: 1200, // USD
        mainComponentsStatus: {
          tank: 'Excellent - 85% remaining life',
          heatingElement: 'Good - 60% remaining life',
          controlSystem: 'Fair - functional but outdated',
          sensors: 'Good - mostly functional'
        },
        usageHistory: {
          operatingHours: 20000,
          cycleCount: 12000,
          maintenanceEvents: 8,
          majorRepairs: 1
        }
      },
      {
        type: 'hvac',
        model: 'Climate Master Pro',
        count: 180,
        averageAge: 9.0, // years
        averageCondition: 'Fair', // Poor, Fair, Good, Excellent
        originalCost: 15000, // USD
        currentBookValue: 1800, // USD
        mainComponentsStatus: {
          compressor: 'Fair - 40% remaining life',
          condenser: 'Good - 65% remaining life',
          controlSystem: 'Poor - requires replacement',
          ductwork: 'Good - 70% remaining life'
        },
        usageHistory: {
          operatingHours: 28000,
          cycleCount: 18000,
          maintenanceEvents: 15,
          majorRepairs: 3
        }
      },
      {
        type: 'refrigeration',
        model: 'CoolStore 2000',
        count: 120,
        averageAge: 6.5, // years
        averageCondition: 'Good', // Poor, Fair, Good, Excellent
        originalCost: 18000, // USD
        currentBookValue: 4200, // USD
        mainComponentsStatus: {
          compressor: 'Good - 60% remaining life',
          condenser: 'Excellent - 80% remaining life',
          evaporator: 'Good - 65% remaining life',
          controlSystem: 'Fair - requires updates'
        },
        usageHistory: {
          operatingHours: 22000,
          cycleCount: 8000,
          maintenanceEvents: 10,
          majorRepairs: 1
        }
      }
    ],
    disposalCosts: {
      standardDisposal: {
        transportationCost: 250, // USD per unit
        disposalFees: 350, // USD per unit
        administrativeCosts: 100 // USD per unit
      },
      environmentalImpact: {
        carbonFootprint: 250, // kg CO2 per unit
        landfillContribution: 85, // kg per unit
        recyclablePercentage: 65 // % of materials recyclable
      }
    },
    complianceRequirements: [
      'Electronic waste handling regulations',
      'Refrigerant recovery requirements',
      'Heavy metals disposal protocols',
      'Extended producer responsibility laws'
    ]
  };
});

Given('secondary market pricing information', async function() {
  // Create secondary market pricing information
  this.testContext.secondaryMarket = {
    componentValues: {
      'water-heater': {
        tank: { excellent: 800, good: 500, fair: 250, poor: 50 },
        heatingElement: { excellent: 300, good: 200, fair: 100, poor: 25 },
        controlSystem: { excellent: 400, good: 250, fair: 100, poor: 20 },
        sensors: { excellent: 200, good: 125, fair: 50, poor: 10 }
      },
      'hvac': {
        compressor: { excellent: 1200, good: 800, fair: 400, poor: 100 },
        condenser: { excellent: 900, good: 600, fair: 300, poor: 75 },
        controlSystem: { excellent: 600, good: 350, fair: 150, poor: 30 },
        ductwork: { excellent: 300, good: 200, fair: 100, poor: 25 }
      },
      'refrigeration': {
        compressor: { excellent: 1500, good: 1000, fair: 500, poor: 125 },
        condenser: { excellent: 1100, good: 700, fair: 350, poor: 85 },
        evaporator: { excellent: 800, good: 500, fair: 250, poor: 60 },
        controlSystem: { excellent: 700, good: 400, fair: 175, poor: 35 }
      }
    },
    refurbishedUnitValues: {
      'water-heater': {
        'Industrial 5000': { excellent: 6000, good: 4000, fair: 2000, poor: 800 },
        'Commercial 3000': { excellent: 4200, good: 2800, fair: 1400, poor: 550 }
      },
      'hvac': {
        'Climate Master Pro': { excellent: 7500, good: 5000, fair: 2500, poor: 1000 }
      },
      'refrigeration': {
        'CoolStore 2000': { excellent: 9000, good: 6000, fair: 3000, poor: 1200 }
      }
    },
    marketDemand: {
      refurbishedUnits: {
        'water-heater': { trend: 'Growing', demandLevel: 'High' },
        'hvac': { trend: 'Stable', demandLevel: 'Medium' },
        'refrigeration': { trend: 'Growing', demandLevel: 'Medium-High' }
      },
      reconditionedComponents: {
        'water-heater': { trend: 'Stable', demandLevel: 'Medium' },
        'hvac': { trend: 'Growing', demandLevel: 'Medium-High' },
        'refrigeration': { trend: 'Growing', demandLevel: 'High' }
      },
      rawMaterials: {
        metals: { trend: 'Growing', demandLevel: 'High' },
        electronics: { trend: 'Growing', demandLevel: 'Medium' },
        plastics: { trend: 'Stable', demandLevel: 'Medium-Low' }
      }
    },
    buyerCategories: [
      {
        type: 'Discount Retailers',
        preferences: 'Refurbished complete units',
        priceExpectation: '40-60% of new',
        qualityRequirements: 'Good to Excellent',
        warrantyExpectations: '6-12 months'
      },
      {
        type: 'Service Companies',
        preferences: 'Functional components',
        priceExpectation: '30-50% of new',
        qualityRequirements: 'Fair to Good',
        warrantyExpectations: '30-90 days'
      },
      {
        type: 'Developing Markets',
        preferences: 'Functional units of any age',
        priceExpectation: '30-40% of new',
        qualityRequirements: 'Fair',
        warrantyExpectations: 'As-is or minimal'
      },
      {
        type: 'Materials Recyclers',
        preferences: 'Raw materials, non-functional units',
        priceExpectation: 'Based on material content',
        qualityRequirements: 'Any condition',
        warrantyExpectations: 'None'
      }
    ]
  };
});

Given('circular economy value chain data', async function() {
  // Create circular economy value chain data
  this.testContext.circularEconomy = {
    partnerNetwork: [
      {
        type: 'Refurbishment Partners',
        capabilities: ['Component testing', 'Repair', 'Recertification', 'Packaging'],
        locationCoverage: ['North America', 'Europe'],
        costStructure: {
          laborRatePerHour: 35,
          componentHandlingFee: 25,
          recertificationCost: 150
        }
      },
      {
        type: 'Recycling Facilities',
        capabilities: ['Material separation', 'Hazardous waste handling', 'Raw material recovery'],
        locationCoverage: ['Global'],
        costStructure: {
          processingFeePerUnit: 75,
          transportationCost: 50,
          revenueShareOfMaterials: 0.6 // 60% to company
        }
      },
      {
        type: 'Logistics Providers',
        capabilities: ['Reverse logistics', 'Warehouse management', 'Distribution'],
        locationCoverage: ['Global'],
        costStructure: {
          pickupCostPerUnit: 40,
          warehouseCostPerUnitMonth: 15,
          redeliveryCostPerUnit: 35
        }
      },
      {
        type: 'Secondary Market Channels',
        capabilities: ['Customer acquisition', 'Sales', 'Warranty management'],
        locationCoverage: ['North America', 'Europe', 'Asia', 'Africa'],
        costStructure: {
          salesCommission: 0.15, // 15% of sale price
          marketingCostPerUnit: 45,
          platformFee: 0.08 // 8% of sale price
        }
      }
    ],
    sustainabilityMetrics: {
      carbonSavings: {
        refurbishment: 65, // % reduction vs. new manufacture
        componentReuse: 80, // % reduction vs. new manufacture
        materialRecycling: 35 // % reduction vs. new manufacture
      },
      waterSavings: {
        refurbishment: 70, // % reduction vs. new manufacture
        componentReuse: 85, // % reduction vs. new manufacture
        materialRecycling: 40 // % reduction vs. new manufacture
      },
      energySavings: {
        refurbishment: 60, // % reduction vs. new manufacture
        componentReuse: 75, // % reduction vs. new manufacture
        materialRecycling: 30 // % reduction vs. new manufacture
      },
      landfillDiversion: {
        refurbishment: 95, // % diverted
        componentReuse: 85, // % diverted
        materialRecycling: 70 // % diverted
      }
    },
    regulatoryIncentives: [
      {
        program: 'Extended Producer Responsibility Credits',
        benefit: 'Reduced compliance fees',
        applicableRegions: ['Europe', 'Canada', 'Parts of US'],
        expectedValue: 75 // USD per unit
      },
      {
        program: 'Carbon Offset Credits',
        benefit: 'Monetary value for carbon reduction',
        applicableRegions: ['Global carbon markets'],
        expectedValue: 15 // USD per ton CO2 reduced
      },
      {
        program: 'Circular Economy Tax Incentives',
        benefit: 'Tax deductions for reuse activities',
        applicableRegions: ['Europe', 'Parts of US', 'Australia'],
        expectedValue: 0.12 // 12% tax reduction on qualifying activities
      }
    ]
  };
});

/**
 * User actions
 */
When('the sustainability analytics system analyzes device lifecycles', async function() {
  try {
    // Analyze device repurposing opportunities
    const repurposingAnalysis = await this.analyticsEngine.analyzeDeviceRepurposingOpportunities({
      eolDevices: this.testContext.eolDevices,
      secondaryMarket: this.testContext.secondaryMarket,
      circularEconomy: this.testContext.circularEconomy
    });

    this.testContext.repurposingAnalysis = repurposingAnalysis;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

/**
 * Verification steps
 */
Then('it should identify high-value repurposing opportunities', function() {
  const analysis = this.testContext.repurposingAnalysis;

  expect(analysis).to.have.property('repurposingOpportunities');
  expect(analysis.repurposingOpportunities).to.be.an('array');
  expect(analysis.repurposingOpportunities.length).to.be.at.least(3);

  // Each opportunity should have detailed information
  for (const opportunity of analysis.repurposingOpportunities) {
    expect(opportunity).to.have.property('deviceType');
    expect(opportunity).to.have.property('model');
    expect(opportunity).to.have.property('repurposingType');
    expect(opportunity).to.have.property('applicableUnits');
    expect(opportunity).to.have.property('financialValue');
    expect(opportunity.financialValue).to.be.an('object');
    expect(opportunity.financialValue).to.have.property('potentialRevenue');
    expect(opportunity.financialValue).to.have.property('processingCosts');
    expect(opportunity.financialValue).to.have.property('netValue');
    expect(opportunity).to.have.property('implementationComplexity');
    expect(opportunity).to.have.property('recommendedPartners');
  }

  // Opportunities should be sorted by net value (highest first)
  for (let i = 1; i < analysis.repurposingOpportunities.length; i++) {
    expect(analysis.repurposingOpportunities[i-1].financialValue.netValue)
      .to.be.at.least(analysis.repurposingOpportunities[i].financialValue.netValue);
  }
});

Then('it should suggest refurbishment strategies for different device conditions', function() {
  const analysis = this.testContext.repurposingAnalysis;

  expect(analysis).to.have.property('refurbishmentStrategies');
  expect(analysis.refurbishmentStrategies).to.be.an('object');

  // Should have strategies for different conditions
  const conditions = ['Excellent', 'Good', 'Fair', 'Poor'];
  for (const condition of conditions) {
    const conditionKey = condition.toLowerCase();
    expect(analysis.refurbishmentStrategies).to.have.property(conditionKey);

    const strategy = analysis.refurbishmentStrategies[conditionKey];
    expect(strategy).to.have.property('recommendedApproach');
    expect(strategy).to.have.property('keyProcessSteps');
    expect(strategy.keyProcessSteps).to.be.an('array');
    expect(strategy).to.have.property('qualityAssurance');
    expect(strategy).to.have.property('marketingApproach');
    expect(strategy).to.have.property('warrantyRecommendation');
    expect(strategy).to.have.property('economicModel');
    expect(strategy.economicModel).to.be.an('object');
  }
});

Then('it should calculate the financial value of reclaimed components', function() {
  const analysis = this.testContext.repurposingAnalysis;

  expect(analysis).to.have.property('componentValueAnalysis');
  expect(analysis.componentValueAnalysis).to.be.an('object');

  // Should have analysis for each device type
  for (const deviceType in this.testContext.secondaryMarket.componentValues) {
    expect(analysis.componentValueAnalysis).to.have.property(deviceType);

    const deviceAnalysis = analysis.componentValueAnalysis[deviceType];
    expect(deviceAnalysis).to.be.an('object');

    // Should have analysis for each component
    for (const component in this.testContext.secondaryMarket.componentValues[deviceType]) {
      expect(deviceAnalysis).to.have.property(component);

      const componentAnalysis = deviceAnalysis[component];
      expect(componentAnalysis).to.have.property('recoveryRate');
      expect(componentAnalysis).to.have.property('reconditioningCost');
      expect(componentAnalysis).to.have.property('marketValue');
      expect(componentAnalysis).to.have.property('netValuePerUnit');
      expect(componentAnalysis).to.have.property('totalPotentialValue');
    }
  }
});

Then('it should recommend optimal end-of-life pathways for each device type', function() {
  const analysis = this.testContext.repurposingAnalysis;

  expect(analysis).to.have.property('endOfLifePathways');
  expect(analysis.endOfLifePathways).to.be.an('object');

  // Should have pathways for each device type
  for (const deviceData of this.testContext.eolDevices.devices) {
    const deviceKey = `${deviceData.type}-${deviceData.model.replace(/\s+/g, '-').toLowerCase()}`;
    expect(analysis.endOfLifePathways).to.have.property(deviceKey);

    const pathway = analysis.endOfLifePathways[deviceKey];
    expect(pathway).to.have.property('recommendedPathway');
    expect(pathway).to.have.property('pathwayBreakdown');
    expect(pathway.pathwayBreakdown).to.be.an('object');

    // Percentages should add up to 100%
    const totalPercentage = Object.values(pathway.pathwayBreakdown)
      .reduce((sum, value) => sum + value, 0);
    expect(totalPercentage).to.be.closeTo(100, 0.1); // Within rounding error

    expect(pathway).to.have.property('processingSteps');
    expect(pathway.processingSteps).to.be.an('array');
    expect(pathway).to.have.property('logisticsRecommendations');
    expect(pathway).to.have.property('financialSummary');
    expect(pathway.financialSummary).to.be.an('object');
  }
});

Then('it should quantify the sustainability impact of reuse strategies', function() {
  const analysis = this.testContext.repurposingAnalysis;

  expect(analysis).to.have.property('sustainabilityImpact');
  expect(analysis.sustainabilityImpact).to.be.an('object');

  // Check environmental metrics
  expect(analysis.sustainabilityImpact).to.have.property('environmentalMetrics');
  expect(analysis.sustainabilityImpact.environmentalMetrics).to.be.an('object');

  const metrics = analysis.sustainabilityImpact.environmentalMetrics;
  expect(metrics).to.have.property('carbonReduction');
  expect(metrics).to.have.property('wasteReduction');
  expect(metrics).to.have.property('waterConservation');
  expect(metrics).to.have.property('energySavings');

  // Check sustainability reporting
  expect(analysis.sustainabilityImpact).to.have.property('reportingFrameworks');
  expect(analysis.sustainabilityImpact.reportingFrameworks).to.be.an('object');

  // Check regulatory compliance
  expect(analysis.sustainabilityImpact).to.have.property('regulatoryCompliance');
  expect(analysis.sustainabilityImpact.regulatoryCompliance).to.be.an('array');
  expect(analysis.sustainabilityImpact.regulatoryCompliance.length).to.be.at.least(2);
});

Then('it should identify potential buyers for repurposed equipment', function() {
  const analysis = this.testContext.repurposingAnalysis;

  expect(analysis).to.have.property('marketOpportunities');
  expect(analysis.marketOpportunities).to.be.an('object');
  expect(analysis.marketOpportunities).to.have.property('buyerSegments');
  expect(analysis.marketOpportunities.buyerSegments).to.be.an('array');
  expect(analysis.marketOpportunities.buyerSegments.length).to.be.at.least(3);

  // Each buyer segment should have detailed information
  for (const segment of analysis.marketOpportunities.buyerSegments) {
    expect(segment).to.have.property('name');
    expect(segment).to.have.property('description');
    expect(segment).to.have.property('preferredDeviceTypes');
    expect(segment.preferredDeviceTypes).to.be.an('array');
    expect(segment).to.have.property('geographicFocus');
    expect(segment).to.have.property('priceExpectations');
    expect(segment).to.have.property('volumePotential');
    expect(segment).to.have.property('salesApproach');
  }

  // Check go-to-market strategy
  expect(analysis.marketOpportunities).to.have.property('goToMarketStrategy');
  expect(analysis.marketOpportunities.goToMarketStrategy).to.be.an('object');
  expect(analysis.marketOpportunities.goToMarketStrategy).to.have.property('channels');
  expect(analysis.marketOpportunities.goToMarketStrategy).to.have.property('pricing');
  expect(analysis.marketOpportunities.goToMarketStrategy).to.have.property('positioning');
  expect(analysis.marketOpportunities.goToMarketStrategy).to.have.property('partnerRequirements');
});
