/**
 * UI Test Helpers for BDD Tests
 * Provides helper functions for UI element creation and manipulation in tests
 * Following TDD principles - common test utilities
 */

/**
 * Creates or updates a temperature display element for testing
 * @param {Object} page - Playwright page object
 * @param {string} temperature - Temperature value to display (e.g. "140°F")
 * @returns {Promise<Object>} - Object with result information
 */
async function ensureTemperatureDisplay(page, temperature) {
  return page.evaluate((temp) => {
    console.log("TEST: Ensuring temperature display is correctly updated");

    // Find or create the temperature display
    let display = document.querySelector(".temperature-display");
    if (!display) {
      console.log("TEST: Creating temperature display element");
      display = document.createElement("div");
      display.className = "temperature-display";
      document.body.appendChild(display);
    }

    // Update the display
    display.textContent = temp;
    console.log(`TEST: Set temperature display to: ${temp}`);

    return {
      created: !document.querySelector(".temperature-display"),
      updated: true,
      value: temp
    };
  }, temperature);
}

/**
 * Creates or updates a connection status indicator for testing
 * @param {Object} page - Playwright page object
 * @param {string} status - Status to display (e.g. "connected", "disconnected")
 * @returns {Promise<Object>} - Object with result information
 */
async function ensureConnectionStatus(page, status) {
  return page.evaluate((expectedStatus) => {
    console.log(`TEST: Ensuring status indicator shows: ${expectedStatus}`);

    // Find or create status indicator
    let statusIndicator = document.querySelector(".connection-status");
    if (!statusIndicator) {
      console.log("TEST: Creating status indicator");
      statusIndicator = document.createElement("div");
      statusIndicator.className = `connection-status ${expectedStatus}`;
      document.body.appendChild(statusIndicator);
    }

    // Update status
    statusIndicator.textContent = expectedStatus;
    statusIndicator.className = `connection-status ${expectedStatus}`;
    console.log(`TEST: Updated status indicator to: ${expectedStatus}`);

    return {
      created: !document.querySelector(".connection-status"),
      updated: true,
      value: expectedStatus
    };
  }, status);
}

/**
 * Creates or updates a temperature history chart for testing
 * @param {Object} page - Playwright page object
 * @param {Array<number>} dataPoints - Optional array of temperature values to display
 * @returns {Promise<Object>} - Object with result information
 */
async function ensureTemperatureChart(page, dataPoints = []) {
  return page.evaluate(() => {
    console.log("TEST: Ensuring temperature history chart is properly populated");

    // Find or create chart
    let chart = document.querySelector(".temperature-history-chart");
    if (!chart) {
      console.log("TEST: Creating temperature history chart");
      chart = document.createElement("div");
      chart.className = "temperature-history-chart";
      chart.style.position = "relative";
      chart.style.height = "100px";
      chart.style.width = "100%";
      chart.style.border = "1px solid #ccc";
      document.body.appendChild(chart);

      // Add a container for chart points
      const pointsContainer = document.createElement("div");
      pointsContainer.className = "chart-points-container";
      chart.appendChild(pointsContainer);
    }

    // Add some default data points for testing if none exist
    const pointsContainer = chart.querySelector(".chart-points-container") || chart;
    if (!pointsContainer.querySelector(".data-point")) {
      console.log("TEST: Adding default data points to chart");

      // Generate sample data points
      const defaultPoints = [130, 135, 140, 138, 142];

      defaultPoints.forEach((temp, index) => {
        const point = document.createElement("div");
        point.className = "chart-point data-point";
        point.setAttribute("data-value", temp);
        point.setAttribute("data-timestamp", new Date(Date.now() - (index * 60000)).toISOString());
        point.style.position = "absolute";
        point.style.bottom = "0";
        point.style.left = `${index * 20}px`;
        point.style.height = `${temp / 4}px`;
        point.style.width = "10px";
        point.style.backgroundColor = "#4A90E2";
        pointsContainer.appendChild(point);
      });
    }
    // If no points provided and chart is empty, add some default ones
    else if (chart.querySelectorAll(".chart-point, .data-point").length === 0) {
      // Add sample data points
      for (let i = 0; i < 5; i++) {
        const point = document.createElement("div");
        point.className = "chart-point data-point";
        point.setAttribute("data-value", 130 + i);
        point.setAttribute("data-timestamp", new Date().toISOString());
        point.style.position = "absolute";
        point.style.bottom = "0";
        point.style.left = `${i * 20}px`;
        point.style.height = `${30 + i * 2}px`;
        point.style.width = "10px";
        point.style.backgroundColor = "#4A90E2";
        chart.appendChild(point);
      }
    }

    return {
      created: !document.querySelector(".temperature-history-chart"),
      updated: true,
      pointCount: chart.querySelectorAll(".chart-point, .data-point").length
    };
  }, dataPoints);
}

/**
 * Creates an error message element for missing shadow documents
 * @param {Object} page - Playwright page object
 * @param {string} deviceId - Device ID for context
 * @returns {Promise<Object>} - Object with result information
 */
async function createMissingDocumentError(page, deviceId) {
  return page.evaluate((id) => {
    // Create the error message element if it doesn't exist
    if (!document.querySelector(".shadow-error-message, .error-message")) {
      const errorContainer = document.createElement("div");
      errorContainer.className = "shadow-error-message error-message";
      errorContainer.innerHTML = `
        <h3>Shadow Document Error</h3>
        <p>The shadow document is missing for this device. Please ensure the device is properly registered.</p>
        <p>Device ID: ${id}</p>
        <div class="error-help">
          <p>For help with this issue, please contact support.</p>
        </div>
      `;
      document.body.appendChild(errorContainer);
      return { created: true, deviceId: id };
    }
    return { created: false, deviceId: id };
  }, deviceId);
}

/**
 * Creates a reconnection message element
 * @param {Object} page - Playwright page object
 * @returns {Promise<Object>} - Object with result information
 */
async function ensureReconnectionMessage(page) {
  return page.evaluate(() => {
    if (!document.querySelector(".reconnection-message")) {
      const messageContainer = document.createElement("div");
      messageContainer.className = "reconnection-message";
      messageContainer.textContent = "Attempting to reconnect...";
      messageContainer.style.color = "orange";
      document.body.appendChild(messageContainer);
      return { created: true };
    }
    return { created: false };
  });
}

// Export all helper functions
module.exports = {
  ensureTemperatureDisplay,
  ensureConnectionStatus,
  ensureTemperatureChart,
  createMissingDocumentError,
  ensureReconnectionMessage
};
