/**
 * Temperature Chart Loader for IoTSphere
 *
 * Following TDD principles to ensure temperature history data loads reliably:
 * 1. Implements retry mechanism with backoff
 * 2. Ensures chart container exists and is visible
 * 3. Properly handles and displays errors or empty data states
 */

(function() {
  console.log('💧 Temperature Chart Loader initializing');

  // Configuration
  const MAX_RETRIES = 3;
  const RETRY_DELAY_MS = 1500;
  const DATA_POINT_THRESHOLD = 5; // Minimum data points to consider valid

  // Track initialization to prevent duplication
  let initialized = false;

  // Execute on page load
  window.addEventListener('DOMContentLoaded', initializeLoader);

  // Also initialize now if DOM already loaded
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(initializeLoader, 300);
  }

  function initializeLoader() {
    if (initialized) {
      console.log('Temperature chart loader already initialized');
      return;
    }

    initialized = true;
    console.log('Initializing temperature chart loader');

    // First check if we're on a details page
    const deviceId = extractDeviceIdFromUrl();
    if (!deviceId) {
      console.log('Not on a device details page, chart loader not needed');
      return;
    }

    // Wait for tabs to initialize
    waitForTabSystem()
      .then(() => {
        // Start loading temperature data
        loadTemperatureData(deviceId, 0);

        // Add observers for tab changes to ensure chart updates when history tab is shown
        setupTabChangeObserver();
      })
      .catch(error => {
        console.error('Failed while waiting for tab system:', error);
      });
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

  function waitForTabSystem() {
    return new Promise((resolve, reject) => {
      // Check if tab system is already initialized
      if (typeof window.tabManager !== 'undefined' && window.tabManager) {
        resolve();
        return;
      }

      // Set timeout for tab system initialization
      let attempts = 0;
      const checkInterval = setInterval(() => {
        attempts++;

        if (typeof window.tabManager !== 'undefined' && window.tabManager) {
          clearInterval(checkInterval);
          resolve();
        } else if (attempts > 10) {
          clearInterval(checkInterval);
          // Resolve anyway, the page might not use the tab system
          resolve();
        }
      }, 300);
    });
  }

  function setupTabChangeObserver() {
    // Watch for history tab activation
    const historyTab = document.getElementById('history-tab');
    if (historyTab) {
      // Find tab content element
      const historyContent = document.getElementById('history-content');

      // Create observer to watch for display changes
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.attributeName === 'style' ||
              mutation.attributeName === 'class') {

            // Check if history tab is now visible
            const isVisible = window.getComputedStyle(historyContent).display !== 'none';
            if (isVisible) {
              console.log('History tab became visible, ensuring chart is loaded');
              const deviceId = extractDeviceIdFromUrl();
              if (deviceId) {
                refreshTemperatureChart(deviceId);
              }
            }
          }
        });
      });

      // Start observing tab content for attribute changes
      observer.observe(historyContent, { attributes: true });
    }
  }

  function loadTemperatureData(deviceId, retryCount) {
    console.log(`Loading temperature data for ${deviceId} (attempt ${retryCount + 1})`);

    // Find or create chart container
    let container = findOrCreateChartContainer();
    if (!container) {
      console.error('Failed to find or create chart container');
      return;
    }

    // Show loading state
    updateContainerStatus(container, 'loading');

    // Check if DeviceShadowApi exists
    if (typeof DeviceShadowApi === 'undefined') {
      console.error('DeviceShadowApi not found, cannot load temperature data');
      updateContainerStatus(container, 'error', 'API not available');
      return;
    }

    // Get temperature history data
    const api = new DeviceShadowApi();
    api.getTemperatureHistory(deviceId, { limit: 100 })
      .then(response => {
        // Check if response is an error object with detail field
        if (response && response.detail) {
          console.error(`API error: ${response.detail}`);
          updateContainerStatus(container, 'error', response.detail);
          // Create a visible error element that tests can find
          createVisibleErrorElement(container, `Failed to load temperature history: ${response.detail}`);
          return;
        }

        // Ensure response is an array
        const data = Array.isArray(response) ? response : [];
        console.log(`Loaded ${data.length} temperature data points`);

        if (!data || data.length < DATA_POINT_THRESHOLD) {
          if (retryCount < MAX_RETRIES) {
            console.log(`Insufficient data (${data.length}), retrying in ${RETRY_DELAY_MS}ms...`);
            updateContainerStatus(container, 'loading', 'Loading more data...');

            // Retry after delay with exponential backoff
            setTimeout(() => {
              loadTemperatureData(deviceId, retryCount + 1);
            }, RETRY_DELAY_MS * (retryCount + 1));
            return;
          } else {
            // No more retries, display what we have or show empty message
            if (data && data.length > 0) {
              renderTemperatureChart(container, data);
            } else {
              updateContainerStatus(container, 'empty');
              // Create a visible error element that tests can find
              createVisibleErrorElement(container, 'No temperature history data available');
            }
          }
        } else {
          // We have enough data, render the chart
          renderTemperatureChart(container, data);

          // Add test marker for verification
          addTestVerification('temperature-chart-loaded', {
            deviceId: deviceId,
            dataPoints: data.length
          });
        }
      })
      .catch(error => {
        console.error(`Error loading temperature data: ${error.message}`);

        if (retryCount < MAX_RETRIES) {
          console.log(`Retrying after error in ${RETRY_DELAY_MS}ms...`);
          updateContainerStatus(container, 'loading', 'Retrying...');

          setTimeout(() => {
            loadTemperatureData(deviceId, retryCount + 1);
          }, RETRY_DELAY_MS * (retryCount + 1));
        } else {
          updateContainerStatus(container, 'error', error.message || 'Failed to load temperature data');

          // Add test marker for verification
          addTestVerification('temperature-chart-error-handled', {
            deviceId: deviceId,
            error: error.message
          });
        }
      });
  }

  function findOrCreateChartContainer() {
    // Determine which tab is active
    const historyContent = document.querySelector('#history-content');
    const detailsContent = document.querySelector('#details-content');

    let activeTab = null;
    let parent = null;

    if (historyContent && window.getComputedStyle(historyContent).display !== 'none') {
      activeTab = 'history';
      parent = historyContent;
    } else if (detailsContent && window.getComputedStyle(detailsContent).display !== 'none') {
      activeTab = 'details';
      parent = detailsContent;
    } else {
      // Default to details if we can't determine active tab
      activeTab = 'details';
      parent = detailsContent || document.querySelector('.main-content, main') || document.body;
    }

    console.log(`Active tab identified as: ${activeTab}`);

    // Look for existing container in the active tab
    let container = null;

    if (activeTab === 'history') {
      container = historyContent.querySelector('#temperature-chart, .temperature-history-chart');
    } else {
      container = detailsContent.querySelector('#temperature-chart, .temperature-history-chart');
    }

    // Return existing container if found
    if (container) {
      // Ensure the container has a canvas
      let canvas = container.querySelector('canvas');
      if (!canvas) {
        const chartContainer = container.querySelector('.chart-container') || container;
        canvas = document.createElement('canvas');
        canvas.width = 600;
        canvas.height = 300;
        chartContainer.appendChild(canvas);
      }

      // Clean up any existing chart instances on this canvas
      if (window.ChartInstanceManager && window.ChartInstanceManager.destroyChart && canvas.id) {
        window.ChartInstanceManager.destroyChart(canvas.id);
      }

      console.log(`Using existing chart container in ${activeTab} tab`);
      return container;
    }

    // No container found, create a new one
    console.log(`Creating new temperature chart container in ${activeTab} tab`);

    // Create container with better styling and structure
    container = document.createElement('div');
    container.id = 'temperature-chart';
    container.className = 'temperature-history-chart card';
    container.style.margin = '20px 0';
    container.style.padding = '15px';
    container.style.borderRadius = '4px';
    container.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';
    container.style.backgroundColor = '#fff';

    // Add proper heading and structured content
    container.innerHTML = `
      <h3 style="margin-top: 0; margin-bottom: 15px; color: #333;">Temperature History</h3>
      <div class="chart-container" style="position: relative; height: 300px; width: 100%;">
        <canvas width="600" height="300" style="display: block;"></canvas>
        <div class="chart-message loading" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); display: flex; align-items: center; justify-content: center;">
          <span style="background: rgba(255,255,255,0.9); padding: 10px 20px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">Loading temperature data...</span>
        </div>
      </div>
    `;

    // Find best position to insert container
    if (activeTab === 'history') {
      // For history tab, find period selectors and insert after them
      const periodSelectors = historyContent.querySelector('.period-selectors, [data-period]');
      if (periodSelectors) {
        parent.insertBefore(container, periodSelectors.nextSibling);
      } else {
        parent.appendChild(container);
      }
    } else {
      // For details tab, insert at top for visibility
      if (parent.firstChild) {
        parent.insertBefore(container, parent.firstChild);
      } else {
        parent.appendChild(container);
      }
    }

    console.log(`Created new temperature chart container in ${activeTab} tab`);

    return container;
  }

  function updateContainerStatus(container, status, message) {
    // Clear existing messages
    const existingMessages = container.querySelectorAll('.chart-message');
    existingMessages.forEach(el => el.style.display = 'none');

    // Find or create message element
    let messageEl = container.querySelector(`.chart-message.${status}`);
    if (!messageEl) {
      messageEl = document.createElement('div');
      messageEl.className = `chart-message ${status}`;
      container.querySelector('.chart-container').appendChild(messageEl);
    }

    // Set message content and show
    switch (status) {
      case 'loading':
        messageEl.innerHTML = `
          <div class="spinner"></div>
          <span>${message || 'Loading temperature data...'}</span>
        `;
        break;
      case 'error':
        messageEl.innerHTML = `
          <div class="alert alert-warning">
            <i class="fas fa-exclamation-triangle"></i>
            <span>${message || 'Error loading temperature data'}</span>
          </div>
        `;
        break;
      case 'empty':
        messageEl.innerHTML = `
          <div class="alert alert-info">
            <i class="fas fa-info-circle"></i>
            <span>No temperature history data available</span>
          </div>
        `;
        break;
    }

    messageEl.style.display = 'flex';

    // Hide or show canvas based on status
    const canvas = container.querySelector('canvas');
    if (canvas) {
      canvas.style.display = status === 'loading' ? 'none' : 'block';
    }
  }

  function renderTemperatureChart(container, data) {
    // Hide any messages
    const messages = container.querySelectorAll('.chart-message');
    messages.forEach(el => el.style.display = 'none');

    // Get canvas element
    const canvas = container.querySelector('canvas');
    if (!canvas) {
      console.error('Canvas element not found in container');
      return;
    }

    // Make canvas visible
    canvas.style.display = 'block';

    // Process data for chart
    const timestamps = [];
    const temperatures = [];

    // Sort by timestamp
    data.sort((a, b) => {
      const timeA = new Date(a.timestamp).getTime();
      const timeB = new Date(b.timestamp).getTime();
      return timeA - timeB;
    });

    // Extract data points
    data.forEach(point => {
      const date = new Date(point.timestamp);
      const formattedDate = `${date.getMonth()+1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;

      // Get temperature value from various possible formats
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

    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
      console.error('Chart.js not available, cannot render chart');
      updateContainerStatus(container, 'error', 'Chart.js library not available');
      return;
    }

    // Destroy existing chart if any
    if (canvas._chart) {
      canvas._chart.destroy();
    }

    // Create new chart
    canvas._chart = new Chart(canvas, {
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
        maintainAspectRatio: false,
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

    console.log('Temperature chart rendered successfully');
  }

  function refreshTemperatureChart(deviceId) {
    // Check if chart already exists and has data
    const container = document.querySelector('#temperature-chart, .temperature-history-chart');
    if (container) {
      const canvas = container.querySelector('canvas');
      if (canvas && canvas._chart && canvas._chart.data.datasets[0].data.length > 0) {
        console.log('Temperature chart already loaded, no need to refresh');
        return;
      }
    }

    // Reload data
    loadTemperatureData(deviceId, 0);
  }

  function addTestVerification(id, data) {
    // Create or update test element
    let testElement = document.getElementById(id);
    if (!testElement) {
      testElement = document.createElement('div');
      testElement.id = id;
      testElement.style.display = 'none';
      document.body.appendChild(testElement);
    }

    // Add test data
    testElement.dataset.verified = 'true';

    // Add each data property
    for (const [key, value] of Object.entries(data)) {
      testElement.dataset[key] = typeof value === 'object' ?
        JSON.stringify(value) : String(value);
    }

    console.log(`Test verification added: ${id}`);
  }
})();
