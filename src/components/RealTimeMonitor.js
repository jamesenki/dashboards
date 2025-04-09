/**
 * Real-Time Monitor Component
 * Displays real-time device data and connection status
 * Implemented following TDD principles based on test requirements
 */

class RealTimeMonitor {
  constructor(deviceId, containerSelector, options = {}) {
    this.deviceId = deviceId;
    this.container = document.querySelector(containerSelector);
    this.options = Object.assign({
      temperatureUnit: 'F',
      showConnectionStatus: true,
      showReconnectMessage: true,
      historyChartEnabled: true,
      maxHistoryPoints: 20,
      refreshInterval: 5000
    }, options);

    this.monitor = new RealTimeMonitor({
      baseUrl: this.options.baseUrl || 'ws://localhost:8000',
      maxReconnectAttempts: this.options.maxReconnectAttempts || 5
    });

    this.historyData = [];
    this.isConnected = false;

    // Initialize the component
    this._initialize();
  }

  /**
   * Initialize the monitor component
   */
  _initialize() {
    if (!this.container) {
      console.error('Container element not found');
      return false;
    }

    // Create UI elements
    this._createUIElements();

    // Set up event listeners for real-time updates
    this._setupEventListeners();

    // Connect to the device
    this.connect();

    return true;
  }

  /**
   * Create UI elements for the monitor
   */
  _createUIElements() {
    // Clear container
    this.container.innerHTML = '';

    // Add component wrapper
    this.componentWrapper = document.createElement('div');
    this.componentWrapper.className = 'real-time-monitor';
    this.container.appendChild(this.componentWrapper);

    // Create temperature display
    this.temperatureDisplay = document.createElement('div');
    this.temperatureDisplay.className = 'temperature-display';
    this.temperatureDisplay.innerHTML = `<span class="temperature-value">--°${this.options.temperatureUnit}</span>`;
    this.componentWrapper.appendChild(this.temperatureDisplay);

    // Create connection status indicator if enabled
    if (this.options.showConnectionStatus) {
      this.statusIndicator = document.createElement('div');
      this.statusIndicator.className = 'connection-status disconnected';
      this.statusIndicator.textContent = 'disconnected';
      this.componentWrapper.appendChild(this.statusIndicator);
    }

    // Create reconnection message container if enabled
    if (this.options.showReconnectMessage) {
      this.reconnectMessage = document.createElement('div');
      this.reconnectMessage.className = 'reconnect-message';
      this.reconnectMessage.style.display = 'none';
      this.componentWrapper.appendChild(this.reconnectMessage);
    }

    // Create history chart if enabled
    if (this.options.historyChartEnabled) {
      this.historyChartContainer = document.createElement('div');
      this.historyChartContainer.className = 'temperature-history-chart';
      this.historyChartContainer.setAttribute('data-device-id', this.deviceId);
      this.componentWrapper.appendChild(this.historyChartContainer);

      // Initialize empty chart with placeholder
      this._initializeHistoryChart();
    }
  }

  /**
   * Initialize the temperature history chart
   */
  _initializeHistoryChart() {
    this.historyChartContainer.innerHTML = `
      <div class="chart-header">Temperature History</div>
      <div class="chart-content">
        <svg class="chart-svg" width="100%" height="200">
          <g class="chart-grid"></g>
          <g class="chart-data"></g>
          <g class="chart-axis"></g>
        </svg>
      </div>
    `;

    // Store reference to chart elements
    this.chartSvg = this.historyChartContainer.querySelector('.chart-svg');
    this.chartData = this.historyChartContainer.querySelector('.chart-data');

    // Add initial "No data" message
    const noDataText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    noDataText.setAttribute('x', '50%');
    noDataText.setAttribute('y', '50%');
    noDataText.setAttribute('text-anchor', 'middle');
    noDataText.setAttribute('class', 'no-data-text');
    noDataText.textContent = 'No temperature data available';
    this.chartData.appendChild(noDataText);
  }

  /**
   * Set up event listeners for real-time updates
   */
  _setupEventListeners() {
    // Listen for temperature updates
    this.monitor.addEventListener('temperature', this._handleTemperatureUpdate.bind(this));

    // Listen for connection status changes
    this.monitor.addEventListener('connectionChange', this._handleConnectionChange.bind(this));

    // Listen for errors
    this.monitor.addEventListener('error', this._handleError.bind(this));
  }

  /**
   * Connect to the device
   */
  connect() {
    if (this.deviceId) {
      // Update UI to show connecting state
      if (this.statusIndicator) {
        this.statusIndicator.className = 'connection-status connecting';
        this.statusIndicator.textContent = 'connecting';
      }

      // Connect to the device
      this.monitor.connect(this.deviceId);
    } else {
      console.error('Device ID not provided');
      this._handleError({ message: 'Device ID not provided' });
    }
  }

  /**
   * Disconnect from the device
   */
  disconnect() {
    this.monitor.disconnect();
  }

  /**
   * Handle temperature update events
   * @param {Object} data - Temperature update data
   */
  _handleTemperatureUpdate(data) {
    // Update temperature display
    const tempValueEl = this.temperatureDisplay.querySelector('.temperature-value');
    if (tempValueEl) {
      tempValueEl.textContent = data.formatted || `${data.value}°${data.unit || this.options.temperatureUnit}`;
    }

    // Add data point to history
    this._addHistoryDataPoint({
      value: data.value,
      timestamp: data.timestamp || new Date().toISOString()
    });

    // Update history chart if enabled
    if (this.options.historyChartEnabled && this.historyChartContainer) {
      this._updateHistoryChart();
    }

    // Dispatch custom event for tests
    this.container.dispatchEvent(new CustomEvent('temperature-updated', {
      detail: data,
      bubbles: true
    }));
  }

  /**
   * Handle connection status change events
   * @param {Object} data - Connection status data
   */
  _handleConnectionChange(data) {
    const status = data.status;
    this.isConnected = status === 'connected';

    // Update status indicator if enabled
    if (this.statusIndicator) {
      // Remove all status classes
      this.statusIndicator.className = 'connection-status';
      // Add current status class
      this.statusIndicator.classList.add(status);
      this.statusIndicator.textContent = status;
    }

    // Show reconnection message if reconnecting and enabled
    if (this.reconnectMessage && this.options.showReconnectMessage) {
      if (status === 'reconnecting') {
        this.reconnectMessage.textContent = `Attempting to reconnect (${data.attempt}/${data.maxAttempts})...`;
        this.reconnectMessage.style.display = 'block';
      } else {
        this.reconnectMessage.style.display = 'none';
      }
    }

    // Dispatch custom event for tests
    this.container.dispatchEvent(new CustomEvent('connection-changed', {
      detail: data,
      bubbles: true
    }));
  }

  /**
   * Handle error events
   * @param {Object} data - Error data
   */
  _handleError(data) {
    console.error('Real-time monitor error:', data.message, data.details);

    // Create error element if it doesn't exist
    if (!this.errorElement) {
      this.errorElement = document.createElement('div');
      this.errorElement.className = 'error-message';
      this.componentWrapper.appendChild(this.errorElement);
    }

    // Display error message
    this.errorElement.textContent = data.message;
    this.errorElement.style.display = 'block';

    // Dispatch custom event for tests
    this.container.dispatchEvent(new CustomEvent('monitor-error', {
      detail: data,
      bubbles: true
    }));
  }

  /**
   * Add data point to temperature history
   * @param {Object} dataPoint - Temperature data point
   */
  _addHistoryDataPoint(dataPoint) {
    // Add new data point
    this.historyData.push(dataPoint);

    // Limit history size
    if (this.historyData.length > this.options.maxHistoryPoints) {
      this.historyData.shift();
    }

    // Set last updated timestamp
    this.historyChartContainer.setAttribute('data-last-updated', new Date().toISOString());

    // Create a hidden data point element for testing
    const dataPointEl = document.createElement('div');
    dataPointEl.className = 'data-point';
    dataPointEl.dataset.value = dataPoint.value;
    dataPointEl.dataset.timestamp = dataPoint.timestamp;
    dataPointEl.style.display = 'none';
    this.historyChartContainer.appendChild(dataPointEl);
  }

  /**
   * Update the temperature history chart
   */
  _updateHistoryChart() {
    if (!this.historyChartContainer || this.historyData.length === 0) {
      return;
    }

    // Remove "No data" message if it exists
    const noDataText = this.chartData.querySelector('.no-data-text');
    if (noDataText) {
      noDataText.remove();
    }

    // Clear existing chart data
    this.chartData.innerHTML = '';

    // Get chart dimensions
    const chartWidth = this.chartSvg.clientWidth;
    const chartHeight = this.chartSvg.clientHeight;
    const padding = { top: 20, right: 20, bottom: 30, left: 40 };
    const graphWidth = chartWidth - padding.left - padding.right;
    const graphHeight = chartHeight - padding.top - padding.bottom;

    // Calculate min and max values
    const values = this.historyData.map(d => parseFloat(d.value));
    const minValue = Math.min(...values) * 0.9;
    const maxValue = Math.max(...values) * 1.1;

    // Create scale functions
    const xScale = (index) => padding.left + (index / (this.historyData.length - 1)) * graphWidth;
    const yScale = (value) => padding.top + graphHeight - ((value - minValue) / (maxValue - minValue)) * graphHeight;

    // Create path for line chart
    let pathData = '';
    this.historyData.forEach((point, index) => {
      const x = xScale(index);
      const y = yScale(parseFloat(point.value));
      pathData += (index === 0 ? 'M' : 'L') + `${x},${y}`;
    });

    // Create line path
    const linePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    linePath.setAttribute('d', pathData);
    linePath.setAttribute('class', 'line');
    linePath.setAttribute('fill', 'none');
    linePath.setAttribute('stroke', '#1e88e5');
    linePath.setAttribute('stroke-width', '2');
    this.chartData.appendChild(linePath);

    // Create data points
    this.historyData.forEach((point, index) => {
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', xScale(index));
      circle.setAttribute('cy', yScale(parseFloat(point.value)));
      circle.setAttribute('r', '4');
      circle.setAttribute('class', 'data-point');
      circle.setAttribute('fill', '#1e88e5');
      this.chartData.appendChild(circle);
    });

    // Add a last updated timestamp for testing
    this.historyChartContainer.classList.add('updated');
  }

  /**
   * Get the current history data
   * @returns {Array} - Temperature history data
   */
  getHistoryData() {
    return [...this.historyData];
  }

  /**
   * Get the current connection status
   * @returns {boolean} - Whether the monitor is connected
   */
  isConnected() {
    return this.isConnected;
  }
}

// Export the component for use in the application
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { RealTimeMonitor };
} else {
  // For browser use
  window.RealTimeMonitorComponent = RealTimeMonitor;
}
