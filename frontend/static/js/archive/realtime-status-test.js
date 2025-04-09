/**
 * Real-time Status Test and Fix
 * Tests and directly fixes the issue with real-time connection status showing both "Connected" and "None"
 * Following TDD principles: Red (failing test) -> Green (fix) -> Refactor
 */
(function() {
  // Run when DOM is fully loaded
  document.addEventListener('DOMContentLoaded', function() {
    console.log('🧪 TDD: Running real-time status test and fix');

    // Test function to verify status consistency
    function testRealtimeStatusConsistency() {
      // RED PHASE: Find both status elements and check for inconsistency
      const statusIndicator = document.getElementById('realtime-connection-status');
      const statusText = document.getElementById('connection-type');

      if (!statusIndicator || !statusText) {
        console.log('⏳ Status elements not yet loaded, will retry...');
        return false;
      }

      // Check if status is consistent
      const hasConnectedClass = statusIndicator.classList.contains('connected');
      const hasDisconnectedClass = statusIndicator.classList.contains('disconnected');
      const textIsConnected = statusText.textContent === 'Connected';
      const textIsDisconnected = statusText.textContent === 'Disconnected';

      // Check for inconsistencies
      const isConsistent =
        (hasConnectedClass && textIsConnected) ||
        (hasDisconnectedClass && textIsDisconnected);

      if (!isConsistent) {
        console.error('❌ TEST FAILED: Real-time status inconsistency detected');
        console.log(`Indicator classes: ${statusIndicator.className}`);
        console.log(`Status text: "${statusText.textContent}"`);

        // GREEN PHASE: Fix the inconsistency
        fixRealtimeStatus();
        return false;
      } else {
        console.log('✅ TEST PASSED: Real-time status is consistent');
        return true;
      }
    }

    // The fix function that ensures both elements show the same status
    function fixRealtimeStatus() {
      const statusIndicator = document.getElementById('realtime-connection-status');
      const statusText = document.getElementById('connection-type');

      if (!statusIndicator || !statusText) return;

      console.log('🔧 APPLYING FIX: Ensuring real-time status consistency');

      // Determine the correct status based on the more reliable indicator
      const hasConnectedClass = statusIndicator.classList.contains('connected');

      // Set both elements to the same status
      if (hasConnectedClass) {
        // Should be connected
        statusIndicator.className = 'status-indicator connected';
        statusText.textContent = 'Connected';
        console.log('✅ Fixed: Set both elements to "Connected"');
      } else {
        // Default to disconnected for any inconsistent state
        statusIndicator.className = 'status-indicator disconnected';
        statusText.textContent = 'Disconnected';
        console.log('✅ Fixed: Set both elements to "Disconnected"');
      }

      // Run test again to verify fix
      setTimeout(() => {
        const isFixed = testRealtimeStatusConsistency();
        if (isFixed) {
          console.log('🎉 REFACTOR PHASE: Fix verified, creating permanent monkey patch');
          createMonkeyPatch();
        }
      }, 100);
    }

    // REFACTOR PHASE: Create a monkey patch for the WebSocketManager
    function createMonkeyPatch() {
      console.log('🛠️ Creating monkey patch for WebSocket status updates');

      // Find functions that might update the connection status
      if (window.updateWebSocketStatus) {
        const originalUpdate = window.updateWebSocketStatus;
        window.updateWebSocketStatus = function(isConnected) {
          // Call original
          originalUpdate(isConnected);

          // Ensure both elements are updated consistently
          const statusIndicator = document.getElementById('realtime-connection-status');
          const statusText = document.getElementById('connection-type');

          if (statusIndicator && statusText) {
            statusIndicator.className = `status-indicator ${isConnected ? 'connected' : 'disconnected'}`;
            statusText.textContent = isConnected ? 'Connected' : 'Disconnected';
          }
        };
        console.log('✅ Patched window.updateWebSocketStatus');
      }

      // Create a MutationObserver to keep status consistent
      const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
          if (mutation.target.id === 'realtime-connection-status' ||
              mutation.target.id === 'connection-type') {
            // Only run the test if we detected a change to either element
            testRealtimeStatusConsistency();
            break;
          }
        }
      });

      // Start observing document
      observer.observe(document.body, {
        attributes: true,
        childList: true,
        subtree: true,
        characterData: true
      });

      console.log('✅ Created MutationObserver to maintain status consistency');
    }

    // Force immediate fix on page load
    setTimeout(testRealtimeStatusConsistency, 1000);

    // Also test periodically
    setInterval(testRealtimeStatusConsistency, 2000);
  });
})();
