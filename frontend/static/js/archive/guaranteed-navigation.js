/**
 * Guaranteed Navigation Fix for AquaTherm Cards
 *
 * This script ensures 100% reliable navigation for AquaTherm cards
 * by using the most direct approach possible.
 *
 * Following TDD principles: We make code changes to pass the tests,
 * not the other way around.
 */

// Run when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
  console.log('⚓ Guaranteed Navigation: Running setup');
  // Initial setup
  setupNavigation();

  // Set up a MutationObserver to watch for new cards instead of using setInterval
  // This is more efficient and won't cause constant reloading
  const observer = new MutationObserver(function(mutations) {
    // Only run the setup when we see actual DOM changes
    let shouldRun = false;

    // Check if any of the mutations involve adding nodes
    mutations.forEach(mutation => {
      if (mutation.addedNodes.length > 0) {
        shouldRun = true;
      }
    });

    if (shouldRun) {
      console.log('⚓ Guaranteed Navigation: DOM changed, checking for new cards');
      setupNavigation();
    }
  });

  // Start observing the document for added nodes
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
});

function setupNavigation() {
  console.log('⚓ Guaranteed Navigation: Setting up navigation handlers');

  // Use a more inclusive selector to catch all card types
  // First, try to find AquaTherm cards by ID pattern
  const aquaCardsByID = document.querySelectorAll('.card[data-id^="aqua-wh-"]');
  console.log(`⚓ Found ${aquaCardsByID.length} AquaTherm cards by ID pattern`);

  fixCardsNavigation(aquaCardsByID);

  // Also look for cards with 'heater-card' class to catch all water heater cards
  const allHeaterCards = document.querySelectorAll('.card.heater-card:not([data-nav-fixed])');
  console.log(`⚓ Found ${allHeaterCards.length} water heater cards to fix`);

  fixCardsNavigation(allHeaterCards);

  // Just to be sure, also target any card with data-id attribute that doesn't have navigation fixed
  const allCardsWithID = document.querySelectorAll('.card[data-id]:not([data-nav-fixed])');
  console.log(`⚓ Found ${allCardsWithID.length} cards with ID to fix`);

  fixCardsNavigation(allCardsWithID);
}

// Helper function to fix navigation for a collection of cards
function fixCardsNavigation(cards) {
  cards.forEach(card => {
    // Skip already processed cards
    if (card.hasAttribute('data-nav-fixed')) return;

    const id = card.getAttribute('data-id');
    if (!id) return; // Skip cards without ID

    const detailUrl = `/water-heaters/${id}`;
    console.log(`⚓ Fixing navigation for card ${id}`);

    // Remove existing onclick attributes which might interfere
    if (card.hasAttribute('onclick')) {
      card.removeAttribute('onclick');
    }

    // Create a completely new click handler with direct navigation
    // Two approaches for maximum reliability

    // Approach 1: Use direct click handler with location change
    card.addEventListener('click', function(event) {
      // Only respond to real user clicks, not programmatic ones
      if (!event.isTrusted) {
        console.log(`⚓ Ignoring programmatic click on card ${id}, preventing navigation`);
        return;
      }

      // Don't interfere with buttons inside cards
      if (event.target.closest('button')) return;

      // Stop any other handlers
      event.stopPropagation();

      console.log(`⚓ User clicked card ${id}, navigating to ${detailUrl}`);
      // Force navigation - most reliable approach
      window.location.href = detailUrl;
    });

    // Approach 2: Add a navigation helper element
    // This provides a backup navigation method
    const navHelper = document.createElement('a');
    navHelper.href = detailUrl;
    navHelper.style.position = 'absolute';
    navHelper.style.top = '0';
    navHelper.style.left = '0';
    navHelper.style.width = '100%';
    navHelper.style.height = '100%';
    navHelper.style.zIndex = '1'; // Below other card content but above card
    navHelper.style.opacity = '0';

    // Only add if the card has position relative or absolute
    if (getComputedStyle(card).position === 'static') {
      card.style.position = 'relative';
    }

    // Add the invisible anchor to the card
    card.appendChild(navHelper);

    // Mark card as fixed
    card.setAttribute('data-nav-fixed', 'true');
    card.style.cursor = 'pointer';
  });
}
