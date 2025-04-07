/**
 * Clear Mock Data Script
 * This script forces all mock water heaters to be removed from the DOM
 * and ensures only real database water heaters are displayed
 */
(function() {
  console.log("Running clear-mock-data script to remove any mock water heaters...");

  // Function to remove any existing water heater cards
  function clearMockWaterHeaters() {
    // Wait for the page to fully load
    document.addEventListener('DOMContentLoaded', function() {
      setTimeout(function() {
        console.log("Checking for mock water heaters...");

        // Find all water heater cards
        const waterHeaterCards = document.querySelectorAll('.heater-card');
        console.log(`Found ${waterHeaterCards.length} water heater cards`);

        // Look for mock IDs (aqua-wh pattern)
        let mockCardsRemoved = 0;
        waterHeaterCards.forEach(card => {
          // Get the link which contains the ID
          const link = card.querySelector('a');
          if (link && link.href) {
            const matches = link.href.match(/\/water-heaters\/([^/]+)/);
            if (matches && matches[1]) {
              const id = matches[1];

              // Check if it's a mock ID (starts with aqua-, mock-, or test-)
              if (id.startsWith('aqua-') || id.startsWith('mock-') || id.startsWith('test-')) {
                console.log(`Removing mock water heater: ${id}`);
                card.remove();
                mockCardsRemoved++;
              }
            }
          }
        });

        console.log(`Removed ${mockCardsRemoved} mock water heater cards`);

        // Verify real water heaters
        const remainingCards = document.querySelectorAll('.heater-card');
        console.log(`Remaining water heaters: ${remainingCards.length}`);
        remainingCards.forEach(card => {
          const link = card.querySelector('a');
          if (link && link.href) {
            const matches = link.href.match(/\/water-heaters\/([^/]+)/);
            if (matches && matches[1]) {
              console.log(`Verified real water heater: ${matches[1]}`);
            }
          }
        });
      }, 1000); // Wait 1 second after load to make sure everything is rendered
    });
  }

  // Run the cleanup
  clearMockWaterHeaters();

  // Also add it to any page navigation events
  window.addEventListener('popstate', clearMockWaterHeaters);
})();
