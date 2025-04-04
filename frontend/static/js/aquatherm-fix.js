/**
 * AquaTherm TDD-Based Fix Implementation
 * This script addresses failing tests for the AquaTherm UI:
 * 1. Card click navigation not working - validated by click navigation tests
 * 2. Display consistency issues - validated by element styling consistency tests
 *
 * Following TDD principles: tests first → minimal implementation → validation → refactor
 */

(function() {
  console.log('🧪 AquaTherm TDD Fix Implementation Loaded');

  // Run the fix when DOM is loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyFixes);
  } else {
    applyFixes();
  }

  // Use a MutationObserver instead of setInterval to avoid constant reloading
  const observer = new MutationObserver(function(mutations) {
    // Only apply fixes when DOM changes are detected
    let shouldApplyFixes = false;

    mutations.forEach(mutation => {
      // Check if any of the added nodes are cards or contain cards
      if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
        mutation.addedNodes.forEach(node => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            // Check if it's a card or might contain cards
            if (node.classList?.contains('heater-card') ||
                node.querySelector?.('.heater-card')) {
              shouldApplyFixes = true;
            }
          }
        });
      }
    });

    if (shouldApplyFixes) {
      console.log('🔄 DOM changes detected - applying AquaTherm fixes');
      applyFixes();
    }
  });

  // Start observing the document body for changes
  observer.observe(document.body, { childList: true, subtree: true });

  /**
   * Apply all fixes to the current page
   */
  function applyFixes() {
    // Limit console logging to avoid overwhelming the console
    console.log('🛠️ Applying AquaTherm fixes...');

    // Fix card click navigation
    fixCardNavigation();

    // Fix display consistency
    fixDisplayConsistency();
  }

  /**
   * Fix card click navigation for all heater cards
   */
  function fixCardNavigation() {
    // Get all heater cards on the page
    const cards = document.querySelectorAll('.heater-card');
    console.log(`Found ${cards.length} heater cards to check/fix`);

    cards.forEach(card => {
      // Skip cards already fixed
      if (card.hasAttribute('data-fixed-navigation')) {
        return;
      }

      // Get the heater ID
      const heaterId = card.getAttribute('data-id');
      if (!heaterId) {
        return; // Skip cards without an ID
      }

      // First, remove any existing click handlers by cloning the card
      const newCard = card.cloneNode(true);
      if (card.parentNode) {
        card.parentNode.replaceChild(newCard, card);
      }

      // Add explicit click handler that directly navigates
      newCard.addEventListener('click', function(event) {
        // Don't navigate if clicking buttons or links
        if (event.target.tagName === 'BUTTON' ||
            event.target.tagName === 'A' ||
            event.target.closest('button') ||
            event.target.closest('a')) {
          return;
        }

        // Direct navigation with logging
        console.log(`🔀 Navigating to heater detail: ${heaterId}`);
        window.location.href = '/water-heaters/' + heaterId;
      });

      // Mark as fixed
      newCard.setAttribute('data-fixed-navigation', 'true');

      // Ensure card has pointer cursor
      newCard.style.cursor = 'pointer';
    });
  }

  /**
   * Fix display consistency issues
   */
  function fixDisplayConsistency() {
    // Add emergency CSS fixes directly to head
    injectEmergencyCSS();

    // Fix mode classes to ensure consistency
    fixModeClasses();

    // Ensure all cards have proper badges
    fixHeaterBadges();
  }

  /**
   * Fix class names for mode elements
   */
  function fixModeClasses() {
    // Get all mode elements
    const modeElements = document.querySelectorAll('.mode, [class*="mode-"]');

    modeElements.forEach(element => {
      // Add 'mode' class if missing
      if (!element.classList.contains('mode')) {
        element.classList.add('mode');
      }

      // Fix uppercase mode classes
      Array.from(element.classList).forEach(cls => {
        if (cls.startsWith('mode-') && cls !== cls.toLowerCase()) {
          // Remove uppercase class
          element.classList.remove(cls);
          // Add lowercase version
          element.classList.add(cls.toLowerCase());
        }
      });
    });
  }

  /**
   * Fix heater type badges
   */
  function fixHeaterBadges() {
    const aquathermCards = document.querySelectorAll('.heater-card.aquatherm-heater');

    aquathermCards.forEach(card => {
      // Skip cards already fixed
      if (card.hasAttribute('data-fixed-badges')) {
        return;
      }

      // Ensure AquaTherm badge exists
      let aquathermBadge = card.querySelector('.aquatherm-badge');
      if (!aquathermBadge) {
        aquathermBadge = document.createElement('div');
        aquathermBadge.className = 'aquatherm-badge';
        aquathermBadge.textContent = 'AquaTherm';
        card.appendChild(aquathermBadge);
      }

      // Determine heater type
      let heaterType = '';
      if (card.classList.contains('aquatherm-hybrid-heater')) {
        heaterType = 'HYBRID';
      } else if (card.classList.contains('aquatherm-tankless-heater')) {
        heaterType = 'TANKLESS';
      } else {
        // Default to TANK if no other type found
        heaterType = 'TANK';
      }

      // Ensure heater type badge exists
      let typeBadge = card.querySelector('.heater-type-badge');
      if (!typeBadge) {
        typeBadge = document.createElement('div');
        typeBadge.className = 'heater-type-badge';

        // Add type-specific class
        if (heaterType === 'HYBRID') {
          typeBadge.classList.add('hybrid-type');
        } else if (heaterType === 'TANKLESS') {
          typeBadge.classList.add('tankless-type');
        } else {
          typeBadge.classList.add('tank-type');
        }

        typeBadge.textContent = heaterType;
        card.appendChild(typeBadge);
      }

      // Mark as fixed
      card.setAttribute('data-fixed-badges', 'true');
    });
  }

  /**
   * Inject emergency CSS to fix styling issues
   */
  function injectEmergencyCSS() {
    // Skip if already injected
    if (document.getElementById('aquatherm-emergency-css')) {
      return;
    }

    // Add external CSS file link if not already present
    if (!document.querySelector('link[href="/static/css/aquatherm-fixes.css"]')) {
      const cssLink = document.createElement('link');
      cssLink.rel = 'stylesheet';
      cssLink.href = '/static/css/aquatherm-fixes.css';
      document.head.appendChild(cssLink);
    }

    // Also inject critical styles directly to ensure they take effect immediately
    const styleElement = document.createElement('style');
    styleElement.id = 'aquatherm-emergency-css';

    styleElement.textContent = `
      /* Card and badge fixes */
      .heater-card {
        cursor: pointer !important;
        position: relative !important;
      }

      .heater-card.aquatherm-heater {
        border-left: 3px solid #00a0b0 !important;
      }

      /* Badge styling */
      .aquatherm-badge, .heater-type-badge {
        position: absolute !important;
        font-size: 11px !important;
        font-weight: bold !important;
        padding: 3px 8px !important;
        border-radius: 4px !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
        z-index: 10 !important;
      }

      .aquatherm-badge {
        top: 10px !important;
        right: 10px !important;
        background-color: #00a0b0 !important;
        color: white !important;
      }

      .heater-type-badge {
        top: 10px !important;
        left: 10px !important;
        color: white !important;
      }

      .heater-type-badge.tank-type {
        background-color: #417505 !important;
      }

      .heater-type-badge.hybrid-type {
        background-color: #9b5de5 !important;
      }

      .heater-type-badge.tankless-type {
        background-color: #0075c4 !important;
      }

      /* Mode styling */
      .mode {
        padding: 4px 8px !important;
        border-radius: 4px !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
      }

      /* Force class case-insensitivity by duplicating rules */
      .mode-eco, .mode-ECO {
        background-color: rgba(6, 214, 160, 0.2) !important;
        color: var(--mode-eco, #06d6a0) !important;
      }

      .mode-boost, .mode-BOOST {
        background-color: rgba(255, 158, 0, 0.2) !important;
        color: var(--mode-boost, #ff9e00) !important;
      }

      .mode-off, .mode-OFF {
        background-color: rgba(151, 151, 151, 0.2) !important;
        color: var(--mode-off, #979797) !important;
      }

      .mode-electric, .mode-ELECTRIC {
        background-color: rgba(131, 56, 236, 0.2) !important;
        color: #8338ec !important;
      }

      .mode-heat_pump, .mode-HEAT_PUMP, .mode-heat\\ pump, .mode-HEAT\\ PUMP {
        background-color: rgba(58, 134, 255, 0.2) !important;
        color: #3a86ff !important;
      }

      /* Card detail fixes */
      .heater-details {
        width: 100% !important;
        display: flex !important;
        justify-content: space-between !important;
        margin-top: 10px !important;
        font-weight: 500 !important;
      }

      /* Gauge fixes */
      .gauge-container {
        position: relative !important;
        width: 150px !important;
        height: 150px !important;
        margin: 0 auto !important;
      }

      /* Add debug indicator */
      #aquatherm-fix-indicator {
        position: fixed;
        bottom: 10px;
        right: 10px;
        background: rgba(0, 160, 176, 0.9);
        color: white;
        padding: 8px 12px;
        font-size: 12px;
        border-radius: 4px;
        z-index: 9999;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        font-family: monospace;
      }
    `;

    document.head.appendChild(styleElement);

    // Add a small indicator that the fix is active
    const indicator = document.createElement('div');
    indicator.id = 'aquatherm-fix-indicator';
    indicator.textContent = '🛠️ AquaTherm Fix Active';
    document.body.appendChild(indicator);

    // Auto-hide the indicator after 5 seconds
    setTimeout(() => {
      indicator.style.opacity = '0';
      indicator.style.transition = 'opacity 0.5s ease';
      setTimeout(() => indicator.remove(), 500);
    }, 5000);
  }
})();
