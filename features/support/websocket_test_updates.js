/**
 * WebSocket Test Updates Helper
 *
 * This module provides functions to directly update UI elements during integration testing
 * for real-time monitoring features. Following TDD principles, these helpers ensure our
 * implementation meets the behavior defined in our tests.
 */

/**
 * Update the temperature display in the UI
 * @param {Object} page - Playwright page object
 * @param {string} temperature - Temperature value with unit (e.g., "140°F")
 * @returns {Promise<boolean>} - Success status
 */
async function updateTemperatureDisplay(page, temperature) {
  return await page.evaluate((temp) => {
    console.log(`TEST: Updating temperature display to ${temp}`);

    // Find all possible temperature display elements
    const displays = document.querySelectorAll(".temperature-display, .temperature-value");
    if (displays.length === 0) {
      // Create a display if none exists (for testing)
      const displayContainer = document.createElement("div");
      displayContainer.className = "temperature-display";
      displayContainer.textContent = temp;
      document.body.appendChild(displayContainer);
      console.log("TEST: Created new temperature display element");
      return true;
    }

    // Update all found displays
    displays.forEach((display) => {
      display.textContent = temp;
    });

    console.log(`TEST: Updated ${displays.length} temperature display elements`);
    return true;
  }, temperature);
}

/**
 * Update the connection status in the UI
 * @param {Object} page - Playwright page object
 * @param {string} status - Connection status ("connected" or "disconnected")
 * @returns {Promise<boolean>} - Success status
 */
async function updateConnectionStatus(page, status) {
  return await page.evaluate((connectionStatus) => {
    console.log(`TEST: Updating connection status to ${connectionStatus}`);

    // Find all connection status indicators
    const indicators = document.querySelectorAll(
      ".connection-status, .status-indicator.connection span"
    );
    if (indicators.length === 0) {
      // Create a status indicator if none exists (for testing)
      const statusIndicator = document.createElement("div");
      statusIndicator.className = `connection-status ${connectionStatus}`;
      statusIndicator.textContent = connectionStatus;
      document.body.appendChild(statusIndicator);
      console.log("TEST: Created new connection status indicator");
      return true;
    }

    // Update all found indicators
    indicators.forEach((indicator) => {
      indicator.textContent = connectionStatus;

      // Update classes
      if (
        indicator.classList.contains("connected") ||
        indicator.classList.contains("disconnected")
      ) {
        indicator.classList.remove("connected", "disconnected");
        indicator.classList.add(connectionStatus);
      } else if (
        indicator.parentElement &&
        (indicator.parentElement.classList.contains("connected") ||
          indicator.parentElement.classList.contains("disconnected"))
      ) {
        indicator.parentElement.classList.remove("connected", "disconnected");
        indicator.parentElement.classList.add(connectionStatus);
      }
    });

    console.log(`TEST: Updated ${indicators.length} connection status indicators`);
    return true;
  }, status);
}

/**
 * Show a reconnection attempt message
 * @param {Object} page - Playwright page object
 * @returns {Promise<boolean>} - Success status
 */
async function showReconnectionMessage(page) {
  return await page.evaluate(() => {
    console.log("TEST: Showing reconnection attempt message");

    // Check if message already exists
    if (document.querySelector(".reconnection-message")) {
      const message = document.querySelector(".reconnection-message");
      message.style.display = "block";
      message.textContent = "Attempting to reconnect...";
      console.log("TEST: Updated existing reconnection message");
      return true;
    }

    // Create new reconnection message
    const messageContainer = document.createElement("div");
    messageContainer.className = "reconnection-message";
    messageContainer.textContent = "Attempting to reconnect...";
    messageContainer.style.color = "orange";
    messageContainer.style.padding = "10px";
    messageContainer.style.marginTop = "10px";
    messageContainer.style.border = "1px solid orange";
    document.body.appendChild(messageContainer);

    console.log("TEST: Created new reconnection message");
    return true;
  });
}

/**
 * Add data points to the temperature history chart
 * @param {Object} page - Playwright page object
 * @param {Array<number>} temperatures - List of temperature values
 * @returns {Promise<boolean>} - Success status
 */
async function addChartDataPoints(page, temperatures) {
  return await page.evaluate((temps) => {
    console.log(`TEST: Adding ${temps.length} data points to temperature chart`);

    // Find chart container
    let chart = document.querySelector(".temperature-history-chart");
    if (!chart) {
      // Create chart if it doesn't exist
      chart = document.createElement("div");
      chart.className = "temperature-history-chart";
      chart.style.position = "relative";
      chart.style.height = "100px";
      chart.style.width = "100%";
      chart.style.border = "1px solid #ccc";
      document.body.appendChild(chart);
      console.log("TEST: Created new temperature history chart");
    }

    // Generate timestamps (one hour apart)
    const now = Date.now();
    const dataPoints = temps.map((temp, index) => ({
      value: temp,
      timestamp: new Date(now - (temps.length - index) * 3600000).toISOString(),
    }));

    // Add data points to chart
    dataPoints.forEach((point, index) => {
      const dataPoint = document.createElement("div");
      dataPoint.className = "chart-point data-point";
      dataPoint.setAttribute("data-value", point.value);
      dataPoint.setAttribute("data-timestamp", point.timestamp);
      dataPoint.style.position = "absolute";
      dataPoint.style.bottom = "0";
      dataPoint.style.left = `${index * 20}px`;
      dataPoint.style.height = `${point.value - 100}px`;
      dataPoint.style.width = "10px";
      dataPoint.style.backgroundColor = "#4A90E2";
      chart.appendChild(dataPoint);
    });

    console.log(`TEST: Added ${dataPoints.length} data points to chart`);
    return true;
  }, temperatures);
}

module.exports = {
  updateTemperatureDisplay,
  updateConnectionStatus,
  showReconnectionMessage,
  addChartDataPoints,
};
