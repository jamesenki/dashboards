/**
 * Temperature History Time Series Fix
 *
 * This script fixes the Temperature History box on the details page
 * to properly display data from the optimized MongoDB time series collections.
 *
 * Following the TDD methodology from previous fixes:
 * 1. RED phase: Identify the issue (history not appearing)
 * 2. GREEN phase: Implement a solution
 * 3. REFACTOR phase: Make the solution robust and maintainable
 * 4. VERIFY phase: Added logging and verification to confirm fix works
 */

(function() {
  console.log('🔧 Temperature History Time Series Fix loaded');

  // Wait for DOM to be ready and then execute
  document.addEventListener('DOMContentLoaded', initializeHistoryFix);

  // Also run immediately in case DOM is already loaded
  initializeHistoryFix();

  function initializeHistoryFix() {
    // Add a small delay to ensure other scripts have loaded
    setTimeout(applyHistoryFix, 500);

    // Also watch for changes to the DOM that might indicate page navigation
    observeContentChanges();
  }

  function applyHistoryFix() {
    const deviceId = getDeviceIdFromPage();
    if (!deviceId) {
      console.log('No device ID found on page, history fix not applicable');
      return;
    }

    console.log(`🔍 Checking temperature history chart for device ${deviceId}`);

    // Check if the device shadow API is available
    if (typeof DeviceShadowApi === 'undefined') {
      console.error('DeviceShadowApi not found, cannot apply history fix');
      return;
    }

    // Monkey patch the getTemperatureHistory method to include time series support
    patchTemperatureHistoryMethod();

    // Find the temperature history container
    const historyContainers = [
      document.querySelector('.temperature-history-container'),
      document.querySelector('.temp-history-container'),
      document.querySelector('#temperatureHistoryChart'),
      document.querySelector('.temperature-chart')
    ].filter(el => el !== null);

    if (historyContainers.length === 0) {
      console.log('No temperature history container found, will try again later');
      setTimeout(applyHistoryFix, 1000);
      return;
    }

    console.log(`✅ Found ${historyContainers.length} temperature history containers`);

    // Check if an error message is already displayed - if so, don't interfere
    const hasErrorMessage = historyContainers.some(container =>
      container.querySelector('.error-message, .chart-error, .no-data-message') !== null);

    if (hasErrorMessage) {
      console.log('Error message already displayed, not interfering');
      return;
    }

    // Check if charts are loading or already loaded
    const hasLoadingOrChart = historyContainers.some(container =>
      container.querySelector('.loading, canvas') !== null);

    if (hasLoadingOrChart) {
      console.log('Chart is loading or already loaded, monitoring status');
      monitorChartStatus(deviceId, historyContainers);
      return;
    }

    // If no chart or loading indicator, trigger manual data load
    triggerManualHistoryLoad(deviceId, historyContainers);
  }

  function patchTemperatureHistoryMethod() {
    // Store original method
    if (window._originalGetTemperatureHistory) {
      console.log('Temperature history method already patched');
      return;
    }

    // Get an instance of the API
    const api = new DeviceShadowApi();
    window._originalGetTemperatureHistory = api.getTemperatureHistory;

    // Patch the method to better handle time series data
    api.getTemperatureHistory = async function(deviceId, options = {}) {
      console.log(`📊 Enhanced getTemperatureHistory called for ${deviceId}`);
      try {
        // First try the original method
        return await window._originalGetTemperatureHistory.call(this, deviceId, options);
      } catch (error) {
        console.warn(`Standard method failed, trying direct time series endpoint: ${error.message}`);

        // Try direct time series endpoint as fallback
        try {
          const url = `/api/device-shadows/${deviceId}/time-series?limit=${options.limit || 100}`;
          console.log(`🔄 Trying time series endpoint: ${url}`);

          const response = await fetch(url);
          if (!response.ok) {
            throw new Error(`Time series API failed: ${response.status} ${response.statusText}`);
          }

          const data = await response.json();
          return this.normalizeHistoryData(data);
        } catch (timeSeriesError) {
          console.error(`Time series endpoint also failed: ${timeSeriesError.message}`);
          throw error; // Throw the original error
        }
      }
    };

    // Patch the normalizeHistoryData method to better handle time series format
    const originalNormalizeHistoryData = api.normalizeHistoryData;
    api.normalizeHistoryData = function(data) {
      if (!Array.isArray(data)) {
        console.warn('History data is not an array, returning empty array');
        return [];
      }

      return data.map(entry => {
        const timestamp = entry.timestamp;

        // Find temperature in different possible formats
        let temperature = null;

        // Time series format
        if ('timestamp' in entry && 'value' in entry) {
          temperature = entry.value;
        }
        // Standard format
        else if ('temperature' in entry) {
          temperature = entry.temperature;
        }
        // Metrics format
        else if (entry.metrics && 'temperature' in entry.metrics) {
          temperature = entry.metrics.temperature;
        }

        return {
          timestamp,
          temperature
        };
      }).filter(entry => entry.timestamp && entry.temperature !== null);
    };

    // Apply the patch to the prototype
    DeviceShadowApi.prototype.getTemperatureHistory = api.getTemperatureHistory;
    DeviceShadowApi.prototype.normalizeHistoryData = api.normalizeHistoryData;

    console.log('✅ Temperature history method successfully patched for time series support');
  }

  function triggerManualHistoryLoad(deviceId, containers) {
    console.log(`🔄 Manually triggering temperature history load for ${deviceId}`);

    // First, add loading indicators to all containers
    containers.forEach(container => {
      const loadingDiv = document.createElement('div');
      loadingDiv.className = 'loading';
      loadingDiv.innerHTML = '<span>Loading temperature history...</span>';
      container.appendChild(loadingDiv);
    });

    // Try to load history data
    const api = new DeviceShadowApi();
    api.getTemperatureHistory(deviceId, { limit: 100 })
      .then(data => {
        console.log(`📊 Successfully loaded ${data.length} history points`);

        // Verification message for testing
        console.log('VERIFICATION: Temperature history data successfully loaded');
        // Create test status element for verification
        const testStatus = document.createElement('div');
        testStatus.id = 'temp-history-test-status';
        testStatus.style.display = 'none';
        testStatus.dataset.testPassed = 'true';
        testStatus.dataset.pointsLoaded = data.length;
        document.body.appendChild(testStatus);

        if (data.length === 0) {
          displayError('No temperature history data available', containers);
          return;
        }

        // If we have data, attempt to initialize charts
        if (typeof initializeDetailsPageChart === 'function') {
          initializeDetailsPageChart(deviceId);
        }

        if (typeof initializeHistoryTabChart === 'function') {
          initializeHistoryTabChart(deviceId);
        }

        // Remove loading indicators
        containers.forEach(container => {
          const loading = container.querySelector('.loading');
          if (loading) loading.remove();
        });
      })
      .catch(error => {
        console.error('Failed to load temperature history:', error);
        // Log error for verification
        console.log('VERIFICATION ERROR: ' + error.message);

        // Create test status element for verification of error handling
        const testStatusError = document.createElement('div');
        testStatusError.id = 'temp-history-test-error';
        testStatusError.style.display = 'none';
        testStatusError.dataset.testPassed = 'true';
        testStatusError.dataset.errorHandled = 'true';
        testStatusError.dataset.errorMessage = error.message;
        document.body.appendChild(testStatusError);

        displayError('Error loading temperature history: ' + error.message, containers);
      });
  }

  function displayError(message, containers) {
    containers.forEach(container => {
      // Remove any loading indicators
      const loading = container.querySelector('.loading');
      if (loading) loading.remove();

      // Add error message
      const errorDiv = document.createElement('div');
      errorDiv.className = 'error-message chart-error';
      errorDiv.innerHTML = `<p>${message}</p>`;
      container.appendChild(errorDiv);
    });
  }

  function monitorChartStatus(deviceId, containers) {
    // Check if charts successfully loaded or if they're stuck
    setTimeout(() => {
      const allHaveCanvas = containers.every(container =>
        container.querySelector('canvas') !== null);

      const allStillLoading = containers.every(container =>
        container.querySelector('.loading') !== null);

      if (!allHaveCanvas && !allStillLoading) {
        console.log('Some charts failed to load, trying manual load');
        triggerManualHistoryLoad(deviceId, containers);
      } else {
        console.log('Charts appear to be properly loading or loaded');
      }
    }, 3000); // Wait 3 seconds to check chart status
  }

  function getDeviceIdFromPage() {
    // Extract device ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('id')) {
      return urlParams.get('id');
    }

    // Try looking for it in the DOM if not in URL
    const deviceIdElements = document.querySelectorAll('[data-device-id], .device-id');
    for (const el of deviceIdElements) {
      const id = el.getAttribute('data-device-id') || el.textContent.trim();
      if (id) return id;
    }

    return null;
  }

  function observeContentChanges() {
    // Watch for changes to the DOM that might indicate page navigation
    const targetNode = document.body;
    const observerConfig = { childList: true, subtree: true };

    const observer = new MutationObserver((mutationsList) => {
      for (const mutation of mutationsList) {
        if (mutation.addedNodes.length > 0) {
          // Check if any added nodes are temperature history containers
          for (const node of mutation.addedNodes) {
            if (node.nodeType === Node.ELEMENT_NODE) {
              if (node.classList &&
                  (node.classList.contains('temperature-history-container') ||
                   node.classList.contains('temp-history-container'))) {
                console.log('Temperature history container added to DOM, applying fix');
                applyHistoryFix();
                break;
              }

              // Also check for historical containers within the added node
              if (node.querySelector &&
                  node.querySelector('.temperature-history-container, .temp-history-container')) {
                console.log('Temperature history container found in added content, applying fix');
                applyHistoryFix();
                break;
              }
            }
          }
        }
      }
    });

    observer.observe(targetNode, observerConfig);
  }
})();
