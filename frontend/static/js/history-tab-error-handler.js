/**
 * History Tab Error Handler
 *
 * Following TDD principles:
 * - Ensures either chart data or error message is visible
 * - Handles empty temperature history data states
 * - Properly shows period selection errors
 */

(function() {
  console.log('📊 History Tab Error Handler: Initializing');

  // Configuration
  const ERROR_CHECK_DELAY = 1000; // Time to wait before checking for errors
  const ERROR_DISPLAY_TIMEOUT = 10000; // Max time to wait for data before showing permanent error

  // Track state
  let isInitialized = false;
  let errorTimer = null;

  // Initialize on page load
  document.addEventListener('DOMContentLoaded', initErrorHandler);
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(initErrorHandler, 100);
  }

  function initErrorHandler() {
    if (isInitialized) return;
    isInitialized = true;

    console.log('📊 History Tab Error Handler: Setting up tab observers');

    // Monitor tab changes to ensure proper error handling in history tab
    observeTabChanges();

    // Set up period selectors to have error handling
    setupPeriodSelectorHandlers();
  }

  // Observe tab changes to handle history tab correctly
  function observeTabChanges() {
    // Find tab buttons
    const tabButtons = document.querySelectorAll('[id$="-tab-btn"]');

    // Listen for clicks on tab buttons
    tabButtons.forEach(button => {
      button.addEventListener('click', function(event) {
        const buttonId = button.id;
        const tabId = buttonId.replace('-tab-btn', '');

        console.log(`📊 History Tab Error Handler: Tab changed to ${tabId}`);

        if (tabId === 'history') {
          // We're in history tab, check for errors
          scheduleErrorCheck();
        } else {
          // Clear any pending error checks when leaving history tab
          if (errorTimer) {
            clearTimeout(errorTimer);
            errorTimer = null;
          }
        }
      });
    });
  }

  // Setup error handling for period selectors
  function setupPeriodSelectorHandlers() {
    // Find period selectors
    const periodSelectors = document.querySelectorAll('.period-selector, [data-days]');

    // Add error handling to period selectors
    periodSelectors.forEach(selector => {
      selector.addEventListener('click', function(event) {
        // Clear any existing error message when selecting a new period
        hideErrorMessages();

        // Schedule error check after selection
        scheduleErrorCheck();
      });
    });
  }

  // Schedule an error check with appropriate timing
  function scheduleErrorCheck() {
    // Clear any existing timer
    if (errorTimer) {
      clearTimeout(errorTimer);
    }

    // Schedule initial check
    errorTimer = setTimeout(checkForHistoryErrors, ERROR_CHECK_DELAY);

    // Also schedule a fallback check to ensure something is displayed
    setTimeout(() => {
      checkForHistoryErrors(true);
    }, ERROR_DISPLAY_TIMEOUT);
  }

  // Check for chart errors and display appropriate messages
  function checkForHistoryErrors(isFallback = false) {
    console.log('📊 Checking for history tab errors');

    // Only proceed if we're in the history tab
    const historyContent = document.getElementById('history-content');
    if (!historyContent || window.getComputedStyle(historyContent).display === 'none') {
      return;
    }

    // Find chart containers
    const chartContainers = historyContent.querySelectorAll('#temperature-chart, .chart-container, .temperature-history-chart');

    // Find canvases in those containers
    const canvases = [];
    chartContainers.forEach(container => {
      const containerCanvases = container.querySelectorAll('canvas');
      containerCanvases.forEach(canvas => canvases.push(canvas));
    });

    // Check for chart instances on these canvases
    let chartInstanceFound = false;
    let chartHasData = false;

    canvases.forEach(canvas => {
      // Try different ways to find chart instance
      const chartInstance = (
        (window.ChartInstanceManager && window.ChartInstanceManager.getChart && window.ChartInstanceManager.getChart(canvas.id)) ||
        (canvas._chart ? canvas._chart : null) ||
        window._temperatureChart
      );

      if (chartInstance) {
        chartInstanceFound = true;

        // Check if chart has data
        if (chartInstance.data &&
            chartInstance.data.datasets &&
            chartInstance.data.datasets.length > 0 &&
            chartInstance.data.datasets[0].data &&
            chartInstance.data.datasets[0].data.length > 0) {
          chartHasData = true;
        }
      }
    });

    // Find existing error messages
    const errorElements = historyContent.querySelectorAll('.error-message, .alert-warning, .alert-danger, .no-data-message, .chart-error');
    let visibleErrorExists = false;

    errorElements.forEach(element => {
      if (window.getComputedStyle(element).display !== 'none') {
        visibleErrorExists = true;
      }
    });

    console.log(`📊 History tab error check: Chart instance found: ${chartInstanceFound}, Chart has data: ${chartHasData}, Visible error exists: ${visibleErrorExists}`);

    // If we have a chart with data, we're good
    if (chartInstanceFound && chartHasData) {
      console.log('📊 Chart with data found, hiding any error messages');
      hideErrorMessages();
      return;
    }

    // If we have a visible error message, we're also good
    if (visibleErrorExists) {
      console.log('📊 Error message already visible');
      return;
    }

    // If chart instance not found or no data, show error
    if (!chartInstanceFound || !chartHasData || isFallback) {
      console.log('📊 No chart with data found, showing error message');
      showErrorMessage(historyContent, 'No temperature history data available');
    }
  }

  // Hide any visible error messages
  function hideErrorMessages() {
    const errorElements = document.querySelectorAll('.error-message, .alert-warning, .alert-danger, .no-data-message, .chart-error');

    errorElements.forEach(element => {
      element.style.display = 'none';
    });
  }

  // Create and show error message
  function showErrorMessage(container, message) {
    // Look for existing error element to reuse
    let errorElement = container.querySelector('.error-message, .chart-error, .no-data-message');

    // Create new error element if needed
    if (!errorElement) {
      errorElement = document.createElement('div');
      errorElement.className = 'error-message';
      errorElement.style.display = 'flex';
      errorElement.style.justifyContent = 'center';
      errorElement.style.alignItems = 'center';
      errorElement.style.padding = '20px';
      errorElement.style.margin = '20px 0';
      errorElement.style.backgroundColor = '#ffebee';
      errorElement.style.color = '#d32f2f';
      errorElement.style.borderRadius = '4px';
      errorElement.style.border = '1px solid #f5c6cb';

      // Insert after chart container if possible
      const chartContainer = container.querySelector('#temperature-chart, .chart-container');
      if (chartContainer) {
        chartContainer.parentNode.insertBefore(errorElement, chartContainer.nextSibling);
      } else {
        // Insert at the beginning of container
        container.insertBefore(errorElement, container.firstChild);
      }
    }

    // Set message and make visible
    errorElement.textContent = message;
    errorElement.style.display = 'flex';
  }

  // Add test verification functions
  window.historyTabErrorHandler = {
    runCheck: checkForHistoryErrors,
    showError: function(message) {
      const historyContent = document.getElementById('history-content');
      if (historyContent) {
        showErrorMessage(historyContent, message || 'No temperature history data available');
        return true;
      }
      return false;
    },
    hideErrors: hideErrorMessages,
    getStatus: function() {
      const historyContent = document.getElementById('history-content');
      if (!historyContent) return { active: false };

      const errors = Array.from(historyContent.querySelectorAll('.error-message, .alert-warning, .alert-danger, .no-data-message'))
        .filter(el => window.getComputedStyle(el).display !== 'none')
        .map(el => el.textContent.trim());

      return {
        active: window.getComputedStyle(historyContent).display !== 'none',
        errors: errors,
        hasVisibleError: errors.length > 0
      };
    }
  };
})();
