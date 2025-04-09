/**
 * Auto Test Runner - Automatically runs dashboard verification tests
 * and displays results on the page
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🧪 Auto Test Runner: Starting tests in 3 seconds...');

    // Create test results display
    const resultsContainer = document.createElement('div');
    resultsContainer.id = 'test-results-container';
    resultsContainer.style.position = 'fixed';
    resultsContainer.style.top = '10px';
    resultsContainer.style.right = '10px';
    resultsContainer.style.width = '350px';
    resultsContainer.style.padding = '15px';
    resultsContainer.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    resultsContainer.style.color = 'white';
    resultsContainer.style.borderRadius = '5px';
    resultsContainer.style.zIndex = '9999';
    resultsContainer.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.5)';
    resultsContainer.style.fontFamily = 'Arial, sans-serif';
    resultsContainer.innerHTML = '<h3 style="margin-top: 0; color: #fff;">Test Results</h3><div id="test-status">Preparing tests...</div>';

    document.body.appendChild(resultsContainer);

    // Run tests after slight delay to ensure dashboard is initialized
    setTimeout(function() {
        runTests();
    }, 3000);

    // Function to run all our verification tests
    function runTests() {
        const statusDiv = document.getElementById('test-status');
        statusDiv.innerHTML = '<div>Running dashboard tests...</div>';

        // Test 1: Check status duplication
        testStatusDuplication().then(result => {
            statusDiv.innerHTML += `<div style="margin-top: 10px; color: ${result.passed ? '#4CAF50' : '#F44336'}">${result.message}</div>`;

            // Test 2: Check temperature chart
            return testTemperatureChart();
        }).then(result => {
            statusDiv.innerHTML += `<div style="margin-top: 10px; color: ${result.passed ? '#4CAF50' : '#F44336'}">${result.message}</div>`;

            // Final summary
            statusDiv.innerHTML += '<div style="margin-top: 15px; border-top: 1px solid #555; padding-top: 10px;">Tests completed</div>';
        }).catch(error => {
            statusDiv.innerHTML += `<div style="margin-top: 10px; color: #F44336">Error running tests: ${error.message}</div>`;
        });
    }

    // Test for status duplication
    function testStatusDuplication() {
        return new Promise((resolve) => {
            console.log('🧪 Testing for status duplication...');

            // Switch to operations tab
            const operationsTab = document.getElementById('operations-tab-btn');
            if (!operationsTab) {
                resolve({
                    passed: false,
                    message: '❌ TEST 1: Could not find operations tab button'
                });
                return;
            }

            operationsTab.click();

            // Wait for operations content to be visible
            setTimeout(() => {
                // Count initial status items
                const initialCount = document.querySelectorAll('.status-item').length;
                console.log(`Initial status items count: ${initialCount}`);

                // Switch to another tab and back
                const historyTab = document.getElementById('history-tab-btn');
                if (!historyTab) {
                    resolve({
                        passed: false,
                        message: '❌ TEST 1: Could not find history tab button'
                    });
                    return;
                }

                historyTab.click();

                // Wait for history tab to become active
                setTimeout(() => {
                    // Switch back to operations
                    operationsTab.click();

                    // Check status items after switching
                    setTimeout(() => {
                        const newCount = document.querySelectorAll('.status-item').length;
                        console.log(`Status items after switching: ${newCount}`);

                        if (newCount <= initialCount) {
                            resolve({
                                passed: true,
                                message: `✅ TEST 1: Status duplication fixed! (${newCount} items)`
                            });
                        } else {
                            resolve({
                                passed: false,
                                message: `❌ TEST 1: Status duplication still present (${newCount} > ${initialCount})`
                            });
                        }
                    }, 500);
                }, 500);
            }, 500);
        });
    }

    // Test for temperature chart visibility
    function testTemperatureChart() {
        return new Promise((resolve) => {
            console.log('🧪 Testing temperature history chart...');

            // Switch to history tab
            const historyTab = document.getElementById('history-tab-btn');
            if (!historyTab) {
                resolve({
                    passed: false,
                    message: '❌ TEST 2: Could not find history tab button'
                });
                return;
            }

            historyTab.click();

            // Wait for history content to be visible
            setTimeout(() => {
                // Check temperature chart
                const tempChart = document.getElementById('temperature-chart');
                if (!tempChart) {
                    resolve({
                        passed: false,
                        message: '❌ TEST 2: Temperature chart element not found'
                    });
                    return;
                }

                const tempChartContainer = tempChart.closest('.chart-container');
                if (!tempChartContainer) {
                    resolve({
                        passed: false,
                        message: '❌ TEST 2: Temperature chart container not found'
                    });
                    return;
                }

                const isVisible = window.getComputedStyle(tempChartContainer).display !== 'none';
                const hasCanvas = tempChart.querySelector('canvas') !== null;

                if (isVisible && hasCanvas) {
                    resolve({
                        passed: true,
                        message: '✅ TEST 2: Temperature chart is visible and rendered!'
                    });
                } else if (!isVisible) {
                    resolve({
                        passed: false,
                        message: '❌ TEST 2: Temperature chart container is not visible'
                    });
                } else {
                    resolve({
                        passed: false,
                        message: '❌ TEST 2: Temperature chart does not have a canvas element'
                    });
                }
            }, 1000);
        });
    }
});
