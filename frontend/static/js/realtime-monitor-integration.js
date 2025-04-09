/**
 * Real-Time Monitor Integration
 * Integrates the RealTimeMonitor class with the UI components
 * Follows TDD principles with implementation driven by test requirements
 */

(function() {
  // Store device-specific monitoring instances
  const monitorInstances = {};
  const DEFAULT_CONFIG = {
    baseUrl: document.location.protocol === 'https:' ?
      `wss://${document.location.host}` :
      `ws://${document.location.host}`,
    endpoint: '/api/ws/device-updates',
    maxReconnectAttempts: 5,
    reconnectDelay: 3000
  };

  // Elements that should be updated with real-time data
  const UI_ELEMENTS = {
    temperatureDisplay: '.temperature-display',
    connectionStatus: '.status-indicator.connection span, .connection-status',
    reconnectionMessage: '.reconnection-message',
    temperatureHistoryChart: '.temperature-history-chart'
  };

  /**
   * Initialize real-time monitoring for a device
   * @param {string} deviceId - The device ID to monitor
   * @param {Object} config - Configuration options
   * @returns {RealTimeMonitor} The monitor instance
   */
  function initializeMonitoring(deviceId, config = {}) {
    // Don't create duplicate monitors
    if (monitorInstances[deviceId]) {
      return monitorInstances[deviceId];
    }

    // Create a monitor instance
    const monitorConfig = {...DEFAULT_CONFIG, ...config};
    const monitor = new RealTimeMonitor(monitorConfig);
    monitorInstances[deviceId] = monitor;

    // Set up event listeners
    setupEventListeners(monitor, deviceId);

    // Connect to the device
    monitor.connect(deviceId);
    console.log(`Real-time monitoring initialized for device ${deviceId}`);

    return monitor;
  }

  /**
   * Set up event listeners for the monitor
   * @param {RealTimeMonitor} monitor - Monitor instance
   * @param {string} deviceId - The device ID being monitored
   */
  function setupEventListeners(monitor, deviceId) {
    // Temperature updates
    monitor.addEventListener('temperature', handleTemperatureUpdate);

    // Status updates
    monitor.addEventListener('status', handleStatusUpdate);

    // Connection changes
    monitor.addEventListener('connectionChange', handleConnectionChange);

    // Error handling
    monitor.addEventListener('error', handleError);

    // Register the device ID with diagnostics
    if (window.websocketDiagnostics) {
      window.websocketDiagnostics.registerDevice(deviceId);
    }
  }

  /**
   * Handle temperature updates from the device
   * @param {Object} data - Temperature data
   */
  function handleTemperatureUpdate(data) {
    // Update temperature display
    const temperatureElements = document.querySelectorAll(UI_ELEMENTS.temperatureDisplay);
    temperatureElements.forEach(element => {
      element.textContent = data.formatted;
      element.classList.add('active');

      // Remove active class after animation
      setTimeout(() => {
        element.classList.remove('active');
      }, 1000);
    });

    // Update temperature history chart
    updateTemperatureChart(data);

    // Dispatch a custom event for test purposes
    const updateEvent = new CustomEvent('temperature-updated', {
      detail: {
        value: data.value,
        unit: data.unit,
        formatted: data.formatted,
        timestamp: data.timestamp
      }
    });
    document.dispatchEvent(updateEvent);

    console.log(`Temperature updated: ${data.formatted}`);
  }

  /**
   * Handle status updates from the device
   * @param {Object} data - Status data
   */
  function handleStatusUpdate(data) {
    console.log(`Device status update: ${data.status}`);

    // Dispatch a custom event for test purposes
    const updateEvent = new CustomEvent('status-updated', {
      detail: data
    });
    document.dispatchEvent(updateEvent);
  }

  /**
   * Handle connection status changes
   * @param {Object} data - Connection data
   */
  function handleConnectionChange(data) {
    console.log(`WebSocket connection status: ${data.status}`);

    // Update status indicator
    updateConnectionStatus(data.status);

    // Handle reconnection messages
    if (data.status === 'reconnecting') {
      showReconnectionMessage(data.attempt, data.maxAttempts);
    } else if (data.status === 'connected') {
      hideReconnectionMessage();
    }

    // Dispatch a custom event for test purposes
    const updateEvent = new CustomEvent('websocket-status-change', {
      detail: data
    });
    document.dispatchEvent(updateEvent);
  }

  /**
   * Handle monitor errors
   * @param {Object} data - Error data
   */
  function handleError(data) {
    console.error(`WebSocket error: ${data.message}`, data.details);

    // Dispatch a custom event for test purposes
    const errorEvent = new CustomEvent('websocket-error', {
      detail: data
    });
    document.dispatchEvent(errorEvent);
  }

  /**
   * Update connection status indicators
   * @param {string} status - Connection status
   */
  function updateConnectionStatus(status) {
    const statusElements = document.querySelectorAll(UI_ELEMENTS.connectionStatus);

    // If using WebSocketStatusManager, update through it
    if (window.webSocketStatusManager) {
      statusElements.forEach(element => {
        window.webSocketStatusManager.updateStatus(
          element.id || 'connection-status',
          status === 'connected' ? 'connected' : 'disconnected'
        );
      });
      return;
    }

    // Direct DOM updates if no manager is available
    statusElements.forEach(element => {
      // Update text content
      element.textContent = status === 'connected' ? 'connected' : 'disconnected';

      // Update classes on parent or element itself
      const target = element.classList.contains('status-indicator') ?
        element : element.parentElement;

      if (target) {
        target.classList.remove('connected', 'disconnected', 'error', 'reconnecting');
        target.classList.add(status === 'connected' ? 'connected' : 'disconnected');
      }
    });
  }

  /**
   * Show reconnection message with attempt information
   * @param {number} attempt - Current attempt number
   * @param {number} maxAttempts - Maximum attempts
   */
  function showReconnectionMessage(attempt, maxAttempts) {
    let messageElement = document.querySelector(UI_ELEMENTS.reconnectionMessage);

    // Create message element if it doesn't exist
    if (!messageElement) {
      messageElement = document.createElement('div');
      messageElement.className = 'reconnection-message';

      const deviceDetail = document.querySelector('.device-detail');
      if (deviceDetail) {
        deviceDetail.appendChild(messageElement);
      } else {
        document.body.appendChild(messageElement);
      }
    }

    messageElement.innerHTML = `<p>Connection lost. Attempting to reconnect... (${attempt}/${maxAttempts})</p>`;
    messageElement.style.display = 'block';
  }

  /**
   * Hide reconnection message
   */
  function hideReconnectionMessage() {
    const messageElement = document.querySelector(UI_ELEMENTS.reconnectionMessage);
    if (messageElement) {
      messageElement.style.display = 'none';
    }
  }

  /**
   * Update temperature history chart with new data
   * @param {Object} data - Temperature data
   */
  function updateTemperatureChart(data) {
    // If using the global temperature chart
    if (window.temperatureChart) {
      window.temperatureChart.addDataPoint({
        timestamp: new Date(data.timestamp),
        value: parseFloat(data.value)
      });
      return;
    }

    // Find chart elements and update if custom implementation
    const chartElement = document.querySelector(UI_ELEMENTS.temperatureHistoryChart);
    if (chartElement && chartElement._chart) {
      // Update chart data
      const chart = chartElement._chart;
      const datasets = chart.data.datasets;

      if (datasets && datasets.length > 0) {
        // Add new data point
        const timestamp = new Date(data.timestamp);

        // Format the timestamp for x-axis
        let label;
        if (timestamp.getSeconds() % 10 === 0) {
          label = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } else {
          label = '';
        }

        chart.data.labels.push(label);
        datasets[0].data.push(data.value);

        // Keep a fixed number of points
        const maxPoints = 30;
        if (chart.data.labels.length > maxPoints) {
          chart.data.labels.shift();
          datasets[0].data.shift();
        }

        chart.update();
      }
    }
  }

  /**
   * Simulate a WebSocket disconnection (for testing)
   * @param {string} deviceId - Device ID
   */
  function simulateDisconnection(deviceId) {
    const monitor = monitorInstances[deviceId];
    if (monitor) {
      // Update UI to show disconnected status
      updateConnectionStatus('disconnected');

      // Dispatch disconnect event
      const disconnectEvent = new CustomEvent('websocket-disconnect', {
        detail: { reason: 'simulated' }
      });
      document.dispatchEvent(disconnectEvent);

      console.log('Simulated WebSocket disconnection');
    }
  }

  /**
   * Simulate a WebSocket reconnection (for testing)
   * @param {string} deviceId - Device ID
   */
  function simulateReconnection(deviceId) {
    const monitor = monitorInstances[deviceId];
    if (monitor) {
      // Update UI to show connected status
      updateConnectionStatus('connected');
      hideReconnectionMessage();

      // Dispatch reconnect event
      const reconnectEvent = new CustomEvent('websocket-reconnect', {
        detail: { reason: 'simulated' }
      });
      document.dispatchEvent(reconnectEvent);

      console.log('Simulated WebSocket reconnection');
    }
  }

  /**
   * Simulate a temperature update (for testing)
   * @param {string} deviceId - Device ID
   * @param {number} temperature - Temperature value
   * @param {string} unit - Temperature unit
   */
  function simulateTemperatureUpdate(deviceId, temperature, unit = 'F') {
    const formatted = `${temperature}°${unit}`;

    handleTemperatureUpdate({
      value: temperature,
      unit: unit,
      formatted: formatted,
      timestamp: new Date().toISOString()
    });

    console.log(`Simulated temperature update: ${formatted}`);
  }

  /**
   * Clean up monitoring for a device
   * @param {string} deviceId - Device ID
   */
  function cleanupMonitoring(deviceId) {
    const monitor = monitorInstances[deviceId];
    if (monitor) {
      monitor.disconnect();
      delete monitorInstances[deviceId];
      console.log(`Cleaned up monitoring for device ${deviceId}`);
    }
  }

  /**
   * Initialize monitoring on page load for devices in the detail view
   */
  function initializeOnLoad() {
    document.addEventListener('DOMContentLoaded', () => {
      // Check if we're on a device detail page
      const deviceIdElement = document.getElementById('device-id');
      if (deviceIdElement) {
        const deviceId = deviceIdElement.value || deviceIdElement.dataset.deviceId;
        if (deviceId) {
          initializeMonitoring(deviceId);
        }
      }
    });
  }

  // Initialize on load
  initializeOnLoad();

  // Expose functions to global scope
  window.realTimeMonitor = {
    initialize: initializeMonitoring,
    simulateDisconnection,
    simulateReconnection,
    simulateTemperatureUpdate,
    cleanup: cleanupMonitoring
  };
})();
