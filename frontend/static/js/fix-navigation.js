/**
 * Enhanced Fix Navigation Issue v2.0
 *
 * This script fixes the navigation to detail pages by resolving conflicts
 * between competing navigation scripts and ensuring reliable navigation
 * between the list page and device detail pages.
 */

(function() {
  // Execute immediately and again when DOM is loaded
  initNavigation();

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNavigation);
  }

  // Also add a failsafe to run after a delay
  setTimeout(initNavigation, 1000);

  function initNavigation() {
    console.log('🧭 Enhanced Navigation Fix v2.0: Initializing...');

    // Run on any page - we need to fix list-to-detail and back navigation
    const isListPage = window.location.pathname === '/' ||
                      window.location.pathname === '/water-heaters' ||
                      window.location.pathname.endsWith('/index.html');

    // Handle navigation based on page type
    if (isListPage) {
      console.log('🧭 On list page, fixing card navigation...');
      fixCardNavigation();
    } else {
      console.log('🧭 On detail page, ensuring back navigation works...');
      fixBackNavigation();
    }

    // Observe DOM for new cards
    const observer = new MutationObserver(function(mutations) {
      let shouldFix = false;
      mutations.forEach(mutation => {
        if (mutation.addedNodes.length > 0) {
          shouldFix = true;
        }
      });

      if (shouldFix) {
        fixCardNavigation();
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });

    // Initial fix
    setTimeout(fixCardNavigation, 500);

    // Backup periodic check in case mutation observer fails
    setInterval(fixCardNavigation, 2000);
  }

  function fixCardNavigation() {
    console.log('🧭 Enhanced Navigation Fix: Fixing card navigation');

    // Expand card selector to catch all possible card formats
    const allCards = document.querySelectorAll(
      '.card[data-id]:not([data-nav-fixed-ultimate]), ' +
      '.heater-card:not([data-nav-fixed-ultimate]), ' +
      '.device-card:not([data-nav-fixed-ultimate]), ' +
      '.water-heater-card:not([data-nav-fixed-ultimate]), ' +
      '.list-item[id^="heater-"]:not([data-nav-fixed-ultimate]), ' +
      '[id^="heater-"]:not([data-nav-fixed-ultimate])'  // Catch any element with an ID starting with 'heater-'
    );

    console.log(`🧭 Enhanced Navigation Fix: Found ${allCards.length} cards to fix`);

    // If no cards found, try again later
    if (allCards.length === 0) {
      console.log('🧭 No cards found, scheduling retry in 1 second');
      setTimeout(fixCardNavigation, 1000);
      return;
    }

    allCards.forEach(card => {
      // Skip already fixed cards
      if (card.hasAttribute('data-nav-fixed-ultimate')) return;

      // Try to extract device ID
      let id = card.getAttribute('data-id');

      // If no data-id, try to extract from ID attribute (e.g., heater-wh-001)
      if (!id && card.id && card.id.startsWith('heater-')) {
        id = card.id.substring(7); // Remove 'heater-' prefix
      }

      if (!id) {
        console.log('🧭 Card without ID, skipping', card);
        return; // Skip cards without ID
      }

      console.log(`🧭 Enhanced Navigation Fix: Fixing card ${id}`);

      // Force navigation directly on the card
      card.onclick = function(event) {
        // Don't navigate if clicking on a button
        if (event.target.closest('button')) return;

        // Stop event propagation
        event.preventDefault();
        event.stopPropagation();

        // Get detail URL
        const detailUrl = `/water-heaters/${id}`;
        console.log(`🧭 Enhanced Navigation: Navigating to ${detailUrl}`);

        // Use multiple navigation methods for redundancy

        // 1. Direct location change (primary method)
        window.location.href = detailUrl;

        // 2. Create and trigger a real link (backup)
        setTimeout(() => {
          try {
            const link = document.createElement('a');
            link.href = detailUrl;
            link.target = '_self';
            link.setAttribute('data-force-navigation', 'true');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
          } catch (e) {
            console.error('Backup navigation failed:', e);
            // 3. Last resort - direct assignment with delay
            setTimeout(() => { document.location = detailUrl; }, 10);
          }
        }, 50);
      };

      // Style as clickable
      card.style.cursor = 'pointer';
      card.classList.add('clickable-card');

      // Mark as ultimately fixed
      card.setAttribute('data-nav-fixed-ultimate', 'true');
    });

    // Schedule periodic re-check for dynamically added cards
    setTimeout(checkForNewCards, 2000);
  }

  function checkForNewCards() {
    // Look for any cards without our fix applied
    const unfixedCards = document.querySelectorAll(
      '.card[data-id]:not([data-nav-fixed-ultimate]), ' +
      '.heater-card:not([data-nav-fixed-ultimate]), ' +
      '.device-card:not([data-nav-fixed-ultimate]), ' +
      '.water-heater-card:not([data-nav-fixed-ultimate]), ' +
      '.list-item[id^="heater-"]:not([data-nav-fixed-ultimate]), ' +
      '[id^="heater-"]:not([data-nav-fixed-ultimate])'
    );

    if (unfixedCards.length > 0) {
      console.log(`🧭 Found ${unfixedCards.length} new cards, fixing navigation...`);
      fixCardNavigation();
    } else {
      // Keep checking periodically
      setTimeout(checkForNewCards, 2000);
    }
  }

  function fixBackNavigation() {
    // Fix any back buttons or links
    const backLinks = document.querySelectorAll('a.back-link, .back-button, [data-action="back"]');

    backLinks.forEach(link => {
      // Already fixed
      if (link.hasAttribute('data-nav-fixed')) return;

      // Store original handler
      const originalOnClick = link.onclick;

      // Add reliable back navigation
      link.onclick = function(event) {
        event.preventDefault();
        console.log('🧭 Enhanced back navigation triggered');

        // Try multiple approaches for back navigation
        window.history.back();

        // Fallback if history.back() doesn't work
        setTimeout(() => {
          const listUrl = '/water-heaters';
          window.location.href = listUrl;
        }, 100);

        // Call original handler if it exists
        if (typeof originalOnClick === 'function') {
          originalOnClick.call(this, event);
        }
      };

      link.setAttribute('data-nav-fixed', 'true');
    });
  }
})();
