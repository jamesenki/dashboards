/**
 * Water Heater History Dashboard functionality
 * Handles loading and displaying historical data for water heaters
 */

class WaterHeaterHistoryDashboard {
    /**
     * Initialize the history dashboard
     * @param {string} heaterId - The ID of the water heater
     */
    constructor(heaterId) {
        this.heaterId = heaterId;
        this.api = new ApiClient();
        
        // Default number of days to display
        this.days = 7;
        
        // Chart references
        this.temperatureChart = null;
        this.energyUsageChart = null;
        this.pressureFlowChart = null;
        
        // Initialize dashboard
        this.initDashboard();
    }
    
    /**
     * Initialize the dashboard elements and load data
     */
    async initDashboard() {
        console.log(`Initializing history dashboard for water heater ${this.heaterId}`);
        
        // Set up event listeners for day selectors
        this.setupDaySelectors();
        
        // Load initial data
        await this.loadHistoryData();
    }
    
    /**
     * Setup event listeners for day selectors
     */
    setupDaySelectors() {
        const daySelectors = document.querySelectorAll('.day-selector');
        daySelectors.forEach(selector => {
            selector.addEventListener('click', async (e) => {
                e.preventDefault();
                
                // Update active class
                daySelectors.forEach(el => el.classList.remove('active'));
                selector.classList.add('active');
                
                // Get selected days
                this.days = parseInt(selector.getAttribute('data-days'));
                
                // Reload data with new time range
                await this.loadHistoryData();
            });
        });
    }
    
    /**
     * Load history data from the API
     */
    async loadHistoryData() {
        try {
            // Show loading indicators
            this.showLoading(true);
            
            // Get history data from API
            const historyData = await this.api.request('GET', `/water-heaters/${this.heaterId}/history?days=${this.days}`);
            
            // Update charts
            this.updateCharts(historyData);
            
            // Hide loading indicators
            this.showLoading(false);
        } catch (error) {
            console.error('Error loading history data:', error);
            this.showError('Failed to load history data. Please try again later.');
            this.showLoading(false);
        }
    }
    
    /**
     * Update all charts with new data
     * @param {Object} historyData - The history data from the API
     */
    updateCharts(historyData) {
        // Update temperature chart
        this.updateTemperatureChart(historyData.temperature);
        
        // Update energy usage chart
        this.updateEnergyUsageChart(historyData.energy_usage);
        
        // Update pressure and flow rate chart
        this.updatePressureFlowChart(historyData.pressure_flow);
    }
    
    /**
     * Update the temperature chart
     * @param {Object} chartData - The chart data for temperature
     */
    updateTemperatureChart(chartData) {
        const canvas = document.getElementById('temperature-chart');
        if (!canvas) {
            console.error('Temperature chart canvas not found');
            this.showError('Chart rendering error. Please refresh the page.');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart if it exists
        if (this.temperatureChart) {
            this.temperatureChart.destroy();
        }
        
        // Create new chart
        this.temperatureChart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Temperature History',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Temperature (°C)'
                        },
                        min: 30,
                        max: 90
                    }
                }
            }
        });
    }
    
    /**
     * Update the energy usage chart
     * @param {Object} chartData - The chart data for energy usage
     */
    updateEnergyUsageChart(chartData) {
        const canvas = document.getElementById('energy-usage-chart');
        if (!canvas) {
            console.error('Energy usage chart canvas not found');
            this.showError('Chart rendering error. Please refresh the page.');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart if it exists
        if (this.energyUsageChart) {
            this.energyUsageChart.destroy();
        }
        
        // Create new chart
        this.energyUsageChart = new Chart(ctx, {
            type: 'bar',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Energy Usage History',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Energy Usage (W)'
                        },
                        min: 0
                    }
                }
            }
        });
    }
    
    /**
     * Update the pressure and flow rate chart
     * @param {Object} chartData - The chart data for pressure and flow rate
     */
    updatePressureFlowChart(chartData) {
        const canvas = document.getElementById('pressure-flow-chart');
        if (!canvas) {
            console.error('Pressure flow chart canvas not found');
            this.showError('Chart rendering error. Please refresh the page.');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart if it exists
        if (this.pressureFlowChart) {
            this.pressureFlowChart.destroy();
        }
        
        // Create new chart
        this.pressureFlowChart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Pressure and Flow Rate History',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Pressure (bar)'
                        },
                        min: 0,
                        max: 5
                    },
                    y1: {
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Flow Rate (L/min)'
                        },
                        min: 0,
                        max: 10,
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Show or hide loading indicators
     * @param {boolean} isLoading - Whether data is loading
     */
    showLoading(isLoading) {
        const loadingIndicators = document.querySelectorAll('.chart-loading');
        const chartContainers = document.querySelectorAll('.chart-container');
        
        if (isLoading) {
            // Show loading indicators
            loadingIndicators.forEach(indicator => {
                indicator.style.display = 'flex';
            });
            
            // Hide chart containers
            chartContainers.forEach(container => {
                container.style.opacity = '0.5';
            });
        } else {
            // Hide loading indicators
            loadingIndicators.forEach(indicator => {
                indicator.style.display = 'none';
            });
            
            // Show chart containers
            chartContainers.forEach(container => {
                container.style.opacity = '1';
            });
        }
    }
    
    /**
     * Show an error message
     * @param {string} message - The error message to display
     */
    showError(message) {
        const errorContainer = document.getElementById('history-error');
        if (errorContainer) {
            errorContainer.textContent = message;
            errorContainer.style.display = 'block';
            
            // Hide after 5 seconds
            setTimeout(() => {
                errorContainer.style.display = 'none';
            }, 5000);
        }
    }
}

// Initialize the dashboard when the tab is clicked
document.addEventListener('DOMContentLoaded', function() {
    // Get the history tab button
    const historyTabBtn = document.getElementById('history-tab-btn');
    if (historyTabBtn) {
        historyTabBtn.addEventListener('click', function() {
            const heaterId = document.body.getAttribute('data-heater-id');
            if (heaterId && window.waterHeaterHistoryDashboard === undefined) {
                // Initialize dashboard only once
                window.waterHeaterHistoryDashboard = new WaterHeaterHistoryDashboard(heaterId);
            }
        });
    }
});
