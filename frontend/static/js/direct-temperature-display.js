/**
 * Direct Temperature History Display Fix
 *
 * Following TDD principles:
 * 1. RED: Confirmed temperature history not displaying
 * 2. GREEN: Add minimal code to make it display
 * 3. REFACTOR: Make it maintainable
 */
(function() {
  // Run immediately on load
  console.log('Direct Temperature Display Fix - Running');

  // Execute as soon as DOM is ready
  document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - initializing temperature history display');
    setTimeout(initTemperatureDisplay, 100);
  });

  // Also run now in case DOM is already loaded
  setTimeout(initTemperatureDisplay, 100);

  function initTemperatureDisplay() {
    // Get device ID from URL or data attribute
    const deviceId = getDeviceId();
    if (!deviceId) {
      console.error('No device ID found');
      return;
    }

    console.log('Found device ID:', deviceId);

    // Get temperature chart container - specifically target the right one
    // Try both main targets based on the diagnostics
    const temperatureChartContainers = [
      document.getElementById('temperature-history-chart'),
      document.getElementById('temperature-chart')
    ];

    let container = null;
    for (const candidate of temperatureChartContainers) {
      if (candidate && !hasContent(candidate)) {
        container = candidate;
        console.log('Using container:', container.id);
        break;
      }
    }

    if (!container) {
      console.error('No suitable temperature chart container found');
      // Retry after a delay as the DOM might still be loading
      setTimeout(initTemperatureDisplay, 500);
      return;
    }

    // Display loading indicator
    showLoading(container);

    // Fetch shadow document directly
    fetchShadowDocument(deviceId)
      .then(shadowData => {
        if (shadowData && shadowData.history && shadowData.history.length > 0) {
          console.log(`Got ${shadowData.history.length} history points from shadow`);
          displayTemperatureChart(container, shadowData.history);
        } else {
          showError(container, 'No temperature history data available');
        }
      })
      .catch(error => {
        console.error('Error fetching shadow document:', error);
        showError(container, 'Failed to load temperature history');
      });
  }

  function getDeviceId() {
    // Try from URL first
    const urlMatch = window.location.pathname.match(/\/water-heaters\/([^\/]+)/);
    if (urlMatch && urlMatch[1]) {
      return urlMatch[1];
    }

    // Try from data attribute
    const detailElement = document.getElementById('water-heater-detail');
    if (detailElement && detailElement.dataset.deviceId) {
      return detailElement.dataset.deviceId;
    }

    // Try from hidden input
    const idInput = document.getElementById('device-id');
    if (idInput && idInput.value) {
      return idInput.value;
    }

    return null;
  }

  function hasContent(container) {
    // Check if container already has chart or error content
    return container.querySelector('canvas') ||
           container.querySelector('.error-message') ||
           container.querySelector('.chart-error');
  }

  function fetchShadowDocument(deviceId) {
    console.log(`Fetching shadow document for ${deviceId}`);
    return fetch(`/api/device-shadows/${deviceId}`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`Shadow API returned ${response.status}`);
        }
        return response.json();
      });
  }

  function displayTemperatureChart(container, historyData) {
    console.log('Displaying temperature chart with', historyData.length, 'points');

    // Clear container
    container.innerHTML = '';

    // Ensure Chart.js is loaded
    if (typeof Chart === 'undefined') {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
      script.onload = () => createChart(container, historyData);
      document.head.appendChild(script);
    } else {
      createChart(container, historyData);
    }
  }

  function createChart(container, historyData) {
    // Process history data for chart
    const chartData = processHistoryData(historyData);

    // Create canvas for chart
    const canvas = document.createElement('canvas');
    container.appendChild(canvas);

    // Create chart
    new Chart(canvas, {
      type: 'line',
      data: {
        labels: chartData.labels,
        datasets: [{
          label: 'Temperature (°F)',
          data: chartData.temperatures,
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
          y: {
            title: {
              display: true,
              text: 'Temperature (°F)'
            }
          },
          x: {
            title: {
              display: true,
              text: 'Time'
            }
          }
        }
      }
    });

    // Add verification element for testing
    const verification = document.createElement('div');
    verification.id = 'temperature-chart-verification';
    verification.setAttribute('data-points', chartData.temperatures.length);
    verification.style.display = 'none';
    document.body.appendChild(verification);

    console.log('Temperature chart created successfully');
  }

  function processHistoryData(history) {
    // Extract timestamps and temperatures from history data
    const labels = [];
    const temperatures = [];

    // Sort by timestamp (newest first)
    const sortedHistory = [...history].sort((a, b) => {
      return new Date(b.timestamp) - new Date(a.timestamp);
    });

    // Process each data point
    sortedHistory.slice(0, 100).forEach(point => {
      // Format timestamp
      const date = new Date(point.timestamp);
      const formattedTime = `${date.getMonth()+1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`;

      // Extract temperature value
      let temp = null;
      if (point.metrics && point.metrics.temperature) {
        temp = point.metrics.temperature;
      } else if (point.temperature) {
        temp = point.temperature;
      } else if (point.value) {
        temp = point.value;
      }

      if (temp !== null) {
        labels.push(formattedTime);
        temperatures.push(temp);
      }
    });

    return {
      labels: labels,
      temperatures: temperatures
    };
  }

  function showLoading(container) {
    container.innerHTML = `
      <div class="loading-indicator" style="display:flex; align-items:center; justify-content:center; height:100%;">
        <div style="text-align:center;">
          <div class="spinner" style="border:4px solid rgba(0,0,0,0.1); border-radius:50%; border-top:4px solid #3498db; width:30px; height:30px; animation:spin 1s linear infinite; margin:0 auto;"></div>
          <p style="margin-top:10px;">Loading temperature history...</p>
        </div>
      </div>
      <style>
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      </style>
    `;
  }

  function showError(container, message) {
    container.innerHTML = `
      <div class="error-message" style="display:flex; align-items:center; justify-content:center; height:100%; padding:20px;">
        <div style="text-align:center; background-color:#fff3cd; color:#856404; padding:15px; border-radius:4px; width:100%;">
          <p style="margin:0;">${message}</p>
        </div>
      </div>
    `;

    // Add verification element for testing
    const verification = document.createElement('div');
    verification.id = 'temperature-chart-error';
    verification.setAttribute('data-message', message);
    verification.style.display = 'none';
    document.body.appendChild(verification);
  }
})();
