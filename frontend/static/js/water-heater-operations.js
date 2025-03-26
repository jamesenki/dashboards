/**
 * Water Heater Operations Dashboard
 * 
 * This module manages the operations dashboard for water heaters,
 * displaying real-time operational data including temperature, pressure,
 * energy usage, and flow rate using gauge visualizations.
 */

class WaterHeaterOperationsDashboard {
    /**
     * Initialize the operations dashboard
     * @param {string} containerId - ID of the container element
     * @param {string} heaterId - ID of the water heater
     */
    constructor(containerId, heaterId) {
        this.containerId = containerId;
        this.heaterId = heaterId;
        this.container = document.getElementById(containerId);
        this.initialized = false;
        
        // Initialize the dashboard
        this.initialize();
    }
    
    /**
     * Initialize the dashboard UI and load data
     */
    async initialize() {
        if (!this.container) {
            console.error(`Container element #${this.containerId} not found`);
            return;
        }
        
        // Build dashboard UI structure
        this.buildDashboardUI();
        
        // Load initial data
        try {
            await this.loadDashboardData();
            this.initialized = true;
            
            // Set up periodic updates
            this.setupPeriodicUpdates();
        } catch (error) {
            this.showError(`Failed to load dashboard data: ${error.message}`);
        }
    }
    
    /**
     * Build the dashboard UI structure
     */
    buildDashboardUI() {
        this.container.innerHTML = `
            <div id="operations-dashboard" class="operations-dashboard dark-theme">
                <h2>Operations Dashboard</h2>
                
                <!-- Status Cards Section -->
                <div class="status-section">
                    <h3>Status</h3>
                    <div class="status-grid">
                        <div id="machine-status-card" class="status-item">
                            <div class="status-label">Machine Status</div>
                            <div class="status-value online">Loading...</div>
                        </div>
                        <div id="heater-status-card" class="status-item">
                            <div class="status-label">Heater Status</div>
                            <div class="status-value">Loading...</div>
                        </div>
                        <div id="current-temp-card" class="status-item">
                            <div class="status-label">Current Temp</div>
                            <div class="status-value">Loading...</div>
                        </div>
                        <div id="target-temp-card" class="status-item">
                            <div class="status-label">Target Temp</div>
                            <div class="status-value">Loading...</div>
                        </div>
                        <div id="mode-card" class="status-item">
                            <div class="status-label">Mode</div>
                            <div class="status-value">Loading...</div>
                        </div>
                    </div>
                </div>
                
                <!-- Gauges Section -->
                <div class="operations-section">
                    <h3>Operational Metrics</h3>
                    <div class="gauge-grid">
                        <!-- Asset Health Gauge -->
                        <div id="asset-health-gauge-panel" class="gauge-panel">
                            <div class="gauge-title">Asset Health</div>
                            <div class="gauge-container">
                                <div class="gauge-needle" id="asset-health-gauge-needle"></div>
                            </div>
                            <div id="asset-health-gauge-value" class="gauge-value">--</div>
                        </div>
                        
                        <!-- Temperature Gauge -->
                        <div id="temperature-gauge-panel" class="gauge-panel">
                            <div class="gauge-title">Temperature</div>
                            <div class="gauge-container">
                                <div class="gauge-needle" id="temperature-gauge-needle"></div>
                            </div>
                            <div id="temperature-gauge-value" class="gauge-value">--</div>
                        </div>
                        
                        <!-- Pressure Gauge -->
                        <div id="pressure-gauge-panel" class="gauge-panel">
                            <div class="gauge-title">Pressure</div>
                            <div class="gauge-container">
                                <div class="gauge-needle" id="pressure-gauge-needle"></div>
                            </div>
                            <div id="pressure-gauge-value" class="gauge-value">--</div>
                        </div>
                        
                        <!-- Energy Usage Gauge -->
                        <div id="energy-gauge-panel" class="gauge-panel">
                            <div class="gauge-title">Energy Usage</div>
                            <div class="gauge-container">
                                <div class="gauge-needle" id="energy-gauge-needle"></div>
                            </div>
                            <div id="energy-gauge-value" class="gauge-value">--</div>
                        </div>
                        
                        <!-- Flow Rate Gauge -->
                        <div id="flow-rate-gauge-panel" class="gauge-panel">
                            <div class="gauge-title">Flow Rate</div>
                            <div class="gauge-container">
                                <div class="gauge-needle" id="flow-rate-gauge-needle"></div>
                            </div>
                            <div id="flow-rate-gauge-value" class="gauge-value">--</div>
                        </div>
                    </div>
                </div>
                
                <!-- Error message container -->
                <div id="operations-error" class="error-message" style="display: none;">
                    Error loading operations data. Please try again later.
                </div>
            </div>
        `;
    }
    
    /**
     * Load dashboard data from the API
     */
    async loadDashboardData() {
        try {
            const response = await fetch(`/api/water-heaters/${this.heaterId}/operations`);
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const data = await response.json();
            this.updateDashboard(data);
            return data;
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showError(`Failed to load data: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * Update the dashboard with data
     * @param {Object} data - Dashboard data from API
     */
    updateDashboard(data) {
        if (!data) {
            this.showError('No data received from server');
            return;
        }
        
        // Update status cards
        this.updateStatusCards(data);
        
        // Update gauge displays
        this.updateGauges(data);
    }
    
    /**
     * Update status cards with data
     * @param {Object} data - Dashboard data
     */
    updateStatusCards(data) {
        // Update machine status
        this.updateStatusCard('machine-status', 'Machine Status', data.machine_status);
        
        // Update heater status
        this.updateStatusCard('heater-status', 'Heater Status', data.heater_status);
        
        // Update current temperature
        this.updateStatusCard('current-temp', 'Current Temp', 
            this.formatTemperature(data.current_temperature));
        
        // Update target temperature
        this.updateStatusCard('target-temp', 'Target Temp', 
            this.formatTemperature(data.target_temperature));
        
        // Update mode
        this.updateStatusCard('mode', 'Mode', data.mode);
    }
    
    /**
     * Update a status card with data
     * @param {string} cardId - ID prefix of the card element
     * @param {string} title - Title for the card
     * @param {string} value - Value to display
     */
    updateStatusCard(cardId, title, value) {
        const card = document.getElementById(`${cardId}-card`);
        if (!card) return;
        
        const valueElement = card.querySelector('.status-value');
        if (valueElement) {
            valueElement.textContent = value;
            
            // Update classes based on value
            valueElement.classList.remove('online', 'offline', 'warning');
            
            // Add appropriate status class
            if (cardId === 'machine-status') {
                if (value === 'ONLINE') valueElement.classList.add('online');
                else if (value === 'OFFLINE') valueElement.classList.add('offline');
                else valueElement.classList.add('warning');
            }
            else if (cardId === 'heater-status') {
                if (value === 'HEATING') valueElement.classList.add('online');
                else if (value === 'STANDBY') valueElement.classList.add('warning');
                else valueElement.classList.add('offline');
            }
        }
    }
    
    /**
     * Update gauge displays with data
     * @param {Object} data - Dashboard data
     */
    updateGauges(data) {
        // Get gauge data
        const gauges = data.gauges || {};
        
        // Update temperature gauge
        if (gauges.temperature) {
            this.updateGauge('temperature', 
                gauges.temperature.value, 
                gauges.temperature.unit, 
                gauges.temperature.percentage);
        }
        
        // Update pressure gauge
        if (gauges.pressure) {
            this.updateGauge('pressure', 
                gauges.pressure.value, 
                gauges.pressure.unit, 
                gauges.pressure.percentage);
        }
        
        // Update energy usage gauge
        if (gauges.energy_usage) {
            this.updateGauge('energy', 
                gauges.energy_usage.value, 
                gauges.energy_usage.unit, 
                gauges.energy_usage.percentage);
        }
        
        // Update flow rate gauge
        if (gauges.flow_rate) {
            this.updateGauge('flow-rate', 
                gauges.flow_rate.value, 
                gauges.flow_rate.unit, 
                gauges.flow_rate.percentage);
        }
        
        // Update asset health gauge
        if (data.asset_health !== undefined) {
            this.updateGauge('asset-health', 
                Math.round(data.asset_health), 
                '%', 
                data.asset_health);
        }
    }
    
    /**
     * Update a gauge with data
     * @param {string} gaugeId - ID prefix of the gauge element
     * @param {number} value - Value to display
     * @param {string} unit - Unit to display after value
     * @param {number} percentage - Percentage for gauge needle (0-100)
     */
    updateGauge(gaugeId, value, unit, percentage) {
        // Update gauge value
        const valueElement = document.getElementById(`${gaugeId}-gauge-value`);
        if (valueElement) {
            // Format value based on type
            let displayValue;
            if (typeof value === 'number') {
                // Format with 1 decimal place if it has a fractional part
                displayValue = Number.isInteger(value) ? value.toString() : value.toFixed(1);
            } else {
                displayValue = value || '--';
            }
            
            valueElement.textContent = `${displayValue}${unit}`;
        }
        
        // Update gauge needle position
        const needleElement = document.getElementById(`${gaugeId}-gauge-needle`);
        if (needleElement) {
            // Limit percentage to valid range
            const limitedPercentage = Math.max(0, Math.min(100, percentage));
            
            // Convert percentage to angle (0% = -90°, 100% = 90°)
            const angle = -90 + (limitedPercentage * 1.8);
            
            // Apply rotation
            needleElement.style.transform = `rotate(${angle}deg)`;
        }
    }
    
    /**
     * Show error message
     * @param {string} message - Error message to display
     */
    showError(message) {
        const errorElement = document.getElementById('operations-error');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
        console.error('Operations Dashboard Error:', message);
    }
    
    /**
     * Setup periodic updates for real-time data
     */
    setupPeriodicUpdates() {
        // Update every 30 seconds
        this.updateInterval = setInterval(() => {
            this.loadDashboardData().catch(error => {
                console.error('Error during periodic update:', error);
            });
        }, 30000);
    }
    
    /**
     * Format temperature for display
     * @param {number} temp - Temperature value
     * @returns {string} Formatted temperature string
     */
    formatTemperature(temp) {
        return temp !== null && temp !== undefined ? `${temp.toFixed(1)}°C` : 'N/A';
    }
    
    /**
     * Clean up resources (e.g., when component is destroyed)
     */
    destroy() {
        // Clear update interval
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Export for use in other modules
window.WaterHeaterOperationsDashboard = WaterHeaterOperationsDashboard;
