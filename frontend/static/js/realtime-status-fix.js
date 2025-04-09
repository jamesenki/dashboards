/**
 * Real-time Status Fix
 * Directly fixes the issue with real-time connection status showing both "Connected" and "None"
 */
(function() {
  // Wait for the DOM to be fully loaded
  document.addEventListener('DOMContentLoaded', function() {
    console.log('🔄 DIRECT FIX: Initializing real-time status fix');

    // Function to fix mismatched status indicators
    function fixRealtimeStatus() {
      // Find the status indicator element
      const statusIndicator = document.getElementById('realtime-connection-status');
      const statusText = document.getElementById('connection-type');

      if (statusIndicator && statusText) {
        console.log('✅ Found real-time status elements, applying fix');

        // Check if the classes are inconsistent with the text
        if (statusIndicator.classList.contains('connected') && statusText.textContent !== 'Connected') {
          statusText.textContent = 'Connected';
          console.log('🔄 Fixed: Status text updated to match "Connected" indicator');
        } else if (statusIndicator.classList.contains('disconnected') && statusText.textContent !== 'Disconnected') {
          statusText.textContent = 'Disconnected';
          console.log('🔄 Fixed: Status text updated to match "Disconnected" indicator');
        } else if (!statusIndicator.classList.contains('connected') && !statusIndicator.classList.contains('disconnected')) {
          // If status indicator has neither class, standardize to disconnected
          statusIndicator.className = 'status-indicator disconnected';
          statusText.textContent = 'Disconnected';
          console.log('🔄 Fixed: Standardized inconsistent status to "Disconnected"');
        }
      }
    }

    // Fix immediately on load
    setTimeout(fixRealtimeStatus, 500);

    // Setup a MutationObserver to watch for changes to the status elements
    const observer = new MutationObserver(function(mutations) {
      mutations.forEach(function(mutation) {
        // If the status indicator or text changed, fix any inconsistencies
        if (mutation.target.id === 'realtime-connection-status' ||
            mutation.target.id === 'connection-type') {
          console.log('🔍 Detected change in real-time status, checking for inconsistencies');
          fixRealtimeStatus();
        }
      });
    });

    // Start observing the document with configured parameters
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: ['class', 'textContent']
    });

    // Run the fix every second to catch any missed updates
    setInterval(fixRealtimeStatus, 1000);

    // Patch the updateWebSocketStatus function if it exists
    if (window.updateWebSocketStatus) {
      const originalUpdateWebSocketStatus = window.updateWebSocketStatus;
      window.updateWebSocketStatus = function(isConnected) {
        // Call the original function
        originalUpdateWebSocketStatus(isConnected);

        // Ensure consistency
        const statusIndicator = document.getElementById('realtime-connection-status');
        const statusText = document.getElementById('connection-type');

        if (statusIndicator && statusText) {
          if (isConnected) {
            statusIndicator.className = 'status-indicator connected';
            statusText.textContent = 'Connected';
          } else {
            statusIndicator.className = 'status-indicator disconnected';
            statusText.textContent = 'Disconnected';
          }
          console.log(`🔄 Patched status update to: ${isConnected ? 'Connected' : 'Disconnected'}`);
        }
      };
    }

    // Final direct updates to the WebSocketManager
    if (window.WebSocketManager) {
      console.log('🛠️ Patching WebSocketManager prototype');

      // Store the original onConnectionChange function
      const originalPrototype = WebSocketManager.prototype.handleConnectionChange;

      // Override with our fixed version
      WebSocketManager.prototype.handleConnectionChange = function(connectionId, isConnected) {
        // Call the original function
        if (originalPrototype) {
          originalPrototype.call(this, connectionId, isConnected);
        }

        // Ensure both elements are updated
        const statusIndicator = document.getElementById('realtime-connection-status');
        const statusText = document.getElementById('connection-type');

        if (statusIndicator && statusText) {
          if (isConnected) {
            statusIndicator.className = 'status-indicator connected';
            statusText.textContent = 'Connected';
          } else {
            statusIndicator.className = 'status-indicator disconnected';
            statusText.textContent = 'Disconnected';
          }
          console.log(`⚡ WebSocketManager patched: connection status updated to ${isConnected ? 'Connected' : 'Disconnected'}`);
        }
      };
    }
  });
})();
