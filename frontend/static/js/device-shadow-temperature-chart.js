/**
 * Device Shadow Temperature History Chart
 *
 * A specialized chart component for displaying temperature history data from device shadows
 * This implementation handles MongoDB shadow data structure
 */

class DeviceShadowTemperatureChart {
  /**
   * Initialize the temperature history chart
   * @param {string} elementId - The ID of the element to render the chart in
   * @param {string} deviceId - The device ID to fetch history for
   * @param {Object} options - Chart options
   */
  constructor(elementId, deviceId, options = {}) {
    this.elementId = elementId;
    this.chartElement = document.getElementById(elementId);
    this.containerElement = null; // Container element for the chart
    this.deviceId = deviceId;
    this.errorElement = null;
    this.chart = null;
    this.api = new DeviceShadowApi();
    this.data = {
      labels: [],
      temperatures: []
    };

    // Debug initialization
    console.log(`Initializing temperature chart for element: ${elementId}, device: ${deviceId}`);
    if (!this.chartElement) {
      console.warn(`Chart element with ID '${elementId}' not found on initial load, will try again during initialization`);
    }

    this.options = Object.assign({
      title: 'Temperature History',
      color: 'rgba(3, 169, 244, 1)',
      backgroundColor: 'rgba(3, 169, 244, 0.1)',
      dataPoints: 24,
      days: 7,
      showLegend: false,
      displayGrid: false,
      errorSelector: '.shadow-document-error',
      autoRefresh: false,
      refreshInterval: 60 * 1000, // 1 minute
    }, options);

    // Initialize chart
    this.initialize();
  }

  /**
   * Initialize the chart component
   */
  async initialize() {
    // Try to find the chart element again if it wasn't found in constructor
    if (!this.chartElement) {
      console.log(`Attempting to find chart element with ID '${this.elementId}' again`);
      this.chartElement = document.getElementById(this.elementId);

      if (!this.chartElement) {
        console.error(`Chart element with ID '${this.elementId}' not found during initialization`);

        // Try to find the container element by class instead
        const containers = document.querySelectorAll('.temperature-chart-container, .chart-container');
        if (containers.length > 0) {
          console.log(`Found ${containers.length} potential chart containers, using the first one`);
          this.chartElement = containers[0];
        } else {
          console.error('No temperature chart containers found');
          return;
        }
      }
    }

    // Find the container element (might be the chart element itself or a parent)
    this.containerElement = this.chartElement.closest('.chart-container') ||
                            this.chartElement.closest('.temperature-chart-container') ||
                            this.chartElement.parentElement;

    // Find error element
    this.findErrorElement();

    // Initialize chart
    this.initializeChart();

    // Load data
    try {
      await this.loadTemperatureHistory();

      // Setup auto-refresh if enabled
      if (this.options.autoRefresh) {
        this.setupAutoRefresh();
      }
    } catch (error) {
      this.handleError(error);
    }
  }

  /**
   * Find error element for displaying errors
   */
  findErrorElement() {
    // Find the closest error element to the chart
    if (this.chartElement) {
      // First check for an existing error element within the chart
      this.errorElement = this.chartElement.querySelector(this.options.errorSelector);

      // If not found in chart, look in parent containers
      if (!this.errorElement) {
        const parent = this.chartElement.closest('.card') || this.chartElement.parentElement;
        this.errorElement = parent.querySelector(this.options.errorSelector);
      }

      // If still not found, try to find globally
      if (!this.errorElement) {
        this.errorElement = document.querySelector(this.options.errorSelector);
      }

      // Create an error element if none exists
      if (!this.errorElement) {
        this.errorElement = document.createElement('div');
        this.errorElement.className = 'shadow-document-error';
        this.errorElement.style.display = 'none';

        // Add to chart container
        this.chartElement.parentNode.insertBefore(this.errorElement, this.chartElement.nextSibling);
      }
    }
  }

  /**
   * Initialize the chart
   */
  initializeChart() {
    // Create a canvas element if needed
    let canvas = this.chartElement.querySelector('canvas');
    if (!canvas) {
      console.log('Creating new canvas element for temperature chart');
      canvas = document.createElement('canvas');
      canvas.id = `${this.elementId}-canvas`;
      canvas.classList.add('temperature-chart-canvas');

      // Set explicit dimensions to ensure chart is visible
      canvas.width = this.chartElement.clientWidth || 400;
      canvas.height = this.chartElement.clientHeight || 200;

      // Ensure the canvas is visible
      canvas.style.display = 'block';
      canvas.style.maxWidth = '100%';

      this.chartElement.appendChild(canvas);
    } else {
      console.log(`Found existing canvas for temperature chart: ${canvas.id}`);
    }

    // Store reference to canvas
    this.chartCanvas = canvas;

    // Ensure canvas is visible
    canvas.style.display = 'block';

    const ctx = canvas.getContext('2d');

    this.chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: this.data.labels,
        datasets: [{
          label: this.options.title,
          data: this.data.temperatures,
          borderColor: this.options.color,
          backgroundColor: this.options.backgroundColor,
          borderWidth: 2,
          tension: 0.4,
          pointRadius: 3,
          fill: true,
          pointBackgroundColor: this.options.color
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: this.options.showLegend
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
              display: this.options.displayGrid,
              color: 'rgba(255, 255, 255, 0.1)'
            },
            ticks: {
              color: 'rgba(255, 255, 255, 0.7)'
            }
          },
          y: {
            beginAtZero: false,
            grid: {
              display: this.options.displayGrid,
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
  }

  /**
   * Load temperature history data from the API
   */
  async loadTemperatureHistory() {
    try {
      console.log(`Loading temperature history for device ${this.deviceId}...`);
      // Reset data
      this.data.labels = [];
      this.data.temperatures = [];

      // Get history data from API
      console.log(`Requesting temperature history with options:`, {
        days: this.options.days,
        limit: this.options.dataPoints
      });
      const history = await this.api.getTemperatureHistory(this.deviceId, {
        days: this.options.days,
        limit: this.options.dataPoints
      });

      console.log(`Received temperature history data:`, history);

      // Check if we have data
      if (!history || !history.length) {
        throw new Error('No temperature history data available');
      }

      // Process and add the data
      history.forEach(entry => {
        // Format date for display
        const date = new Date(entry.timestamp);
        const label = date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

        // Add to data arrays
        this.data.labels.push(label);
        this.data.temperatures.push(entry.temperature);
      });

      // Reverse data to show oldest first
      this.data.labels.reverse();
      this.data.temperatures.reverse();

      // Update chart
      this.updateChart();
      this.hideError();

      return true;
    } catch (error) {
      this.handleError(error);
      return false;
    }
  }

  /**
   * Set the number of days for the temperature history and refresh the chart
   * @param {number} days - Number of days to display (7, 14, or 30)
   */
  async setDays(days) {
    console.log(`Setting temperature chart period to ${days} days`);

    // Update the days option
    this.options.days = days;

    // Reload data with new period
    await this.loadTemperatureHistory();

    return this;
  }

  /**
   * Update the chart with current data
   */
  updateChart() {
    if (!this.chart) {
      console.warn('Chart not initialized yet, attempting to initialize it now');
      this.initializeChart();
      if (!this.chart) {
        console.error('Failed to initialize chart');
        return;
      }
    }

    // Update chart data
    this.chart.data.labels = this.data.labels;
    this.chart.data.datasets[0].data = this.data.temperatures;

    // Update chart
    this.chart.update();
  }

  /**
   * Handle errors, showing appropriate messages
   * @param {Error} error - The error that occurred
   */
  handleError(error) {
    console.error('Device shadow temperature chart error:', error);

    // Extract error message
    let errorMessage = error.message || 'Error loading temperature data';

    // Notify the diagnostics system if available
    if (window.diagnostics && typeof window.diagnostics.logError === 'function') {
      window.diagnostics.logError('TemperatureChart', errorMessage);
    }

    // Handle specific error types with more visibility
    if (errorMessage.includes('No shadow document exists')) {
      console.warn(`⚠️ No shadow document exists for device ${this.deviceId}. Showing error message.`);
      this.showShadowDocumentError();

      // Make sure chart container is hidden
      if (this.chartElement) {
        this.chartElement.style.display = 'none';
      }

      // Attempt to notify parent components about the error for better visibility
      if (typeof window.dispatchEvent === 'function') {
        window.dispatchEvent(new CustomEvent('shadow-document-error', {
          detail: { deviceId: this.deviceId, error: errorMessage }
        }));
      }
    } else {
      this.showError(errorMessage);
    }
  }

  /**
   * Show a specific shadow document error
   */
  showShadowDocumentError() {
    // Improved error message with warning icon and better visibility
    const errorHtml = `
      <div style="text-align: center; padding: 20px; background-color: rgba(231, 76, 60, 0.1); border: 2px solid #e74c3c; border-radius: 6px; margin: 15px 0;">
        <div style="font-size: 32px; margin-bottom: 15px; color: #e74c3c;">⚠️</div>
        <h4 style="color: #e74c3c; margin-bottom: 15px; font-weight: bold; font-size: 18px;">Temperature History Unavailable</h4>
        <p style="margin-bottom: 12px; font-size: 15px;">No shadow document exists for device <strong>${this.deviceId}</strong>.</p>
        <p style="margin-bottom: 8px; font-size: 14px;">Temperature history cannot be displayed until the device has reported data.</p>
        <p><small style="color: #7f8c8d; font-size: 13px;">This typically happens when a device is new or has been reset.</small></p>
      </div>
    `;

    // Update error element
    if (this.errorElement) {
      this.errorElement.innerHTML = errorHtml;
      this.errorElement.style.display = 'block';
    }

    // Hide the chart
    if (this.chartElement) {
      this.chartElement.style.display = 'none';
    }
  }

  /**
   * Show a generic error message
   * @param {string} message - Error message to display
   */
  showError(message) {
    if (this.errorElement) {
      this.errorElement.textContent = message;
      this.errorElement.style.display = 'block';
    }

    // Hide the chart
    if (this.chartElement) {
      this.chartElement.style.display = 'none';
    }
  }

  /**
   * Hide the error message
   */
  hideError() {
    if (this.errorElement) {
      this.errorElement.style.display = 'none';
    }

    // Show the chart
    if (this.chartElement) {
      this.chartElement.style.display = 'block';
    }
  }

  /**
   * Set up auto-refresh for the chart
   */
  setupAutoRefresh() {
    this.refreshTimer = setInterval(() => {
      this.loadTemperatureHistory().catch(error => {
        console.warn('Auto-refresh error:', error);
      });
    }, this.options.refreshInterval);
  }

  /**
   * Clean up resources used by the chart
   */
  destroy() {
    // Clear refresh timer
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }

    // Destroy chart
    if (this.chart) {
      this.chart.destroy();
    }
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DeviceShadowTemperatureChart;
}
