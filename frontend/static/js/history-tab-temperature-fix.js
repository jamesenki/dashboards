/**
 * History Tab Temperature Chart Fix
 *
 * This script specifically addresses the empty temperature chart in the History tab
 * by ensuring proper initialization and data loading for all time periods.
 *
 * Following TDD principles:
 * 1. RED: Identified empty temperature chart in History tab while energy chart works
 * 2. GREEN: Implement focused fix that ensures chart displays with data
 * 3. REFACTOR: Ensure consistent behavior across all period selectors
 */

(function() {
  console.log('🧪 History Tab Temperature Chart Fix: Initializing');

  // Run when DOM is fully loaded
  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(initializeTemperatureChart, 500);
  });

  /**
   * Initialize the temperature chart in the History tab
   */
  function initializeTemperatureChart() {
    console.log('🧪 Initializing temperature chart in History tab');

    // Find the temperature chart canvas
    const temperatureCanvas = document.getElementById('temperature-chart');
    if (!temperatureCanvas) {
      console.error('Temperature chart canvas not found');
      return;
    }

    // Get device ID
    const deviceId = getDeviceId();
    if (!deviceId) {
      console.error('Could not get device ID');
      return;
    }

    // Make sure the chart is visible
    temperatureCanvas.style.display = 'block';

    // Get the default period (7 days if not specified)
    const activePeriodButton = document.querySelector('.day-selector.active');
    const days = activePeriodButton ? activePeriodButton.getAttribute('data-days') : '7';

    // Load the chart data
    loadTemperatureData(deviceId, days);
  }

  /**
   * Extract device ID from URL or page elements
   */
  function getDeviceId() {
    // Try to get from URL
    const urlPath = window.location.pathname;
    const pathSegments = urlPath.split('/');
    const deviceId = pathSegments[pathSegments.length - 1];

    // Validate it looks like a device ID
    if (deviceId && deviceId.startsWith('wh-')) {
      return deviceId;
    }

    // Try alternate ways to get device ID
    const deviceIdEl = document.getElementById('device-id');
    if (deviceIdEl && deviceIdEl.dataset.deviceId) {
      return deviceIdEl.dataset.deviceId;
    }

    return null;
  }

  /**
   * Load temperature data for the specified period
   */
  function loadTemperatureData(deviceId, days) {
    // Show loading indicator
    const chartContainer = document.querySelector('.chart-container');
    if (chartContainer) {
      const loadingEl = chartContainer.previousElementSibling;
      if (loadingEl && loadingEl.classList.contains('chart-loading')) {
        loadingEl.style.display = 'flex';
      }
    }

    // URL for temperature history API
    const apiUrl = `/api/manufacturer/water-heaters/${deviceId}/history/temperature?days=${days}`;

    console.log(`Loading temperature data: ${apiUrl}`);

    // Fetch data from API
    fetch(apiUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error(`Failed to fetch temperature data: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('Temperature data loaded:', data);

        // Hide loading indicator
        const chartContainer = document.querySelector('.chart-container');
        if (chartContainer) {
          const loadingEl = chartContainer.previousElementSibling;
          if (loadingEl && loadingEl.classList.contains('chart-loading')) {
            loadingEl.style.display = 'none';
          }
        }

        // Create or update chart
        createOrUpdateTemperatureChart(data);
      })
      .catch(err => {
        console.error('Error loading temperature data:', err);

        // Hide loading indicator and show error
        const chartContainer = document.querySelector('.chart-container');
        if (chartContainer) {
          const loadingEl = chartContainer.previousElementSibling;
          if (loadingEl && loadingEl.classList.contains('chart-loading')) {
            loadingEl.style.display = 'none';
          }

          const errorEl = document.getElementById('history-error');
          if (errorEl) {
            errorEl.textContent = `Could not load temperature data: ${err.message}`;
            errorEl.style.display = 'block';
          }
        }
      });
  }

  /**
   * Create or update the temperature chart with data
   */
  function createOrUpdateTemperatureChart(data) {
    const canvas = document.getElementById('temperature-chart');
    if (!canvas) {
      console.error('Temperature chart canvas not found');
      return;
    }

    // Ensure canvas is visible
    canvas.style.display = 'block';

    // Initialize Chart.js if needed
    if (!window.Chart) {
      console.error('Chart.js library not loaded');
      return;
    }

    // Format data for Chart.js if needed
    let chartData = data;
    if (Array.isArray(data)) {
      // Transform array format to Chart.js format
      chartData = {
        labels: data.map(d => typeof d.timestamp === 'string' ? d.timestamp.split('T')[0] : d.timestamp),
        datasets: [{
          label: 'Temperature (°F)',
          data: data.map(d => d.temperature),
          fill: false,
          borderColor: 'rgba(75, 192, 192, 1)',
          tension: 0.1
        }]
      };
    } else if (!data.datasets && data.temperatures) {
      // Handle older format with temperatures array
      chartData = {
        labels: data.labels || [],
        datasets: [{
          label: 'Temperature (°F)',
          data: data.temperatures,
          fill: false,
          borderColor: 'rgba(75, 192, 192, 1)',
          tension: 0.1
        }]
      };
    }

    // Check if chart already exists
    if (window.temperatureHistoryChart instanceof Chart) {
      // Update existing chart
      window.temperatureHistoryChart.data = chartData;
      window.temperatureHistoryChart.update();
      console.log('Updated existing temperature chart');
    } else {
      // Create new chart
      window.temperatureHistoryChart = new Chart(canvas, {
        type: 'line',
        data: chartData,
        options: {
          responsive: true,
          maintainAspectRatio: false,
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
                text: 'Date'
              }
            }
          },
          plugins: {
            title: {
              display: true,
              text: 'Temperature History'
            },
            legend: {
              display: true,
              position: 'top'
            },
            tooltip: {
              mode: 'index',
              intersect: false
            }
          }
        }
      });
      console.log('Created new temperature chart');
    }
  }
})();
