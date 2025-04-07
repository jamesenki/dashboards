/**
 * Step definitions for sales optimization scenarios
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
Given('historical sales data for IoT devices', async function() {
  // Create historical sales data for the past 3 years
  this.testContext.salesData = {
    historicalSales: [],
    productLines: [
      { id: 'basic-water-heater', name: 'Basic Water Heater', launchDate: '2022-01-01', unitPrice: 2500 },
      { id: 'smart-water-heater', name: 'Smart Water Heater', launchDate: '2022-06-15', unitPrice: 4500 },
      { id: 'industrial-water-heater', name: 'Industrial Water Heater', launchDate: '2023-03-01', unitPrice: 12000 },
      { id: 'smart-hvac', name: 'Smart HVAC System', launchDate: '2023-09-15', unitPrice: 8500 },
      { id: 'smart-refrigeration', name: 'Smart Refrigeration', launchDate: '2024-01-10', unitPrice: 15000 }
    ],
    salesChannels: [
      'Direct Sales',
      'Distribution Partner',
      'Online',
      'System Integrator',
      'OEM Partnership'
    ],
    regions: [
      'North America',
      'Europe',
      'Asia Pacific',
      'Latin America',
      'Middle East & Africa'
    ],
    industries: [
      'Manufacturing',
      'Healthcare',
      'Hospitality',
      'Retail',
      'Education',
      'Government',
      'Food & Beverage'
    ]
  };
  
  // Create sales records from 2022 to current date
  const startDate = new Date('2022-01-01');
  const endDate = new Date(); // Current date
  const dayDiff = Math.floor((endDate - startDate) / (1000 * 60 * 60 * 24));
  
  // Generate approximately 5000 sales records spread over the time period
  const salesTransactions = 5000;
  
  for (let i = 0; i < salesTransactions; i++) {
    // Random date within the period
    const randomDayOffset = Math.floor(Math.random() * dayDiff);
    const saleDate = new Date(startDate);
    saleDate.setDate(startDate.getDate() + randomDayOffset);
    
    // Only include products that were launched before the sale date
    const availableProducts = this.testContext.salesData.productLines.filter(
      product => new Date(product.launchDate) <= saleDate
    );
    
    if (availableProducts.length === 0) continue;
    
    // Select random attributes for this sale
    const product = availableProducts[Math.floor(Math.random() * availableProducts.length)];
    const channel = this.testContext.salesData.salesChannels[
      Math.floor(Math.random() * this.testContext.salesData.salesChannels.length)
    ];
    const region = this.testContext.salesData.regions[
      Math.floor(Math.random() * this.testContext.salesData.regions.length)
    ];
    const industry = this.testContext.salesData.industries[
      Math.floor(Math.random() * this.testContext.salesData.industries.length)
    ];
    
    // Calculate quantity based on product type (industrial products sell in smaller quantities)
    const isIndustrial = product.id.includes('industrial');
    const quantity = isIndustrial ? 
      Math.floor(Math.random() * 5) + 1 : // 1-5 units for industrial
      Math.floor(Math.random() * 20) + 1; // 1-20 units for others
    
    // Calculate revenue
    const revenue = quantity * product.unitPrice;
    
    // Calculate customer acquisition cost (varies by channel)
    let acquisitionCost;
    switch (channel) {
      case 'Direct Sales':
        acquisitionCost = revenue * 0.15; // 15% of revenue
        break;
      case 'Distribution Partner':
        acquisitionCost = revenue * 0.08; // 8% of revenue
        break;
      case 'Online':
        acquisitionCost = revenue * 0.05; // 5% of revenue
        break;
      case 'System Integrator':
        acquisitionCost = revenue * 0.12; // 12% of revenue
        break;
      case 'OEM Partnership':
        acquisitionCost = revenue * 0.07; // 7% of revenue
        break;
      default:
        acquisitionCost = revenue * 0.10; // 10% of revenue
    }
    
    // Create sale record
    const saleRecord = {
      id: `SALE-${i + 1}`,
      date: saleDate,
      product: product.id,
      productName: product.name,
      channel,
      region,
      industry,
      quantity,
      unitPrice: product.unitPrice,
      revenue,
      acquisitionCost,
      salesCycle: Math.floor(Math.random() * 120) + 15, // 15-135 days
      customerType: Math.random() > 0.7 ? 'New' : 'Existing', // 30% new, 70% existing
      dealSize: revenue < 10000 ? 'Small' : revenue < 50000 ? 'Medium' : 'Large'
    };
    
    this.testContext.salesData.historicalSales.push(saleRecord);
  }
  
  // Verify sales data was created
  expect(this.testContext.salesData.historicalSales.length).to.be.at.least(1000);
});

Given('customer adoption patterns across different regions', async function() {
  // Create adoption pattern data
  this.testContext.adoptionPatterns = {
    regions: {},
    timePeriods: [
      { id: 'early', name: 'Early Adoption (2022)' },
      { id: 'growth', name: 'Growth Phase (2023)' },
      { id: 'current', name: 'Current (2024+)' }
    ]
  };
  
  // For each region, create adoption patterns
  for (const region of this.testContext.salesData.regions) {
    this.testContext.adoptionPatterns.regions[region] = {
      early: {
        adoptionRate: Math.random() * 0.05 + 0.01, // 1-6%
        keyDrivers: ['Innovation', 'Cost Savings', 'Early Mover Advantage'].slice(0, Math.floor(Math.random() * 3) + 1),
        customerProfile: 'Technology-focused enterprises with substantial R&D budgets',
        challenges: ['Product education', 'Integration complexity', 'ROI uncertainty']
      },
      growth: {
        adoptionRate: Math.random() * 0.2 + 0.1, // 10-30%
        keyDrivers: ['Proven ROI', 'Competitive Pressure', 'Operational Efficiency'].slice(0, Math.floor(Math.random() * 3) + 1),
        customerProfile: 'Mid-market organizations seeking operational improvements',
        challenges: ['Scaling deployments', 'Training staff', 'Legacy system integration']
      },
      current: {
        adoptionRate: Math.random() * 0.4 + 0.3, // 30-70%
        keyDrivers: ['Industry Standard', 'Regulatory Compliance', 'Competitive Necessity'].slice(0, Math.floor(Math.random() * 3) + 1),
        customerProfile: 'Mainstream enterprises of all sizes',
        challenges: ['Customization needs', 'Advanced feature utilization', 'Integration with broader IoT ecosystem']
      }
    };
  }
});

Given('current sales pipeline information', async function() {
  // Create sales pipeline data
  this.testContext.salesPipeline = {
    opportunities: [],
    stageDefinitions: [
      { id: 'lead', name: 'Lead', probability: 0.1 },
      { id: 'qualified', name: 'Qualified', probability: 0.3 },
      { id: 'proposal', name: 'Proposal', probability: 0.5 },
      { id: 'negotiation', name: 'Negotiation', probability: 0.7 },
      { id: 'closing', name: 'Closing', probability: 0.9 }
    ],
    totalForecast: 0
  };
  
  // Generate pipeline opportunities
  const opportunityCount = 200; // 200 opportunities in the pipeline
  
  for (let i = 0; i < opportunityCount; i++) {
    // Select random attributes for this opportunity
    const product = this.testContext.salesData.productLines[
      Math.floor(Math.random() * this.testContext.salesData.productLines.length)
    ];
    const channel = this.testContext.salesData.salesChannels[
      Math.floor(Math.random() * this.testContext.salesData.salesChannels.length)
    ];
    const region = this.testContext.salesData.regions[
      Math.floor(Math.random() * this.testContext.salesData.regions.length)
    ];
    const industry = this.testContext.salesData.industries[
      Math.floor(Math.random() * this.testContext.salesData.industries.length)
    ];
    const stage = this.testContext.salesPipeline.stageDefinitions[
      Math.floor(Math.random() * this.testContext.salesPipeline.stageDefinitions.length)
    ];
    
    // Calculate quantity based on product type
    const isIndustrial = product.id.includes('industrial');
    const quantity = isIndustrial ? 
      Math.floor(Math.random() * 5) + 1 : // 1-5 units for industrial
      Math.floor(Math.random() * 20) + 1; // 1-20 units for others
    
    // Calculate revenue
    const revenue = quantity * product.unitPrice;
    
    // Create opportunity
    const opportunity = {
      id: `OPP-${i + 1}`,
      createdDate: new Date(Date.now() - (Math.random() * 90 * 24 * 60 * 60 * 1000)), // Last 90 days
      product: product.id,
      productName: product.name,
      channel,
      region,
      industry,
      quantity,
      expectedRevenue: revenue,
      stage: stage.id,
      stageName: stage.name,
      probability: stage.probability,
      expectedCloseDate: new Date(Date.now() + (Math.random() * 180 * 24 * 60 * 60 * 1000)), // Next 180 days
      customerType: Math.random() > 0.5 ? 'New' : 'Existing',
      salesRepId: `REP-${Math.floor(Math.random() * 20) + 1}`
    };
    
    this.testContext.salesPipeline.opportunities.push(opportunity);
    this.testContext.salesPipeline.totalForecast += revenue * stage.probability;
  }
  
  // Verify pipeline data was created
  expect(this.testContext.salesPipeline.opportunities.length).to.equal(opportunityCount);
});

/**
 * User actions
 */
When('the AI system analyzes sales performance patterns', async function() {
  try {
    // Analyze sales performance
    const salesAnalysis = await this.analyticsEngine.analyzeSalesPerformance({
      historicalSales: this.testContext.salesData.historicalSales,
      adoptionPatterns: this.testContext.adoptionPatterns,
      salesPipeline: this.testContext.salesPipeline,
      analysisDepth: 'comprehensive'
    });
    
    this.testContext.salesAnalysis = salesAnalysis;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

/**
 * Verification steps
 */
Then('it should identify sales process bottlenecks', function() {
  const analysis = this.testContext.salesAnalysis;
  
  expect(analysis).to.have.property('processBottlenecks');
  expect(analysis.processBottlenecks).to.be.an('array');
  expect(analysis.processBottlenecks.length).to.be.at.least(1);
  
  // Each bottleneck should have detailed information
  for (const bottleneck of analysis.processBottlenecks) {
    expect(bottleneck).to.have.property('stage');
    expect(bottleneck).to.have.property('conversionRate');
    expect(bottleneck).to.have.property('industryBenchmark');
    expect(bottleneck).to.have.property('impactOnRevenue');
    expect(bottleneck).to.have.property('rootCauses');
    expect(bottleneck).to.have.property('recommendedActions');
  }
});

Then('it should recommend optimal sales approaches per customer segment', function() {
  const analysis = this.testContext.salesAnalysis;
  
  expect(analysis).to.have.property('segmentApproaches');
  expect(analysis.segmentApproaches).to.be.an('object');
  
  // Should have approaches for multiple segments
  expect(Object.keys(analysis.segmentApproaches).length).to.be.at.least(3);
  
  // Each segment approach should have detailed recommendations
  for (const segmentKey in analysis.segmentApproaches) {
    const approach = analysis.segmentApproaches[segmentKey];
    
    expect(approach).to.have.property('salesMethodology');
    expect(approach).to.have.property('keyMessaging');
    expect(approach).to.have.property('decisionMakers');
    expect(approach).to.have.property('salesCycleBestPractices');
    expect(approach).to.have.property('pricingStrategy');
    expect(approach).to.have.property('objectionHandling');
  }
});

Then('it should generate sales forecasts with confidence intervals', function() {
  const analysis = this.testContext.salesAnalysis;
  
  expect(analysis).to.have.property('salesForecasts');
  expect(analysis.salesForecasts).to.be.an('object');
  
  // Check forecast periods
  expect(analysis.salesForecasts).to.have.property('quarterly');
  expect(analysis.salesForecasts).to.have.property('annual');
  
  // Check quarterly forecasts
  expect(analysis.salesForecasts.quarterly).to.be.an('array');
  expect(analysis.salesForecasts.quarterly.length).to.be.at.least(4);
  
  // Each forecast should have confidence intervals
  for (const forecast of analysis.salesForecasts.quarterly) {
    expect(forecast).to.have.property('period');
    expect(forecast).to.have.property('expectedRevenue');
    expect(forecast).to.have.property('lowerBound');
    expect(forecast).to.have.property('upperBound');
    expect(forecast).to.have.property('confidenceLevel');
    
    // Lower bound should be less than expected which should be less than upper bound
    expect(forecast.lowerBound).to.be.lessThan(forecast.expectedRevenue);
    expect(forecast.expectedRevenue).to.be.lessThan(forecast.upperBound);
  }
});

Then('it should highlight the most profitable customer acquisition channels', function() {
  const analysis = this.testContext.salesAnalysis;
  
  expect(analysis).to.have.property('channelProfitability');
  expect(analysis.channelProfitability).to.be.an('array');
  expect(analysis.channelProfitability.length).to.be.at.least(3);
  
  // Channels should be sorted by profitability (highest first)
  for (let i = 1; i < analysis.channelProfitability.length; i++) {
    expect(analysis.channelProfitability[i-1].profitMargin)
      .to.be.at.least(analysis.channelProfitability[i].profitMargin);
  }
  
  // Each channel should have detailed metrics
  for (const channel of analysis.channelProfitability) {
    expect(channel).to.have.property('name');
    expect(channel).to.have.property('acquisitionCost');
    expect(channel).to.have.property('conversionRate');
    expect(channel).to.have.property('averageDealSize');
    expect(channel).to.have.property('customerLifetimeValue');
    expect(channel).to.have.property('roi');
    expect(channel).to.have.property('profitMargin');
  }
});

Then('it should suggest ways to reduce customer acquisition costs', function() {
  const analysis = this.testContext.salesAnalysis;
  
  expect(analysis).to.have.property('acquisitionCostReduction');
  expect(analysis.acquisitionCostReduction).to.be.an('object');
  
  // Should have specific strategies
  expect(analysis.acquisitionCostReduction).to.have.property('strategies');
  expect(analysis.acquisitionCostReduction.strategies).to.be.an('array');
  expect(analysis.acquisitionCostReduction.strategies.length).to.be.at.least(3);
  
  // Each strategy should have details
  for (const strategy of analysis.acquisitionCostReduction.strategies) {
    expect(strategy).to.have.property('name');
    expect(strategy).to.have.property('description');
    expect(strategy).to.have.property('estimatedImpact');
    expect(strategy).to.have.property('implementationDifficulty');
    expect(strategy).to.have.property('timeToValue');
  }
  
  // Should have overall potential savings
  expect(analysis.acquisitionCostReduction).to.have.property('potentialSavings');
  expect(analysis.acquisitionCostReduction.potentialSavings).to.be.an('object');
  expect(analysis.acquisitionCostReduction.potentialSavings).to.have.property('percentage');
  expect(analysis.acquisitionCostReduction.potentialSavings).to.have.property('absoluteValue');
});
