/**
 * Custom lazy loading test for water heater ID: wh-e3ae2f6
 * This test verifies the lazy tab loading functionality for a specific device
 * Following TDD principles to ensure expected behavior is correctly implemented
 */

// Create test utilities for monitoring API calls
const LazyLoadingTest = {
  apiCalls: {
    details: 0,
    operations: 0,
    history: 0,
    predictions: 0
  },

  // Track tab loading status
  tabsLoaded: {
    details: false,
    operations: false,
    history: false,
    predictions: false
  },

  // Original API functions to intercept
  originalFunctions: {},

  // Initialize the test
  init: function() {
    console.log('🧪 Initializing Lazy Loading Test for water heater ID: wh-e3ae2f6');

    // Check for correct device ID
    const deviceId = document.getElementById('device-id')?.value;
    if (deviceId !== 'wh-e3ae2f6') {
      console.warn(`⚠️ Expected device ID 'wh-e3ae2f6' but found '${deviceId}'. Test may not be valid.`);
    }

    // Store original API functions before intercepting
    this.saveOriginalFunctions();

    // Intercept API calls for each tab
    this.interceptTabLoading();

    // Add visual test indicator to page
    this.addTestIndicator();

    console.log('🧪 Test initialized. Navigate through tabs to test lazy loading.');
  },

  // Save original functions before intercepting
  saveOriginalFunctions: function() {
    // Save original load functions for each tab component
    if (window.WaterHeaterDetails && window.WaterHeaterDetails.loadDeviceDetails) {
      this.originalFunctions.details = window.WaterHeaterDetails.loadDeviceDetails;
    }

    if (window.WaterHeaterOperations && window.WaterHeaterOperations.loadOperationsData) {
      this.originalFunctions.operations = window.WaterHeaterOperations.loadOperationsData;
    }

    if (window.WaterHeaterHistory && window.WaterHeaterHistory.loadHistoryData) {
      this.originalFunctions.history = window.WaterHeaterHistory.loadHistoryData;
    }

    if (window.WaterHeaterPredictions && window.WaterHeaterPredictions.loadPredictions) {
      this.originalFunctions.predictions = window.WaterHeaterPredictions.loadPredictions;
    }
  },

  // Intercept tab loading functions to track API calls
  interceptTabLoading: function() {
    const self = this;

    // Intercept Details tab loading
    if (window.WaterHeaterDetails) {
      window.WaterHeaterDetails.loadDeviceDetails = function(...args) {
        console.log('🔍 Intercepted Details tab loading');
        self.apiCalls.details++;
        self.tabsLoaded.details = true;
        self.updateTestIndicator();
        return self.originalFunctions.details ? self.originalFunctions.details.apply(this, args) : null;
      };
    }

    // Intercept Operations tab loading
    if (window.WaterHeaterOperations) {
      window.WaterHeaterOperations.loadOperationsData = function(...args) {
        console.log('🔍 Intercepted Operations tab loading');
        self.apiCalls.operations++;
        self.tabsLoaded.operations = true;
        self.updateTestIndicator();
        return self.originalFunctions.operations ? self.originalFunctions.operations.apply(this, args) : null;
      };
    }

    // Intercept History tab loading
    if (window.WaterHeaterHistory) {
      window.WaterHeaterHistory.loadHistoryData = function(...args) {
        console.log('🔍 Intercepted History tab loading');
        self.apiCalls.history++;
        self.tabsLoaded.history = true;
        self.updateTestIndicator();
        return self.originalFunctions.history ? self.originalFunctions.history.apply(this, args) : null;
      };
    }

    // Intercept Predictions tab loading
    if (window.WaterHeaterPredictions) {
      window.WaterHeaterPredictions.loadPredictions = function(...args) {
        console.log('🔍 Intercepted Predictions tab loading');
        self.apiCalls.predictions++;
        self.tabsLoaded.predictions = true;
        self.updateTestIndicator();
        return self.originalFunctions.predictions ? self.originalFunctions.predictions.apply(this, args) : null;
      };
    }
  },

  // Add visual test indicator to the page
  addTestIndicator: function() {
    const indicator = document.createElement('div');
    indicator.id = 'lazy-loading-test-indicator';
    indicator.style.position = 'fixed';
    indicator.style.top = '10px';
    indicator.style.right = '10px';
    indicator.style.padding = '10px';
    indicator.style.background = 'rgba(0, 0, 0, 0.8)';
    indicator.style.border = '1px solid #666';
    indicator.style.borderRadius = '5px';
    indicator.style.color = '#fff';
    indicator.style.fontSize = '12px';
    indicator.style.zIndex = '9999';
    indicator.style.maxWidth = '300px';
    indicator.innerHTML = `
      <div style="font-weight: bold; margin-bottom: 5px;">Lazy Loading Test: wh-e3ae2f6</div>
      <div>Details: <span id="test-details-status">❌ Not loaded</span></div>
      <div>Operations: <span id="test-operations-status">❌ Not loaded</span></div>
      <div>History: <span id="test-history-status">❌ Not loaded</span></div>
      <div>Predictions: <span id="test-predictions-status">❌ Not loaded</span></div>
      <div style="margin-top: 5px;">
        <div>API Calls:</div>
        <div>Details: <span id="test-details-calls">0</span></div>
        <div>Operations: <span id="test-operations-calls">0</span></div>
        <div>History: <span id="test-history-calls">0</span></div>
        <div>Predictions: <span id="test-predictions-calls">0</span></div>
      </div>
    `;
    document.body.appendChild(indicator);
  },

  // Update test indicator with current loading status
  updateTestIndicator: function() {
    // Update loaded status
    for (const tab in this.tabsLoaded) {
      const statusEl = document.getElementById(`test-${tab}-status`);
      if (statusEl) {
        statusEl.textContent = this.tabsLoaded[tab] ? '✅ Loaded' : '❌ Not loaded';
        statusEl.style.color = this.tabsLoaded[tab] ? '#4CAF50' : '#f44336';
      }
    }

    // Update API call counts
    for (const tab in this.apiCalls) {
      const callsEl = document.getElementById(`test-${tab}-calls`);
      if (callsEl) {
        callsEl.textContent = this.apiCalls[tab];
      }
    }

    // Log current state to console
    console.log('📊 Current Test Status:', {
      tabsLoaded: this.tabsLoaded,
      apiCalls: this.apiCalls
    });

    // Check if lazy loading is working correctly
    this.verifyLazyLoading();
  },

  // Verify if lazy loading is working correctly
  verifyLazyLoading: function() {
    const activeTab = document.querySelector('.tab-btn.active');
    if (!activeTab) return;

    const activeTabId = activeTab.id.replace('-tab-btn', '');

    // Check if only the active tab and previously activated tabs are loaded
    const loadedTabs = Object.entries(this.tabsLoaded).filter(([, loaded]) => loaded);
    const loadedTabNames = loadedTabs.map(([tab]) => tab);

    console.log(`🔍 Active tab: ${activeTabId}, Loaded tabs: ${loadedTabNames.join(', ')}`);

    if (this.tabsLoaded[activeTabId]) {
      console.log(`✅ Active tab '${activeTabId}' is correctly loaded`);
    } else {
      console.error(`❌ Active tab '${activeTabId}' is NOT loaded - lazy loading not working!`);
    }

    // Check for unnecessary loading of inactive tabs
    const unnecessaryLoads = [];
    for (const tab in this.tabsLoaded) {
      // Skip the active tab and details (which may be loaded by default)
      if (tab !== activeTabId && tab !== 'details' && this.tabsLoaded[tab]) {
        // Check if this tab was previously activated
        const wasActivated = document.getElementById(`${tab}-tab-btn`).classList.contains('visited');
        if (!wasActivated) {
          unnecessaryLoads.push(tab);
        }
      }
    }

    if (unnecessaryLoads.length > 0) {
      console.warn(`⚠️ Possible lazy loading issue: These tabs were loaded without being activated: ${unnecessaryLoads.join(', ')}`);
    }
  },

  // Reset the test
  reset: function() {
    // Reset counters
    for (const tab in this.apiCalls) {
      this.apiCalls[tab] = 0;
    }

    for (const tab in this.tabsLoaded) {
      this.tabsLoaded[tab] = false;
    }

    // Update indicator
    this.updateTestIndicator();

    // Restore original functions
    for (const tab in this.originalFunctions) {
      if (window[`WaterHeater${tab.charAt(0).toUpperCase() + tab.slice(1)}`]) {
        const funcName = tab === 'details' ? 'loadDeviceDetails' :
                          tab === 'operations' ? 'loadOperationsData' :
                          tab === 'history' ? 'loadHistoryData' : 'loadPredictions';

        window[`WaterHeater${tab.charAt(0).toUpperCase() + tab.slice(1)}`][funcName] =
          this.originalFunctions[tab];
      }
    }

    // Remove test indicator
    const indicator = document.getElementById('lazy-loading-test-indicator');
    if (indicator) {
      indicator.remove();
    }

    console.log('🧪 Test reset complete');
  }
};

// Mark tabs as visited when clicked
document.addEventListener('DOMContentLoaded', function() {
  const tabButtons = document.querySelectorAll('.tab-btn');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', function() {
      this.classList.add('visited');
    });
  });
});

// Auto-initialize the test when the script loads
window.addEventListener('load', function() {
  // Wait a moment for everything to initialize first
  setTimeout(() => {
    LazyLoadingTest.init();
  }, 1000);
});

// Expose test controls to console
window.LazyLoadingTest = LazyLoadingTest;

console.log('🧪 Lazy loading test script loaded. The test will auto-initialize or type LazyLoadingTest.init() to manually start.');
