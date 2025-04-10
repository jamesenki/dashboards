/**
 * Temperature Chart Fix Verification Script
 *
 * This script follows TDD principles to:
 * 1. RED: Validate that the temperature chart container issue is present
 * 2. GREEN: Verify that our fix resolves the container finding issue
 * 3. REFACTOR: Ensure the solution is robust and handles edge cases
 */

// Self-executing function to avoid polluting global scope
(function() {
  console.log('🧪 Starting Temperature Chart Fix verification');

  // Track if we've verified the fix
  let fixVerified = false;

  // Store reference to original console methods for diagnostics
  const originalConsoleError = console.error;
  const originalConsoleWarn = console.warn;
  const originalConsoleLog = console.log;

  // Capture console errors to detect the specific chart container issue
  const errors = [];
  console.error = function() {
    errors.push(Array.from(arguments).join(' '));
    originalConsoleError.apply(console, arguments);
  };

  // Function to verify if our chart container fix works
  function verifyTemperatureChartFix() {
    if (fixVerified) return;

    console.log('🔍 Verifying temperature chart container fix...');

    // Get all chart containers in the document
    const chartContainers = document.querySelectorAll('.chart-container, .temperature-chart-container, [id*="temperatureChart"], [class*="temperature-chart"]');
    console.log(`Found ${chartContainers.length} chart container candidates`);

    // Check each container for a canvas element
    let containersWithCanvas = 0;
    let visibleCanvases = 0;

    chartContainers.forEach((container, index) => {
      const canvases = container.querySelectorAll('canvas');
      if (canvases.length > 0) {
        containersWithCanvas++;

        // Check if canvas is visible
        canvases.forEach(canvas => {
          const style = window.getComputedStyle(canvas);
          const isVisible = style.display !== 'none' && style.visibility !== 'hidden' && canvas.width > 0 && canvas.height > 0;
          if (isVisible) {
            visibleCanvases++;
          }

          console.log(`Canvas #${index+1}: visible=${isVisible}, width=${canvas.width}, height=${canvas.height}, display=${style.display}, visibility=${style.visibility}`);
        });
      }
    });

    // Check for specific error in logs
    const containerNotFoundError = errors.some(err =>
      err.includes('No temperature history container found') ||
      err.includes('temperature chart container')
    );

    console.log(`Containers with canvas: ${containersWithCanvas}`);
    console.log(`Visible canvases: ${visibleCanvases}`);

    if (containerNotFoundError && visibleCanvases === 0) {
      console.log('❌ Temperature chart container issue detected - fix needed');
    } else if (visibleCanvases > 0) {
      console.log('✅ Temperature chart container fix verified - chart is rendering properly');
      fixVerified = true;
    } else {
      console.log('⚠️ Inconclusive test - no visible canvases, but no specific errors detected');
    }
  }

  // Wait for the chart to initialize before testing
  function waitForChartAndVerify() {
    // Check if we're on a page with chart elements
    const chartElements = document.querySelectorAll('[id*="chart"], [class*="chart"]');
    if (chartElements.length === 0) {
      console.log('No chart elements found on this page, verification not applicable');
      return;
    }

    // Find the temperature chart specifically
    const historyTab = document.querySelector('a[href="#history"], a[data-target="#history"]');
    if (historyTab) {
      console.log('Found History tab, clicking to show temperature chart...');
      historyTab.click();
    }

    // Initial verification
    setTimeout(verifyTemperatureChartFix, 2000);

    // Check again after ChartJS might have initialized
    setTimeout(verifyTemperatureChartFix, 5000);
  }

  // Run test when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', waitForChartAndVerify);
  } else {
    // DOM already loaded, run test now
    waitForChartAndVerify();
  }

  // Periodically verify in case page content changes
  setInterval(verifyTemperatureChartFix, 10000);
})();
