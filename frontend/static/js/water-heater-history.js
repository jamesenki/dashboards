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
        
        // Root container for scoped element selection
        this.container = document.getElementById('water-heater-history-dashboard');
        if (!this.container) {
            console.error('History Dashboard: Could not find root container');
        }
        
        // Cache DOM elements for performance
        this.elements = {};
        
        // Initialize dashboard
        this.initDashboard();
    }
    
    /**
     * Get a DOM element within the dashboard's container
     * @param {string} selector - CSS selector for the element
     * @param {boolean} cacheResult - Whether to cache the result for future use
     * @param {string} cacheKey - Key to use for caching (defaults to selector)
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
     * Initialize the dashboard elements and load data
     * @returns {Promise<void>}
     */
    async initDashboard() {
        console.log(`Initializing history dashboard for water heater ${this.heaterId}`);
        
        // Cache frequently accessed elements
        this.cacheElements();
        
        // Set up event listeners for day selectors
        this.setupDaySelectors();
        
        // Make sure the history tab content is visible before loading data
        const historyContent = this.getElement('#history-content', true, 'historyContent');
        if (historyContent) {
            console.log('Ensuring history content is visible before loading data');
            historyContent.style.display = 'block';
            historyContent.style.visibility = 'visible';
            historyContent.style.opacity = '1';
        }
        
        // Load initial data with a slight delay to ensure DOM is ready
        setTimeout(() => {
            this.loadHistoryData().catch(err => {
                console.error('Error loading initial history data:', err);
                this.showError('Failed to load initial data. Please try refreshing the page.');
            });
        }, 100);
    }
    
    /**
     * Cache frequently accessed DOM elements for better performance
     */
    cacheElements() {
        // Tab content element
        this.elements.historyContent = document.getElementById('history-content');
        
        // Chart canvases
        this.elements.temperatureCanvas = this.getElement('#temperature-chart');
        this.elements.energyUsageCanvas = this.getElement('#energy-usage-chart');
        this.elements.pressureFlowCanvas = this.getElement('#pressure-flow-chart');
        
        // Control elements
        this.elements.daySelectors = this.getAllElements('.day-selector');
        this.elements.errorContainer = this.getElement('#history-error');
        
        // Chart containers for loading state
        this.elements.chartContainers = this.getAllElements('.chart-container');
        this.elements.loadingIndicators = this.getAllElements('.chart-loading');
        
        console.log('History Dashboard: Cached DOM elements');
    }
    
    /**
     * Setup event listeners for day selectors
     */
    setupDaySelectors() {
        // Use cached selectors or get them using our scoped method
        const daySelectors = this.elements.daySelectors || this.getAllElements('.day-selector');
        
        // If no selectors found, log error and return
        if (!daySelectors || daySelectors.length === 0) {
            console.error('History Dashboard: No day selectors found');
            return;
        }
        
        // Log found selectors
        console.log(`History Dashboard: Setting up ${daySelectors.length} day selectors`);
        
        daySelectors.forEach(selector => {
            selector.addEventListener('click', async (e) => {
                e.preventDefault();
                
                // Update active class
                daySelectors.forEach(el => el.classList.remove('active'));
                selector.classList.add('active');
                
                // Get selected days
                this.days = parseInt(selector.getAttribute('data-days'));
                
                // Log user selection for analytics
                console.log(`History Dashboard: User selected ${this.days} days view`);
                
                // Reload data with new time range
                await this.loadHistoryData();
            });
        });
    }
    
    /**
     * Reload method called by the TabManager when the History tab is activated
     * This method ensures charts are properly initialized and data is fresh
     */
    reload() {
        console.log('WaterHeaterHistoryDashboard reload method called by TabManager');
        
        // EXTREME ISOLATION: First, handle the predictions tab content to prevent it from showing
        // Use our cached element or find it
        const predictionsContent = this.getElement('#predictions-content', true, 'predictionsContent');
        if (predictionsContent) {
            console.log('Forcing predictions content to be completely hidden using isolation pattern');
            // Most aggressive possible hiding - using tabContent isolation technique
            predictionsContent.style.display = 'none !important';
            predictionsContent.style.visibility = 'hidden !important';
            predictionsContent.style.opacity = '0 !important';
            predictionsContent.style.position = 'absolute !important';
            predictionsContent.style.zIndex = '-1000 !important';
            predictionsContent.style.pointerEvents = 'none !important';
            predictionsContent.style.clip = 'rect(0, 0, 0, 0) !important';
            predictionsContent.style.clipPath = 'inset(100%) !important';
            predictionsContent.style.maxHeight = '0px !important';
            predictionsContent.style.maxWidth = '0px !important';
            predictionsContent.style.overflow = 'hidden !important';
            predictionsContent.style.transform = 'translateX(-100000px) !important';
            predictionsContent.classList.remove('active');
            predictionsContent.classList.add('tab-content-hidden');
        }
        
        // Ensure history content is visible and properly isolated
        // Use our cached element or find it
        const historyContent = this.elements.historyContent || this.getElement('#history-content');
        if (historyContent) {
            console.log('Ensuring history content is visible during reload');
            
            // Reset all inline styles first for clean slate
            historyContent.removeAttribute('style');
            
            // Apply comprehensive visibility settings
            historyContent.style.display = 'block';
            historyContent.style.visibility = 'visible';
            historyContent.style.opacity = '1';
            historyContent.style.position = 'relative';
            historyContent.style.zIndex = '100';
            historyContent.style.pointerEvents = 'auto';
            historyContent.classList.add('active');
            historyContent.classList.remove('tab-content-hidden');
            
            // Force the history content to be at the top of the stacking context
            // Use our container-scoped query to find the tab content container
            const tabContentContainer = this.getElement('.tab-content-container');
            if (tabContentContainer) {
                // Move history content to the end of its parent to ensure it's rendered last (on top)
                tabContentContainer.appendChild(historyContent);
                console.log('History Dashboard: Repositioned history content for proper stacking context');
            }
        }
        
        // Check if charts need to be reinitialized
        const reinitializeCharts = !this.temperatureChart || 
                                !this.energyUsageChart || 
                                !this.pressureFlowChart;
        
        if (reinitializeCharts) {
            console.log('Charts need to be reinitialized during reload');
            
            // Double layout recalculation to ensure chart containers are visible
            void historyContent?.offsetWidth;
            
            // Use timeout for extra reliability
            setTimeout(() => {
                // Last extreme measure - move prediction content completely out of the DOM temporarily
                const predictionsContent = document.getElementById('predictions-content');
                if (predictionsContent && predictionsContent.parentNode) {
                    // Store the current parent and next sibling for later restoration
                    const parentNode = predictionsContent.parentNode;
                    const nextSibling = predictionsContent.nextSibling;
                    
                    // Temporarily remove predictions content from DOM
                    if (parentNode) {
                        console.log('Temporarily removing predictions content from DOM for complete isolation');
                        parentNode.removeChild(predictionsContent);
                        
                        // Restore after a short delay (after history content is fully initialized)
                        setTimeout(() => {
                            if (nextSibling) {
                                parentNode.insertBefore(predictionsContent, nextSibling);
                            } else {
                                parentNode.appendChild(predictionsContent);
                            }
                            console.log('Restored predictions content to DOM');
                            // Ensure it's still hidden
                            predictionsContent.style.display = 'none';
                            predictionsContent.style.visibility = 'hidden';
                        }, 100);
                    }
                }
            }, 0);
        }
        
        // Load fresh data
        this.loadHistoryData();
        
        // Return true to indicate successful reload
        return true;
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
        // Use our cached element or get it from DOM
        const canvas = this.elements.temperatureCanvas || this.getElement('#temperature-chart');
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
        // Use our cached element or get it from DOM
        const canvas = this.elements.energyUsageCanvas || this.getElement('#energy-usage-chart');
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
        // Use our cached element or get it from DOM
        const canvas = this.elements.pressureFlowCanvas || this.getElement('#pressure-flow-chart');
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
     * Reload all charts when the History tab becomes visible
     * This resolves issues with Chart.js initialization when containers are hidden
     */
    reloadCharts() {
        console.log('Reloading history charts');
        
        // First ensure the history content is visible
        const historyContent = document.getElementById('history-content');
        if (historyContent) {
            historyContent.style.display = 'block';
            historyContent.style.visibility = 'visible';
            historyContent.style.opacity = '1';
        }
        
        // Destroy existing charts to force proper re-initialization
        if (this.temperatureChart) {
            this.temperatureChart.destroy();
            this.temperatureChart = null;
        }
        if (this.energyUsageChart) {
            this.energyUsageChart.destroy();
            this.energyUsageChart = null;
        }
        if (this.pressureFlowChart) {
            this.pressureFlowChart.destroy();
            this.pressureFlowChart = null;
        }
        
        // Reload the data with a slight delay
        setTimeout(() => {
            this.loadHistoryData();
        }, 200);
    }
    
    /**
     * Show or hide loading indicators
     * @param {boolean} isLoading - Whether data is loading
     */
    showLoading(isLoading) {
        // Use our cached elements or get them from DOM
        const loadingIndicators = this.elements.loadingIndicators || this.getAllElements('.chart-loading');
        const chartContainers = this.elements.chartContainers || this.getAllElements('.chart-container');
        
        if (isLoading) {
            console.log('History Dashboard: Showing loading indicators');
            // Show loading indicators
            loadingIndicators.forEach(indicator => {
                indicator.style.display = 'flex';
            });
            
            // Dim chart containers
            chartContainers.forEach(container => {
                container.style.opacity = '0.5';
            });
        } else {
            console.log('History Dashboard: Hiding loading indicators');
            // Hide loading indicators
            loadingIndicators.forEach(indicator => {
                indicator.style.display = 'none';
            });
            
            // Restore chart containers
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
        // Use our cached element or get it from DOM
        const errorContainer = this.elements.errorContainer || this.getElement('#history-error');
        if (errorContainer) {
            console.error(`History Dashboard Error: ${message}`);
            errorContainer.textContent = message;
            errorContainer.style.display = 'block';
            
            // Hide after 5 seconds
            setTimeout(() => {
                errorContainer.style.display = 'none';
            }, 5000);
        }
    }
}

// Initialize the dashboard when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Extract heater ID from URL (most reliable method)
    const urlParts = window.location.pathname.split('/');
    const heaterId = urlParts[urlParts.length - 1];
    
    if (!heaterId || heaterId === 'water-heaters') {
        console.error('History Dashboard: Could not extract valid heater ID from URL');
        return;
    }
    
    console.log('History Dashboard: Extracted heater ID:', heaterId);
    
    // Initialize the dashboard instance
    function initHistoryDashboard() {
        // Only create once
        if (!window.waterHeaterHistoryDashboard) {
            console.log('History Dashboard: Creating new instance');
            window.waterHeaterHistoryDashboard = new WaterHeaterHistoryDashboard(heaterId);
            
            // Register with TabManager if available
            if (window.tabManager) {
                window.tabManager.registerComponent(
                    'history',
                    window.waterHeaterHistoryDashboard,
                    'history-dashboard'
                );
                console.log('History Dashboard: Registered with TabManager');
            }
        }
    }
    
    // Initialize dashboard
    initHistoryDashboard();
    
    // Set up event handling with the enhanced event system
    if (window.tabManager) {
        console.log('History Dashboard: Setting up enhanced event subscriptions');
        
        // Subscribe to tab changes via direct subscription (more efficient than DOM events)
        window.tabManager.subscribe(window.tabManager.EVENTS.TAB_CHANGED, function(eventData) {
            const newTabId = eventData.newTabId;
            
            // If switching to history tab, ensure dashboard is initialized and visible
            if (newTabId === 'history') {
                console.log('History Dashboard: Tab activated via subscription system');
                
                // Ensure dashboard is initialized
                initHistoryDashboard();
                
                // Reload data if dashboard instance exists
                if (window.waterHeaterHistoryDashboard) {
                    window.waterHeaterHistoryDashboard.reload();
                }
            }
        });
        
        // Also listen for data refresh events from other components
        window.tabManager.subscribe(window.tabManager.EVENTS.DATA_REFRESH, function(eventData) {
            // Only respond if we're on the history tab or refresh is forced
            if ((window.tabManager.getActiveTabId() === 'history' || eventData.forceRefresh) && 
                window.waterHeaterHistoryDashboard) {
                console.log('History Dashboard: Refreshing data based on system-wide refresh event');
                window.waterHeaterHistoryDashboard.reload();
            }
        });
    } else {
        // Fallback to standard DOM events if TabManager isn't available
        console.log('History Dashboard: TabManager not available, using DOM events');
        document.addEventListener('tabmanager:tabchanged', function(event) {
            const newTabId = event.detail.newTabId;
            
            if (newTabId === 'history') {
                console.log('History Dashboard: Tab activated via DOM event');
                initHistoryDashboard();
                
                if (window.waterHeaterHistoryDashboard) {
                    window.waterHeaterHistoryDashboard.reload();
                }
            }
        });
    }
    
    // Add direct click handler on history tab as a backup mechanism
    // This is maintained for backward compatibility and resilience
    const historyTabBtn = document.getElementById('history-tab-btn');
    if (historyTabBtn) {
        historyTabBtn.addEventListener('click', function() {
            console.log('History Dashboard: Direct tab button click detected');
            
            // Make sure dashboard is initialized
            initHistoryDashboard();
            
            // Let TabManager handle visibility through its showTab method
            if (window.tabManager) {
                window.tabManager.showTab('history');
                // TabManager will handle the reload via events
            } else {
                // Fallback direct reload if TabManager isn't available
                if (window.waterHeaterHistoryDashboard) {
                    window.waterHeaterHistoryDashboard.reload();
                }
            }
        });
    }
    
    // Share information about this dashboard with the system
    if (window.tabManager) {
        window.tabManager.dispatchEvent(window.tabManager.EVENTS.COMPONENT_REGISTERED, {
            componentType: 'WaterHeaterHistoryDashboard',
            componentId: 'history-dashboard',
            tabId: 'history',
            capabilities: ['dataRefresh', 'chartRendering', 'historyViewing']
        });
    }
});
