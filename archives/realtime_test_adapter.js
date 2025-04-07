/**
 * Real-Time Monitoring Test Adapter
 * 
 * This adapter helps bridge the gap between the BDD tests and the actual implementation
 * Following TDD principles - tests should drive implementation, not vice versa
 */
const { RealTimeMonitor } = require('../../src/services/realtime_monitor');

class RealTimeTestAdapter {
  constructor(page) {
    this.page = page;
    this.deviceId = null;
  }
  
  /**
   * Initialize the test environment for real-time monitoring
   * @param {string} deviceId - The device ID to monitor
   */
  async initialize(deviceId) {
    this.deviceId = deviceId;
    
    // Initialize the test environment in the page context
    await this.page.evaluate((deviceId) => {
      // Create global test context if it doesn't exist
      window.testContext = window.testContext || {};
      
      // Store device ID
      window.testContext.currentDeviceId = deviceId;
      
      // Setup shadow document handler for WebSocket simulation
      window.shadowDocumentHandler = {
        ws: null,
        connectionStatus: 'disconnected',
        onMessage: null,
        
        // Method to simulate connection
        connect: function() {
          if (this.ws) {
            // Close existing connection
            this.close();
          }
          
          // Create mock WebSocket
          this.ws = {
            readyState: 1, // OPEN
            close: () => {
              this.ws.readyState = 3; // CLOSED
              if (typeof this.ws.onclose === 'function') {
                this.ws.onclose({ code: 1000, reason: 'Normal closure' });
              }
            },
            send: (data) => {
              console.log('WebSocket message sent:', data);
            },
            onopen: null,
            onmessage: null,
            onclose: null,
            onerror: null
          };
          
          // Set connection status
          this.connectionStatus = 'connected';
          
          // Trigger onopen callback
          if (typeof this.ws.onopen === 'function') {
            this.ws.onopen();
          }
          
          // Update UI
          this._updateUI('connected');
          
          return true;
        },
        
        // Method to simulate disconnection
        disconnect: function() {
          if (this.ws) {
            this.ws.close();
            this.ws = null;
          }
          
          // Set connection status
          this.connectionStatus = 'disconnected';
          
          // Update UI
          this._updateUI('disconnected');
          
          return true;
        },
        
        // Method to simulate incoming message
        simulateMessage: function(messageData) {
          if (!this.ws) {
            console.error('Cannot simulate message: WebSocket not connected');
            return false;
          }
          
          // Create message event
          const event = {
            data: typeof messageData === 'string' ? messageData : JSON.stringify(messageData)
          };
          
          // Trigger onmessage callback
          if (typeof this.ws.onmessage === 'function') {
            this.ws.onmessage(event);
          }
          
          // If this is a temperature update, update UI directly
          if (messageData.messageType === 'update' && 
              messageData.update && 
              messageData.update.state && 
              messageData.update.state.reported && 
              messageData.update.state.reported.temperature !== undefined) {
            const temp = messageData.update.state.reported.temperature;
            this._updateTemperatureDisplay(temp);
          }
          
          return true;
        },
        
        // Update UI elements for testing
        _updateUI: function(status) {
          // Update connection status
          const statusIndicator = document.querySelector('.connection-status, .status-indicator');
          if (statusIndicator) {
            statusIndicator.textContent = status;
            statusIndicator.className = `connection-status ${status}`;
          }
          
          // Show/hide reconnection message
          const reconnectionMsg = document.querySelector('.reconnect-message');
          if (reconnectionMsg) {
            reconnectionMsg.style.display = status === 'reconnecting' ? 'block' : 'none';
            if (status === 'reconnecting') {
              reconnectionMsg.textContent = 'Attempting to reconnect...';
            }
          }
          
          // Dispatch custom event for tests
          document.dispatchEvent(new CustomEvent('connection-status-changed', {
            detail: { status }
          }));
        },
        
        // Update temperature display for testing
        _updateTemperatureDisplay: function(temperature, unit = 'F') {
          const tempDisplay = document.querySelector('.temperature-display, .temperature-value');
          if (tempDisplay) {
            tempDisplay.textContent = `${temperature}°${unit}`;
          }
          
          // Add data point to history chart
          const historyChart = document.querySelector('.temperature-history-chart');
          if (historyChart) {
            // Create data point for tests
            const dataPoint = document.createElement('div');
            dataPoint.className = 'data-point';
            dataPoint.dataset.value = temperature;
            dataPoint.dataset.timestamp = new Date().toISOString();
            dataPoint.style.display = 'none';
            historyChart.appendChild(dataPoint);
            
            // Set last updated attribute
            historyChart.setAttribute('data-last-updated', new Date().toISOString());
            historyChart.classList.add('updated');
          }
          
          // Dispatch custom event for tests
          document.dispatchEvent(new CustomEvent('temperature-updated', {
            detail: { temperature, unit }
          }));
        }
      };
      
      console.log(`Test environment initialized for device: ${deviceId}`);
    }, deviceId);
    
    return true;
  }
  
  /**
   * Simulate a device sending a temperature reading
   * @param {string} temperature - Temperature reading with unit (e.g. "140°F")
   */
  async simulateTemperatureReading(temperature) {
    // Parse temperature value and unit
    const match = temperature.match(/(\d+)([°℃℉]*)([CF])?/);
    if (!match) {
      throw new Error(`Invalid temperature format: ${temperature}`);
    }
    
    const tempValue = parseInt(match[1]);
    const unit = match[3] || 'F';
    
    // Simulate WebSocket message with temperature update
    await this.page.evaluate((tempValue, unit) => {
      if (window.shadowDocumentHandler) {
        // Create update message
        const message = {
          messageType: 'update',
          timestamp: new Date().toISOString(),
          deviceId: window.testContext.currentDeviceId,
          update: {
            state: {
              reported: {
                temperature: tempValue,
                temperature_unit: unit
              }
            }
          }
        };
        
        // Simulate message
        window.shadowDocumentHandler.simulateMessage(message);
      }
    }, tempValue, unit);
    
    // Wait for UI to update
    await this.page.waitForTimeout(500);
    
    return true;
  }
  
  /**
   * Simulate multiple temperature readings for chart updates
   */
  async simulateMultipleReadings() {
    // Simulate a series of temperature updates
    const temperatures = [138, 139, 140, 141, 142];
    
    for (const temp of temperatures) {
      await this.simulateTemperatureReading(`${temp}°F`);
      await this.page.waitForTimeout(200);
    }
    
    return true;
  }
  
  /**
   * Simulate WebSocket connection interruption
   */
  async simulateConnectionInterrupt() {
    await this.page.evaluate(() => {
      if (window.shadowDocumentHandler) {
        // Simulate onclose event
        if (window.shadowDocumentHandler.ws && typeof window.shadowDocumentHandler.ws.onclose === 'function') {
          window.shadowDocumentHandler.ws.onclose({ code: 1006, reason: 'Connection interrupted' });
        }
        
        // Update UI to disconnected state
        window.shadowDocumentHandler._updateUI('disconnected');
        
        // Create reconnection message
        const reconnectionMsg = document.querySelector('.reconnect-message');
        if (!reconnectionMsg) {
          const msgElement = document.createElement('div');
          msgElement.className = 'reconnect-message';
          msgElement.textContent = 'Attempting to reconnect...';
          msgElement.style.display = 'block';
          
          const container = document.querySelector('.real-time-monitor') || document.body;
          container.appendChild(msgElement);
        } else {
          reconnectionMsg.style.display = 'block';
        }
      }
    });
    
    // Wait for UI to update
    await this.page.waitForTimeout(500);
    
    return true;
  }
  
  /**
   * Simulate WebSocket connection restoration
   */
  async simulateConnectionRestore() {
    await this.page.evaluate(() => {
      if (window.shadowDocumentHandler) {
        // Simulate connection restore
        window.shadowDocumentHandler.connect();
      }
    });
    
    // Wait for UI to update
    await this.page.waitForTimeout(500);
    
    return true;
  }
}

module.exports = RealTimeTestAdapter;
