/**
 * TEMPERATURE HISTORY KILLER (SAFE VERSION)
 *
 * This is a less aggressive version of the temperature history removal script.
 * It focuses only on the details page and uses more targeted selectors to avoid
 * breaking other functionality.
 */

(function() {
    console.log('🔍 Safe Temperature History Removal: Initialized');

    // Only apply to details page, not history tab
    function isDetailsPage() {
        // Check if we're on a details page and not in a tab
        const urlPath = window.location.pathname;
        // Look for patterns like /water-heaters/device-id but not /water-heaters
        return urlPath.match(/\/water-heaters\/[^\/]+$/) !== null;
    }

    // More targeted CSS that only affects the temperature history on details page
    function injectTargetedCSS() {
        if (!isDetailsPage()) {
            console.log('Not on details page, skipping CSS injection');
            return;
        }

        const styleId = 'temperature-history-targeted-css';
        if (document.getElementById(styleId)) return;

        const styleEl = document.createElement('style');
        styleEl.id = styleId;
        styleEl.innerHTML = `
            /* Only target temperature history on the main details section, not in tabs */
            .dashboard-container .temperature-chart,
            .dashboard-container #temperature-chart,
            .dashboard-container [id^="temperature-chart"] {
                display: none;
            }

            /* Make sure the maintenance tab is active */
            #maintenance.tab-panel {
                display: block;
            }
            button[data-tab="maintenance"] {
                background-color: #fff;
                color: #0066cc;
                border-bottom: 2px solid #0066cc;
            }
        `;
        document.head.appendChild(styleEl);
        console.log('🎯 Safe Temperature History Removal: CSS injected');
    }

    // Safely find and modify temperature history elements
    function safelyHandleTemperatureElements() {
        if (!isDetailsPage()) {
            console.log('Not on details page, skipping element handling');
            return;
        }

        // Only target specific elements in the dashboard container
        const dashboardContainer = document.querySelector('.dashboard-container');
        if (!dashboardContainer) return;

        // Look for temperature charts specifically in the dashboard container
        const tempCharts = dashboardContainer.querySelectorAll('.temperature-chart, #temperature-chart, [id^="temperature-chart"]');
        tempCharts.forEach(chart => {
            console.log('🎯 Safe Temperature History Removal: Hiding chart in dashboard');
            chart.style.display = 'none';
        });

        // Make sure the maintenance tab is active
        const maintenanceTab = document.querySelector('[data-tab="maintenance"]');
        const maintenancePanel = document.getElementById('maintenance');

        if (maintenanceTab && !maintenanceTab.classList.contains('active')) {
            // Only modify if it's not already active
            document.querySelectorAll('.tab-btn').forEach(tab => {
                tab.classList.remove('active');
            });
            maintenanceTab.classList.add('active');
        }

        if (maintenancePanel && !maintenancePanel.classList.contains('active')) {
            // Only modify if it's not already active
            document.querySelectorAll('.tab-panel').forEach(panel => {
                panel.classList.remove('active');
            });
            maintenancePanel.classList.add('active');
        }
    }

    // Initialize the safe temperature history removal
    function init() {
        console.log('🔍 Safe Temperature History Removal: Initializing');
        injectTargetedCSS();

        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', safelyHandleTemperatureElements);
        } else {
            safelyHandleTemperatureElements();
        }

        // Set up a lighter-weight mutation observer that only looks for charts
        const observer = new MutationObserver(function(mutations) {
            let shouldCheck = false;

            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length) {
                    shouldCheck = true;
                }
            });

            if (shouldCheck) {
                safelyHandleTemperatureElements();
            }
        });

        // Only observe the dashboard container if it exists
        const dashboardContainer = document.querySelector('.dashboard-container');
        if (dashboardContainer) {
            observer.observe(dashboardContainer, {
                childList: true,
                subtree: true
            });
            console.log('🔍 Safe Temperature History Removal: Observer set up');
        }
    }

    // Run initialization
    init();
})();
