/**
 * Telemetry Service
 * 
 * Handles real-time telemetry data from IoT devices
 * Designed as part of the device-agnostic architecture to support multiple device types
 */
export class TelemetryService {
  /**
   * Create a new TelemetryService instance
   * 
   * @param {Object} config - Service configuration
   * @param {string} config.endpoint - REST API endpoint for telemetry data
   * @param {string} config.wsEndpoint - WebSocket endpoint for real-time updates
   * @param {Object} config.auth - Authentication details
   */
  constructor({ endpoint, wsEndpoint, auth }) {
    this.endpoint = endpoint || '/api/telemetry';
    this.wsEndpoint = wsEndpoint;
    this.auth = auth;
    
    // WebSocket connection
    this.ws = null;
    this.wsConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 2000; // Starting delay in milliseconds
    
    // Subscription management
    this.subscriptions = new Map(); // Map of subscription id -> callback
    this.deviceSubscriptions = new Map(); // Map of device id -> Set of subscription ids
    
    // Initialize WebSocket if endpoint is provided
    if (this.wsEndpoint) {
      this.connect();
    }
  }
  
  /**
   * Connect to the WebSocket server
   */
  connect() {
    if (this.ws) {
      // Close existing connection
      this.disconnect();
    }
    
    try {
      // Create WebSocket URL with authentication token if available
      let wsUrl = this.wsEndpoint;
      if (this.auth && this.auth.token) {
        wsUrl += `?token=${this.auth.token}`;
      }
      
      this.ws = new WebSocket(wsUrl);
      
      // Set up event handlers
      this.ws.addEventListener('open', this.handleOpen.bind(this));
      this.ws.addEventListener('message', this.handleMessage.bind(this));
      this.ws.addEventListener('close', this.handleClose.bind(this));
      this.ws.addEventListener('error', this.handleError.bind(this));
    } catch (error) {
      console.error('Error connecting to telemetry WebSocket:', error);
      this.scheduleReconnect();
    }
  }
  
  /**
   * Handle WebSocket open event
   */
  handleOpen(event) {
    console.log('Connected to telemetry WebSocket');
    this.wsConnected = true;
    this.reconnectAttempts = 0;
    
    // Resubscribe to all device telemetry
    this.resubscribeAll();
  }
  
  /**
   * Handle WebSocket message event
   */
  handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      
      // Handle different message types
      switch (data.type) {
        case 'telemetry':
          this.handleTelemetryUpdate(data);
          break;
        case 'subscription_confirmation':
          this.handleSubscriptionConfirmation(data);
          break;
        case 'error':
          console.error('WebSocket error message:', data.error);
          break;
        default:
          console.log('Unknown WebSocket message type:', data.type);
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
    }
  }
  
  /**
   * Handle telemetry update message
   */
  handleTelemetryUpdate(data) {
    const { device_id, telemetry } = data;
    
    // Get all subscriptions for this device
    const subscriptionIds = this.deviceSubscriptions.get(device_id);
    if (!subscriptionIds) return;
    
    // Call all subscription callbacks with telemetry data
    subscriptionIds.forEach(subscriptionId => {
      const callback = this.subscriptions.get(subscriptionId);
      if (callback) {
        callback(telemetry);
      }
    });
  }
  
  /**
   * Handle subscription confirmation message
   */
  handleSubscriptionConfirmation(data) {
    console.log(`Subscription ${data.subscription_id} confirmed for device ${data.device_id}`);
  }
  
  /**
   * Handle WebSocket close event
   */
  handleClose(event) {
    console.log(`Telemetry WebSocket closed: ${event.code} ${event.reason}`);
    this.wsConnected = false;
    
    // Attempt to reconnect if not closed intentionally
    if (event.code !== 1000) {
      this.scheduleReconnect();
    }
  }
  
  /**
   * Handle WebSocket error event
   */
  handleError(event) {
    console.error('Telemetry WebSocket error:', event);
    // The WebSocket will automatically close after an error
  }
  
  /**
   * Schedule a reconnection attempt
   */
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max WebSocket reconnection attempts reached');
      return;
    }
    
    const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts);
    console.log(`Scheduling WebSocket reconnect in ${delay}ms`);
    
    setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }
  
  /**
   * Resubscribe to all device telemetry after reconnection
   */
  resubscribeAll() {
    this.deviceSubscriptions.forEach((subscriptionIds, deviceId) => {
      this.sendSubscriptionMessage(deviceId);
    });
  }
  
  /**
   * Send a subscription message via WebSocket
   */
  sendSubscriptionMessage(deviceId) {
    if (!this.wsConnected || !this.ws) {
      return;
    }
    
    try {
      this.ws.send(JSON.stringify({
        action: 'subscribe',
        device_id: deviceId
      }));
    } catch (error) {
      console.error(`Error subscribing to device ${deviceId}:`, error);
    }
  }
  
  /**
   * Disconnect from the WebSocket server
   */
  disconnect() {
    if (this.ws) {
      // Close with 1000 (Normal Closure) code to indicate intentional closing
      this.ws.close(1000, 'Intentional disconnect');
      this.ws = null;
      this.wsConnected = false;
    }
  }
  
  /**
   * Subscribe to telemetry updates for a specific device
   * 
   * @param {string} deviceId - ID of the device to subscribe to
   * @param {Function} callback - Function to call with telemetry updates
   * @returns {string} - Subscription ID
   */
  subscribeToDeviceTelemetry(deviceId, callback) {
    // Generate unique subscription ID
    const subscriptionId = `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Store the callback
    this.subscriptions.set(subscriptionId, callback);
    
    // Add to device subscriptions map
    if (!this.deviceSubscriptions.has(deviceId)) {
      this.deviceSubscriptions.set(deviceId, new Set());
      
      // Send subscription message if this is the first subscription for this device
      this.sendSubscriptionMessage(deviceId);
    }
    
    this.deviceSubscriptions.get(deviceId).add(subscriptionId);
    
    return subscriptionId;
  }
  
  /**
   * Unsubscribe from telemetry updates
   * 
   * @param {string} subscriptionId - ID of the subscription to cancel
   */
  unsubscribe(subscriptionId) {
    const callback = this.subscriptions.get(subscriptionId);
    if (!callback) return;
    
    // Remove subscription
    this.subscriptions.delete(subscriptionId);
    
    // Remove from device subscriptions
    this.deviceSubscriptions.forEach((subscriptions, deviceId) => {
      if (subscriptions.has(subscriptionId)) {
        subscriptions.delete(subscriptionId);
        
        // If no more subscriptions for this device, unsubscribe from WebSocket
        if (subscriptions.size === 0) {
          this.deviceSubscriptions.delete(deviceId);
          this.sendUnsubscriptionMessage(deviceId);
        }
      }
    });
  }
  
  /**
   * Send an unsubscription message via WebSocket
   */
  sendUnsubscriptionMessage(deviceId) {
    if (!this.wsConnected || !this.ws) {
      return;
    }
    
    try {
      this.ws.send(JSON.stringify({
        action: 'unsubscribe',
        device_id: deviceId
      }));
    } catch (error) {
      console.error(`Error unsubscribing from device ${deviceId}:`, error);
    }
  }
  
  /**
   * Get historical telemetry data for a device
   * 
   * @param {string} deviceId - ID of the device
   * @param {Object} options - Query options
   * @param {string} options.startTime - Start time of data range (ISO string)
   * @param {string} options.endTime - End time of data range (ISO string)
   * @param {number} options.limit - Maximum number of data points to return
   * @returns {Promise<Array>} - Historical telemetry data
   */
  async getHistoricalTelemetry(deviceId, options = {}) {
    try {
      // Build query params
      const queryParams = new URLSearchParams();
      
      if (options.startTime) queryParams.append('start_time', options.startTime);
      if (options.endTime) queryParams.append('end_time', options.endTime);
      if (options.limit) queryParams.append('limit', options.limit.toString());
      
      const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
      const url = `${this.endpoint}/${deviceId}/history${queryString}`;
      
      const response = await fetch(url, {
        headers: this.getAuthHeaders()
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch historical telemetry: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Error fetching historical telemetry for device ${deviceId}:`, error);
      throw error;
    }
  }
  
  /**
   * Get the latest telemetry data for a device
   * 
   * @param {string} deviceId - ID of the device
   * @returns {Promise<Object>} - Latest telemetry data
   */
  async getLatestTelemetry(deviceId) {
    try {
      const url = `${this.endpoint}/${deviceId}/latest`;
      
      const response = await fetch(url, {
        headers: this.getAuthHeaders()
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch latest telemetry: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Error fetching latest telemetry for device ${deviceId}:`, error);
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
}
