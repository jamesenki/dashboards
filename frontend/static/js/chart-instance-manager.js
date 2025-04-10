/**
 * Chart Instance Manager for IoTSphere
 *
 * This script resolves canvas conflicts by:
 * 1. Providing centralized chart instance tracking and management
 * 2. Properly destroying chart instances before reuse
 * 3. Handling tab navigation to prevent duplicate chart creation
 *
 * Following TDD principles:
 * - Resolves the "Canvas is already in use" error
 * - Ensures clean chart instance lifecycle
 * - Manages chart instances across tab navigation
 */

(function() {
  console.log('📊 Chart Instance Manager: Initializing...');

  // Maintain a registry of all chart instances
  const chartRegistry = new Map();

  // Store the original Chart constructor
  let originalChartConstructor = null;

  // Keep track of the tab navigation
  let currentTab = null;

  // Initialize
  initializeManager();

  function initializeManager() {
    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
      console.log('Chart.js not available yet, waiting...');
      setTimeout(initializeManager, 300);
      return;
    }

    // Store the original Chart constructor
    originalChartConstructor = Chart;

    // Patch the Chart constructor
    patchChartConstructor();

    // Set up tab change listener
    observeTabChanges();

    // Add global access
    window.ChartInstanceManager = {
      getChart: getChartInstance,
      destroyChart: destroyChartInstance,
      listCharts: listChartInstances,
      reset: resetAllCharts,
      clearChartInstance: clearChartInstance,
      ensureDetailsChart: ensureDetailsPageChartContainer, // Expose details chart helper
      verifyManager: verifyChartInstanceManager // Expose verification for tests
    };

    // Ensure chart manager initializes early in load process
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function() {
        console.log('📊 Chart Instance Manager: DOMContentLoaded initialization');
        setTimeout(ensureDetailsPageChartContainer, 500);
      });
    } else {
      // Document already loaded, initialize now
      console.log('📊 Chart Instance Manager: Immediate initialization');
      setTimeout(ensureDetailsPageChartContainer, 100);
    }

    console.log('📊 Chart Instance Manager: Initialized successfully');
  }

  function patchChartConstructor() {
    // Create a patched constructor that manages instances
    window.Chart = function(canvas, config) {
      // If canvas is a string, find the element
      const canvasElement = typeof canvas === 'string'
        ? document.getElementById(canvas)
        : canvas;

      if (!canvasElement) {
        console.error('Chart initialization failed: Canvas element not found');
        return null;
      }

      // Get canvas identifier (id or generated id)
      const canvasId = canvasElement.id || `auto-canvas-${Math.random().toString(36).substring(2, 11)}`;
      if (!canvasElement.id) {
        canvasElement.id = canvasId;
      }

      // Check if there's already a chart using this canvas
      const existingChart = chartRegistry.get(canvasId);
      if (existingChart) {
        console.log(`📊 Chart Instance Manager: Destroying existing chart for canvas ${canvasId}`);
        try {
          existingChart.destroy();
        } catch (error) {
          console.warn(`Failed to destroy existing chart: ${error.message}`);
        }
        chartRegistry.delete(canvasId);
      }

      // Check if the canvas is ready for a new chart
      if (canvasElement._chartInstance) {
        console.log(`📊 Chart Instance Manager: Clearing _chartInstance reference on canvas ${canvasId}`);
        delete canvasElement._chartInstance;
      }

      // Create a new chart instance
      let chartInstance;
      try {
        chartInstance = new originalChartConstructor(canvasElement, config);

        // Store in registry
        chartRegistry.set(canvasId, chartInstance);

        // Also store a reference on the canvas (safely)
        Object.defineProperty(canvasElement, '_chartManager', {
          value: { chartId: chartInstance.id, registryId: canvasId },
          writable: true,
          configurable: true
        });

        console.log(`📊 Chart Instance Manager: Created new chart for canvas ${canvasId}`);
        return chartInstance;
      } catch (error) {
        console.error(`Failed to create chart on canvas ${canvasId}: ${error.message}`);

        // Try to recover by clearing any remaining references
        clearChartInstance(canvasId);

        // Rethrow to maintain original behavior
        throw error;
      }
    };

    // Copy all properties from original Chart to patched version
    for (const prop in originalChartConstructor) {
      if (originalChartConstructor.hasOwnProperty(prop)) {
        window.Chart[prop] = originalChartConstructor[prop];
      }
    }

    // Also patch the destroy method to ensure proper cleanup
    const originalPrototype = originalChartConstructor.prototype;
    const originalDestroy = originalPrototype.destroy;

    originalPrototype.destroy = function() {
      const canvas = this.canvas;
      const canvasId = canvas ? canvas.id : null;

      // Call original destroy
      const result = originalDestroy.apply(this, arguments);

      // Remove from registry if it exists
      if (canvasId && chartRegistry.has(canvasId)) {
        chartRegistry.delete(canvasId);
        console.log(`📊 Chart Instance Manager: Removed chart for canvas ${canvasId} from registry after destroy`);
      }

      // Clean up canvas reference
      if (canvas && canvas._chartManager) {
        delete canvas._chartManager;
      }

      return result;
    };

    console.log('📊 Chart Instance Manager: Chart constructor patched successfully');
  }

  function observeTabChanges() {
    // Wait for tab manager to be available
    if (typeof window.tabManager === 'undefined') {
      // If tab manager is not available after a reasonable time, set up our own observers
      setTimeout(function() {
        if (typeof window.tabManager === 'undefined') {
          console.log('📊 Chart Instance Manager: Tab manager not available, setting up direct observers');
          setupDirectTabObservers();
        } else {
          observeTabChanges();
        }
      }, 1000);
      return;
    }

    // Add tab change listener
    window.tabManager.addListener('tabchanged', function(event) {
      const newTabId = event.newTabId;
      const prevTabId = event.prevTabId;

      console.log(`📊 Chart Instance Manager: Tab changed from ${prevTabId} to ${newTabId}`);
      currentTab = newTabId;

      // Handle special case for history tab
      if (newTabId === 'history') {
        // Give time for history tab content to load
        setTimeout(function() {
          console.log('📊 Chart Instance Manager: Checking temperature chart in history tab');

          // Find temperature chart in history tab
          const historyContainer = document.getElementById('history-content');
          if (historyContainer) {
            const chartContainers = historyContainer.querySelectorAll('#temperature-chart, .temperature-history-chart, [data-chart="temperature-history"]');
            for (const container of chartContainers) {
              const canvas = container.querySelector('canvas');
              if (canvas && canvas.id) {
                // Clear any existing chart instance
                clearChartInstance(canvas.id);
              }
            }
          }
        }, 300);
      }

      // Handle details tab - ensure temperature chart is properly managed
      if (newTabId === 'details') {
        setTimeout(function() {
          console.log('📊 Chart Instance Manager: Handling details tab temperature chart');
          ensureDetailsPageChartContainer();
        }, 300);
      }
    });

    console.log('📊 Chart Instance Manager: Tab change observer set up');
  }

  // Set up direct observers for tab buttons if tab manager is not available
  function setupDirectTabObservers() {
    // Find all tab buttons
    const tabButtons = document.querySelectorAll('[id$="-tab-btn"]');
    if (tabButtons.length === 0) {
      // Try again later if buttons are not found
      setTimeout(setupDirectTabObservers, 500);
      return;
    }

    // Add click handlers to all tab buttons
    tabButtons.forEach(button => {
      button.addEventListener('click', function(event) {
        // Extract tab id from button id (remove '-tab-btn' suffix)
        const buttonId = button.id;
        const tabId = buttonId.replace(/-tab-btn$/, '');

        // Update current tab
        const prevTab = currentTab;
        currentTab = tabId;

        console.log(`📊 Chart Instance Manager: Tab changed via click from ${prevTab} to ${currentTab}`);

        // Handle specific tabs
        if (tabId === 'history') {
          setTimeout(function() {
            // Clear any existing chart instances in history tab
            const historyContainer = document.getElementById('history-content');
            if (historyContainer) {
              const canvases = historyContainer.querySelectorAll('canvas');
              canvases.forEach(canvas => {
                if (canvas.id) {
                  clearChartInstance(canvas.id);
                }
              });
            }
          }, 300);
        }

        if (tabId === 'details') {
          setTimeout(function() {
            ensureDetailsPageChartContainer();
          }, 300);
        }
      });
    });

    console.log(`📊 Chart Instance Manager: Set up direct observers for ${tabButtons.length} tab buttons`);
  }

  // Ensure the details page chart container exists and is properly set up
  function ensureDetailsPageChartContainer() {
    console.log('📊 Chart Instance Manager: Ensuring details page chart container');

    // Look for temperature chart container in details tab
    const detailsContent = document.getElementById('details-content');
    if (!detailsContent) {
      console.warn('Details content container not found');
      return;
    }

    // Find or create the temperature chart container
    let chartContainer = detailsContent.querySelector('#temperature-chart');

    if (!chartContainer) {
      // Try alternative selectors
      chartContainer = detailsContent.querySelector('.temperature-chart-container, [data-chart="temperature"]');
    }

    if (!chartContainer) {
      console.log('Creating temperature chart container for details page');

      // Find a suitable parent element
      const parentElement = detailsContent.querySelector('.temperature-section') ||
                          detailsContent.querySelector('.chart-section') ||
                          detailsContent;

      // Create container and canvas
      chartContainer = document.createElement('div');
      chartContainer.id = 'temperature-chart';
      chartContainer.className = 'chart-container temperature-chart-container';

      const canvas = document.createElement('canvas');
      canvas.id = 'temperature-chart-canvas';
      canvas.width = 400;
      canvas.height = 300;

      chartContainer.appendChild(canvas);
      parentElement.appendChild(chartContainer);

      console.log('📊 Chart Instance Manager: Created new temperature chart container and canvas');
    } else {
      console.log('📊 Chart Instance Manager: Found existing temperature chart container');

      // Ensure any existing chart is properly destroyed
      const canvas = chartContainer.querySelector('canvas');
      if (canvas && canvas.id) {
        clearChartInstance(canvas.id);
      }
    }
  }

  // Utility functions for chart management

  function getChartInstance(canvasId) {
    return chartRegistry.get(canvasId);
  }

  function destroyChartInstance(canvasId) {
    const chartInstance = chartRegistry.get(canvasId);
    if (chartInstance) {
      try {
        chartInstance.destroy();
        chartRegistry.delete(canvasId);
        console.log(`📊 Chart Instance Manager: Destroyed chart for canvas ${canvasId}`);
        return true;
      } catch (error) {
        console.error(`Failed to destroy chart on canvas ${canvasId}: ${error.message}`);
      }
    }
    return false;
  }

  function clearChartInstance(canvasId) {
    // Force clear all chart references for a canvas to resolve conflicts
    chartRegistry.delete(canvasId);

    const canvas = document.getElementById(canvasId);
    if (canvas) {
      // Clear all chart-related properties
      if (canvas._chart) delete canvas._chart;
      if (canvas._chartInstance) delete canvas._chartInstance;
      if (canvas._chartManager) delete canvas._chartManager;

      // Also clear any Chart.js internal references
      if (window.Chart && window.Chart.instances) {
        for (const [instanceId, instance] of Object.entries(window.Chart.instances)) {
          if (instance.canvas === canvas) {
            delete window.Chart.instances[instanceId];
          }
        }
      }
    }

    console.log(`📊 Chart Instance Manager: Cleared all chart references for canvas ${canvasId}`);
    return true;
  }

  function listChartInstances() {
    const instances = [];
    for (const [canvasId, chart] of chartRegistry.entries()) {
      instances.push({
        canvasId,
        chartId: chart.id,
        type: chart.config.type
      });
    }
    return instances;
  }

  function resetAllCharts() {
    const canvasIds = Array.from(chartRegistry.keys());
    for (const canvasId of canvasIds) {
      destroyChartInstance(canvasId);
    }
    chartRegistry.clear();
    console.log('📊 Chart Instance Manager: Reset all chart instances');
  }

  // Expose a verification method for test scenarios
  window.verifyChartInstanceManager = function() {
    return {
      patchedConstructor: window.Chart !== originalChartConstructor,
      registrySize: chartRegistry.size,
      instances: listChartInstances(),
      currentTab: currentTab
    };
  };
})();
