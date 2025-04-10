/**
 * Temperature Chart Fix Integration
 *
 * This script applies critical fixes to the temperature history chart functionality.
 * Following TDD principles:
 * 1. RED: Identify the issue with temperature chart not rendering
 * 2. GREEN: Apply fixes to make the chart render properly
 * 3. REFACTOR: Ensure the solution is robust and maintainable
 */

(function() {
  console.log('📊 Temperature Chart Fix: Initializing...');

  // Configuration
  const config = {
    defaultContainerId: 'temperatureHistoryChart',
    containerSelectors: [
      '#temperatureHistoryChart',
      '.temperature-chart-container',
      '.chart-container',
      '[id*="temperature"][id*="chart"]'
    ],
    retryAttempts: 5,
    retryInterval: 1000,
    chartClasses: ['temperature-chart', 'chart-js', 'shadow-chart'],
    deviceIdAttribute: 'data-device-id'
  };

  // Track fix application status
  let fixApplied = false;
  let lastDeviceId = null;
  let attempts = 0;

  /**
   * Find a temperature chart container in the DOM
   * @returns {HTMLElement|null} The container element or null if not found
   */
  function findChartContainer() {
    for (const selector of config.containerSelectors) {
      const container = document.querySelector(selector);
      if (container) {
        console.log(`📊 Found chart container with selector: ${selector}`);
        return container;
      }
    }

    // If no container found with specific selectors, look for any element that might be a chart container
    const potentialContainers = document.querySelectorAll('[id*="chart"], [class*="chart"]');
    if (potentialContainers.length > 0) {
      console.log(`📊 Found ${potentialContainers.length} potential chart containers`);
      return potentialContainers[0]; // Use the first potential container
    }

    console.warn('📊 No temperature chart container found');
    return null;
  }

  /**
   * Extract device ID from the page
   * @returns {string|null} The device ID or null if not found
   */
  function getDeviceId() {
    // Try to find device ID from URL
    const urlMatch = window.location.pathname.match(/\/water-heaters\/([^\/]+)/);
    if (urlMatch && urlMatch[1]) {
      return urlMatch[1];
    }

    // Try to find from data attributes
    const container = findChartContainer();
    if (container && container.hasAttribute(config.deviceIdAttribute)) {
      return container.getAttribute(config.deviceIdAttribute);
    }

    // Try to find from any element with the attribute
    const deviceElement = document.querySelector(`[${config.deviceIdAttribute}]`);
    if (deviceElement) {
      return deviceElement.getAttribute(config.deviceIdAttribute);
    }

    // Fallback: check if there's a global variable with device ID
    if (window.DEVICE_ID) {
      return window.DEVICE_ID;
    }

    return null;
  }

  /**
   * Initialize or fix an existing temperature chart
   * @param {HTMLElement} container The chart container
   * @param {string} deviceId The device ID
   */
  function initializeTemperatureChart(container, deviceId) {
    if (!container || !deviceId) {
      console.error('📊 Cannot initialize temperature chart: missing container or device ID');
      return;
    }

    // Ensure container has needed properties
    container.id = container.id || 'temperatureHistoryChart';

    // Add necessary classes
    config.chartClasses.forEach(className => {
      if (!container.classList.contains(className)) {
        container.classList.add(className);
      }
    });

    // Store device ID on container
    container.setAttribute(config.deviceIdAttribute, deviceId);

    // Check if we already have a canvas
    let canvas = container.querySelector('canvas');
    if (!canvas) {
      console.log('📊 Creating canvas for temperature chart');
      canvas = document.createElement('canvas');
      canvas.id = `${container.id}-canvas`;
      canvas.style.width = '100%';
      canvas.style.height = '300px';
      canvas.style.display = 'block';
      container.appendChild(canvas);
    }

    // Check if chart object already exists and is properly initialized
    if (window.temperatureChart && window.temperatureChart.chart) {
      console.log('📊 Temperature chart already initialized, updating container');
      window.temperatureChart.chartElement = container;
      window.temperatureChart.chartCanvas = canvas;
      return;
    }

    // Create a new chart instance if none exists
    console.log(`📊 Creating new temperature chart for device ${deviceId}`);
    window.temperatureChart = new DeviceShadowTemperatureChart(container.id, deviceId, {
      autoRefresh: true,
      refreshInterval: 60000 // Refresh every minute
    });

    // Set period to 7 days by default
    window.temperatureChart.setDays(7);

    fixApplied = true;
    console.log('📊 Temperature chart fix applied successfully');
  }

  /**
   * Main function to apply the temperature chart fix
   */
  function applyTemperatureChartFix() {
    if (fixApplied) {
      return;
    }

    attempts++;
    console.log(`📊 Applying temperature chart fix (attempt ${attempts}/${config.retryAttempts})`);

    const deviceId = getDeviceId();
    lastDeviceId = deviceId;

    if (!deviceId) {
      console.warn('📊 No device ID found, cannot apply fix yet');

      // Continue retrying if we haven't reached the limit
      if (attempts < config.retryAttempts) {
        setTimeout(applyTemperatureChartFix, config.retryInterval);
      }
      return;
    }

    const container = findChartContainer();
    if (!container) {
      console.warn('📊 No temperature chart container found, cannot apply fix yet');

      // Create container if this is our last attempt
      if (attempts >= config.retryAttempts) {
        console.log('📊 Creating chart container as last resort');
        const historyTab = document.querySelector('#history, [data-tab="history"]');

        if (historyTab) {
          const newContainer = document.createElement('div');
          newContainer.id = config.defaultContainerId;
          newContainer.classList.add('temperature-chart-container', 'chart-container');

          historyTab.appendChild(newContainer);
          initializeTemperatureChart(newContainer, deviceId);
          return;
        }
      }

      // Continue retrying if we haven't reached the limit
      if (attempts < config.retryAttempts) {
        setTimeout(applyTemperatureChartFix, config.retryInterval);
      }
      return;
    }

    initializeTemperatureChart(container, deviceId);
  }

  /**
   * Wait for the chart dependencies to be loaded
   */
  function waitForDependencies() {
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
      console.log('📊 Waiting for Chart.js to load...');
      setTimeout(waitForDependencies, 500);
      return;
    }

    // Check if DeviceShadowTemperatureChart is loaded
    if (typeof DeviceShadowTemperatureChart === 'undefined') {
      console.log('📊 Waiting for DeviceShadowTemperatureChart to load...');
      setTimeout(waitForDependencies, 500);
      return;
    }

    // Check if DeviceShadowApi is loaded
    if (typeof DeviceShadowApi === 'undefined') {
      console.log('📊 Waiting for DeviceShadowApi to load...');
      setTimeout(waitForDependencies, 500);
      return;
    }

    console.log('📊 All dependencies loaded, applying fix...');
    applyTemperatureChartFix();
  }

  // Add event listener to detect when history tab is shown
  document.addEventListener('click', function(e) {
    // Check if clicked element is a tab that shows the history
    const target = e.target.closest('a[href="#history"], button[data-tab="history"]');
    if (target) {
      console.log('📊 History tab clicked, checking temperature chart...');
      setTimeout(applyTemperatureChartFix, 500);
    }
  });

  // Apply fix when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', waitForDependencies);
  } else {
    waitForDependencies();
  }

  // Apply fix if page URL changes (for SPAs)
  let lastUrl = window.location.href;
  setInterval(function() {
    if (lastUrl !== window.location.href) {
      lastUrl = window.location.href;
      console.log('📊 URL changed, checking temperature chart...');
      attempts = 0;
      fixApplied = false;
      setTimeout(applyTemperatureChartFix, 1000);
    }
  }, 1000);

  // Run a final verification check
  setTimeout(function() {
    // Verify chart is working as expected
    if (!fixApplied) {
      console.warn('📊 Temperature chart fix never applied successfully');

      // Last resort: check if there's a canvas that might not be visible
      const canvases = document.querySelectorAll('canvas');
      if (canvases.length > 0) {
        console.log(`📊 Found ${canvases.length} canvas elements, ensuring visibility...`);
        canvases.forEach(canvas => {
          canvas.style.display = 'block';
          canvas.style.visibility = 'visible';

          // Try to get parent containers and make them visible too
          let parent = canvas.parentElement;
          while (parent) {
            parent.style.display = 'block';
            parent.style.visibility = 'visible';
            parent = parent.parentElement;
          }
        });
      }
    }
  }, 10000);
})();
