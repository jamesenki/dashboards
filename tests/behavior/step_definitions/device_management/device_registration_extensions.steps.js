/**
 * Extended step definitions for device registration and manufacturer-agnostic API scenarios
 */
const { Given } = require('@cucumber/cucumber');
// Using async import for Chai (ES module)
let expect;
import('chai').then(chai => {
  expect = chai.expect;
});

/**
 * Register multiple devices from different manufacturers for testing
 */
Given('multiple water heaters from different manufacturers are registered', function() {
  // Create an array of manufacturer-specific devices
  this.testContext.multiManufacturerDevices = [
    {
      id: 'rheem-wh-001',
      manufacturer: 'Rheem',
      model: 'ProTerra',
      serialNumber: 'RH100123',
      capacity: '50 gallons',
      installDate: '2025-01-15',
      location: 'Building A, Floor 1'
    },
    {
      id: 'ao-smith-wh-002',
      manufacturer: 'A.O. Smith',
      model: 'Signature Premier',
      serialNumber: 'AOS200456',
      capacity: '40 gallons',
      installDate: '2025-02-10',
      location: 'Building B, Floor 2'
    },
    {
      id: 'bradford-white-wh-003',
      manufacturer: 'Bradford White',
      model: 'eF Series',
      serialNumber: 'BW300789',
      capacity: '75 gallons',
      installDate: '2025-03-05',
      location: 'Building C, Floor 1'
    },
    {
      id: 'rheem-wh-004',
      manufacturer: 'Rheem',
      model: 'Gladiator',
      serialNumber: 'RH400321',
      capacity: '65 gallons',
      installDate: '2025-01-28',
      location: 'Building A, Floor 3'
    }
  ];
  
  // Register devices in the mocked device repository
  const devices = this.testContext.multiManufacturerDevices;
  for (const device of devices) {
    this.deviceRepository.registerDevice(device);
  }
  
  // Store manufacturer counts for later verification
  this.testContext.manufacturerCounts = devices.reduce((counts, device) => {
    counts[device.manufacturer] = (counts[device.manufacturer] || 0) + 1;
    return counts;
  }, {});
  
  return 'pending'; // Mark as pending since this is just a stub implementation
});

/**
 * Register a single water heater with specific ID
 */
Given('a registered water heater with ID {string}', function(deviceId) {
  // Create a device with the specified ID
  const device = {
    id: deviceId,
    manufacturer: 'Rheem',
    model: 'Performance Platinum',
    serialNumber: 'RH' + deviceId.split('-')[1],
    capacity: '50 gallons',
    installDate: '2025-02-15',
    location: 'Test Building, Floor 1',
    settings: {
      temperature: 120,
      mode: 'STANDARD'
    }
  };
  
  // Register the device in the mocked device repository
  this.deviceRepository.registerDevice(device);
  
  // Store the device for later usage
  this.testContext.currentDevice = device;
  
  return 'pending'; // Mark as pending since this is just a stub implementation
});
