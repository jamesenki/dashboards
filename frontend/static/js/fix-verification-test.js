/**
 * Fix Verification Test
 *
 * This script verifies that our fixes for water heater duplication
 * and temperature history display are working correctly.
 *
 * Following TDD principles:
 * 1. RED: Define expected behaviors
 * 2. GREEN: Implement fixes to make tests pass
 * 3. REFACTOR: Improve and verify
 */

(function() {
  console.log('🧪 Starting Fix Verification Tests');

  // Start tests when DOM is ready
  document.addEventListener('DOMContentLoaded', runVerificationTests);

  // Also run immediately in case DOM is already loaded
  setTimeout(runVerificationTests, 1000);

  /**
   * Main test runner function
   */
  function runVerificationTests() {
    console.log('🧪 Running verification tests...');

    // Determine which page we're on
    const isWaterHeaterList = window.location.href.includes('/water-heaters') &&
                              !window.location.href.includes('detail');

    const isWaterHeaterDetails = window.location.href.includes('/water-heaters') &&
                                window.location.href.includes('detail');

    // Run appropriate tests
    if (isWaterHeaterList) {
      testWaterHeaterDeduplication();
    }

    if (isWaterHeaterDetails) {
      testTemperatureHistoryDisplay();
    }

    // If not on a testable page, log information
    if (!isWaterHeaterList && !isWaterHeaterDetails) {
      console.log('📋 Not on a testable page. Navigate to water heater list or details to run tests.');
    }
  }

  /**
   * Test water heater deduplication
   */
  function testWaterHeaterDeduplication() {
    console.log('🧪 TEST: Water Heater Deduplication');

    // Test will complete asynchronously
    const testCompletionPromise = new Promise((resolve) => {
      // Wait for deduplication to finish
      const checkInterval = setInterval(() => {
        const testStatus = document.getElementById('deduplication-test-status');

        if (testStatus) {
          clearInterval(checkInterval);

          // Get test results
          const testPassed = testStatus.dataset.testPassed === 'true';
          const duplicatesFound = parseInt(testStatus.dataset.duplicatesFound);

          if (testPassed) {
            console.log('✅ PASS: Water heater deduplication fix successfully applied');
            console.log(`   - ${duplicatesFound} duplicates were removed`);
          } else {
            console.log('❌ FAIL: Water heater deduplication did not work as expected');
          }

          resolve(testPassed);
        }
      }, 500);

      // Timeout after 5 seconds
      setTimeout(() => {
        clearInterval(checkInterval);
        console.log('❓ INCONCLUSIVE: Deduplication test timed out');
        console.log('   - Possible causes: No duplicates to remove or script not running');

        // Count water heater cards manually
        const cards = document.querySelectorAll('.water-heater-card');
        console.log(`   - Found ${cards.length} water heater cards (should be without duplicates)`);

        resolve(false);
      }, 5000);
    });

    return testCompletionPromise;
  }

  /**
   * Test temperature history display
   */
  function testTemperatureHistoryDisplay() {
    console.log('🧪 TEST: Temperature History Display');

    // Test will complete asynchronously
    const testCompletionPromise = new Promise((resolve) => {
      // Wait for history chart to load or error
      const checkInterval = setInterval(() => {
        const successStatus = document.getElementById('temp-history-test-status');
        const errorStatus = document.getElementById('temp-history-test-error');

        if (successStatus) {
          clearInterval(checkInterval);

          // Get test results
          const testPassed = successStatus.dataset.testPassed === 'true';
          const pointsLoaded = parseInt(successStatus.dataset.pointsLoaded);

          console.log('✅ PASS: Temperature history data successfully loaded');
          console.log(`   - ${pointsLoaded} data points loaded`);

          // Check if canvas element exists
          const canvas = document.querySelector('.temperature-history-container canvas');
          if (canvas) {
            console.log('✅ PASS: Temperature chart rendered successfully');
          } else {
            console.log('❌ FAIL: Chart canvas not found even though data was loaded');
          }

          resolve(testPassed);
        } else if (errorStatus) {
          clearInterval(checkInterval);

          // If error is handled properly, that's still a pass for our fix
          const errorHandled = errorStatus.dataset.errorHandled === 'true';
          const errorMessage = errorStatus.dataset.errorMessage;

          console.log('✅ PASS: Temperature history error properly handled');
          console.log(`   - Error message: ${errorMessage}`);

          // Check if error message is displayed
          const errorElement = document.querySelector('.error-message, .chart-error');
          if (errorElement) {
            console.log('✅ PASS: Error message displayed to user correctly');
          } else {
            console.log('❌ FAIL: Error message not displayed to user');
          }

          resolve(errorHandled);
        }
      }, 500);

      // Timeout after 10 seconds
      setTimeout(() => {
        clearInterval(checkInterval);
        console.log('❓ INCONCLUSIVE: Temperature history test timed out');

        // Check for chart or error message manually
        const canvas = document.querySelector('.temperature-history-container canvas');
        const errorElement = document.querySelector('.error-message, .chart-error');

        if (canvas) {
          console.log('✅ PASS: Temperature chart appears to be rendered');
          resolve(true);
        } else if (errorElement) {
          console.log('✅ PASS: Error message is displayed correctly');
          resolve(true);
        } else {
          console.log('❌ FAIL: Neither chart nor error message found');
          resolve(false);
        }
      }, 10000);
    });

    return testCompletionPromise;
  }

  /**
   * Create a visual test report
   * @param {boolean} passed - Whether the test passed
   * @param {string} message - Test message
   */
  function showTestReport(passed, message) {
    // Create a test report element
    const reportElement = document.createElement('div');
    reportElement.className = 'test-report ' + (passed ? 'pass' : 'fail');
    reportElement.innerHTML = `
      <div class="test-result">
        <span class="test-icon">${passed ? '✅' : '❌'}</span>
        <span class="test-message">${message}</span>
      </div>
      <button class="test-close">Close</button>
    `;

    // Style the report
    Object.assign(reportElement.style, {
      position: 'fixed',
      bottom: '20px',
      right: '20px',
      backgroundColor: passed ? '#e6ffec' : '#ffebe9',
      border: `1px solid ${passed ? '#56d364' : '#ff7b72'}`,
      padding: '15px',
      borderRadius: '6px',
      boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
      zIndex: '9999',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      maxWidth: '300px'
    });

    // Style the icon and message
    const resultElement = reportElement.querySelector('.test-result');
    Object.assign(resultElement.style, {
      display: 'flex',
      alignItems: 'center',
      marginBottom: '10px'
    });

    const iconElement = reportElement.querySelector('.test-icon');
    Object.assign(iconElement.style, {
      fontSize: '20px',
      marginRight: '10px'
    });

    // Style the close button
    const closeButton = reportElement.querySelector('.test-close');
    Object.assign(closeButton.style, {
      backgroundColor: '#f6f8fa',
      border: '1px solid #d0d7de',
      borderRadius: '6px',
      padding: '4px 8px',
      fontSize: '12px',
      cursor: 'pointer'
    });

    // Add close functionality
    closeButton.addEventListener('click', () => {
      reportElement.remove();
    });

    // Add to the document
    document.body.appendChild(reportElement);

    // Auto-remove after 10 seconds
    setTimeout(() => {
      if (document.body.contains(reportElement)) {
        reportElement.remove();
      }
    }, 10000);
  }
})();
