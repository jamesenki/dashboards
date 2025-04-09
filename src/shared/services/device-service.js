/**
 * Device Service
 *
 * Provides an API for interacting with IoT devices in the system
 * Part of the device-agnostic architecture, designed to support multiple device types
 */
export class DeviceService {
  /**
   * Create a new DeviceService instance
   *
   * @param {Object} config - Service configuration
   * @param {string} config.endpoint - API endpoint for device operations
   * @param {string} config.deviceType - Type of device (e.g., 'water-heater', 'vending-machine')
   * @param {Object} config.auth - Authentication details
   */
  constructor({ endpoint, deviceType, auth }) {
    this.endpoint = endpoint || '/api/devices';
    this.deviceType = deviceType;
    this.auth = auth;

    // Cache for device data
    this.deviceCache = new Map();
    this.manufacturersCache = null;
  }

  /**
   * Get a list of all devices of the specified type
   *
   * @returns {Promise<Array>} - List of devices
   */
  async getDevices() {
    try {
      const url = this.deviceType
        ? `${this.endpoint}?type=${this.deviceType}`
        : this.endpoint;

      const response = await fetch(url, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch devices: ${response.statusText}`);
      }

      const devices = await response.json();

      // Update cache
      devices.forEach(device => {
        this.deviceCache.set(device.device_id, device);
      });

      return devices;
    } catch (error) {
      console.error('Error fetching devices:', error);
      throw error;
    }
  }

  /**
   * Get a device by ID
   *
   * @param {string} deviceId - The ID of the device to retrieve
   * @returns {Promise<Object>} - Device data
   */
  async getDevice(deviceId) {
    // Check cache first
    if (this.deviceCache.has(deviceId)) {
      return this.deviceCache.get(deviceId);
    }

    try {
      const response = await fetch(`${this.endpoint}/${deviceId}`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch device ${deviceId}: ${response.statusText}`);
      }

      const device = await response.json();

      // Update cache
      this.deviceCache.set(deviceId, device);

      return device;
    } catch (error) {
      console.error(`Error fetching device ${deviceId}:`, error);
      throw error;
    }
  }

  /**
   * Get a summary of device metrics
   *
   * @returns {Promise<Object>} - Summary metrics
   */
  async getDevicesSummary() {
    try {
      // First get all devices if we don't have them cached
      let devices = [];
      const cachedDevices = Array.from(this.deviceCache.values());

      if (cachedDevices.length > 0) {
        devices = cachedDevices;
      } else {
        devices = await this.getDevices();
      }

      // Calculate summary metrics
      const summary = {
        totalDevices: devices.length,
        connectedDevices: devices.filter(d => d.connection_status === 'connected').length,
        disconnectedDevices: devices.filter(d => d.connection_status === 'disconnected').length,
        simulatedDevices: devices.filter(d => d.simulated).length
      };

      return summary;
    } catch (error) {
      console.error('Error generating device summary:', error);
      throw error;
    }
  }

  /**
   * Get a list of unique manufacturers
   *
   * @returns {Promise<Array<string>>} - List of manufacturer names
   */
  async getManufacturers() {
    // Return cached manufacturers if available
    if (this.manufacturersCache) {
      return this.manufacturersCache;
    }

    try {
      // First get all devices if we don't have them cached
      let devices = [];
      const cachedDevices = Array.from(this.deviceCache.values());

      if (cachedDevices.length > 0) {
        devices = cachedDevices;
      } else {
        devices = await this.getDevices();
      }

      // Extract unique manufacturers
      const manufacturerSet = new Set(
        devices.map(device => device.manufacturer).filter(Boolean)
      );

      const manufacturers = Array.from(manufacturerSet).sort();

      // Update cache
      this.manufacturersCache = manufacturers;

      return manufacturers;
    } catch (error) {
      console.error('Error getting manufacturers:', error);
      throw error;
    }
  }

  /**
   * Update a device
   *
   * @param {string} deviceId - The ID of the device to update
   * @param {Object} updateData - The data to update
   * @returns {Promise<Object>} - Updated device data
   */
  async updateDevice(deviceId, updateData) {
    try {
      const response = await fetch(`${this.endpoint}/${deviceId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...this.getAuthHeaders()
        },
        body: JSON.stringify(updateData)
      });

      if (!response.ok) {
        throw new Error(`Failed to update device ${deviceId}: ${response.statusText}`);
      }

      const updatedDevice = await response.json();

      // Update cache
      this.deviceCache.set(deviceId, updatedDevice);

      return updatedDevice;
    } catch (error) {
      console.error(`Error updating device ${deviceId}:`, error);
      throw error;
    }
  }

  /**
   * Add a new device
   *
   * @param {Object} deviceData - The device data to add
   * @returns {Promise<Object>} - Added device data
   */
  async addDevice(deviceData) {
    try {
      // Ensure device type is set
      const newDeviceData = {
        ...deviceData,
        device_type: deviceData.device_type || this.deviceType
      };

      const response = await fetch(this.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.getAuthHeaders()
        },
        body: JSON.stringify(newDeviceData)
      });

      if (!response.ok) {
        throw new Error(`Failed to add device: ${response.statusText}`);
      }

      const addedDevice = await response.json();

      // Update cache
      this.deviceCache.set(addedDevice.device_id, addedDevice);

      // Invalidate manufacturers cache if a new manufacturer is added
      if (addedDevice.manufacturer &&
          this.manufacturersCache &&
          !this.manufacturersCache.includes(addedDevice.manufacturer)) {
        this.manufacturersCache = null;
      }

      return addedDevice;
    } catch (error) {
      console.error('Error adding device:', error);
      throw error;
    }
  }

  /**
   * Delete a device
   *
   * @param {string} deviceId - The ID of the device to delete
   * @returns {Promise<boolean>} - Success status
   */
  async deleteDevice(deviceId) {
    try {
      const response = await fetch(`${this.endpoint}/${deviceId}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to delete device ${deviceId}: ${response.statusText}`);
      }

      // Remove from cache
      this.deviceCache.delete(deviceId);

      // Invalidate manufacturers cache
      this.manufacturersCache = null;

      return true;
    } catch (error) {
      console.error(`Error deleting device ${deviceId}:`, error);
      throw error;
    }
  }

  /**
   * Get auth headers for API requests
   *
   * @returns {Object} - Authentication headers
   */
  getAuthHeaders() {
    if (!this.auth) return {};

    return {
      'Authorization': `Bearer ${this.auth.token}`
    };
  }

  /**
   * Clear the device cache
   */
  clearCache() {
    this.deviceCache.clear();
    this.manufacturersCache = null;
  }
}
