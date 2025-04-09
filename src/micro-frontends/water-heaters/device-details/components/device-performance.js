/**
 * Device Performance Component
 *
 * Displays performance metrics and historical data for a water heater device
 * Part of the device-agnostic IoTSphere platform architecture
 */
export class DevicePerformance extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });

    // Component state
    this.device = null;
    this.deviceId = null;
    this.telemetryService = null;
    this.isLoading = true;
    this.error = null;

    // Historical data
    this.historyData = {
      temperature: [],
      energyUsage: [],
      efficiency: []
    };

    // Chart instances (will be populated when charts are created)
    this.charts = {};

    // Date range selection
    this.selectedRange = '24h'; // Default to 24 hours
    this.availableRanges = [
      { id: '24h', label: 'Last 24 Hours' },
      { id: '7d', label: 'Last 7 Days' },
      { id: '30d', label: 'Last 30 Days' },
      { id: 'custom', label: 'Custom Range' }
    ];

    // Custom date range (if selected)
    this.customRange = {
      startDate: null,
      endDate: null
    };
  }

  /**
   * Initialize the component
   */
  initialize({ device, deviceId, telemetryService }) {
    this.device = device;
    this.deviceId = deviceId || (device ? device.device_id : null);
    this.telemetryService = telemetryService;

    this.render();

    // Don't load data immediately since the Performance tab may not be visible initially
    // Data will be loaded when the tab becomes visible via the refresh() method
  }

  /**
   * Called when the element is connected to the DOM
   */
  connectedCallback() {
    this.render();
  }

  /**
   * Load historical data for the current date range
   */
  async loadHistoricalData() {
    if (!this.deviceId || !this.telemetryService) return;

    this.isLoading = true;
    this.error = null;
    this.render();

    try {
      // Calculate date range based on selected option
      const { startTime, endTime } = this.calculateTimeRange();

      // Fetch historical telemetry data
      const historyOptions = {
        startTime,
        endTime,
        limit: 1000 // Adjust based on API capabilities
      };

      const historyData = await this.telemetryService.getHistoricalTelemetry(
        this.deviceId,
        historyOptions
      );

      // Process and organize the data for charts
      this.processHistoricalData(historyData);

      this.isLoading = false;
      this.render();

      // Initialize charts after rendering
      this.initializeCharts();

      return historyData;
    } catch (error) {
      console.error('Error loading historical data:', error);
      this.error = 'Failed to load historical data. Please try again.';
      this.isLoading = false;
      this.render();

      return null;
    }
  }

  /**
   * Process raw historical data into format needed for charts
   */
  processHistoricalData(rawData) {
    // Since we don't have actual API data, we'll simulate the data processing
    // In a real implementation, this would process the API response

    // For demonstration, we'll generate synthetic data if no API data is available
    if (!rawData || !Array.isArray(rawData) || rawData.length === 0) {
      this.generateSyntheticData();
      return;
    }

    // Process actual API data
    // Extract temperature data points
    this.historyData.temperature = rawData
      .filter(point => point.temperature_current !== undefined)
      .map(point => ({
        timestamp: new Date(point.timestamp),
        value: point.temperature_current
      }))
      .sort((a, b) => a.timestamp - b.timestamp);

    // Extract energy usage data points
    this.historyData.energyUsage = rawData
      .filter(point => point.power_consumption_watts !== undefined)
      .map(point => ({
        timestamp: new Date(point.timestamp),
        value: point.power_consumption_watts / 1000 // Convert to kW
      }))
      .sort((a, b) => a.timestamp - b.timestamp);

    // Extract efficiency data points
    this.historyData.efficiency = rawData
      .filter(point => point.efficiency_rating !== undefined)
      .map(point => ({
        timestamp: new Date(point.timestamp),
        value: point.efficiency_rating
      }))
      .sort((a, b) => a.timestamp - b.timestamp);
  }

  /**
   * Generate synthetic data for demonstration
   */
  generateSyntheticData() {
    const { startTime, endTime } = this.calculateTimeRange();
    const start = new Date(startTime).getTime();
    const end = new Date(endTime).getTime();

    // Determine data point interval based on date range
    let interval;
    const timeSpan = end - start;

    if (timeSpan <= 24 * 60 * 60 * 1000) {
      // For 24 hours or less, use 15-minute intervals
      interval = 15 * 60 * 1000;
    } else if (timeSpan <= 7 * 24 * 60 * 60 * 1000) {
      // For 7 days or less, use 2-hour intervals
      interval = 2 * 60 * 60 * 1000;
    } else {
      // For longer periods, use 6-hour intervals
      interval = 6 * 60 * 60 * 1000;
    }

    // Generate timestamps for the data points
    const timestamps = [];
    for (let time = start; time <= end; time += interval) {
      timestamps.push(new Date(time));
    }

    // Generate temperature data
    const baseTemp = 120; // Base temperature in F
    this.historyData.temperature = timestamps.map(timestamp => {
      const hourOfDay = timestamp.getHours();
      // Simulate daily temperature fluctuations with higher temps in evening
      const timeVariation = Math.sin((hourOfDay - 6) * Math.PI / 12) * 5;
      // Add some random noise
      const noise = (Math.random() - 0.5) * 3;
      return {
        timestamp,
        value: baseTemp + timeVariation + noise
      };
    });

    // Generate energy usage data
    const baseUsage = 2.5; // Base usage in kW
    this.historyData.energyUsage = timestamps.map(timestamp => {
      const hourOfDay = timestamp.getHours();
      // Simulate higher usage in morning and evening
      const morningPeak = Math.max(0, 1.5 - Math.abs(hourOfDay - 7)) * 1.5;
      const eveningPeak = Math.max(0, 1.5 - Math.abs(hourOfDay - 19)) * 2;
      // Add some random noise
      const noise = (Math.random() - 0.5) * 0.8;
      return {
        timestamp,
        value: baseUsage + morningPeak + eveningPeak + noise
      };
    });

    // Generate efficiency data
    const baseEfficiency = 92; // Base efficiency percentage
    this.historyData.efficiency = timestamps.map(timestamp => {
      // Add some random noise
      const noise = (Math.random() - 0.5) * 4;
      return {
        timestamp,
        value: Math.min(100, Math.max(80, baseEfficiency + noise))
      };
    });
  }

  /**
   * Calculate start and end times based on selected range
   */
  calculateTimeRange() {
    const endTime = new Date();
    let startTime;

    switch (this.selectedRange) {
      case '24h':
        startTime = new Date(endTime);
        startTime.setHours(endTime.getHours() - 24);
        break;
      case '7d':
        startTime = new Date(endTime);
        startTime.setDate(endTime.getDate() - 7);
        break;
      case '30d':
        startTime = new Date(endTime);
        startTime.setDate(endTime.getDate() - 30);
        break;
      case 'custom':
        if (this.customRange.startDate && this.customRange.endDate) {
          startTime = new Date(this.customRange.startDate);
          // For custom range, end time is the end of the selected day
          endTime.setHours(23, 59, 59, 999);
          return {
            startTime: startTime.toISOString(),
            endTime: endTime.toISOString()
          };
        } else {
          // Fallback to 24h if custom range is incomplete
          startTime = new Date(endTime);
          startTime.setHours(endTime.getHours() - 24);
        }
        break;
      default:
        startTime = new Date(endTime);
        startTime.setHours(endTime.getHours() - 24);
    }

    return {
      startTime: startTime.toISOString(),
      endTime: endTime.toISOString()
    };
  }

  /**
   * Initialize chart visualizations
   */
  initializeCharts() {
    // In a real implementation, this would use a charting library like Chart.js
    // For this demonstration, we'll simulate the charts with basic HTML/CSS

    this.renderTemperatureChart();
    this.renderEnergyUsageChart();
    this.renderEfficiencyChart();
  }

  /**
   * Render the temperature chart
   */
  renderTemperatureChart() {
    if (!this.historyData.temperature.length) return;

    const container = this.shadowRoot.querySelector('#temperature-chart');
    if (!container) return;

    const data = this.historyData.temperature;

    // Find min/max values for scaling
    const values = data.map(d => d.value);
    const minTemp = Math.floor(Math.min(...values) - 5);
    const maxTemp = Math.ceil(Math.max(...values) + 5);

    // Generate bar chart HTML
    const chartHtml = this.generateChartHtml(
      data,
      'Temperature History',
      minTemp,
      maxTemp,
      value => `${value.toFixed(1)}°F`
    );

    container.innerHTML = chartHtml;
  }

  /**
   * Render the energy usage chart
   */
  renderEnergyUsageChart() {
    if (!this.historyData.energyUsage.length) return;

    const container = this.shadowRoot.querySelector('#energy-chart');
    if (!container) return;

    const data = this.historyData.energyUsage;

    // Find min/max values for scaling
    const values = data.map(d => d.value);
    const minValue = 0; // Energy usage should start at 0
    const maxValue = Math.ceil(Math.max(...values) + 1);

    // Generate bar chart HTML
    const chartHtml = this.generateChartHtml(
      data,
      'Energy Usage History',
      minValue,
      maxValue,
      value => `${value.toFixed(2)} kW`
    );

    container.innerHTML = chartHtml;
  }

  /**
   * Render the efficiency chart
   */
  renderEfficiencyChart() {
    if (!this.historyData.efficiency.length) return;

    const container = this.shadowRoot.querySelector('#efficiency-chart');
    if (!container) return;

    const data = this.historyData.efficiency;

    // Efficiency should be displayed from 0-100%
    const minValue = 0;
    const maxValue = 100;

    // Generate bar chart HTML
    const chartHtml = this.generateChartHtml(
      data,
      'Efficiency Rating History',
      minValue,
      maxValue,
      value => `${value.toFixed(1)}%`
    );

    container.innerHTML = chartHtml;
  }

  /**
   * Generate HTML for a chart
   */
  generateChartHtml(data, title, minValue, maxValue, formatValue) {
    // Skip if no data
    if (!data.length) return '<div class="no-data">No data available</div>';

    // Limit number of bars displayed to keep chart readable
    let displayData = data;
    if (data.length > 24) {
      // Sample data points
      const sampleSize = Math.min(24, Math.ceil(data.length / 10));
      const sampleInterval = Math.floor(data.length / sampleSize);
      displayData = Array.from({ length: sampleSize }, (_, i) => data[i * sampleInterval]);
    }

    // Calculate bar heights
    const range = maxValue - minValue;
    const barHeights = displayData.map(d => {
      const normalized = (d.value - minValue) / range;
      return Math.max(0.05, normalized) * 100; // At least 5% height for visibility
    });

    // Generate chart HTML
    const bars = displayData.map((d, i) => {
      const height = barHeights[i];
      const formattedValue = formatValue(d.value);
      const formattedTime = this.formatChartTimestamp(d.timestamp);

      return `
        <div class="chart-bar-container">
          <div class="chart-bar-label">${formattedValue}</div>
          <div class="chart-bar" style="height: ${height}%"></div>
          <div class="chart-bar-time">${formattedTime}</div>
        </div>
      `;
    }).join('');

    // Create axis labels
    const yAxisMax = formatValue(maxValue);
    const yAxisMid = formatValue(minValue + range / 2);
    const yAxisMin = formatValue(minValue);

    return `
      <div class="chart-container">
        <div class="chart-title">${title}</div>
        <div class="chart-y-axis">
          <div class="chart-y-label chart-y-max">${yAxisMax}</div>
          <div class="chart-y-label chart-y-mid">${yAxisMid}</div>
          <div class="chart-y-label chart-y-min">${yAxisMin}</div>
        </div>
        <div class="chart-content">
          ${bars}
        </div>
      </div>
    `;
  }

  /**
   * Format timestamp for chart display
   */
  formatChartTimestamp(timestamp) {
    // Different format based on selected time range
    switch (this.selectedRange) {
      case '24h':
        return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      case '7d':
        return timestamp.toLocaleDateString([], { weekday: 'short' });
      case '30d':
      case 'custom':
        return timestamp.toLocaleDateString([], { month: 'short', day: 'numeric' });
      default:
        return timestamp.toLocaleString();
    }
  }

  /**
   * Refresh the component data
   */
  refresh() {
    return this.loadHistoricalData();
  }

  /**
   * Update device data
   */
  updateDevice(updatedDevice) {
    this.device = updatedDevice;
    // No need to refresh data just because the device was updated
  }

  /**
   * Render the component
   */
  render() {
    // Define CSS styles
    const styles = `
      :host {
        display: block;
        width: 100%;
      }

      .performance-container {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
      }

      .performance-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
        gap: 1rem;
      }

      .performance-title {
        font-size: 1.2rem;
        font-weight: 500;
        margin: 0;
      }

      .range-selector {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      .range-label {
        font-size: 0.9rem;
        color: #757575;
      }

      .range-select {
        padding: 0.5rem;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        font-family: inherit;
        font-size: 0.9rem;
        background-color: white;
      }

      .custom-range-inputs {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-top: 0.5rem;
        display: none;
      }

      .custom-range-inputs.visible {
        display: flex;
      }

      .date-input {
        padding: 0.5rem;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        font-family: inherit;
        font-size: 0.9rem;
      }

      .apply-button {
        padding: 0.5rem 1rem;
        background-color: #2196F3;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.9rem;
      }

      .apply-button:hover {
        background-color: #1976D2;
      }

      .charts-container {
        display: grid;
        grid-template-columns: 1fr;
        gap: 2rem;
      }

      .chart-wrapper {
        width: 100%;
      }

      .chart-container {
        width: 100%;
        height: 300px;
        display: flex;
        position: relative;
      }

      .chart-title {
        position: absolute;
        top: -25px;
        left: 40px;
        font-weight: 500;
      }

      .chart-y-axis {
        width: 40px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 10px 0;
      }

      .chart-y-label {
        font-size: 0.8rem;
        color: #757575;
        text-align: right;
        padding-right: 5px;
      }

      .chart-content {
        flex: 1;
        height: 100%;
        display: flex;
        align-items: flex-end;
        justify-content: space-around;
        padding: 10px 0;
        border-left: 1px solid #e0e0e0;
        border-bottom: 1px solid #e0e0e0;
      }

      .chart-bar-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        height: 100%;
        flex: 1;
        max-width: 30px;
      }

      .chart-bar {
        width: 20px;
        background-color: #2196F3;
        border-radius: 2px 2px 0 0;
      }

      .chart-bar-label {
        font-size: 0.7rem;
        color: #424242;
        margin-bottom: 5px;
        text-align: center;
      }

      .chart-bar-time {
        font-size: 0.7rem;
        color: #757575;
        margin-top: 5px;
        transform: rotate(45deg);
        transform-origin: left top;
        white-space: nowrap;
      }

      .loading-container {
        padding: 3rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
      }

      .loading-spinner {
        width: 40px;
        height: 40px;
        border: 4px solid rgba(33, 150, 243, 0.2);
        border-top: 4px solid #2196F3;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 1rem;
      }

      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }

      .error-container {
        padding: 1.5rem;
        background-color: #FFEBEE;
        color: #F44336;
        border-radius: 4px;
        text-align: center;
        margin-bottom: 1rem;
      }

      .error-container button {
        margin-top: 1rem;
        padding: 0.5rem 1rem;
        background-color: #F44336;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
      }

      .no-data {
        text-align: center;
        padding: 2rem;
        color: #757575;
      }

      @media (min-width: 768px) {
        .charts-container {
          grid-template-columns: 1fr 1fr;
        }
      }

      @media (min-width: 1200px) {
        .charts-container {
          grid-template-columns: 1fr 1fr 1fr;
        }
      }
    `;

    // Define HTML template
    let contentHtml;

    if (this.isLoading) {
      contentHtml = `
        <div class="loading-container">
          <div class="loading-spinner"></div>
          <div>Loading performance data...</div>
        </div>
      `;
    } else if (this.error) {
      contentHtml = `
        <div class="error-container">
          <div>${this.error}</div>
          <button id="retry-button">Retry</button>
        </div>
      `;
    } else {
      contentHtml = `
        <div class="performance-header">
          <h3 class="performance-title">Performance Metrics</h3>

          <div class="range-controls">
            <div class="range-selector">
              <span class="range-label">Time Range:</span>
              <select class="range-select" id="time-range-select">
                ${this.availableRanges.map(range =>
                  `<option value="${range.id}" ${range.id === this.selectedRange ? 'selected' : ''}>
                    ${range.label}
                  </option>`
                ).join('')}
              </select>
            </div>

            <div class="custom-range-inputs ${this.selectedRange === 'custom' ? 'visible' : ''}">
              <input
                type="date"
                class="date-input"
                id="start-date-input"
                value="${this.customRange.startDate || ''}"
              >
              <span>to</span>
              <input
                type="date"
                class="date-input"
                id="end-date-input"
                value="${this.customRange.endDate || ''}"
                max="${new Date().toISOString().split('T')[0]}"
              >
              <button class="apply-button" id="apply-custom-range">Apply</button>
            </div>
          </div>
        </div>

        <div class="charts-container">
          <div class="chart-wrapper">
            <div id="temperature-chart"></div>
          </div>

          <div class="chart-wrapper">
            <div id="energy-chart"></div>
          </div>

          <div class="chart-wrapper">
            <div id="efficiency-chart"></div>
          </div>
        </div>
      `;
    }

    const template = `
      <div class="performance-container">
        ${contentHtml}
      </div>
    `;

    // Set the shadow DOM content
    this.shadowRoot.innerHTML = `<style>${styles}</style>${template}`;

    // Add event listeners
    this.addEventListeners();

    // Initialize charts if data is loaded
    if (!this.isLoading && !this.error) {
      this.initializeCharts();
    }
  }

  /**
   * Add event listeners
   */
  addEventListeners() {
    // Time range selector
    const rangeSelect = this.shadowRoot.querySelector('#time-range-select');
    if (rangeSelect) {
      rangeSelect.addEventListener('change', () => {
        this.selectedRange = rangeSelect.value;

        // Show/hide custom range inputs
        const customRangeInputs = this.shadowRoot.querySelector('.custom-range-inputs');
        if (customRangeInputs) {
          customRangeInputs.classList.toggle('visible', this.selectedRange === 'custom');
        }

        // If not custom range, load data immediately
        if (this.selectedRange !== 'custom') {
          this.loadHistoricalData();
        }
      });
    }

    // Custom range apply button
    const applyButton = this.shadowRoot.querySelector('#apply-custom-range');
    if (applyButton) {
      applyButton.addEventListener('click', () => {
        const startDateInput = this.shadowRoot.querySelector('#start-date-input');
        const endDateInput = this.shadowRoot.querySelector('#end-date-input');

        if (startDateInput && endDateInput) {
          this.customRange.startDate = startDateInput.value;
          this.customRange.endDate = endDateInput.value;

          if (this.customRange.startDate && this.customRange.endDate) {
            // Validate dates
            if (new Date(this.customRange.startDate) > new Date(this.customRange.endDate)) {
              alert('Start date must be before end date');
              return;
            }

            this.loadHistoricalData();
          } else {
            alert('Please select both start and end dates');
          }
        }
      });
    }

    // Retry button
    const retryButton = this.shadowRoot.querySelector('#retry-button');
    if (retryButton) {
      retryButton.addEventListener('click', () => {
        this.loadHistoricalData();
      });
    }
  }
}
