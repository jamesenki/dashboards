/**
 * TEMPERATURE HISTORY KILLER
 *
 * This script is designed to completely eliminate any temperature history elements
 * on the water heater details page. It uses multiple techniques:
 *
 * 1. Preemptive DOM modification to eliminate elements
 * 2. Function overriding to prevent chart initialization
 * 3. CSS injection to hide any elements that might appear
 * 4. MutationObserver to catch dynamically added elements
 */

(function() {
    console.log('🚫 Temperature History Killer: Initialized');

    // Create and inject CSS immediately to prevent any flicker
    function injectBlockingCSS() {
        const styleId = 'temperature-history-killer-css';
        if (document.getElementById(styleId)) return;

        const styleEl = document.createElement('style');
        styleEl.id = styleId;
        styleEl.innerHTML = `
            /* Target temperature history elements */
            #temperature-chart,
            .temperature-chart,
            #history,
            .tab-panel#history,
            .tab-btn[data-tab="history"],
            [data-tab="history"],
            [id*="temperature"][id*="chart"],
            [id*="temperature"][id*="history"],
            [class*="temperature"][class*="chart"],
            [class*="temperature"][class*="history"],
            .chart-container,
            .chart-wrapper {
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
                max-height: 0 !important;
                max-width: 0 !important;
                overflow: hidden !important;
                position: absolute !important;
                top: -9999px !important;
                left: -9999px !important;
                pointer-events: none !important;
                z-index: -9999 !important;
            }

            /* Target headings with Temperature History text */
            h1:contains('Temperature History'),
            h2:contains('Temperature History'),
            h3:contains('Temperature History'),
            h4:contains('Temperature History'),
            h5:contains('Temperature History'),
            h6:contains('Temperature History'),
            /* Ensure the maintenance tab is active by default instead */
            #maintenance.tab-panel {
                display: block !important;
            }
            button[data-tab="maintenance"] {
                background-color: #fff !important;
                color: #0066cc !important;
                border-bottom: 2px solid #0066cc !important;
            }
        `;
        document.head.appendChild(styleEl);
        console.log('💉 Temperature History Killer: CSS injected');
    }

    // Aggressively remove elements
    function removeTemperatureElements() {
        // Common selectors for temperature history elements
        const selectors = [
            '#temperature-chart',
            '.temperature-chart',
            '#history',
            '.tab-panel#history',
            '.tab-btn[data-tab="history"]',
            '[data-tab="history"]',
            '[id*="temperature"][id*="chart"]',
            '[class*="temperature"][class*="chart"]',
            '.chart-container',
            '.chart-wrapper'
        ];

        // Remove elements by selector
        selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                console.log(`🔥 Temperature History Killer: Removing ${selector}`);
                try {
                    el.innerHTML = '';
                    el.style.display = 'none';
                    el.remove();
                } catch (e) {
                    // Fallback if remove fails
                    el.style.visibility = 'hidden';
                    el.style.height = '0';
                    el.style.width = '0';
                }
            });
        });

        // Remove by content text
        const textPhrases = ['Temperature History', 'temperature history', 'Temp. History'];
        textPhrases.forEach(phrase => {
            document.querySelectorAll('*').forEach(el => {
                if (el.innerText && el.innerText.includes(phrase)) {
                    console.log(`🔥 Temperature History Killer: Removing element with text "${phrase}"`);
                    try {
                        el.innerHTML = '';
                        el.style.display = 'none';
                        el.remove();
                    } catch (e) {
                        // Fallback
                        el.style.visibility = 'hidden';
                        el.style.height = '0';
                        el.style.width = '0';
                    }
                }
            });
        });

        // Ensure the maintenance tab is active
        const maintenanceTab = document.querySelector('[data-tab="maintenance"]');
        const maintenancePanel = document.getElementById('maintenance');

        if (maintenanceTab) {
            // Deactivate all tabs
            document.querySelectorAll('.tab-btn').forEach(tab => {
                tab.classList.remove('active');
            });
            // Activate maintenance tab
            maintenanceTab.classList.add('active');
        }

        if (maintenancePanel) {
            // Deactivate all panels
            document.querySelectorAll('.tab-panel').forEach(panel => {
                panel.classList.remove('active');
            });
            // Activate maintenance panel
            maintenancePanel.classList.add('active');
        }
    }

    // Override initialization functions
    function overrideFunctions() {
        console.log('🛡️ Temperature History Killer: Overriding chart functions');

        // Make sure these objects exist before trying to modify them
        window.ShadowDocumentHandler = window.ShadowDocumentHandler || { prototype: {} };

        // If they exist as constructors, modify their prototypes
        if (typeof ShadowDocumentHandler === 'function') {
            // Override chart functions
            ShadowDocumentHandler.prototype.initializeCharts = function() {
                console.log('🛡️ Chart initialization blocked by Temperature History Killer');
                return null;
            };
            ShadowDocumentHandler.prototype.renderTemperatureChart = function() {
                console.log('🛡️ Chart rendering blocked by Temperature History Killer');
                return null;
            };
            ShadowDocumentHandler.prototype.updateTemperatureChart = function() {
                console.log('🛡️ Chart update blocked by Temperature History Killer');
                return null;
            };
        }

        // Override any chart constructor if it exists
        window.TemperatureHistoryChart = function() {
            console.log('🛡️ Temperature History Chart constructor blocked');
            return {
                render: function() { return null; },
                update: function() { return null; },
                destroy: function() { return null; }
            };
        };
    }

    // Set up observers to catch dynamic changes
    function setupObservers() {
        // Create a MutationObserver to watch for changes to the DOM
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length) {
                    console.log('👀 Temperature History Killer: Detected DOM changes, removing temperature elements');
                    removeTemperatureElements();
                }
            });
        });

        // Start observing
        observer.observe(document.documentElement, {
            childList: true,
            subtree: true
        });

        console.log('👀 Temperature History Killer: DOM observer active');
    }

    // Execution sequence
    function init() {
        // Immediate actions
        injectBlockingCSS();
        removeTemperatureElements();
        overrideFunctions();

        // Set up for future changes
        setupObservers();
    }

    // Run immediately for fastest removal
    init();

    // Run again when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        console.log('📄 Temperature History Killer: DOM loaded, running again');
        init();

        // Run additional times to catch any late initializations
        setTimeout(removeTemperatureElements, 100);
        setTimeout(removeTemperatureElements, 500);
    });

    // Run again when everything is loaded
    window.addEventListener('load', function() {
        console.log('🔄 Temperature History Killer: Window loaded, running final check');
        init();

        // Keep checking periodically
        setInterval(removeTemperatureElements, 1000);
    });
})();
