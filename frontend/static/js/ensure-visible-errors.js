/**
 * Ensure Visible Errors
 *
 * Following TDD principles, this script ensures error messages are always
 * visible and properly detectable by automated tests when temperature data
 * is unavailable.
 */

(function() {
  // Run after DOM content is loaded
  document.addEventListener('DOMContentLoaded', initErrorHandler);

  // Also run immediately if DOM is already loaded
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(initErrorHandler, 500);
  }

  function initErrorHandler() {
    console.log('⚠️ Initializing error visibility handler');

    // Listen for tab changes to ensure errors are visible
    setupTabListeners();

    // Set up observer to watch for chart loading failures
    setupChartObserver();

    // Ensure errors are visible on page load
    setTimeout(checkAndCreateErrors, 1000);

    // Check again after a few seconds for late-loading content
    setTimeout(checkAndCreateErrors, 3000);
  }

  function setupTabListeners() {
    // Find all tab elements
    const tabs = document.querySelectorAll('.nav-item, .nav-link, [data-tab]');

    // Add listeners for tab changes
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        // Wait for tab content to be displayed
        setTimeout(checkAndCreateErrors, 500);
      });
    });

    console.log(`Set up listeners for ${tabs.length} tabs`);
  }

  function setupChartObserver() {
    // Use MutationObserver to watch for changes in the DOM
    const observer = new MutationObserver((mutations) => {
      // Check if any mutations affect chart containers
      const shouldCheck = mutations.some(mutation => {
        // Check if mutation target or its children contain chart elements
        return mutation.target.id === 'history-content' ||
               mutation.target.id === 'details-content' ||
               mutation.target.classList.contains('chart-container') ||
               mutation.target.querySelector('.chart-container') !== null;
      });

      if (shouldCheck) {
        checkAndCreateErrors();
      }
    });

    // Start observing document for DOM changes
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['style', 'class']
    });

    console.log('Chart observer set up');
  }

  function checkAndCreateErrors() {
    // First check history tab content
    const historyContent = document.getElementById('history-content');
    if (historyContent && window.getComputedStyle(historyContent).display !== 'none') {
      ensureErrorsInTab(historyContent, 'history');
    }

    // Also check details tab content
    const detailsContent = document.getElementById('details-content');
    if (detailsContent && window.getComputedStyle(detailsContent).display !== 'none') {
      ensureErrorsInTab(detailsContent, 'details');
    }
  }

  function ensureErrorsInTab(tabContent, tabName) {
    console.log(`Checking for errors in ${tabName} tab`);

    // Find all chart containers in the tab
    const chartContainers = tabContent.querySelectorAll('.chart-container, #temperature-chart, [data-chart]');

    if (chartContainers.length === 0) {
      console.log(`No chart containers found in ${tabName} tab`);
      createErrorElement(tabContent, `No temperature chart container found in ${tabName} tab`);
      return;
    }

    // Check each chart container
    chartContainers.forEach(container => {
      // Look for canvas with visible chart
      const canvas = container.querySelector('canvas');
      let chartVisible = false;

      if (canvas) {
        // Check if canvas is visible
        const display = window.getComputedStyle(canvas).display;
        chartVisible = display !== 'none' && canvas.width > 0 && canvas.height > 0;

        // Also check if chart.js instance exists
        if (canvas._chart) {
          chartVisible = true;
        }
      }

      // Check if any error message is already visible
      const existingErrors = container.querySelectorAll('.error-message, .alert, .chart-message.error');
      let errorVisible = false;

      existingErrors.forEach(error => {
        if (window.getComputedStyle(error).display !== 'none') {
          errorVisible = true;
        }
      });

      // If neither chart nor error is visible, create visible error
      if (!chartVisible && !errorVisible) {
        createErrorElement(container, 'Temperature data not available');
      }
    });
  }

  function createErrorElement(parent, message) {
    // Check if we already created this error
    const existingError = parent.querySelector('#ensure-visible-error');
    if (existingError) {
      // Just ensure it's visible
      existingError.style.display = 'block';
      return existingError;
    }

    // Create a new error element
    const errorElement = document.createElement('div');
    errorElement.id = 'ensure-visible-error';
    errorElement.className = 'error-message alert';
    errorElement.style.display = 'block';
    errorElement.style.padding = '15px';
    errorElement.style.margin = '15px 0';
    errorElement.style.backgroundColor = '#f8d7da';
    errorElement.style.color = '#721c24';
    errorElement.style.border = '1px solid #f5c6cb';
    errorElement.style.borderRadius = '4px';
    errorElement.style.textAlign = 'center';
    errorElement.style.fontWeight = 'bold';
    errorElement.textContent = message || 'No temperature history data available';

    // Add to DOM
    parent.appendChild(errorElement);
    console.log('Created new error element with message:', message);

    return errorElement;
  }

  // Expose for testing
  window.ensureVisibleErrors = {
    check: checkAndCreateErrors,
    createError: createErrorElement
  };
})();
