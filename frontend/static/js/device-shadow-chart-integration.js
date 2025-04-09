/**
 * Device Shadow Temperature Chart Integration
 *
 * This script integrates the device shadow temperature chart with the IoTSphere UI.
 * It automatically detects temperature chart containers on pages and initializes
 * the appropriate charts using the device shadow API.
 */

(function() {
  console.log('🔧 Device Shadow Temperature Chart Integration loaded');

  // Run on DOM loaded
  document.addEventListener('DOMContentLoaded', function() {
    // Small delay to ensure other scripts have loaded
    setTimeout(initializeCharts, 500);
  });

  // Initialize charts on URL change (for SPAs)
  window.addEventListener('popstate', function() {
    setTimeout(initializeCharts, 500);
  });

  // Also run immediately in case the DOM is already loaded
  initializeCharts();

  /**
   * Initialize temperature charts on the page
   */
  function initializeCharts() {
    // First check if we're on a details page by looking for device ID in the URL or the DOM
    const deviceId = getDeviceIdFromPage();
    if (!deviceId) {
      return;
    }

    // Check if charts are already initialized
    if (window._temperatureChartsInitialized) {
      return;
    }

    // Look for temperature chart containers, but only initialize one in each location
    initializeDetailsPageChart(deviceId);
    initializeHistoryTabChart(deviceId);

    // Mark as initialized to prevent duplication
    window._temperatureChartsInitialized = true;
  }

  /**
   * Get device ID from the current page
   * @returns {string|null} - Device ID or null if not found
   */
  function getDeviceIdFromPage() {
    // Try to get from URL first
    const urlMatch = window.location.pathname.match(/water-heaters\/([^/]+)/);
    if (urlMatch && urlMatch[1]) {
      return urlMatch[1];
    }

    // Try to get from hidden input or data attribute
    const deviceIdInput = document.querySelector('input[name="device_id"], [data-device-id]');
    if (deviceIdInput) {
      return deviceIdInput.value || deviceIdInput.getAttribute('data-device-id');
    }

    // Try to get from heading (often contains device name which might have ID)
    const heading = document.querySelector('h1, h2');
    if (heading) {
      const text = heading.textContent;
      const idMatch = text.match(/\b(wh-[a-z0-9]+)\b/i);
      if (idMatch) {
        return idMatch[1];
      }
    }

    return null;
  }

  /**
   * Initialize temperature chart on the details page
   * @param {string} deviceId - Device ID
   */
  function initializeDetailsPageChart(deviceId) {
    // Check if a chart is already initialized in the details area
    if (document.querySelector('#details-content canvas')) {
      return;
    }

    // Find PRIMARY temperature chart container first
    let container = document.getElementById('temperature-chart');

    // If primary container not found, then look for secondary options
    if (!container) {
      const chartContainers = [
        document.querySelector('.temperature-history-chart'),
        document.querySelector('[data-chart="temperature-history"]'),
        document.getElementById('temp-chart'),
        document.querySelector('#details-content .card-chart'),
        document.querySelector('#temperature-history-container')
      ].filter(Boolean); // Remove null/undefined entries

      container = chartContainers[0]; // Use the first container found
    }

    // If still no container, create a fallback one
    if (!container) {
      const detailsSection = document.querySelector('#details-content') || document.body;
      const emergencyContainer = document.createElement('div');
      emergencyContainer.id = 'temperature-chart';
      emergencyContainer.className = 'temperature-history-chart';
      emergencyContainer.style.height = '300px';
      emergencyContainer.style.marginTop = '20px';
      detailsSection.appendChild(emergencyContainer);
      container = emergencyContainer;
    }

    console.log(`Found temperature chart container: #${container.id || 'unnamed'}`);

    // Check if we already have a chart
    if (container._chart) {
      return;
    }

    // Create our chart
    try {
      // Clear any existing content (like error messages)
      container.innerHTML = '';

      // Add a data attribute to mark this as the primary chart
      container.setAttribute('data-primary-chart', 'true');

      // Create the chart instance
      const chart = new DeviceShadowTemperatureChart(container.id || 'temperature-chart', deviceId, {
        title: 'Temperature History',
        dataPoints: 24,
        days: 7
      });

      // Store reference to prevent re-initialization
      container._chart = chart;
      window._detailsChartInitialized = true;
    } catch (error) {
      console.error('Error initializing temperature chart:', error);
    }
  }

  /**
   * Initialize temperature chart on the history tab
   * @param {string} deviceId - Device ID
   */
  function initializeHistoryTabChart(deviceId) {
    console.log('Initializing history tab temperature chart for device:', deviceId);

    // Find the history tab content
    const historyContent = document.getElementById('history-content');
    if (!historyContent) {
      console.log('History content not found');
      return;
    }

    // Find the temperature chart canvas
    const tempCanvas = document.getElementById('temperature-chart');
    if (!tempCanvas) {
      console.log('Temperature chart canvas not found');
      return;
    }

    // Make sure the canvas is visible
    tempCanvas.style.display = 'block';
    tempCanvas.style.visibility = 'visible';
    tempCanvas.style.opacity = '1';

    // Find the chart container
    let container = tempCanvas.parentElement;
    if (!container) {
      console.log('Chart container not found');
      return;
    }

    // Create our chart
    try {
      console.log('Creating temperature chart...');

      // Check if we already have a chart instance
      if (window.temperatureChart) {
        console.log('Chart already exists, updating...');
        return;
      }

      // Get the active period
      const activeSelector = document.querySelector('.day-selector.active');
      const days = activeSelector ? activeSelector.getAttribute('data-days') || '7' : '7';

      console.log(`Initializing chart with ${days} days of data`);

      // Create the chart instance directly on the canvas
      window.temperatureChart = new DeviceShadowTemperatureChart('temperature-chart', deviceId, {
        title: 'Temperature History',
        dataPoints: 48,
        days: parseInt(days),
        displayGrid: true
      });

      // Set up period selector event handlers
      setupPeriodSelectors(deviceId);

      // Store reference to prevent re-initialization
      container._chart = window.temperatureChart;
      window._historyTabChartInitialized = true;
    } catch (error) {
      console.error('Error initializing history tab temperature chart:', error);
    }
  }

  /**
   * Set up period selector buttons (7, 14, 30 days) in the History tab
   * @param {string} deviceId - Device ID
   */
  function setupPeriodSelectors(deviceId) {
    const periodSelectors = document.querySelectorAll('.day-selector');
    if (!periodSelectors || periodSelectors.length === 0) {
      console.log('No period selectors found');
      return;
    }

    console.log(`Found ${periodSelectors.length} period selectors`);

    // Add click handler to each selector
    periodSelectors.forEach(selector => {
      selector.addEventListener('click', function() {
        // Get the selected period
        const days = this.getAttribute('data-days');
        if (!days) return;

        console.log(`Period selector clicked: ${days} days`);

        // Update active state
        periodSelectors.forEach(s => s.classList.remove('active'));
        this.classList.add('active');

        // Show loading indicator
        const chartContainer = document.querySelector('.chart-container');
        if (chartContainer) {
          const loadingEl = chartContainer.previousElementSibling;
          if (loadingEl && loadingEl.classList.contains('chart-loading')) {
            loadingEl.style.display = 'flex';
          }
        }

        // Update the chart with the new period
        if (window.temperatureChart && window.temperatureChart.setDays) {
          window.temperatureChart.setDays(parseInt(days));

          // Hide loading indicator after chart updates
          setTimeout(() => {
            const loadingEl = document.querySelector('.chart-loading');
            if (loadingEl) {
              loadingEl.style.display = 'none';
            }
          }, 500);
        }
      });
    });

    console.log('Period selectors initialized');
  }
})();
