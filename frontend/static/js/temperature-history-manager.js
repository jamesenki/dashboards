/**
 * Temperature History Manager
 *
 * A clean, optimized implementation for handling temperature history data
 * that follows best practices:
 *
 * 1. Lazy loading - only load data when needed (tab activation)
 * 2. Server-side processing - use optimized endpoints with aggregation
 * 3. Proper memory management - clean up charts and data when not in use
 * 4. Clear separation of concerns - follows TDD principles
 *
 * This implementation intentionally:
 * - DOES NOT show temperature history on the details page (per tests)
 * - DOES show temperature history on the history tab
 * - Properly handles error conditions including missing shadow documents
 */

class TemperatureHistoryManager {
    /**
     * Initialize the temperature history manager
     * @param {string} deviceId - The device ID
     * @param {Object} options - Configuration options
     */
    constructor(deviceId, options = {}) {
        this.deviceId = deviceId;
        this.options = Object.assign({
            historyTabSelector: '#history',
            detailsContainerSelector: '.dashboard-container',
            chartContainerSelector: '#temperature-chart-container',
            dayButtonClass: 'day-selector-btn',
            activeDayClass: 'active',
            errorMessageClass: 'chart-error-message',
            loadingClass: 'chart-loading',
            days: 7, // Default to 7 days of history
            resolution: 'hourly',
            chartOptions: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 500
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            tooltipFormat: 'MMM dd, yyyy HH:mm',
                            displayFormats: {
                                hour: 'MMM dd, HH:mm',
                                day: 'MMM dd'
                            }
                        },
                        title: {
                            display: true,
                            text: 'Date/Time'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Temperature (°F)'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Temperature: ${context.parsed.y.toFixed(1)}°F`;
                            }
                        }
                    }
                }
            }
        }, options);

        // Chart instance
        this.chart = null;
        this.chartData = [];
        this.isInitialized = false;

        // Register with tab manager if available
        this.registerWithTabManager();

        // Check if we should hide temperature history on details page
        this.hideOnDetailsPage();

        // Initialize on DOM ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initialize());
        } else {
            this.initialize();
        }
    }

    /**
     * Register with the tab manager to handle activation/deactivation
     */
    registerWithTabManager() {
        // If window.tabManager exists, register this component
        if (window.tabManager) {
            window.tabManager.registerComponent('history', {
                reload: () => this.loadData(),
                activate: () => this.onTabActivate(),
                deactivate: () => this.onTabDeactivate()
            });
            console.log('TemperatureHistoryManager: Registered with TabManager');
        } else {
            // If TabManager doesn't exist, set up basic tab click listener
            document.addEventListener('DOMContentLoaded', () => {
                const tabButtons = document.querySelectorAll('.tab-btn');
                tabButtons.forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        const tabId = e.target.getAttribute('data-tab');
                        if (tabId === 'history') {
                            this.onTabActivate();
                        } else {
                            this.onTabDeactivate();
                        }
                    });
                });
            });
        }
    }

    /**
     * Initialize the chart and day selector buttons
     */
    initialize() {
        // Don't initialize immediately - wait for tab activation
        this.isInitialized = true;
        console.log('TemperatureHistoryManager: Initialized, waiting for tab activation');
    }

    /**
     * Create the chart if it doesn't exist
     */
    createChart() {
        const historyTab = document.querySelector(this.options.historyTabSelector);
        if (!historyTab) return;

        let chartContainer = historyTab.querySelector(this.options.chartContainerSelector);

        // If chart container doesn't exist, create it
        if (!chartContainer) {
            chartContainer = document.createElement('div');
            chartContainer.id = this.options.chartContainerSelector.replace('#', '');
            chartContainer.className = 'chart-container';
            chartContainer.style.height = '400px';
            chartContainer.style.width = '100%';
            chartContainer.style.position = 'relative';

            // Create a loading indicator
            const loadingDiv = document.createElement('div');
            loadingDiv.className = this.options.loadingClass;
            loadingDiv.textContent = 'Loading temperature history...';
            loadingDiv.style.textAlign = 'center';
            loadingDiv.style.padding = '20px';
            chartContainer.appendChild(loadingDiv);

            // Create an error message container (hidden by default)
            const errorDiv = document.createElement('div');
            errorDiv.className = this.options.errorMessageClass;
            errorDiv.style.display = 'none';
            errorDiv.style.color = '#e85600';
            errorDiv.style.textAlign = 'center';
            errorDiv.style.padding = '20px';
            chartContainer.appendChild(errorDiv);

            // Create day selector buttons
            const daySelector = document.createElement('div');
            daySelector.className = 'day-selector';
            daySelector.style.marginBottom = '20px';
            daySelector.style.textAlign = 'center';

            const createDayButton = (days, label) => {
                const btn = document.createElement('button');
                btn.className = `${this.options.dayButtonClass} ${days === this.options.days ? this.options.activeDayClass : ''}`;
                btn.setAttribute('data-days', days);
                btn.textContent = label;
                btn.style.margin = '0 5px';
                btn.style.padding = '5px 10px';
                btn.style.border = '1px solid #ddd';
                btn.style.borderRadius = '4px';
                btn.style.background = days === this.options.days ? '#5755d9' : '#fff';
                btn.style.color = days === this.options.days ? '#fff' : '#333';
                btn.addEventListener('click', () => this.changeDays(days));
                return btn;
            };

            daySelector.appendChild(createDayButton(7, '7 Days'));
            daySelector.appendChild(createDayButton(14, '14 Days'));
            daySelector.appendChild(createDayButton(30, '30 Days'));

            // Create canvas for the chart
            const canvas = document.createElement('canvas');
            canvas.id = 'temperature-chart';
            chartContainer.appendChild(daySelector);
            chartContainer.appendChild(canvas);

            // Add to the history tab
            historyTab.appendChild(chartContainer);
        }

        // Create the chart
        const ctx = document.getElementById('temperature-chart').getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'Temperature',
                    data: [],
                    borderColor: '#e85600',
                    backgroundColor: 'rgba(232, 86, 0, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.2
                }]
            },
            options: this.options.chartOptions
        });

        console.log('TemperatureHistoryManager: Chart created');
    }

    /**
     * Load temperature history data from the API
     */
    async loadData() {
        if (!this.chart) {
            this.createChart();
        }

        // Show loading indicator
        const loadingDiv = document.querySelector(`.${this.options.loadingClass}`);
        if (loadingDiv) loadingDiv.style.display = 'block';

        // Hide error message
        const errorDiv = document.querySelector(`.${this.options.errorMessageClass}`);
        if (errorDiv) errorDiv.style.display = 'none';

        try {
            // Use the new optimized endpoint
            const response = await fetch(`/api/temperature-history/${this.deviceId}?days=${this.options.days}&resolution=${this.options.resolution}`);

            if (!response.ok) {
                throw new Error(`Failed to fetch temperature history: ${response.statusText}`);
            }

            const data = await response.json();

            // Check if we got a specific error about missing shadow document
            if (data.error === 'NO_SHADOW_DOCUMENT') {
                console.log('No shadow document exists for this device');

                // Show a user-friendly error message
                if (errorDiv) {
                    errorDiv.innerHTML = `<div class="shadow-error">
                        <h4>No Temperature History Available</h4>
                        <p>This device doesn't have a shadow document, which is required for temperature history.</p>
                        <p>This typically occurs when a device hasn't reported any temperature data yet.</p>
                    </div>`;
                    errorDiv.style.display = 'block';
                }

                // Hide loading indicator
                if (loadingDiv) loadingDiv.style.display = 'none';

                // Clear chart data
                if (this.chart) {
                    this.chart.data.datasets[0].data = [];
                    this.chart.update();
                }
                return;
            }

            // Update chart with the new data
            this.updateChart(data);

            // Hide loading indicator
            if (loadingDiv) loadingDiv.style.display = 'none';

        } catch (error) {
            console.error('Error loading temperature history:', error);

            // Show error message
            if (errorDiv) {
                errorDiv.textContent = `Error loading temperature history: ${error.message}`;
                errorDiv.style.display = 'block';
            }

            // Hide loading indicator
            if (loadingDiv) loadingDiv.style.display = 'none';

            // Clear chart data
            if (this.chart) {
                this.chart.data.datasets[0].data = [];
                this.chart.update();
            }
        }
    }

    /**
     * Update the chart with new data
     * @param {Object} data - The temperature history data
     */
    updateChart(data) {
        if (!this.chart || !data || !data.data) return;

        // Convert data to chart format
        const chartData = data.data.map(point => ({
            x: new Date(point.timestamp),
            y: point.temperature
        }));

        // Update chart data
        this.chart.data.datasets[0].data = chartData;

        // Update chart title based on resolution
        let titleText = `Temperature History - Last ${this.options.days} Days`;
        if (this.options.resolution === 'hourly') {
            titleText += ' (Hourly Average)';
        } else if (this.options.resolution === 'daily') {
            titleText += ' (Daily Average)';
        }

        // Update chart options
        this.chart.options.plugins.title = {
            display: true,
            text: titleText,
            font: {
                size: 16
            }
        };

        // Update chart
        this.chart.update();
        console.log(`TemperatureHistoryManager: Chart updated with ${chartData.length} data points`);
    }

    /**
     * Change the number of days to display
     * @param {number} days - Number of days (7, 14, or 30)
     */
    changeDays(days) {
        if (this.options.days === days) return;

        // Update active button
        document.querySelectorAll(`.${this.options.dayButtonClass}`).forEach(btn => {
            const btnDays = parseInt(btn.getAttribute('data-days'));
            btn.classList.toggle(this.options.activeDayClass, btnDays === days);
            btn.style.background = btnDays === days ? '#5755d9' : '#fff';
            btn.style.color = btnDays === days ? '#fff' : '#333';
        });

        // Update days option
        this.options.days = days;

        // Update resolution based on days
        if (days === 30) {
            this.options.resolution = 'daily';
        } else {
            this.options.resolution = 'hourly';
        }

        // Reload data
        this.loadData();
    }

    /**
     * Handle tab activation
     */
    onTabActivate() {
        console.log('TemperatureHistoryManager: History tab activated');

        // Load data if chart doesn't exist or is empty
        if (!this.chart || this.chart.data.datasets[0].data.length === 0) {
            this.loadData();
        }
    }

    /**
     * Handle tab deactivation
     */
    onTabDeactivate() {
        // No need to destroy the chart, just let it be
        console.log('TemperatureHistoryManager: History tab deactivated');
    }

    /**
     * Destroy the chart and clean up
     */
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }

    /**
     * Hide temperature history on details page but not on history tab
     * Follows TDD requirements to remove temperature history from details page
     */
    hideOnDetailsPage() {
        // Only hide on details page, not history tab
        const isDetailsPage = window.location.pathname.includes('/water-heaters/') &&
                             !window.location.pathname.includes('/history');

        if (isDetailsPage) {
            console.log('TemperatureHistoryManager: Hiding temperature history on details page');

            // Create and insert CSS to hide temperature charts on details page
            const style = document.createElement('style');
            style.textContent = `
                /* Hide temperature charts on details page per TDD requirements */
                .dashboard-container #temperature-chart,
                .dashboard-container .temperature-chart,
                .dashboard-container [id*="temperature"][id*="chart"],
                .dashboard-container .chart-container,
                .dashboard-container .chart-wrapper {
                    display: none !important;
                }
            `;
            document.head.appendChild(style);
        }
    }
}

// Initialize the manager
document.addEventListener('DOMContentLoaded', () => {
    // Extract device ID from URL
    const deviceId = window.location.pathname.split('/').pop();

    if (deviceId && deviceId.startsWith('wh-')) {
        // Create temperature history manager
        window.temperatureHistoryManager = new TemperatureHistoryManager(deviceId);
    }
});
