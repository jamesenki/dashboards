/**
 * Step definitions for competitive analysis scenarios
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
Given('market data on competitors and their offerings', async function() {
  // Create market data on competitors and their offerings
  this.testContext.competitorData = {
    competitors: [
      {
        name: 'TraditionTech',
        type: 'Established Industry Leader',
        marketShare: 0.32, // 32%
        primaryOfferings: ['Industrial Water Heaters', 'HVAC Systems', 'Basic Monitoring'],
        pricing: {
          positioning: 'Premium',
          model: 'Traditional purchase + maintenance contracts',
          relativeCost: 1.1 // 10% above average
        },
        strengths: [
          'Brand recognition',
          'Established distribution networks',
          'Large installed base',
          'Proven durability'
        ],
        weaknesses: [
          'Limited IoT capabilities',
          'Slow innovation cycle',
          'Fragmented digital experience',
          'High TCO'
        ],
        recentMoves: [
          'Acquired small IoT monitoring company',
          'Launched basic analytics dashboard',
          'Introduced extended warranty program'
        ]
      },
      {
        name: 'SmartSolutions',
        type: 'Digital-First Disruptor',
        marketShare: 0.18, // 18%
        primaryOfferings: ['Smart Water Heaters', 'IoT Platform', 'Predictive Analytics'],
        pricing: {
          positioning: 'Value',
          model: 'Hardware-as-a-Service + subscription tiers',
          relativeCost: 0.95 // 5% below average when comparing TCO
        },
        strengths: [
          'Advanced IoT platform',
          'Superior user experience',
          'Data-driven insights',
          'Attractive financing options'
        ],
        weaknesses: [
          'Limited product range',
          'Smaller service network',
          'Less proven long-term reliability',
          'Complex contracts'
        ],
        recentMoves: [
          'Launched usage-based pricing tier',
          'Expanded device partnerships',
          'Opened API for third-party integrations'
        ]
      },
      {
        name: 'GlobalTech',
        type: 'Tech Giant Expansion',
        marketShare: 0.15, // 15%
        primaryOfferings: ['Smart Building Platform', 'IoT Ecosystem', 'Enterprise Analytics'],
        pricing: {
          positioning: 'Premium Ecosystem',
          model: 'Platform licenses + hardware partnerships',
          relativeCost: 1.15 // 15% above average
        },
        strengths: [
          'Comprehensive ecosystem',
          'Advanced AI capabilities',
          'Strong enterprise relationships',
          'Deep R&D resources'
        ],
        weaknesses: [
          'Less industry-specific expertise',
          'Complex implementation',
          'Higher initial investment',
          'Lock-in concerns'
        ],
        recentMoves: [
          'Acquired building management system company',
          'Launched vertical-specific solutions',
          'Introduced sustainability analytics'
        ]
      },
      {
        name: 'EcoSystems',
        type: 'Sustainability Specialist',
        marketShare: 0.08, // 8%
        primaryOfferings: ['Eco-Efficient Equipment', 'Energy Optimization', 'Sustainability Reporting'],
        pricing: {
          positioning: 'Premium Green',
          model: 'Premium hardware + efficiency-as-a-service',
          relativeCost: 1.2 // 20% above average upfront, but marketed on TCO benefits
        },
        strengths: [
          'Strong sustainability credentials',
          'Energy efficiency leadership',
          'Regulatory compliance expertise',
          'Attractive to ESG-focused customers'
        ],
        weaknesses: [
          'Premium pricing',
          'Narrower product range',
          'Smaller market presence',
          'Longer ROI timeframe'
        ],
        recentMoves: [
          'Launched carbon footprint tracking',
          'Secured green certification for all products',
          'Introduced circular economy program'
        ]
      },
      {
        name: 'RegionalSystems',
        type: 'Regional Specialist',
        marketShare: 0.12, // 12%
        primaryOfferings: ['Water Heaters', 'Local Service', 'Custom Solutions'],
        pricing: {
          positioning: 'Value',
          model: 'Competitive hardware + high-touch service',
          relativeCost: 0.9 // 10% below average
        },
        strengths: [
          'Strong regional presence',
          'Customer relationships',
          'Responsive service',
          'Local market knowledge'
        ],
        weaknesses: [
          'Limited technology capabilities',
          'Geographical constraints',
          'Basic digital offerings',
          'Scale limitations'
        ],
        recentMoves: [
          'Partnered with IoT platform provider',
          'Expanded service territory',
          'Introduced financing options'
        ]
      }
    ],
    marketTrends: [
      'Increasing customer demand for integrated solutions',
      'Growing focus on energy efficiency and sustainability',
      'Shift toward outcome-based contracts',
      'Rising importance of data security and privacy',
      'Consolidation of smaller regional players',
      'Entrance of technology companies into the space'
    ],
    regulatoryEnvironment: [
      'Tightening energy efficiency standards',
      'Increased focus on data privacy regulations',
      'Carbon reduction mandates in some regions',
      'Extended producer responsibility legislation',
      'Cybersecurity requirements for connected devices'
    ]
  };
});

Given('customer sentiment data across competing products', async function() {
  // Create customer sentiment data across competing products
  this.testContext.customerSentiment = {
    satisfactionScores: {
      'TraditionTech': {
        overall: 7.2, // Out of 10
        reliability: 8.5,
        performance: 7.4,
        costValue: 6.2,
        userExperience: 5.8,
        customerService: 7.6,
        innovationPerception: 5.2
      },
      'SmartSolutions': {
        overall: 8.3,
        reliability: 7.6,
        performance: 8.2,
        costValue: 8.0,
        userExperience: 9.1,
        customerService: 7.4,
        innovationPerception: 9.0
      },
      'GlobalTech': {
        overall: 7.8,
        reliability: 8.0,
        performance: 8.4,
        costValue: 6.5,
        userExperience: 8.6,
        customerService: 6.8,
        innovationPerception: 8.8
      },
      'EcoSystems': {
        overall: 8.0,
        reliability: 8.2,
        performance: 8.5,
        costValue: 6.6,
        userExperience: 7.8,
        customerService: 8.1,
        innovationPerception: 8.4
      },
      'RegionalSystems': {
        overall: 7.6,
        reliability: 7.9,
        performance: 7.1,
        costValue: 8.3,
        userExperience: 6.2,
        customerService: 8.7,
        innovationPerception: 5.4
      }
    },
    unmetNeeds: [
      {
        need: 'Seamless multi-system integration',
        importance: 8.4,
        satisfactionByCompetitor: {
          'TraditionTech': 5.2,
          'SmartSolutions': 7.8,
          'GlobalTech': 8.5,
          'EcoSystems': 6.9,
          'RegionalSystems': 4.8
        }
      },
      {
        need: 'Predictive maintenance that actually works',
        importance: 9.1,
        satisfactionByCompetitor: {
          'TraditionTech': 5.8,
          'SmartSolutions': 8.1,
          'GlobalTech': 7.9,
          'EcoSystems': 6.7,
          'RegionalSystems': 5.1
        }
      },
      {
        need: 'Simple, transparent pricing model',
        importance: 8.9,
        satisfactionByCompetitor: {
          'TraditionTech': 6.7,
          'SmartSolutions': 6.9,
          'GlobalTech': 5.8,
          'EcoSystems': 6.1,
          'RegionalSystems': 8.2
        }
      },
      {
        need: 'End-to-end sustainability management',
        importance: 7.6,
        satisfactionByCompetitor: {
          'TraditionTech': 5.1,
          'SmartSolutions': 7.2,
          'GlobalTech': 7.5,
          'EcoSystems': 9.0,
          'RegionalSystems': 4.8
        }
      },
      {
        need: 'Reliable post-installation support',
        importance: 9.3,
        satisfactionByCompetitor: {
          'TraditionTech': 7.8,
          'SmartSolutions': 6.9,
          'GlobalTech': 6.2,
          'EcoSystems': 7.4,
          'RegionalSystems': 8.9
        }
      }
    ],
    netPromoterScores: {
      'TraditionTech': 42,
      'SmartSolutions': 56,
      'GlobalTech': 48,
      'EcoSystems': 51,
      'RegionalSystems': 45
    },
    sentimentTrends: {
      'TraditionTech': 'Declining',
      'SmartSolutions': 'Improving',
      'GlobalTech': 'Stable',
      'EcoSystems': 'Improving',
      'RegionalSystems': 'Stable'
    }
  };
});

Given('feature comparison data across the product landscape', async function() {
  // Create feature comparison data across the product landscape
  this.testContext.featureComparison = {
    featureCategories: [
      {
        category: 'Core Equipment Functionality',
        features: [
          {
            name: 'Energy Efficiency Rating',
            importance: 9.2,
            competitorRatings: {
              'TraditionTech': 7.8,
              'SmartSolutions': 8.5,
              'GlobalTech': 8.2,
              'EcoSystems': 9.5,
              'RegionalSystems': 7.2
            }
          },
          {
            name: 'Reliability/Durability',
            importance: 9.5,
            competitorRatings: {
              'TraditionTech': 9.0,
              'SmartSolutions': 7.8,
              'GlobalTech': 8.3,
              'EcoSystems': 8.5,
              'RegionalSystems': 8.2
            }
          },
          {
            name: 'Operational Performance',
            importance: 8.8,
            competitorRatings: {
              'TraditionTech': 8.2,
              'SmartSolutions': 8.6,
              'GlobalTech': 8.5,
              'EcoSystems': 8.7,
              'RegionalSystems': 7.4
            }
          }
        ]
      },
      {
        category: 'Smart Capabilities',
        features: [
          {
            name: 'Remote Monitoring',
            importance: 8.5,
            competitorRatings: {
              'TraditionTech': 6.2,
              'SmartSolutions': 9.1,
              'GlobalTech': 9.3,
              'EcoSystems': 8.4,
              'RegionalSystems': 5.5
            }
          },
          {
            name: 'Predictive Analytics',
            importance: 8.2,
            competitorRatings: {
              'TraditionTech': 5.5,
              'SmartSolutions': 8.8,
              'GlobalTech': 9.0,
              'EcoSystems': 7.8,
              'RegionalSystems': 4.2
            }
          },
          {
            name: 'Mobile App Experience',
            importance: 7.9,
            competitorRatings: {
              'TraditionTech': 5.8,
              'SmartSolutions': 9.2,
              'GlobalTech': 8.8,
              'EcoSystems': 7.9,
              'RegionalSystems': 5.0
            }
          },
          {
            name: 'Integration Capabilities',
            importance: 7.6,
            competitorRatings: {
              'TraditionTech': 4.8,
              'SmartSolutions': 8.2,
              'GlobalTech': 9.4,
              'EcoSystems': 7.2,
              'RegionalSystems': 4.5
            }
          }
        ]
      },
      {
        category: 'Customer Experience',
        features: [
          {
            name: 'Installation Process',
            importance: 8.4,
            competitorRatings: {
              'TraditionTech': 7.8,
              'SmartSolutions': 8.0,
              'GlobalTech': 7.2,
              'EcoSystems': 7.8,
              'RegionalSystems': 8.7
            }
          },
          {
            name: 'Service Quality',
            importance: 9.0,
            competitorRatings: {
              'TraditionTech': 8.2,
              'SmartSolutions': 7.5,
              'GlobalTech': 6.8,
              'EcoSystems': 8.0,
              'RegionalSystems': 9.1
            }
          },
          {
            name: 'Support Responsiveness',
            importance: 8.7,
            competitorRatings: {
              'TraditionTech': 7.8,
              'SmartSolutions': 7.9,
              'GlobalTech': 6.5,
              'EcoSystems': 7.8,
              'RegionalSystems': 8.8
            }
          }
        ]
      },
      {
        category: 'Business Model',
        features: [
          {
            name: 'Pricing Transparency',
            importance: 8.6,
            competitorRatings: {
              'TraditionTech': 7.2,
              'SmartSolutions': 6.8,
              'GlobalTech': 5.5,
              'EcoSystems': 6.5,
              'RegionalSystems': 8.5
            }
          },
          {
            name: 'Financing Options',
            importance: 7.8,
            competitorRatings: {
              'TraditionTech': 6.5,
              'SmartSolutions': 8.7,
              'GlobalTech': 7.8,
              'EcoSystems': 7.5,
              'RegionalSystems': 7.2
            }
          },
          {
            name: 'Total Cost of Ownership',
            importance: 9.1,
            competitorRatings: {
              'TraditionTech': 6.8,
              'SmartSolutions': 8.5,
              'GlobalTech': 7.2,
              'EcoSystems': 8.8,
              'RegionalSystems': 7.8
            }
          }
        ]
      }
    ],
    competitiveDifferentiators: {
      'TraditionTech': [
        'Established reliability track record',
        'Widest service network',
        'Broadest product range'
      ],
      'SmartSolutions': [
        'Best-in-class digital experience',
        'Most advanced predictive capabilities',
        'Flexible subscription model'
      ],
      'GlobalTech': [
        'Most comprehensive ecosystem',
        'Best third-party integrations',
        'Advanced enterprise features'
      ],
      'EcoSystems': [
        'Highest energy efficiency',
        'Leading sustainability features',
        'Best environmental certifications'
      ],
      'RegionalSystems': [
        'Best local service response time',
        'Most competitive pricing',
        'Most personalized customer service'
      ]
    }
  };
});

/**
 * User actions
 */
When('the competitive intelligence system analyzes the market position', async function() {
  try {
    // Analyze competitive position
    const competitiveAnalysis = await this.analyticsEngine.analyzeCompetitivePosition({
      competitorData: this.testContext.competitorData,
      customerSentiment: this.testContext.customerSentiment,
      featureComparison: this.testContext.featureComparison,
      analysisTimeframe: '3 years'
    });
    
    this.testContext.competitiveAnalysis = competitiveAnalysis;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

/**
 * Verification steps
 */
Then('it should identify key competitive strengths and vulnerabilities', function() {
  const analysis = this.testContext.competitiveAnalysis;
  
  expect(analysis).to.have.property('strengthsAndVulnerabilities');
  expect(analysis.strengthsAndVulnerabilities).to.be.an('object');
  expect(analysis.strengthsAndVulnerabilities).to.have.property('strengths');
  expect(analysis.strengthsAndVulnerabilities).to.have.property('vulnerabilities');
  
  // Check strengths array
  expect(analysis.strengthsAndVulnerabilities.strengths).to.be.an('array');
  expect(analysis.strengthsAndVulnerabilities.strengths.length).to.be.at.least(3);
  
  // Each strength should have specific properties
  for (const strength of analysis.strengthsAndVulnerabilities.strengths) {
    expect(strength).to.have.property('area');
    expect(strength).to.have.property('description');
    expect(strength).to.have.property('competitiveAdvantage');
    expect(strength).to.have.property('sustainability');
    expect(strength).to.have.property('relevantCompetitors');
  }
  
  // Check vulnerabilities array
  expect(analysis.strengthsAndVulnerabilities.vulnerabilities).to.be.an('array');
  expect(analysis.strengthsAndVulnerabilities.vulnerabilities.length).to.be.at.least(2);
  
  // Each vulnerability should have specific properties
  for (const vulnerability of analysis.strengthsAndVulnerabilities.vulnerabilities) {
    expect(vulnerability).to.have.property('area');
    expect(vulnerability).to.have.property('description');
    expect(vulnerability).to.have.property('impactSeverity');
    expect(vulnerability).to.have.property('mitigationOptions');
    expect(vulnerability).to.have.property('relevantCompetitors');
  }
});

Then('it should map opportunities for differentiation', function() {
  const analysis = this.testContext.competitiveAnalysis;
  
  expect(analysis).to.have.property('differentiationOpportunities');
  expect(analysis.differentiationOpportunities).to.be.an('array');
  expect(analysis.differentiationOpportunities.length).to.be.at.least(3);
  
  // Each opportunity should have specific properties
  for (const opportunity of analysis.differentiationOpportunities) {
    expect(opportunity).to.have.property('area');
    expect(opportunity).to.have.property('description');
    expect(opportunity).to.have.property('customerImpact');
    expect(opportunity).to.have.property('competitiveGap');
    expect(opportunity).to.have.property('implementationRequirements');
    expect(opportunity).to.have.property('timeToMarket');
  }
});

Then('it should highlight underserved market needs', function() {
  const analysis = this.testContext.competitiveAnalysis;
  
  expect(analysis).to.have.property('underservedNeeds');
  expect(analysis.underservedNeeds).to.be.an('array');
  expect(analysis.underservedNeeds.length).to.be.at.least(2);
  
  // Each need should have specific properties
  for (const need of analysis.underservedNeeds) {
    expect(need).to.have.property('need');
    expect(need).to.have.property('importance');
    expect(need).to.have.property('currentSatisfactionLevel');
    expect(need).to.have.property('targetCustomers');
    expect(need).to.have.property('solutionApproaches');
    expect(need).to.have.property('marketSizePotential');
  }
});

Then('it should recommend strategic positioning options', function() {
  const analysis = this.testContext.competitiveAnalysis;
  
  expect(analysis).to.have.property('strategicPositioningOptions');
  expect(analysis.strategicPositioningOptions).to.be.an('array');
  expect(analysis.strategicPositioningOptions.length).to.be.at.least(3);
  
  // Each positioning option should have specific properties
  for (const option of analysis.strategicPositioningOptions) {
    expect(option).to.have.property('positioningStatement');
    expect(option).to.have.property('targetSegments');
    expect(option).to.have.property('valueProposition');
    expect(option).to.have.property('competitiveResponse');
    expect(option).to.have.property('resourceRequirements');
    expect(option).to.have.property('expectedOutcomes');
    expect(option).to.have.property('riskAssessment');
  }
});

Then('it should quantify potential market share gains for each strategy', function() {
  const analysis = this.testContext.competitiveAnalysis;
  
  expect(analysis).to.have.property('marketShareProjections');
  expect(analysis.marketShareProjections).to.be.an('object');
  expect(analysis.marketShareProjections).to.have.property('baseline');
  expect(analysis.marketShareProjections).to.have.property('byStrategy');
  
  // Check baseline projection
  expect(analysis.marketShareProjections.baseline).to.be.an('object');
  expect(analysis.marketShareProjections.baseline).to.have.property('currentMarketShare');
  expect(analysis.marketShareProjections.baseline).to.have.property('projectedMarketShare');
  expect(analysis.marketShareProjections.baseline).to.have.property('assumptions');
  
  // Check projections for each strategy
  expect(analysis.marketShareProjections.byStrategy).to.be.an('object');
  
  for (const option of analysis.strategicPositioningOptions) {
    const strategyId = option.positioningStatement.toLowerCase().replace(/\s+/g, '-').substring(0, 20);
    expect(analysis.marketShareProjections.byStrategy).to.have.property(strategyId);
    
    const projection = analysis.marketShareProjections.byStrategy[strategyId];
    expect(projection).to.have.property('year1MarketShare');
    expect(projection).to.have.property('year3MarketShare');
    expect(projection).to.have.property('confidenceLevel');
    expect(projection).to.have.property('keyDrivers');
  }
});

Then('it should identify high-value acquisition or partnership targets', function() {
  const analysis = this.testContext.competitiveAnalysis;
  
  expect(analysis).to.have.property('acquisitionPartnershipTargets');
  expect(analysis.acquisitionPartnershipTargets).to.be.an('object');
  expect(analysis.acquisitionPartnershipTargets).to.have.property('acquisitionTargets');
  expect(analysis.acquisitionPartnershipTargets).to.have.property('partnershipOpportunities');
  
  // Check acquisition targets
  expect(analysis.acquisitionPartnershipTargets.acquisitionTargets).to.be.an('array');
  if (analysis.acquisitionPartnershipTargets.acquisitionTargets.length > 0) {
    for (const target of analysis.acquisitionPartnershipTargets.acquisitionTargets) {
      expect(target).to.have.property('companyProfile');
      expect(target).to.have.property('strategicFit');
      expect(target).to.have.property('valuationEstimate');
      expect(target).to.have.property('integrationComplexity');
      expect(target).to.have.property('riskFactors');
    }
  }
  
  // Check partnership opportunities
  expect(analysis.acquisitionPartnershipTargets.partnershipOpportunities).to.be.an('array');
  expect(analysis.acquisitionPartnershipTargets.partnershipOpportunities.length).to.be.at.least(2);
  
  for (const opportunity of analysis.acquisitionPartnershipTargets.partnershipOpportunities) {
    expect(opportunity).to.have.property('partnerType');
    expect(opportunity).to.have.property('potentialPartners');
    expect(opportunity).to.have.property('partnershipModel');
    expect(opportunity).to.have.property('valueCreation');
    expect(opportunity).to.have.property('implementationRequirements');
  }
});
