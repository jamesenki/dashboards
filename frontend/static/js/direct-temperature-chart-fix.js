/**
 * Direct Temperature Chart Fix
 *
 * This script forces the temperature chart in the History tab to be visible
 * and properly initialized, following the TDD approach:
 *
 * 1. RED: Our diagnostics confirmed the canvas exists but is not visible
 * 2. GREEN: This script provides the minimal implementation to make the chart visible
 * 3. REFACTOR: The solution is isolated and doesn't interfere with other functionality
 */

(function() {
  console.log('🧪 Direct Temperature Chart Fix: Initializing');

  // Execute immediately
  document.addEventListener('DOMContentLoaded', function() {
    setTimeout(fixTemperatureChart, 500);

    // Also run whenever history tab is clicked
    document.querySelectorAll('[data-tab="history"]').forEach(btn => {
      btn.addEventListener('click', function() {
        setTimeout(fixTemperatureChart, 500);
      });
    });
  });

  /**
   * Fix temperature chart in History tab
   */
  function fixTemperatureChart() {
    console.log('🧪 Direct Temperature Chart Fix: Running fix');

    // 1. Find temperature chart canvas and make it visible
    const canvas = document.getElementById('temperature-chart');
    if (canvas) {
      // Force visibility
      canvas.style.display = 'block';
      canvas.style.visibility = 'visible';
      canvas.style.opacity = '1';
      console.log('✅ Chart canvas forced to be visible');
    } else {
      console.log('❌ Temperature chart canvas not found');
      return;
    }

    // 2. Get device ID
    const deviceId = getDeviceId();
    if (!deviceId) {
      console.error('❌ Could not determine device ID');
      return;
    }

    // 3. Get active period
    const activeSelector = document.querySelector('.day-selector.active');
    const days = activeSelector ? activeSelector.getAttribute('data-days') || '7' : '7';

    // 4. Force create chart with data from API
    createTemperatureHistoryChart(deviceId, days);
  }

  /**
   * Extract device ID from URL
   */
  function getDeviceId() {
    const urlPath = window.location.pathname;
    const pathSegments = urlPath.split('/');
    const deviceId = pathSegments[pathSegments.length - 1];

    if (deviceId && deviceId.startsWith('wh-')) {
      return deviceId;
    }

    const deviceIdEl = document.getElementById('device-id');
    if (deviceIdEl && deviceIdEl.dataset.deviceId) {
      return deviceIdEl.dataset.deviceId;
    }

    return null;
  }

  /**
   * Create temperature history chart
   */
  function createTemperatureHistoryChart(deviceId, days) {
    console.log(`🧪 Creating temperature chart for device ${deviceId}, ${days} days`);

    // Show loading indicator
    const chartContainer = document.querySelector('.chart-container');
    if (chartContainer) {
      const loadingEl = chartContainer.previousElementSibling;
      if (loadingEl && loadingEl.classList.contains('chart-loading')) {
        loadingEl.style.display = 'flex';
      }
    }

    // Fetch temperature history data
    const apiUrl = `/api/manufacturer/water-heaters/${deviceId}/history/temperature?days=${days}`;
    fetch(apiUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('✅ Got temperature data:', data);

        // Hide loading indicator
        if (chartContainer) {
          const loadingEl = chartContainer.previousElementSibling;
          if (loadingEl && loadingEl.classList.contains('chart-loading')) {
            loadingEl.style.display = 'none';
          }
        }

        // Format chart data
        let chartData = formatChartData(data);

        // Initialize chart
        const canvas = document.getElementById('temperature-chart');

        // Destroy existing chart instance if it exists
        if (window.temperatureChart && window.temperatureChart.destroy) {
          window.temperatureChart.destroy();
        }

        // Create new Chart.js instance
        window.temperatureChart = new Chart(canvas, {
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

        console.log('✅ Temperature chart created successfully');
      })
      .catch(error => {
        console.error('❌ Error creating temperature chart:', error);

        // Hide loading indicator and show error
        if (chartContainer) {
          const loadingEl = chartContainer.previousElementSibling;
          if (loadingEl) {
            loadingEl.style.display = 'none';
          }

          // Show error message
          const errorEl = document.getElementById('history-error');
          if (errorEl) {
            errorEl.textContent = `Could not load temperature data: ${error.message}`;
            errorEl.style.display = 'block';
          }
        }
      });
  }

  /**
   * Format chart data for Chart.js
   */
  function formatChartData(data) {
    // Handle different possible data formats
    if (Array.isArray(data)) {
      // Array of objects with timestamp and temperature
      return {
        labels: data.map(item => {
          return typeof item.timestamp === 'string'
            ? item.timestamp.split('T')[0] // Extract date part only
            : item.timestamp;
        }),
        datasets: [{
          label: 'Temperature (°F)',
          data: data.map(item => item.temperature),
          borderColor: 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          tension: 0.1
        }]
      };
    } else if (data.datasets) {
      // Already in Chart.js format
      return data;
    } else if (data.labels && (data.temperatures || data.data)) {
      // Custom format with labels and temperatures/data arrays
      return {
        labels: data.labels,
        datasets: [{
          label: 'Temperature (°F)',
          data: data.temperatures || data.data,
          borderColor: 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          tension: 0.1
        }]
      };
    }

    // Fallback to empty chart with warning
    console.warn('❌ Unknown data format received:', data);
    return {
      labels: [],
      datasets: [{
        label: 'Temperature (°F)',
        data: [],
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)'
      }]
    };
  }

  // Add event listeners to period selectors
  document.addEventListener('DOMContentLoaded', function() {
    // Wait for DOM and other scripts to initialize
    setTimeout(function() {
      const periodSelectors = document.querySelectorAll('.day-selector');
      periodSelectors.forEach(selector => {
        selector.addEventListener('click', function() {
          // Get active period
          const days = this.getAttribute('data-days');
          if (!days) return;

          // Update active state
          periodSelectors.forEach(s => s.classList.remove('active'));
          this.classList.add('active');

          // Get device ID and create chart
          const deviceId = getDeviceId();
          if (deviceId) {
            createTemperatureHistoryChart(deviceId, days);
          }
        });
      });
    }, 800);
  });
})();
