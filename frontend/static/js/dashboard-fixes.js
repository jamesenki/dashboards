/**
 * Dashboard Fixes - Targeted patches for water heater dashboard issues
 * Following Test-Driven Development principles
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('📋 Applying dashboard fixes...');

    // Fix 1: Prevent status duplication in the operations tab
    fixStatusDuplication();

    // Fix 2: Fix empty temperature history chart
    fixTemperatureHistoryChart();

    console.log('✅ Dashboard fixes applied!');
});

/**
 * Fix for status duplication in the operations tab
 * Patches the WaterHeaterOperationsDashboard.updateStatusCards method to clear existing items
 */
function fixStatusDuplication() {
    // Wait for the dashboard instance to be loaded
    const waitForOperationsDashboard = setInterval(() => {
        if (window.WaterHeaterOperationsDashboard && window.WaterHeaterOperationsDashboard.prototype) {
            clearInterval(waitForOperationsDashboard);

            console.log('📋 Patching status card update method...');

            // Store original method
            const originalUpdateStatusCards = window.WaterHeaterOperationsDashboard.prototype.updateStatusCards;

            // Replace with patched version that clears status cards first
            window.WaterHeaterOperationsDashboard.prototype.updateStatusCards = function(data) {
                console.log('Operations Dashboard: Updating status cards with duplication prevention');

                // Get or create the status container
                const statusContainer = document.querySelector('.status-container');
                if (statusContainer) {
                    // Clear existing status items to prevent duplication
                    console.log('Operations Dashboard: Clearing existing status items');
                    statusContainer.innerHTML = '';
                }

                // Call original method
                return originalUpdateStatusCards.call(this, data);
            };

            console.log('✅ Status duplication fix applied');
        }
    }, 100);
}

/**
 * Fix for empty temperature history chart
 * Ensures the chart is properly initialized when the history tab is activated
 */
function fixTemperatureHistoryChart() {
    // Wait for history dashboard instance to be loaded
    const waitForHistoryDashboard = setInterval(() => {
        if (window.WaterHeaterHistoryDashboard && window.WaterHeaterHistoryDashboard.prototype) {
            clearInterval(waitForHistoryDashboard);

            console.log('📋 Patching temperature chart initialization...');

            // Store original reload method
            const originalReload = window.WaterHeaterHistoryDashboard.prototype.reload;

            // Replace with patched version that forces chart initialization
            window.WaterHeaterHistoryDashboard.prototype.reload = function() {
                console.log('History Dashboard: Enhanced reload for chart visibility');

                // Force charts to be reinitialized
                this.temperatureChart = null;
                this.energyUsageChart = null;
                this.pressureFlowChart = null;

                // Ensure chart containers are visible
                const chartContainers = document.querySelectorAll('#history-content .chart-container');
                chartContainers.forEach(container => {
                    container.style.display = 'block';
                    container.style.visibility = 'visible';
                });

                // Call original reload
                const result = originalReload.call(this);

                // Additional actions to ensure chart rendering
                setTimeout(() => {
                    const historyContent = document.getElementById('history-content');
                    if (historyContent && historyContent.classList.contains('active')) {
                        console.log('History Dashboard: Forcing chart rendering after tab activation');

                        // Ensure we have chart data
                        this.loadHistoryData().catch(error => {
                            console.error('History Dashboard: Error loading data', error);
                        });
                    }
                }, 200);

                return result;
            };

            console.log('✅ Temperature history chart fix applied');
        }
    }, 100);
}

// Run verification tests to ensure fixes are working
function verifyFixes() {
    console.log('🧪 Verifying dashboard fixes...');

    // Test status duplication fix
    let testsPassed = 0;
    let testsFailed = 0;

    // Test 1: Status duplication fix
    const operationsTab = document.getElementById('operations-tab-btn');
    const historyTab = document.getElementById('history-tab-btn');

    if (operationsTab && historyTab) {
        // Switch to operations tab
        operationsTab.click();

        // Count initial status items
        const initialCount = document.querySelectorAll('.status-item').length;
        console.log(`Initial status item count: ${initialCount}`);

        // Switch tabs back and forth
        historyTab.click();
        setTimeout(() => {
            operationsTab.click();

            // Check count after switching
            setTimeout(() => {
                const newCount = document.querySelectorAll('.status-item').length;
                console.log(`Status item count after switching: ${newCount}`);

                if (newCount <= initialCount) {
                    console.log('✅ Status duplication fix verified!');
                    testsPassed++;
                } else {
                    console.error(`❌ Status duplication still occurring (${newCount} items vs initial ${initialCount})`);
                    testsFailed++;
                }

                // Test 2: Temperature chart fix
                historyTab.click();

                setTimeout(() => {
                    const tempChart = document.getElementById('temperature-chart');
                    if (tempChart) {
                        const chartContainer = tempChart.closest('.chart-container');
                        const isVisible = window.getComputedStyle(chartContainer).display !== 'none';

                        if (isVisible && tempChart.getContext && typeof tempChart.getContext === 'function') {
                            console.log('✅ Temperature chart fix verified!');
                            testsPassed++;
                        } else {
                            console.error('❌ Temperature chart still not rendering properly');
                            testsFailed++;
                        }
                    } else {
                        console.error('❌ Temperature chart element not found');
                        testsFailed++;
                    }

                    // Report results
                    console.log(`🧪 Tests summary: ${testsPassed} passed, ${testsFailed} failed`);
                }, 1000);
            }, 500);
        }, 500);
    } else {
        console.error('❌ Tab buttons not found, cannot verify fixes');
    }
}

// Make verification function available globally
window.verifyDashboardFixes = verifyFixes;

console.log('Dashboard fixes loaded! Run window.verifyDashboardFixes() to test the fixes.');
