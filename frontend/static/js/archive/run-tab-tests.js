/**
 * Tab Tests - Run this to verify if our fixes resolved the issues
 */

function runTabTests() {
  console.log('🔍 Running tab tests to validate fixes...');

  // Store results
  const results = {
    tabSwitchTests: [],
    statusDuplicationTests: [],
    historyChartTests: []
  };

  // Test tab switching
  function testTabSwitching() {
    console.log('🔍 Testing tab switching...');

    // Get tab manager
    const tabManager = window.tabManager;
    if (!tabManager) {
      results.tabSwitchTests.push('❌ TabManager not found');
      return;
    }

    // Record initial tab
    const initialTab = tabManager.getActiveTabId();
    results.tabSwitchTests.push(`✅ Initial tab: ${initialTab}`);

    // Try switching to operations
    console.log('Switching to operations tab...');
    tabManager.showTab('operations');

    // Verify switch
    const operationsActive = tabManager.getActiveTabId() === 'operations';
    results.tabSwitchTests.push(operationsActive ?
      '✅ Successfully switched to operations tab' :
      '❌ Failed to switch to operations tab');

    // Try switching to history
    console.log('Switching to history tab...');
    tabManager.showTab('history');

    // Verify switch
    const historyActive = tabManager.getActiveTabId() === 'history';
    results.tabSwitchTests.push(historyActive ?
      '✅ Successfully switched to history tab' :
      '❌ Failed to switch to history tab');

    // Return to initial tab
    tabManager.showTab(initialTab);
    results.tabSwitchTests.push(`✅ Returned to ${initialTab} tab`);
  }

  // Test status card duplication
  function testStatusDuplication() {
    console.log('🔍 Testing status card duplication...');

    // Get tab manager
    const tabManager = window.tabManager;
    if (!tabManager) {
      results.statusDuplicationTests.push('❌ TabManager not found');
      return;
    }

    // Switch to operations tab
    tabManager.showTab('operations');

    // Count status cards
    const initialStatusCards = document.querySelectorAll('.status-item').length;
    results.statusDuplicationTests.push(`✅ Initial status card count: ${initialStatusCards}`);

    // Switch to another tab and back
    tabManager.showTab('predictions');
    setTimeout(() => {
      tabManager.showTab('operations');

      // Count status cards again
      const newStatusCards = document.querySelectorAll('.status-item').length;
      results.statusDuplicationTests.push(`✅ Status card count after switching: ${newStatusCards}`);

      // Check for duplication
      if (newStatusCards > initialStatusCards) {
        results.statusDuplicationTests.push(`❌ Status duplication detected: ${newStatusCards} cards (expected ${initialStatusCards})`);
      } else if (newStatusCards === initialStatusCards) {
        results.statusDuplicationTests.push('✅ No status duplication detected');
      } else {
        results.statusDuplicationTests.push(`⚠️ Fewer status cards than expected: ${newStatusCards} (expected ${initialStatusCards})`);
      }

      // Continue with history tests
      testHistoryCharts();
    }, 500);
  }

  // Test history charts
  function testHistoryCharts() {
    console.log('🔍 Testing history charts...');

    // Get tab manager
    const tabManager = window.tabManager;
    if (!tabManager) {
      results.historyChartTests.push('❌ TabManager not found');
      return;
    }

    // Switch to history tab
    tabManager.showTab('history');

    setTimeout(() => {
      // Check if temperature chart exists and is visible
      const tempChart = document.getElementById('temperature-chart');
      if (!tempChart) {
        results.historyChartTests.push('❌ Temperature chart not found');
      } else {
        const isVisible = window.getComputedStyle(tempChart).display !== 'none';
        results.historyChartTests.push(isVisible ?
          '✅ Temperature chart is visible' :
          '❌ Temperature chart exists but is not visible');
      }

      // Check other charts
      const energyChart = document.getElementById('energy-usage-chart');
      const pressureChart = document.getElementById('pressure-flow-chart');

      results.historyChartTests.push(energyChart ?
        '✅ Energy usage chart found' :
        '❌ Energy usage chart not found');

      results.historyChartTests.push(pressureChart ?
        '✅ Pressure flow chart found' :
        '❌ Pressure flow chart not found');

      // Display results
      displayResults();
    }, 1000);
  }

  // Display test results
  function displayResults() {
    console.log('\n🔍 TEST RESULTS:');

    console.log('\n📋 Tab Switching Tests:');
    results.tabSwitchTests.forEach(result => console.log(result));

    console.log('\n📋 Status Duplication Tests:');
    results.statusDuplicationTests.forEach(result => console.log(result));

    console.log('\n📋 History Chart Tests:');
    results.historyChartTests.forEach(result => console.log(result));

    // Summary
    const allTests = [
      ...results.tabSwitchTests,
      ...results.statusDuplicationTests,
      ...results.historyChartTests
    ];

    const passed = allTests.filter(test => test.includes('✅')).length;
    const failed = allTests.filter(test => test.includes('❌')).length;
    const warnings = allTests.filter(test => test.includes('⚠️')).length;

    console.log(`\n📊 SUMMARY: ${passed} tests passed, ${failed} tests failed, ${warnings} warnings`);

    return {
      passed,
      failed,
      warnings,
      results
    };
  }

  // Run the tests
  testTabSwitching();
  setTimeout(testStatusDuplication, 500);

  return "Tests running... check console for results";
}

// Add test runner to window object
window.runTabTests = runTabTests;

console.log('Tab tests loaded! Run window.runTabTests() in console to validate fixes.');
