/**
 * Extended step definitions for device command execution scenarios
 */
const { When, Then } = require('@cucumber/cucumber');
// Using async import for Chai (ES module)
let expect;
import('chai').then(chai => {
  expect = chai.expect;
});

/**
 * Handle user sending a command to a device
 */
When('the user sends a {string} command', function(commandType) {
  // Get the current device
  const deviceId = this.testContext.currentDeviceId || 'water-heater-123';
  
  // Create a command object based on the type
  let command = {
    type: commandType,
    deviceId: deviceId,
    timestamp: new Date().toISOString(),
    status: 'PENDING'
  };
  
  // Add command-specific parameters
  switch(commandType) {
    case 'setMode':
      command.parameters = {
        mode: 'STANDARD' // Default value, will be overridden if specified
      };
      break;
    case 'setTemperature':
      command.parameters = {
        temperature: 120 // Default value in Fahrenheit
      };
      break;
    case 'startHeating':
      command.parameters = {
        duration: 60 // Default duration in minutes
      };
      break;
    default:
      command.parameters = {};
  }
  
  // Store the command for later steps
  this.testContext.currentCommand = command;
  
  return 'pending'; // Mark as pending since this is just a stub implementation
});

/**
 * Handle device coming back online
 */
Then('when the device comes online', function() {
  // Get the current device and command
  const deviceId = this.testContext.currentDeviceId || 'water-heater-123';
  const command = this.testContext.currentCommand;
  
  if (!command) {
    throw new Error('No command has been created to execute when device comes online');
  }
  
  // Update device status to online
  this.deviceRepository.updateDeviceStatus(deviceId, 'ONLINE');
  
  // Simulate the command being sent to the device
  command.status = 'SENT';
  command.sentTimestamp = new Date().toISOString();
  
  // Store updated command
  this.testContext.currentCommand = command;
  
  return 'pending'; // Mark as pending since this is just a stub implementation
});
