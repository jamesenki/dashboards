/**
 * WebSocket Status Manager
 * A centralized utility to manage WebSocket connection status indicators
 * Ensures consistent status representation across the application
 */
class WebSocketStatusManager {
  /**
   * Initialize the WebSocket Status Manager
   */
  constructor() {
    // Keep track of all registered status elements
    this.statusElements = {};

    // Status types and their display values
    this.statusConfig = {
      'connected': {
        className: 'status-indicator connected',
        text: 'Connected'
      },
      'disconnected': {
        className: 'status-indicator disconnected',
        text: 'Disconnected'
      },
      'connecting': {
        className: 'status-indicator connecting',
        text: 'Connecting...'
      },
      'error': {
        className: 'status-indicator error',
        text: 'Error'
      }
    };

    // Initialize without logging
  }

  /**
   * Register a status element to be managed
   * @param {string} elementId - The ID of the status element
   * @param {string} initialStatus - Initial status (connected, disconnected, connecting, error)
   */
  registerStatusElement(elementId, initialStatus = 'disconnected') {
    this.statusElements[elementId] = {
      elementId,
      currentStatus: initialStatus
    };

    // Apply initial status
    this.updateStatus(elementId, initialStatus);
  }

  /**
   * Update a status element with the specified status
   * @param {string} elementId - The ID of the status element
   * @param {string} status - New status (connected, disconnected, connecting, error)
   * @param {string} [customText] - Optional custom text to display
   */
  updateStatus(elementId, status, customText = null) {
    if (!this.statusElements[elementId]) {
      // Auto-register if not registered yet
      this.registerStatusElement(elementId, status);
      return;
    }

    // Get the element
    const element = document.getElementById(elementId);
    if (!element) {
      return;
    }

    // Get status configuration
    const statusConfig = this.statusConfig[status];
    if (!statusConfig) {
      return;
    }

    // Update the element
    element.className = statusConfig.className;
    element.textContent = customText || statusConfig.text;

    // Store current status
    this.statusElements[elementId].currentStatus = status;
  }

  /**
   * Get the current status of an element
   * @param {string} elementId - The ID of the status element
   * @returns {string} Current status
   */
  getStatus(elementId) {
    if (!this.statusElements[elementId]) {
      return null;
    }
    return this.statusElements[elementId].currentStatus;
  }

  /**
   * Clean up any invisible or non-existent status elements
   */
  cleanupStatusElements() {
    Object.keys(this.statusElements).forEach(elementId => {
      const element = document.getElementById(elementId);
      if (!element) {
        delete this.statusElements[elementId];
      }
    });
  }
}

// Create a global instance
window.webSocketStatusManager = window.webSocketStatusManager || new WebSocketStatusManager();

// Make it accessible as a global object instead of using ES module exports
// This avoids the 'Unexpected token export' error

// For backwards compatibility with any code that might try to import this
if (typeof module !== 'undefined' && module.exports) {
  module.exports = window.webSocketStatusManager;
}
