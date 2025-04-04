/**
 * AquaTherm Card Navigation Fix
 *
 * This module ensures that all AquaTherm cards navigate correctly to their detail pages
 * when clicked. It's implemented as a separate global fix to ensure maximum reliability
 * without requiring changes to the original card rendering logic.
 *
 * Following TDD principles:
 * 1. Tests define the expected behavior (cards should navigate when clicked)
 * 2. We change the code to make tests pass, not vice versa
 *
 * IMPORTANT: This script should NOT cause automatic navigation on page load,
 * only enable navigation when cards are clicked.
 */

// Run the fix when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
  console.log('🔧 AquaTherm Navigation Fix: Setting up guaranteed navigation...');

  // Check if we're on the water heaters list page (not a detail page)
  const isListPage = window.location.pathname === '/' ||
                     window.location.pathname === '/water-heaters';

  if (isListPage) {
    console.log('🔧 On water heaters list page, setting up card navigation');
    setupAquaThermNavigation();

    // Also set up a mutation observer to handle dynamically added cards
    const observer = new MutationObserver(function(mutations) {
      setupAquaThermNavigation();
    });

    // Observe changes to the container where cards might be added
    const container = document.getElementById('water-heater-container') || document.body;
    observer.observe(container, { childList: true, subtree: true });
  } else {
    console.log('🔧 Not on list page, skipping card navigation setup');
  }
});

/**
 * Sets up reliable navigation for all AquaTherm cards
 */
function setupAquaThermNavigation() {
  // Find all cards on the page
  const allCards = document.querySelectorAll('[data-id]');
  let aquaThermCards = [];

  // Filter for AquaTherm cards
  allCards.forEach(card => {
    const id = card.getAttribute('data-id');
    if (id && id.startsWith('aqua-wh-')) {
      aquaThermCards.push(card);
    }
  });

  console.log(`🔧 AquaTherm Navigation Fix: Found ${aquaThermCards.length} AquaTherm cards`);

  // Add guaranteed navigation to each card
  aquaThermCards.forEach(card => {
    const id = card.getAttribute('data-id');
    const detailUrl = `/water-heaters/${id}`;

    // Remove existing click listeners to avoid conflicts
    const cardClone = card.cloneNode(true);
    card.parentNode.replaceChild(cardClone, card);

    // Use both direct anchor wrapping and onclick handler for belt-and-suspenders approach
    const wrapper = document.createElement('a');
    wrapper.href = detailUrl;
    wrapper.style.textDecoration = 'none';
    wrapper.style.color = 'inherit';
    wrapper.style.display = 'block';

    // Add additional click handler that's guaranteed to work
    wrapper.addEventListener('click', function(e) {
      e.preventDefault(); // Prevent default to use our custom handler
      console.log(`🔧 AquaTherm Navigation: Navigating to ${detailUrl}`);

      // Use both window.location approaches for maximum browser compatibility
      window.location.href = detailUrl;
      window.location = detailUrl;

      return false;
    });

    // Move the card into the wrapper
    cardClone.parentNode.insertBefore(wrapper, cardClone);
    wrapper.appendChild(cardClone);

    console.log(`🔧 AquaTherm Navigation Fix: Added guaranteed navigation to ${id}`);
  });
}
