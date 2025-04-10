/**
 * WebSocket Resilience Handler
 *
 * Enhances the WebSocket connection reliability and ensures proper error display
 * following Test-Driven Development principles:
 *
 * 1. RED: Tests expect error messages to be visible when shadow document is missing
 * 2. GREEN: This code ensures errors are properly displayed and not hidden
 * 3. REFACTOR: Optimizes connection handling without breaking functionality
 */

(function() {
  'use strict';

  console.log('WebSocket Resilience: Initializing');

  // Configuration
  const config = {
    reconnectInterval: 2000, // Faster reconnect interval
    maxReconnectAttempts: 10, // More reconnection attempts for MQTT stability
    initialReconnectDelay: 500, // Start with a short delay
    maxReconnectDelay: 10000, // Cap maximum delay
    errorSelectors: ['.shadow-document-error', '.metadata-error', '.reconnection-message'],
    statusIndicatorSelector: '#realtime-connection-status',
    connectionClass: {
      connected: 'connected',
      disconnected: 'disconnected',
      connecting: 'connecting'
    }
  };

  // Track WebSocket state
  let wsState = {
    isConnected: false,
    reconnectAttempts: 0,
    connectionErrors: false,
    reconnectTimers: {}, // Track reconnection timers by endpoint
    lastConnectionAttempt: Date.now(),
    mqttConnected: false, // Track MQTT broker connection status
    shadowsFound: false // Track if shadows have been successfully found
  };

  /**
   * Ensure error messages remain visible
   */
  function ensureErrorVisibility() {
    // For each error container
    config.errorSelectors.forEach(selector => {
      const errorElement = document.querySelector(selector);
      if (!errorElement) return;

      // Create observer to watch for display changes
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.attributeName === 'style' &&
              errorElement.style.display === 'none' &&
              errorElement.textContent.includes('shadow document')) {

            // Error is hidden but should be visible - override
            errorElement.style.display = 'block';
            console.log('WebSocket Resilience: Kept error message visible');
          }
        });
      });

      // Start observing
      observer.observe(errorElement, { attributes: true });
    });

    console.log('WebSocket Resilience: Error visibility monitoring active');
  }

  /**
   * Update connection status indicator
   * @param {string} status - 'connected', 'disconnected', or 'connecting'
   * @param {string} [message] - Optional status message to display
   */
  function updateConnectionStatus(status, message) {
    const statusIndicator = document.querySelector(config.statusIndicatorSelector);
    if (!statusIndicator) return;

    // Reset all status classes first
    statusIndicator.classList.remove(
      config.connectionClass.connected,
      config.connectionClass.disconnected,
      config.connectionClass.connecting
    );

    // Add the appropriate class
    const statusClass = config.connectionClass[status] || config.connectionClass.disconnected;
    statusIndicator.classList.add(statusClass);

    // Set the status text (with message if provided)
    const statusText = message || (
      status === 'connected' ? 'Connected' : 
      status === 'connecting' ? 'Connecting...' : 
      'Disconnected'
    );
    statusIndicator.textContent = statusText;

    // Update the global state
    wsState.isConnected = (status === 'connected');
    
    console.log(`WebSocket status updated to: ${status} - ${message || ''}`);
  }

  /**
   * Monitor WebSocket events across the application
   */
  function monitorWebSocketEvents() {
    // Listen for WebSocket events
    document.addEventListener('ws-connect', (event) => {
      wsState.isConnected = true;
      wsState.reconnectAttempts = 0;
      wsState.connectionErrors = false;
      
      // Get connection details from event if available
      const detail = event.detail || {};
      const endpoint = detail.endpoint || 'server';
      updateConnectionStatus('connected', `Connected to ${endpoint}`);
      
      // If this is an MQTT connection, mark it
      if (detail.url && (detail.url.includes('mqtt') || detail.url.includes('broker'))) {
        wsState.mqttConnected = true;
      }
    });

    document.addEventListener('ws-disconnect', (event) => {
      const detail = event.detail || {};
      const endpoint = detail.endpoint || 'server';
      const wasConnected = wsState.isConnected;
      
      wsState.isConnected = false;
      
      // If this was an MQTT connection, update its status
      if (detail.url && (detail.url.includes('mqtt') || detail.url.includes('broker'))) {
        wsState.mqttConnected = false;
      }
      
      // Only show disconnected if we were previously connected
      if (wasConnected) {
        updateConnectionStatus('disconnected', `Disconnected from ${endpoint}`);
      }
      
      // Schedule reconnection if needed
      if (wsState.reconnectAttempts < config.maxReconnectAttempts) {
        setTimeout(() => {
          updateConnectionStatus('connecting', `Reconnecting to ${endpoint}...`);
          document.dispatchEvent(new CustomEvent('ws-reconnect-attempt', { detail }));
        }, config.reconnectInterval);
        wsState.reconnectAttempts++;
      }
    });

    document.addEventListener('ws-error', (event) => {
      const detail = event.detail || {};
      const endpoint = detail.endpoint || 'server';
      
      wsState.connectionErrors = true;
      updateConnectionStatus('disconnected', `Error connecting to ${endpoint}`);
    });

    document.addEventListener('shadow-update', (event) => {
      // If we're getting shadow updates, we're connected
      wsState.shadowsFound = true;
      
      if (!wsState.isConnected) {
        wsState.isConnected = true;
        updateConnectionStatus('connected', 'Connected (receiving data)');
      }
    });
    
    // Listen specifically for MQTT connection events
    document.addEventListener('mqtt-connected', () => {
      wsState.mqttConnected = true;
      // Only update status if we weren't already connected
      if (!wsState.isConnected) {
        updateConnectionStatus('connected', 'Connected to MQTT broker');
      }
    });
    
    document.addEventListener('mqtt-disconnected', () => {
      wsState.mqttConnected = false;
      // Only show disconnected if we don't have other connections active
      if (wsState.isConnected && !wsState.shadowsFound) {
        updateConnectionStatus('disconnected', 'Disconnected from MQTT broker');
      }
    });

    console.log('WebSocket Resilience: Enhanced event monitoring active');
  }

  /**
   * Enhance ShadowDocumentHandler with better error handling if present
   */
  function enhanceShadowHandler() {
    // Wait for shadow handler to be initialized
    const checkInterval = setInterval(() => {
      if (window.shadowDocumentHandler) {
        clearInterval(checkInterval);

        // Enhance error handling
        const originalHandleError = window.shadowDocumentHandler.handleShadowError;
        window.shadowDocumentHandler.handleShadowError = function(error) {
          // Call original
          originalHandleError.call(this, error);

          // Ensure error is visible
          if (this.errorElement) {
            this.errorElement.style.display = 'block';

            // Focus the tab containing the error if needed
            const tabId = this.errorElement.closest('.tab-panel')?.id;
            if (tabId && window.OptimizedTabManager) {
              window.OptimizedTabManager.activateTab(tabId);
            }
          }
        };

        console.log('WebSocket Resilience: Enhanced ShadowDocumentHandler');
      }
    }, 100);
  }

  /**
   * Helper function to check if a shadow document exists and is properly connected
   */
  function checkShadowDocumentStatus() {
    // Set an initial check and periodic rechecks
    const checkShadowStatus = () => {
      // Check if shadowDocumentHandler exists and has a device
      if (window.shadowDocumentHandler && window.shadowDocumentHandler.deviceId) {
        // Attempt to access shadow data
        window.shadowDocumentHandler.getShadowState().then(state => {
          if (state) {
            wsState.shadowsFound = true;
            // Dispatch an event that the shadow was found successfully
            document.dispatchEvent(new CustomEvent('shadow-document-found', {
              detail: { deviceId: window.shadowDocumentHandler.deviceId }
            }));
            
            // Update connection status if we have MQTT too
            if (wsState.mqttConnected) {
              updateConnectionStatus('connected', 'Connected (shadow document found)');
            }
          }
        }).catch(err => {
          console.warn('Shadow document check failed:', err);
          wsState.shadowsFound = false;
        });
      }
    };
    
    // Initial check after a short delay
    setTimeout(checkShadowStatus, 2000);
    
    // Set up periodic rechecks if not connected
    const recheckInterval = setInterval(() => {
      if (!wsState.shadowsFound) {
        checkShadowStatus();
      } else {
        // Once we find shadows, we can stop checking
        clearInterval(recheckInterval);
      }
    }, 5000); // Check every 5 seconds
  }
  
  /**
   * Initialize the resilience handler
   */
  function initialize() {
    console.log('WebSocket Resilience: Starting initialization');

    // Initial status update
    updateConnectionStatus('connecting', 'Initializing connection...');
    
    // Set up error visibility
    ensureErrorVisibility();

    // Monitor WebSocket events
    monitorWebSocketEvents();

    // Enhance shadow handler
    enhanceShadowHandler();
    
    // Check shadow document status
    checkShadowDocumentStatus();
    
    console.log('WebSocket Resilience: Initialization complete');
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
  } else {
    initialize();
  }
})();
