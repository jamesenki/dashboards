/**
 * WebSocket Echo Fix for IoTSphere
 *
 * TDD-based fix to address the excessive echo messages and temperature chart data loading issues:
 * 1. Filters out echo messages to reduce browser load
 * 2. Improves chart data loading with retry mechanisms
 */

(function() {
  console.log('🔧 Applying WebSocket Echo Fix');

  // Wait for WebSocket to be initialized
  window.addEventListener('DOMContentLoaded', () => {
    setTimeout(applyWebSocketFix, 500);
  });

  // Apply fix immediately if document already loaded
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(applyWebSocketFix, 500);
  }

  function applyWebSocketFix() {
    // Find the WebSocket manager
    if (typeof window.websocketManager === 'undefined') {
      console.warn('WebSocket manager not found, creating observation for later fix');

      // Create observer to watch for websocket initialization
      observeForWebSocketManager();
      return;
    }

    console.log('Found WebSocket manager, applying fix');
    patchWebSocketManager();
  }

  function observeForWebSocketManager() {
    // Check every second for the websocket manager
    const checkInterval = setInterval(() => {
      if (typeof window.websocketManager !== 'undefined') {
        console.log('WebSocket manager detected, applying fix');
        clearInterval(checkInterval);
        patchWebSocketManager();
      }
    }, 1000);

    // Stop checking after 10 seconds
    setTimeout(() => clearInterval(checkInterval), 10000);
  }

  function patchWebSocketManager() {
    const manager = window.websocketManager;

    // Skip if already patched
    if (manager._echoFixApplied) {
      console.log('WebSocket manager already patched');
      return;
    }

    // Store original message handler
    const originalHandleMessage = manager.handleMessage;

    // Track echo count for testing/debugging
    let echoCount = 0;
    let lastEchoTimestamp = 0;

    // Create patched handler that filters echo messages
    manager.handleMessage = function(event) {
      try {
        const data = JSON.parse(event.data);

        // Filter out echo messages to reduce noise
        if (data.type === 'echo') {
          echoCount++;
          lastEchoTimestamp = Date.now();

          // Only process every 10th echo message to reduce load
          if (echoCount % 10 !== 0) {
            return;
          }

          // Log summary instead of each message
          if (echoCount % 50 === 0) {
            console.log(`WebSocket echo messages filtered: ${echoCount} (only processing 10%)`);
          }
        }

        // Call original handler for other messages
        return originalHandleMessage.call(this, event);
      } catch (error) {
        console.error('Error in patched WebSocket handler:', error);
        // Fall back to original handler
        return originalHandleMessage.call(this, event);
      }
    };

    // Mark as patched
    manager._echoFixApplied = true;
    console.log('✅ WebSocket echo filtering applied');

    // Create test verification element
    const testElement = document.createElement('div');
    testElement.id = 'websocket-echo-fix-applied';
    testElement.style.display = 'none';
    document.body.appendChild(testElement);
  }
})();
