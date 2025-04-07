/**
 * Step definitions for knowledge capture and integration scenarios
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
Given('a service technician resolves an unusual issue', async function() {
  // Create a device with an unusual issue
  const deviceId = 'knowledge-capture-device';
  
  // Register device if not exists
  let device = await this.deviceRepository.findDeviceById(deviceId);
  
  if (!device) {
    device = await this.deviceRepository.registerDevice({
      id: deviceId,
      type: 'water-heater',
      name: 'Knowledge Capture Test Device',
      manufacturer: 'Test Manufacturer',
      model: 'Test Model',
      serialNumber: 'KNOWLEDGE-1',
      firmwareVersion: '1.0.0'
    });
  }
  
  this.testContext.currentDeviceId = deviceId;
  
  // Create an unusual error code
  await this.deviceRepository.addDeviceErrorCode(deviceId, 'E-UNUSUAL-42');
  
  // Set up technician
  this.testContext.technician = {
    id: 'test-technician',
    name: 'Test Technician',
    role: 'SERVICE_TECHNICIAN',
    specialization: 'Water Heater Systems',
    experienceYears: 12
  };
  
  // Store resolution details
  this.testContext.unusualResolution = {
    errorCode: 'E-UNUSUAL-42',
    deviceId,
    deviceType: 'water-heater',
    issueDescription: 'Unit showing intermittent pressure drops despite normal water supply',
    rootCause: 'Debris accumulation in secondary pressure relief valve causing intermittent blockage',
    resolution: 'Dismantled secondary pressure relief valve and cleaned using ultrasonic bath, then reinstalled with new gasket',
    additionalInsights: 'This may not be visible in standard diagnostics as the primary pressure relief valve continues to function normally'
  };
});

Given('accumulated knowledge about device operations and maintenance', async function() {
  // Create a knowledge base with accumulated operations and maintenance knowledge
  this.testContext.knowledgeBase = {
    deviceTypes: ['water-heater', 'vending-machine', 'hvac'],
    issueCategories: [
      'routine-maintenance',
      'component-failure',
      'efficiency-degradation',
      'operational-error'
    ],
    knowledgeEntries: []
  };
  
  // Create sample knowledge entries
  const sampleEntries = [
    {
      id: 'knowledge-1',
      deviceType: 'water-heater',
      category: 'routine-maintenance',
      title: 'Annual flushing procedure',
      content: 'Standard annual flushing procedure for sediment removal',
      author: 'Maintenance Team',
      dateAdded: new Date(Date.now() - (180 * 24 * 60 * 60 * 1000)),
      appliedCount: 57,
      successRate: 0.98
    },
    {
      id: 'knowledge-2',
      deviceType: 'water-heater',
      category: 'component-failure',
      title: 'Heating element replacement',
      content: 'Procedure for diagnosing and replacing failed heating elements',
      author: 'Service Team',
      dateAdded: new Date(Date.now() - (120 * 24 * 60 * 60 * 1000)),
      appliedCount: 28,
      successRate: 0.95
    },
    {
      id: 'knowledge-3',
      deviceType: 'water-heater',
      category: 'efficiency-degradation',
      title: 'Scale build-up treatment',
      content: 'Procedure for treating scale build-up on heating elements',
      author: 'Service Team',
      dateAdded: new Date(Date.now() - (90 * 24 * 60 * 60 * 1000)),
      appliedCount: 36,
      successRate: 0.92
    },
    {
      id: 'knowledge-4',
      deviceType: 'vending-machine',
      category: 'operational-error',
      title: 'Coin mechanism cleaning',
      content: 'Procedure for cleaning jammed coin mechanisms',
      author: 'Maintenance Team',
      dateAdded: new Date(Date.now() - (60 * 24 * 60 * 60 * 1000)),
      appliedCount: 42,
      successRate: 0.88
    },
    {
      id: 'knowledge-5',
      deviceType: 'hvac',
      category: 'efficiency-degradation',
      title: 'Filter replacement schedule',
      content: 'Optimal filter replacement schedule based on usage patterns',
      author: 'Maintenance Team',
      dateAdded: new Date(Date.now() - (45 * 24 * 60 * 60 * 1000)),
      appliedCount: 65,
      successRate: 0.96
    }
  ];
  
  // Add entries to knowledge base
  for (const entry of sampleEntries) {
    await this.analyticsEngine.addKnowledgeEntry(entry);
    this.testContext.knowledgeBase.knowledgeEntries.push(entry);
  }
  
  // Verify knowledge base has entries
  const entries = await this.analyticsEngine.getKnowledgeEntries();
  expect(entries.length).to.equal(sampleEntries.length);
});

/**
 * User actions
 */
When('they document their solution in the system', async function() {
  const solution = this.testContext.unusualResolution;
  const technician = this.testContext.technician;
  
  try {
    // Document the solution
    const knowledgeEntry = {
      deviceType: solution.deviceType,
      errorCode: solution.errorCode,
      issueDescription: solution.issueDescription,
      resolution: solution.resolution,
      rootCause: solution.rootCause,
      additionalInsights: solution.additionalInsights,
      author: technician.name,
      dateAdded: new Date()
    };
    
    const result = await this.analyticsEngine.addTechnicianSolution(knowledgeEntry);
    this.testContext.knowledgeResult = result;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('the business intelligence system analyzes this knowledge', async function() {
  try {
    // Analyze accumulated knowledge
    const analysisResults = await this.analyticsEngine.analyzeKnowledgeBase();
    this.testContext.knowledgeAnalysis = analysisResults;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

/**
 * Verification steps
 */
Then('the knowledge management system should:', function(dataTable) {
  const expectedActions = dataTable.rowsHash();
  const result = this.testContext.knowledgeResult;
  
  expect(result).to.not.be.null;
  
  // Verify each expected action was performed
  for (const [action] of Object.entries(expectedActions)) {
    // Convert to camelCase
    const propertyName = action
      .toLowerCase()
      .replace(/[^a-z0-9]+(.)/g, (match, chr) => chr.toUpperCase());
    
    expect(result).to.have.property(propertyName);
    expect(result[propertyName]).to.be.an('object');
  }
});

Then('the new knowledge should be available for future similar issues', async function() {
  const result = this.testContext.knowledgeResult;
  const deviceId = this.testContext.currentDeviceId;
  
  // Verify knowledge can be retrieved
  const knowledgeEntry = await this.analyticsEngine.getKnowledgeEntryByErrorCode(result.extractKeyInsights.errorCode);
  expect(knowledgeEntry).to.not.be.null;
  
  // Now try to use it for a similar issue
  const similarDeviceId = 'similar-issue-device';
  
  // Register a similar device
  await this.deviceRepository.registerDevice({
    id: similarDeviceId,
    type: 'water-heater',
    name: 'Similar Issue Device',
    manufacturer: 'Test Manufacturer',
    model: 'Test Model',
    serialNumber: 'SIMILAR-1',
    firmwareVersion: '1.0.0'
  });
  
  // Add the same error code
  await this.deviceRepository.addDeviceErrorCode(similarDeviceId, result.extractKeyInsights.errorCode);
  
  // Request troubleshooting assistance
  const assistance = await this.analyticsEngine.getTroubleshootingAssistance(similarDeviceId);
  
  // Verify the new knowledge is utilized
  expect(assistance.solutions).to.be.an('array');
  const relevantSolution = assistance.solutions.find(s => s.source && s.source.includes(result.extractKeyInsights.id));
  expect(relevantSolution).to.not.be.undefined;
});

Then('other technicians should benefit from the captured expertise', async function() {
  const result = this.testContext.knowledgeResult;
  
  // Simulate technician searching for solutions
  const searchResults = await this.analyticsEngine.searchSolutions({
    deviceType: 'water-heater',
    searchTerm: 'pressure'
  });
  
  // Verify the new solution is in the search results
  expect(searchResults).to.be.an('array');
  const foundSolution = searchResults.find(s => s.id === result.extractKeyInsights.id);
  expect(foundSolution).to.not.be.undefined;
});

Then('it should identify opportunities for operational improvements such as:', function(dataTable) {
  const expectedOpportunities = dataTable.rowsHash();
  const analysis = this.testContext.knowledgeAnalysis;
  
  expect(analysis).to.have.property('improvementOpportunities');
  expect(analysis.improvementOpportunities).to.be.an('object');
  
  // Check each expected opportunity type
  for (const [opportunity] of Object.entries(expectedOpportunities)) {
    // Convert to camelCase
    const propertyName = opportunity
      .toLowerCase()
      .replace(/[^a-z0-9]+(.)/g, (match, chr) => chr.toUpperCase());
    
    expect(analysis.improvementOpportunities).to.have.property(propertyName);
    expect(analysis.improvementOpportunities[propertyName]).to.be.an('array');
    expect(analysis.improvementOpportunities[propertyName].length).to.be.greaterThan(0);
  }
});

Then('each improvement should include an estimated impact', function() {
  const analysis = this.testContext.knowledgeAnalysis;
  
  // Check all improvement types
  for (const improvements of Object.values(analysis.improvementOpportunities)) {
    // Each improvement should have impact information
    for (const improvement of improvements) {
      expect(improvement).to.have.property('estimatedImpact');
      expect(improvement.estimatedImpact).to.be.an('object');
      expect(improvement.estimatedImpact).to.have.property('operational');
      expect(improvement.estimatedImpact).to.have.property('financial');
    }
  }
});

Then('implementation guidance should be provided', function() {
  const analysis = this.testContext.knowledgeAnalysis;
  
  expect(analysis).to.have.property('implementationGuidance');
  expect(analysis.implementationGuidance).to.be.an('object');
  
  // Should have guidance for each improvement type
  for (const improvementType of Object.keys(analysis.improvementOpportunities)) {
    expect(analysis.implementationGuidance).to.have.property(improvementType);
    expect(analysis.implementationGuidance[improvementType]).to.be.an('object');
    expect(analysis.implementationGuidance[improvementType]).to.have.property('steps');
    expect(analysis.implementationGuidance[improvementType].steps).to.be.an('array');
  }
});

Then('training materials should be automatically suggested', function() {
  const analysis = this.testContext.knowledgeAnalysis;
  
  expect(analysis).to.have.property('suggestedTraining');
  expect(analysis.suggestedTraining).to.be.an('array');
  expect(analysis.suggestedTraining.length).to.be.greaterThan(0);
  
  // Each training suggestion should include essential information
  for (const training of analysis.suggestedTraining) {
    expect(training).to.have.property('title');
    expect(training).to.have.property('targetAudience');
    expect(training).to.have.property('content');
    expect(training).to.have.property('estimatedDuration');
  }
});
