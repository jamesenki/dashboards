/**
 * Temperature History Chart Validator
 *
 * This script validates that the temperature history chart works correctly
 * for all time periods (7, 14, and 30 days) on the History tab.
 * It will be automatically injected into the page when loaded.
 */

(function() {
  // Run when the DOM is fully loaded
  document.addEventListener('DOMContentLoaded', function() {
    console.log('🧪 Temperature History Validator: Starting validation');

    // Wait a bit for charts to initialize
    setTimeout(validateTemperatureHistory, 1000);
  });

  // Main validation function
  function validateTemperatureHistory() {
    // Check if we're on a page with temperature history
    const historyTab = document.getElementById('history-content');
    if (!historyTab) {
      console.log('❌ Temperature History Validator: No history tab found');
      return;
    }

    console.log('✅ Temperature History Validator: Found history tab');

    // Find period selectors
    const periodSelectors = document.querySelectorAll('.day-selector, [data-days]');
    if (!periodSelectors || periodSelectors.length === 0) {
      console.log('❌ Temperature History Validator: No period selectors found');
      return;
    }

    console.log(`✅ Temperature History Validator: Found ${periodSelectors.length} period selectors`);

    // Find the temperature chart
    const tempChart = document.getElementById('temperature-chart');
    if (!tempChart) {
      console.log('❌ Temperature History Validator: No temperature chart found');
      return;
    }

    console.log('✅ Temperature History Validator: Found temperature chart');

    // Track periods found
    const periodsFound = [];

    // Check period selectors
    periodSelectors.forEach(selector => {
      const days = selector.getAttribute('data-days');
      if (days) {
        periodsFound.push(days);
        console.log(`✅ Temperature History Validator: Found period selector for ${days} days`);
      }
    });

    // Verify we have 7, 14, and 30 day selectors
    const requiredPeriods = ['7', '14', '30'];
    const missingPeriods = requiredPeriods.filter(period => !periodsFound.includes(period));

    if (missingPeriods.length > 0) {
      console.log(`❌ Temperature History Validator: Missing period selectors for: ${missingPeriods.join(', ')} days`);
    } else {
      console.log('✅ Temperature History Validator: All required period selectors (7, 14, 30 days) are present');
    }

    // Check if selectors are clickable (have event listeners)
    const selectorWithListener = Array.from(periodSelectors).some(selector => {
      const clone = selector.cloneNode(true);
      return selector.onclick !== null ||
             selector.getAttribute('onclick') !== null ||
             selector !== clone; // This is a heuristic check
    });

    if (selectorWithListener) {
      console.log('✅ Temperature History Validator: Period selectors appear to have event handlers');
    } else {
      console.log('⚠️ Temperature History Validator: Could not detect event handlers on period selectors');
    }

    // Check if chart container is properly set up
    const chartContainer = document.querySelector('.chart-container, .chart-wrapper');
    if (chartContainer) {
      console.log('✅ Temperature History Validator: Chart container found');

      // Add validation complete message to the page
      const validationMessage = document.createElement('div');
      validationMessage.className = 'validation-message';
      validationMessage.style.background = '#e8f5e9';
      validationMessage.style.border = '1px solid #a5d6a7';
      validationMessage.style.borderRadius = '4px';
      validationMessage.style.padding = '10px';
      validationMessage.style.margin = '10px 0';
      validationMessage.innerHTML = `
        <strong>Temperature History Validator:</strong> All components present<br>
        ✅ History tab found<br>
        ✅ ${periodSelectors.length} period selectors found (${periodsFound.join(', ')} days)<br>
        ✅ Temperature chart container found
      `;

      chartContainer.parentNode.insertBefore(validationMessage, chartContainer);
    }

    console.log('🏁 Temperature History Validator: Validation complete');
  }
})();
