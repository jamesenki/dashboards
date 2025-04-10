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
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
    errorSelectors: ['.shadow-document-error', '.metadata-error', '.reconnection-message'],
    statusIndicatorSelector: '#realtime-connection-status',
    connectionClass: {
      connected: 'connected',
      disconnected: 'disconnected'
    }
  };

  // Track WebSocket state
  let wsState = {
    isConnected: false,
    reconnectAttempts: 0,
    connectionErrors: false
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
   */
  function updateConnectionStatus(isConnected) {
    const statusIndicator = document.querySelector(config.statusIndicatorSelector);
    if (!statusIndicator) return;

    if (isConnected) {
      statusIndicator.classList.add(config.connectionClass.connected);
      statusIndicator.classList.remove(config.connectionClass.disconnected);
      statusIndicator.textContent = 'Connected';
    } else {
      statusIndicator.classList.remove(config.connectionClass.connected);
      statusIndicator.classList.add(config.connectionClass.disconnected);
      statusIndicator.textContent = 'Disconnected';
    }

    wsState.isConnected = isConnected;
  }

  /**
   * Monitor WebSocket events across the application
   */
  function monitorWebSocketEvents() {
    // Listen for WebSocket events
    document.addEventListener('ws-connect', () => {
      wsState.isConnected = true;
      wsState.reconnectAttempts = 0;
      wsState.connectionErrors = false;
      updateConnectionStatus(true);
    });

    document.addEventListener('ws-disconnect', () => {
      wsState.isConnected = false;
      updateConnectionStatus(false);
    });

    document.addEventListener('ws-error', () => {
      wsState.connectionErrors = true;
      updateConnectionStatus(false);
    });

    document.addEventListener('shadow-update', () => {
      // If we're getting updates, we're connected
      if (!wsState.isConnected) {
        wsState.isConnected = true;
        updateConnectionStatus(true);
      }
    });

    console.log('WebSocket Resilience: Event monitoring active');
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
   * Initialize the resilience handler
   */
  function initialize() {
    console.log('WebSocket Resilience: Starting initialization');

    // Set up error visibility
    ensureErrorVisibility();

    // Monitor WebSocket events
    monitorWebSocketEvents();

    // Enhance shadow handler
    enhanceShadowHandler();

    console.log('WebSocket Resilience: Initialization complete');
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
  } else {
    initialize();
  }
})();
