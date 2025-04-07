/**
 * Step definitions for business model innovation scenarios
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
Given('device usage and value creation data across industries', async function() {
  // Create device usage and value creation data
  this.testContext.valueCreationData = {
    industries: [
      'Manufacturing',
      'Healthcare',
      'Hospitality',
      'Retail',
      'Education',
      'Government',
      'Food & Beverage',
      'Transportation',
      'Utilities'
    ],
    deviceTypes: [
      { type: 'water-heater', currentDeployment: 1000, maturity: 'Established' },
      { type: 'hvac', currentDeployment: 750, maturity: 'Growing' },
      { type: 'refrigeration', currentDeployment: 500, maturity: 'Growing' },
      { type: 'vending-machine', currentDeployment: 250, maturity: 'Emerging' },
      { type: 'robot', currentDeployment: 100, maturity: 'Emerging' },
      { type: 'vehicle', currentDeployment: 50, maturity: 'Experimental' }
    ],
    valueMetrics: [
      { name: 'Energy Savings', unit: 'kWh', dataAvailable: true, averageImprovement: '15-25%' },
      { name: 'Downtime Reduction', unit: 'hours', dataAvailable: true, averageImprovement: '30-40%' },
      { name: 'Maintenance Cost Savings', unit: 'USD', dataAvailable: true, averageImprovement: '20-35%' },
      { name: 'Asset Lifespan Extension', unit: 'years', dataAvailable: true, averageImprovement: '2-5 years' },
      { name: 'Operational Efficiency', unit: 'throughput', dataAvailable: true, averageImprovement: '10-20%' },
      { name: 'Quality Improvement', unit: 'defect rate', dataAvailable: true, averageImprovement: '5-15%' },
      { name: 'Customer Satisfaction', unit: 'NPS', dataAvailable: false, averageImprovement: '10-30 points' },
      { name: 'Regulatory Compliance', unit: 'incidents', dataAvailable: true, averageImprovement: '60-90%' }
    ],
    usageTrends: [],
    valueCreationByIndustry: {}
  };

  // Generate usage trends data
  for (const deviceType of this.testContext.valueCreationData.deviceTypes) {
    // Create quarterly data for last 3 years
    const quarters = 12; // 3 years of quarterly data
    const baselineUsage = {
      operatingHours: Math.floor(Math.random() * 12) + 4, // 4-16 hours per day
      dataTransmissionFrequency: Math.floor(Math.random() * 1440) + 60, // 1-24 times per day (in minutes)
      featureUtilization: Math.random() * 0.4 + 0.3, // 30-70% of features used
      remoteInteractions: Math.floor(Math.random() * 10) + 1 // 1-10 interactions per day
    };

    const trend = {
      deviceType: deviceType.type,
      quarterlyData: []
    };

    for (let i = 0; i < quarters; i++) {
      // Create usage growth over time
      const growthFactor = 1 + (i * 0.05); // 5% growth per quarter

      trend.quarterlyData.push({
        quarter: `Q${(i % 4) + 1} ${2022 + Math.floor(i / 4)}`,
        operatingHours: baselineUsage.operatingHours * Math.min(growthFactor, 2), // Cap at 2x
        dataTransmissionFrequency: baselineUsage.dataTransmissionFrequency / Math.min(growthFactor, 3), // More frequent over time, cap at 3x
        featureUtilization: Math.min(baselineUsage.featureUtilization * growthFactor, 0.95), // Cap at 95%
        remoteInteractions: baselineUsage.remoteInteractions * Math.min(growthFactor, 4) // Cap at 4x
      });
    }

    this.testContext.valueCreationData.usageTrends.push(trend);
  }

  // Generate value creation by industry
  for (const industry of this.testContext.valueCreationData.industries) {
    this.testContext.valueCreationData.valueCreationByIndustry[industry] = {
      deviceAdoption: {},
      valueRealization: [],
      topChallenges: []
    };

    // Set device adoption rates per industry
    for (const deviceType of this.testContext.valueCreationData.deviceTypes) {
      // Different industries have different adoption patterns
      let adoptionRate;
      let growthRate;

      switch (industry) {
        case 'Manufacturing':
          adoptionRate = deviceType.type === 'water-heater' ? 0.7 :
                        deviceType.type === 'hvac' ? 0.6 :
                        deviceType.type === 'robot' ? 0.4 : 0.2;
          growthRate = deviceType.type === 'robot' ? 0.3 : 0.15;
          break;
        case 'Healthcare':
          adoptionRate = deviceType.type === 'water-heater' ? 0.8 :
                        deviceType.type === 'hvac' ? 0.7 : 0.3;
          growthRate = 0.1;
          break;
        case 'Hospitality':
          adoptionRate = deviceType.type === 'water-heater' ? 0.9 :
                        deviceType.type === 'hvac' ? 0.8 :
                        deviceType.type === 'refrigeration' ? 0.7 : 0.2;
          growthRate = 0.12;
          break;
        default:
          adoptionRate = Math.random() * 0.5 + 0.2; // 20-70%
          growthRate = Math.random() * 0.2 + 0.05; // 5-25%
      }

      this.testContext.valueCreationData.valueCreationByIndustry[industry].deviceAdoption[deviceType.type] = {
        currentAdoptionRate: adoptionRate,
        projectedGrowthRate: growthRate,
        averageDeploymentSize: Math.floor(Math.random() * 20) + 5 // 5-25 devices per customer
      };
    }

    // Set value realization metrics
    for (const metric of this.testContext.valueCreationData.valueMetrics) {
      // Different value realization based on industry
      const realization = {
        metric: metric.name,
        industryAverage: Math.random() * 0.7 + 0.3, // 30-100% of average improvement
        leadingPerformers: Math.random() * 0.3 + 0.7, // 70-100% of average improvement
        timeToValue: Math.floor(Math.random() * 10) + 2, // 2-12 months
        sustainabilityOfValue: Math.random() > 0.3 // 70% sustainable value
      };

      this.testContext.valueCreationData.valueCreationByIndustry[industry].valueRealization.push(realization);
    }

    // Set industry-specific challenges
    const commonChallenges = [
      'Integration complexity',
      'User adoption',
      'Legacy systems compatibility',
      'ROI justification',
      'Data security',
      'Training requirements',
      'Maintenance knowledge'
    ];

    // Select 3-5 challenges for each industry
    const challengeCount = Math.floor(Math.random() * 3) + 3;
    const shuffledChallenges = [...commonChallenges].sort(() => 0.5 - Math.random());
    this.testContext.valueCreationData.valueCreationByIndustry[industry].topChallenges =
      shuffledChallenges.slice(0, challengeCount);
  }
});

Given('current business model configuration', async function() {
  // Define the current business model
  this.testContext.currentBusinessModel = {
    name: 'Traditional Hardware + Services',
    components: [
      {
        name: 'Hardware Sales',
        revenueContribution: 0.65, // 65% of revenue
        marginProfile: 0.35, // 35% margin
        growthRate: 0.08, // 8% annual growth
        salesCycle: 90, // 90 days
        customerAcquisitionCost: 5000, // $5,000 per new customer
        recurringRevenue: false
      },
      {
        name: 'Maintenance Services',
        revenueContribution: 0.25, // 25% of revenue
        marginProfile: 0.50, // 50% margin
        growthRate: 0.12, // 12% annual growth
        salesCycle: 30, // 30 days
        customerAcquisitionCost: 1000, // $1,000 per new customer
        recurringRevenue: true,
        contractLength: 12 // 12 months
      },
      {
        name: 'Parts and Supplies',
        revenueContribution: 0.10, // 10% of revenue
        marginProfile: 0.45, // 45% margin
        growthRate: 0.05, // 5% annual growth
        salesCycle: 15, // 15 days
        customerAcquisitionCost: 500, // $500 per new customer
        recurringRevenue: true,
        repurchaseFrequency: 3 // Every 3 months
      }
    ],
    keyMetrics: {
      customerLifetimeValue: 50000, // $50,000
      averageContractValue: 35000, // $35,000
      renewalRate: 0.75, // 75%
      customerSatisfaction: 0.82, // 82%
      referralRate: 0.15 // 15%
    },
    limitingFactors: [
      'Capital-intensive upfront costs',
      'Long sales cycles for new customers',
      'Inconsistent service revenue',
      'Limited recurring revenue components',
      'Margin pressure on hardware'
    ]
  };
});

Given('competitor business model information', async function() {
  // Create competitor business model information
  this.testContext.competitorBusinessModels = [
    {
      competitorName: 'Traditional Competitor A',
      modelType: 'Hardware-Centric',
      description: 'Similar to current model with focus on high-margin hardware',
      marketShare: 0.28, // 28%
      strengths: ['Established brand', 'Wide distribution', 'Large install base'],
      weaknesses: ['Limited services', 'Slow innovation cycle', 'High prices'],
      uniqueValue: 'Premium hardware quality and reliability'
    },
    {
      competitorName: 'Digital Disruptor B',
      modelType: 'Subscription-First',
      description: 'Hardware-as-a-Service with monthly subscriptions instead of purchases',
      marketShare: 0.15, // 15%
      strengths: ['Predictable revenue', 'Lower customer entry barrier', 'Continuous upgrades'],
      weaknesses: ['Complex financing structure', 'Higher lifetime customer cost', 'Working capital requirements'],
      uniqueValue: 'No upfront costs and automatic technology refreshes'
    },
    {
      competitorName: 'Tech Giant C',
      modelType: 'Platform Ecosystem',
      description: 'Integrated hardware, software and marketplace of extensions',
      marketShare: 0.12, // 12%
      strengths: ['Network effects', 'Partner ecosystem leverage', 'Multiple revenue streams'],
      weaknesses: ['Complex partner management', 'Platform governance challenges', 'Partner dependency'],
      uniqueValue: 'One-stop solution with extensive third-party integrations'
    },
    {
      competitorName: 'Analytics Specialist D',
      modelType: 'Data-Monetization',
      description: 'Low-cost hardware with premium analytics services',
      marketShare: 0.08, // 8%
      strengths: ['High-margin services', 'Actionable insights', 'Customer stickiness'],
      weaknesses: ['Privacy concerns', 'Hardware commoditization', 'Services sales complexity'],
      uniqueValue: 'Industry benchmarking and AI-driven recommendations'
    },
    {
      competitorName: 'Industry Vertical E',
      modelType: 'Outcome-Based',
      description: 'Charging based on measurable business outcomes, not products or time',
      marketShare: 0.05, // 5%
      strengths: ['Perfect alignment with customer value', 'Differentiation', 'High customer loyalty'],
      weaknesses: ['Outcome measurement challenges', 'Revenue predictability', 'Risk management'],
      uniqueValue: 'Guaranteed outcomes with shared success model'
    }
  ];

  // Add market dynamics
  this.testContext.marketDynamics = {
    customerPreferences: {
      subscriptionVsPurchase: {
        current: { subscription: 0.35, purchase: 0.65 },
        trend: 'Increasing preference for subscription models',
        yearOverYearChange: 0.05 // 5% shift toward subscription annually
      },
      valueDrivers: {
        priceVsValue: { price: 0.40, value: 0.60 },
        upfrontVsLifetime: { upfront: 0.45, lifetime: 0.55 },
        ownershipVsAccess: { ownership: 0.55, access: 0.45 }
      }
    },
    industryTrends: [
      'Increasing focus on total cost of ownership',
      'Growing demand for usage-based pricing',
      'Rising importance of sustainability metrics',
      'Preference for integrated solutions over point products',
      'Consumerization of enterprise buying experience'
    ],
    disruptiveForces: [
      'Cloud-based management replacing on-premise',
      'AI-driven automation reducing traditional service needs',
      'IoT data creating new value streams',
      'Circular economy promoting reuse and refurbishment',
      'Open ecosystems challenging proprietary approaches'
    ]
  };
});

/**
 * User actions
 */
When('the business innovation system analyzes value creation patterns', async function() {
  try {
    // Analyze business model opportunities
    const businessModelAnalysis = await this.analyticsEngine.analyzeBusinessModelOpportunities({
      valueCreationData: this.testContext.valueCreationData,
      currentBusinessModel: this.testContext.currentBusinessModel,
      competitorBusinessModels: this.testContext.competitorBusinessModels,
      marketDynamics: this.testContext.marketDynamics,
      analysisTimeframe: '5 years'
    });

    this.testContext.businessModelAnalysis = businessModelAnalysis;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

/**
 * Verification steps
 */
Then('it should identify potential new business models such as:', function(dataTable) {
  const expectedModels = dataTable.rowsHash();
  const analysis = this.testContext.businessModelAnalysis;

  expect(analysis).to.have.property('businessModelOpportunities');
  expect(analysis.businessModelOpportunities).to.be.an('array');
  expect(analysis.businessModelOpportunities.length).to.be.at.least(Object.keys(expectedModels).length);

  // Check that all expected model types are included
  for (const [modelType] of Object.entries(expectedModels)) {
    const matchingModel = analysis.businessModelOpportunities.find(
      model => model.type.toLowerCase() === modelType.toLowerCase()
    );

    expect(matchingModel, `Business model of type ${modelType} should be identified`).to.not.be.undefined;
  }
});

Then('each model should include:', function(dataTable) {
  const expectedAttributes = dataTable.rowsHash();
  const analysis = this.testContext.businessModelAnalysis;

  for (const model of analysis.businessModelOpportunities) {
    // Check each model has all the required attributes
    for (const [attribute] of Object.entries(expectedAttributes)) {
      // Convert to camelCase
      const propertyName = attribute
        .toLowerCase()
        .replace(/[^a-z0-9]+(.)/g, (match, chr) => chr.toUpperCase());

      expect(model, `Model ${model.type} should have ${attribute} attribute`).to.have.property(propertyName);
    }
  }
});
