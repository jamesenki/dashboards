/**
 * Shadow Document Helper for Integration Tests
 *
 * This module provides functions to set up and tear down shadow document test data
 * following TDD principles - defining the expected behavior first
 */

/**
 * Set up a shadow document for testing
 * @param {Object} page - Playwright page object
 * @param {string} deviceId - Device ID to set up shadow for
 * @param {Object} options - Shadow document options
 * @returns {Promise<void>}
 */
async function setupTestShadow(page, deviceId, options = {}) {
  console.log(`Setting up shadow document for device: ${deviceId}`);

  // Default shadow data
  const defaultShadow = {
    reported: {
      temperature: options.temperature || 135,
      status: options.status || "online",
      mode: options.mode || "standard",
      temperatureHistory: [
        { timestamp: Date.now() - 86400000, value: 133 },
        { timestamp: Date.now() - 43200000, value: 134 },
        { timestamp: Date.now(), value: 135 },
      ],
    },
    desired: {
      temperature: options.desiredTemperature || 135,
      mode: options.desiredMode || "standard",
    },
  };

  // Allow complete override with shadowData option
  const shadowData = options.shadowData || defaultShadow;

  // Set up shadow data in the page
  await page.evaluate(
    (data) => {
      // Store shadow data in global window object for testing
      window.testShadowDocuments = window.testShadowDocuments || {};
      window.testShadowDocuments[data.deviceId] = data.shadow;

      console.log(`Shadow document set up for ${data.deviceId}:`, data.shadow);
    },
    { deviceId, shadow: shadowData }
  );

  return shadowData;
}

/**
 * Clear test shadow document data
 * @param {Object} page - Playwright page object
 * @returns {Promise<void>}
 */
async function clearTestData(page) {
  await page.evaluate(() => {
    // Clear test data
    delete window.testShadowDocuments;
    console.log("Shadow document test data cleared");
  });
}

module.exports = {
  setupTestShadow,
  clearTestData,
};
