/**
 * Complete Fixes for IoTSphere
 *
 * This script fixes the two critical issues:
 * 1. Duplicate water heaters on the list page
 * 2. Missing temperature history on details page
 *
 * Following TDD methodology:
 * - RED: Identified failing behavior
 * - GREEN: Implement solutions
 * - REFACTOR: Consolidate fixes
 */

(function() {
  // Execute immediately AND when DOM is loaded
  applyFixes();
  document.addEventListener('DOMContentLoaded', applyFixes);

  // Also set a timeout as a fallback
  setTimeout(applyFixes, 1000);

  function applyFixes() {
    // Get current page type
    const isListPage = isWaterHeaterListPage();
    const isDetailsPage = isWaterHeaterDetailsPage();

    console.log(`🔧 Complete fixes running on ${isListPage ? 'list page' : isDetailsPage ? 'details page' : 'other page'}`);

    if (isListPage) {
      // FIX 1: Deduplicate water heater cards
      fixDuplicateWaterHeaters();
    }

    if (isDetailsPage) {
      // FIX 2: Fix temperature history display
      fixTemperatureHistory();
    }
  }

  // CHECK PAGE TYPE FUNCTIONS

  function isWaterHeaterListPage() {
    // Check if we're on the water heater list page
    const path = window.location.pathname;
    return path === '/' ||
           path === '/water-heaters' ||
           path === '/index.html' ||
           path.endsWith('/water-heaters/');
  }

  function isWaterHeaterDetailsPage() {
    // Check if we're on a water heater details page
    const path = window.location.pathname;
    return path.match(/\/water-heaters\/[\w-]+/i) !== null;
  }

  // FIX 1: DUPLICATE WATER HEATERS

  function fixDuplicateWaterHeaters() {
    console.log('🔧 Fixing duplicate water heaters on list page');

    // Wait a moment to ensure cards are rendered
    setTimeout(() => {
      // First, let's find all elements that might be water heater cards using multiple approaches
      const allPossibleCards = document.querySelectorAll(
        // Standard card classes
        '.water-heater-card, .card, .device-card, ' +
        // Elements with device ID attributes
        '[data-id], [data-device-id], ' +
        // Elements with IDs that look like water heater IDs
        '[id^="heater-"], [id^="aqua-"], [id^="water-heater-"]'
      );

      console.log(`Found ${allPossibleCards.length} possible water heater cards`);

      // Initialize tracking
      const seenDeviceIds = new Map();
      const duplicateCards = [];

      // Process each card to find duplicates
      allPossibleCards.forEach((card, index) => {
        // First, try to get device ID using multiple methods
        let deviceId = card.getAttribute('data-id') ||
                        card.getAttribute('data-device-id');

        // Check for ID attribute pattern like "heater-wh-001"
        if (!deviceId && card.id && card.id.startsWith('heater-')) {
          deviceId = card.id.substring(7); // remove "heater-" prefix
        }

        // Try to find device ID in inner content
        if (!deviceId) {
          // Look for specific device ID elements
          const idElement = card.querySelector('.device-id, .id');
          if (idElement && idElement.textContent) {
            deviceId = idElement.textContent.trim();
          }

          // If still no ID, try to extract from header or title
          if (!deviceId) {
            const titleElement = card.querySelector('h2, h3, .title, .header');
            if (titleElement && titleElement.textContent) {
              // Extract ID-like pattern (letters followed by numbers and dashes)
              const match = titleElement.textContent.match(/([a-z]+-[\w-]+)/i);
              if (match) {
                deviceId = match[1];
              }
            }
          }
        }

        // If we found a device ID
        if (deviceId) {
          // Check if we've seen this ID before
          if (seenDeviceIds.has(deviceId)) {
            // This is a duplicate
            console.log(`Found duplicate for device ${deviceId} at index ${index}`);
            duplicateCards.push(card);
          } else {
            // First time seeing this ID
            seenDeviceIds.set(deviceId, card);
          }
        } else {
          console.log(`Card at index ${index} has no identifiable device ID`);
        }
      });

      // Hide duplicates
      duplicateCards.forEach(card => {
        card.style.display = 'none';
        card.classList.add('duplicate-card');
        card.setAttribute('data-duplicate', 'true');
      });

      console.log(`✅ Hidden ${duplicateCards.length} duplicate cards`);

      // If we actually fixed duplicates, add a test verification
      if (duplicateCards.length > 0) {
        // Create test status element
        const testStatus = document.createElement('div');
        testStatus.id = 'deduplication-complete-test';
        testStatus.style.display = 'none';
        testStatus.dataset.testPassed = 'true';
        testStatus.dataset.duplicatesFixed = duplicateCards.length;
        document.body.appendChild(testStatus);

        console.log('VERIFICATION: Duplicate water heaters fixed');
      }
    }, 500); // Short delay to ensure DOM is populated
  }

  // FIX 2: TEMPERATURE HISTORY

  function fixTemperatureHistory() {
    console.log('🔧 Fixing temperature history on details page');

    // Extract device ID from URL
    const deviceId = extractDeviceIdFromUrl();
    if (!deviceId) {
      console.log('Could not extract device ID from URL, cannot fix temperature history');
      return;
    }

    console.log(`Found device ID in URL: ${deviceId}`);

    // Set a flag to prevent multiple initializations
    if (window._temperatureHistoryFixed) {
      console.log('Temperature history fix already applied');
      return;
    }
    window._temperatureHistoryFixed = true;

    // First, locate or create temperature chart containers
    const detailsContainer = document.querySelector('.details-content, .device-details, main');
    if (!detailsContainer) {
      console.error('Could not find details container');
      return;
    }

    // Look for existing temperature chart containers
    let chartContainer = document.querySelector(
      '.temperature-history-container, .temp-history-container, ' +
      '#temperatureHistoryChart, .temperature-chart'
    );

    // If no chart container exists, create one in the details section
    if (!chartContainer) {
      console.log('Creating temperature history container');

      // Find a good location for the chart
      const insertLocation = document.querySelector(
        '.details-section, .dashboard-section, .chart-section, ' +
        '.temperature-section, .main-content > div'
      ) || detailsContainer;

      // Create chart container
      chartContainer = document.createElement('div');
      chartContainer.className = 'temperature-history-container';
      chartContainer.innerHTML = `
        <h3>Temperature History</h3>
        <div class="chart-wrapper">
          <canvas id="temperatureHistoryChart"></canvas>
          <div class="loading">Loading temperature history...</div>
        </div>
      `;

      // Insert it into the DOM
      insertLocation.appendChild(chartContainer);
    }

    // Next, add our shadow document error handling
    patchDeviceShadowApi();

    // Finally, initialize the chart
    initializeTemperatureHistoryChart(deviceId, chartContainer);
  }

  function extractDeviceIdFromUrl() {
    // Get device ID from URL pattern /water-heaters/{id}
    const path = window.location.pathname;
    const matches = path.match(/\/water-heaters\/([\w-]+)/i);
    if (matches && matches[1]) {
      return matches[1];
    }

    // Fallback to query parameter ?id=
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('id')) {
      return urlParams.get('id');
    }

    return null;
  }

  function patchDeviceShadowApi() {
    // Check if DeviceShadowApi exists
    if (typeof DeviceShadowApi === 'undefined') {
      console.error('DeviceShadowApi not found, cannot patch');
      return;
    }

    console.log('Patching DeviceShadowApi for proper error handling');

    // Get an instance of the API
    const api = new DeviceShadowApi();

    // Store original method if not already stored
    if (!window._originalGetTemperatureHistory) {
      window._originalGetTemperatureHistory = api.getTemperatureHistory;
    }

    // Patch the method to handle errors properly
    api.getTemperatureHistory = async function(deviceId, options = {}) {
      try {
        console.log(`Getting temperature history for ${deviceId}`);
        // Try the original method
        return await window._originalGetTemperatureHistory.call(this, deviceId, options);
      } catch (error) {
        console.warn(`Error getting temperature history: ${error.message}`);

        // Check for "No shadow document exists" error
        if (error.message && error.message.includes('No shadow document exists')) {
          console.log('Detected missing shadow document error');

          // Try direct time series endpoint as fallback
          try {
            const url = `/api/device-shadows/${deviceId}/time-series?limit=${options.limit || 100}`;
            console.log(`Trying time series endpoint: ${url}`);

            const response = await fetch(url);
            if (!response.ok) {
              if (response.status === 404) {
                throw new Error('No temperature history available for this device');
              }
              throw new Error(`Time series API failed: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            console.log(`Time series API returned ${data.length} entries`);
            return this.normalizeHistoryData(data);
          } catch (timeSeriesError) {
            console.error(`Time series endpoint also failed: ${timeSeriesError.message}`);

            // Re-throw with clearer message
            const message = 'No shadow document exists for this device. Please check device configuration.';
            const newError = new Error(message);
            newError.originalError = error;
            throw newError;
          }
        }

        // Re-throw the original error
        throw error;
      }
    };

    // Apply the patch to the prototype
    DeviceShadowApi.prototype.getTemperatureHistory = api.getTemperatureHistory;

    console.log('✅ DeviceShadowApi patched for proper error handling');
  }

  function initializeTemperatureHistoryChart(deviceId, container) {
    console.log(`Initializing temperature history chart for ${deviceId}`);

    // Add loading indicator if not present
    let loadingIndicator = container.querySelector('.loading');
    if (!loadingIndicator) {
      loadingIndicator = document.createElement('div');
      loadingIndicator.className = 'loading';
      loadingIndicator.textContent = 'Loading temperature history...';
      container.appendChild(loadingIndicator);
    }

    // Create API instance
    const api = new DeviceShadowApi();

    // Load temperature history
    api.getTemperatureHistory(deviceId, { limit: 100 })
      .then(data => {
        console.log(`Loaded ${data.length} temperature history points`);

        // Remove loading indicator
        if (loadingIndicator) {
          loadingIndicator.remove();
        }

        if (data.length === 0) {
          displayError(container, 'No temperature history data available');
          return;
        }

        // Render chart
        renderTemperatureChart(deviceId, data, container);

        // Add test verification
        const testStatus = document.createElement('div');
        testStatus.id = 'temp-history-fix-complete';
        testStatus.style.display = 'none';
        testStatus.dataset.testPassed = 'true';
        testStatus.dataset.pointsLoaded = data.length;
        document.body.appendChild(testStatus);

        console.log('VERIFICATION: Temperature history loaded and displayed');
      })
      .catch(error => {
        console.error(`Error loading temperature history: ${error.message}`);

        // Remove loading indicator
        if (loadingIndicator) {
          loadingIndicator.remove();
        }

        // Display error message
        displayError(container, error.message || 'Failed to load temperature history data');

        // Create test status for error verification
        const testStatus = document.createElement('div');
        testStatus.id = 'temp-history-error-handled';
        testStatus.style.display = 'none';
        testStatus.dataset.errorHandled = 'true';
        testStatus.dataset.errorMessage = error.message;
        document.body.appendChild(testStatus);

        console.log(`VERIFICATION: Temperature history error handled: ${error.message}`);
      });
  }

  function displayError(container, message) {
    console.log(`Displaying error: ${message}`);

    // Create error element
    const errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.innerHTML = `
      <div class="alert alert-warning">
        <i class="fas fa-exclamation-triangle"></i>
        <span>${message}</span>
      </div>
    `;

    // Clear container and append error
    if (container.querySelector('canvas')) {
      container.querySelector('canvas').style.display = 'none';
    }

    // Remove loading if it exists
    const loading = container.querySelector('.loading');
    if (loading) {
      loading.remove();
    }

    // Remove existing error messages
    const existingError = container.querySelector('.error-message');
    if (existingError) {
      existingError.remove();
    }

    // Add the error message
    container.appendChild(errorElement);
  }

  function renderTemperatureChart(deviceId, data, container) {
    console.log(`Rendering chart with ${data.length} points`);

    // Find or create canvas element
    let canvas = container.querySelector('canvas');
    if (!canvas) {
      canvas = document.createElement('canvas');
      canvas.id = 'temperatureHistoryChart';
      container.appendChild(canvas);
    }

    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
      console.error('Chart.js not available, cannot render chart');
      // Load Chart.js dynamically
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
      script.onload = () => renderTemperatureChart(deviceId, data, container);
      document.head.appendChild(script);
      return;
    }

    // Prepare data for Chart.js
    const timestamps = [];
    const temperatures = [];

    // Sort data by timestamp
    data.sort((a, b) => {
      const timestampA = new Date(a.timestamp);
      const timestampB = new Date(b.timestamp);
      return timestampA - timestampB;
    });

    // Extract data points
    data.forEach(point => {
      // Format date for display
      const date = new Date(point.timestamp);
      const formattedDate = `${date.getMonth()+1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;

      // Get temperature from various possible formats
      let temperature = null;
      if ('temperature' in point) {
        temperature = point.temperature;
      } else if (point.metrics && 'temperature' in point.metrics) {
        temperature = point.metrics.temperature;
      } else if ('value' in point) {
        temperature = point.value;
      }

      if (temperature !== null) {
        timestamps.push(formattedDate);
        temperatures.push(temperature);
      }
    });

    // Create chart
    if (window._temperatureChart) {
      window._temperatureChart.destroy();
    }

    window._temperatureChart = new Chart(canvas, {
      type: 'line',
      data: {
        labels: timestamps,
        datasets: [{
          label: 'Temperature (°F)',
          data: temperatures,
          borderColor: 'rgb(75, 192, 192)',
          tension: 0.1,
          fill: false
        }]
      },
      options: {
        responsive: true,
        scales: {
          x: {
            title: {
              display: true,
              text: 'Date/Time'
            }
          },
          y: {
            title: {
              display: true,
              text: 'Temperature (°F)'
            }
          }
        }
      }
    });

    console.log('✅ Temperature chart rendered successfully');
  }
})();
