/**
 * Step definitions for Device Management features
 * Following TDD principles - RED phase (defining expected behavior)
 */
const { Given, When, Then } = require('@cucumber/cucumber');
const { expect } = require('chai');

// Store context between steps
let deviceContext = {};
let managementContext = {};

/**
 * Device setup steps
 */
Given('a device with name {string} exists with status {string}', async function(deviceName, status) {
  // RED phase implementation
  console.log(`[RED] Setup: Device ${deviceName} exists with status ${status}`);
  deviceContext.name = deviceName;
  deviceContext.status = status;

  // In GREEN phase, we would:
  // - Set up test device with the specified name and status
  // - Add device to test database or mock system
});

/**
 * Navigation and action steps
 */
When('I navigate to the device management page', async function() {
  // RED phase implementation
  console.log('[RED] Action: Navigate to device management page');

  // In GREEN phase, we would:
  // await this.page.goto('http://localhost:8006/device-management');
  // await this.page.waitForSelector('.device-management-container');
});

When('I select {string}', async function(option) {
  // RED phase implementation
  console.log(`[RED] Action: Select option ${option}`);
  managementContext.selectedOption = option;

  // In GREEN phase, we would:
  // await this.page.click(`[data-action="${option.toLowerCase().replace(/\s/g, '-')}"]`);
});

When('I select the device with name {string}', async function(deviceName) {
  // RED phase implementation
  console.log(`[RED] Action: Select device with name ${deviceName}`);
  deviceContext.name = deviceName;

  // In GREEN phase, we would:
  // await this.page.click(`[data-device-name="${deviceName}"]`);
});

When('I enter the following device information:', async function(dataTable) {
  // RED phase implementation
  console.log('[RED] Action: Enter device information');
  const deviceInfo = {};

  dataTable.hashes().forEach(row => {
    deviceInfo[row.field] = row.value;
  });
  deviceContext.deviceInfo = deviceInfo;

  // In GREEN phase, we would:
  // for (const row of dataTable.hashes()) {
  //   await this.page.fill(`[name="${row.field}"]`, row.value);
  // }
});

When('I update the following information:', async function(dataTable) {
  // RED phase implementation
  console.log('[RED] Action: Update device information');
  const updateInfo = {};

  dataTable.hashes().forEach(row => {
    updateInfo[row.field] = row.value;
  });
  deviceContext.updateInfo = updateInfo;

  // In GREEN phase, we would:
  // for (const row of dataTable.hashes()) {
  //   await this.page.fill(`[name="${row.field}"]`, row.value);
  // }
});

When('I enter the following activation information:', async function(dataTable) {
  // RED phase implementation
  console.log('[RED] Action: Enter activation information');
  const activationInfo = {};

  dataTable.hashes().forEach(row => {
    activationInfo[row.field] = row.value;
  });
  deviceContext.activationInfo = activationInfo;

  // In GREEN phase, we would:
  // for (const row of dataTable.hashes()) {
  //   await this.page.fill(`[name="${row.field}"]`, row.value);
  // }
});

When('I submit the device registration form', async function() {
  // RED phase implementation
  console.log('[RED] Action: Submit device registration form');

  // In GREEN phase, we would:
  // await this.page.click('#submit-registration');
  // await this.page.waitForSelector('.registration-success', { timeout: 5000 });
});

When('I submit the activation form', async function() {
  // RED phase implementation
  console.log('[RED] Action: Submit activation form');

  // In GREEN phase, we would:
  // await this.page.click('#submit-activation');
  // await this.page.waitForSelector('.activation-success', { timeout: 5000 });
});

When('I save the changes', async function() {
  // RED phase implementation
  console.log('[RED] Action: Save changes');

  // In GREEN phase, we would:
  // await this.page.click('#save-changes');
  // await this.page.waitForSelector('.save-success', { timeout: 5000 });
});

When('I confirm the deactivation', async function() {
  // RED phase implementation
  console.log('[RED] Action: Confirm deactivation');

  // In GREEN phase, we would:
  // await this.page.click('#confirm-deactivation');
  // await this.page.waitForSelector('.deactivation-success', { timeout: 5000 });
});

When('I enter {string} in the confirmation field', async function(text) {
  // RED phase implementation
  console.log(`[RED] Action: Enter "${text}" in confirmation field`);

  // In GREEN phase, we would:
  // await this.page.fill('#confirmation-text', text);
});

When('I confirm the removal', async function() {
  // RED phase implementation
  console.log('[RED] Action: Confirm removal');

  // In GREEN phase, we would:
  // await this.page.click('#confirm-removal');
  // await this.page.waitForSelector('.removal-success', { timeout: 5000 });
});

/**
 * Assertion steps
 */
Then('the device should be successfully registered in the system', async function() {
  // RED phase implementation
  console.log('[RED] Verification: Device should be successfully registered');

  // In GREEN phase, we would:
  // await this.page.waitForSelector('.registration-success-message');
  // const successMsg = await this.page.$eval('.registration-success-message', el => el.textContent);
  // expect(successMsg).to.include('Device registered successfully');
});

Then('I should see the new device in the device list', async function() {
  // RED phase implementation
  console.log('[RED] Verification: Should see new device in list');

  // In GREEN phase, we would:
  // const deviceName = deviceContext.deviceInfo.name;
  // await this.page.waitForSelector(`[data-device-name="${deviceName}"]`);
  // const deviceElement = await this.page.$(`[data-device-name="${deviceName}"]`);
  // expect(deviceElement).to.not.be.null;
});

Then('the device should have status {string}', async function(status) {
  // RED phase implementation
  console.log(`[RED] Verification: Device should have status ${status}`);

  // In GREEN phase, we would:
  // const deviceName = deviceContext.name || deviceContext.deviceInfo.name;
  // const statusElement = await this.page.$(`[data-device-name="${deviceName}"] .device-status`);
  // const deviceStatus = await statusElement.textContent();
  // expect(deviceStatus.trim()).to.equal(status);
});

Then('the system should generate device credentials', async function() {
  // RED phase implementation
  console.log('[RED] Verification: System should generate device credentials');

  // In GREEN phase, we would:
  // await this.page.waitForSelector('.device-credentials');
  // const credentialsElement = await this.page.$('.device-credentials');
  // expect(credentialsElement).to.not.be.null;
});

Then('I should see the device connection information', async function() {
  // RED phase implementation
  console.log('[RED] Verification: Should see device connection information');

  // In GREEN phase, we would:
  // await this.page.waitForSelector('.connection-info');
  // const connectionInfoElement = await this.page.$('.connection-info');
  // expect(connectionInfoElement).to.not.be.null;
});

Then('the device details should be updated in the system', async function() {
  // RED phase implementation
  console.log('[RED] Verification: Device details should be updated in system');

  // In GREEN phase, we would:
  // await this.page.waitForSelector('.update-success-message');
  // const successMsg = await this.page.$eval('.update-success-message', el => el.textContent);
  // expect(successMsg).to.include('Device updated successfully');
});

Then('I should see the updated information in the device list', async function() {
  // RED phase implementation
  console.log('[RED] Verification: Should see updated information in device list');

  // In GREEN phase, we would:
  // const deviceName = deviceContext.updateInfo.name || deviceContext.name;
  // await this.page.waitForSelector(`[data-device-name="${deviceName}"]`);
  // const deviceElement = await this.page.$(`[data-device-name="${deviceName}"]`);
  // expect(deviceElement).to.not.be.null;
});

Then('the device should no longer receive commands', async function() {
  // RED phase implementation
  console.log('[RED] Verification: Device should no longer receive commands');

  // In GREEN phase, we would:
  // Verify command queue or test command sending to device
});

Then('the device should no longer report telemetry', async function() {
  // RED phase implementation
  console.log('[RED] Verification: Device should no longer report telemetry');

  // In GREEN phase, we would:
  // Verify telemetry ingestion or monitoring system
});

Then('the device should be permanently removed from the system', async function() {
  // RED phase implementation
  console.log('[RED] Verification: Device should be permanently removed from system');

  // In GREEN phase, we would:
  // Check database or API to verify device no longer exists
});

Then('I should not see the device in the device list', async function() {
  // RED phase implementation
  console.log('[RED] Verification: Should not see device in list');

  // In GREEN phase, we would:
  // const deviceName = deviceContext.name;
  // const deviceElements = await this.page.$$(`[data-device-name="${deviceName}"]`);
  // expect(deviceElements.length).to.equal(0);
});

Then('I should see a confirmation message', async function() {
  // RED phase implementation
  console.log('[RED] Verification: Should see confirmation message');

  // In GREEN phase, we would:
  // await this.page.waitForSelector('.confirmation-message');
  // const message = await this.page.$eval('.confirmation-message', el => el.textContent);
  // expect(message).to.include('Device has been removed');
});
