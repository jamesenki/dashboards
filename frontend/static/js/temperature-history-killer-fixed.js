/**
 * SIMPLIFIED TEMPERATURE HISTORY HANDLER
 *
 * This script applies a targeted approach to hide temperature history charts
 * only on the water heater details page main view, not in the tabs.
 * It uses minimal DOM modifications and targeted CSS.
 */

(function() {
    console.log('Temperature History Handler: Initialized');

    // Add a simple CSS rule to hide temperature history panels
    function addSimpleCss() {
        const styleId = 'temperature-history-style';
        if (document.getElementById(styleId)) return;

        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            /* Only hide temperature history on the main container, not in tabs */
            .dashboard-container .temperature-chart { display: none; }
        `;
        document.head.appendChild(style);
        console.log('Temperature History Handler: Simple CSS added');
    }

    // Handle tab activation
    function setupTabs() {
        // Simple fix - just hide the history tab and show maintenance tab instead
        // This focuses ONLY on tab visibility, not removing important functionality

        // 1. Find the temperature history tab button
        const historyTabBtn = document.querySelector('.tab-btn[data-tab="history"]');
        const historyPanel = document.getElementById('history');

        // 2. Find the maintenance tab button and panel
        const maintenanceTabBtn = document.querySelector('.tab-btn[data-tab="maintenance"]');
        const maintenancePanel = document.getElementById('maintenance');

        // 3. If history tab exists, make it inactive
        if (historyTabBtn) {
            historyTabBtn.classList.remove('active');
        }

        if (historyPanel) {
            historyPanel.classList.remove('active');
        }

        // 4. Make maintenance tab active
        if (maintenanceTabBtn) {
            maintenanceTabBtn.classList.add('active');
        }

        if (maintenancePanel) {
            maintenancePanel.classList.add('active');
        }

        console.log('Temperature History Handler: Tab visibility adjusted');
    }

    // Initialize the handler
    function init() {
        addSimpleCss();

        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', setupTabs);
        } else {
            setupTabs();
        }
    }

    // Run initialization
    init();
})();
