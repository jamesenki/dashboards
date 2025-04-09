/**
 * Details Page Temperature History Fix
 *
 * This script specifically targets the temperature history chart on the details page
 * and ensures it displays either chart data or an error message.
 *
 * Following TDD principles:
 * 1. RED: Identified missing temperature history in details page but working in history tab
 * 2. GREEN: Implement direct solution for this specific element
 * 3. REFACTOR: Create robust error handling with consistent behavior across tabs
 */

(function() {
  // Execute immediately
  console.log('🔧 Details Page Temperature History Fix loaded');

  // Run on page load
  document.addEventListener('DOMContentLoaded', initializeDetailsPageFix);

  // Also run immediately in case the DOM is already loaded
  initializeDetailsPageFix();

  function initializeDetailsPageFix() {
    // Short delay to ensure DOM is ready
    setTimeout(fixDetailsPageTemperatureChart, 100);
  }

  function fixDetailsPageTemperatureChart() {
    console.log('Applying details page temperature chart fix...');

    // Get device ID from URL or data attribute
    const deviceId = getDeviceId();
    if (!deviceId) {
      console.log('No device ID found');
      return;
    }

    console.log(`Found device ID: ${deviceId}`);

    // Find the temperature chart container in the details page
    const chartContainer = document.getElementById('temperature-chart');
    if (!chartContainer) {
      console.log('Temperature chart container not found, retrying in 500ms');
      setTimeout(fixDetailsPageTemperatureChart, 500);
      return;
    }

    console.log('Found temperature chart container');

    // Check if container already has content
    if (chartContainer.querySelector('canvas') && chartContainer.querySelector('canvas').__chart) {
      console.log('Chart already initialized, skipping');
      return;
    }

    // If we made it here, we need to initialize the chart
    initializeChart(deviceId, chartContainer);
  }

  function getDeviceId() {
    // Try to get from data attribute first (most reliable)
    const detailElement = document.getElementById('water-heater-detail');
    if (detailElement && detailElement.dataset.deviceId) {
      return detailElement.dataset.deviceId;
    }

    // Try hidden input
    const deviceIdInput = document.getElementById('device-id');
    if (deviceIdInput && deviceIdInput.value) {
      return deviceIdInput.value;
    }

    // Extract from URL path pattern: /water-heaters/{id}
    const match = window.location.pathname.match(/\/water-heaters\/([^\/]+)/);
    if (match && match[1]) {
      return match[1];
    }

    // Fallback to query parameter
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('id');
  }

  function initializeChart(deviceId, container) {
    console.log(`Initializing details page temperature chart for ${deviceId}`);

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

    // Use the manufacturer endpoint that works in the history tab
    fetch(`/api/manufacturer/water-heaters/${deviceId}/history`)
      .then(response => {
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('No shadow document exists for this device');
          } else {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
        }
        return response.json();
      })
      .then(data => {
        console.log('History data received:', data);

        if (!data || !data.history || data.history.length === 0) {
          throw new Error('No temperature history data available');
        }

        const chartData = processTemperatureData(data);
        createChart(container, chartData);
      })
      .catch(error => {
        console.error('Error fetching temperature history:', error);

        // Show error in chart container
        showError(container, error.message);

        // Also check for shadow document error container and update it
        const errorContainer = document.querySelector('.shadow-document-error');
        if (errorContainer) {
          errorContainer.textContent = error.message;
          errorContainer.style.display = 'block';
        }
      })
      .finally(() => {
        removeLoading(container);
      });
  }

  function processTemperatureData(data) {
    const history = data.history || [];

    // Extract temperature data from history entries
    const labels = [];
    const temperatures = [];

    history.forEach(entry => {
      const timestamp = new Date(entry.timestamp);
      const formattedTime = timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

      labels.push(formattedTime);

      // Extract temperature from metrics object
      if (entry.metrics && typeof entry.metrics.temperature !== 'undefined') {
        temperatures.push(entry.metrics.temperature);
      } else {
        // Handle missing temperature data
        temperatures.push(null);
      }
    });

    return { labels, temperatures };
  }

  function createChart(container, data) {
    // Clear container first
    container.innerHTML = '';

    // Create a canvas element
    const canvas = document.createElement('canvas');
    container.appendChild(canvas);

    // Create the chart
    const ctx = canvas.getContext('2d');
    const chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.labels,
        datasets: [{
          label: 'Temperature (°C)',
          data: data.temperatures,
          borderColor: 'rgba(3, 169, 244, 1)',
          backgroundColor: 'rgba(3, 169, 244, 0.1)',
          borderWidth: 2,
          tension: 0.4,
          pointRadius: 3,
          fill: true,
          pointBackgroundColor: 'rgba(3, 169, 244, 1)'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            enabled: true,
            mode: 'index',
            intersect: false
          }
        },
        scales: {
          x: {
            grid: {
              display: false,
              color: 'rgba(255, 255, 255, 0.1)'
            },
            ticks: {
              color: 'rgba(255, 255, 255, 0.7)'
            }
          },
          y: {
            beginAtZero: false,
            grid: {
              display: false,
              color: 'rgba(255, 255, 255, 0.1)'
            },
            ticks: {
              color: 'rgba(255, 255, 255, 0.7)'
            }
          }
        },
        animation: {
          duration: 1000
        }
      }
    });

    // Store reference to chart instance on the canvas
    canvas.__chart = chart;

    console.log('Chart created successfully');
  }

  function showLoading(container) {
    // Clear container
    container.innerHTML = '';

    // Create loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'chart-loading';
    loadingDiv.style.cssText = `
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100%;
      width: 100%;
      flex-direction: column;
    `;

    const spinner = document.createElement('div');
    spinner.className = 'spinner';
    spinner.style.cssText = `
      border: 3px solid rgba(0, 0, 0, 0.1);
      border-radius: 50%;
      border-top: 3px solid #03A9F4;
      width: 30px;
      height: 30px;
      animation: spin 1s linear infinite;
      margin-bottom: 10px;
    `;

    const loadingText = document.createElement('div');
    loadingText.textContent = 'Loading temperature history...';
    loadingText.style.cssText = `
      color: rgba(255, 255, 255, 0.7);
      font-size: 14px;
    `;

    // Add animation style
    const styleElement = document.createElement('style');
    styleElement.textContent = `
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    `;
    document.head.appendChild(styleElement);

    // Assemble and add to container
    loadingDiv.appendChild(spinner);
    loadingDiv.appendChild(loadingText);
    container.appendChild(loadingDiv);
  }

  function removeLoading(container) {
    const loadingDiv = container.querySelector('.chart-loading');
    if (loadingDiv) {
      loadingDiv.remove();
    }
  }

  function showError(container, message) {
    // Clear container
    container.innerHTML = '';

    // Create error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.cssText = `
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100%;
      width: 100%;
      flex-direction: column;
      padding: 15px;
      text-align: center;
    `;

    const icon = document.createElement('div');
    icon.innerHTML = '⚠️';
    icon.style.cssText = `
      font-size: 24px;
      margin-bottom: 10px;
    `;

    const errorText = document.createElement('div');
    errorText.textContent = message || 'Failed to load temperature history';
    errorText.style.cssText = `
      color: rgba(255, 255, 255, 0.7);
      font-size: 14px;
    `;

    const retryButton = document.createElement('button');
    retryButton.textContent = 'Retry';
    retryButton.className = 'btn btn-sm btn-primary mt-3';
    retryButton.onclick = () => {
      // Clear error and try again
      container.innerHTML = '';
      const deviceId = getDeviceId();
      if (deviceId) {
        initializeChart(deviceId, container);
      }
    };

    // Assemble and add to container
    errorDiv.appendChild(icon);
    errorDiv.appendChild(errorText);
    errorDiv.appendChild(retryButton);
    container.appendChild(errorDiv);
  }
})();
