/**
 * Real-Time Monitoring Service
 * Handles WebSocket connections for device updates
 * Follows TDD principles with implementation driven by test requirements
 */

class RealTimeMonitor {
  constructor(config = {}) {
    this.baseUrl = config.baseUrl || 'ws://localhost:8000';
    this.endpoint = config.endpoint || '/api/ws/device-updates';
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = config.maxReconnectAttempts || 5;
    this.reconnectDelay = config.reconnectDelay || 3000;
    this.deviceId = null;
    this.ws = null;
    this.connectionStatus = 'disconnected';
    this.listeners = {
      'temperature': [],
      'status': [],
      'connectionChange': [],
      'error': []
    };
  }

  /**
   * Connect to WebSocket for specified device
   * @param {string} deviceId - The device ID to monitor
   */
  connect(deviceId) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.close();
    }

    this.deviceId = deviceId;
    const wsUrl = `${this.baseUrl}${this.endpoint}?deviceId=${deviceId}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = this._handleOpen.bind(this);
      this.ws.onmessage = this._handleMessage.bind(this);
      this.ws.onclose = this._handleClose.bind(this);
      this.ws.onerror = this._handleError.bind(this);

      // Set up a timeout to notify if connection takes too long
      this.connectionTimeout = setTimeout(() => {
        if (this.connectionStatus !== 'connected') {
          this._updateConnectionStatus('timeout');
        }
      }, 10000);

      return true;
    } catch (error) {
      this._notifyError('Failed to establish WebSocket connection', error);
      return false;
    }
  }

  /**
   * Disconnect WebSocket connection
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this._updateConnectionStatus('disconnected');
    this.deviceId = null;
    this.reconnectAttempts = 0;

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
      this.connectionTimeout = null;
    }
  }

  /**
   * Handle WebSocket open event
   */
  _handleOpen() {
    this._updateConnectionStatus('connected');
    this.reconnectAttempts = 0;

    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
      this.connectionTimeout = null;
    }

    // Send subscription message to server
    if (this.deviceId) {
      this.ws.send(JSON.stringify({
        action: 'subscribe',
        deviceId: this.deviceId
      }));
    }

    console.log(`WebSocket connected for device ${this.deviceId}`);
  }

  /**
   * Handle WebSocket message event
   * @param {MessageEvent} event - WebSocket message event
   */
  _handleMessage(event) {
    try {
      const data = JSON.parse(event.data);

      // Handle different message types
      switch(data.messageType) {
        case 'update':
          this._processUpdate(data);
          break;
        case 'status':
          this._processStatusChange(data);
          break;
        case 'error':
          this._notifyError(data.message, data.details);
          break;
        default:
          console.log('Received unknown message type', data);
      }
    } catch (error) {
      this._notifyError('Failed to process message', error);
    }
  }

  /**
   * Handle WebSocket close event
   * @param {CloseEvent} event - WebSocket close event
   */
  _handleClose(event) {
    // Clear connection timeout if it exists
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
      this.connectionTimeout = null;
    }

    this._updateConnectionStatus('disconnected');

    // Attempt reconnection if not intentionally closed
    if (event.code !== 1000 && this.deviceId) {
      this._attemptReconnect();
    }

    console.log(`WebSocket disconnected: ${event.code} - ${event.reason}`);
  }

  /**
   * Handle WebSocket error event
   * @param {Event} error - WebSocket error event
   */
  _handleError(error) {
    this._notifyError('WebSocket connection error', error);

    // Update connection status
    this._updateConnectionStatus('error');
  }

  /**
   * Attempt to reconnect the WebSocket
   */
  _attemptReconnect() {
    this._updateConnectionStatus('reconnecting');

    // Check if we've exceeded max reconnect attempts
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this._notifyError('Maximum reconnection attempts reached', {
        attempts: this.reconnectAttempts
      });
      this._updateConnectionStatus('failed');
      return;
    }

    // Increment reconnect attempts
    this.reconnectAttempts++;

    // Schedule reconnect attempt
    const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1);
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);

    this.reconnectTimer = setTimeout(() => {
      if (this.deviceId) {
        this.connect(this.deviceId);
      }
    }, delay);

    // Notify listeners of reconnection attempt
    this._notifyListeners('connectionChange', {
      status: 'reconnecting',
      attempt: this.reconnectAttempts,
      maxAttempts: this.maxReconnectAttempts
    });
  }

  /**
   * Process device update message
   * @param {Object} data - Update message data
   */
  _processUpdate(data) {
    const update = data.update;

    // Process temperature updates
    if (update.state && update.state.reported &&
        update.state.reported.temperature !== undefined) {
      const temperature = update.state.reported.temperature;
      const unit = update.state.reported.temperature_unit || 'F';

      this._notifyListeners('temperature', {
        value: temperature,
        unit: unit,
        formatted: `${temperature}°${unit}`,
        timestamp: data.timestamp || new Date().toISOString()
      });
    }

    // Process other updates here as needed
  }

  /**
   * Process device status change
   * @param {Object} data - Status message data
   */
  _processStatusChange(data) {
    if (data.status) {
      this._notifyListeners('status', {
        status: data.status,
        timestamp: data.timestamp || new Date().toISOString()
      });
    }
  }

  /**
   * Update connection status and notify listeners
   * @param {string} status - New connection status
   */
  _updateConnectionStatus(status) {
    const oldStatus = this.connectionStatus;
    this.connectionStatus = status;

    // Notify listeners of connection status change
    if (oldStatus !== status) {
      this._notifyListeners('connectionChange', {
        status: status,
        previousStatus: oldStatus,
        timestamp: new Date().toISOString()
      });
    }
  }

  /**
   * Notify error listeners
   * @param {string} message - Error message
   * @param {Object} details - Error details
   */
  _notifyError(message, details = {}) {
    this._notifyListeners('error', {
      message: message,
      details: details,
      timestamp: new Date().toISOString()
    });

    console.error(`RealTimeMonitor Error: ${message}`, details);
  }

  /**
   * Notify listeners of a specific event type
   * @param {string} type - Event type
   * @param {Object} data - Event data
   */
  _notifyListeners(type, data) {
    if (this.listeners[type]) {
      this.listeners[type].forEach(listener => {
        try {
          listener(data);
        } catch (error) {
          console.error(`Error in ${type} listener:`, error);
        }
      });
    }
  }

  /**
   * Add event listener
   * @param {string} event - Event type
   * @param {Function} callback - Event callback
   * @returns {boolean} - Whether listener was added successfully
   */
  addEventListener(event, callback) {
    if (this.listeners[event] && typeof callback === 'function') {
      this.listeners[event].push(callback);
      return true;
    }
    return false;
  }

  /**
   * Remove event listener
   * @param {string} event - Event type
   * @param {Function} callback - Event callback
   * @returns {boolean} - Whether listener was removed successfully
   */
  removeEventListener(event, callback) {
    if (this.listeners[event]) {
      const index = this.listeners[event].indexOf(callback);
      if (index !== -1) {
        this.listeners[event].splice(index, 1);
        return true;
      }
    }
    return false;
  }

  /**
   * Get current connection status
   * @returns {string} - Current connection status
   */
  getConnectionStatus() {
    return this.connectionStatus;
  }
}

// Export for browser use
window.RealTimeMonitor = RealTimeMonitor;
