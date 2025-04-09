/**
 * Prevent Auto-Navigation Module
 *
 * This script blocks any automatic navigation attempts that happen shortly after page load.
 * It follows TDD principles by ensuring navigation only occurs when users actually click.
 */

(function() {
  // Set a flag to prevent any navigation within the first few seconds of page load
  let allowNavigation = false;

  // Store the original window.location methods
  const originalAssign = window.location.assign;
  const originalReplace = window.location.replace;
  const originalHref = Object.getOwnPropertyDescriptor(window.location, 'href');

  // Helper to determine if navigation should be blocked
  function shouldBlockNavigation() {
    // Only allow navigation if:
    // 1. We've passed the initial block period, OR
    // 2. The navigation is coming from a trusted user event

    if (allowNavigation) {
      return false; // Don't block if we're past the block period
    }

    // Check if this is triggered by a user event
    const lastEvent = window.lastUserEvent;
    const now = Date.now();

    if (lastEvent && (now - lastEvent.timestamp < 1000)) {
      console.log('🧭 Navigation is coming from a recent user event, allowing');
      return false; // Allow if it's coming from a user event within the last second
    }

    console.log('🛑 Blocking automatic navigation attempt');
    return true; // Block in all other cases
  }

  // Track the last user event
  window.lastUserEvent = null;
  document.addEventListener('click', function(e) {
    if (e.isTrusted) {
      window.lastUserEvent = {
        type: 'click',
        timestamp: Date.now(),
        target: e.target
      };
      console.log('🖱️ Recorded user click event');
    }
  }, true);

  // Override window.location.href setter
  Object.defineProperty(window.location, 'href', {
    set: function(value) {
      if (shouldBlockNavigation()) {
        console.warn(`🛑 Blocked automatic navigation to: ${value}`);
        return;
      }

      console.log(`🧭 Allowing navigation to: ${value}`);
      return originalHref.set.call(this, value);
    },
    get: originalHref.get,
    configurable: true
  });

  // Override window.location.assign
  window.location.assign = function(url) {
    if (shouldBlockNavigation()) {
      console.warn(`🛑 Blocked automatic location.assign to: ${url}`);
      return;
    }

    return originalAssign.call(window.location, url);
  };

  // Override window.location.replace
  window.location.replace = function(url) {
    if (shouldBlockNavigation()) {
      console.warn(`🛑 Blocked automatic location.replace to: ${url}`);
      return;
    }

    return originalReplace.call(window.location, url);
  };

  // Allow navigation after a delay
  setTimeout(function() {
    allowNavigation = true;
    console.log('🧭 Navigation block period ended, normal navigation now allowed');
  }, 5000); // Block all navigation for 5 seconds after page load

  console.log('🛡️ Anti-auto-navigation protection active for 5 seconds');
})();
