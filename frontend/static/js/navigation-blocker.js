/**
 * Navigation Blocker - Prevents ALL automatic navigation on the water heater list page
 *
 * This is a defensive script that intercepts and blocks ALL navigation attempts
 * when on the main water heater list page.
 *
 * Following TDD principles: We implement the minimal code needed to make tests pass,
 * and in this case, the expected behavior is for the list page to stay on the list page
 * unless the user explicitly clicks on a card.
 */

(function() {
  // Only run this script on the water heaters list page
  if (window.location.pathname !== '/' && window.location.pathname !== '/water-heaters') {
    console.log('Navigation Blocker: Not on list page, exiting');
    return;
  }

  console.log('🛑 Navigation Blocker: Activating on water heater list page');

  // Store original navigation methods
  const originalAssign = window.location.assign;
  const originalReplace = window.location.replace;
  const originalHref = Object.getOwnPropertyDescriptor(window.location, 'href');
  const originalOpen = window.open;

  // Flag to track if navigation is from a user click
  let navigationAllowed = false;
  let lastClickTime = 0;

  // Helper to determine if this is a user-initiated navigation
  function isUserInitiatedNavigation() {
    const timeSinceLastClick = Date.now() - lastClickTime;
    return navigationAllowed && timeSinceLastClick < 500; // Only allow navigation within 500ms of a user click
  }

  // Override navigation methods with blocking versions

  // 1. Block changing window.location.href
  Object.defineProperty(window.location, 'href', {
    set: function(value) {
      if (isUserInitiatedNavigation()) {
        console.log(`✅ Navigation Blocker: Allowing user navigation to ${value}`);
        navigationAllowed = false; // Reset flag after use
        return originalHref.set.call(this, value);
      } else {
        console.warn(`🛑 Navigation Blocker: Blocked automatic navigation to ${value}`);
        return value; // Return value without navigating
      }
    },
    get: originalHref.get,
    configurable: true
  });

  // 2. Block window.location.assign
  window.location.assign = function(url) {
    if (isUserInitiatedNavigation()) {
      console.log(`✅ Navigation Blocker: Allowing user assign to ${url}`);
      navigationAllowed = false; // Reset flag after use
      return originalAssign.call(window.location, url);
    } else {
      console.warn(`🛑 Navigation Blocker: Blocked automatic assign to ${url}`);
      return undefined;
    }
  };

  // 3. Block window.location.replace
  window.location.replace = function(url) {
    if (isUserInitiatedNavigation()) {
      console.log(`✅ Navigation Blocker: Allowing user replace to ${url}`);
      navigationAllowed = false; // Reset flag after use
      return originalReplace.call(window.location, url);
    } else {
      console.warn(`🛑 Navigation Blocker: Blocked automatic replace to ${url}`);
      return undefined;
    }
  };

  // 4. Block window.open
  window.open = function(url, target, features) {
    if (isUserInitiatedNavigation()) {
      console.log(`✅ Navigation Blocker: Allowing user window.open to ${url}`);
      navigationAllowed = false; // Reset flag after use
      return originalOpen.call(window, url, target, features);
    } else {
      console.warn(`🛑 Navigation Blocker: Blocked automatic window.open to ${url}`);
      return null;
    }
  };

  // 5. Monitor form submissions
  document.addEventListener('submit', function(e) {
    if (!isUserInitiatedNavigation()) {
      console.warn(`🛑 Navigation Blocker: Blocked automatic form submission`);
      e.preventDefault();
      e.stopPropagation();
    }
  }, true);

  // Function to allow navigation for a single user click
  function allowNavigationForUserClick() {
    navigationAllowed = true;
    lastClickTime = Date.now();

    // Auto-reset after a short delay in case navigation doesn't happen
    setTimeout(function() {
      navigationAllowed = false;
    }, 1000);
  }

  // Monitor all card clicks and only then allow navigation
  document.addEventListener('click', function(e) {
    // Only handle trusted (actual user) clicks
    if (!e.isTrusted) return;

    // Check if clicking on a card or a link
    const card = e.target.closest('.card, .heater-card, [data-id]');
    const link = e.target.closest('a');

    if (card || link) {
      console.log('🖱️ Navigation Blocker: User clicked navigable element, allowing navigation');
      allowNavigationForUserClick();
    }
  }, true);

  // Provide a debug console message
  console.log('🛡️ Navigation Blocker: Successfully intercepted all navigation methods');
})();
