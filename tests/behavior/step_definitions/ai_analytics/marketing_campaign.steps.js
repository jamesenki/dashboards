/**
 * Step definitions for targeted marketing campaign scenarios
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
Given('customer segmentation data', async function() {
  // Reuse customer segmentation data if available, otherwise create it
  if (!this.testContext.customerSegments) {
    this.testContext.customerSegments = [
      {
        id: 'enterprise-industrial',
        name: 'Enterprise Industrial',
        industries: ['Manufacturing', 'Food Processing', 'Pharmaceuticals'],
        size: 'Enterprise',
        demographics: {
          region: ['Northeast', 'Midwest'],
          employeeCount: '1000-5000',
          annualRevenue: '$500M-1B'
        },
        psychographics: {
          painPoints: ['Equipment reliability', 'Operational efficiency', 'Regulatory compliance'],
          decisionDrivers: ['ROI', 'Reliability', 'Support quality'],
          riskTolerance: 'Medium-Low'
        },
        behaviorMetrics: {
          purchaseCycle: '12-24 months',
          informationSources: ['Industry events', 'Peer recommendations', 'Consultant advice'],
          digitalEngagement: 'Medium'
        }
      },
      {
        id: 'mid-market-commercial',
        name: 'Mid-Market Commercial',
        industries: ['Hospitality', 'Healthcare', 'Retail'],
        size: 'Mid-Market',
        demographics: {
          region: ['Southeast', 'West'],
          employeeCount: '250-1000',
          annualRevenue: '$50M-250M'
        },
        psychographics: {
          painPoints: ['Cost management', 'Staff efficiency', 'Customer experience'],
          decisionDrivers: ['Total cost of ownership', 'Ease of use', 'Customer satisfaction impact'],
          riskTolerance: 'Medium'
        },
        behaviorMetrics: {
          purchaseCycle: '6-12 months',
          informationSources: ['Industry publications', 'Digital content', 'Sales relationships'],
          digitalEngagement: 'Medium-High'
        }
      },
      {
        id: 'small-business',
        name: 'Small Business',
        industries: ['Restaurants', 'Small Retail', 'Services'],
        size: 'Small Business',
        demographics: {
          region: ['West', 'Southeast', 'Southwest'],
          employeeCount: '10-50',
          annualRevenue: '$1M-10M'
        },
        psychographics: {
          painPoints: ['Cash flow management', 'Operational simplicity', 'Reliability'],
          decisionDrivers: ['Upfront cost', 'Simplicity', 'Local support'],
          riskTolerance: 'Low'
        },
        behaviorMetrics: {
          purchaseCycle: '3-6 months',
          informationSources: ['Online research', 'Peer recommendations', 'Local providers'],
          digitalEngagement: 'Varied'
        }
      },
      {
        id: 'educational-institutions',
        name: 'Educational Institutions',
        industries: ['Higher Education', 'K-12 Schools'],
        size: 'Varied',
        demographics: {
          region: ['Nationwide'],
          employeeCount: '500-2000',
          annualRevenue: 'Non-profit'
        },
        psychographics: {
          painPoints: ['Budget constraints', 'Long-term planning', 'Sustainability goals'],
          decisionDrivers: ['Total cost of ownership', 'Sustainability', 'Educational impact'],
          riskTolerance: 'Low'
        },
        behaviorMetrics: {
          purchaseCycle: '12-36 months',
          informationSources: ['RFPs', 'Education-specific publications', 'Peer institutions'],
          digitalEngagement: 'Medium'
        }
      },
      {
        id: 'public-sector',
        name: 'Public Sector',
        industries: ['Government Facilities', 'Municipal Buildings'],
        size: 'Large',
        demographics: {
          region: ['Nationwide'],
          employeeCount: '1000+',
          annualRevenue: 'Budget-based'
        },
        psychographics: {
          painPoints: ['Procurement rules', 'Budget cycles', 'Long-term planning'],
          decisionDrivers: ['Compliance', 'Longevity', 'Service guarantees'],
          riskTolerance: 'Very Low'
        },
        behaviorMetrics: {
          purchaseCycle: '18-36 months',
          informationSources: ['Formal RFPs', 'Approved vendor lists', 'Agency recommendations'],
          digitalEngagement: 'Low-Medium'
        }
      }
    ];
  }
});

Given('historical campaign performance data', async function() {
  // Create historical campaign performance data
  this.testContext.campaignHistory = {
    campaigns: [
      {
        id: 'general-awareness-2023',
        name: 'General Brand Awareness 2023',
        type: 'Awareness',
        audience: 'General',
        channels: ['Digital Display', 'Industry Publications', 'Trade Shows'],
        budget: 150000,
        duration: '3 months',
        metrics: {
          impressions: 1500000,
          clicks: 22500,
          leads: 450,
          opportunities: 90,
          deals: 15,
          revenue: 525000,
          roi: 2.5
        },
        messaging: {
          primary: 'Leading provider of intelligent equipment solutions',
          secondary: 'Trusted by industry leaders across verticals',
          callToAction: 'Learn how our solutions can transform your operations'
        }
      },
      {
        id: 'manufacturing-solution-2023',
        name: 'Manufacturing Solutions Campaign 2023',
        type: 'Solution-specific',
        audience: 'Manufacturing',
        channels: ['LinkedIn', 'Email', 'Industry Publications', 'Direct Mail'],
        budget: 80000,
        duration: '2 months',
        metrics: {
          impressions: 750000,
          clicks: 18750,
          leads: 185,
          opportunities: 55,
          deals: 22,
          revenue: 880000,
          roi: 10
        },
        messaging: {
          primary: 'Improve manufacturing efficiency with smart equipment',
          secondary: 'Reduce downtime by up to 30% and extend equipment life',
          callToAction: 'Schedule a consultation with our manufacturing specialists'
        }
      },
      {
        id: 'small-business-2023',
        name: 'Small Business Solutions 2023',
        type: 'Segment-specific',
        audience: 'Small Business',
        channels: ['Facebook', 'Google Ads', 'Local Events'],
        budget: 50000,
        duration: '2 months',
        metrics: {
          impressions: 1200000,
          clicks: 36000,
          leads: 320,
          opportunities: 45,
          deals: 18,
          revenue: 270000,
          roi: 4.4
        },
        messaging: {
          primary: 'Affordable smart equipment solutions for small businesses',
          secondary: 'Better reliability, lower costs, and simplified operations',
          callToAction: 'See how small businesses like yours are saving money'
        }
      },
      {
        id: 'healthcare-solution-2023',
        name: 'Healthcare Solutions Campaign 2023',
        type: 'Solution-specific',
        audience: 'Healthcare',
        channels: ['Email', 'Healthcare Publications', 'Events', 'Direct Outreach'],
        budget: 70000,
        duration: '3 months',
        metrics: {
          impressions: 450000,
          clicks: 9000,
          leads: 125,
          opportunities: 35,
          deals: 12,
          revenue: 600000,
          roi: 7.57
        },
        messaging: {
          primary: 'Smart equipment solutions for reliable healthcare operations',
          secondary: 'Ensure patient safety with reliable equipment and predictive maintenance',
          callToAction: 'Learn about our healthcare-specific solutions'
        }
      },
      {
        id: 'product-launch-2024',
        name: 'New Product Launch 2024',
        type: 'Product-specific',
        audience: 'Multiple segments',
        channels: ['Digital Display', 'Email', 'Social Media', 'PR', 'Events'],
        budget: 200000,
        duration: '3 months',
        metrics: {
          impressions: 2000000,
          clicks: 40000,
          leads: 600,
          opportunities: 120,
          deals: 40,
          revenue: 1600000,
          roi: 7
        },
        messaging: {
          primary: 'Introducing our next-generation smart equipment platform',
          secondary: 'More insights, better efficiency, lower total cost of ownership',
          callToAction: 'Be among the first to experience the future of smart equipment'
        }
      }
    ]
  };
});

Given('product usage patterns by segment', async function() {
  // Create product usage patterns by segment
  this.testContext.usagePatterns = {};
  
  // For each customer segment
  for (const segment of this.testContext.customerSegments) {
    this.testContext.usagePatterns[segment.id] = {
      primaryDeviceTypes: segment.id === 'enterprise-industrial' ? 
        ['water-heater', 'hvac', 'industrial-refrigeration'] :
        segment.id === 'small-business' ? 
        ['water-heater'] : ['water-heater', 'hvac'],
      featureUtilization: {
        basic: 0.95, // 95% use basic features
        advanced: segment.id === 'enterprise-industrial' ? 0.65 : 
                  segment.id === 'mid-market-commercial' ? 0.45 : 0.25,
        ai: segment.id === 'enterprise-industrial' ? 0.35 : 
            segment.id === 'mid-market-commercial' ? 0.20 : 0.05
      },
      usageFrequency: {
        dailyActiveUsers: segment.id === 'enterprise-industrial' ? 0.40 : 
                           segment.id === 'mid-market-commercial' ? 0.30 : 0.20,
        weeklyActiveUsers: segment.id === 'enterprise-industrial' ? 0.75 : 
                            segment.id === 'mid-market-commercial' ? 0.60 : 0.45,
        monthlyActiveUsers: segment.id === 'enterprise-industrial' ? 0.95 : 
                             segment.id === 'mid-market-commercial' ? 0.85 : 0.70
      },
      primaryUseCase: segment.id === 'enterprise-industrial' ? 
        'Operational efficiency and compliance' :
        segment.id === 'mid-market-commercial' ? 
        'Cost management and reliability' :
        segment.id === 'small-business' ? 
        'Basic operational needs' :
        segment.id === 'educational-institutions' ? 
        'Maintenance planning and sustainability' : 'Budget compliance and planning',
      valuePerception: {
        costSavings: segment.id === 'small-business' ? 'High' : 'Medium',
        operationalEfficiency: segment.id === 'enterprise-industrial' ? 'High' : 'Medium',
        reliability: 'High',
        serviceQuality: segment.id === 'enterprise-industrial' ? 'High' : 'Medium'
      }
    };
  }
});

/**
 * User actions
 */
When('the marketing optimization system analyzes customer responses', async function() {
  try {
    // Analyze customer responses and optimize marketing
    const marketingAnalysis = await this.analyticsEngine.optimizeMarketingCampaigns({
      customerSegments: this.testContext.customerSegments,
      campaignHistory: this.testContext.campaignHistory,
      usagePatterns: this.testContext.usagePatterns,
      targetQuarters: 4, // Plan for next 4 quarters
      optimizationGoal: 'balanced' // Balance acquisition, engagement, and retention
    });
    
    this.testContext.marketingAnalysis = marketingAnalysis;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

/**
 * Verification steps
 */
Then('it should generate segment-specific marketing messaging', function() {
  const analysis = this.testContext.marketingAnalysis;
  
  expect(analysis).to.have.property('segmentMessaging');
  expect(analysis.segmentMessaging).to.be.an('object');
  
  // Should have messaging for each segment
  for (const segment of this.testContext.customerSegments) {
    expect(analysis.segmentMessaging).to.have.property(segment.id);
    
    const messaging = analysis.segmentMessaging[segment.id];
    expect(messaging).to.have.property('valueProposition');
    expect(messaging).to.have.property('keySelling');
    expect(messaging).to.have.property('messagingFrameworks');
    expect(messaging.messagingFrameworks).to.be.an('object');
    expect(messaging.messagingFrameworks).to.have.property('primary');
    expect(messaging.messagingFrameworks).to.have.property('supporting');
    expect(messaging.messagingFrameworks).to.have.property('callToAction');
  }
});

Then('it should recommend optimal channel mix by segment', function() {
  const analysis = this.testContext.marketingAnalysis;
  
  expect(analysis).to.have.property('channelRecommendations');
  expect(analysis.channelRecommendations).to.be.an('object');
  
  // Should have channel recommendations for each segment
  for (const segment of this.testContext.customerSegments) {
    expect(analysis.channelRecommendations).to.have.property(segment.id);
    
    const channelMix = analysis.channelRecommendations[segment.id];
    expect(channelMix).to.have.property('primaryChannels');
    expect(channelMix.primaryChannels).to.be.an('array');
    expect(channelMix).to.have.property('secondaryChannels');
    expect(channelMix.secondaryChannels).to.be.an('array');
    expect(channelMix).to.have.property('budgetAllocation');
    expect(channelMix.budgetAllocation).to.be.an('object');
    expect(channelMix).to.have.property('timingRecommendations');
  }
});

Then('it should predict campaign performance metrics by segment', function() {
  const analysis = this.testContext.marketingAnalysis;
  
  expect(analysis).to.have.property('performancePredictions');
  expect(analysis.performancePredictions).to.be.an('object');
  
  // Should have performance predictions for each segment
  for (const segment of this.testContext.customerSegments) {
    expect(analysis.performancePredictions).to.have.property(segment.id);
    
    const predictions = analysis.performancePredictions[segment.id];
    expect(predictions).to.have.property('expectedLeads');
    expect(predictions).to.have.property('expectedConversionRate');
    expect(predictions).to.have.property('expectedRevenue');
    expect(predictions).to.have.property('expectedROI');
    expect(predictions).to.have.property('confidenceInterval');
  }
});

Then('it should optimize marketing budget allocation across segments', function() {
  const analysis = this.testContext.marketingAnalysis;
  
  expect(analysis).to.have.property('budgetOptimization');
  expect(analysis.budgetOptimization).to.be.an('object');
  expect(analysis.budgetOptimization).to.have.property('recommendedAllocation');
  expect(analysis.budgetOptimization.recommendedAllocation).to.be.an('object');
  
  // Total allocation should be 100%
  const totalAllocation = Object.values(analysis.budgetOptimization.recommendedAllocation)
    .reduce((sum, value) => sum + value, 0);
  expect(totalAllocation).to.be.closeTo(1, 0.001); // Within rounding error of 100%
  
  // Should explain the allocation strategy
  expect(analysis.budgetOptimization).to.have.property('allocationRationale');
  expect(analysis.budgetOptimization.allocationRationale).to.be.an('object');
  
  // Should have quarterly breakdown
  expect(analysis.budgetOptimization).to.have.property('quarterlyBreakdown');
  expect(analysis.budgetOptimization.quarterlyBreakdown).to.be.an('array');
  expect(analysis.budgetOptimization.quarterlyBreakdown.length).to.equal(4); // 4 quarters
});

Then('it should identify the highest ROI marketing opportunities', function() {
  const analysis = this.testContext.marketingAnalysis;
  
  expect(analysis).to.have.property('highestRoiOpportunities');
  expect(analysis.highestRoiOpportunities).to.be.an('array');
  expect(analysis.highestRoiOpportunities.length).to.be.at.least(3);
  
  // Each opportunity should have detailed attributes
  for (const opportunity of analysis.highestRoiOpportunities) {
    expect(opportunity).to.have.property('segment');
    expect(opportunity).to.have.property('channel');
    expect(opportunity).to.have.property('messageTheme');
    expect(opportunity).to.have.property('expectedRoi');
    expect(opportunity).to.have.property('investmentRequired');
    expect(opportunity).to.have.property('timeToResults');
  }
  
  // Opportunities should be sorted by ROI (highest first)
  for (let i = 1; i < analysis.highestRoiOpportunities.length; i++) {
    expect(analysis.highestRoiOpportunities[i-1].expectedRoi)
      .to.be.at.least(analysis.highestRoiOpportunities[i].expectedRoi);
  }
});

Then('it should generate A/B testing variants for key messages', function() {
  const analysis = this.testContext.marketingAnalysis;
  
  expect(analysis).to.have.property('abTestingPlan');
  expect(analysis.abTestingPlan).to.be.an('object');
  expect(analysis.abTestingPlan).to.have.property('messageVariants');
  expect(analysis.abTestingPlan.messageVariants).to.be.an('object');
  
  // Should have variants for each segment
  for (const segment of this.testContext.customerSegments) {
    expect(analysis.abTestingPlan.messageVariants).to.have.property(segment.id);
    
    const variants = analysis.abTestingPlan.messageVariants[segment.id];
    expect(variants).to.be.an('array');
    expect(variants.length).to.be.at.least(2); // At least 2 variants
    
    // Each variant should have specific elements
    for (const variant of variants) {
      expect(variant).to.have.property('headline');
      expect(variant).to.have.property('subheadline');
      expect(variant).to.have.property('callToAction');
      expect(variant).to.have.property('expectedImpact');
    }
  }
  
  // Should have test execution plan
  expect(analysis.abTestingPlan).to.have.property('testingSchedule');
  expect(analysis.abTestingPlan).to.have.property('successMetrics');
  expect(analysis.abTestingPlan).to.have.property('sampleSizeRequirements');
});
