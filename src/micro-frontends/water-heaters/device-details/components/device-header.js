/**
 * Device Header Component
 * 
 * Displays the header for a specific water heater device with basic information
 * and quick actions. Part of the device-agnostic architecture.
 */
export class DeviceHeader extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    
    // Component state
    this.device = null;
    this.deviceService = null;
    this.isEditing = false;
  }
  
  /**
   * Initialize the component with device data and services
   */
  initialize({ device, deviceService }) {
    this.device = device;
    this.deviceService = deviceService;
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
    this.device = updatedDevice;
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
      
      .device-header {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        position: relative;
      }
      
      .device-header-content {
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      
      .device-info {
        display: flex;
        align-items: center;
      }
      
      .device-icon {
        background-color: #E3F2FD;
        color: #2196F3;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 1rem;
        font-size: 1.5rem;
      }
      
      .device-text {
        flex: 1;
      }
      
      .device-name {
        font-size: 1.5rem;
        font-weight: 500;
        margin: 0 0 0.5rem 0;
        display: flex;
        align-items: center;
      }
      
      .device-name-display {
        margin-right: 0.5rem;
      }
      
      .edit-name-form {
        display: flex;
        align-items: center;
        margin-bottom: 0.5rem;
      }
      
      .edit-name-input {
        font-size: 1.25rem;
        padding: 0.25rem 0.5rem;
        margin-right: 0.5rem;
        width: 300px;
        border: 1px solid #2196F3;
        border-radius: 4px;
      }
      
      .edit-button {
        background: none;
        border: none;
        color: #757575;
        cursor: pointer;
        padding: 0.25rem;
        margin-left: 0.5rem;
      }
      
      .edit-button:hover {
        color: #2196F3;
      }
      
      .save-button, .cancel-button {
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.875rem;
      }
      
      .save-button {
        background-color: #2196F3;
        color: white;
        border: none;
        margin-right: 0.5rem;
      }
      
      .save-button:hover {
        background-color: #1976D2;
      }
      
      .cancel-button {
        background-color: #F5F5F5;
        color: #757575;
        border: 1px solid #E0E0E0;
      }
      
      .cancel-button:hover {
        background-color: #EEEEEE;
      }
      
      .device-meta {
        color: #757575;
        font-size: 0.9rem;
      }
      
      .device-meta span:not(:last-child)::after {
        content: '•';
        margin: 0 0.5rem;
      }
      
      .device-actions {
        display: flex;
        gap: 0.5rem;
      }
      
      .action-button {
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #f5f5f5;
        color: #424242;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
        cursor: pointer;
        transition: background-color 0.2s, color 0.2s;
      }
      
      .action-button:hover {
        background-color: #e0e0e0;
      }
      
      .action-button.primary {
        background-color: #2196F3;
        color: white;
      }
      
      .action-button.primary:hover {
        background-color: #1976D2;
      }
      
      .action-button.danger {
        background-color: #FFEBEE;
        color: #F44336;
      }
      
      .action-button.danger:hover {
        background-color: #FFCDD2;
      }
      
      .device-status {
        display: flex;
        align-items: center;
        margin-left: 1rem;
      }
      
      .status-indicator {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 0.5rem;
      }
      
      .status-indicator.connected {
        background-color: #4CAF50;
      }
      
      .status-indicator.disconnected {
        background-color: #F44336;
      }
      
      .simulation-badge {
        background-color: #673AB7;
        color: white;
        font-size: 0.7rem;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        margin-left: 0.5rem;
      }
    `;
    
    // Define HTML template
    const template = this.isEditing ? this.renderEditMode() : this.renderViewMode();
    
    // Set the shadow DOM content
    this.shadowRoot.innerHTML = `<style>${styles}</style>${template}`;
    
    // Add event listeners
    if (this.isEditing) {
      this.addEditModeEventListeners();
    } else {
      this.addViewModeEventListeners();
    }
  }
  
  /**
   * Render component in view mode
   */
  renderViewMode() {
    return `
      <div class="device-header">
        <div class="device-header-content">
          <div class="device-info">
            <div class="device-icon">
              <span>WH</span>
            </div>
            <div class="device-text">
              <h2 class="device-name">
                <span class="device-name-display">${this.device.display_name || this.getDefaultDeviceName()}</span>
                <button class="edit-button" id="edit-name-button">
                  <span>✏️</span>
                </button>
                
                <!-- Status indicator -->
                <div class="device-status">
                  <div class="status-indicator ${this.device.connection_status}"></div>
                  <span>${this.device.connection_status}</span>
                  ${this.device.simulated ? '<span class="simulation-badge">SIMULATED</span>' : ''}
                </div>
              </h2>
              <div class="device-meta">
                <span>${this.device.manufacturer} ${this.device.model}</span>
                <span>ID: ${this.device.device_id}</span>
                ${this.device.location ? `<span>Location: ${this.device.location}</span>` : ''}
                ${this.device.last_maintenance_date ? 
                  `<span>Last maintenance: ${new Date(this.device.last_maintenance_date).toLocaleDateString()}</span>` : ''}
              </div>
            </div>
          </div>
          
          <div class="device-actions">
            <button class="action-button" id="refresh-device-button">
              <span>🔄</span> Refresh
            </button>
            <button class="action-button primary" id="control-device-button">
              <span>🎮</span> Control
            </button>
            ${this.device.connection_status === 'disconnected' ? `
              <button class="action-button" id="reconnect-device-button">
                <span>🔌</span> Reconnect
              </button>
            ` : ''}
          </div>
        </div>
      </div>
    `;
  }
  
  /**
   * Render component in edit mode
   */
  renderEditMode() {
    return `
      <div class="device-header">
        <div class="device-header-content">
          <div class="device-info">
            <div class="device-icon">
              <span>WH</span>
            </div>
            <div class="device-text">
              <div class="edit-name-form">
                <input 
                  type="text" 
                  class="edit-name-input" 
                  id="device-name-input" 
                  value="${this.device.display_name || this.getDefaultDeviceName()}"
                  placeholder="Enter device name"
                >
                <button class="save-button" id="save-name-button">Save</button>
                <button class="cancel-button" id="cancel-edit-button">Cancel</button>
              </div>
              <div class="device-meta">
                <span>${this.device.manufacturer} ${this.device.model}</span>
                <span>ID: ${this.device.device_id}</span>
                ${this.device.location ? `<span>Location: ${this.device.location}</span>` : ''}
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }
  
  /**
   * Add event listeners for view mode
   */
  addViewModeEventListeners() {
    // Edit name button
    const editNameButton = this.shadowRoot.querySelector('#edit-name-button');
    if (editNameButton) {
      editNameButton.addEventListener('click', () => {
        this.isEditing = true;
        this.render();
        
        // Focus the input after rendering
        setTimeout(() => {
          const input = this.shadowRoot.querySelector('#device-name-input');
          if (input) input.focus();
        }, 0);
      });
    }
    
    // Refresh device button
    const refreshButton = this.shadowRoot.querySelector('#refresh-device-button');
    if (refreshButton) {
      refreshButton.addEventListener('click', async () => {
        try {
          if (this.deviceService) {
            const refreshedDevice = await this.deviceService.getDevice(this.device.device_id);
            this.updateDevice(refreshedDevice);
          }
        } catch (error) {
          console.error('Error refreshing device:', error);
          // Display error notification
        }
      });
    }
    
    // Control device button
    const controlButton = this.shadowRoot.querySelector('#control-device-button');
    if (controlButton) {
      controlButton.addEventListener('click', () => {
        // Dispatch event to scroll to controls section
        this.dispatchEvent(new CustomEvent('navigate-to-controls', {
          bubbles: true,
          composed: true
        }));
      });
    }
    
    // Reconnect device button (if device is disconnected)
    const reconnectButton = this.shadowRoot.querySelector('#reconnect-device-button');
    if (reconnectButton) {
      reconnectButton.addEventListener('click', async () => {
        try {
          if (this.deviceService) {
            // Send reconnect command to the device
            await this.deviceService.updateDevice(this.device.device_id, {
              command: 'reconnect'
            });
            
            // Refresh device data
            const refreshedDevice = await this.deviceService.getDevice(this.device.device_id);
            this.updateDevice(refreshedDevice);
          }
        } catch (error) {
          console.error('Error reconnecting device:', error);
          // Display error notification
        }
      });
    }
  }
  
  /**
   * Add event listeners for edit mode
   */
  addEditModeEventListeners() {
    // Save button
    const saveButton = this.shadowRoot.querySelector('#save-name-button');
    if (saveButton) {
      saveButton.addEventListener('click', () => {
        this.saveDeviceName();
      });
    }
    
    // Cancel button
    const cancelButton = this.shadowRoot.querySelector('#cancel-edit-button');
    if (cancelButton) {
      cancelButton.addEventListener('click', () => {
        this.isEditing = false;
        this.render();
      });
    }
    
    // Input keypress events
    const input = this.shadowRoot.querySelector('#device-name-input');
    if (input) {
      input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          this.saveDeviceName();
        } else if (e.key === 'Escape') {
          this.isEditing = false;
          this.render();
        }
      });
    }
  }
  
  /**
   * Save the device name
   */
  async saveDeviceName() {
    const input = this.shadowRoot.querySelector('#device-name-input');
    const newName = input?.value.trim();
    
    if (newName && this.deviceService) {
      try {
        // Update device name
        const updatedDevice = await this.deviceService.updateDevice(this.device.device_id, {
          display_name: newName
        });
        
        // Exit edit mode and update view
        this.isEditing = false;
        this.updateDevice(updatedDevice);
      } catch (error) {
        console.error('Error updating device name:', error);
        // Display error notification
      }
    } else {
      // Exit edit mode without saving
      this.isEditing = false;
      this.render();
    }
  }
  
  /**
   * Get default device name from manufacturer and model
   */
  getDefaultDeviceName() {
    return `${this.device.manufacturer} ${this.device.model}`;
  }
}
