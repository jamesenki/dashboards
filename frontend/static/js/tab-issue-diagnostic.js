/**
 * Tab Issue Diagnostic
 * A simple script to diagnose and fix tab-related issues in the water heater dashboard
 */

class TabIssuesDiagnostic {
    constructor() {
        console.log('🧪 Tab Issues Diagnostic Tool initializing...');
        this.issues = {
            statusDuplication: false,
            emptyHistoryChart: false
        };
        
        // Run diagnostics on load
        this.runDiagnostics();
        
        // Apply fixes
        this.applyFixes();
    }
    
    runDiagnostics() {
        console.log('🔍 Running diagnostics...');
        
        // Check for status duplication
        this.checkStatusDuplication();
        
        // Check for empty history chart
        this.checkHistoryChartRendering();
        
        // Report results
        console.log('📊 Diagnostic Results:');
        console.log(`Status Duplication: ${this.issues.statusDuplication ? '❌ Detected' : '✅ Not detected'}`);
        console.log(`Empty History Chart: ${this.issues.emptyHistoryChart ? '❌ Detected' : '✅ Not detected'}`);
    }
    
    checkStatusDuplication() {
        const statusItems = document.querySelectorAll('.status-item');
        const statusLabels = {};
        
        // Count occurrences of each status label
        statusItems.forEach(item => {
            const label = item.querySelector('.status-label')?.textContent.trim();
            if (label) {
                statusLabels[label] = (statusLabels[label] || 0) + 1;
            }
        });
        
        // Check if any label appears more than once
        for (const label in statusLabels) {
            if (statusLabels[label] > 1) {
                console.log(`❌ Status duplication detected: "${label}" appears ${statusLabels[label]} times`);
                this.issues.statusDuplication = true;
                return;
            }
        }
    }
    
    checkHistoryChartRendering() {
        // Force switch to history tab
        const historyTabBtn = document.getElementById('history-tab-btn');
        if (historyTabBtn) {
            // Save current tab
            const currentActiveTab = document.querySelector('.tab-btn.active');
            
            // Switch to history tab
            console.log('Switching to history tab to check chart rendering...');
            historyTabBtn.click();
            
            // Check if temperature chart exists and has a canvas
            const tempChart = document.getElementById('temperature-chart');
            const tempChartContainer = tempChart?.closest('.chart-container');
            
            if (!tempChart) {
                console.log('❌ Temperature chart element not found');
                this.issues.emptyHistoryChart = true;
            } else if (window.getComputedStyle(tempChartContainer).display === 'none') {
                console.log('❌ Temperature chart container is hidden');
                this.issues.emptyHistoryChart = true;
            } else {
                // Check if chart has been rendered
                const canvas = tempChart.getContext('2d');
                if (!canvas) {
                    console.log('❌ Temperature chart canvas context not available');
                    this.issues.emptyHistoryChart = true;
                }
            }
            
            // Return to previous tab
            if (currentActiveTab) {
                currentActiveTab.click();
            }
        }
    }
    
    applyFixes() {
        console.log('🔧 Applying fixes...');
        
        // Fix status duplication
        if (this.issues.statusDuplication) {
            this.fixStatusDuplication();
        }
        
        // Fix empty history chart
        if (this.issues.emptyHistoryChart) {
            this.fixHistoryChartRendering();
        }
    }
    
    fixStatusDuplication() {
        console.log('🔧 Fixing status duplication...');
        
        // Patch the operations dashboard reload method
        if (window.waterHeaterOperationsDashboard) {
            const originalReload = window.waterHeaterOperationsDashboard.reload;
            
            window.waterHeaterOperationsDashboard.reload = function() {
                console.log('Patched reload method for operations dashboard');
                
                // Clear existing status items before reloading
                const statusContainer = document.querySelector('.status-container');
                if (statusContainer) {
                    console.log('Clearing existing status items');
                    statusContainer.innerHTML = '';
                }
                
                // Call original reload
                return originalReload.apply(this, arguments);
            };
            
            console.log('✅ Applied patch to prevent status duplication');
        } else {
            console.log('❌ Cannot patch operations dashboard - not initialized');
        }
    }
    
    fixHistoryChartRendering() {
        console.log('🔧 Fixing history chart rendering...');
        
        // Patch the history dashboard reload method
        if (window.waterHeaterHistoryDashboard) {
            const originalReload = window.waterHeaterHistoryDashboard.reload;
            
            window.waterHeaterHistoryDashboard.reload = function() {
                console.log('Patched reload method for history dashboard');
                
                // Force reinitialization of charts
                this.temperatureChart = null;
                this.energyUsageChart = null;
                this.pressureFlowChart = null;
                
                // Make sure chart containers are visible
                const chartContainers = document.querySelectorAll('#history-content .chart-container');
                chartContainers.forEach(container => {
                    container.style.display = 'block';
                    container.style.visibility = 'visible';
                });
                
                // Call original reload
                return originalReload.apply(this, arguments);
            };
            
            console.log('✅ Applied patch to fix history chart rendering');
        } else {
            console.log('❌ Cannot patch history dashboard - not initialized');
        }
    }
}

// Initialize diagnostic tool when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🧪 Initializing Tab Issues Diagnostic Tool...');
    window.tabDiagnostic = new TabIssuesDiagnostic();
});

console.log('🧪 Tab Issues Diagnostic Tool loaded');
