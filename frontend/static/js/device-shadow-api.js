/**
 * Device Shadow API Client
 *
 * Provides functions to interact with the device shadow API endpoints
 */

class DeviceShadowApi {
  /**
   * Initialize the device shadow API client
   * @param {Object} options - API options
   */
  constructor(options = {}) {
    this.baseUrl = options.baseUrl || '';
    this.endpoints = {
      // Try multiple possible API endpoints in order of preference
      shadow: [
        '/api/device-shadows/{device_id}',
        '/api/shadows/{device_id}',
        '/api/manufacturer/water-heaters/{device_id}/shadow'
      ],
      tempHistory: [
        '/api/manufacturer/water-heaters/{device_id}/history/temperature',
        '/api/device-shadows/{device_id}/temperature-history',
        '/api/shadows/{device_id}/history',
        '/api/manufacturer/water-heaters/{device_id}/temperature-history'
      ]
    };

    this.cachedEndpoints = {};
  }

  /**
   * Format an endpoint URL with parameters
   * @param {string} endpoint - Endpoint template
   * @param {Object} params - Parameters to substitute
   * @returns {string} - Formatted URL
   */
  formatEndpoint(endpoint, params) {
    let result = endpoint;

    // Replace parameters in URL template
    for (const [key, value] of Object.entries(params)) {
      result = result.replace(`{${key}}`, encodeURIComponent(value));
    }

    // Add base URL if provided
    if (this.baseUrl && !result.startsWith('http')) {
      result = this.baseUrl + result;
    }

    return result;
  }

  /**
   * Find a working endpoint for a device
   * @param {string} endpointType - Type of endpoint (shadow, tempHistory, etc.)
   * @param {string} deviceId - Device ID
   * @returns {Promise<string>} - Working endpoint or null
   */
  async findWorkingEndpoint(endpointType, deviceId) {
    console.log(`🔎 Finding working endpoint for ${endpointType} and device ${deviceId}`);

    // Check if we already have a cached working endpoint
    const cacheKey = `${endpointType}_${deviceId}`;
    if (this.cachedEndpoints[cacheKey]) {
      console.log(`✅ Using cached endpoint: ${this.cachedEndpoints[cacheKey]}`);
      return this.cachedEndpoints[cacheKey];
    }

    // Get list of endpoints to try
    const endpoints = this.endpoints[endpointType];
    if (!endpoints || !endpoints.length) {
      console.error(`No endpoints defined for type: ${endpointType}`);
      return null;
    }

    // Try each endpoint until one works
    for (const endpoint of endpoints) {
      const url = this.formatEndpoint(endpoint, { device_id: deviceId });

      try {
        // Make a GET request to check if endpoint exists
        const response = await fetch(url, { method: 'GET' });

        if (response.ok) {
          // Cache this working endpoint
          this.cachedEndpoints[cacheKey] = endpoint;
          return endpoint;
        }
      } catch (error) {
        console.warn(`Endpoint ${url} failed:`, error);
      }
    }

    // If we get here, no endpoint worked
    console.error(`No working ${endpointType} endpoint found for device ${deviceId}`);
    return null;
  }

  /**
   * Get device shadow document
   * @param {string} deviceId - Device ID
   * @returns {Promise<Object>} - Shadow document or null
   */
  async getShadow(deviceId) {
    try {
      // Find a working endpoint
      const endpoint = await this.findWorkingEndpoint('shadow', deviceId);
      if (!endpoint) {
        throw new Error(`No shadow API endpoint available for device ${deviceId}`);
      }

      // Format the URL
      const url = this.formatEndpoint(endpoint, { device_id: deviceId });

      // Make the request
      const response = await fetch(url);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`No shadow document exists for device ${deviceId}`);
        }
        throw new Error(`Failed to get shadow document: ${response.status} ${response.statusText}`);
      }

      // Parse response
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting shadow document:', error);
      throw error;
    }
  }

  /**
   * Get temperature history for a device
   * @param {string} deviceId - Device ID
   * @param {Object} options - Options for history retrieval
   * @returns {Promise<Array>} - Temperature history data
   */
  async getTemperatureHistory(deviceId, options = {}) {
    const { days = 7, limit = 100 } = options;

    console.log(`🔄 Getting temperature history for device ${deviceId} with options:`, options);

    try {
      // Find a working endpoint
      console.log(`Looking for a working temperature history endpoint...`);
      const endpoint = await this.findWorkingEndpoint('tempHistory', deviceId);
      if (!endpoint) {
        throw new Error(`No temperature history API endpoint available for device ${deviceId}`);
      }
      console.log(`Found working endpoint: ${endpoint}`);

      // Format the URL
      let url = this.formatEndpoint(endpoint, { device_id: deviceId });

      // Add query parameters
      const params = new URLSearchParams();
      if (days) params.append('days', days);
      if (limit) params.append('limit', limit);

      if (params.toString()) {
        url = `${url}?${params.toString()}`;
      }

      // Make the request
      console.log(`🔍 Fetching temperature history from URL: ${url}`);
      const response = await fetch(url);

      console.log(`📊 Response status:`, response.status, response.statusText);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`No shadow document exists for device ${deviceId}`);
        }
        throw new Error(`Failed to get temperature history: ${response.status} ${response.statusText}`);
      }

      // Parse response
      const data = await response.json();

      // Normalize data format
      return this.normalizeHistoryData(data);
    } catch (error) {
      console.error('Error getting temperature history:', error);
      throw error;
    }
  }

  /**
   * Normalize history data to a consistent format
   * @param {Array} data - Raw history data
   * @returns {Array} - Normalized data with timestamp and temperature
   */
  normalizeHistoryData(data) {
    if (!Array.isArray(data)) {
      console.warn('History data is not an array, returning empty array');
      return [];
    }

    return data.map(entry => {
      const timestamp = entry.timestamp;

      // Find temperature in different possible locations
      let temperature = null;
      if ('temperature' in entry) {
        temperature = entry.temperature;
      } else if ('value' in entry) {
        temperature = entry.value;
      } else if (entry.metrics && 'temperature' in entry.metrics) {
        temperature = entry.metrics.temperature;
      }

      return {
        timestamp,
        temperature
      };
    }).filter(entry => entry.timestamp && entry.temperature !== null);
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DeviceShadowApi;
}
