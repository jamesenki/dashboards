/**
 * Real-time Status Formatter
 * Formats the real-time connection status indicator to avoid duplication
 * while maintaining the styling and visual appearance of the status
 */
(function() {
  // Run this fix when the DOM is loaded
  document.addEventListener('DOMContentLoaded', function() {
    console.log('🔄 Initializing real-time status formatter');
    
    // Define our status configurations
    const statusConfigs = {
      'connected': {
        color: '#2ecc71', // Green
        text: 'Connected'
      },
      'disconnected': {
        color: '#e74c3c', // Red
        text: 'Disconnected'
      },
      'connecting': {
        color: '#f39c12', // Yellow/orange
        text: 'Connecting'
      }
    };
    
    // Function to update the status display
    function updateStatusDisplay() {
      // Get the elements
      const statusIndicator = document.getElementById('realtime-connection-status');
      const statusContainer = document.getElementById('connection-type-container');
      
      if (!statusIndicator || !statusContainer) {
        console.log('⏳ Status elements not found, will try again later');
        return;
      }
      
      // Determine current status based on indicator classes
      let currentStatus = 'disconnected'; // Default
      
      if (statusIndicator.classList.contains('connected')) {
        currentStatus = 'connected';
      } else if (statusIndicator.classList.contains('connecting')) {
        currentStatus = 'connecting';
      }
      
      // Update the text container with proper styling
      const config = statusConfigs[currentStatus];
      statusContainer.innerHTML = `<span style="color: ${config.color}; font-weight: bold; margin-left: 5px;">${config.text}</span>`;
      
      console.log(`✅ Updated real-time status display to: ${config.text}`);
    }
    
    // Initial update after a short delay
    setTimeout(updateStatusDisplay, 500);
    
    // Setup a MutationObserver to detect changes to the status indicator
    const observer = new MutationObserver(function(mutations) {
      for (const mutation of mutations) {
        if (mutation.target.id === 'realtime-connection-status') {
          console.log('🔍 Status indicator changed, updating display');
          updateStatusDisplay();
          break;
        }
      }
    });
    
    // Start observing changes to the status indicator
    observer.observe(document.body, {
      attributes: true,
      childList: true,
      subtree: true
    });
    
    // Patch the WebSocketManager if available
    if (window.WebSocketManager) {
      // Keep track of the original implementation
      const originalProto = WebSocketManager.prototype.handleConnectionChange;
      
      // Override with our own implementation
      WebSocketManager.prototype.handleConnectionChange = function(connectionId, isConnected) {
        // Call the original method
        if (originalProto) {
          originalProto.call(this, connectionId, isConnected);
        }
        
        // Update our status display
        setTimeout(updateStatusDisplay, 50);
      };
      
      console.log('✅ Patched WebSocketManager to update status display');
    }
    
    // Also run periodically to ensure it's always correct
    setInterval(updateStatusDisplay, 1000);
  });
})();
