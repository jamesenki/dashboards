/**
 * Direct Fix Verification
 * This script directly tests and verifies the fixes for:
 * 1. Status duplication in Operations tab
 * 2. Empty Temperature History box with proper error message
 * 
 * Following TDD principles - we define expected behavior and test against it
 */

// Test runner that will execute immediately when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('%c📋 DIRECT FIX VERIFICATION TESTS', 'font-size: 14px; font-weight: bold; color: blue;');
    
    // Create a visible test report element
    createTestReportElement();
    
    // Run the tests after a delay to ensure everything is loaded
    setTimeout(function() {
        runDirectFixVerificationTests();
    }, 2000);
});

// Create a visible test report element
function createTestReportElement() {
    const reportEl = document.createElement('div');
    reportEl.id = 'fix-verification-report';
    reportEl.style.position = 'fixed';
    reportEl.style.top = '10px';
    reportEl.style.right = '10px';
    reportEl.style.width = '400px';
    reportEl.style.backgroundColor = '#333';
    reportEl.style.color = 'white';
    reportEl.style.padding = '15px';
    reportEl.style.borderRadius = '5px';
    reportEl.style.zIndex = '10000';
    reportEl.style.boxShadow = '0 0 10px rgba(0,0,0,0.5)';
    reportEl.style.fontFamily = 'Arial, sans-serif';
    reportEl.style.fontSize = '14px';
    
    reportEl.innerHTML = `
        <h3 style="margin-top:0; border-bottom: 1px solid #666; padding-bottom: 5px;">🧪 Fix Verification Tests</h3>
        <div id="status-tests-result">⏳ Status duplication test: Running...</div>
        <div id="history-tests-result">⏳ Temperature history test: Waiting...</div>
        <div id="test-summary" style="margin-top: 10px; font-weight: bold;"></div>
        <button id="close-report" style="position: absolute; top: 5px; right: 5px; background: none; border: none; color: white; cursor: pointer;">X</button>
    `;
    
    document.body.appendChild(reportEl);
    
    // Add close button functionality
    document.getElementById('close-report').addEventListener('click', function() {
        document.getElementById('fix-verification-report').style.display = 'none';
    });
}

// Run all verification tests
function runDirectFixVerificationTests() {
    console.log('🧪 Running verification tests for status duplication and temperature history fixes');
    
    // Initialize results
    let testsPassed = 0;
    let testsFailed = 0;
    
    // First test: Status duplication fix
    testStatusDuplication()
        .then(result => {
            // Update status test result
            const statusResultEl = document.getElementById('status-tests-result');
            statusResultEl.innerHTML = result.passed ? 
                '✅ Status duplication test: PASSED - No duplicate items detected' : 
                '❌ Status duplication test: FAILED - Duplicate items still present';
            
            if (result.passed) testsPassed++; else testsFailed++;
            
            // Continue with history test
            return testTemperatureHistory();
        })
        .then(result => {
            // Update history test result
            const historyResultEl = document.getElementById('history-tests-result');
            historyResultEl.innerHTML = result.passed ? 
                `✅ Temperature history test: PASSED - ${result.message}` : 
                `❌ Temperature history test: FAILED - ${result.message}`;
            
            if (result.passed) testsPassed++; else testsFailed++;
            
            // Update summary
            const summaryEl = document.getElementById('test-summary');
            summaryEl.innerHTML = `Tests summary: ${testsPassed} passed, ${testsFailed} failed`;
            summaryEl.style.color = testsFailed === 0 ? '#4CAF50' : '#F44336';
        })
        .catch(error => {
            console.error('Error running tests:', error);
            document.getElementById('test-summary').innerHTML = `Error running tests: ${error.message}`;
            document.getElementById('test-summary').style.color = '#F44336';
        });
}

// Test 1: Verify status duplication fix
function testStatusDuplication() {
    return new Promise((resolve) => {
        console.log('🧪 Testing status duplication fix...');
        
        // Navigate to operations tab
        const operationsTab = document.getElementById('operations-tab-btn');
        if (!operationsTab) {
            resolve({
                passed: false,
                message: 'Could not find operations tab button'
            });
            return;
        }
        
        operationsTab.click();
        
        // Wait for operations tab to activate and render
        setTimeout(() => {
            // Count initial status items
            const initialStatusItems = document.querySelectorAll('.status-item');
            const initialCount = initialStatusItems.length;
            console.log(`Initial status items: ${initialCount}`);
            
            // Get each item's text content to check for duplicates
            const statusTexts = Array.from(initialStatusItems).map(item => {
                const label = item.querySelector('.status-label');
                const value = item.querySelector('.status-value');
                return `${label?.textContent || ''}:${value?.textContent || ''}`;
            });
            
            // Check for duplicate texts
            const uniqueTexts = new Set(statusTexts);
            const hasDuplicates = uniqueTexts.size !== statusTexts.length;
            
            if (hasDuplicates) {
                console.error('Duplicate status items detected in initial state!');
                resolve({
                    passed: false,
                    message: 'Duplicate status items found in initial state'
                });
                return;
            }
            
            // Switch to history tab and back to operations to test duplication fix
            const historyTab = document.getElementById('history-tab-btn');
            if (!historyTab) {
                resolve({
                    passed: false,
                    message: 'Could not find history tab button'
                });
                return;
            }
            
            historyTab.click();
            
            // Wait for history tab to activate, then switch back
            setTimeout(() => {
                operationsTab.click();
                
                // Wait for operations tab to re-render
                setTimeout(() => {
                    // Count status items after tab switching
                    const newStatusItems = document.querySelectorAll('.status-item');
                    const newCount = newStatusItems.length;
                    console.log(`Status items after switching: ${newCount}`);
                    
                    // Get new text contents
                    const newStatusTexts = Array.from(newStatusItems).map(item => {
                        const label = item.querySelector('.status-label');
                        const value = item.querySelector('.status-value');
                        return `${label?.textContent || ''}:${value?.textContent || ''}`;
                    });
                    
                    // Check for duplicates after switching
                    const newUniqueTexts = new Set(newStatusTexts);
                    const stillHasDuplicates = newUniqueTexts.size !== newStatusTexts.length;
                    
                    resolve({
                        passed: !stillHasDuplicates && newCount === 5,
                        message: stillHasDuplicates ? 
                            'Duplicate status items still present after switching tabs' : 
                            (newCount !== 5 ? 
                                `Wrong number of status items: ${newCount} (expected 5)` : 
                                'No duplicate status items after switching tabs')
                    });
                }, 500);
            }, 500);
        }, 500);
    });
}

// Test 2: Verify temperature history or error message
function testTemperatureHistory() {
    return new Promise((resolve) => {
        console.log('🧪 Testing temperature history chart or error message...');
        
        // Navigate to history tab
        const historyTab = document.getElementById('history-tab-btn');
        if (!historyTab) {
            resolve({
                passed: false,
                message: 'Could not find history tab button'
            });
            return;
        }
        
        historyTab.click();
        
        // Wait for history tab to activate and render
        setTimeout(() => {
            // Look for temperature chart
            const tempChart = document.getElementById('temperature-chart');
            if (!tempChart) {
                resolve({
                    passed: false,
                    message: 'Temperature chart element not found'
                });
                return;
            }
            
            // Check for chart error messaging
            const chartError = document.querySelector('.chart-error');
            
            // Look for chart canvas or error message
            const canvas = tempChart.querySelector('canvas');
            const hasCanvas = canvas !== null;
            const hasVisibleError = chartError !== null && window.getComputedStyle(chartError).display !== 'none';
            
            // Either we should see a rendered chart OR a clear error message
            if (hasCanvas) {
                resolve({
                    passed: true,
                    message: 'Temperature chart is properly rendered'
                });
            } else if (hasVisibleError) {
                // This is also acceptable - we're showing the shadow document error clearly
                resolve({
                    passed: true,
                    message: 'Error message is clearly displayed for missing shadow document'
                });
            } else {
                // Neither a chart nor an error message is shown - this is a failure
                resolve({
                    passed: false,
                    message: 'Neither chart nor error message is displayed'
                });
            }
        }, 1000);
    });
}

// Make functions globally available
window.runDirectFixVerificationTests = runDirectFixVerificationTests;
