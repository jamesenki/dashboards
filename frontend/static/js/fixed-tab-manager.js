/**
 * Fixed Tab Manager
 *
 * A robust tab management system that follows TDD principles to solve tab navigation issues
 * in the water heater dashboard. This implementation aligns with the actual HTML structure
 * and ensures proper component lifecycle management.
 *
 * Features:
 * - Proper tab visibility management through CSS classes
 * - Component registration for tab content
 * - Event propagation for tab changes
 * - Tab activation/deactivation with data reloading
 */

(function() {
  'use strict';

  // Tab state registry
  const tabState = {
    activeTabId: null,
    tabs: {},
    initialized: false,
    tabLoadTimes: {}
  };

  // Event listeners
  const eventListeners = {
    tabActivated: [],
    tabDeactivated: [],
    allTabsInitialized: [],
    dataRefresh: []
  };

  // Initialize when DOM is ready
  document.addEventListener('DOMContentLoaded', initialize);
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(initialize, 100);
  }

  function initialize() {
    // console.log removed for performance

    // Find and register all tabs - supporting multiple tab structures in the HTML
    const tabButtons = document.querySelectorAll('.tab-btn, .nav-link, [data-tab]');
    if (tabButtons.length === 0) {
      // console.warn removed for performance
      return;
    }

    // console.log removed for performance

    // Register each tab
    tabButtons.forEach(tabButton => {
      // Get tab ID from various possible attributes
      const tabId = tabButton.dataset.tab ||
                   tabButton.getAttribute('href')?.replace('#', '') ||
                   tabButton.dataset.target?.replace('#', '');

      if (!tabId) {
        // Console logging removed for performance
        return;
      }

      // Find corresponding content element - supporting multiple content ID formats
      let contentElement = null;

      // Try various selector patterns that might exist in the HTML
      const possibleSelectors = [
        `#${tabId}`,                    // Direct ID match
        `#${tabId}-content`,            // ID with -content suffix
        `#${tabId}-tab`,                // ID with -tab suffix
        `.${tabId}-content`,            // Class with -content suffix
        `[data-content="${tabId}"]`,    // Data attribute
        `.tab-content[data-tab="${tabId}"]` // Tab content with matching data-tab
      ];

      for (const selector of possibleSelectors) {
        const element = document.querySelector(selector);
        if (element) {
          contentElement = element;
          // Console logging removed for performance
          break;
        }
      }

      if (!contentElement) {
        // Last resort - look for div inside a container that matches the naming pattern
        const containers = document.querySelectorAll('.tab-content, .tab-contents, .content-container');
        for (const container of containers) {
          const element = container.querySelector(`#${tabId}, .${tabId}, [data-tab="${tabId}"]`);
          if (element) {
            contentElement = element;
            // Console logging removed for performance
            break;
          }
        }
      }

      if (!contentElement) {
        // Console logging removed for performance
        return;
      }

      // Register tab in state
      tabState.tabs[tabId] = {
        id: tabId,
        linkElement: tabButton,
        contentElement: contentElement,
        isActive: tabButton.classList.contains('active'),
        loadTime: 0,
        initialized: false
      };

      // Console logging removed for performance
    });

    // Early exit if no valid tabs were found
    if (Object.keys(tabState.tabs).length === 0) {
      // Console logging removed for performance
      return;
    }

    // Set up tab click handlers
    setupTabClickHandlers();

    // Set initial active tab
    let initialTab = null;

    // First check if URL has a hash
    const hashValue = window.location.hash.replace('#', '');
    if (hashValue && tabState.tabs[hashValue]) {
      initialTab = hashValue;
      // Console logging removed for performance
    }

    // Then check if a tab is already marked as active in HTML
    if (!initialTab) {
      const activeTabButton = document.querySelector('.tab-btn.active, .nav-link.active, [data-tab].active');
      if (activeTabButton) {
        const tabId = activeTabButton.dataset.tab ||
                     activeTabButton.getAttribute('href')?.replace('#', '') ||
                     activeTabButton.dataset.target?.replace('#', '');
        if (tabId && tabState.tabs[tabId]) {
          initialTab = tabId;
          // Console logging removed for performance
        }
      }
    }

    // Default to first tab if nothing else is selected
    if (!initialTab && Object.keys(tabState.tabs).length > 0) {
      initialTab = Object.keys(tabState.tabs)[0];
      // Console logging removed for performance
    }

    // Activate initial tab
    if (initialTab) {
      activateTab(initialTab);
    }

    // Mark as initialized
    tabState.initialized = true;

    // Trigger initialization complete event
    triggerEvent('allTabsInitialized', tabState);

    // Log summary
    // Console logging removed for performance
  }

  function setupTabClickHandlers() {
    // Add click handlers to all tab links
    Object.values(tabState.tabs).forEach(tab => {
      if (tab.linkElement) {
        tab.linkElement.addEventListener('click', (event) => {
          // Prevent default for anchor links
          if (tab.linkElement.tagName === 'A') {
            event.preventDefault();
          }

          // Activate the clicked tab
          activateTab(tab.id);
        });

        // Console logging removed for performance
      }
    });
  }

  function activateTab(tabId) {
    // Check if tab exists
    if (!tabState.tabs[tabId]) {
      // Console logging removed for performance
      return false;
    }

    // Skip if already active
    if (tabState.activeTabId === tabId) {
      // Console logging removed for performance
      return true;
    }

    // Console logging removed for performance

    // Get tab data
    const tab = tabState.tabs[tabId];

    // Deactivate current tab
    if (tabState.activeTabId && tabState.tabs[tabState.activeTabId]) {
      deactivateTab(tabState.activeTabId);
    }

    // Update state
    tabState.activeTabId = tabId;
    tab.isActive = true;

    // Record load time
    const startTime = performance.now();

    // Update button state
    tab.linkElement.classList.add('active');

    // Make content visible - attempt multiple visibility methods for compatibility
    if (tab.contentElement) {
      // First try display style
      tab.contentElement.style.display = 'block';

      // Also add active class for CSS-managed visibility
      tab.contentElement.classList.add('active');

      // Remove hidden class if present
      tab.contentElement.classList.remove('hidden');

      // Remove inline visibility: hidden if set
      if (tab.contentElement.style.visibility === 'hidden') {
        tab.contentElement.style.visibility = 'visible';
      }

      // Specific for Bootstrap tabs
      tab.contentElement.classList.add('show');
    }

    // Update URL hash for bookmarkability
    updateUrlHash(tabId);

    // Trigger event
    triggerEvent('tabActivated', {
      tabId: tabId,
      tab: tab
    });

    // Record load time
    tabState.tabLoadTimes[tabId] = performance.now() - startTime;

    // Console logging removed for performance

    return true;
  }

  function deactivateTab(tabId) {
    // Check if tab exists
    if (!tabState.tabs[tabId]) {
      // Console logging removed for performance
      return false;
    }

    // Console logging removed for performance

    // Get tab data
    const tab = tabState.tabs[tabId];

    // Update state
    tab.isActive = false;

    // Update button state
    tab.linkElement.classList.remove('active');

    // Hide content - attempt multiple visibility methods for compatibility
    if (tab.contentElement) {
      // First try display style
      tab.contentElement.style.display = 'none';

      // Also remove active class for CSS-managed visibility
      tab.contentElement.classList.remove('active');

      // Add hidden class
      tab.contentElement.classList.add('hidden');

      // Specific for Bootstrap tabs
      tab.contentElement.classList.remove('show');
    }

    // Trigger event
    triggerEvent('tabDeactivated', {
      tabId: tabId,
      tab: tab
    });

    return true;
  }

  function updateUrlHash(tabId) {
    if (history.pushState) {
      history.pushState(null, null, `#${tabId}`);
    } else {
      // Fallback for older browsers
      window.location.hash = tabId;
    }
  }

  // Event management
  function addEventListener(eventName, callback) {
    if (!eventListeners[eventName]) {
      eventListeners[eventName] = [];
    }
    eventListeners[eventName].push(callback);
    return callback; // Return for easier removal
  }

  function removeEventListener(eventName, callback) {
    if (!eventListeners[eventName]) {
      return false;
    }
    const index = eventListeners[eventName].indexOf(callback);
    if (index > -1) {
      eventListeners[eventName].splice(index, 1);
      return true;
    }
    return false;
  }

  function triggerEvent(eventName, data) {
    if (!eventListeners[eventName]) {
      return;
    }
    eventListeners[eventName].forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        // Console logging removed for performance
      }
    });
  }

  // Data refresh helper
  function requestDataRefresh(tabId) {
    triggerEvent('dataRefresh', {
      tabId: tabId || tabState.activeTabId
    });
  }

  // External component registration
  function registerComponent(componentName, callbacks) {
    // Console logging removed for performance

    if (!callbacks || typeof callbacks !== 'object') {
      // Console logging removed for performance
      return;
    }

    // Register event listeners
    if (callbacks.onTabActivated) {
      addEventListener('tabActivated', callbacks.onTabActivated);
    }

    if (callbacks.onTabDeactivated) {
      addEventListener('tabDeactivated', callbacks.onTabDeactivated);
    }

    if (callbacks.onDataRefresh) {
      addEventListener('dataRefresh', callbacks.onDataRefresh);
    }

    // If already initialized, immediately call initialization callback
    if (tabState.initialized && callbacks.onInitialized) {
      callbacks.onInitialized(tabState);
    } else if (callbacks.onInitialized) {
      addEventListener('allTabsInitialized', callbacks.onInitialized);
    }
  }

  // Utility functions
  function getActiveTab() {
    return tabState.activeTabId ? tabState.tabs[tabState.activeTabId] : null;
  }

  function getAllTabs() {
    return Object.values(tabState.tabs);
  }

  function getTabLoadTime(tabId) {
    return tabState.tabLoadTimes[tabId] || 0;
  }

  function isInitialized() {
    return tabState.initialized;
  }

  // Diagnostics for debugging tab issues
  function diagnoseTabIssues() {
    // Diagnostics functions disabled for performance

    // Diagnostics logging disabled for performance

    // Check for common issues
    const tabButtons = document.querySelectorAll('.tab-btn, .nav-link, [data-tab]');
    // Diagnostics logging disabled for performance

    if (tabButtons.length === 0) {
      // Diagnostics logging disabled for performance
    }

    // Check content elements
    let contentElementsMissing = 0;
    for (const [tabId, tab] of Object.entries(tabState.tabs)) {
      if (!tab.contentElement) {
        contentElementsMissing++;
        // Diagnostics logging disabled for performance
      }
    }

    if (contentElementsMissing > 0) {
      // Diagnostics logging disabled for performance
    }

    // Diagnostics logging disabled for performance

    return {
      activeTabId: tabState.activeTabId,
      initialized: tabState.initialized,
      tabCount: Object.keys(tabState.tabs).length,
      tabButtonCount: tabButtons.length,
      contentElementsMissing,
      issues: contentElementsMissing > 0 || tabButtons.length === 0
    };
  }

  // Expose public API
  window.TabManager = {
    activateTab,
    getActiveTab,
    getAllTabs,
    getTabLoadTime,
    addEventListener,
    removeEventListener,
    registerComponent,
    requestDataRefresh,
    isInitialized,
    diagnoseTabIssues
  };

  // Create diagnostic tools for console testing
  window.diagnoseTabs = diagnoseTabIssues;

  // Console logging removed for performance
})();
