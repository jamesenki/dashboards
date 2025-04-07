/**
 * Mock Device Repository
 *
 * This file provides a mock implementation of the device repository
 * for use in BDD tests. It simulates the behavior of the real repository
 * but doesn't actually connect to the database.
 */

/**
 * Creates a mock device repository for testing
 */
function mockDeviceRepository() {
  // In-memory storage for registered devices
  const devices = new Map();

  // Mock capability definitions
  const capabilities = {
    'TEMPERATURE_CONTROL': {
      name: 'Temperature Control',
      commands: ['getTemperature', 'setTemperature', 'setMode'],
      telemetryTypes: ['temperature', 'setpoint', 'mode']
    },
    'ENERGY_MONITORING': {
      name: 'Energy Monitoring',
      commands: ['getEnergyUsage'],
      telemetryTypes: ['energyConsumed', 'powerLevel']
    },
    'WATER_LEVEL': {
      name: 'Water Level Monitoring',
      commands: ['getWaterLevel'],
      telemetryTypes: ['waterLevel', 'pressure']
    },
    'INVENTORY_MANAGEMENT': {
      name: 'Inventory Management',
      commands: ['getInventory', 'updateStock'],
      telemetryTypes: ['stockLevels', 'transactions']
    }
  };

  return {
    /**
     * Reset the mock to initial state
     */
    reset() {
      devices.clear();
    },

    /**
     * Register a new device
     * @param {Object} deviceData Device registration data
     * @returns {Promise<Object>} The registered device
     */
    async registerDevice(deviceData) {
      // Generate a unique ID if one is not provided
      const deviceId = deviceData.id || `device-${Date.now()}-${Math.floor(Math.random() * 1000)}`;

      // Determine device capabilities based on type
      let deviceCapabilities = [];

      if (deviceData.capabilities) {
        // Use explicitly provided capabilities
        deviceCapabilities = deviceData.capabilities;
      } else {
        // Assign default capabilities based on device type
        switch (deviceData.type) {
          case 'water-heater':
            deviceCapabilities = ['TEMPERATURE_CONTROL', 'ENERGY_MONITORING', 'WATER_LEVEL'];
            break;
          case 'vending-machine':
            deviceCapabilities = ['TEMPERATURE_CONTROL', 'INVENTORY_MANAGEMENT', 'ENERGY_MONITORING'];
            break;
          default:
            deviceCapabilities = [];
        }
      }

      // Create the device record
      const device = {
        id: deviceId,
        name: deviceData.name || `Device ${deviceId}`,
        type: deviceData.type,
        manufacturer: deviceData.manufacturer,
        model: deviceData.model,
        serialNumber: deviceData.serialNumber,
        firmwareVersion: deviceData.firmwareVersion || '1.0',
        capabilities: deviceCapabilities,
        status: 'REGISTERED',
        registrationDate: new Date().toISOString(),
        lastConnected: null,
        metadata: deviceData.metadata || {}
      };

      // Add device-type specific attributes
      if (deviceData.type === 'water-heater') {
        device.tankCapacity = deviceData.tankCapacity;
        device.temperature = deviceData.temperature || 120;
        device.mode = deviceData.mode || 'STANDARD';
      } else if (deviceData.type === 'vending-machine') {
        device.inventory = deviceData.inventory || [];
        device.cashBalance = deviceData.cashBalance || 0;
        device.slotCount = deviceData.slotCount || 20;
      }

      // Store the device
      devices.set(deviceId, device);

      return device;
    },

    /**
     * Find a device by ID
     * @param {string} deviceId The device ID
     * @returns {Promise<Object>} The device or null if not found
     */
    async findDeviceById(deviceId) {
      return devices.get(deviceId) || null;
    },

    /**
     * Find devices by criteria
     * @param {Object} criteria Search criteria
     * @returns {Promise<Array<Object>>} Matching devices
     */
    async findDevices(criteria = {}) {
      const result = [];

      for (const device of devices.values()) {
        let matches = true;

        // Check each criterion
        for (const [key, value] of Object.entries(criteria)) {
          if (device[key] !== value) {
            matches = false;
            break;
          }
        }

        if (matches) {
          result.push(device);
        }
      }

      return result;
    },

    /**
     * Update a device
     * @param {string} deviceId The device ID
     * @param {Object} updates The updates to apply
     * @returns {Promise<Object>} The updated device
     */
    async updateDevice(deviceId, updates) {
      const device = devices.get(deviceId);

      if (!device) {
        throw new Error(`Device not found: ${deviceId}`);
      }

      // Apply updates
      Object.assign(device, updates);

      return device;
    },

    /**
     * Get device capabilities
     * @param {string} deviceId The device ID
     * @returns {Promise<Array<Object>>} The device capabilities
     */
    async getDeviceCapabilities(deviceId) {
      const device = devices.get(deviceId);

      if (!device) {
        throw new Error(`Device not found: ${deviceId}`);
      }

      return device.capabilities.map(capabilityId => ({
        id: capabilityId,
        ...capabilities[capabilityId]
      }));
    }
  };
}

module.exports = { mockDeviceRepository };
