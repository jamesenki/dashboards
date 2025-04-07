/**
 * Device Metadata Handler
 * 
 * This component manages device metadata separate from device state,
 * following the architecture of separating static device information (metadata)
 * from dynamic device state (shadow documents).
 * 
 * It handles:
 * 1. Loading device metadata from the Asset DB
 * 2. Listening for real-time metadata change events
 * 3. Updating the UI with metadata information
 */
class DeviceMetadataHandler {
  /**
   * Initialize the Device Metadata Handler
   * @param {string} deviceId - The ID of the device to manage metadata for
   */
  constructor(deviceId) {
    this.deviceId = deviceId;
    this.metadata = null;
    this.ws = null;
    this.metadataConnectionStatus = false;
    
    // Initialize
    this.fetchMetadata().then(() => {
      this.updateMetadataDisplay();
      this.subscribeToMetadataChanges();
    }).catch(error => {
      console.error('Failed to initialize device metadata handler:', error);
      this.showMetadataError('Failed to load device metadata');
    });
  }
  
  /**
   * Fetch device metadata from the Asset DB
   * @returns {Promise} Promise that resolves when metadata is fetched
   */
  async fetchMetadata() {
    try {
      const response = await fetch(`/api/devices/${this.deviceId}/metadata`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch metadata: ${response.status}`);
      }
      
      this.metadata = await response.json();
      console.log('Device metadata loaded:', this.deviceId);
      return this.metadata;
    } catch (error) {
      console.error('Error fetching device metadata:', error);
      this.metadata = null;
      throw error;
    }
  }
  
  /**
   * Update the UI with the current device metadata
   */
  updateMetadataDisplay() {
    // If no metadata is available, show "Not available" in all fields
    if (!this.metadata) {
      document.querySelectorAll('#deviceMetadata [id^="device"]').forEach(el => {
        el.textContent = 'Not available';
      });
      return;
    }
    
    // Update basic metadata fields
    if (document.getElementById('deviceManufacturer')) {
      document.getElementById('deviceManufacturer').textContent = 
        `Manufacturer: ${this.metadata.manufacturer || 'Not specified'}`;
    }
    
    if (document.getElementById('deviceModel')) {
      document.getElementById('deviceModel').textContent = 
        `Model: ${this.metadata.model || 'Not specified'}`;
    }
    
    if (document.getElementById('deviceSerialNumber')) {
      document.getElementById('deviceSerialNumber').textContent = 
        `Serial Number: ${this.metadata.serial_number || 'Not specified'}`;
    }
    
    if (document.getElementById('deviceInstallationDate')) {
      // Format the date for display
      let installDate = 'Not specified';
      if (this.metadata.installation_date) {
        installDate = new Date(this.metadata.installation_date).toLocaleDateString();
      }
      document.getElementById('deviceInstallationDate').textContent = 
        `Installation Date: ${installDate}`;
    }
    
    // Update location information
    if (document.getElementById('deviceLocation') && this.metadata.location) {
      const location = this.metadata.location;
      let locationText = '';
      
      if (location.building) locationText += `Building: ${location.building}, `;
      if (location.floor) locationText += `Floor: ${location.floor}, `;
      if (location.room) locationText += `Room: ${location.room}`;
      
      document.getElementById('deviceLocation').textContent = locationText || 'Location not specified';
    }
    
    // Update specifications
    if (document.getElementById('deviceSpecifications') && this.metadata.specifications) {
      const specs = this.metadata.specifications;
      let specsText = '';
      
      if (specs.capacity) specsText += `Capacity: ${specs.capacity} gallons, `;
      if (specs.voltage) specsText += `Voltage: ${specs.voltage}V, `;
      if (specs.wattage) specsText += `Wattage: ${specs.wattage}W`;
      
      document.getElementById('deviceSpecifications').textContent = specsText || 'Specifications not available';
    }
    
    // Trigger a custom event for other components that might need to know
    // metadata has been updated
    document.dispatchEvent(new CustomEvent('deviceMetadataUpdated', {
      detail: { deviceId: this.deviceId, metadata: this.metadata }
    }));
  }
  
  /**
   * Subscribe to real-time metadata change events via WebSocket
   */
  subscribeToMetadataChanges() {
    // Close existing connection if any
    if (this.ws) {
      this.ws.close();
    }
    
    // Create a new WebSocket connection for metadata events
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/api/events/device/${this.deviceId}/metadata`;
    
    try {
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        console.log('Metadata event subscription established');
        this.updateMetadataConnectionStatus(true);
      };
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMetadataEvent(data);
        } catch (error) {
          console.error('Error processing metadata event:', error);
        }
      };
      
      this.ws.onclose = () => {
        console.log('Metadata event subscription closed');
        this.updateMetadataConnectionStatus(false);
        
        // Attempt to reconnect after a delay
        setTimeout(() => this.subscribeToMetadataChanges(), 5000);
      };
      
      this.ws.onerror = (error) => {
        console.error('Metadata WebSocket error:', error);
        this.updateMetadataConnectionStatus(false);
      };
    } catch (error) {
      console.error('Failed to create metadata WebSocket:', error);
      this.updateMetadataConnectionStatus(false);
    }
  }
  
  /**
   * Handle an incoming metadata change event
   * @param {Object} event - The metadata event data
   */
  handleMetadataEvent(event) {
    if (!event || !event.device_id || event.device_id !== this.deviceId) {
      return;
    }
    
    console.log(`Received metadata update for ${this.deviceId}:`, event);
    
    // Ensure we have metadata to update
    if (!this.metadata) {
      this.fetchMetadata().then(() => this.updateMetadataDisplay());
      return;
    }
    
    // Update the appropriate part of the metadata based on event type
    switch (event.change_type) {
      case 'location_update':
        this.metadata.location = event.new_value;
        break;
      
      case 'firmware_update':
        this.metadata.firmware_version = event.new_value;
        break;
      
      case 'maintenance_update':
        if (!this.metadata.maintenance) {
          this.metadata.maintenance = [];
        }
        this.metadata.maintenance.unshift(event.new_value);
        break;
      
      case 'specification_update':
        if (!this.metadata.specifications) {
          this.metadata.specifications = {};
        }
        // Merge the updated specifications
        this.metadata.specifications = {
          ...this.metadata.specifications,
          ...event.new_value
        };
        break;
      
      default:
        // For unknown event types, fetch the complete metadata
        this.fetchMetadata().then(() => this.updateMetadataDisplay());
        return;
    }
    
    // Update the UI with the new metadata
    this.updateMetadataDisplay();
    
    // Notify any integration points that metadata has changed
    this.notifyMetadataChanged(event.change_type);
  }
  
  /**
   * Update the metadata connection status indicator
   * @param {boolean} isConnected - Whether the metadata WebSocket is connected
   */
  updateMetadataConnectionStatus(isConnected) {
    this.metadataConnectionStatus = isConnected;
    
    // Update UI status indicator if available
    const statusIndicator = document.getElementById('metadataConnectionStatus');
    if (statusIndicator) {
      statusIndicator.className = isConnected ? 'connected' : 'disconnected';
      statusIndicator.textContent = isConnected ? 'Metadata: Connected' : 'Metadata: Disconnected';
    }
  }
  
  /**
   * Show an error message for metadata issues
   * @param {string} message - The error message to display
   */
  showMetadataError(message) {
    console.error('Metadata error:', message);
    
    // Display error in the UI if elements exist
    const metadataContainer = document.getElementById('deviceMetadata');
    if (metadataContainer) {
      metadataContainer.innerHTML = `
        <div class="error-message">
          <i class="fas fa-exclamation-triangle"></i>
          <span>${message}</span>
        </div>
      `;
    }
  }
  
  /**
   * Notify integration points that metadata has changed
   * @param {string} changeType - Type of metadata change
   */
  notifyMetadataChanged(changeType) {
    // Dispatch an event that other components can listen for
    document.dispatchEvent(new CustomEvent('deviceMetadataChanged', {
      detail: {
        deviceId: this.deviceId,
        changeType: changeType,
        metadata: this.metadata
      }
    }));
    
    // If we have a shadow document handler on the page, notify it
    // This enables coordination between state and metadata components
    if (window.shadowDocumentHandler) {
      window.shadowDocumentHandler.onMetadataChanged(this.metadata, changeType);
    }
  }
}

// Export for testing in Node.js environment
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DeviceMetadataHandler;
}
