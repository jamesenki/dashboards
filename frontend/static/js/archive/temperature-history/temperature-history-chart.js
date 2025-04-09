/**
 * Temperature History Chart
 *
 * Displays temperature history data in a chart
 * Part of the GREEN phase implementation for our TDD cycle
 */

class TemperatureHistoryChart {
    /**
     * Initialize the temperature history chart
     * @param {string} elementId - The ID of the element to render the chart in
     * @param {Object} options - Chart options
     */
    constructor(elementId, options = {}) {
        this.elementId = elementId;
        this.chartElement = document.getElementById(elementId);
        this.errorElement = null;
        this.data = {
            labels: [],
            temperatures: []
        };

        this.options = Object.assign({
            title: 'Temperature Data', // Changed from 'Temperature History' to follow TDD principles
            color: 'rgba(3, 169, 244, 1)',
            backgroundColor: 'rgba(3, 169, 244, 0.1)',
            dataPoints: 10,
            showLegend: false,
            displayGrid: false,
            errorSelector: '.shadow-document-error'
        }, options);

        // Initialize chart
        this.findErrorElement();
        this.initializeChart();
    }

    /**
     * Find error element for displaying errors
     */
    findErrorElement() {
        // Find the closest error element to the chart
        if (this.chartElement) {
            const parent = this.chartElement.closest('.card') || this.chartElement.parentElement;
            this.errorElement = parent.querySelector(this.options.errorSelector);

            // If not found in parent, try to find globally
            if (!this.errorElement) {
                this.errorElement = document.querySelector(this.options.errorSelector);
            }

            if (!this.errorElement) {
                console.warn(`No error element found for chart ${this.elementId}, errors will not be displayed`);
            }
        }
    }

    /**
     * Initialize the chart
     */
    initializeChart() {
        if (!this.chartElement) {
            console.error(`Chart element with ID '${this.elementId}' not found`);
            return;
        }

        // Create a canvas element if needed
        let canvas = this.chartElement.querySelector('canvas');
        if (!canvas) {
            canvas = document.createElement('canvas');
            this.chartElement.appendChild(canvas);
        }

        const ctx = canvas.getContext('2d');

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.data.labels,
                datasets: [{
                    label: this.options.title,
                    data: this.data.temperatures,
                    borderColor: this.options.color,
                    backgroundColor: this.options.backgroundColor,
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 3,
                    fill: true,
                    pointBackgroundColor: this.options.color
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: this.options.showLegend
                    },
                    tooltip: {
                        enabled: true,
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: this.options.displayGrid,
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    },
                    y: {
                        beginAtZero: false,
                        grid: {
                            display: this.options.displayGrid,
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    }
                },
                animation: {
                    duration: 1000
                }
            }
        });
    }

    /**
     * Add a new data point to the chart
     * @param {number} temperature - Temperature value to add
     * @param {Date} timestamp - Optional timestamp, defaults to now
     */
    addDataPoint(temperature, timestamp = new Date()) {
        if (isNaN(temperature)) {
            console.warn('Invalid temperature value:', temperature);
            return;
        }

        // Format timestamp for display
        const label = typeof timestamp === 'string' ?
            new Date(timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) :
            timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

        // Add data to arrays
        this.data.labels.push(label);
        this.data.temperatures.push(temperature);

        // Limit the number of data points shown
        if (this.data.labels.length > this.options.dataPoints) {
            this.data.labels.shift();
            this.data.temperatures.shift();
        }

        // Update chart
        this.updateChart();
    }

    /**
     * Add a historical data point (used to populate the initial chart)
     * @param {number} temperature - Temperature value
     * @param {Date|string} timestamp - Timestamp for the data point
     */
    addHistoricalDataPoint(temperature, timestamp) {
        // Format date and time appropriately
        let label;
        if (typeof timestamp === 'string') {
            const date = new Date(timestamp);
            label = date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        } else {
            label = timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        }

        this.data.labels.push(label);
        this.data.temperatures.push(temperature);

        // Update chart
        this.updateChart();
    }

    /**
     * Update the chart with current data
     */
    updateChart() {
        if (!this.chart) {
            console.warn('Chart not initialized yet');
            return;
        }

        // Hide error if we have data
        if (this.data.temperatures.length > 0) {
            this.hideError();
        }

        // Update chart data
        this.chart.data.labels = this.data.labels;
        this.chart.data.datasets[0].data = this.data.temperatures;

        // Update chart
        this.chart.update();
    }

    /**
     * Show an error message
     * @param {string} message - Error message to display
     */
    showError(message) {
        if (this.errorElement) {
            this.errorElement.textContent = message || 'Error loading temperature data';
            this.errorElement.style.display = 'block';
        } else {
            console.error('Temperature chart error:', message);
        }

        // Hide the chart
        if (this.chartElement) {
            this.chartElement.style.display = 'none';
        }
    }

    /**
     * Hide the error message
     */
    hideError() {
        if (this.errorElement) {
            this.errorElement.style.display = 'none';
        }

        // Show the chart
        if (this.chartElement) {
            this.chartElement.style.display = 'block';
        }
    }

    /**
     * Set chart data directly (useful for testing)
     * @param {Array} labels - Array of label strings
     * @param {Array} temperatures - Array of temperature values
     */
    setData(labels, temperatures) {
        if (!Array.isArray(labels) || !Array.isArray(temperatures)) {
            console.error('Invalid data provided to temperature chart');
            return;
        }

        if (labels.length !== temperatures.length) {
            console.error('Labels and temperatures arrays must have the same length');
            return;
        }

        this.data.labels = labels;
        this.data.temperatures = temperatures;

        this.updateChart();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TemperatureHistoryChart;
}
