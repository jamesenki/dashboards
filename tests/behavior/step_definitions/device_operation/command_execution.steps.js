/**
 * Step definitions for device command execution scenarios
 */
const { Given, When, Then } = require('@cucumber/cucumber');
// Using async import for Chai (ES module)
let expect;
import('chai').then(chai => {
  expect = chai.expect;
});

/**
 * Setup and device preparations
 */
Given('the device has the {string} capability', async function(capability) {
  const deviceId = this.testContext.currentDeviceId;
  
  // Check if device exists
  const device = await this.deviceRepository.findDeviceById(deviceId);
  expect(device).to.not.be.null;
  
  // Add capability if not present
  const capabilities = await this.deviceRepository.getDeviceCapabilities(deviceId);
  const hasCapability = capabilities.some(cap => cap.id === capability);
  
  if (!hasCapability) {
    await this.deviceRepository.addDeviceCapability(deviceId, capability);
    
    // Verify capability was added
    const updatedCapabilities = await this.deviceRepository.getDeviceCapabilities(deviceId);
    const nowHasCapability = updatedCapabilities.some(cap => cap.id === capability);
    expect(nowHasCapability).to.be.true;
  }
});

Given('the device is online', async function() {
  const deviceId = this.testContext.currentDeviceId;
  
  // Set device to online
  await this.deviceRepository.updateDeviceConnectionState(deviceId, 'ONLINE');
  
  // Verify device is online
  const device = await this.deviceRepository.findDeviceById(deviceId);
  expect(device.connectionState).to.equal('ONLINE');
});

Given('the device is offline', async function() {
  const deviceId = this.testContext.currentDeviceId;
  
  // Set device to offline
  await this.deviceRepository.updateDeviceConnectionState(deviceId, 'OFFLINE');
  
  // Verify device is offline
  const device = await this.deviceRepository.findDeviceById(deviceId);
  expect(device.connectionState).to.equal('OFFLINE');
});

Given('the device supports diagnostic commands', async function() {
  const deviceId = this.testContext.currentDeviceId;
  
  // Add diagnostic capabilities
  const diagnosticCapabilities = ['DIAGNOSTICS', 'SELF_TEST'];
  
  for (const capability of diagnosticCapabilities) {
    await this.deviceRepository.addDeviceCapability(deviceId, capability);
  }
  
  // Verify capabilities were added
  const updatedCapabilities = await this.deviceRepository.getDeviceCapabilities(deviceId);
  for (const capability of diagnosticCapabilities) {
    const hasCapability = updatedCapabilities.some(cap => cap.id === capability);
    expect(hasCapability).to.be.true;
  }
});

Given('the following registered devices with {string} capability:', async function(capability, dataTable) {
  const devices = dataTable.hashes();
  this.testContext.devicesWithCapability = [];
  
  for (const device of devices) {
    // Check if device exists
    let existingDevice = await this.deviceRepository.findDeviceById(device.deviceId);
    
    if (!existingDevice) {
      // Register device
      existingDevice = await this.deviceRepository.registerDevice({
        id: device.deviceId,
        type: device.type,
        name: `Test ${device.type}`,
        manufacturer: 'Test Manufacturer',
        model: 'Test Model',
        serialNumber: device.deviceId,
        firmwareVersion: '1.0.0'
      });
    }
    
    // Add capability if not present
    const capabilities = await this.deviceRepository.getDeviceCapabilities(device.deviceId);
    const hasCapability = capabilities.some(cap => cap.id === capability);
    
    if (!hasCapability) {
      await this.deviceRepository.addDeviceCapability(device.deviceId, capability);
    }
    
    // Set device to online
    await this.deviceRepository.updateDeviceConnectionState(device.deviceId, 'ONLINE');
    
    this.testContext.devicesWithCapability.push(existingDevice);
  }
  
  expect(this.testContext.devicesWithCapability.length).to.equal(devices.length);
});

Given('the devices have interdependent operations', async function() {
  const devices = this.testContext.devicesWithCapability || this.testContext.diverseDevices;
  
  if (!devices || devices.length < 2) {
    throw new Error('Need at least 2 devices to establish interdependencies');
  }
  
  // Create mock interdependency data
  this.testContext.deviceDependencies = [];
  
  for (let i = 0; i < devices.length - 1; i++) {
    const dependency = {
      primaryDeviceId: devices[i].id,
      dependentDeviceId: devices[i+1].id,
      dependencyType: 'OPERATIONAL',
      relationship: 'SEQUENTIAL',
      description: `Device ${devices[i].id} operations affect ${devices[i+1].id}`
    };
    
    this.testContext.deviceDependencies.push(dependency);
  }
  
  // Add cyclic dependency to make it interesting
  const cyclicDependency = {
    primaryDeviceId: devices[devices.length - 1].id,
    dependentDeviceId: devices[0].id,
    dependencyType: 'RESOURCE',
    relationship: 'SHARED',
    description: 'Shared resource dependency'
  };
  
  this.testContext.deviceDependencies.push(cyclicDependency);
});

Given('a facility with established operational patterns', async function() {
  const devices = this.testContext.devicesWithCapability || this.testContext.diverseDevices;
  
  if (!devices || devices.length === 0) {
    throw new Error('Need devices to establish operational patterns');
  }
  
  // Create command history for the past 30 days
  const now = new Date();
  const startDate = new Date(now);
  startDate.setDate(now.getDate() - 30);
  
  this.testContext.commandHistory = [];
  
  // Create patterns:
  // 1. Morning temperature adjustment (7-8am weekdays)
  // 2. Evening mode change (6-7pm weekdays)
  // 3. Weekend energy saving mode (Fridays 5-6pm)
  
  // Generate days
  for (let i = 30; i >= 0; i--) {
    const day = new Date(now);
    day.setDate(now.getDate() - i);
    const dayOfWeek = day.getDay(); // 0 = Sunday, 6 = Saturday
    const isWeekday = dayOfWeek >= 1 && dayOfWeek <= 5;
    const isFriday = dayOfWeek === 5;
    
    // Morning pattern on weekdays
    if (isWeekday) {
      const morningTime = new Date(day);
      morningTime.setHours(7, Math.floor(Math.random() * 60), 0);
      
      for (const device of devices) {
        if (device.type === 'water-heater') {
          const command = {
            deviceId: device.id,
            commandType: 'setTemperature',
            parameters: { temperature: 120 + (Math.random() * 5 - 2.5) },
            timestamp: morningTime,
            status: 'COMPLETED',
            user: {
              id: 'scheduled-system',
              role: 'SYSTEM'
            }
          };
          
          this.testContext.commandHistory.push(command);
        } else if (device.type === 'hvac') {
          const command = {
            deviceId: device.id,
            commandType: 'setTemperature',
            parameters: { temperature: 68 + (Math.random() * 3 - 1.5) },
            timestamp: morningTime,
            status: 'COMPLETED',
            user: {
              id: 'scheduled-system',
              role: 'SYSTEM'
            }
          };
          
          this.testContext.commandHistory.push(command);
        }
      }
      
      // Evening pattern on weekdays
      const eveningTime = new Date(day);
      eveningTime.setHours(18, Math.floor(Math.random() * 60), 0);
      
      for (const device of devices) {
        if (device.type === 'water-heater' || device.type === 'hvac') {
          const command = {
            deviceId: device.id,
            commandType: 'setMode',
            parameters: { mode: 'ECO' },
            timestamp: eveningTime,
            status: 'COMPLETED',
            user: {
              id: 'scheduled-system',
              role: 'SYSTEM'
            }
          };
          
          this.testContext.commandHistory.push(command);
        }
      }
    }
    
    // Friday pattern
    if (isFriday) {
      const fridayTime = new Date(day);
      fridayTime.setHours(17, Math.floor(Math.random() * 60), 0);
      
      for (const device of devices) {
        const command = {
          deviceId: device.id,
          commandType: 'setMode',
          parameters: { mode: 'VACATION' },
          timestamp: fridayTime,
          status: 'COMPLETED',
          user: {
            id: 'facility-manager',
            role: 'FACILITY_MANAGER'
          }
        };
        
        this.testContext.commandHistory.push(command);
      }
    }
  }
  
  // Store the command history
  for (const command of this.testContext.commandHistory) {
    await this.deviceRepository.addCommandToHistory(command);
  }
  
  // Verify history was stored
  const storedHistory = await this.deviceRepository.getCommandHistory(devices[0].id, 30);
  expect(storedHistory.length).to.be.greaterThan(0);
});

Given('command history for the past {int} days', function(days) {
  // Already covered by the previous step
  expect(this.testContext.commandHistory.length).to.be.greaterThan(0);
  
  // Count commands in the specified period
  const now = new Date();
  const cutoffDate = new Date(now);
  cutoffDate.setDate(now.getDate() - days);
  
  const commandsInPeriod = this.testContext.commandHistory.filter(
    cmd => cmd.timestamp >= cutoffDate
  );
  
  expect(commandsInPeriod.length).to.be.greaterThan(0);
});

/**
 * Command actions
 */
When('a user with {string} role sends a {string} command', async function(role, commandType) {
  // Set up user with specified role
  const user = await this.userService.getUserByRole(role);
  expect(user).to.not.be.null;
  
  const deviceId = this.testContext.currentDeviceId;
  
  // Prepare command without parameters yet
  this.testContext.pendingCommand = {
    deviceId,
    commandType,
    parameters: {},
    user: {
      id: user.id,
      role
    }
  };
});

When('provides a parameter {string} with value {string}', async function(paramName, paramValue) {
  // Add parameter to pending command
  let parsedValue = paramValue;
  
  // Try to convert numeric values
  if (!isNaN(paramValue)) {
    parsedValue = Number(paramValue);
  }
  
  this.testContext.pendingCommand.parameters[paramName] = parsedValue;
  
  // Execute the command
  try {
    const commandResult = await this.deviceRepository.executeCommand(this.testContext.pendingCommand);
    this.testContext.commandResult = commandResult;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('selects the {string} mode', async function(mode) {
  const command = this.testContext.pendingCommand;
  command.parameters.mode = mode;
  
  // Execute the command
  try {
    const commandResult = await this.deviceRepository.executeCommand(command);
    this.testContext.commandResult = commandResult;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('the command completes', async function() {
  const commandId = this.testContext.commandResult.id;
  
  // Wait for command to complete (mock will complete immediately)
  try {
    const result = await this.deviceRepository.waitForCommandCompletion(commandId);
    this.testContext.completedCommand = result;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('the device comes online', async function() {
  const deviceId = this.testContext.currentDeviceId;
  
  // Set device to online
  await this.deviceRepository.updateDeviceConnectionState(deviceId, 'ONLINE');
  
  // Process any queued commands
  try {
    const result = await this.deviceRepository.processQueuedCommands(deviceId);
    this.testContext.queuedCommandResults = result;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('a user sends a batch {string} command', async function(commandType) {
  const devices = this.testContext.devicesWithCapability;
  
  // Prepare batch command
  this.testContext.batchCommand = {
    commandType,
    parameters: {},
    deviceIds: devices.map(d => d.id),
    user: {
      id: 'test-user',
      role: 'FACILITY_MANAGER'
    }
  };
});

When('a user requests to optimize system operation', async function() {
  const devices = this.testContext.devicesWithCapability || this.testContext.diverseDevices;
  const deviceIds = devices.map(d => d.id);
  
  try {
    const optimizationResult = await this.analyticsEngine.optimizeSystemOperation(deviceIds);
    this.testContext.optimizationResult = optimizationResult;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('the system analyzes command patterns', async function() {
  const devices = this.testContext.devicesWithCapability || this.testContext.diverseDevices;
  const deviceIds = devices.map(d => d.id);
  
  try {
    const patternAnalysis = await this.analyticsEngine.analyzeCommandPatterns(deviceIds, 30);
    this.testContext.patternAnalysis = patternAnalysis;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

/**
 * Verification steps
 */
Then('the system should successfully dispatch the command', function() {
  const commandResult = this.testContext.commandResult;
  
  expect(commandResult).to.not.be.undefined;
  expect(commandResult).to.have.property('id');
  expect(commandResult).to.have.property('status');
});

Then('the command status should be {string}', function(expectedStatus) {
  const commandResult = this.testContext.commandResult;
  
  expect(commandResult.status).to.equal(expectedStatus);
});

Then('when the command completes', function() {
  // This is handled by the When step with the same name
});

Then('the command status should change to {string}', function(expectedStatus) {
  const completedCommand = this.testContext.completedCommand;
  
  expect(completedCommand).to.not.be.undefined;
  expect(completedCommand.status).to.equal(expectedStatus);
});

Then('the device state should reflect the new temperature setting', async function() {
  const deviceId = this.testContext.currentDeviceId;
  const pendingCommand = this.testContext.pendingCommand;
  
  // Get current device state
  const deviceState = await this.deviceRepository.getDeviceState(deviceId);
  
  expect(deviceState).to.have.property('temperature');
  expect(deviceState.temperature).to.equal(pendingCommand.parameters.temperature);
});

Then('the command execution should be logged', async function() {
  const deviceId = this.testContext.currentDeviceId;
  const commandId = this.testContext.commandResult.id;
  
  // Check command history
  const history = await this.deviceRepository.getCommandHistory(deviceId, 1);
  
  expect(history.length).to.be.greaterThan(0);
  const loggedCommand = history.find(cmd => cmd.id === commandId);
  expect(loggedCommand).to.not.be.undefined;
});

Then('the device state should be updated to reflect the new mode', async function() {
  const deviceId = this.testContext.currentDeviceId;
  const pendingCommand = this.testContext.pendingCommand;
  
  // Get current device state
  const deviceState = await this.deviceRepository.getDeviceState(deviceId);
  
  expect(deviceState).to.have.property('mode');
  expect(deviceState.mode).to.equal(pendingCommand.parameters.mode);
});

Then('the user should receive confirmation of the mode change', function() {
  const commandResult = this.testContext.commandResult;
  
  expect(commandResult).to.have.property('confirmation');
  expect(commandResult.confirmation).to.be.true;
});

Then('the expected energy savings should be displayed', function() {
  const commandResult = this.testContext.commandResult;
  
  expect(commandResult).to.have.property('energySavings');
  expect(commandResult.energySavings).to.be.an('object');
  expect(commandResult.energySavings).to.have.property('percentage');
  expect(commandResult.energySavings).to.have.property('estimated');
});

Then('the system should queue the command for later execution', function() {
  const commandResult = this.testContext.commandResult;
  
  expect(commandResult.status).to.equal('QUEUED');
  expect(commandResult).to.have.property('queuePosition');
});

Then('the user should be notified that the device is offline', function() {
  const commandResult = this.testContext.commandResult;
  
  expect(commandResult).to.have.property('notification');
  expect(commandResult.notification).to.include('offline');
});

Then('the system should attempt to execute the queued command', function() {
  const queuedResults = this.testContext.queuedCommandResults;
  
  expect(queuedResults).to.be.an('array');
  expect(queuedResults.length).to.be.greaterThan(0);
  
  // At least one command should have been processed
  const processedCommand = queuedResults.find(cmd => 
    cmd.status === 'COMPLETED' || cmd.status === 'FAILED'
  );
  
  expect(processedCommand).to.not.be.undefined;
});

Then('the diagnostic results should be returned', function() {
  const commandResult = this.testContext.commandResult;
  
  expect(commandResult).to.have.property('diagnosticResults');
  expect(commandResult.diagnosticResults).to.be.an('object');
});

Then('the results should include component status information', function() {
  const commandResult = this.testContext.commandResult;
  
  expect(commandResult.diagnosticResults).to.have.property('components');
  expect(commandResult.diagnosticResults.components).to.be.an('array');
  expect(commandResult.diagnosticResults.components.length).to.be.greaterThan(0);
  
  // Each component should have a status
  for (const component of commandResult.diagnosticResults.components) {
    expect(component).to.have.property('name');
    expect(component).to.have.property('status');
    expect(component).to.have.property('readings');
  }
});

Then('the diagnostic execution should be logged in the maintenance record', async function() {
  const deviceId = this.testContext.currentDeviceId;
  
  // Check maintenance records
  const records = await this.analyticsEngine.getMaintenanceRecords(deviceId);
  
  expect(records.length).to.be.greaterThan(0);
  
  // Find diagnostic record
  const diagnosticRecord = records.find(r => 
    r.type === 'DIAGNOSTIC' || r.description.includes('diagnostic')
  );
  
  expect(diagnosticRecord).to.not.be.undefined;
});

Then('the system should adapt the command for each device type', function() {
  const batchCommand = this.testContext.batchCommand;
  
  // Add temperature parameter to complete the batch command
  batchCommand.parameters.temperature = 68;
  
  // Mock method that checks for command adaptation
  const adaptationCheck = this.deviceRepository.checkCommandAdaptation(batchCommand);
  expect(adaptationCheck.adapted).to.be.true;
});

Then('it should apply appropriate unit conversions', function() {
  const batchCommand = this.testContext.batchCommand;
  
  // Mock method that checks for unit conversion
  const conversionCheck = this.deviceRepository.checkUnitConversion(batchCommand);
  expect(conversionCheck.converted).to.be.true;
});

Then('each device should receive a properly formatted command', async function() {
  const batchCommand = this.testContext.batchCommand;
  
  try {
    // Execute the batch command
    const batchResult = await this.deviceRepository.executeBatchCommand(batchCommand);
    this.testContext.batchResult = batchResult;
    
    expect(batchResult).to.have.property('results');
    expect(batchResult.results).to.be.an('array');
    expect(batchResult.results.length).to.equal(batchCommand.deviceIds.length);
    
    // Each result should have a valid command format
    for (const result of batchResult.results) {
      expect(result).to.have.property('deviceId');
      expect(result).to.have.property('status');
      expect(result).to.have.property('adaptedCommand');
    }
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

Then('the commands should be executed in parallel', function() {
  const batchResult = this.testContext.batchResult;
  
  expect(batchResult).to.have.property('executionStats');
  expect(batchResult.executionStats).to.have.property('parallelExecution');
  expect(batchResult.executionStats.parallelExecution).to.be.true;
});

Then('the system should report individual command status for each device', function() {
  const batchResult = this.testContext.batchResult;
  
  // Each device should have its own status
  for (const result of batchResult.results) {
    expect(result).to.have.property('status');
    expect(['COMPLETED', 'FAILED', 'QUEUED']).to.include(result.status);
  }
});

Then('the AI should analyze the operational dependencies', function() {
  const result = this.testContext.optimizationResult;
  
  expect(result).to.have.property('dependencyAnalysis');
  expect(result.dependencyAnalysis).to.be.an('object');
  expect(result.dependencyAnalysis).to.have.property('dependencies');
  expect(result.dependencyAnalysis.dependencies).to.be.an('array');
  expect(result.dependencyAnalysis.dependencies.length).to.be.greaterThan(0);
});

Then('it should generate an optimal command sequence', function() {
  const result = this.testContext.optimizationResult;
  
  expect(result).to.have.property('commandSequence');
  expect(result.commandSequence).to.be.an('array');
  expect(result.commandSequence.length).to.be.greaterThan(0);
  
  // Sequence should have appropriate ordering
  for (const command of result.commandSequence) {
    expect(command).to.have.property('deviceId');
    expect(command).to.have.property('commandType');
    expect(command).to.have.property('parameters');
    expect(command).to.have.property('sequencePosition');
  }
});

Then('the sequence should minimize energy consumption', function() {
  const result = this.testContext.optimizationResult;
  
  expect(result).to.have.property('projectedOutcomes');
  expect(result.projectedOutcomes).to.be.an('object');
  expect(result.projectedOutcomes).to.have.property('energyConsumption');
  expect(result.projectedOutcomes.energyConsumption).to.have.property('optimizedConsumption');
  expect(result.projectedOutcomes.energyConsumption).to.have.property('baselineConsumption');
  expect(result.projectedOutcomes.energyConsumption.optimizedConsumption).to.be.lessThan(
    result.projectedOutcomes.energyConsumption.baselineConsumption
  );
});

Then('the sequence should maintain required performance levels', function() {
  const result = this.testContext.optimizationResult;
  
  expect(result.projectedOutcomes).to.have.property('performance');
  expect(result.projectedOutcomes.performance).to.have.property('meetsRequirements');
  expect(result.projectedOutcomes.performance.meetsRequirements).to.be.true;
});

Then('the system should execute the commands in the recommended sequence', async function() {
  const result = this.testContext.optimizationResult;
  
  try {
    // Execute the optimized sequence
    const executionResult = await this.deviceRepository.executeCommandSequence(
      result.commandSequence
    );
    
    this.testContext.sequenceExecutionResult = executionResult;
    
    expect(executionResult).to.have.property('completedCommands');
    expect(executionResult.completedCommands).to.be.an('array');
    expect(executionResult.completedCommands.length).to.equal(result.commandSequence.length);
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

Then('it should monitor the effects and adjust if necessary', function() {
  const executionResult = this.testContext.sequenceExecutionResult;
  
  expect(executionResult).to.have.property('adjustments');
  expect(executionResult.adjustments).to.be.an('array');
});

Then('it should identify recurring command sequences', function() {
  const analysis = this.testContext.patternAnalysis;
  
  expect(analysis).to.have.property('recurringSequences');
  expect(analysis.recurringSequences).to.be.an('array');
  expect(analysis.recurringSequences.length).to.be.greaterThan(0);
});

Then('it should suggest automated routines based on:', function(dataTable) {
  const patterns = dataTable.rowsHash();
  const analysis = this.testContext.patternAnalysis;
  
  expect(analysis).to.have.property('suggestedRoutines');
  expect(analysis.suggestedRoutines).to.be.an('array');
  expect(analysis.suggestedRoutines.length).to.be.greaterThan(0);
  
  // Check that routines are based on the expected patterns
  for (const [pattern] of Object.entries(patterns)) {
    // Convert pattern to property name
    let propertyName;
    
    switch(pattern) {
      case 'timeOfDay':
        propertyName = 'timeOfDayRoutines';
        break;
      case 'dayOfWeek':
        propertyName = 'dayOfWeekRoutines';
        break;
      case 'externalConditions':
        propertyName = 'conditionBasedRoutines';
        break;
      case 'userRoles':
        propertyName = 'roleBasedRoutines';
        break;
      default:
        propertyName = pattern;
    }
    
    expect(analysis).to.have.property(propertyName);
    expect(analysis[propertyName]).to.be.an('array');
    expect(analysis[propertyName].length).to.be.greaterThan(0);
  }
});

Then('for each suggested routine, it should provide:', function(dataTable) {
  const expectedFields = dataTable.rowsHash();
  const analysis = this.testContext.patternAnalysis;
  
  // Check each routine has all expected fields
  for (const routine of analysis.suggestedRoutines) {
    for (const [field] of Object.entries(expectedFields)) {
      expect(routine).to.have.property(field);
    }
  }
});
