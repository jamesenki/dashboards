/**
 * Unified Chart Manager
 *
 * This script consolidates chart management functionality following proper architecture principles:
 * - Single responsibility: Manages all chart instances and their lifecycle
 * - Clean interfaces: Provides clear APIs for creating/updating charts
 * - Error handling: Properly manages and displays errors
 * - Performance: Reduces redundant DOM operations
 */

(function() {
  'use strict';

  // Configuration constants
  const CONFIG = {
    chartDefaultHeight: 300,
    chartDefaultWidth: 600,
    dataPointThreshold: 3,
    maxRetries: 2,
    retryDelayMs: 1000
  };

  // Chart registry to keep track of all chart instances
  const chartRegistry = {};

  // Initialize when the DOM is ready
  document.addEventListener('DOMContentLoaded', initialize);
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(initialize, 100);
  }

  function initialize() {
    console.log('🔄 Unified Chart Manager: Initializing');

    // Set up tab change listeners to manage chart lifecycle
    setupTabListeners();

    // Initialize any charts in the current active tab
    initializeActiveTabCharts();

    // Clean up any orphaned chart instances
    cleanupOrphanedCharts();

    // Export public API to window
    exposePublicApi();
  }

  function setupTabListeners() {
    // Find all tab elements
    const tabs = document.querySelectorAll('[data-tab], .nav-link, .nav-item');

    // Add click listeners to handle tab changes
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        // Give the DOM time to update after tab change
        setTimeout(() => {
          // Clean up charts in hidden tabs
          cleanupHiddenTabCharts();

          // Initialize charts in newly active tab
          initializeActiveTabCharts();
        }, 200);
      });
    });

    console.log(`🔄 Tab listeners set up for ${tabs.length} tabs`);
  }

  function initializeActiveTabCharts() {
    // Find active tab content
    const activeTab = getActiveTabContent();
    if (!activeTab) {
      console.warn('No active tab content found');
      return;
    }

    console.log(`🔄 Initializing charts in tab: ${activeTab.id}`);

    // Initialize temperature chart if in history or details tab
    if (activeTab.id === 'history-content' || activeTab.id === 'details-content') {
      const deviceId = getDeviceId();
      if (deviceId) {
        loadTemperatureChart(activeTab, deviceId);
      }
    }
  }

  function cleanupHiddenTabCharts() {
    // Find all tab content elements
    const tabContents = document.querySelectorAll('[id$="-content"]');

    // Check each tab content
    tabContents.forEach(tabContent => {
      // If the tab is hidden
      if (window.getComputedStyle(tabContent).display === 'none') {
        // Find all charts in this tab
        const canvases = tabContent.querySelectorAll('canvas');

        // Destroy chart instances
        canvases.forEach(canvas => {
          if (canvas.id && chartRegistry[canvas.id]) {
            destroyChart(canvas.id);
          }
        });
      }
    });
  }

  function cleanupOrphanedCharts() {
    // Check for any chart instances without visible canvases
    Object.keys(chartRegistry).forEach(chartId => {
      const canvas = document.getElementById(chartId);
      if (!canvas || window.getComputedStyle(canvas).display === 'none') {
        destroyChart(chartId);
      }
    });
  }

  function getActiveTabContent() {
    // Try to find the active tab content
    const tabContents = document.querySelectorAll('[id$="-content"]');

    // Return the first visible tab content
    for (const tabContent of tabContents) {
      if (window.getComputedStyle(tabContent).display !== 'none') {
        return tabContent;
      }
    }

    return null;
  }

  function getDeviceId() {
    // Try to extract device ID from URL
    const path = window.location.pathname;
    const matches = path.match(/\/water-heaters\/(wh-[a-zA-Z0-9]+)/);

    if (matches && matches[1]) {
      return matches[1];
    }

    // Fallback: look for device ID in the DOM
    const deviceIdEl = document.querySelector('[data-device-id]');
    if (deviceIdEl) {
      return deviceIdEl.dataset.deviceId;
    }

    return null;
  }

  // Temperature chart handling
  function loadTemperatureChart(container, deviceId) {
    // Find or create chart container
    const chartContainer = findOrCreateChartContainer(container);
    if (!chartContainer) {
      console.error('Failed to find or create chart container');
      return;
    }

    // Show loading state
    updateChartStatus(chartContainer, 'loading');

    // Check if DeviceShadowApi exists
    if (typeof DeviceShadowApi === 'undefined') {
      console.error('DeviceShadowApi not found, cannot load temperature data');
      updateChartStatus(chartContainer, 'error', 'API not available');
      return;
    }

    // Load data and render chart
    loadTemperatureData(chartContainer, deviceId, 0);
  }

  function loadTemperatureData(container, deviceId, retryCount) {
    console.log(`🔄 Loading temperature data for ${deviceId} (attempt ${retryCount + 1})`);

    // Get temperature history data
    const api = new DeviceShadowApi();
    api.getTemperatureHistory(deviceId, { limit: 100 })
      .then(response => {
        // Handle error responses
        if (response && response.detail) {
          console.error(`API error: ${response.detail}`);
          updateChartStatus(container, 'error', response.detail);
          return;
        }

        // Ensure response is an array
        const data = Array.isArray(response) ? response : [];
        console.log(`🔄 Loaded ${data.length} temperature data points`);

        // Handle insufficient data
        if (!data || data.length < CONFIG.dataPointThreshold) {
          if (retryCount < CONFIG.maxRetries) {
            console.log(`🔄 Insufficient data (${data.length}), retrying...`);
            updateChartStatus(container, 'loading', 'Loading more data...');

            // Retry after delay with exponential backoff
            setTimeout(() => {
              loadTemperatureData(container, deviceId, retryCount + 1);
            }, CONFIG.retryDelayMs * (retryCount + 1));
            return;
          } else {
            // No more retries, display what we have or show empty message
            if (data && data.length > 0) {
              renderTemperatureChart(container, data);
            } else {
              updateChartStatus(container, 'empty');
            }
          }
        } else {
          // We have enough data, render the chart
          renderTemperatureChart(container, data);
        }
      })
      .catch(error => {
        console.error('Error loading temperature data:', error);
        updateChartStatus(container, 'error', error.message);
      });
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

    // Ensure canvas has ID
    if (!canvas.id) {
      canvas.id = 'chart-' + new Date().getTime();
    }

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

    // Create or update chart
    createOrUpdateChart(canvas.id, {
      type: 'line',
      data: {
        labels: timestamps,
        datasets: [{
          label: 'Temperature (°F)',
          data: temperatures,
          borderColor: 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, 0.1)',
          tension: 0.1,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 500 // Faster animations
        },
        scales: {
          y: {
            beginAtZero: false,
            title: {
              display: true,
              text: 'Temperature (°F)'
            }
          },
          x: {
            title: {
              display: true,
              text: 'Date/Time'
            }
          }
        }
      }
    });

    // Mark container for test detection
    container.setAttribute('data-chart-rendered', 'true');
    canvas.setAttribute('data-chart-rendered', 'true');
  }

  // Container and status management
  function findOrCreateChartContainer(parentElement) {
    // First check if container already exists in parent
    let container = parentElement.querySelector('#temperature-chart, .temperature-chart-container');

    // Return existing container if found
    if (container) {
      return container;
    }

    // Create new container
    container = document.createElement('div');
    container.id = 'temperature-chart';
    container.className = 'temperature-chart-container';
    container.style.margin = '20px 0';
    container.style.padding = '15px';
    container.style.backgroundColor = '#fff';
    container.style.borderRadius = '4px';
    container.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';

    // Add structured HTML
    container.innerHTML = `
      <h3 style="margin-top: 0; margin-bottom: 15px;">Temperature History</h3>
      <div class="chart-container" style="position: relative; height: ${CONFIG.chartDefaultHeight}px; width: 100%;">
        <canvas width="${CONFIG.chartDefaultWidth}" height="${CONFIG.chartDefaultHeight}" style="display: block;"></canvas>
        <div class="chart-message loading" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); display: flex; align-items: center; justify-content: center; padding: 10px 20px; background: rgba(255,255,255,0.9); border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
          <span>Loading temperature data...</span>
        </div>
        <div class="chart-message error" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); display: none; padding: 10px 20px; background: #fff3cd; color: #856404; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #ffeeba;">
          <span>Error loading temperature data</span>
        </div>
        <div class="chart-message empty" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); display: none; padding: 10px 20px; background: #f8f9fa; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e9ecef;">
          <span>No temperature history data available</span>
        </div>
      </div>
    `;

    // Find a good insert position (for history tab, after period selectors)
    if (parentElement.id === 'history-content') {
      const periodSelectors = parentElement.querySelector('.period-selectors');
      if (periodSelectors) {
        parentElement.insertBefore(container, periodSelectors.nextSibling);
      } else {
        parentElement.appendChild(container);
      }
    } else {
      // For other tabs, insert at the top
      if (parentElement.firstChild) {
        parentElement.insertBefore(container, parentElement.firstChild);
      } else {
        parentElement.appendChild(container);
      }
    }

    return container;
  }

  function updateChartStatus(container, status, message) {
    // Find chart container wrapper
    const chartContainer = container.querySelector('.chart-container');
    if (!chartContainer) return;

    // Hide all message elements
    const messages = chartContainer.querySelectorAll('.chart-message');
    messages.forEach(el => el.style.display = 'none');

    // Show the appropriate message based on status
    const messageEl = chartContainer.querySelector(`.chart-message.${status}`);
    if (messageEl) {
      // Update message text if provided
      if (message) {
        const spanEl = messageEl.querySelector('span');
        if (spanEl) {
          spanEl.textContent = message;
        }
      }

      // Show the message
      messageEl.style.display = 'flex';
    }

    // Show/hide canvas based on status
    const canvas = chartContainer.querySelector('canvas');
    if (canvas) {
      canvas.style.display = status === 'loading' || status === 'error' || status === 'empty' ? 'none' : 'block';
    }
  }

  // Chart instance management
  function createOrUpdateChart(canvasId, config) {
    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
      console.error('Chart.js not available');
      const canvas = document.getElementById(canvasId);
      if (canvas) {
        const container = canvas.closest('.temperature-chart-container, .chart-container');
        if (container) {
          updateChartStatus(container, 'error', 'Chart.js library not available');
        }
      }
      return null;
    }

    // Destroy existing chart if any
    destroyChart(canvasId);

    // Get canvas element
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
      console.error(`Canvas not found: ${canvasId}`);
      return null;
    }

    // Create new chart
    const chart = new Chart(canvas, config);

    // Register in chart registry
    chartRegistry[canvasId] = chart;

    console.log(`🔄 Chart created: ${canvasId}`);
    return chart;
  }

  function destroyChart(canvasId) {
    // Check if chart exists in registry
    if (chartRegistry[canvasId]) {
      // Destroy chart
      chartRegistry[canvasId].destroy();
      delete chartRegistry[canvasId];
      console.log(`🔄 Chart destroyed: ${canvasId}`);
      return true;
    }

    // Also check for chart attached directly to canvas
    const canvas = document.getElementById(canvasId);
    if (canvas && canvas._chart) {
      canvas._chart.destroy();
      delete canvas._chart;
      console.log(`🔄 Direct chart destroyed: ${canvasId}`);
      return true;
    }

    return false;
  }

  function getChart(canvasId) {
    return chartRegistry[canvasId] || null;
  }

  function getAllCharts() {
    return { ...chartRegistry };
  }

  // Public API
  function exposePublicApi() {
    window.UnifiedChartManager = {
      createChart: createOrUpdateChart,
      destroyChart: destroyChart,
      getChart: getChart,
      getAllCharts: getAllCharts,
      loadTemperatureChart: (containerId, deviceId) => {
        const container = document.getElementById(containerId);
        if (container) {
          loadTemperatureChart(container, deviceId);
        }
      }
    };
  }
})();
