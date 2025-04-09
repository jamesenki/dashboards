/**
 * Device Status Card Component
 *
 * Displays current status and real-time telemetry for a water heater device
 * Designed as a reusable component following the device-agnostic architecture
 */
export class DeviceStatusCard extends HTMLElement {
  // Observed attributes that trigger attributeChangedCallback
  static get observedAttributes() {
    return [
      'device-id',
      'device-name',
      'manufacturer',
      'model',
      'connection-status',
      'simulated'
    ];
  }

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });

    // Component state
    this.deviceId = '';
    this.deviceName = '';
    this.manufacturer = '';
    this.model = '';
    this.connectionStatus = 'disconnected';
    this.simulated = false;
    this.temperatureUnit = 'F'; // Default temperature unit

    // Telemetry state
    this.telemetry = {
      temperature_current: null,
      temperature_setpoint: null,
      heating_status: false,
      power_consumption_watts: null,
      water_flow_gpm: null,
      mode: 'standby',
      last_updated: null
    };
  }

  /**
   * Called when the element is connected to the DOM
   */
  connectedCallback() {
    this.render();
  }

  /**
   * Called when observed attributes change
   */
  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue === newValue) return;

    switch (name) {
      case 'device-id':
        this.deviceId = newValue;
        break;
      case 'device-name':
        this.deviceName = newValue;
        break;
      case 'manufacturer':
        this.manufacturer = newValue;
        break;
      case 'model':
        this.model = newValue;
        break;
      case 'connection-status':
        this.connectionStatus = newValue;
        break;
      case 'simulated':
        this.simulated = (newValue === 'true' || newValue === '');
        break;
    }

    this.render();
  }

  /**
   * Update telemetry data
   */
  updateTelemetry(telemetryData) {
    // Update only the fields that are present in the data
    this.telemetry = { ...this.telemetry, ...telemetryData };

    // Update the UI
    this.updateTelemetryUI();
  }

  /**
   * Update device information
   */
  updateDevice(deviceData) {
    if (deviceData.device_id !== this.deviceId) return;

    // Update device attributes
    if (deviceData.display_name) {
      this.deviceName = deviceData.display_name;
    } else if (deviceData.manufacturer && deviceData.model) {
      this.deviceName = `${deviceData.manufacturer} ${deviceData.model}`;
    }

    if (deviceData.manufacturer) this.manufacturer = deviceData.manufacturer;
    if (deviceData.model) this.model = deviceData.model;
    if (deviceData.connection_status) this.connectionStatus = deviceData.connection_status;
    if (deviceData.simulated !== undefined) this.simulated = deviceData.simulated;

    // Update telemetry if state is included
    if (deviceData.state) {
      this.updateTelemetry(deviceData.state);
    }

    // Re-render the component
    this.render();
  }

  /**
   * Update only the telemetry sections of the UI without full re-render
   */
  updateTelemetryUI() {
    // Get references to elements that need updating
    const card = this.shadowRoot.querySelector('.device-card');
    if (!card) return; // Exit if card isn't rendered yet

    // Update temperature display
    const currentTempEl = this.shadowRoot.querySelector('.current-temp .value');
    const targetTempEl = this.shadowRoot.querySelector('.target-temp .value');

    if (currentTempEl && this.telemetry.temperature_current !== null) {
      currentTempEl.textContent = this.formatTemperature(this.telemetry.temperature_current);
    }

    if (targetTempEl && this.telemetry.temperature_setpoint !== null) {
      targetTempEl.textContent = this.formatTemperature(this.telemetry.temperature_setpoint);
    }

    // Update heating status
    const heatingStatusEl = this.shadowRoot.querySelector('.heating-status');
    if (heatingStatusEl) {
      heatingStatusEl.classList.toggle('active', this.telemetry.heating_status);
      heatingStatusEl.textContent = this.telemetry.heating_status ? 'Heating' : 'Idle';
    }

    // Update mode
    const modeValueEl = this.shadowRoot.querySelector('.mode-value');
    if (modeValueEl && this.telemetry.mode) {
      modeValueEl.textContent = this.formatMode(this.telemetry.mode);
    }

    // Update power consumption
    const powerValueEl = this.shadowRoot.querySelector('.power-value');
    if (powerValueEl && this.telemetry.power_consumption_watts !== null) {
      powerValueEl.textContent = `${this.telemetry.power_consumption_watts.toFixed(0)} W`;
    }

    // Update water flow
    const flowValueEl = this.shadowRoot.querySelector('.flow-value');
    if (flowValueEl && this.telemetry.water_flow_gpm !== null) {
      flowValueEl.textContent = `${this.telemetry.water_flow_gpm.toFixed(1)} GPM`;
    }

    // Update last updated timestamp
    const lastUpdatedEl = this.shadowRoot.querySelector('.last-updated');
    if (lastUpdatedEl) {
      lastUpdatedEl.textContent = this.telemetry.last_updated
        ? this.formatLastUpdated(this.telemetry.last_updated)
        : 'Never';
    }
  }

  /**
   * Format temperature value with unit
   */
  formatTemperature(value) {
    if (value === null || isNaN(value)) return '—';
    return `${value.toFixed(1)}°${this.temperatureUnit}`;
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
   * Format last updated timestamp for display
   */
  formatLastUpdated(timestamp) {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch (e) {
      return timestamp || 'Unknown';
    }
  }

  /**
   * Toggle temperature unit between Fahrenheit and Celsius
   */
  toggleTemperatureUnit() {
    this.temperatureUnit = this.temperatureUnit === 'F' ? 'C' : 'F';
    this.updateTelemetryUI();
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

      .device-card {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        transition: box-shadow 0.3s, transform 0.3s;
        cursor: pointer;
      }

      .device-card:hover {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
      }

      .card-header {
        padding: 1rem;
        border-bottom: 1px solid #f0f0f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .device-name {
        font-size: 1.1rem;
        font-weight: 500;
        margin: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .device-meta {
        display: flex;
        align-items: center;
        font-size: 0.8rem;
        color: #757575;
      }

      .connection-status {
        display: flex;
        align-items: center;
        font-size: 0.8rem;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        margin-left: 0.5rem;
      }

      .connection-status.connected {
        background-color: #E8F5E9;
        color: #4CAF50;
      }

      .connection-status.disconnected {
        background-color: #FFEBEE;
        color: #F44336;
      }

      .simulation-badge {
        position: absolute;
        top: 0.5rem;
        right: 0.5rem;
        background-color: #673AB7;
        color: white;
        font-size: 0.7rem;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
      }

      .temperature-display {
        display: flex;
        justify-content: space-between;
        padding: 1.5rem;
        background-color: #f5f5f5;
        position: relative;
      }

      .current-temp, .target-temp {
        display: flex;
        flex-direction: column;
        align-items: center;
      }

      .temp-label {
        font-size: 0.8rem;
        color: #757575;
        margin-bottom: 0.5rem;
      }

      .value {
        font-size: 1.8rem;
        font-weight: 500;
      }

      .heating-status {
        position: absolute;
        top: 0.5rem;
        left: 50%;
        transform: translateX(-50%);
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.8rem;
        background-color: #F5F5F5;
        color: #757575;
      }

      .heating-status.active {
        background-color: #FFF3E0;
        color: #FF9800;
      }

      .status-rows {
        padding: 1rem;
      }

      .status-row {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid #f0f0f0;
      }

      .status-row:last-child {
        border-bottom: none;
      }

      .status-label {
        color: #757575;
        font-size: 0.9rem;
      }

      .status-value {
        font-weight: 500;
        font-size: 0.9rem;
      }

      .card-footer {
        padding: 0.5rem 1rem;
        background-color: #f5f5f5;
        font-size: 0.8rem;
        color: #9e9e9e;
        text-align: right;
      }
    `;

    // Define HTML template
    const template = `
      <div class="device-card">
        <div class="card-header">
          <h3 class="device-name">${this.deviceName}</h3>
          <div class="device-meta">
            ${this.manufacturer} ${this.model}
            <div class="connection-status ${this.connectionStatus}">
              ${this.connectionStatus}
            </div>
          </div>
          ${this.simulated ? '<div class="simulation-badge">SIMULATED</div>' : ''}
        </div>

        <div class="temperature-display">
          <div class="heating-status ${this.telemetry.heating_status ? 'active' : ''}">
            ${this.telemetry.heating_status ? 'Heating' : 'Idle'}
          </div>
          <div class="current-temp">
            <div class="temp-label">Current</div>
            <div class="value">${this.formatTemperature(this.telemetry.temperature_current)}</div>
          </div>
          <div class="target-temp">
            <div class="temp-label">Target</div>
            <div class="value">${this.formatTemperature(this.telemetry.temperature_setpoint)}</div>
          </div>
        </div>

        <div class="status-rows">
          <div class="status-row">
            <div class="status-label">Mode:</div>
            <div class="status-value mode-value">${this.formatMode(this.telemetry.mode)}</div>
          </div>
          <div class="status-row">
            <div class="status-label">Power:</div>
            <div class="status-value power-value">
              ${this.telemetry.power_consumption_watts !== null
                ? `${this.telemetry.power_consumption_watts.toFixed(0)} W`
                : '—'}
            </div>
          </div>
          <div class="status-row">
            <div class="status-label">Water Flow:</div>
            <div class="status-value flow-value">
              ${this.telemetry.water_flow_gpm !== null
                ? `${this.telemetry.water_flow_gpm.toFixed(1)} GPM`
                : '—'}
            </div>
          </div>
        </div>

        <div class="card-footer">
          Last updated: <span class="last-updated">
            ${this.telemetry.last_updated
              ? this.formatLastUpdated(this.telemetry.last_updated)
              : 'Never'}
          </span>
        </div>
      </div>
    `;

    // Set the shadow DOM content
    this.shadowRoot.innerHTML = `<style>${styles}</style>${template}`;

    // Add click handler to the card
    const card = this.shadowRoot.querySelector('.device-card');
    card.addEventListener('click', (event) => {
      // Dispatch custom event
      this.dispatchEvent(new CustomEvent('device-selected', {
        detail: {
          deviceId: this.deviceId
        },
        bubbles: true,
        composed: true
      }));
    });
  }
}
