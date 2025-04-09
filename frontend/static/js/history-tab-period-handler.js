/**
 * History Tab Period Handler
 *
 * This script implements the functionality for switching between 7, 14, and 30-day
 * periods in the History tab, ensuring that temperature charts update correctly.
 *
 * Following TDD principles, this implementation addresses the requirement for
 * working period selectors (7, 14, and 30 days) in the History tab.
 */

(function() {
  // Run when the DOM is fully loaded
  document.addEventListener('DOMContentLoaded', function() {
    console.log('🧪 History Tab Period Handler: Initializing');
    initializePeriodSelectors();
  });

  /**
   * Initialize period selectors for the History tab
   */
  function initializePeriodSelectors() {
    // Find period selector buttons
    const periodSelectors = document.querySelectorAll('.day-selector, [data-days]');
    if (!periodSelectors || periodSelectors.length === 0) {
      console.log('❌ History Tab Period Handler: No period selectors found');
      return;
    }

    console.log(`✅ History Tab Period Handler: Found ${periodSelectors.length} period selectors`);

    // Get device ID
    const deviceIdElement = document.getElementById('water-heater-detail');
    if (!deviceIdElement) {
      console.log('❌ History Tab Period Handler: No device ID element found');
      return;
    }

    // Extract device ID
    const urlPath = window.location.pathname;
    const pathSegments = urlPath.split('/');
    const deviceId = pathSegments[pathSegments.length - 1];

    if (!deviceId) {
      console.log('❌ History Tab Period Handler: Could not extract device ID');
      return;
    }

    console.log(`✅ History Tab Period Handler: Using device ID: ${deviceId}`);

    // Add click event handler to each period selector
    periodSelectors.forEach(selector => {
      // Get the period value (days)
      const days = selector.getAttribute('data-days');
      if (!days) {
        return;
      }

      // Add click event handler
      selector.addEventListener('click', function(event) {
        // Prevent default behavior if it's an anchor tag
        event.preventDefault();

        // Update active state
        periodSelectors.forEach(s => s.classList.remove('active'));
        selector.classList.add('active');

        // Trigger loading state
        const chartContainer = document.querySelector('.chart-container');
        if (chartContainer) {
          const loadingElement = document.querySelector('.chart-loading');
          if (loadingElement) {
            loadingElement.style.display = 'flex';
          }
        }

        // Fetch and update chart data for the selected period
        updateTemperatureChart(deviceId, days);

        console.log(`✅ History Tab Period Handler: Selected ${days}-day period`);
      });

      console.log(`✅ History Tab Period Handler: Added event handler for ${days}-day period`);
    });

    // Initialize with default period (first one with active class or first in list)
    const activeSelector = Array.from(periodSelectors).find(s => s.classList.contains('active'));
    const defaultSelector = activeSelector || periodSelectors[0];
    const defaultDays = defaultSelector.getAttribute('data-days');

    if (defaultDays) {
      console.log(`✅ History Tab Period Handler: Using default period of ${defaultDays} days`);
      // Initialize chart with default period
      updateTemperatureChart(deviceId, defaultDays);
    }
  }

  /**
   * Update temperature chart with data for the selected period
   *
   * @param {string} deviceId - Device ID
   * @param {string} days - Number of days to show
   */
  function updateTemperatureChart(deviceId, days) {
    // Get the API URL
    let apiUrl = `/api/manufacturer/water-heaters/${deviceId}/history/temperature?days=${days}`;

    // Show loading indicator
    const chartContainer = document.querySelector('.chart-container');
    if (chartContainer) {
      const canvas = chartContainer.querySelector('canvas');
      if (canvas) {
        canvas.style.opacity = '0.5';
      }
    }

    // Fetch data from API
    fetch(apiUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        // Hide loading indicator
        const loadingElement = document.querySelector('.chart-loading');
        if (loadingElement) {
          loadingElement.style.display = 'none';
        }

        // Update chart with new data
        if (window.temperatureChart) {
          try {
            // If the chart has a loadData or updateData method, use it
            if (typeof window.temperatureChart.loadData === 'function') {
              window.temperatureChart.loadData(data);
            } else if (typeof window.temperatureChart.updateData === 'function') {
              window.temperatureChart.updateData(data);
            } else {
              // Otherwise, try to update the chart directly
              if (window.temperatureChart.chart) {
                const chart = window.temperatureChart.chart;

                // Check if we got data in Chart.js format or data points format
                if (data.datasets) {
                  // Format is Chart.js ready
                  chart.data = data;
                } else if (Array.isArray(data)) {
                  // Format is data points - need to transform
                  const formattedData = {
                    labels: data.map(d => d.timestamp),
                    datasets: [{
                      label: 'Temperature',
                      data: data.map(d => d.temperature),
                      borderColor: 'rgba(3, 169, 244, 1)',
                      backgroundColor: 'rgba(3, 169, 244, 0.1)',
                    }]
                  };
                  chart.data = formattedData;
                }

                chart.update();
              }
            }

            // Show the chart
            const canvas = document.getElementById('temperature-chart');
            if (canvas) {
              canvas.style.display = 'block';
              canvas.style.opacity = '1';
            }

            console.log(`✅ History Tab Period Handler: Updated chart with ${days}-day data`);
          } catch (error) {
            console.error('Error updating chart:', error);
          }
        } else {
          console.error('Temperature chart not initialized');
        }
      })
      .catch(error => {
        console.error('Error fetching temperature history:', error);

        // Hide loading indicator
        const loadingElement = document.querySelector('.chart-loading');
        if (loadingElement) {
          loadingElement.style.display = 'none';
        }

        // Show error message
        const errorElement = document.getElementById('history-error');
        if (errorElement) {
          errorElement.textContent = `Could not load temperature data: ${error.message}`;
          errorElement.style.display = 'block';
        }
      });
  }
})();
