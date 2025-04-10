/**
 * Data Management Tests
 *
 * This test suite validates the implementation of proper data loading strategies:
 * 1. Tab-specific selective loading (only load data needed for current tab)
 * 2. Time-range specific loading (only load data for selected time period)
 * 3. Data preprocessing verification
 *
 * These tests follow TDD principles - they define expected behavior first,
 * then we'll implement code to match these expectations.
 */

// Test suite for data management
const DataManagementTest = {
  // Track API calls by endpoint and parameters
  apiCalls: {
    currentData: [],
    historyData: [],
    preprocessedData: [],
    archivedData: []
  },

  // Original API methods we'll intercept
  originalMethods: {},

  /**
   * Initialize the test
   */
  init: function() {
    console.log('🧪 Initializing Data Management Test Suite');

    // Store original API methods
    this.interceptApiMethods();

    // Add visual test indicator
    this.addTestIndicator();

    // Set up event listeners for tabs and time period selectors
    this.setupEventListeners();

    console.log('✅ Data Management Test Suite initialized');
  },

  /**
   * Intercept API methods to track calls
   */
  interceptApiMethods: function() {
    const self = this;

    // Intercept API client methods if available
    if (window.ApiClient && window.ApiClient.prototype) {
      // Save original methods
      this.originalMethods.getCurrentData = window.ApiClient.prototype.getCurrentTemperature;
      this.originalMethods.getHistoryData = window.ApiClient.prototype.getTemperatureHistory;
      this.originalMethods.getPreprocessedData = window.ApiClient.prototype.getPreprocessedTemperatureHistory;
      this.originalMethods.getArchivedData = window.ApiClient.prototype.getArchivedTemperatureHistory;

      // Intercept current data calls
      window.ApiClient.prototype.getCurrentTemperature = function(deviceId) {
        self.apiCalls.currentData.push({
          deviceId,
          timestamp: new Date().toISOString()
        });
        console.log(`🔍 Intercepted getCurrentTemperature call for device ${deviceId}`);
        return self.originalMethods.getCurrentData.apply(this, arguments);
      };

      // Intercept history data calls
      window.ApiClient.prototype.getTemperatureHistory = function(deviceId, days) {
        self.apiCalls.historyData.push({
          deviceId,
          days,
          timestamp: new Date().toISOString()
        });
        console.log(`🔍 Intercepted getTemperatureHistory call for device ${deviceId}, days: ${days || 'default'}`);
        return self.originalMethods.getHistoryData.apply(this, arguments);
      };

      // Intercept preprocessed data calls
      window.ApiClient.prototype.getPreprocessedTemperatureHistory = function(deviceId, days) {
        self.apiCalls.preprocessedData.push({
          deviceId,
          days,
          timestamp: new Date().toISOString()
        });
        console.log(`🔍 Intercepted getPreprocessedTemperatureHistory call for device ${deviceId}, days: ${days || 'default'}`);
        return self.originalMethods.getPreprocessedData.apply(this, arguments);
      };

      // Intercept archived data calls
      window.ApiClient.prototype.getArchivedTemperatureHistory = function(deviceId, startDate, endDate) {
        self.apiCalls.archivedData.push({
          deviceId,
          startDate,
          endDate,
          timestamp: new Date().toISOString()
        });
        console.log(`🔍 Intercepted getArchivedTemperatureHistory call for device ${deviceId}`);
        return self.originalMethods.getArchivedData.apply(this, arguments);
      };
    } else {
      console.error('❌ ApiClient not available for interception');
    }
  },

  /**
   * Set up event listeners for tabs and time period selectors
   */
  setupEventListeners: function() {
    // Track tab changes
    document.addEventListener('tabmanager:tabchanged', (event) => {
      const tabId = event.detail.newTabId;
      console.log(`🔄 Tab changed to: ${tabId}`);
      this.verifyTabSpecificLoading(tabId);
    });

    // Track day selectors on history tab
    const daySelectors = document.querySelectorAll('.day-selector');
    daySelectors.forEach(selector => {
      selector.addEventListener('click', (event) => {
        const days = parseInt(event.target.getAttribute('data-days'));
        console.log(`🔄 User selected ${days} days view`);
        this.verifyTimeRangeSpecificLoading(days);
      });
    });
  },

  /**
   * Verify that only data for the current tab is loaded
   */
  verifyTabSpecificLoading: function(tabId) {
    // Reset API call counters for new verification
    this.resetApiCallCounters();

    // Add a small delay to allow API calls to complete
    setTimeout(() => {
      // Log current state
      console.log('📊 API Call State after tab change:', {
        tabId,
        currentDataCalls: this.apiCalls.currentData.length,
        historyDataCalls: this.apiCalls.historyData.length,
        preprocessedDataCalls: this.apiCalls.preprocessedData.length,
        archivedDataCalls: this.apiCalls.archivedData.length
      });

      // Check tab-specific loading expectations
      if (tabId === 'details') {
        // Details tab should only load current data
        const result = this.apiCalls.currentData.length > 0 &&
                      this.apiCalls.historyData.length === 0;

        this.updateTestResult('tab-specific-loading', result,
          result ?
            `✅ Details tab correctly loaded only current data` :
            `❌ Details tab incorrectly loaded history data or failed to load current data`
        );
      }
      else if (tabId === 'history') {
        // History tab should load history data, not just current
        const result = this.apiCalls.historyData.length > 0;

        this.updateTestResult('tab-specific-loading', result,
          result ?
            `✅ History tab correctly loaded history data` :
            `❌ History tab failed to load history data`
        );

        // Also check time-range specific loading
        this.verifyTimeRangeSpecificLoading();
      }

      this.updateTestIndicator();
    }, 500);
  },

  /**
   * Verify that only data for the selected time period is loaded
   */
  verifyTimeRangeSpecificLoading: function(days) {
    // If days parameter wasn't provided, try to determine from active selector
    if (!days) {
      const activeSelector = document.querySelector('.day-selector.active');
      if (activeSelector) {
        days = parseInt(activeSelector.getAttribute('data-days'));
      } else {
        days = 7; // Default assumption
      }
    }

    // Reset API call counters for new verification
    this.resetApiCallCounters();

    // Add a small delay to allow API calls to complete
    setTimeout(() => {
      // Log current state
      console.log('📊 API Call State after time period change:', {
        days,
        historyDataCalls: this.apiCalls.historyData.length,
        historyDataParams: this.apiCalls.historyData
      });

      // Only proceed if we have history calls to analyze
      if (this.apiCalls.historyData.length === 0) {
        return;
      }

      // Check that history calls use correct time period
      const correctTimeRange = this.apiCalls.historyData.some(call =>
        call.days === days || (call.days === undefined && days === 7) // Handle default 7 days
      );

      this.updateTestResult('time-range-specific-loading', correctTimeRange,
        correctTimeRange ?
          `✅ Correctly loaded only ${days} days of data` :
          `❌ Failed to load correct time range (${days} days)`
      );

      this.updateTestIndicator();
    }, 500);
  },

  /**
   * Reset API call counters for a new test
   */
  resetApiCallCounters: function() {
    this.apiCalls.currentData = [];
    this.apiCalls.historyData = [];
    this.apiCalls.preprocessedData = [];
    this.apiCalls.archivedData = [];
  },

  /**
   * Update a specific test result
   */
  updateTestResult: function(testId, passed, message) {
    console.log(message);
    const resultElement = document.getElementById(`test-${testId}-result`);
    if (resultElement) {
      resultElement.textContent = passed ? 'Passed' : 'Failed';
      resultElement.style.color = passed ? '#4CAF50' : '#F44336';
    }

    const messageElement = document.getElementById(`test-${testId}-message`);
    if (messageElement) {
      messageElement.textContent = message;
    }
  },

  /**
   * Add visual test indicator to the page
   */
  addTestIndicator: function() {
    const indicator = document.createElement('div');
    indicator.id = 'data-management-test-indicator';
    indicator.style.position = 'fixed';
    indicator.style.bottom = '10px';
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
      <div style="font-weight: bold; margin-bottom: 5px;">Data Management Tests</div>
      <div>
        Tab-Specific Loading:
        <span id="test-tab-specific-loading-result">Not Tested</span>
      </div>
      <div id="test-tab-specific-loading-message" style="font-size: 10px; color: #aaa;">
        Not tested yet
      </div>
      <div>
        Time-Range Specific Loading:
        <span id="test-time-range-specific-loading-result">Not Tested</span>
      </div>
      <div id="test-time-range-specific-loading-message" style="font-size: 10px; color: #aaa;">
        Not tested yet
      </div>
      <div style="margin-top: 5px; font-size: 11px;">
        <div>API Calls:</div>
        <div>Current Data: <span id="test-current-data-calls">0</span></div>
        <div>History Data: <span id="test-history-data-calls">0</span></div>
        <div>Preprocessed: <span id="test-preprocessed-data-calls">0</span></div>
        <div>Archived: <span id="test-archived-data-calls">0</span></div>
      </div>
    `;
    document.body.appendChild(indicator);
  },

  /**
   * Update the test indicator with current state
   */
  updateTestIndicator: function() {
    document.getElementById('test-current-data-calls').textContent = this.apiCalls.currentData.length;
    document.getElementById('test-history-data-calls').textContent = this.apiCalls.historyData.length;
    document.getElementById('test-preprocessed-data-calls').textContent = this.apiCalls.preprocessedData.length;
    document.getElementById('test-archived-data-calls').textContent = this.apiCalls.archivedData.length;
  }
};

// Initialize the test when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  // Wait a bit for other scripts to initialize
  setTimeout(() => {
    DataManagementTest.init();
  }, 1000);
});
