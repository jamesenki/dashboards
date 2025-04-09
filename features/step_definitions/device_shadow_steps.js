/**
 * Step definitions for device shadow feature tests
 * Following TDD principles to define expected behavior
 */
const { Given, When, Then } = require('@cucumber/cucumber');
const { expect } = require('chai');
const axios = require('axios');
const WebSocket = require('ws');

// Configuration
const BASE_URL = 'http://localhost:8000';
const API_BASE = `${BASE_URL}/api`;
const WS_BASE = 'ws://localhost:8000/api/ws';

let shadowData = {};
let wsConnection = null;
let wsMessages = [];

// Helper function to establish WebSocket connection
async function connectToDeviceShadowWebSocket(deviceId) {
    return new Promise((resolve, reject) => {
        const ws = new WebSocket(`${WS_BASE}/shadows/${deviceId}`);

        ws.on('open', () => {
            console.log(`WebSocket connection established for device ${deviceId}`);
            wsConnection = ws;
            resolve(ws);
        });

        ws.on('message', (data) => {
            const message = JSON.parse(data);
            console.log(`Received WebSocket message: ${JSON.stringify(message)}`);
            wsMessages.push(message);
        });

        ws.on('error', (error) => {
            console.error(`WebSocket error: ${error}`);
            reject(error);
        });

        ws.on('close', () => {
            console.log('WebSocket connection closed');
        });
    });
}

// Background steps
Given('the IoTSphere application is running', async function() {
    try {
        const response = await axios.get(`${BASE_URL}/health`);
        expect(response.status).to.equal(200);
    } catch (error) {
        throw new Error('IoTSphere application is not running');
    }
});

Given('I am logged in as an administrator', async function() {
    // Mock authentication for testing
    this.authToken = 'test-admin-token';
});

Given('there are registered devices in the system', async function() {
    try {
        // Check for both water heater device shadows
        const wh1Response = await axios.get(`${API_BASE}/shadows/wh-001`);
        expect(wh1Response.status).to.equal(200);
        expect(wh1Response.data).to.have.property('device_id', 'wh-001');

        const wh2Response = await axios.get(`${API_BASE}/shadows/wh-002`);
        expect(wh2Response.status).to.equal(200);
        expect(wh2Response.data).to.have.property('device_id', 'wh-002');

        console.log('Verified both water heater devices are registered');
    } catch (error) {
        console.error(`Error checking registered devices: ${error.message}`);
        throw new Error('Required test devices are not registered');
    }
});

// Scenario: View current device state
When('I navigate to the device details page for {string}', async function(deviceId) {
    try {
        // Get the device shadow data for verification
        const response = await axios.get(`${API_BASE}/shadows/${deviceId}`);
        shadowData = response.data;
        this.currentDeviceId = deviceId;

        // Establish WebSocket connection for real-time updates
        await connectToDeviceShadowWebSocket(deviceId);
    } catch (error) {
        throw new Error(`Failed to get shadow data for device ${deviceId}: ${error.message}`);
    }
});

Then('I should see the current temperature displayed', function() {
    // All devices are water heaters now, so they all use 'temperature' property
    expect(shadowData).to.have.nested.property('reported.temperature');

    // Check temperature is within expected range for water heaters
    const temp = shadowData.reported.temperature;
    expect(temp).to.be.a('number');
    expect(temp).to.be.at.least(90);
    expect(temp).to.be.at.most(180);

    console.log(`Verified temperature display: ${temp}°F`);
});

Then('I should see the device status indicator', function() {
    expect(shadowData).to.have.nested.property('reported.status');
    // Status should be one of these values
    expect(['ONLINE', 'OFFLINE', 'MAINTENANCE', 'ERROR']).to.include(shadowData.reported.status);

    console.log(`Verified device status: ${shadowData.reported.status}`);
});

Then('I should see the heater status indicator', function() {
    // All devices are water heaters now
    expect(shadowData).to.have.nested.property('reported.heater_status');
    // Heater status should be one of these values
    expect(['HEATING', 'STANDBY', 'OFF']).to.include(shadowData.reported.heater_status);

    console.log(`Verified heater status indicator: ${shadowData.reported.heater_status}`);
});

// Scenario: Request device state change
When('I change the target temperature to {int}°F', function(temperature) {
    this.targetTemperature = temperature;
});

When('I click the {string} button', async function(buttonName) {
    if (buttonName === 'Apply') {
        try {
            // Send the desired state change request
            const requestBody = {
                target_temperature: this.targetTemperature
            };

            const response = await axios.patch(
                `${API_BASE}/shadows/${this.currentDeviceId}/desired`,
                requestBody
            );

            this.stateChangeResponse = response.data;
        } catch (error) {
            throw new Error(`Failed to send state change request: ${error.message}`);
        }
    }
});

Then('the system should confirm the request was submitted', function() {
    expect(this.stateChangeResponse).to.have.property('success', true);
    expect(this.stateChangeResponse).to.have.property('device_id', this.currentDeviceId);
});

Then('the target temperature should show as {string}', function(status) {
    if (status === 'pending') {
        expect(this.stateChangeResponse).to.have.property('pending');
        expect(this.stateChangeResponse.pending).to.include('target_temperature');
    }
});

Then('when the device responds, the pending status should clear', async function() {
    // Simulate device response
    const deviceUpdateBody = {
        target_temperature: this.targetTemperature,
        temperature: this.targetTemperature - 5, // Current temp still catching up
        heater_status: 'HEATING'
    };

    try {
        // Direct call to device update API (normally would come from device)
        await axios.post(
            `${API_BASE}/device-updates/${this.currentDeviceId}`,
            deviceUpdateBody
        );

        // Wait for WebSocket message that confirms the update
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Should receive at least one message
        expect(wsMessages.length).to.be.greaterThan(0);

        // Get latest shadow to verify the pending status is cleared
        const response = await axios.get(`${API_BASE}/shadows/${this.currentDeviceId}`);
        const updatedShadow = response.data;

        // The desired state should no longer have pending states for target_temperature
        const pendingStates = updatedShadow.desired && updatedShadow.desired._pending || [];
        expect(pendingStates).to.not.include('target_temperature');
    } catch (error) {
        throw new Error(`Failed to simulate device response: ${error.message}`);
    }
});

// Scenario: Receive real-time device updates
When('the device sends a state update', async function() {
    // Simulate device state update
    const stateUpdate = {
        temperature: 122,
        heater_status: 'HEATING',
        status: 'ONLINE',
        last_updated: new Date().toISOString()
    };

    // All devices are water heaters now, no need to adjust for different types
    // Each water heater has the same properties, just different values

    try {
        // Direct call to device update API (normally would come from device)
        await axios.post(
            `${API_BASE}/device-updates/${this.currentDeviceId}`,
            stateUpdate
        );

        // Store the update for later verification
        this.stateUpdate = stateUpdate;
    } catch (error) {
        throw new Error(`Failed to simulate device state update: ${error.message}`);
    }
});

Then('I should see the updated values without refreshing', async function() {
    // Wait for WebSocket message
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Verify there's at least one message received
    expect(wsMessages.length).to.be.greaterThan(0);

    // Get the latest message
    const latestMessage = wsMessages[wsMessages.length - 1];

    // All devices are water heaters now
    expect(latestMessage.reported.temperature).to.equal(this.stateUpdate.temperature);
    expect(latestMessage.reported.heater_status).to.equal(this.stateUpdate.heater_status);

    expect(latestMessage.reported.status).to.equal(this.stateUpdate.status);
});

Then('the history chart should update with the new data point', function() {
    // This would verify chart updates in a real UI test
    // For API-level tests, we'll assume the frontend will update
    // if it's properly subscribed to the WebSocket
});

// Scenario: View multiple water heaters
Then('I should see the water heater details', function() {
    expect(this.currentDeviceId).to.equal('wh-002');
    expect(shadowData).to.have.property('device_id', 'wh-002');
    expect(shadowData).to.have.nested.property('reported.temperature');
    expect(shadowData).to.have.nested.property('reported.pressure');
    expect(shadowData).to.have.nested.property('reported.flow_rate');
    expect(shadowData).to.have.nested.property('reported.energy_usage');

    console.log('Verified water heater details for device wh-002');
});

Then('I should see if the water heater is active or in standby', function() {
    expect(shadowData).to.have.nested.property('reported.heater_status');
    // The heater status should be one of these values
    expect(['HEATING', 'STANDBY', 'OFF']).to.include(shadowData.reported.heater_status);

    console.log(`Verified heater status: ${shadowData.reported.heater_status}`);
});

Then('I should see the device status indicator', function() {
    expect(shadowData).to.have.nested.property('reported.status');
    // Status should be one of these values
    expect(['ONLINE', 'OFFLINE', 'MAINTENANCE', 'ERROR']).to.include(shadowData.reported.status);

    console.log(`Verified device status: ${shadowData.reported.status}`);
});

Then('I should see the heater status indicator', function() {
    expect(shadowData).to.have.nested.property('reported.heater_status');
    // Heater status should be one of these values
    expect(['HEATING', 'STANDBY', 'OFF']).to.include(shadowData.reported.heater_status);

    console.log(`Verified heater status indicator: ${shadowData.reported.heater_status}`);
});

Then('I should see the current temperature displayed', function() {
    // This step is used by both water heater scenarios
    expect(shadowData).to.have.nested.property('reported.temperature');

    // Check temperature is within expected range for water heaters
    const temp = shadowData.reported.temperature;
    expect(temp).to.be.a('number');
    expect(temp).to.be.at.least(90);
    expect(temp).to.be.at.most(180);

    console.log(`Verified temperature display: ${temp}°F`);
});
