/**
 * Maintenance Predictions Module
 *
 * Handles fetching and displaying maintenance prediction data
 * for water heaters, focusing on real-time operational monitoring.
 */

class MaintenancePredictionsModule {
    constructor(deviceId) {
        this.deviceId = deviceId;
        this.predictions = {};
        this.lastUpdate = null;
        this.isLoading = false;

        // DOM element references
        this.loadingElement = document.getElementById('prediction-loading');
        this.errorElement = document.getElementById('prediction-error');
        this.errorMessageElement = document.getElementById('prediction-error-message');
        this.emptyElement = document.getElementById('prediction-empty');
        this.resultsElement = document.getElementById('prediction-results');

        // Component failure elements
        this.componentFailureGauge = document.getElementById('component-failure-gauge');
        this.componentFailurePercentage = document.getElementById('component-failure-percentage');
        this.componentFailureSummary = document.getElementById('component-failure-summary');
        this.componentHealthBreakdown = document.getElementById('component-health-breakdown');
        this.componentFailureActions = document.getElementById('component-failure-actions');

        // Descaling requirement elements
        this.descalingGauge = document.getElementById('descaling-requirement-gauge');
        this.descalingPercentage = document.getElementById('descaling-requirement-percentage');
        this.descalingSummary = document.getElementById('descaling-requirement-summary');
        this.scaleThickness = document.getElementById('scale-thickness');
        this.lastDescaling = document.getElementById('last-descaling');
        this.waterHardness = document.getElementById('water-hardness');
        this.descalingActions = document.getElementById('descaling-requirement-actions');

        // Timeline element
        this.maintenanceTimeline = document.getElementById('maintenance-timeline');

        // Refresh button
        const refreshButton = document.getElementById('refresh-predictions');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => this.loadPredictions(true));
        }

        // Initial load
        this.loadPredictions();

        // Set up auto-refresh (every 15 minutes)
        setInterval(() => this.loadPredictions(true), 15 * 60 * 1000);
    }

    /**
     * Load predictions from the API
     * @param {boolean} forceRefresh - Force a refresh even if data is recent
     */
    async loadPredictions(forceRefresh = false) {
        // Skip if already loading or data is fresh (within last 5 minutes)
        if (this.isLoading) return;

        const now = new Date();
        if (!forceRefresh && this.lastUpdate &&
            (now - this.lastUpdate) < (5 * 60 * 1000)) {
            return;
        }

        this.isLoading = true;
        this.showLoading();

        try {
            // Load component failure prediction
            const componentFailure = await this.fetchPrediction('component_failure');
            if (componentFailure) {
                this.predictions.componentFailure = componentFailure;
            }

            // Load descaling requirement prediction
            const descalingRequirement = await this.fetchPrediction('descaling_requirement');
            if (descalingRequirement) {
                this.predictions.descalingRequirement = descalingRequirement;
            }

            this.lastUpdate = new Date();
            this.updateUI();
            this.showResults();
        } catch (error) {
            console.error('Error loading predictions:', error);
            this.showError(error.message || 'Failed to load maintenance predictions');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Fetch a specific prediction type from the API
     * @param {string} predictionType - Type of prediction to fetch
     * @returns {Promise<object>} - Prediction data
     */
    async fetchPrediction(predictionType) {
        // Prepare telemetry data for the prediction
        const telemetryData = await this.getDeviceTelemetryData();

        // Prepare API request
        const requestData = {
            device_id: this.deviceId,
            prediction_type: predictionType,
            features: telemetryData
        };

        // Make API request
        const response = await fetch('/api/predictions/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Failed to generate ${predictionType} prediction`);
        }

        return await response.json();
    }

    /**
     * Get telemetry data for the current device
     * @returns {Promise<object>} - Telemetry data for predictions
     */
    async getDeviceTelemetryData() {
        // Fetch recent telemetry data for the device
        const response = await fetch(`/api/manufacturer/water-heaters/${this.deviceId}/telemetry`);

        if (!response.ok) {
            console.warn('Failed to fetch detailed telemetry, using basic data');
            return this.getBasicDeviceData();
        }

        const telemetry = await response.json();

        // Process telemetry into the format needed for predictions
        return {
            device_id: this.deviceId,
            timestamp: telemetry.readings.map(r => r.timestamp),
            temperature: telemetry.readings.map(r => r.temperature),
            energy_usage: telemetry.readings.map(r => r.energy_usage),
            flow_rate: telemetry.readings.map(r => r.flow_rate),
            pressure: telemetry.readings.map(r => r.pressure),
            element_temperature: telemetry.readings.map(r => r.element_temperature),
            efficiency: telemetry.readings.map(r => r.efficiency),
            heating_cycles: telemetry.readings.map(r => r.heating_cycle_duration),
            water_hardness: telemetry.water_hardness || 150,
            total_operation_hours: telemetry.total_operation_hours || 0,
            maintenance_history: telemetry.maintenance_history || []
        };
    }

    /**
     * Get basic device data if detailed telemetry is unavailable
     * @returns {object} - Basic device data
     */
    async getBasicDeviceData() {
        // Fetch basic device info
        const response = await fetch(`/api/manufacturer/water-heaters/${this.deviceId}`);

        if (!response.ok) {
            throw new Error('Unable to fetch device data');
        }

        const deviceData = await response.json();

        // Create minimal dataset for predictions
        return {
            device_id: this.deviceId,
            current_temperature: deviceData.current_temperature,
            target_temperature: deviceData.target_temperature,
            mode: deviceData.mode,
            water_hardness: 150, // Default assumption
            total_operation_hours: deviceData.operational_since ?
                this.calculateOperationHours(new Date(deviceData.operational_since)) :
                4380, // Default to 6 months
            maintenance_history: []
        };
    }

    /**
     * Calculate operation hours from installation date
     * @param {Date} installDate - Installation date
     * @returns {number} - Total operation hours
     */
    calculateOperationHours(installDate) {
        const now = new Date();
        const hoursDiff = (now - installDate) / (1000 * 60 * 60);
        return Math.max(0, Math.round(hoursDiff));
    }

    /**
     * Update the UI with prediction data
     */
    updateUI() {
        // Check if we have any predictions to display
        if (!this.predictions.componentFailure && !this.predictions.descalingRequirement) {
            this.showEmpty();
            return;
        }

        // Update component failure UI if available
        if (this.predictions.componentFailure) {
            this.updateComponentFailureUI(this.predictions.componentFailure);
        }

        // Update descaling requirement UI if available
        if (this.predictions.descalingRequirement) {
            this.updateDescalingRequirementUI(this.predictions.descalingRequirement);
        }

        // Update maintenance timeline
        this.updateMaintenanceTimeline();
    }

    /**
     * Update component failure prediction UI
     * @param {object} prediction - Component failure prediction data
     */
    updateComponentFailureUI(prediction) {
        // Update gauge value (invert since higher value means higher failure risk)
        const gaugeValue = prediction.predicted_value * 100;
        this.componentFailureGauge.querySelector('.gauge-value').style.height = `${gaugeValue}%`;
        this.componentFailurePercentage.textContent = `${Math.round(gaugeValue)}%`;

        // Update summary text
        let summaryText = '';
        if (gaugeValue < 30) {
            summaryText = 'All components are operating normally.';
        } else if (gaugeValue < 70) {
            summaryText = 'Some components are showing early signs of wear.';
        } else {
            summaryText = 'Critical components need attention soon.';
        }
        this.componentFailureSummary.textContent = summaryText;

        // Update component breakdown
        if (prediction.raw_details && prediction.raw_details.components) {
            this.componentHealthBreakdown.innerHTML = '';

            Object.entries(prediction.raw_details.components).forEach(([component, value]) => {
                const formattedComponent = component.replace(/_/g, ' ');
                let statusClass = 'status-good';

                if (value > 0.7) statusClass = 'status-critical';
                else if (value > 0.3) statusClass = 'status-warning';

                const el = document.createElement('div');
                el.className = 'component-health-item';
                el.innerHTML = `
                    <div class="component-health-status ${statusClass}"></div>
                    <span>${formattedComponent}: ${Math.round(value * 100)}%</span>
                `;
                this.componentHealthBreakdown.appendChild(el);
            });
        }

        // Update actions
        this.componentFailureActions.innerHTML = '';
        if (prediction.recommended_actions && prediction.recommended_actions.length > 0) {
            prediction.recommended_actions.forEach(action => {
                this.addActionElement(this.componentFailureActions, action);
            });
        }
    }

    /**
     * Update descaling requirement prediction UI
     * @param {object} prediction - Descaling requirement prediction data
     */
    updateDescalingRequirementUI(prediction) {
        // Update gauge value
        const gaugeValue = prediction.predicted_value * 100;
        this.descalingGauge.querySelector('.gauge-value').style.height = `${gaugeValue}%`;
        this.descalingPercentage.textContent = `${Math.round(gaugeValue)}%`;

        // Update summary text
        let summaryText = '';
        if (gaugeValue < 30) {
            summaryText = 'No descaling needed at this time.';
        } else if (gaugeValue < 70) {
            summaryText = 'Consider scheduling descaling in the upcoming maintenance.';
        } else {
            summaryText = 'Descaling needed soon to prevent efficiency loss.';
        }
        this.descalingSummary.textContent = summaryText;

        // Update scale details
        if (prediction.raw_details) {
            // Scale thickness
            const thickness = prediction.raw_details.estimated_scale_thickness_mm || 0;
            this.scaleThickness.textContent = `${thickness.toFixed(1)} mm`;

            // Last descaling
            const daysSinceDescaling = prediction.raw_details.days_since_last_descaling || 0;
            if (daysSinceDescaling === 0) {
                this.lastDescaling.textContent = 'Recently';
            } else if (daysSinceDescaling < 30) {
                this.lastDescaling.textContent = `${daysSinceDescaling} days ago`;
            } else {
                const monthsAgo = Math.round(daysSinceDescaling / 30);
                this.lastDescaling.textContent = `${monthsAgo} month${monthsAgo !== 1 ? 's' : ''} ago`;
            }

            // Water hardness
            const hardness = prediction.raw_details.water_hardness || 0;
            let hardnessCategory = 'Unknown';

            if (hardness < 60) hardnessCategory = 'Soft';
            else if (hardness < 120) hardnessCategory = 'Slightly Hard';
            else if (hardness < 180) hardnessCategory = 'Moderately Hard';
            else if (hardness < 250) hardnessCategory = 'Hard';
            else hardnessCategory = 'Very Hard';

            this.waterHardness.textContent = `${hardnessCategory} (${hardness} ppm)`;
        }

        // Update actions
        this.descalingActions.innerHTML = '';
        if (prediction.recommended_actions && prediction.recommended_actions.length > 0) {
            prediction.recommended_actions.forEach(action => {
                this.addActionElement(this.descalingActions, action);
            });
        }
    }

    /**
     * Update maintenance timeline with all recommended actions
     */
    updateMaintenanceTimeline() {
        this.maintenanceTimeline.innerHTML = '';

        // Collect all actions
        const allActions = [];

        if (this.predictions.componentFailure && this.predictions.componentFailure.recommended_actions) {
            allActions.push(...this.predictions.componentFailure.recommended_actions);
        }

        if (this.predictions.descalingRequirement && this.predictions.descalingRequirement.recommended_actions) {
            allActions.push(...this.predictions.descalingRequirement.recommended_actions);
        }

        // Sort by due date
        allActions.sort((a, b) => {
            const dateA = a.due_date ? new Date(a.due_date) : new Date(9999, 11, 31);
            const dateB = b.due_date ? new Date(b.due_date) : new Date(9999, 11, 31);
            return dateA - dateB;
        });

        // Add to timeline
        allActions.forEach(action => {
            const dueDate = action.due_date ? new Date(action.due_date) : null;

            const timelineItem = document.createElement('div');
            timelineItem.className = 'timeline-item';

            timelineItem.innerHTML = `
                <div class="timeline-point severity-${action.severity.toLowerCase()}"></div>
                <div class="timeline-content">
                    <div class="timeline-date">${dueDate ? this.formatDate(dueDate) : 'No specific timeline'}</div>
                    <p class="timeline-action">${action.description}</p>
                </div>
            `;

            this.maintenanceTimeline.appendChild(timelineItem);
        });

        // If no actions, show message
        if (allActions.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'timeline-empty';
            emptyMessage.textContent = 'No maintenance actions scheduled at this time.';
            this.maintenanceTimeline.appendChild(emptyMessage);
        }
    }

    /**
     * Add an action recommendation element
     * @param {HTMLElement} container - Container to add the action to
     * @param {object} action - Action recommendation data
     */
    addActionElement(container, action) {
        const actionElement = document.createElement('div');
        actionElement.className = `action-item severity-${action.severity.toLowerCase()}`;

        // Due date text
        let dueText = '';
        if (action.due_date) {
            const dueDate = new Date(action.due_date);
            const now = new Date();
            const daysDiff = Math.round((dueDate - now) / (1000 * 60 * 60 * 24));

            if (daysDiff < 0) {
                dueText = 'Overdue';
            } else if (daysDiff === 0) {
                dueText = 'Due today';
            } else if (daysDiff === 1) {
                dueText = 'Due tomorrow';
            } else if (daysDiff < 7) {
                dueText = `Due in ${daysDiff} days`;
            } else if (daysDiff < 30) {
                dueText = `Due in ${Math.round(daysDiff / 7)} weeks`;
            } else {
                dueText = `Due ${this.formatDate(dueDate)}`;
            }
        }

        actionElement.innerHTML = `
            <div class="action-text">
                <p class="action-description">${action.description}</p>
                <p class="action-impact">${action.impact}</p>
            </div>
            <div class="action-due">${dueText}</div>
        `;

        container.appendChild(actionElement);
    }

    /**
     * Format a date for display
     * @param {Date} date - Date to format
     * @returns {string} - Formatted date string
     */
    formatDate(date) {
        const now = new Date();
        const isThisYear = date.getFullYear() === now.getFullYear();

        // Format: Month Day (Year if not current year)
        const options = {
            month: 'short',
            day: 'numeric',
            year: isThisYear ? undefined : 'numeric'
        };

        return date.toLocaleDateString(undefined, options);
    }

    /**
     * Show loading state
     */
    showLoading() {
        this.loadingElement.style.display = 'block';
        this.errorElement.style.display = 'none';
        this.emptyElement.style.display = 'none';
        this.resultsElement.style.display = 'none';
    }

    /**
     * Show error state
     * @param {string} message - Error message to display
     */
    showError(message) {
        this.loadingElement.style.display = 'none';
        this.errorElement.style.display = 'block';
        this.emptyElement.style.display = 'none';
        this.resultsElement.style.display = 'none';

        this.errorMessageElement.textContent = message;
    }

    /**
     * Show empty state
     */
    showEmpty() {
        this.loadingElement.style.display = 'none';
        this.errorElement.style.display = 'none';
        this.emptyElement.style.display = 'block';
        this.resultsElement.style.display = 'none';
    }

    /**
     * Show results state
     */
    showResults() {
        this.loadingElement.style.display = 'none';
        this.errorElement.style.display = 'none';
        this.emptyElement.style.display = 'none';
        this.resultsElement.style.display = 'block';
    }
}

// Initialize the module when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Get device ID from URL or data attribute
    const deviceIdElement = document.getElementById('device-id');
    const deviceId = deviceIdElement ? deviceIdElement.dataset.deviceId : null;

    if (deviceId) {
        window.maintenancePredictions = new MaintenancePredictionsModule(deviceId);
    } else {
        console.error('Device ID not found for maintenance predictions');
    }
});
