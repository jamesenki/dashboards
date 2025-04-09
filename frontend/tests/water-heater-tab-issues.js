/**
 * Water Heater Tab Issues Diagnostic Tests
 *
 * This test file specifically targets the history tab and operations tab issues:
 * 1. Status duplication when switching between tabs
 * 2. Missing temperature history element in history tab
 * 3. Visibility issues with tab content
 */

// Remember that tests should drive our implementation, not the other way around
// Following TDD principles from our project guidelines

// Diagnostic information container
const diagnostics = {
  issues: [],
  passed: [],
  elements: {}
};

// Store references to DOM elements we need to test
function cacheElements() {
  // Tab navigation elements
  diagnostics.elements.tabButtons = {
    details: document.getElementById('details-tab-btn'),
    operations: document.getElementById('operations-tab-btn'),
    predictions: document.getElementById('predictions-tab-btn'),
    history: document.getElementById('history-tab-btn')
  };

  // Tab content elements
  diagnostics.elements.tabContents = {
    details: document.getElementById('details-content'),
    operations: document.getElementById('operations-content'),
    predictions: document.getElementById('predictions-content'),
    history: document.getElementById('history-content')
  };

  // Status elements in operations tab
  diagnostics.elements.statusCards = document.querySelectorAll('.status-item');

  // History elements
  diagnostics.elements.temperatureHistoryChart = document.getElementById('temperature-chart');
  diagnostics.elements.energyUsageChart = document.getElementById('energy-usage-chart');
  diagnostics.elements.pressureFlowChart = document.getElementById('pressure-flow-chart');

  // TabManager
  diagnostics.elements.tabManager = window.tabManager;
}

// Test that all tab buttons exist and function
function testTabButtons() {
  console.log('🔍 Testing tab buttons...');

  const buttons = diagnostics.elements.tabButtons;
  // Check if all buttons exist
  for (const [name, element] of Object.entries(buttons)) {
    if (!element) {
      diagnostics.issues.push(`❌ ${name} tab button not found in DOM`);
    } else {
      diagnostics.passed.push(`✅ ${name} tab button found`);
    }
  }
}

// Test tab content visibility - only one should be visible at a time
function testTabContentVisibility() {
  console.log('🔍 Testing tab content visibility...');

  const contents = diagnostics.elements.tabContents;
  let visibleTabs = 0;

  for (const [name, element] of Object.entries(contents)) {
    if (!element) {
      diagnostics.issues.push(`❌ ${name} tab content not found in DOM`);
      continue;
    }

    // Check if tab content is visible
    const isVisible = element.classList.contains('active') ||
                      getComputedStyle(element).display !== 'none';

    if (isVisible) {
      visibleTabs++;
      diagnostics.passed.push(`✅ ${name} tab content is visible`);
    }
  }

  // Only one tab should be visible at a time
  if (visibleTabs !== 1) {
    diagnostics.issues.push(`❌ ${visibleTabs} tabs visible at once (should be exactly 1)`);
  } else {
    diagnostics.passed.push('✅ Exactly one tab is visible');
  }
}

// Test status elements in operations dashboard
function testStatusElements() {
  console.log('🔍 Testing status elements in operations dashboard...');

  const statusCards = diagnostics.elements.statusCards;
  if (!statusCards || statusCards.length === 0) {
    diagnostics.issues.push('❌ No status cards found in operations dashboard');
    return;
  }

  diagnostics.passed.push(`✅ Found ${statusCards.length} status cards`);

  // Check for duplicate status cards
  const statusLabels = new Set();
  let duplicateLabels = [];

  statusCards.forEach(card => {
    const labelElement = card.querySelector('.status-label');
    if (labelElement) {
      const label = labelElement.textContent.trim();
      if (statusLabels.has(label)) {
        duplicateLabels.push(label);
      } else {
        statusLabels.add(label);
      }
    }
  });

  if (duplicateLabels.length > 0) {
    diagnostics.issues.push(`❌ Found duplicate status cards: ${duplicateLabels.join(', ')}`);
  } else {
    diagnostics.passed.push('✅ No duplicate status cards found');
  }
}

// Test history tab charts
function testHistoryCharts() {
  console.log('🔍 Testing history charts...');

  // Test temperature chart
  if (!diagnostics.elements.temperatureHistoryChart) {
    diagnostics.issues.push('❌ Temperature history chart not found in DOM');
  } else {
    diagnostics.passed.push('✅ Temperature history chart found');
  }

  // Test energy usage chart
  if (!diagnostics.elements.energyUsageChart) {
    diagnostics.issues.push('❌ Energy usage chart not found in DOM');
  } else {
    diagnostics.passed.push('✅ Energy usage chart found');
  }

  // Test pressure/flow chart
  if (!diagnostics.elements.pressureFlowChart) {
    diagnostics.issues.push('❌ Pressure/flow chart not found in DOM');
  } else {
    diagnostics.passed.push('✅ Pressure/flow chart found');
  }
}

// Test tab switching behavior
function testTabSwitching() {
  console.log('🔍 Testing tab switching behavior...');

  // We'll use the TabManager if available
  const tabManager = diagnostics.elements.tabManager;

  if (!tabManager) {
    diagnostics.issues.push('❌ TabManager not found - tab switching tests skipped');
    return;
  }

  diagnostics.passed.push('✅ TabManager found');

  // Current active tab
  const currentTab = tabManager.getActiveTabId();
  diagnostics.passed.push(`✅ Current active tab: ${currentTab}`);

  // Store the number of status elements before switching to operations
  let initialStatusCount = 0;
  if (currentTab !== 'operations') {
    initialStatusCount = document.querySelectorAll('.status-item').length;

    // Switch to operations tab
    console.log('🔄 Switching to operations tab...');
    tabManager.showTab('operations');

    // Check status elements after switching
    const operationsStatusCount = document.querySelectorAll('.status-item').length;

    // Should have 5 status items in operations tab
    if (operationsStatusCount === 5) {
      diagnostics.passed.push(`✅ Operations tab has correct number of status items (${operationsStatusCount})`);
    } else {
      diagnostics.issues.push(`❌ Operations tab has incorrect number of status items (${operationsStatusCount}, expected 5)`);
    }
  }

  // Switch to history tab
  console.log('🔄 Switching to history tab...');
  tabManager.showTab('history');

  // Check if history tab is now active
  if (tabManager.getActiveTabId() === 'history') {
    diagnostics.passed.push('✅ Successfully switched to history tab');

    // Check if temperature chart is now visible
    const tempChart = document.getElementById('temperature-chart');
    if (tempChart) {
      const isVisible = tempChart.offsetParent !== null;
      if (isVisible) {
        diagnostics.passed.push('✅ Temperature chart is visible in history tab');
      } else {
        diagnostics.issues.push('❌ Temperature chart exists but is not visible');
      }
    } else {
      diagnostics.issues.push('❌ Temperature chart not found after switching to history tab');
    }
  } else {
    diagnostics.issues.push('❌ Failed to switch to history tab');
  }

  // Switch back to operations tab
  console.log('🔄 Switching back to operations tab...');
  tabManager.showTab('operations');

  // Check for status duplication
  const finalStatusCount = document.querySelectorAll('.status-item').length;

  if (finalStatusCount > 5) {
    diagnostics.issues.push(`❌ Status duplication detected! (${finalStatusCount} status items, expected 5)`);
  } else {
    diagnostics.passed.push(`✅ No status duplication when switching back to operations tab (${finalStatusCount} status items)`);
  }

  // Return to original tab
  if (currentTab !== 'operations') {
    console.log(`🔄 Switching back to original ${currentTab} tab...`);
    tabManager.showTab(currentTab);
  }
}

// Check for any CSS issues
function testCssIssues() {
  console.log('🔍 Testing for CSS issues...');

  // Check for !important flags in inline styles which may be causing issues
  const tabContents = Object.values(diagnostics.elements.tabContents).filter(Boolean);

  let foundImportantFlags = false;
  tabContents.forEach(content => {
    if (content.style.cssText.includes('!important')) {
      foundImportantFlags = true;
      diagnostics.issues.push(`❌ Found !important flags in inline styles for ${content.id}`);
    }
  });

  if (!foundImportantFlags) {
    diagnostics.passed.push('✅ No !important flags found in inline styles');
  }

  // Check for z-index stacking issues
  const zIndexes = {};
  tabContents.forEach(content => {
    const zIndex = getComputedStyle(content).zIndex;
    if (zIndex !== 'auto') {
      zIndexes[content.id] = parseInt(zIndex, 10);
    }
  });

  if (Object.keys(zIndexes).length > 0) {
    diagnostics.passed.push(`✅ Found z-index values: ${JSON.stringify(zIndexes)}`);

    // Check if active tab has highest z-index
    const activeTab = document.querySelector('.tab-content.active');
    if (activeTab) {
      const activeZIndex = getComputedStyle(activeTab).zIndex;
      let isHighest = true;

      for (const [id, zIndex] of Object.entries(zIndexes)) {
        if (id !== activeTab.id && zIndex > activeZIndex) {
          isHighest = false;
          diagnostics.issues.push(`❌ Active tab (${activeTab.id}) has lower z-index than ${id}`);
        }
      }

      if (isHighest) {
        diagnostics.passed.push('✅ Active tab has highest z-index');
      }
    }
  }
}

// Run all tests and report results
function runDiagnostics() {
  console.log('🚀 Starting water heater tab diagnostics...');
  diagnostics.timestamp = new Date().toISOString();
  diagnostics.url = window.location.href;

  try {
    // Cache DOM elements
    cacheElements();

    // Run tests
    testTabButtons();
    testTabContentVisibility();
    testStatusElements();
    testHistoryCharts();
    testTabSwitching();
    testCssIssues();

    // Output results
    console.log('\n🔍 DIAGNOSTIC RESULTS:');
    console.log(`🕒 ${diagnostics.timestamp}`);
    console.log(`🌐 ${diagnostics.url}`);

    console.log('\n✅ TESTS PASSED:');
    diagnostics.passed.forEach(msg => console.log(msg));

    console.log('\n❌ ISSUES FOUND:');
    if (diagnostics.issues.length === 0) {
      console.log('No issues found in this diagnostic run!');
    } else {
      diagnostics.issues.forEach(msg => console.log(msg));
    }

    return {
      passed: diagnostics.passed,
      issues: diagnostics.issues,
      timestamp: diagnostics.timestamp,
      url: diagnostics.url
    };
  } catch (error) {
    console.error('💥 Error running diagnostics:', error);
    return {
      error: error.message,
      stack: error.stack
    };
  }
}

// Auto-run diagnostics when loaded
window.runWaterHeaterTabDiagnostics = runDiagnostics;
console.log('Water heater tab diagnostics loaded! Call window.runWaterHeaterTabDiagnostics() to run tests.');
