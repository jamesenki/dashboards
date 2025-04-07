/**
 * Mock Telemetry Service
 *
 * This file provides a mock implementation of the telemetry service
 * for use in BDD tests. It simulates the behavior of the real service
 * without actually connecting to any devices.
 */

/**
 * Creates a mock telemetry service for testing
 */
function mockTelemetryService() {
  // In-memory storage for telemetry data
  const telemetryData = new Map();

  // Mock telemetry patterns for different device types
  const telemetryPatterns = {
    'water-heater': {
      temperature: () => 120 + (Math.random() * 10 - 5), // Random around 120°F
      pressure: () => 45 + (Math.random() * 5 - 2.5),    // Random around 45 PSI
      energyConsumed: (previousValue = 0) => previousValue + (Math.random() * 0.2), // Increasing value
      mode: () => ['STANDARD', 'ECO', 'VACATION'][Math.floor(Math.random() * 3)]
    },
    'vending-machine': {
      temperature: () => 34 + (Math.random() * 6 - 3),   // Random around 34°F (refrigerated)
      stockLevels: (previousValue = {}) => {
        // Simulate random product sales
        const result = { ...previousValue };
        const slots = Object.keys(result);
        if (slots.length > 0) {
          const randomSlot = slots[Math.floor(Math.random() * slots.length)];
          if (result[randomSlot] > 0) {
            result[randomSlot] -= 1;
          }
        }
        return result;
      },
      transactions: (previousValue = 0) => previousValue + (Math.random() > 0.7 ? 1 : 0), // Occasional new transaction
      cashBalance: (previousValue = 0) => previousValue + (Math.random() > 0.7 ? (Math.random() * 3 + 1) : 0) // Occasional cash increase
    }
  };

  /**
   * Add historical telemetry data for a device
   * @param {string} deviceId - The ID of the device
   * @param {Object} data - The telemetry data to add
   * @param {Date} timestamp - Optional timestamp for the data (defaults to now)
   * @returns {Promise<void>}
   */
  async function addHistoricalTelemetry(deviceId, data, timestamp = new Date()) {
    if (!telemetryData.has(deviceId)) {
      telemetryData.set(deviceId, []);
    }

    const telemetryEntry = {
      ...data,
      timestamp: timestamp instanceof Date ? timestamp : new Date(timestamp),
      deviceId
    };

    const deviceTelemetry = telemetryData.get(deviceId);

    // Insert in chronological order
    let insertIndex = deviceTelemetry.length;
    for (let i = 0; i < deviceTelemetry.length; i++) {
      if (telemetryEntry.timestamp < deviceTelemetry[i].timestamp) {
        insertIndex = i;
        break;
      }
    }

    deviceTelemetry.splice(insertIndex, 0, telemetryEntry);
    return Promise.resolve();
  }

  /**
   * Generate operational history for a device over a time period
   * @param {string} deviceId - The ID of the device
   * @param {Date} startDate - Start date for the history
   * @param {Date} endDate - End date for the history
   * @returns {Promise<void>}
   */
  /**
   * Generate a minimal operational history for a device - ultra lightweight version
   * @param {string} deviceId - The device ID
   * @param {Date} startDate - Start date for history
   * @param {Date} endDate - End date for history
   * @returns {Promise<void>}
   */
  async function generateOperationalHistory(deviceId, startDate, endDate) {
    // For BDD testing, we don't need to generate actual historical data
    // Just store a flag indicating the device has history
    telemetryData.set(deviceId, true);

    // When needed, we'll return static pre-defined data instead of generating it
    return Promise.resolve();
  }

  /**
   * Generate maintenance history for a device
   * @param {string} deviceId - The ID of the device
   * @param {Date} startDate - Start date for the history
   * @param {Date} endDate - End date for the history
   * @returns {Promise<void>}
   */
  async function generateMaintenanceHistory(deviceId, startDate, endDate) {
    // This is a placeholder since we'll add maintenance records in the step definition
    return Promise.resolve();
  }

  /**
   * Generate reliability metrics for a device
   * @param {string} deviceId - The ID of the device
   * @param {Date} startDate - Start date for the history
   * @param {Date} endDate - End date for the history
   * @returns {Promise<void>}
   */
  async function generateReliabilityMetrics(deviceId, startDate, endDate) {
    // This is a placeholder since we'll generate metrics in the mock analytics engine
    return Promise.resolve();
  }

  return {
    /**
     * Reset the mock to initial state
     */
    reset() {
      telemetryData.clear();
    },

    /**
     * Get the current telemetry for a device
     * @param {string} deviceId The device ID
     * @returns {Promise<Object>} The current telemetry data
     */
    async getCurrentTelemetry(deviceId) {
      return telemetryData.get(deviceId) || {};
    },

    /**
     * Get historical telemetry for a device
     * @param {string} deviceId The device ID
     * @param {Date} startDate Start date for the telemetry data
     * @param {Date} endDate End date for the telemetry data
     * @returns {Promise<Array<Object>>} Historical telemetry data
     */
    async getHistoricalTelemetry(deviceId, startDate, endDate) {
      // Mark that this device has been queried
      if (!telemetryData.has(deviceId)) {
        await generateOperationalHistory(deviceId, startDate, endDate);
      }

      // Instead of generating and storing actual telemetry data,
      // just return a pre-defined static dataset using the date range
      const actualStartDate = startDate instanceof Date ? startDate : new Date(startDate);
      const actualEndDate = endDate instanceof Date ? endDate : new Date(endDate);
      const timeSpan = actualEndDate.getTime() - actualStartDate.getTime();

      // Get device type from deviceId
      const isVendingMachine = deviceId.includes('vending');

      // Return static data for water heaters or vending machines
      return [
        // First data point at start date
        {
          timestamp: actualStartDate,
          deviceId,
          ...(isVendingMachine ? {
            temperature: 38,
            doorStatus: 'CLOSED',
            inventoryLevel: 85,
            cashBalance: 124.50,
            transactions: 42
          } : {
            temperature: 120,
            pressure: 40,
            flowRate: 2.5,
            energyConsumed: 2.1,
            waterVolume: 40
          })
        },
        // Midpoint with anomaly
        {
          timestamp: new Date(actualStartDate.getTime() + timeSpan / 2),
          deviceId,
          ...(isVendingMachine ? {
            temperature: 48, // Anomaly
            doorStatus: 'OPEN',
            inventoryLevel: 80,
            cashBalance: 130.00,
            transactions: 45
          } : {
            temperature: 150, // Anomaly
            pressure: 65, // Anomaly
            flowRate: 2.8,
            energyConsumed: 3.2,
            waterVolume: 38
          })
        },
        // End date point
        {
          timestamp: actualEndDate,
          deviceId,
          ...(isVendingMachine ? {
            temperature: 37,
            doorStatus: 'CLOSED',
            inventoryLevel: 75,
            cashBalance: 142.50,
            transactions: 48
          } : {
            temperature: 122,
            pressure: 41,
            flowRate: 2.6,
            energyConsumed: 4.5,
            waterVolume: 38
          })
        }
      ];
    },

    /**
     * Generate simulated telemetry for a device
     * @param {Object} device The device object
     * @param {string} deviceType The device type
     * @returns {Promise<Object>} The generated telemetry
     */
    async generateTelemetry(device, deviceType = 'water-heater') {
      const deviceId = device.id;

      // Return static telemetry data based on device type
      // No data generation or storage - just static pre-defined values
      if (deviceType === 'vending-machine' || deviceId.includes('vending')) {
        return {
          deviceId,
          timestamp: new Date().toISOString(),
          temperature: 38,
          doorStatus: 'CLOSED',
          inventoryLevel: 85,
          cashBalance: 124.50,
          transactions: 42
        };
      } else {
        return {
          deviceId,
          timestamp: new Date().toISOString(),
          temperature: 120,
          pressure: 40,
          flowRate: 2.5,
          energyConsumed: 2.1,
          waterVolume: 40
        };
      }
    },

    /**
     * Subscribe to telemetry updates for a device
     * @param {string} deviceId The device ID
     * @param {Function} callback The callback to invoke with updates
     * @returns {Object} A subscription object with an unsubscribe method
     */
    subscribeTelemetry(deviceId, callback) {
      // In a real implementation, this would set up a subscription
      // For the mock, we'll just return an object with an unsubscribe method
      return {
        unsubscribe: () => {}
      };
    },

    // Add new functions to the exported object
    addHistoricalTelemetry,
    generateOperationalHistory,
    generateMaintenanceHistory,
    generateReliabilityMetrics,

    /**
     * Add telemetry data for a device - alias for addHistoricalTelemetry
     * @param {string} deviceId - The ID of the device
     * @param {Object} data - The telemetry data to add
     * @returns {Promise<void>}
     */
    addTelemetryData: async function(deviceId, data) {
      return addHistoricalTelemetry(deviceId, data);
    },

    /**
     * Add a single telemetry data point for a device
     * @param {string} deviceId - The ID of the device
     * @param {string} dataType - The type of data (temperature, pressure, etc.)
     * @param {any} value - The value of the data point
     * @param {Date} timestamp - Optional timestamp for the data point
     * @returns {Promise<void>}
     */
    addTelemetryDataPoint: async function(deviceId, dataType, value, timestamp = new Date()) {
      const data = {};
      data[dataType] = value;
      return addHistoricalTelemetry(deviceId, data, timestamp);
    }
  };
}

module.exports = { mockTelemetryService };
