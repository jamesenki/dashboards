/**
 * Direct Fix for Temperature History Box
 *
 * This script directly targets the temperature history box on the details page
 * and ensures it displays either chart data or an error message.
 *
 * Following TDD principles:
 * 1. RED: Identified missing temperature history in box
 * 2. GREEN: Implement direct solution for this specific element
 * 3. REFACTOR: Create robust error handling
 */

(function() {
  // Execute immediately
  console.log('🔧 Direct Temperature History Box Fix loaded');

  // Run on page load
  document.addEventListener('DOMContentLoaded', initializeHistoryBoxFix);

  // Also run immediately in case the DOM is already loaded
  initializeHistoryBoxFix();

  function initializeHistoryBoxFix() {
    // Short delay to ensure DOM is ready
    setTimeout(fixTemperatureHistoryBox, 100);
  }

  function fixTemperatureHistoryBox() {
    console.log('Direct Temperature History Box Fix - DISABLED FOR DETAILS PAGE');
    console.log('Temperature history is now ONLY available in the History tab');

    // Check if we're on the details page or history tab
    const isDetailsPage = window.location.pathname.includes('/water-heaters/') &&
                         !window.location.pathname.includes('/history');

    // Skip initialization on details page
    if (isDetailsPage) {
      console.log('Skipping temperature history chart on details page - by design');
      return;
    }

    // Continue only for history tab
    console.log('On history tab, proceeding with temperature chart initialization');

    // Get device ID from URL
    const deviceId = getDeviceIdFromUrl();
    if (!deviceId) {
      console.log('No device ID found in URL');
      return;
    }

    console.log(`Found device ID: ${deviceId}`);

    // Only look for temperature chart in history tab content
    const historyContent = document.getElementById('history-content');
    if (!historyContent) {
      console.log('History tab content not found');
      return;
    }

    const chartContainer = historyContent.querySelector('#temperature-chart');
    if (!chartContainer) {
      console.log('Temperature chart container not found in history tab, retrying in 500ms');
      setTimeout(fixTemperatureHistoryBox, 500);
      return;
    }

    console.log('Found temperature chart container in history tab');

    // Check if container already has content
    if (chartContainer.querySelector('canvas') || chartContainer.querySelector('.error-message')) {
      console.log('Chart already initialized, skipping');
      return;
    }

    // If we made it here, we need to initialize the chart
    initializeChart(deviceId, chartContainer);
  }

  function getDeviceIdFromUrl() {
    // Extract device ID from URL path pattern: /water-heaters/{id}
    const match = window.location.pathname.match(/\/water-heaters\/([^\/]+)/);
    if (match && match[1]) {
      return match[1];
    }

    // Fallback to query parameter
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('id');
  }

  function initializeChart(deviceId, container) {
    console.log(`Initializing temperature history chart for ${deviceId}`);

    // Add loading indicator
    showLoading(container);

    // Load Chart.js if not already loaded
    if (typeof Chart === 'undefined') {
      loadChartJs(() => fetchDataAndCreateChart(deviceId, container));
    } else {
      fetchDataAndCreateChart(deviceId, container);
    }
  }

  function loadChartJs(callback) {
    console.log('Loading Chart.js');
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
    script.onload = callback;
    document.head.appendChild(script);
  }

  function fetchDataAndCreateChart(deviceId, container) {
    console.log(`Fetching temperature history data for ${deviceId}`);

    // Direct API call to get temperature history
    fetch(`/api/device-shadows/${deviceId}/history`)
      .then(response => {
        if (!response.ok) {
          if (response.status === 404) {
            // Try timeseries endpoint as fallback
            return fetch(`/api/device-shadows/${deviceId}/time-series?limit=100`);
          }
          throw new Error(`API request failed with status ${response.status}`);
        }
        return response;
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`API request failed with status ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log(`Received ${data.length} temperature history points`);

        if (data.length === 0) {
          showError(container, 'No temperature history data available');
          return;
        }

        // Process the data
        const chartData = processTemperatureData(data);

        // Create chart
        createChart(container, chartData);

        // Add verification element for testing
        const testStatus = document.createElement('div');
        testStatus.id = 'temperature-history-box-fixed';
        testStatus.style.display = 'none';
        testStatus.dataset.pointsLoaded = data.length;
        document.body.appendChild(testStatus);

        console.log('VERIFICATION: Temperature history box fixed');
      })
      .catch(error => {
        console.error('Error fetching temperature history:', error);

        // Try shadow document as a fallback
        fetch(`/api/device-shadows/${deviceId}`)
          .then(response => response.ok ? response.json() : null)
          .then(shadow => {
            if (shadow && shadow.history && shadow.history.length > 0) {
              console.log(`Retrieved ${shadow.history.length} history points from shadow document`);
              const chartData = processTemperatureData(shadow.history);
              createChart(container, chartData);
            } else {
              // Show error message
              const errorMessage = error.message.includes('No shadow document')
                ? 'No shadow document exists for this device'
                : 'Failed to load temperature history data';

              showError(container, errorMessage);
            }
          })
          .catch(e => {
            showError(container, 'Failed to load temperature history data');
          });
      });
  }

  function processTemperatureData(data) {
    // Extract timestamps and temperatures, handling different data formats
    const timestamps = [];
    const temperatures = [];

    // Sort data by timestamp
    data.sort((a, b) => {
      const timestampA = new Date(a.timestamp);
      const timestampB = new Date(b.timestamp);
      return timestampA - timestampB;
    });

    // Process each data point
    data.forEach(point => {
      // Format date for display
      const date = new Date(point.timestamp);
      const formattedDate = `${date.getMonth()+1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;

      // Extract temperature from various possible formats
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

    return { timestamps, temperatures };
  }

  function createChart(container, data) {
    console.log('Creating temperature history chart');

    // Remove loading indicator
    removeLoading(container);

    // Create canvas element for chart
    const canvas = document.createElement('canvas');
    container.appendChild(canvas);

    // Create chart instance
    const chart = new Chart(canvas, {
      type: 'line',
      data: {
        labels: data.timestamps,
        datasets: [{
          label: 'Temperature (°F)',
          data: data.temperatures,
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.1)',
          tension: 0.1,
          fill: true
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

    // Store chart instance for reference
    container.chart = chart;
    console.log('✅ Temperature history chart created successfully');
  }

  function showLoading(container) {
    // Clear container
    container.innerHTML = '';

    // Add loading indicator
    const loading = document.createElement('div');
    loading.className = 'loading-indicator';
    loading.innerHTML = `
      <div class="spinner"></div>
      <p>Loading temperature history...</p>
    `;

    // Add CSS styles directly
    const style = document.createElement('style');
    style.textContent = `
      .loading-indicator {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        padding: 20px;
      }
      .spinner {
        border: 4px solid rgba(0, 0, 0, 0.1);
        border-radius: 50%;
        border-top: 4px solid #3498db;
        width: 30px;
        height: 30px;
        animation: spin 1s linear infinite;
        margin-bottom: 10px;
      }
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    `;
    document.head.appendChild(style);

    container.appendChild(loading);
  }

  function removeLoading(container) {
    const loading = container.querySelector('.loading-indicator');
    if (loading) {
      loading.remove();
    }
  }

  function showError(container, message) {
    console.log(`Showing error message: ${message}`);

    // Clear container
    container.innerHTML = '';

    // Create error message element
    const error = document.createElement('div');
    error.className = 'error-message';
    error.innerHTML = `
      <div class="alert alert-warning">
        <i class="fas fa-exclamation-triangle"></i>
        <span>${message}</span>
      </div>
    `;

    // Add CSS styles directly
    const style = document.createElement('style');
    style.textContent = `
      .error-message {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        padding: 20px;
      }
      .alert {
        padding: 15px;
        border: 1px solid transparent;
        border-radius: 4px;
        width: 100%;
        text-align: center;
      }
      .alert-warning {
        color: #8a6d3b;
        background-color: #fcf8e3;
        border-color: #faebcc;
      }
    `;
    document.head.appendChild(style);

    container.appendChild(error);

    // Add verification element for testing
    const testStatus = document.createElement('div');
    testStatus.id = 'temperature-history-error-handled';
    testStatus.style.display = 'none';
    testStatus.dataset.errorMessage = message;
    document.body.appendChild(testStatus);
  }
})();
