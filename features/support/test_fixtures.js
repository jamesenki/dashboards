/**
 * Test Fixtures for BDD Tests
 * Provides consistent mock data for tests
 * Following TDD principles - define expected test data
 */

/**
 * Mock data for shadow device tests
 */
const shadowDevices = {
  "wh-test-001": {
    deviceId: "wh-test-001",
    reported: {
      temperature: 140,
      status: "online",
      mode: "standard",
      temperatureHistory: [
        { timestamp: Date.now() - 86400000, value: 138 },
        { timestamp: Date.now() - 43200000, value: 139 },
        { timestamp: Date.now(), value: 140 },
      ],
    },
    desired: {
      temperature: 140,
      mode: "standard",
    },
  },
  "wh-missing-shadow": null,
};

/**
 * Default test values
 */
const testDefaults = {
  timeouts: {
    ui: 500,
    network: 1500,
    reconnection: 2000
  },
  temperature: {
    default: 140,
    unit: "F",
    updates: [142, 143, 144]
  },
  websocket: {
    reconnectDelay: 500
  }
};

/**
 * Gets the mock shadow data for a specific device
 * @param {string} deviceId - The device ID to get shadow data for
 * @returns {Object|null} The shadow data or null if no shadow exists
 */
function getShadowData(deviceId) {
  return shadowDevices[deviceId] || null;
}

/**
 * Gets the reported temperature for a device
 * @param {string} deviceId - The device ID to get temperature for
 * @returns {number|null} The temperature or null if no shadow exists
 */
function getDeviceTemperature(deviceId) {
  const shadow = getShadowData(deviceId);
  return shadow?.reported?.temperature || null;
}

/**
 * Gets formatted temperature with unit for a device
 * @param {string} deviceId - The device ID
 * @param {string} unit - Optional unit override (F or C)
 * @returns {string} Formatted temperature string
 */
function getFormattedTemperature(deviceId, unit = "F") {
  const temp = getDeviceTemperature(deviceId);
  return temp ? `${temp}°${unit}` : "N/A";
}

// Export all fixtures and helper functions
module.exports = {
  shadowDevices,
  testDefaults,
  getShadowData,
  getDeviceTemperature,
  getFormattedTemperature
};
