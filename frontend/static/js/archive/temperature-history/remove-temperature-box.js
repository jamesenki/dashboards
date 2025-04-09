/**
 * THERMINATOR: THE ULTIMATE TEMPERATURE HISTORY BOX DESTROYER
 *
 * This is the NUCLEAR approach to removing any trace of the Temperature History box.
 * It uses every technique possible to detect and eliminate the offending elements.
 */

// IIFE to keep variables scoped and run immediately
(function() {
  console.log('🔥🔥🔥 THERMINATOR: MISSION DESTROY TEMPERATURE HISTORY BOX 🔥🔥🔥');

  /**
   * The Therminator - our ultimate box destroyer function
   * This aggressively hunts down and eliminates any trace of temperature history elements
   */
  function THERMINATOR() {
    console.log('🔪 THERMINATOR: EXECUTION PHASE INITIATED');

    // 1. REMOVE BY ID - Direct and efficient targeting
    const TARGET_IDS = [
      'temperature-chart',
      'history',
      'temperatureHistoryChart',
      'temperatureHistory',
      'temp-history',
      'temperature_history',
      'temperature-history',
      'tempHistory',
      'temperature-container'
    ];

    TARGET_IDS.forEach(id => {
      const target = document.getElementById(id);
      if (target) {
        console.log(`⚡ ELIMINATING TARGET ID: ${id}`);
        target.innerHTML = ''; // Clear contents first
        target.remove();        // Then remove from DOM
      }
    });

    // 2. REMOVE BY CLASS/SELECTOR - Wider targeting net
    const TARGET_SELECTORS = [
      // Chart related
      '.temperature-chart',
      '.chart-container',
      '.chart-wrapper',
      '.chartjs-render-monitor',
      'canvas',  // All canvas elements (likely used for charts)

      // History related
      '.temperature-history',
      '.temp-history',
      '#history',
      '.tab-panel#history',
      '.history-panel',
      '.history-tab',
      '.temperature-history-container',

      // Tab related
      'button[data-tab="history"]',
      '.tab-btn[data-tab="history"]',
      '[data-tab="history"]',

      // Advanced attribute-based targeting
      '[id*="temperature"][id*="chart"]',
      '[id*="temperature"][id*="history"]',
      '[class*="temperature"][class*="chart"]',
      '[class*="temperature"][class*="history"]'
    ];

    TARGET_SELECTORS.forEach(selector => {
      try {
        document.querySelectorAll(selector).forEach(elem => {
          console.log(`⚡ ELIMINATING SELECTOR: ${selector}`);
          elem.innerHTML = ''; // Clear contents first
          elem.remove();        // Then remove from DOM
        });
      } catch (e) {
        // Continue to next selector if one fails
      }
    });

    // 3. TEXT CONTENT SEARCH - Find anything with 'Temperature History' text
    const TEXT_TARGETS = ['Temperature History', 'temperature history', 'Temp History', 'Temperature Chart'];

    document.querySelectorAll('*').forEach(element => {
      if (element.childNodes.length < 20) { // Only check elements with reasonable number of children
        const text = element.innerText || element.textContent || '';
        if (TEXT_TARGETS.some(target => text.includes(target))) {
          console.log(`⚡ ELIMINATING TEXT MATCH: "${text.substring(0, 30)}..."`);
          element.innerHTML = ''; // Clear contents first
          element.remove();        // Then remove from DOM
        }
      }
    });

    // 4. TAB AND CHART ELIMINATION SYSTEM
    // Check for tab navigation system and remove history tab
    const tabNavs = document.querySelectorAll('.tab-nav, .tabs, .tab-container, nav');
    tabNavs.forEach(nav => {
      nav.querySelectorAll('[data-tab="history"], .history-tab, li:contains("History"), button:contains("History")').forEach(tab => {
        console.log('⚡ ELIMINATING HISTORY TAB');
        tab.remove();
      });
    });

    // 5. MAKE OTHER TABS ACTIVE
    // Make maintenance tab active if it exists
    const maintenanceTab = document.querySelector('[data-tab="maintenance"], .tab-btn[data-tab="maintenance"]');
    const maintenancePanel = document.getElementById('maintenance');

    if (maintenanceTab) {
      console.log('🔄 MAKING MAINTENANCE TAB ACTIVE');
      // Remove active class from all tabs
      document.querySelectorAll('.tab-btn, [data-tab]').forEach(tab => {
        tab.classList.remove('active');
      });
      // Add active class to maintenance tab
      maintenanceTab.classList.add('active');
    }

    if (maintenancePanel) {
      console.log('🔄 MAKING MAINTENANCE PANEL ACTIVE');
      // Remove active class from all panels
      document.querySelectorAll('.tab-panel, .tab-content > div').forEach(panel => {
        panel.classList.remove('active');
      });
      // Add active class to maintenance panel
      maintenancePanel.classList.add('active');
    }

    // 6. FUNCTION OVERRIDE SYSTEM - Neutralize any functions that might restore the temperature history
    console.log('⚡ NEUTRALIZING CHART FUNCTIONS');

    // Handle window objects safely
    window.ShadowDocumentHandler = window.ShadowDocumentHandler || {};

    // If ShadowDocumentHandler exists, override its prototype
    if (typeof ShadowDocumentHandler === 'function') {
      ShadowDocumentHandler.prototype.initializeCharts = function() { return null; };
      ShadowDocumentHandler.prototype.renderTemperatureChart = function() { return null; };
      ShadowDocumentHandler.prototype.updateChart = function() { return null; };
      ShadowDocumentHandler.prototype.destroyChart = function() { return null; };
    }

    // Also try to override any DeviceShadowApi functions
    window.DeviceShadowApi = window.DeviceShadowApi || {};
    if (typeof DeviceShadowApi === 'function') {
      DeviceShadowApi.prototype.getTemperatureHistory = function() {
        return Promise.resolve([]);
      };
    }

    // 7. STYLE INJECTION - Add CSS to hide anything that might slip through
    const styleTag = document.createElement('style');
    styleTag.textContent = `
      #temperature-chart, #history, .temperature-chart, .temperature-history,
      [id*="temperature"][id*="chart"], [id*="temperature"][id*="history"],
      .tab-btn[data-tab="history"], [data-tab="history"], .tab-panel#history,
      .chart-container, .chart-wrapper, .temperature-history-container,
      div:has(> h3:contains("Temperature History")), h3:contains("Temperature History") {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        position: absolute !important;
        top: -9999px !important;
        left: -9999px !important;
        height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
        pointer-events: none !important;
      }
    `;
    document.head.appendChild(styleTag);

    console.log('✅ THERMINATOR EXECUTION COMPLETE');
  }

  // EXECUTION STRATEGY:
  // 1. Run immediately for fastest possible removal
  THERMINATOR();

  // 2. Run when DOM is ready for more complete targeting
  document.addEventListener('DOMContentLoaded', function() {
    console.log('🔄 DOM LOADED - RUNNING THERMINATOR');
    THERMINATOR();
    // Run multiple times to catch any dynamic content
    setTimeout(THERMINATOR, 100);
    setTimeout(THERMINATOR, 500);
    setTimeout(THERMINATOR, 1000);
  });

  // 3. Run when all resources have loaded
  window.addEventListener('load', function() {
    console.log('🔄 PAGE FULLY LOADED - RUNNING THERMINATOR');
    THERMINATOR();
    // Set up recurring execution to catch dynamically added elements
    setInterval(THERMINATOR, 1000);

    // 4. Set up a mutation observer to detect and destroy newly added elements
    const observer = new MutationObserver(function(mutations) {
      console.log('🔄 DOM MUTATION DETECTED - RUNNING THERMINATOR');
      THERMINATOR();
    });

    // Watch for any changes to the entire document body
    observer.observe(document.body, {
      childList: true,       // Watch for element additions/removals
      subtree: true,         // Watch all descendants, not just children
      attributes: true,      // Watch for attribute changes
      characterData: true    // Watch for text content changes
    });
  });
})();
