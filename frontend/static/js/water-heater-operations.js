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
     * @param {string} heaterId - ID of the water heater
     * @param {string} [containerId='operations-content'] - ID of the container element
     */
    constructor(heaterId, containerId = 'operations-content') {
        this.heaterId = heaterId;
        this.containerId = containerId;

        // Root container for scoped element selection
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Operations Dashboard: Container element #${this.containerId} not found`);
        }

        // Element cache for performance optimization
        this.elements = {};

        // Initialize charts container
        this.gauges = {};

        // Track initialization state
        this.initialized = false;

        // Intervals for cleanup
        this.updateInterval = null;

        // Initialize the dashboard
        this.initialize();
    }

    /**
     * Get a DOM element within the dashboard's container
     * @param {string} selector - CSS selector for the element
     * @param {boolean} [cacheResult=true] - Whether to cache the result for future use
     * @param {string} [cacheKey=null] - Key to use for caching (defaults to selector)
     * @returns {HTMLElement|null} The element or null if not found
     */
    getElement(selector, cacheResult = true, cacheKey = null) {
        const key = cacheKey || selector;

        // Return cached element if available
        if (this.elements[key]) {
            return this.elements[key];
        }

        // Try to find element within container first (scoped)
        let element = null;
        if (this.container) {
            element = this.container.querySelector(selector);
        }

        // If not found in container, try document-wide as fallback
        if (!element) {
            // Handle ID selectors specially
            if (selector.startsWith('#')) {
                const id = selector.substring(1);
                element = document.getElementById(id);
            } else {
                element = document.querySelector(selector);
            }
        }

        // Cache result if requested
        if (element && cacheResult) {
            this.elements[key] = element;
        }

        return element;
    }

    /**
     * Get all DOM elements matching a selector within the dashboard's container
     * @param {string} selector - CSS selector for the elements
     * @returns {NodeList} The matching elements
     */
    getAllElements(selector) {
        // First try container-scoped query
        if (this.container) {
            return this.container.querySelectorAll(selector);
        }

        // Fallback to document-wide
        return document.querySelectorAll(selector);
    }

    /**
     * Initialize the dashboard UI and load data
     */
    async initialize() {
        if (!this.container) {
            console.error(`Operations Dashboard: Container element #${this.containerId} not found`);
            return;
        }

        console.log(`Operations Dashboard: Initializing for water heater ${this.heaterId}`);

        // Build dashboard UI structure if not already built
        if (!this.initialized) {
            this.buildDashboardUI();
        }

        // Cache frequently accessed elements
        this.cacheElements();

        // Load initial data
        try {
            await this.loadDashboardData();
            this.initialized = true;

            // Set up periodic updates
            this.setupPeriodicUpdates();

            console.log('Operations Dashboard: Initialization complete');
        } catch (error) {
            console.error('Operations Dashboard: Initialization error', error);
            this.showError(`Failed to load dashboard data: ${error.message}`);
        }
    }

    /**
     * Cache frequently accessed DOM elements for better performance
     */
    cacheElements() {
        // Status elements
        this.elements.machineStatus = this.getElement('#machine-status-card .status-value');
        this.elements.heaterStatus = this.getElement('#heater-status-card .status-value');
        this.elements.currentTemp = this.getElement('#current-temp-card .status-value');
        this.elements.targetTemp = this.getElement('#target-temp-card .status-value');
        this.elements.modeValue = this.getElement('#mode-card .status-value');

        // Gauge elements
        this.elements.temperatureGauge = this.getElement('#temperature-gauge');
        this.elements.pressureGauge = this.getElement('#pressure-gauge');
        this.elements.flowRateGauge = this.getElement('#flow-rate-gauge');
        this.elements.energyGauge = this.getElement('#energy-gauge');

        // Error container
        this.elements.errorContainer = this.getElement('#operations-error');

        console.log('Operations Dashboard: Cached DOM elements');
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
            const response = await fetch(`/api/manufacturer/water-heaters/${this.heaterId}/operations`);
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
        console.log('🔄 COMPLETE REWRITE: Creating status cards with guaranteed no duplication');

        // CRITICAL FIX: COMPLETELY rebuild status container from scratch
        const operationsContent = document.getElementById('operations-content');
        if (!operationsContent) {
            console.error('Cannot find operations-content element');
            return;
        }

        // Find the existing status container
        let statusContainer = operationsContent.querySelector('.status-container');

        // If no container exists, create one
        if (!statusContainer) {
            statusContainer = document.createElement('div');
            statusContainer.className = 'status-container';
            operationsContent.appendChild(statusContainer);
        } else {
            // COMPLETE REBUILD: Always start with a clean slate
            statusContainer.innerHTML = '';
            console.log('⚠️ Completely cleared status container to prevent any possibility of duplication');
        }

        // Define status items to create
        const statusItems = [
            { id: 'machine-status', label: 'Machine Status', value: data.machine_status },
            { id: 'heater-status', label: 'Heater Status', value: data.heater_status },
            { id: 'current-temp', label: 'Current Temp', value: this.formatTemperature(data.current_temperature) },
            { id: 'target-temp', label: 'Target Temp', value: this.formatTemperature(data.target_temperature) },
            { id: 'mode', label: 'Mode', value: data.mode }
        ];

        // Create each status item from scratch
        statusItems.forEach(item => {
            const statusItem = document.createElement('div');
            statusItem.id = `${item.id}-card`;
            statusItem.className = 'status-item';

            const labelElement = document.createElement('div');
            labelElement.className = 'status-label';
            labelElement.textContent = item.label;

            const valueElement = document.createElement('div');
            valueElement.className = 'status-value';
            valueElement.textContent = item.value;

            // Add appropriate status class
            if (item.id === 'machine-status') {
                if (item.value === 'ONLINE') valueElement.classList.add('online');
                else if (item.value === 'OFFLINE') valueElement.classList.add('offline');
                else valueElement.classList.add('warning');
            }
            else if (item.id === 'heater-status') {
                if (item.value === 'HEATING') valueElement.classList.add('online');
                else if (item.value === 'STANDBY') valueElement.classList.add('warning');
                else valueElement.classList.add('offline');
            }

            statusItem.appendChild(labelElement);
            statusItem.appendChild(valueElement);
            statusContainer.appendChild(statusItem);
        });

        console.log(`✅ Successfully created exactly 5 status items`);

        // VERIFICATION: Double-check for any duplication
        setTimeout(() => {
            const allStatusItems = document.querySelectorAll('.status-item');
            if (allStatusItems.length !== 5) {
                console.error(`⚠️ CRITICAL ERROR: Found ${allStatusItems.length} status items (expected exactly 5)`);

                // Last resort nuclear option to fix any remaining duplication
                const statusContainers = document.querySelectorAll('.status-container');
                if (statusContainers.length > 1) {
                    console.warn(`⚠️ Multiple status containers found (${statusContainers.length}) - fixing this issue`);

                    // Keep only the first container, remove all others
                    for (let i = 1; i < statusContainers.length; i++) {
                        statusContainers[i].remove();
                    }
                }
            }
        }, 100);
    }

    /**
     * Update a status card with data
     * @param {string} cardId - ID prefix of the card element
     * @param {string} title - Title for the card
     * @param {string} value - Value to display
     */
    updateStatusCard(cardId, title, value) {
        // Use our scoped element selection to prevent multiple updates to the same element
        const card = this.getElement(`#${cardId}-card`);
        if (!card) return;

        // Find the value element within our scoped element
        const valueElement = card.querySelector('.status-value');
        if (!valueElement) return;

        // Clean existing content first to prevent duplication
        valueElement.innerHTML = '';

        // Set new content
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
        // Use our scoped element selection to ensure we get the right elements
        // and prevent duplicate updates
        const valueElement = this.getElement(`#${gaugeId}-gauge-value`);
        if (valueElement) {
            // Format value based on type
            let displayValue;
            if (typeof value === 'number') {
                // Format with 1 decimal place if it has a fractional part
                displayValue = Number.isInteger(value) ? value.toString() : value.toFixed(1);
            } else {
                displayValue = value || '--';
            }

            // Clear existing content first to prevent duplication
            valueElement.innerHTML = '';
            valueElement.textContent = `${displayValue}${unit}`;
        }

        // Update gauge needle position using scoped selection
        const needleElement = this.getElement(`#${gaugeId}-gauge-needle`);
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
        // Use cached element or find it
        const errorElement = this.elements.errorContainer || this.getElement('#operations-error');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';

            // Hide after 5 seconds
            setTimeout(() => {
                errorElement.style.display = 'none';
            }, 5000);
        }
        console.error('Operations Dashboard Error:', message);
    }

    /**
     * Setup periodic updates for real-time data
     */
    setupPeriodicUpdates() {
        // Clear any existing interval first
        this.clearUpdateInterval();

        // Only set up interval if we're the active tab
        if (window.tabManager && window.tabManager.getActiveTabId() === 'operations') {
            console.log('Operations Dashboard: Setting up periodic updates (30s interval)');

            // Update every 30 seconds
            this.updateInterval = setInterval(() => {
                // Only fetch data if this tab is still active
                if (window.tabManager && window.tabManager.getActiveTabId() === 'operations') {
                    this.loadDashboardData().catch(error => {
                        console.error('Error during periodic update:', error);
                    });
                } else {
                    // If no longer active, clear the interval
                    console.log('Operations Dashboard: No longer active, clearing update interval');
                    this.clearUpdateInterval();
                }
            }, 30000);
        }
    }

    /**
     * Clear the update interval
     */
    clearUpdateInterval() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
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
        console.log('Operations Dashboard: Cleaning up resources');

        // Clear update interval
        this.clearUpdateInterval();

        // Clear gauge objects
        Object.values(this.gauges).forEach(gauge => {
            if (gauge && typeof gauge.destroy === 'function') {
                gauge.destroy();
            }
        });
        this.gauges = {};

        // Clear element cache
        this.elements = {};
    }

    /**
     * TabManager reload method - Called when the Operations tab is activated
     * @returns {boolean} Success status
     */
    reload() {
        // COMPLETE FIX: Guarantee there are no duplicate status items when tab is activated
        console.log('🔥 NUCLEAR OPTION: Ensuring zero possibility of status duplication');

        // 1. Find all status containers across the entire document
        const allStatusContainers = document.querySelectorAll('.status-container');
        if (allStatusContainers.length > 1) {
            console.warn(`⚠️ Found ${allStatusContainers.length} status containers - removing all but the first`);
            // Keep only the first container, remove all others
            for (let i = 1; i < allStatusContainers.length; i++) {
                allStatusContainers[i].remove();
            }
        }

        // 2. Get the remaining status container
        const statusContainer = document.querySelector('.status-container');
        if (statusContainer) {
            // Always clear the container completely
            statusContainer.innerHTML = '';
            console.log('✅ Status container completely cleared');
        } else {
            console.log('👀 No status container found yet, will be created during update');
        }

        // 3. Clean up any stray status items that might exist outside containers
        const strayStatusItems = document.querySelectorAll('.status-item');
        if (strayStatusItems.length > 0) {
            console.warn(`⚠️ Found ${strayStatusItems.length} stray status items - removing all`);
            strayStatusItems.forEach(item => item.remove());
        }
        console.log('Operations Dashboard: Reload method called by TabManager');

        try {
            // Only proceed if this is the active tab
            if (window.tabManager && window.tabManager.getActiveTabId() !== 'operations') {
                console.log('Operations Dashboard: Not the active tab, aborting reload');
                // Clear any update intervals if we're not the active tab
                this.clearUpdateInterval();
                return true;
            }

            // Clear any existing intervals first to prevent duplicates
            this.clearUpdateInterval();

            // Force clean the UI to prevent duplication
            // Reset status cards to loading state
            const statusValues = this.getAllElements('.status-value');
            statusValues.forEach(el => {
                el.textContent = 'Loading...';
                el.classList.remove('online', 'offline', 'warning');
            });

            // Reset gauge values
            const gaugeValues = this.getAllElements('.gauge-value');
            gaugeValues.forEach(el => {
                el.textContent = '--';
            });

            // Reset gauge needles
            const gaugeNeedles = this.getAllElements('.gauge-needle');
            gaugeNeedles.forEach(el => {
                el.style.transform = 'rotate(-90deg)';
            });

            // Safe initialization check
            const safeInitialized = this.initialized === true;
            console.log(`Operations Dashboard: Initialization status: ${safeInitialized ? 'Initialized' : 'Not initialized'}`);

            // Reload dashboard data - this is a defensive implementation
            // that will work even if the initialization state is incorrect
            if (safeInitialized && typeof this.loadDashboardData === 'function') {
                // If already initialized, just refresh data
                console.log('Operations Dashboard: Refreshing data for initialized dashboard');
                // Add a small delay to ensure UI is reset before loading new data
                setTimeout(() => {
                    this.loadDashboardData().catch(error => {
                        console.error('Operations Dashboard: Error reloading data', error);
                        this.showError('Failed to refresh operations data');
                    });

                    // Restart periodic updates
                    if (typeof this.setupPeriodicUpdates === 'function') {
                        this.setupPeriodicUpdates();
                    }
                }, 50);
            } else {
                // If not initialized or in an uncertain state, do full initialization
                console.log('Operations Dashboard: Performing full initialization');
                if (typeof this.initialize === 'function') {
                    this.initialize().catch(error => {
                        console.error('Operations Dashboard: Error during initialization', error);
                    });
                } else {
                    console.error('Operations Dashboard: Initialize method not found');
                }
            }

            return true; // Indicate successful reload attempt
        } catch (error) {
            console.error('Operations Dashboard: Critical error in reload method:', error);
            // Try recovery
            setTimeout(() => {
                console.log('Operations Dashboard: Attempting recovery initialization');
                try {
                    this.initialize();
                } catch (e) {
                    console.error('Operations Dashboard: Recovery failed', e);
                }
            }, 500);
            return false;
        }
    }
}

// Export for use in other modules
window.WaterHeaterOperationsDashboard = WaterHeaterOperationsDashboard;
