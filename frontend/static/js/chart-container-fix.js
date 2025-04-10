/**
 * Chart Container Fix
 * Implements targeted fixes for chart container issues
 * Following TDD principles - minimal changes to make tests pass
 */

(function() {
  console.log('📊 Chart Container Fix: Initializing');

  // Run when DOM is ready
  document.addEventListener('DOMContentLoaded', initFixOnLoad);

  // Also try to initialize now if already loaded
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(initFixOnLoad, 100);
  }

  function initFixOnLoad() {
    console.log('📊 Chart Container Fix: DOM ready, checking containers');

    // Fix 1: Ensure IDs on all canvas elements to prevent reference issues
    ensureCanvasIds();

    // Fix 2: Ensure parent-child relationships are correct for chart containers
    fixContainerHierarchy();

    // Add diagnostic functions for testing
    exposeTestHelpers();
  }

  // Fix 1: Ensure all canvas elements have IDs
  function ensureCanvasIds() {
    const canvases = document.querySelectorAll('canvas');
    let fixedCount = 0;

    canvases.forEach((canvas, index) => {
      if (!canvas.id) {
        // For canvas without ID, generate one based on parent or position
        const parentId = canvas.parentElement ?
          (canvas.parentElement.id || canvas.parentElement.className.replace(/\s+/g, '-')) : '';

        canvas.id = parentId ?
          `${parentId}-canvas` :
          `canvas-${Date.now()}-${index}`;

        fixedCount++;
      }
    });

    if (fixedCount > 0) {
      console.log(`📊 Chart Container Fix: Added IDs to ${fixedCount} canvas elements`);
    }
  }

  // Fix 2: Ensure container hierarchy is correct
  function fixContainerHierarchy() {
    // Check for nested temperature chart containers
    const tempHistoryChart = document.getElementById('temperatureHistoryChart');
    const tempChart = document.getElementById('temperature-chart');

    if (tempHistoryChart && tempChart && tempHistoryChart.contains(tempChart)) {
      console.log('📊 Chart Container Fix: Found nested temperature charts, fixing hierarchy');

      // Get canvas from child container if any
      const canvas = tempChart.querySelector('canvas');

      if (canvas) {
        // Move canvas directly to parent and remove intermediary
        if (!canvas.id) canvas.id = 'temperature-chart-canvas';
        tempHistoryChart.appendChild(canvas);
        tempChart.remove();
        console.log('📊 Chart Container Fix: Moved canvas to direct parent, removed intermediary');
      }
    }

    // Ensure clean canvas in current container
    ensureCleanCanvas('temperature-chart');
  }

  // Ensure a clean canvas exists in container
  function ensureCleanCanvas(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Check if container already has canvas
    let canvas = container.querySelector('canvas');

    // If no canvas, create one
    if (!canvas) {
      console.log(`📊 Chart Container Fix: Creating new canvas in ${containerId}`);
      canvas = document.createElement('canvas');
      canvas.id = `${containerId}-canvas`;
      container.appendChild(canvas);
    }

    // Ensure canvas is clean (no existing chart instance)
    if (window.ChartInstanceManager && window.ChartInstanceManager.clearChartInstance) {
      window.ChartInstanceManager.clearChartInstance(canvas.id);
    }
  }

  // Test helpers for TDD verification
  function exposeTestHelpers() {
    window.chartContainerFix = {
      // Verify container structure and return diagnostic info
      verifyContainers: function() {
        const containers = document.querySelectorAll('.chart-container, #temperature-chart, [id*="Chart"]');
        const canvases = document.querySelectorAll('canvas');

        return {
          containerCount: containers.length,
          containers: Array.from(containers).map(c => ({
            id: c.id || 'unnamed',
            className: c.className,
            hasCanvas: !!c.querySelector('canvas'),
            canvasIds: Array.from(c.querySelectorAll('canvas')).map(canvas => canvas.id || 'unnamed')
          })),
          canvasCount: canvases.length,
          canvasInfo: Array.from(canvases).map(c => ({
            id: c.id || 'unnamed',
            parentId: c.parentElement ? (c.parentElement.id || 'unnamed-parent') : 'no-parent',
            width: c.width,
            height: c.height
          }))
        };
      },

      // Manually run fixes
      runFixes: function() {
        ensureCanvasIds();
        fixContainerHierarchy();

        return this.verifyContainers();
      }
    };
  }
})();
