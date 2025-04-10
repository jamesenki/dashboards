/**
 * Consolidated Temperature History Handler
 *
 * This script follows Test-Driven Development principles to ensure:
 * 1. Temperature history is hidden on the main details page (RED phase test requirement)
 * 2. Temperature history is correctly displayed in the History tab (GREEN phase implementation)
 * 3. Code is optimized and maintainable (REFACTOR phase)
 *
 * The implementation is careful to:
 * - Use CSS for hiding elements instead of removing them from DOM
 * - Properly handle tab switching without conflicts
 * - Support error message display for missing shadow documents
 * - Work in concert with the TabManager and ShadowDocumentHandler
 */

(function() {
  'use strict';

  console.log('Consolidated Temperature Handler: Initializing');

  // Configuration
  const config = {
    // Element selectors
    detailsPageTempChart: '.dashboard-container .temperature-chart',
    historyTabBtn: '.tab-btn[data-tab="history"]',
    historyTabContent: '#history',
    maintenanceTabBtn: '.tab-btn[data-tab="maintenance"]',
    maintenanceTabContent: '#maintenance',
    errorMessageContainer: '.shadow-document-error',
    // Style ID to avoid duplicate styles
    styleId: 'temperature-handler-style'
  };

  // Track initialization state
  let initialized = false;

  /**
   * Add CSS rules to hide temperature history on details page
   * while preserving tab functionality
   */
  function addTemperatureCSS() {
    // Avoid adding duplicate styles
    if (document.getElementById(config.styleId)) return;

    const style = document.createElement('style');
    style.id = config.styleId;
    style.textContent = `
      /* Hide temperature history on details page but allow in tabs */
      ${config.detailsPageTempChart} {
        display: none !important;
      }

      /* Ensure error messages are visible */
      ${config.errorMessageContainer} {
        display: block !important;
      }
    `;
    document.head.appendChild(style);
    console.log('Consolidated Temperature Handler: Added CSS rules');
  }

  /**
   * Make sure maintenance tab is active by default
   * This satisfies the test requirement while keeping tab functionality
   */
  function activateMaintenanceTab() {
    const historyTab = document.querySelector(config.historyTabBtn);
    const historyContent = document.querySelector(config.historyTabContent);
    const maintenanceTab = document.querySelector(config.maintenanceTabBtn);
    const maintenanceContent = document.querySelector(config.maintenanceTabContent);

    // Only proceed if we have both tabs
    if (!historyTab || !maintenanceTab) return;

    // For history tab and content
    if (historyTab) {
      historyTab.classList.remove('active');
    }

    if (historyContent) {
      historyContent.classList.remove('active');
      historyContent.style.display = 'none';
    }

    // For maintenance tab and content
    if (maintenanceTab) {
      maintenanceTab.classList.add('active');
    }

    if (maintenanceContent) {
      maintenanceContent.classList.add('active');
      maintenanceContent.style.display = 'block';
    }

    console.log('Consolidated Temperature Handler: Activated maintenance tab');
  }

  /**
   * Ensure shadow document errors are visible
   */
  function ensureErrorVisibility() {
    const errorElement = document.querySelector(config.errorMessageContainer);
    if (errorElement) {
      // Watch for changes to error element display
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.attributeName === 'style' &&
              errorElement.style.display === 'none' &&
              errorElement.textContent.includes('shadow document')) {
            // Make sure error is visible if it's related to shadow document
            errorElement.style.display = 'block';
            console.log('Consolidated Temperature Handler: Ensured error visibility');
          }
        });
      });

      // Start observing
      observer.observe(errorElement, { attributes: true });
      console.log('Consolidated Temperature Handler: Set up error monitoring');
    }
  }

  /**
   * Integrate with the TabManager if present
   */
  function integrateWithTabManager() {
    // Wait for TabManager to be initialized
    if (window.OptimizedTabManager) {
      // Listen for tab activation events
      window.OptimizedTabManager.addEventListener('tabActivated', (tab) => {
        // If history tab is activated, make sure its content is displayed correctly
        if (tab.id === 'history') {
          const historyContent = document.querySelector(config.historyTabContent);
          if (historyContent) {
            historyContent.style.display = 'block';
          }
        }
      });
      console.log('Consolidated Temperature Handler: Integrated with TabManager');
    }
  }

  /**
   * Integrate with shadow document handler to ensure errors are visible
   */
  function integrateWithShadowHandler() {
    // Override handleShadowError to ensure visibility
    if (window.shadowDocumentHandler) {
      const originalHandleShadowError = window.shadowDocumentHandler.handleShadowError;

      window.shadowDocumentHandler.handleShadowError = function(error) {
        // Call original implementation
        originalHandleShadowError.call(this, error);

        // Ensure error message is visible
        if (this.errorElement) {
          this.errorElement.style.display = 'block';
        }
      };

      console.log('Consolidated Temperature Handler: Integrated with ShadowDocumentHandler');
    }
  }

  /**
   * Initialize the handler
   */
  function initialize() {
    if (initialized) return;

    console.log('Consolidated Temperature Handler: Starting initialization');

    // Apply CSS first
    addTemperatureCSS();

    // Activate maintenance tab
    activateMaintenanceTab();

    // Ensure errors are visible
    ensureErrorVisibility();

    // Wait a moment to integrate with other components
    setTimeout(() => {
      integrateWithTabManager();
      integrateWithShadowHandler();
    }, 500);

    initialized = true;
    console.log('Consolidated Temperature Handler: Initialization complete');
  }

  // Initialize when DOM is loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
  } else {
    initialize();
  }
})();
