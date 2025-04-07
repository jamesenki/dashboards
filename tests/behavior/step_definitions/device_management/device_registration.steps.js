/**
 * Step definitions for device registration scenarios
 */
const { Given, When, Then } = require('@cucumber/cucumber');
// Using async import for Chai (ES module)
let expect;
import('chai').then(chai => {
  expect = chai.expect;
});

/**
 * Authentication and user context
 */
Given('a user with {string} role is authenticated', async function(role) {
  const user = await this.authenticateUser(role);
  expect(user).to.not.be.null;
  expect(user.roles).to.include(role);
});

/**
 * Device registration actions
 */
When('they register a new water heater with the following details:', async function(dataTable) {
  const deviceData = dataTable.rowsHash();

  // Transform data as needed for the repository
  const registrationData = {
    type: deviceData.type || 'water-heater',
    name: deviceData.name,
    manufacturer: deviceData.manufacturer,
    model: deviceData.model,
    serialNumber: deviceData.serialNumber,
    firmwareVersion: deviceData.firmwareVersion,
    metadata: {}
  };

  // Add water heater specific fields
  if (registrationData.type === 'water-heater') {
    if (deviceData.tankCapacity) {
      registrationData.tankCapacity = parseFloat(deviceData.tankCapacity);
    }

    if (deviceData.temperature) {
      registrationData.temperature = parseFloat(deviceData.temperature);
    }

    if (deviceData.mode) {
      registrationData.mode = deviceData.mode;
    }
  }

  try {
    const device = await this.registerDevice(registrationData);
    this.testContext.currentDevice = device;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('they register a new water heater with minimum required details:', async function(dataTable) {
  const deviceData = dataTable.rowsHash();

  // Create minimal registration data
  const registrationData = {
    type: deviceData.type || 'water-heater',
    manufacturer: deviceData.manufacturer,
    model: deviceData.model
  };

  try {
    const device = await this.registerDevice(registrationData);
    this.testContext.currentDevice = device;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('they attempt to register a new water heater with incomplete details:', async function(dataTable) {
  const deviceData = dataTable.rowsHash();

  try {
    const device = await this.registerDevice(deviceData);
    this.testContext.currentDevice = device;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('they register a new water heater on behalf of facility {string}:', async function(facilityName, dataTable) {
  const deviceData = dataTable.rowsHash();

  // Transform data as needed for the repository
  const registrationData = {
    type: deviceData.type || 'water-heater',
    name: deviceData.name,
    manufacturer: deviceData.manufacturer,
    model: deviceData.model,
    metadata: {
      facility: facilityName,
      location: deviceData.location
    }
  };

  try {
    const device = await this.registerDevice(registrationData);
    this.testContext.currentDevice = device;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('they register a new device with basic information:', async function(dataTable) {
  const deviceData = dataTable.rowsHash();

  // Transform data as needed for the repository
  const registrationData = {
    type: deviceData.type,
    name: deviceData.name,
    manufacturer: deviceData.manufacturer,
    model: deviceData.model,
    metadata: {
      protocol: deviceData.protocol
    }
  };

  try {
    const device = await this.registerDevice(registrationData);
    this.testContext.currentDevice = device;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

When('they register a new device with custom capabilities:', async function(dataTable) {
  const deviceData = dataTable.rowsHash();

  // Process capabilities from comma-separated string
  const capabilities = deviceData.capabilities ?
    deviceData.capabilities.split(',').map(cap => cap.trim()) : [];

  // Transform data as needed for the repository
  const registrationData = {
    type: deviceData.type,
    name: deviceData.name,
    manufacturer: deviceData.manufacturer,
    model: deviceData.model,
    capabilities: capabilities
  };

  try {
    const device = await this.registerDevice(registrationData);
    this.testContext.currentDevice = device;
  } catch (error) {
    this.testContext.errors.push(error);
  }
});

/**
 * Verification steps
 */
Then('the system should confirm successful registration', function() {
  expect(this.testContext.currentDevice).to.not.be.null;
  expect(this.testContext.currentDevice.id).to.be.a('string');
  expect(this.testContext.errors).to.be.empty;
});

Then('the water heater should appear in the device registry', async function() {
  const deviceId = this.testContext.currentDevice.id;
  const device = await this.deviceRepository.findDeviceById(deviceId);

  expect(device).to.not.be.null;
  expect(device.id).to.equal(deviceId);
});

Then('the water heater should have the {string} capability', async function(capability) {
  const deviceId = this.testContext.currentDevice.id;
  const capabilities = await this.deviceRepository.getDeviceCapabilities(deviceId);

  const capabilityIds = capabilities.map(cap => cap.id);
  expect(capabilityIds).to.include(capability);
});

Then('the water heater should be assigned a default name', function() {
  expect(this.testContext.currentDevice.name).to.be.a('string');
  expect(this.testContext.currentDevice.name).to.not.be.empty;
});

Then('the system should reject the registration', function() {
  expect(this.testContext.errors).to.not.be.empty;
  expect(this.testContext.currentDevice).to.be.undefined;
});

Then('the system should indicate {string} as the reason', function(reason) {
  const errorMessages = this.testContext.errors.map(err => err.message);
  const hasMatchingError = errorMessages.some(msg =>
    msg.toLowerCase().includes(reason.toLowerCase())
  );

  expect(hasMatchingError).to.be.true;
});

Then('the water heater should not appear in the device registry', async function() {
  // Since registration failed, we don't have a device ID
  // We can verify there are no devices matching the registration data
  const manufacturer = this.testContext.deviceRegistrationData?.manufacturer;

  if (manufacturer) {
    const devices = await this.deviceRepository.findDevices({ manufacturer });
    const matchingDevices = devices.filter(d =>
      d.model === this.testContext.deviceRegistrationData.model
    );

    expect(matchingDevices).to.be.empty;
  }
});

Then('the water heater should be associated with {string} facility', function(facilityName) {
  expect(this.testContext.currentDevice.metadata).to.not.be.null;
  expect(this.testContext.currentDevice.metadata.facility).to.equal(facilityName);
});

Then('the system should detect the device\'s capabilities', async function() {
  const deviceId = this.testContext.currentDevice.id;
  const capabilities = await this.deviceRepository.getDeviceCapabilities(deviceId);

  expect(capabilities).to.not.be.empty;
  expect(capabilities.length).to.be.at.least(1);
});

Then('assign at least the capabilities:', async function(dataTable) {
  const expectedCapabilities = dataTable.raw().map(row => row[0]);
  const deviceId = this.testContext.currentDevice.id;
  const capabilities = await this.deviceRepository.getDeviceCapabilities(deviceId);
  const capabilityIds = capabilities.map(cap => cap.id);

  for (const expectedCap of expectedCapabilities) {
    expect(capabilityIds).to.include(expectedCap);
  }
});

Then('the vending machine should appear in the device registry', async function() {
  const deviceId = this.testContext.currentDevice.id;
  const device = await this.deviceRepository.findDeviceById(deviceId);

  expect(device).to.not.be.null;
  expect(device.id).to.equal(deviceId);
  expect(device.type).to.equal('vending-machine');
});

Then('the device type should be correctly identified as {string}', function(deviceType) {
  expect(this.testContext.currentDevice.type).to.equal(deviceType);
});

Then('the robot should have exactly the specified capabilities', async function() {
  const deviceId = this.testContext.currentDevice.id;
  const capabilities = await this.deviceRepository.getDeviceCapabilities(deviceId);
  const capabilityIds = capabilities.map(cap => cap.id);

  // Get the expected capabilities from the registration data
  const expectedCapabilities = this.testContext.deviceRegistrationData.capabilities;

  expect(capabilityIds.length).to.equal(expectedCapabilities.length);
  for (const expectedCap of expectedCapabilities) {
    expect(capabilityIds).to.include(expectedCap);
  }
});

Then('the robot should appear in the device registry', async function() {
  const deviceId = this.testContext.currentDevice.id;
  const device = await this.deviceRepository.findDeviceById(deviceId);

  expect(device).to.not.be.null;
  expect(device.id).to.equal(deviceId);
  expect(device.type).to.equal('robot');
});
