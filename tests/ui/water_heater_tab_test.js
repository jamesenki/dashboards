/**
 * TDD-compliant test for Water Heater Dashboard tab issues
 * Follows Red, Green, Refactor methodology
 */

// Test 1: Verify that status cards don't duplicate when switching tabs
function testStatusCardDuplication() {
  console.log('🧪 TEST: Status cards should not duplicate when switching tabs');
  
  // Count initial status cards
  const initialStatusCount = document.querySelectorAll('.status-item').length;
  console.log(`Initial status card count: ${initialStatusCount}`);
  
  // Switch to history tab and back to operations
  const historyTab = document.getElementById('history-tab-btn');
  const operationsTab = document.getElementById('operations-tab-btn');
  
  if (historyTab && operationsTab) {
    historyTab.click();
    setTimeout(() => {
      operationsTab.click();
      
      // Count status cards after switching
      setTimeout(() => {
        const newStatusCount = document.querySelectorAll('.status-item').length;
        console.log(`Status card count after switching: ${newStatusCount}`);
        
        if (newStatusCount > initialStatusCount) {
          console.error(`❌ FAILED: Status cards were duplicated (${newStatusCount} > ${initialStatusCount})`);
          return false;
        } else {
          console.log('✅ PASSED: Status cards were not duplicated');
          return true;
        }
      }, 500);
    }, 500);
  }
}

// Test 2: Verify that temperature history chart is visible
function testTemperatureHistoryChart() {
  console.log('🧪 TEST: Temperature history chart should be visible when history tab is active');
  
  // Switch to history tab
  const historyTab = document.getElementById('history-tab-btn');
  
  if (historyTab) {
    historyTab.click();
    
    setTimeout(() => {
      // Check if temperature chart exists and is visible
      const tempChart = document.getElementById('temperature-chart');
      const tempChartContainer = tempChart?.closest('.chart-container');
      
      if (!tempChart) {
        console.error('❌ FAILED: Temperature chart element not found');
        return false;
      }
      
      const isVisible = window.getComputedStyle(tempChartContainer).display !== 'none';
      
      if (!isVisible) {
        console.error('❌ FAILED: Temperature chart is not visible');
        return false;
      }
      
      console.log('✅ PASSED: Temperature chart is visible');
      return true;
    }, 1000);
  }
}

// Run tests
function runTests() {
  console.log('🧪 Running TDD-compliant tests for Water Heater Dashboard');
  testStatusCardDuplication();
  setTimeout(testTemperatureHistoryChart, 2000);
}

// Expose to window
window.runWaterHeaterTests = runTests;
console.log('Water heater tests loaded. Run window.runWaterHeaterTests() to execute tests.');
