/**
 * Device Telemetry Component
 *
 * Displays real-time telemetry data for a water heater device
 * Part of the device-agnostic IoTSphere platform architecture
 */
export class DeviceTelemetry extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });

    // Component state
    this.device = null;
    this.deviceService = null;
    this.telemetryService = null;
    this.telemetrySubscription = null;
    this.telemetryData = {
      temperature_current: null,
      temperature_setpoint: null,
      heating_status: false,
      power_consumption_watts: null,
      water_flow_gpm: null,
      energy_used_today_kwh: null,
      mode: 'standby',
      efficiency_rating: null,
      last_updated: null
    };

    // Settings
    this.temperatureUnit = 'F'; // Default temperature unit
    this.refreshInterval = null;
    this.refreshRate = 30000; // 30 seconds
  }

  /**
   * Initialize the component with device data and services
   */
  initialize({ device, deviceService, telemetryService }) {
    this.device = device;
    this.deviceService = deviceService;
    this.telemetryService = telemetryService;

    // Merge any telemetry data from device state
    if (device.state) {
      this.telemetryData = {
        ...this.telemetryData,
        ...device.state
      };
    }

    // Start real-time updates
    this.startRealTimeUpdates();

    // Render the component
    this.render();
  }

  /**
   * Called when the element is connected to the DOM
   */
  connectedCallback() {
    if (this.device) {
      this.render();
    }
  }

  /**
   * Called when the element is disconnected from the DOM
   */
  disconnectedCallback() {
    this.cleanup();
  }

  /**
   * Clean up resources
   */
  cleanup() {
    // Unsubscribe from telemetry updates
    if (this.telemetrySubscription && this.telemetryService) {
      this.telemetryService.unsubscribe(this.telemetrySubscription);
      this.telemetrySubscription = null;
    }

    // Clear refresh interval
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  }

  /**
   * Start real-time telemetry updates
   */
  startRealTimeUpdates() {
    if (!this.telemetryService || !this.device) return;

    // Fetch initial telemetry data
    this.fetchLatestTelemetry();

    // Subscribe to real-time updates
    this.telemetrySubscription = this.telemetryService.subscribeToDeviceTelemetry(
      this.device.device_id,
      (telemetryData) => {
        this.updateTelemetry(telemetryData);
      }
    );

    // Set up periodic refresh as a fallback
    this.refreshInterval = setInterval(() => {
      if (this.device.connection_status === 'connected') {
        this.fetchLatestTelemetry();
      }
    }, this.refreshRate);
  }

  /**
   * Fetch the latest telemetry from the service
   */
  async fetchLatestTelemetry() {
    if (!this.telemetryService || !this.device) return;

    try {
      const latestTelemetry = await this.telemetryService.getLatestTelemetry(this.device.device_id);
      this.updateTelemetry(latestTelemetry);
    } catch (error) {
      console.error('Error fetching latest telemetry:', error);
    }
  }

  /**
   * Update telemetry data and UI
   */
  updateTelemetry(telemetryData) {
    // Update telemetry state
    this.telemetryData = {
      ...this.telemetryData,
      ...telemetryData,
      last_updated: telemetryData.timestamp || new Date().toISOString()
    };

    // Update UI with new telemetry data
    this.updateTelemetryUI();
  }

  /**
   * Update device data
   */
  updateDevice(updatedDevice) {
    this.device = updatedDevice;

    // Update telemetry from device state if available
    if (updatedDevice.state) {
      this.updateTelemetry(updatedDevice.state);
    }

    this.render();
  }

  /**
   * Update only the telemetry portions of the UI
   */
  updateTelemetryUI() {
    // Find and update temperature gauge
    const temperatureGauge = this.shadowRoot.querySelector('#temperature-gauge');
    if (temperatureGauge) {
      this.updateTemperatureGauge(temperatureGauge);
    }

    // Update all telemetry values
    const temperatureValue = this.shadowRoot.querySelector('#temperature-value');
    const setpointValue = this.shadowRoot.querySelector('#setpoint-value');
    const heatingStatus = this.shadowRoot.querySelector('#heating-status');
    const powerValue = this.shadowRoot.querySelector('#power-value');
    const flowValue = this.shadowRoot.querySelector('#flow-value');
    const energyValue = this.shadowRoot.querySelector('#energy-value');
    const modeValue = this.shadowRoot.querySelector('#mode-value');
    const efficiencyValue = this.shadowRoot.querySelector('#efficiency-value');
    const lastUpdated = this.shadowRoot.querySelector('#last-updated');

    if (temperatureValue) {
      temperatureValue.textContent = this.formatTemperature(this.telemetryData.temperature_current);
    }

    if (setpointValue) {
      setpointValue.textContent = this.formatTemperature(this.telemetryData.temperature_setpoint);
    }

    if (heatingStatus) {
      heatingStatus.textContent = this.telemetryData.heating_status ? 'Heating' : 'Idle';
      heatingStatus.className = `status-value ${this.telemetryData.heating_status ? 'active' : 'inactive'}`;
    }

    if (powerValue && this.telemetryData.power_consumption_watts !== null) {
      powerValue.textContent = `${this.telemetryData.power_consumption_watts.toFixed(0)} W`;
    }

    if (flowValue && this.telemetryData.water_flow_gpm !== null) {
      flowValue.textContent = `${this.telemetryData.water_flow_gpm.toFixed(1)} GPM`;
    }

    if (energyValue && this.telemetryData.energy_used_today_kwh !== null) {
      energyValue.textContent = `${this.telemetryData.energy_used_today_kwh.toFixed(2)} kWh`;
    }

    if (modeValue) {
      modeValue.textContent = this.formatMode(this.telemetryData.mode);
    }

    if (efficiencyValue && this.telemetryData.efficiency_rating !== null) {
      efficiencyValue.textContent = `${this.telemetryData.efficiency_rating.toFixed(0)}%`;
    }

    if (lastUpdated && this.telemetryData.last_updated) {
      lastUpdated.textContent = this.formatTimestamp(this.telemetryData.last_updated);
    }
  }

  /**
   * Update the temperature gauge visualization
   */
  updateTemperatureGauge(gaugeElement) {
    const current = this.telemetryData.temperature_current;
    const setpoint = this.telemetryData.temperature_setpoint;

    if (current === null || setpoint === null) return;

    // Calculate gauge percentages
    // Assuming water heater range is 60°F to 160°F (adjust as needed)
    const minTemp = 60;
    const maxTemp = 160;
    const range = maxTemp - minTemp;

    // Calculate percentage positions for current and setpoint
    const currentPercent = Math.min(100, Math.max(0, ((current - minTemp) / range) * 100));
    const setpointPercent = Math.min(100, Math.max(0, ((setpoint - minTemp) / range) * 100));

    // Update gauge visualization
    const currentIndicator = gaugeElement.querySelector('.current-indicator');
    const setpointIndicator = gaugeElement.querySelector('.setpoint-indicator');
    const heatingIndicator = gaugeElement.querySelector('.heating-indicator');

    if (currentIndicator) {
      currentIndicator.style.left = `${currentPercent}%`;
    }

    if (setpointIndicator) {
      setpointIndicator.style.left = `${setpointPercent}%`;
    }

    if (heatingIndicator) {
      heatingIndicator.style.display = this.telemetryData.heating_status ? 'block' : 'none';
    }
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

      .telemetry-container {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
      }

      .telemetry-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
      }

      .telemetry-title {
        font-size: 1.2rem;
        font-weight: 500;
        margin: 0;
      }

      .unit-toggle {
        background: none;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 0.3rem 0.6rem;
        font-size: 0.8rem;
        cursor: pointer;
      }

      .unit-toggle:hover {
        background-color: #f5f5f5;
      }

      .temperature-gauge-container {
        margin-bottom: 2rem;
      }

      .temperature-gauge {
        position: relative;
        height: 8px;
        background-color: #f5f5f5;
        border-radius: 4px;
        margin: 2rem 0 1rem 0;
      }

      .gauge-ticks {
        position: relative;
        height: 100%;
        width: 100%;
      }

      .gauge-tick {
        position: absolute;
        width: 1px;
        height: 8px;
        background-color: #e0e0e0;
        bottom: 0;
      }

      .gauge-label {
        position: absolute;
        font-size: 0.75rem;
        color: #757575;
        top: 12px;
        transform: translateX(-50%);
      }

      .current-indicator {
        position: absolute;
        width: 12px;
        height: 12px;
        background-color: #2196F3;
        border-radius: 50%;
        top: -2px;
        transform: translateX(-50%);
        z-index: 2;
      }

      .setpoint-indicator {
        position: absolute;
        width: 4px;
        height: 16px;
        background-color: #FF9800;
        top: -4px;
        transform: translateX(-50%);
        z-index: 1;
      }

      .heating-indicator {
        position: absolute;
        left: 0;
        right: 0;
        height: 100%;
        background: linear-gradient(90deg, rgba(255,152,0,0.1) 0%, rgba(255,152,0,0.3) 100%);
        border-radius: 4px;
        display: none;
      }

      .gauge-info {
        display: flex;
        justify-content: space-between;
      }

      .gauge-data {
        display: flex;
        align-items: center;
      }

      .gauge-data-label {
        font-size: 0.8rem;
        color: #757575;
        margin-right: 0.5rem;
      }

      .gauge-data-value {
        font-weight: 500;
      }

      .current-temp {
        color: #2196F3;
      }

      .setpoint-temp {
        color: #FF9800;
      }

      .telemetry-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 1.5rem;
      }

      .telemetry-item {
        display: flex;
        flex-direction: column;
      }

      .telemetry-label {
        font-size: 0.8rem;
        color: #757575;
        margin-bottom: 0.5rem;
      }

      .telemetry-value {
        font-size: 1.25rem;
        font-weight: 500;
      }

      .status-value {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.9rem;
        font-weight: 500;
      }

      .status-value.active {
        background-color: #FFF3E0;
        color: #FF9800;
      }

      .status-value.inactive {
        background-color: #F5F5F5;
        color: #757575;
      }

      .telemetry-footer {
        margin-top: 1.5rem;
        text-align: right;
        font-size: 0.8rem;
        color: #9E9E9E;
      }

      .disconnected-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(255, 255, 255, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10;
        border-radius: 8px;
      }

      .disconnected-message {
        background-color: #FFEBEE;
        color: #F44336;
        padding: 1rem;
        border-radius: 4px;
        text-align: center;
      }
    `;

    // Define HTML template
    const isDisconnected = this.device?.connection_status === 'disconnected';

    const template = `
      <div class="telemetry-container" style="position: relative;">
        ${isDisconnected ? this.renderDisconnectedOverlay() : ''}

        <div class="telemetry-header">
          <h3 class="telemetry-title">Current Telemetry</h3>
          <button class="unit-toggle" id="unit-toggle">
            °${this.temperatureUnit} → °${this.temperatureUnit === 'F' ? 'C' : 'F'}
          </button>
        </div>

        <div class="temperature-gauge-container">
          <div class="temperature-gauge" id="temperature-gauge">
            <div class="heating-indicator"></div>
            <div class="gauge-ticks">
              <!-- Generate tick marks for temperature scale -->
              ${this.generateGaugeTicks()}
            </div>
            <div class="current-indicator"></div>
            <div class="setpoint-indicator"></div>
          </div>

          <div class="gauge-info">
            <div class="gauge-data">
              <span class="gauge-data-label">Current:</span>
              <span class="gauge-data-value current-temp" id="temperature-value">
                ${this.formatTemperature(this.telemetryData.temperature_current)}
              </span>
            </div>
            <div class="gauge-data">
              <span class="gauge-data-label">Target:</span>
              <span class="gauge-data-value setpoint-temp" id="setpoint-value">
                ${this.formatTemperature(this.telemetryData.temperature_setpoint)}
              </span>
            </div>
          </div>
        </div>

        <div class="telemetry-grid">
          <div class="telemetry-item">
            <div class="telemetry-label">Heating Status</div>
            <div class="telemetry-value">
              <span class="status-value ${this.telemetryData.heating_status ? 'active' : 'inactive'}" id="heating-status">
                ${this.telemetryData.heating_status ? 'Heating' : 'Idle'}
              </span>
            </div>
          </div>

          <div class="telemetry-item">
            <div class="telemetry-label">Operating Mode</div>
            <div class="telemetry-value" id="mode-value">
              ${this.formatMode(this.telemetryData.mode)}
            </div>
          </div>

          <div class="telemetry-item">
            <div class="telemetry-label">Power Consumption</div>
            <div class="telemetry-value" id="power-value">
              ${this.telemetryData.power_consumption_watts !== null ?
                `${this.telemetryData.power_consumption_watts.toFixed(0)} W` : '—'}
            </div>
          </div>

          <div class="telemetry-item">
            <div class="telemetry-label">Water Flow</div>
            <div class="telemetry-value" id="flow-value">
              ${this.telemetryData.water_flow_gpm !== null ?
                `${this.telemetryData.water_flow_gpm.toFixed(1)} GPM` : '—'}
            </div>
          </div>

          <div class="telemetry-item">
            <div class="telemetry-label">Energy Used Today</div>
            <div class="telemetry-value" id="energy-value">
              ${this.telemetryData.energy_used_today_kwh !== null ?
                `${this.telemetryData.energy_used_today_kwh.toFixed(2)} kWh` : '—'}
            </div>
          </div>

          <div class="telemetry-item">
            <div class="telemetry-label">Efficiency Rating</div>
            <div class="telemetry-value" id="efficiency-value">
              ${this.telemetryData.efficiency_rating !== null ?
                `${this.telemetryData.efficiency_rating.toFixed(0)}%` : '—'}
            </div>
          </div>
        </div>

        <div class="telemetry-footer">
          Last updated: <span id="last-updated">${this.formatTimestamp(this.telemetryData.last_updated)}</span>
        </div>
      </div>
    `;

    // Set the shadow DOM content
    this.shadowRoot.innerHTML = `<style>${styles}</style>${template}`;

    // Initialize the temperature gauge
    const temperatureGauge = this.shadowRoot.querySelector('#temperature-gauge');
    if (temperatureGauge) {
      this.updateTemperatureGauge(temperatureGauge);
    }

    // Add event listener for temperature unit toggle
    const unitToggle = this.shadowRoot.querySelector('#unit-toggle');
    if (unitToggle) {
      unitToggle.addEventListener('click', () => {
        this.toggleTemperatureUnit();
      });
    }
  }

  /**
   * Generate tick marks for the temperature gauge
   */
  generateGaugeTicks() {
    // Generate ticks for temperature gauge at 20° increments
    const ticks = [];
    const minTemp = 60;
    const maxTemp = 160;
    const range = maxTemp - minTemp;

    for (let temp = minTemp; temp <= maxTemp; temp += 20) {
      const position = ((temp - minTemp) / range) * 100;
      ticks.push(`
        <div class="gauge-tick" style="left: ${position}%"></div>
        <div class="gauge-label" style="left: ${position}%">${temp}°${this.temperatureUnit}</div>
      `);
    }

    return ticks.join('');
  }

  /**
   * Render disconnected overlay
   */
  renderDisconnectedOverlay() {
    return `
      <div class="disconnected-overlay">
        <div class="disconnected-message">
          <div>Device is currently disconnected</div>
          <div>Telemetry data may be outdated</div>
        </div>
      </div>
    `;
  }

  /**
   * Toggle temperature unit between Fahrenheit and Celsius
   */
  toggleTemperatureUnit() {
    this.temperatureUnit = this.temperatureUnit === 'F' ? 'C' : 'F';
    this.render();
  }

  /**
   * Format temperature value with unit
   */
  formatTemperature(value) {
    if (value === null || isNaN(value)) return '—';

    // Convert temperature if needed
    let displayValue = value;
    if (this.temperatureUnit === 'C' && this.device?.temperature_unit === 'F') {
      displayValue = (value - 32) * (5/9);
    } else if (this.temperatureUnit === 'F' && this.device?.temperature_unit === 'C') {
      displayValue = (value * 9/5) + 32;
    }

    return `${displayValue.toFixed(1)}°${this.temperatureUnit}`;
  }

  /**
   * Format device mode for display
   */
  formatMode(mode) {
    if (!mode) return 'Unknown';

    // Title case the mode
    return mode.charAt(0).toUpperCase() + mode.slice(1);
  }

  /**
   * Format timestamp for display
   */
  formatTimestamp(timestamp) {
    if (!timestamp) return 'Never';

    try {
      return new Date(timestamp).toLocaleString();
    } catch (e) {
      return timestamp;
    }
  }
}
