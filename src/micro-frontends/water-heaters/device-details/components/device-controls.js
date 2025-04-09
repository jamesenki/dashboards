/**
 * Device Controls Component
 *
 * Provides interactive controls for adjusting water heater settings
 * Part of the device-agnostic IoTSphere platform architecture
 */
export class DeviceControls extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });

    // Component state
    this.device = null;
    this.deviceService = null;
    this.onDeviceControlChange = null;

    // Controls state
    this.isControlsEnabled = true;
    this.isUpdating = false;
    this.controlsError = null;

    // Debounce timers
    this.updateTimers = {};
  }

  /**
   * Initialize the component with device data and services
   */
  initialize({ device, deviceService, onDeviceControlChange }) {
    this.device = device;
    this.deviceService = deviceService;
    this.onDeviceControlChange = onDeviceControlChange;

    // Disable controls if device is disconnected
    this.isControlsEnabled = device.connection_status === 'connected';

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
   * Update device data
   */
  updateDevice(updatedDevice) {
    const wasDisconnected = this.device.connection_status === 'disconnected';
    const isNowConnected = updatedDevice.connection_status === 'connected';

    this.device = updatedDevice;

    // Update controls state if connection status changed
    if (wasDisconnected && isNowConnected) {
      this.isControlsEnabled = true;
      this.controlsError = null;
    } else if (!wasDisconnected && !isNowConnected) {
      this.isControlsEnabled = false;
      this.controlsError = 'Device is disconnected. Controls are disabled.';
    }

    this.render();
  }

  /**
   * Render the component
   */
  render() {
    if (!this.device) return;

    // Define CSS styles
    const styles = `
      :host {
        display: block;
        width: 100%;
      }

      .controls-container {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        position: relative;
      }

      .controls-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
      }

      .controls-title {
        font-size: 1.2rem;
        font-weight: 500;
        margin: 0;
      }

      .control-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 1.5rem;
      }

      .control-item {
        display: flex;
        flex-direction: column;
      }

      .control-label {
        font-size: 0.9rem;
        color: #757575;
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .current-value {
        font-weight: 500;
        color: #424242;
      }

      .control-slider {
        -webkit-appearance: none;
        width: 100%;
        height: 6px;
        border-radius: 3px;
        background: #e0e0e0;
        outline: none;
      }

      .control-slider::-webkit-slider-thumb {
        -webkit-appearance: none;
        appearance: none;
        width: 18px;
        height: 18px;
        border-radius: 50%;
        background: #2196F3;
        cursor: pointer;
      }

      .control-slider::-moz-range-thumb {
        width: 18px;
        height: 18px;
        border-radius: 50%;
        background: #2196F3;
        cursor: pointer;
      }

      .control-slider:disabled {
        opacity: 0.5;
      }

      .control-slider:disabled::-webkit-slider-thumb {
        background: #bdbdbd;
      }

      .control-slider:disabled::-moz-range-thumb {
        background: #bdbdbd;
      }

      .control-select {
        padding: 0.5rem;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        font-family: inherit;
        font-size: 0.9rem;
        background-color: white;
      }

      .control-select:disabled {
        opacity: 0.5;
        background-color: #f5f5f5;
      }

      .toggle-switch {
        position: relative;
        display: inline-block;
        width: 50px;
        height: 24px;
        margin-top: 0.25rem;
      }

      .toggle-switch input {
        opacity: 0;
        width: 0;
        height: 0;
      }

      .toggle-slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #ccc;
        transition: .4s;
        border-radius: 24px;
      }

      .toggle-slider:before {
        position: absolute;
        content: "";
        height: 16px;
        width: 16px;
        left: 4px;
        bottom: 4px;
        background-color: white;
        transition: .4s;
        border-radius: 50%;
      }

      input:checked + .toggle-slider {
        background-color: #2196F3;
      }

      input:disabled + .toggle-slider {
        opacity: 0.5;
        cursor: not-allowed;
      }

      input:checked + .toggle-slider:before {
        transform: translateX(26px);
      }

      .control-button {
        background-color: #2196F3;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
        cursor: pointer;
        margin-top: 0.5rem;
      }

      .control-button:hover {
        background-color: #1976D2;
      }

      .control-button:disabled {
        background-color: #bdbdbd;
        cursor: not-allowed;
      }

      .status-message {
        margin-top: 1.5rem;
        padding: 0.75rem;
        border-radius: 4px;
        text-align: center;
        font-size: 0.9rem;
      }

      .error-message {
        background-color: #FFEBEE;
        color: #F44336;
      }

      .success-message {
        background-color: #E8F5E9;
        color: #4CAF50;
      }

      .info-message {
        background-color: #E3F2FD;
        color: #2196F3;
      }

      .controls-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: rgba(255, 255, 255, 0.8);
        z-index: 10;
        border-radius: 8px;
      }

      .controls-overlay-message {
        background-color: #FFEBEE;
        color: #F44336;
        padding: 1rem;
        border-radius: 4px;
        text-align: center;
      }

      .updating-indicator {
        position: absolute;
        top: 1.5rem;
        right: 1.5rem;
        display: flex;
        align-items: center;
        color: #2196F3;
        font-size: 0.9rem;
      }

      .updating-spinner {
        width: 16px;
        height: 16px;
        border: 2px solid rgba(33, 150, 243, 0.2);
        border-top: 2px solid #2196F3;
        border-radius: 50%;
        margin-right: 0.5rem;
        animation: spin 1s linear infinite;
      }

      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    `;

    // Define HTML template
    const template = `
      <div class="controls-container">
        ${!this.isControlsEnabled ? this.renderDisabledOverlay() : ''}
        ${this.isUpdating ? this.renderUpdatingIndicator() : ''}

        <div class="controls-header">
          <h3 class="controls-title">Device Controls</h3>
        </div>

        <div class="control-grid">
          <!-- Temperature setpoint control -->
          <div class="control-item">
            <div class="control-label">
              <span>Temperature Setpoint</span>
              <span class="current-value">${this.getDeviceStateValue('temperature_setpoint', 120)}°F</span>
            </div>
            <input
              type="range"
              class="control-slider"
              id="temp-setpoint-control"
              min="100"
              max="140"
              step="1"
              value="${this.getDeviceStateValue('temperature_setpoint', 120)}"
              ${!this.isControlsEnabled ? 'disabled' : ''}
            >
          </div>

          <!-- Operating mode control -->
          <div class="control-item">
            <div class="control-label">
              <span>Operating Mode</span>
              <span class="current-value">${this.formatMode(this.getDeviceStateValue('mode', 'standard'))}</span>
            </div>
            <select
              class="control-select"
              id="mode-control"
              ${!this.isControlsEnabled ? 'disabled' : ''}
            >
              <option value="standard" ${this.getDeviceStateValue('mode', 'standard') === 'standard' ? 'selected' : ''}>Standard</option>
              <option value="eco" ${this.getDeviceStateValue('mode', 'standard') === 'eco' ? 'selected' : ''}>Eco</option>
              <option value="vacation" ${this.getDeviceStateValue('mode', 'standard') === 'vacation' ? 'selected' : ''}>Vacation</option>
              <option value="high_demand" ${this.getDeviceStateValue('mode', 'standard') === 'high_demand' ? 'selected' : ''}>High Demand</option>
            </select>
          </div>

          <!-- Schedule active toggle -->
          <div class="control-item">
            <div class="control-label">
              <span>Schedule Active</span>
              <span class="current-value">${this.getDeviceStateValue('schedule_active', false) ? 'On' : 'Off'}</span>
            </div>
            <label class="toggle-switch">
              <input
                type="checkbox"
                id="schedule-control"
                ${this.getDeviceStateValue('schedule_active', false) ? 'checked' : ''}
                ${!this.isControlsEnabled ? 'disabled' : ''}
              >
              <span class="toggle-slider"></span>
            </label>
          </div>

          <!-- Vacation mode settings (conditionally displayed) -->
          ${this.getDeviceStateValue('mode', 'standard') === 'vacation' ? `
            <div class="control-item">
              <div class="control-label">
                <span>Vacation Return Date</span>
              </div>
              <input
                type="date"
                class="control-select"
                id="vacation-date-control"
                value="${this.getDeviceStateValue('vacation_end_date', this.getTomorrowDate())}"
                min="${this.getTodayDate()}"
                ${!this.isControlsEnabled ? 'disabled' : ''}
              >
              <button
                class="control-button"
                id="schedule-vacation-button"
                ${!this.isControlsEnabled ? 'disabled' : ''}
              >
                Schedule Vacation
              </button>
            </div>
          ` : ''}

          <!-- Emergency heat button (shown conditionally based on device capabilities) -->
          ${this.device.capabilities?.includes('emergency_heat') ? `
            <div class="control-item">
              <div class="control-label">
                <span>Emergency Heat</span>
                <span class="current-value">${this.getDeviceStateValue('emergency_heat', false) ? 'Active' : 'Inactive'}</span>
              </div>
              <button
                class="control-button"
                id="emergency-heat-button"
                ${!this.isControlsEnabled ? 'disabled' : ''}
              >
                ${this.getDeviceStateValue('emergency_heat', false) ? 'Disable' : 'Enable'} Emergency Heat
              </button>
            </div>
          ` : ''}
        </div>

        ${this.controlsError ? `
          <div class="status-message error-message">
            ${this.controlsError}
          </div>
        ` : ''}
      </div>
    `;

    // Set the shadow DOM content
    this.shadowRoot.innerHTML = `<style>${styles}</style>${template}`;

    // Add event listeners
    this.addEventListeners();
  }

  /**
   * Add event listeners to controls
   */
  addEventListeners() {
    // Temperature setpoint slider
    const tempSetpointControl = this.shadowRoot.querySelector('#temp-setpoint-control');
    if (tempSetpointControl) {
      tempSetpointControl.addEventListener('input', (e) => {
        // Update the current value display in real-time
        const valueDisplay = tempSetpointControl.parentNode.querySelector('.current-value');
        if (valueDisplay) {
          valueDisplay.textContent = `${e.target.value}°F`;
        }
      });

      tempSetpointControl.addEventListener('change', (e) => {
        this.handleControlChange('temperature_setpoint', parseFloat(e.target.value));
      });
    }

    // Operating mode select
    const modeControl = this.shadowRoot.querySelector('#mode-control');
    if (modeControl) {
      modeControl.addEventListener('change', (e) => {
        const newMode = e.target.value;
        this.handleControlChange('mode', newMode);

        // Re-render to show/hide vacation controls
        this.render();
      });
    }

    // Schedule toggle
    const scheduleControl = this.shadowRoot.querySelector('#schedule-control');
    if (scheduleControl) {
      scheduleControl.addEventListener('change', (e) => {
        this.handleControlChange('schedule_active', e.target.checked);
      });
    }

    // Vacation date control
    const vacationDateControl = this.shadowRoot.querySelector('#vacation-date-control');
    if (vacationDateControl) {
      vacationDateControl.addEventListener('change', (e) => {
        this.handleControlChange('vacation_end_date', e.target.value);
      });
    }

    // Schedule vacation button
    const scheduleVacationButton = this.shadowRoot.querySelector('#schedule-vacation-button');
    if (scheduleVacationButton) {
      scheduleVacationButton.addEventListener('click', () => {
        this.scheduleVacation();
      });
    }

    // Emergency heat button
    const emergencyHeatButton = this.shadowRoot.querySelector('#emergency-heat-button');
    if (emergencyHeatButton) {
      emergencyHeatButton.addEventListener('click', () => {
        const currentValue = this.getDeviceStateValue('emergency_heat', false);
        this.handleControlChange('emergency_heat', !currentValue);
      });
    }
  }

  /**
   * Handle control value changes
   */
  handleControlChange(controlType, value) {
    if (!this.isControlsEnabled || !this.deviceService) return;

    // Cancel any existing update timer for this control
    if (this.updateTimers[controlType]) {
      clearTimeout(this.updateTimers[controlType]);
    }

    // Set a short debounce delay for sending changes to the server
    this.updateTimers[controlType] = setTimeout(async () => {
      try {
        this.isUpdating = true;
        this.render();

        // Create update payload
        const updateData = {
          state: {
            [controlType]: value
          }
        };

        // Send update to server
        const updatedDevice = await this.deviceService.updateDevice(
          this.device.device_id,
          updateData
        );

        // Update local state
        this.updateDevice(updatedDevice);

        // Notify parent of control change
        if (this.onDeviceControlChange) {
          this.onDeviceControlChange(controlType, value);
        }

        this.isUpdating = false;
        this.controlsError = null;
        this.render();
      } catch (error) {
        console.error(`Error updating ${controlType}:`, error);
        this.isUpdating = false;
        this.controlsError = `Failed to update ${controlType}: ${error.message || 'Unknown error'}`;
        this.render();
      }
    }, 500); // 500ms debounce
  }

  /**
   * Schedule vacation mode
   */
  async scheduleVacation() {
    if (!this.isControlsEnabled || !this.deviceService) return;

    const vacationDateControl = this.shadowRoot.querySelector('#vacation-date-control');
    if (!vacationDateControl) return;

    const returnDate = vacationDateControl.value;
    if (!returnDate) {
      this.controlsError = 'Please select a return date';
      this.render();
      return;
    }

    try {
      this.isUpdating = true;
      this.render();

      // Create update payload
      const updateData = {
        state: {
          mode: 'vacation',
          vacation_end_date: returnDate
        }
      };

      // Send update to server
      const updatedDevice = await this.deviceService.updateDevice(
        this.device.device_id,
        updateData
      );

      // Update local state
      this.updateDevice(updatedDevice);

      // Notify parent of control change
      if (this.onDeviceControlChange) {
        this.onDeviceControlChange('vacation_mode', {
          active: true,
          end_date: returnDate
        });
      }

      this.isUpdating = false;
      this.controlsError = null;
      this.render();
    } catch (error) {
      console.error('Error scheduling vacation mode:', error);
      this.isUpdating = false;
      this.controlsError = `Failed to schedule vacation mode: ${error.message || 'Unknown error'}`;
      this.render();
    }
  }

  /**
   * Render an overlay for disabled controls
   */
  renderDisabledOverlay() {
    return `
      <div class="controls-overlay">
        <div class="controls-overlay-message">
          <div>Device is disconnected</div>
          <div>Controls are currently disabled</div>
        </div>
      </div>
    `;
  }

  /**
   * Render updating indicator
   */
  renderUpdatingIndicator() {
    return `
      <div class="updating-indicator">
        <div class="updating-spinner"></div>
        <span>Updating...</span>
      </div>
    `;
  }

  /**
   * Get a value from device state with fallback
   */
  getDeviceStateValue(key, defaultValue) {
    if (!this.device || !this.device.state) return defaultValue;
    return this.device.state[key] !== undefined ? this.device.state[key] : defaultValue;
  }

  /**
   * Format mode value for display
   */
  formatMode(mode) {
    if (!mode) return 'Standard';

    // Format based on mode value
    switch (mode) {
      case 'standard':
        return 'Standard';
      case 'eco':
        return 'Eco';
      case 'vacation':
        return 'Vacation';
      case 'high_demand':
        return 'High Demand';
      default:
        // Title case any other values
        return mode.charAt(0).toUpperCase() + mode.slice(1);
    }
  }

  /**
   * Get today's date in YYYY-MM-DD format
   */
  getTodayDate() {
    const today = new Date();
    return today.toISOString().split('T')[0];
  }

  /**
   * Get tomorrow's date in YYYY-MM-DD format
   */
  getTomorrowDate() {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  }
}
