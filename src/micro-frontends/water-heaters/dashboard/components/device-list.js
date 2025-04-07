/**
 * Device List Component
 * 
 * Displays a grid of water heater devices with real-time status updates
 * Part of the device-agnostic IoTSphere platform architecture
 */
export class DeviceListComponent extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    
    // Component state
    this.devices = [];
    this.filteredDevices = [];
    this.isLoading = true;
    this.error = null;
    this.activeFilters = {};
    
    // Services will be injected
    this.deviceService = null;
    this.telemetryService = null;
    this.onDeviceSelected = null;
    
    // Real-time update subscription references
    this.telemetrySubscriptions = new Map();
  }
  
  /**
   * Initialize the component with services and event handlers
   */
  initialize({ deviceService, telemetryService, onDeviceSelected }) {
    this.deviceService = deviceService;
    this.telemetryService = telemetryService;
    this.onDeviceSelected = onDeviceSelected;
    
    this.render();
  }
  
  /**
   * Called when the element is connected to the DOM
   */
  connectedCallback() {
    this.render();
  }
  
  /**
   * Called when the element is disconnected from the DOM
   */
  disconnectedCallback() {
    // Clean up subscriptions
    this.unsubscribeFromTelemetry();
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
      
      .device-list-container {
        position: relative;
      }
      
      .device-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 1.5rem;
        margin-top: 1.5rem;
      }
      
      .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 3rem;
        color: var(--text-secondary, #757575);
      }
      
      .loading-spinner {
        width: 40px;
        height: 40px;
        border: 4px solid rgba(33, 150, 243, 0.2);
        border-top: 4px solid var(--primary-color, #2196F3);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 1rem;
      }
      
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
      
      .error-container {
        padding: 2rem;
        background-color: var(--error-light, #FFEBEE);
        color: var(--error-color, #F44336);
        border-radius: 8px;
        text-align: center;
        margin: 1.5rem 0;
      }
      
      .error-container button {
        margin-top: 1rem;
        padding: 0.5rem 1rem;
        background-color: var(--primary-color, #2196F3);
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
      }
      
      .no-devices {
        padding: 3rem;
        background-color: white;
        border-radius: 8px;
        text-align: center;
        margin: 1.5rem 0;
        color: var(--text-secondary, #757575);
      }
      
      /* Empty slot styles for device status cards */
      ::slotted(device-status-card) {
        width: 100%;
      }
    `;
    
    // Define HTML template
    const template = `
      <div class="device-list-container">
        ${this.isLoading ? this.renderLoading() : ''}
        ${this.error ? this.renderError() : ''}
        ${!this.isLoading && !this.error && this.filteredDevices.length === 0 
          ? this.renderNoDevices() 
          : ''}
        
        ${!this.isLoading && !this.error && this.filteredDevices.length > 0 
          ? this.renderDevices() 
          : ''}
      </div>
    `;
    
    // Set the shadow DOM content
    this.shadowRoot.innerHTML = `<style>${styles}</style>${template}`;
    
    // Add event listeners to device cards if devices are rendered
    if (!this.isLoading && !this.error && this.filteredDevices.length > 0) {
      this.addEventListeners();
    }
  }
  
  /**
   * Render the loading state
   */
  renderLoading() {
    return `
      <div class="loading-container">
        <div class="loading-spinner"></div>
        <div>Loading devices...</div>
      </div>
    `;
  }
  
  /**
   * Render the error state
   */
  renderError() {
    return `
      <div class="error-container">
        <div>${this.error}</div>
        <button id="retry-button">Retry</button>
      </div>
    `;
  }
  
  /**
   * Render the empty state when no devices are found
   */
  renderNoDevices() {
    if (Object.keys(this.activeFilters).length > 0) {
      return `
        <div class="no-devices">
          <div>No devices match your filters.</div>
          <button id="clear-filters-button">Clear Filters</button>
        </div>
      `;
    } else {
      return `
        <div class="no-devices">
          <div>No devices found.</div>
          <div>Add your first water heater to get started.</div>
        </div>
      `;
    }
  }
  
  /**
   * Render the devices grid
   */
  renderDevices() {
    return `
      <div class="device-grid">
        ${this.filteredDevices.map(device => this.renderDeviceCard(device)).join('')}
      </div>
    `;
  }
  
  /**
   * Render a single device card
   */
  renderDeviceCard(device) {
    return `
      <device-status-card
        id="device-${device.device_id}"
        device-id="${device.device_id}"
        device-name="${device.display_name || `${device.manufacturer} ${device.model}`}"
        manufacturer="${device.manufacturer}"
        model="${device.model}"
        connection-status="${device.connection_status}"
        ?simulated="${device.simulated}"
      ></device-status-card>
    `;
  }
  
  /**
   * Add event listeners to rendered elements
   */
  addEventListeners() {
    // Retry button for error state
    const retryButton = this.shadowRoot.querySelector('#retry-button');
    if (retryButton) {
      retryButton.addEventListener('click', () => this.refresh());
    }
    
    // Clear filters button for empty state
    const clearFiltersButton = this.shadowRoot.querySelector('#clear-filters-button');
    if (clearFiltersButton) {
      clearFiltersButton.addEventListener('click', () => {
        this.activeFilters = {};
        this.filterDevices();
        
        // Dispatch custom event to notify parent components
        this.dispatchEvent(new CustomEvent('filters-cleared'));
      });
    }
    
    // Add click listeners to each device card
    this.filteredDevices.forEach(device => {
      const card = this.shadowRoot.querySelector(`#device-${device.device_id}`);
      if (card) {
        card.addEventListener('click', () => {
          if (this.onDeviceSelected) {
            this.onDeviceSelected(device.device_id);
          }
        });
      }
    });
  }
  
  /**
   * Load devices from the device service
   */
  async refresh() {
    this.isLoading = true;
    this.error = null;
    this.render();
    
    try {
      // Unsubscribe from previous telemetry subscriptions
      this.unsubscribeFromTelemetry();
      
      // Fetch devices from the service
      this.devices = await this.deviceService.getDevices();
      
      // Apply any active filters
      this.filterDevices();
      
      // Subscribe to telemetry for each device
      this.subscribeToTelemetry();
      
      this.isLoading = false;
      this.render();
    } catch (error) {
      console.error('Error loading devices:', error);
      this.error = 'Failed to load devices. Please try again.';
      this.isLoading = false;
      this.render();
    }
  }
  
  /**
   * Subscribe to real-time telemetry updates for devices
   */
  subscribeToTelemetry() {
    if (!this.telemetryService) return;
    
    this.filteredDevices.forEach(device => {
      const subscription = this.telemetryService.subscribeToDeviceTelemetry(
        device.device_id, 
        (telemetryData) => {
          // Update the device status card with new telemetry data
          const deviceCard = this.shadowRoot.querySelector(`#device-${device.device_id}`);
          if (deviceCard) {
            deviceCard.updateTelemetry(telemetryData);
          }
        }
      );
      
      this.telemetrySubscriptions.set(device.device_id, subscription);
    });
  }
  
  /**
   * Unsubscribe from all telemetry updates
   */
  unsubscribeFromTelemetry() {
    if (!this.telemetryService) return;
    
    this.telemetrySubscriptions.forEach((subscription, deviceId) => {
      this.telemetryService.unsubscribe(subscription);
    });
    
    this.telemetrySubscriptions.clear();
  }
  
  /**
   * Apply filters to the device list
   */
  applyFilters(filters) {
    this.activeFilters = filters;
    this.filterDevices();
    this.render();
    
    // Update telemetry subscriptions for the filtered devices
    this.unsubscribeFromTelemetry();
    this.subscribeToTelemetry();
  }
  
  /**
   * Filter devices based on active filters
   */
  filterDevices() {
    this.filteredDevices = this.devices.filter(device => {
      // If no filters are active, show all devices
      if (Object.keys(this.activeFilters).length === 0) {
        return true;
      }
      
      // Check each filter
      for (const [key, value] of Object.entries(this.activeFilters)) {
        if (key === 'manufacturer' && device.manufacturer !== value) {
          return false;
        }
        
        if (key === 'connectionStatus' && device.connection_status !== value) {
          return false;
        }
        
        if (key === 'onlySimulated' && value === true && !device.simulated) {
          return false;
        }
      }
      
      return true;
    });
  }
  
  /**
   * Update a single device in the list
   */
  updateDevice(updatedDevice) {
    // Find the device in the list
    const index = this.devices.findIndex(d => d.device_id === updatedDevice.device_id);
    
    if (index !== -1) {
      // Update the device
      this.devices[index] = updatedDevice;
      
      // Apply filters to update the filtered list
      this.filterDevices();
      
      // Find the device card and update it
      const deviceCard = this.shadowRoot.querySelector(`#device-${updatedDevice.device_id}`);
      if (deviceCard) {
        deviceCard.updateDevice(updatedDevice);
      } else {
        // If the card isn't in the DOM (possibly due to filtering), re-render
        this.render();
      }
    }
  }
}
