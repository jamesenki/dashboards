/**
 * Optimized Tab Manager
 *
 * Creates a clean, efficient tab management system that:
 * - Properly handles tab lifecycle (activation, deactivation)
 * - Reduces unnecessary DOM operations during tab switching
 * - Ensures proper loading/unloading of content
 * - Provides event hooks for other components
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
    allTabsInitialized: []
  };

  // Initialize when DOM is ready
  document.addEventListener('DOMContentLoaded', initialize);
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(initialize, 100);
  }

  function initialize() {
    console.log('📊 Tab Manager: Initializing');

    // Find and register all tabs
    registerAllTabs();

    // Set up tab click handlers
    setupTabClickHandlers();

    // Activate the current tab based on URL hash or default
    activateTabFromUrlHash();

    // Mark as initialized
    tabState.initialized = true;

    // Trigger initialization complete event
    triggerEvent('allTabsInitialized', tabState);

    // Log summary
    console.log(`📊 Tab Manager: Initialized with ${Object.keys(tabState.tabs).length} tabs`);
  }

  function registerAllTabs() {
    // Find tab navigation elements
    const tabLinks = document.querySelectorAll('.nav-link, [data-tab]');

    // Register each tab
    tabLinks.forEach(tabLink => {
      // Get tab ID from various possible attributes
      const tabId = tabLink.dataset.tab ||
                    tabLink.getAttribute('href')?.replace('#', '') ||
                    tabLink.dataset.target?.replace('#', '');

      if (!tabId) return;

      // Find corresponding content element
      const contentElement = document.getElementById(tabId) ||
                            document.getElementById(`${tabId}-content`);

      if (!contentElement) return;

      // Register tab in state
      tabState.tabs[tabId] = {
        id: tabId,
        linkElement: tabLink,
        contentElement: contentElement,
        isActive: false,
        loadTime: 0,
        initialized: false
      };

      console.log(`📊 Tab registered: ${tabId}`);
    });
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

          // Update URL hash without triggering scroll
          updateUrlHash(tab.id);
        });
      }
    });
  }

  function activateTabFromUrlHash() {
    // Get current hash from URL (remove # symbol)
    const currentHash = window.location.hash.replace('#', '');

    // If hash exists and corresponds to a tab, activate it
    if (currentHash && tabState.tabs[currentHash]) {
      activateTab(currentHash);
    } else {
      // Otherwise, check for a default tab
      const defaultTab = document.querySelector('.nav-link.active, [data-tab].active');
      if (defaultTab) {
        const defaultTabId = defaultTab.dataset.tab ||
                            defaultTab.getAttribute('href')?.replace('#', '') ||
                            defaultTab.dataset.target?.replace('#', '');

        if (defaultTabId && tabState.tabs[defaultTabId]) {
          activateTab(defaultTabId);
        }
      } else {
        // If no default, activate the first tab
        const firstTabId = Object.keys(tabState.tabs)[0];
        if (firstTabId) {
          activateTab(firstTabId);
        }
      }
    }
  }

  function activateTab(tabId) {
    // If tab is already active, do nothing
    if (tabState.activeTabId === tabId) {
      console.log(`📊 Tab ${tabId} is already active`);
      return;
    }

    console.log(`📊 Activating tab: ${tabId}`);

    // Deactivate the currently active tab
    if (tabState.activeTabId && tabState.tabs[tabState.activeTabId]) {
      deactivateTab(tabState.activeTabId);
    }

    // Get the tab to activate
    const tab = tabState.tabs[tabId];
    if (!tab) {
      console.error(`Tab not found: ${tabId}`);
      return;
    }

    // Activate tab link (add active class)
    if (tab.linkElement) {
      tab.linkElement.classList.add('active');

      // Also activate parent if it's a list item
      const parentLi = tab.linkElement.closest('li');
      if (parentLi) {
        parentLi.classList.add('active');
      }
    }

    // Show tab content
    if (tab.contentElement) {
      tab.contentElement.style.display = 'block';
      tab.contentElement.classList.add('active');
    }

    // Update tab state
    tab.isActive = true;
    tab.loadTime = Date.now();
    if (!tab.initialized) {
      tab.initialized = true;
    }

    // Update active tab ID
    tabState.activeTabId = tabId;
    tabState.tabLoadTimes[tabId] = Date.now();

    // Trigger tab activated event
    triggerEvent('tabActivated', tab);
  }

  function deactivateTab(tabId) {
    console.log(`📊 Deactivating tab: ${tabId}`);

    // Get the tab to deactivate
    const tab = tabState.tabs[tabId];
    if (!tab) return;

    // Deactivate tab link (remove active class)
    if (tab.linkElement) {
      tab.linkElement.classList.remove('active');

      // Also deactivate parent if it's a list item
      const parentLi = tab.linkElement.closest('li');
      if (parentLi) {
        parentLi.classList.remove('active');
      }
    }

    // Hide tab content
    if (tab.contentElement) {
      tab.contentElement.style.display = 'none';
      tab.contentElement.classList.remove('active');
    }

    // Update tab state
    tab.isActive = false;

    // Trigger tab deactivated event
    triggerEvent('tabDeactivated', tab);
  }

  function updateUrlHash(tabId) {
    // Update URL hash without scrolling
    if (history.pushState) {
      history.pushState(null, null, `#${tabId}`);
    } else {
      // Fallback for older browsers
      const scrollPosition = window.scrollY;
      window.location.hash = tabId;
      window.scrollTo(0, scrollPosition);
    }
  }

  // Event management
  function addEventListener(eventName, callback) {
    if (eventListeners[eventName]) {
      eventListeners[eventName].push(callback);
      return true;
    }
    return false;
  }

  function removeEventListener(eventName, callback) {
    if (eventListeners[eventName]) {
      const index = eventListeners[eventName].indexOf(callback);
      if (index !== -1) {
        eventListeners[eventName].splice(index, 1);
        return true;
      }
    }
    return false;
  }

  function triggerEvent(eventName, data) {
    if (eventListeners[eventName]) {
      eventListeners[eventName].forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in ${eventName} event handler:`, error);
        }
      });
    }
  }

  // Utility functions
  function getActiveTab() {
    return tabState.tabs[tabState.activeTabId] || null;
  }

  function getAllTabs() {
    return { ...tabState.tabs };
  }

  function getTabLoadTime(tabId) {
    return tabState.tabLoadTimes[tabId] || 0;
  }

  // Expose public API
  window.OptimizedTabManager = {
    activateTab: activateTab,
    getActiveTab: getActiveTab,
    getAllTabs: getAllTabs,
    getTabLoadTime: getTabLoadTime,
    addEventListener: addEventListener,
    removeEventListener: removeEventListener
  };
})();
