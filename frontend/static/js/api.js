/**
 * API Client for IoTSphere
 */
class ApiClient {
  constructor(baseUrl = null) {
    // Use the current hostname and port for API requests
    // This ensures it works from any network location
    const apiHost = window.location.hostname;
    const apiPort = window.location.port || '8006';

    // Construct base URL using current location information
    this.baseUrl = baseUrl || `${window.location.protocol}//${apiHost}${apiPort ? ':' + apiPort : ''}/api`;

    console.log('API client initialized with base URL:', this.baseUrl);
  }

  /**
   * Make an API request with timeout
   * @param {string} method - HTTP method
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request body for POST/PUT/PATCH
   * @param {number} timeout - Request timeout in milliseconds (default: 10000ms)
   * @returns {Promise<any>} - Response data
   */
  async request(method, endpoint, data = null, timeout = 20000) {
    // Add timestamp to prevent caching
    if (endpoint.includes('?')) {
      endpoint += `&_t=${Date.now()}`;
    } else {
      endpoint += `?_t=${Date.now()}`;
    }

    // Handle endpoint formatting - remove trailing slash if query params exist
    if (endpoint.includes('?')) {
      endpoint = endpoint.replace(/\/$/, '');
    }
    // Otherwise ensure trailing slash for FastAPI compatibility
    else if (!endpoint.endsWith('/')) {
      endpoint = `${endpoint}/`;
    }

    // Handle all machine ID formats safely
    if (endpoint.includes('/vending-machines/') || endpoint.includes('/ice-cream-machines/')) {
      console.log('Machine endpoint detected, ensuring ID compatibility');
    }

    const url = `${this.baseUrl}${endpoint}`;
    console.log(`Making ${method} request to: ${url}`);

    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': window.location.origin
      },
      mode: 'cors',
      credentials: 'omit', // Must be omit with wildcard CORS on server
      cache: 'no-cache'
    };

    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      options.body = JSON.stringify(data);
    }

    // Create a timeout promise to avoid hanging requests
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error(`Request timeout after ${timeout}ms for ${url}`));
      }, timeout);
    });

    try {
      // Race the fetch against the timeout
      const response = await Promise.race([
        fetch(url, options),
        timeoutPromise
      ]);

      console.log(`Response status: ${response.status} ${response.statusText}`);

      // Check for CORS errors
      if (response.type === 'opaque' || response.status === 0) {
        console.error('Possible CORS error - received opaque response');

        // Try again with a different mode as fallback
        console.log('Retrying with no-cors mode as fallback');
        const fallbackOptions = {...options, mode: 'no-cors'};
        try {
          // This will give us an opaque response we can't read but at least confirms connectivity
          await fetch(url, fallbackOptions);
          throw new Error('CORS issue detected - API is reachable but cross-origin restrictions prevent access');
        } catch (fallbackError) {
          throw new Error('Unable to access API due to cross-origin restrictions. Please check CORS configuration.');
        }
      }

      // Handle non-JSON responses
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const responseData = await response.json();

        if (!response.ok) {
          // Handle API errors with more detail
          console.error('API error response:', responseData);
          throw new Error(responseData.detail || `API request failed: ${response.status} ${response.statusText}`);
        }

        return responseData;
      } else {
        if (!response.ok) {
          throw new Error(`API request failed: ${response.status} ${response.statusText}`);
        }
        return await response.text();
      }
    } catch (error) {
      console.error(`API request error for ${url}:`, error);

      // Add more helpful debugging for common errors
      if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
        console.error('Network error detected. This could be due to CORS issues, network connectivity, or the server being down');
        console.log('Trying to reach server at:', this.baseUrl);
      }

      // Rethrow with enhanced error message
      throw new Error(`Request failed: ${error.message}. Please check console for details.`);
    }
  }

  // Water Heater API methods

  /**
   * Get all water heaters
   * @returns {Promise<Array>} - List of water heaters
   */
  async getWaterHeaters(manufacturer = null) {
    // Use the manufacturer-agnostic API endpoint
    let endpoint = '/manufacturer/water-heaters';
    if (manufacturer) {
      endpoint += `?manufacturer=${encodeURIComponent(manufacturer)}`;
    }
    console.log(`Fetching water heaters from endpoint: ${endpoint}`);
    return this.request('GET', endpoint);
  }

  /**
   * Get a specific water heater
   * @param {string} id - Water heater ID
   * @returns {Promise<Object>} - Water heater data
   */
  async getWaterHeater(id) {
    // Use the manufacturer-agnostic API endpoint
    console.log(`Fetching water heater details for ID: ${id}`);
    return this.request('GET', `/manufacturer/water-heaters/${id}`);
  }

  /**
   * Create a new water heater
   * @param {Object} data - Water heater data
   * @returns {Promise<Object>} - Created water heater
   */
  async createWaterHeater(data) {
    return this.request('POST', '/water-heaters', data);
  }

  /**
   * Update a water heater's target temperature
   * @param {string} id - Water heater ID
   * @param {number} temperature - New target temperature
   * @returns {Promise<Object>} - Updated water heater
   */
  async updateTemperature(id, temperature) {
    return this.request('PATCH', `/water-heaters/${id}/temperature`, { temperature });
  }

  /**
   * Update a water heater's operational mode
   * @param {string} id - Water heater ID
   * @param {string} mode - New mode (ECO, BOOST, OFF)
   * @returns {Promise<Object>} - Updated water heater
   */
  async updateMode(id, mode) {
    return this.request('PATCH', `/water-heaters/${id}/mode`, { mode });
  }

  /**
   * Add a temperature reading to a water heater
   * @param {string} id - Water heater ID
   * @param {Object} reading - Reading data
   * @returns {Promise<Object>} - Updated water heater
   */
  async addReading(id, reading) {
    return this.request('POST', `/water-heaters/${id}/readings`, reading);
  }

  // Vending Machine API methods

  /**
   * Get all vending machines
   * @returns {Promise<Array>} - List of vending machines
   */
  async getVendingMachines() {
    return this.request('GET', '/vending-machines');
  }

  /**
   * Get a specific vending machine
   * @param {string} id - Vending machine ID
   * @returns {Promise<Object>} - Vending machine data
   */
  async getVendingMachine(id) {
    return this.request('GET', `/vending-machines/${id}`);
  }

  /**
   * Create a new vending machine
   * @param {Object} data - Vending machine data
   * @returns {Promise<Object>} - Created vending machine
   */
  async createVendingMachine(data) {
    return this.request('POST', '/vending-machines', data);
  }

  /**
   * Update a vending machine
   * @param {string} id - Vending machine ID
   * @param {Object} data - Updated vending machine data
   * @returns {Promise<Object>} - Updated vending machine
   */
  async updateVendingMachine(id, data) {
    return this.request('PUT', `/vending-machines/${id}`, data);
  }

  /**
   * Get operations analytics data for a vending machine
   * @param {string} id - Vending machine ID
   * @returns {Promise<Object>} - Operations analytics data
   */
  async getVendingMachineOperationsAnalytics(id) {
    return this.request('GET', `/ice-cream-machines/${id}/operations`);
  }

  /**
   * Get real-time operations data for a vending machine
   * @param {string} id - Vending machine ID
   * @returns {Promise<Object>} - Real-time operations data
   */
  async getVendingMachineRealtimeOperations(id) {
    console.log(`Fetching operations data from: ${this.baseUrl}/ice-cream-machines/${id}/operations`);
    // Using the main operations endpoint since we don't have a specific /realtime endpoint
    return this.request('GET', `/ice-cream-machines/${id}/operations`);
  }

  /**
   * Get real-time operations data for an ice cream machine
   * @param {string} id - Ice cream machine ID
   * @returns {Promise<Object>} - Real-time operations data
   */
  async getIceCreamMachineOperations(id) {
    console.log(`Fetching ice cream machine operations data from: ${this.baseUrl}/ice-cream-machines/${id}/operations`);
    return this.request('GET', `/ice-cream-machines/${id}/operations`);
  }
}

// Export the API client
const api = new ApiClient();
