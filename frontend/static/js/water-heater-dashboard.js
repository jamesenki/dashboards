/**
 * Water Heater Operational Dashboard
 *
 * Handles real-time monitoring of water heater operations,
 * displaying current status, temperature, energy usage,
 * and heating cycle information.
 */

class WaterHeaterDashboard {
    constructor(deviceId) {
        this.deviceId = deviceId;
        this.telemetryData = null;
        this.lastUpdate = null;
        this.isLoading = false;
        this.pollingInterval = null;
        this.temperatureHistory = [];
        this.energyHistory = [];
        this.cycleHistory = [];

        // DOM elements - Status cards
        this.heaterModeElement = document.getElementById('heater-mode');
        this.heaterStatusElement = document.getElementById('heater-status');
        this.powerStatusElement = document.getElementById('power-status');
        this.networkStatusElement = document.getElementById('network-status');

        // DOM elements - Temperature gauge
        this.currentTempElement = document.getElementById('current-temperature');
        this.targetTempMarkerElement = document.getElementById('target-temp-marker');
        this.legendCurrentTempElement = document.getElementById('legend-current-temp');
        this.legendTargetTempElement = document.getElementById('legend-target-temp');

        // DOM elements - Energy usage
        this.energyGaugeValueElement = document.getElementById('energy-gauge-value');
        this.currentEnergyElement = document.getElementById('current-energy');
        this.dailyEnergyAvgElement = document.getElementById('daily-energy-avg');
        this.energyEfficiencyElement = document.getElementById('energy-efficiency');

        // DOM elements - Heating cycle
        this.cycleProgressElement = document.getElementById('cycle-progress');
        this.cycleTimeElement = document.getElementById('cycle-time');
        this.avgCycleTimeElement = document.getElementById('avg-cycle-time');
        this.cyclesTodayElement = document.getElementById('cycles-today');

        // DOM elements - Last update
        this.lastUpdateTimeElement = document.getElementById('last-update-time');

        // Refresh button
        const refreshButton = document.getElementById('refresh-dashboard');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => this.refreshData());
        }

        // Initialize dashboard
        this.initializeDashboard();
    }

    /**
     * Initialize the dashboard and start polling for updates
     */
    async initializeDashboard() {
        // Initial data load
        await this.refreshData();

        // Start polling every 30 seconds for real-time updates
        this.pollingInterval = setInterval(() => this.refreshData(), 30000);

        // Stop polling when page is hidden
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden') {
                clearInterval(this.pollingInterval);
                this.pollingInterval = null;
            } else if (!this.pollingInterval) {
                this.refreshData();
                this.pollingInterval = setInterval(() => this.refreshData(), 30000);
            }
        });
    }

    /**
     * Refresh all dashboard data
     */
    async refreshData() {
        if (this.isLoading) return;

        this.isLoading = true;

        try {
            // Fetch current device state
            const deviceState = await this.fetchDeviceState();

            // Fetch telemetry data
            const telemetry = await this.fetchTelemetryData();

            // Update all dashboard components
            this.updateStatusCards(deviceState);
            this.updateTemperatureGauge(deviceState, telemetry);
            this.updateEnergyUsage(deviceState, telemetry);
            this.updateHeatingCycle(deviceState, telemetry);

            // Update last update time
            this.updateLastUpdateTime();

            // Store data in history arrays
            this.updateHistoricalData(deviceState, telemetry);
        } catch (error) {
            console.error('Error refreshing dashboard data:', error);
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Fetch current device state
     */
    async fetchDeviceState() {
        const response = await fetch(`/api/water-heaters/${this.deviceId}`);

        if (!response.ok) {
            throw new Error('Failed to fetch device state');
        }

        return await response.json();
    }

    /**
     * Fetch telemetry data
     */
    async fetchTelemetryData() {
        const response = await fetch(`/api/water-heaters/${this.deviceId}/telemetry?limit=100`);

        if (!response.ok) {
            throw new Error('Failed to fetch telemetry data');
        }

        return await response.json();
    }

    /**
     * Update status cards with current device state
     */
    updateStatusCards(deviceState) {
        // Update mode
        if (this.heaterModeElement) {
            const mode = deviceState.mode || 'Unknown';
            this.heaterModeElement.textContent = this.formatMode(mode);
            this.heaterModeElement.className = `status-${mode.toLowerCase()}`;
        }

        // Update heater status
        if (this.heaterStatusElement) {
            const isHeating = deviceState.is_heating || false;
            const heaterStatus = isHeating ? 'Active' : 'Idle';
            this.heaterStatusElement.textContent = heaterStatus;
            this.heaterStatusElement.className = isHeating ? 'status-online' : 'status-standby';
        }

        // Update power status
        if (this.powerStatusElement) {
            const powerStatus = deviceState.power_status || 'Unknown';
            this.powerStatusElement.textContent = powerStatus;
            this.powerStatusElement.className = powerStatus === 'On' ? 'status-online' : 'status-offline';
        }

        // Update network status
        if (this.networkStatusElement) {
            const isOnline = deviceState.is_online !== undefined ? deviceState.is_online : true;
            const networkStatus = isOnline ? 'Online' : 'Offline';
            this.networkStatusElement.textContent = networkStatus;
            this.networkStatusElement.className = isOnline ? 'status-online' : 'status-offline';

            // Add pulse animation if recently reconnected
            if (isOnline && this.networkStatusElement.dataset.wasOffline === 'true') {
                this.networkStatusElement.classList.add('status-pulse');
                setTimeout(() => {
                    this.networkStatusElement.classList.remove('status-pulse');
                }, 5000);
            }

            // Store current status for next comparison
            this.networkStatusElement.dataset.wasOffline = !isOnline;
        }
    }

    /**
     * Update temperature gauge
     */
    updateTemperatureGauge(deviceState, telemetry) {
        const currentTemp = deviceState.current_temperature;
        const targetTemp = deviceState.target_temperature;

        // Update current temperature display
        if (this.currentTempElement && currentTemp !== undefined) {
            this.currentTempElement.textContent = currentTemp.toFixed(1);
        }

        // Update legend values
        if (this.legendCurrentTempElement && currentTemp !== undefined) {
            this.legendCurrentTempElement.textContent = currentTemp.toFixed(1);
        }

        if (this.legendTargetTempElement && targetTemp !== undefined) {
            this.legendTargetTempElement.textContent = targetTemp.toFixed(1);
        }

        // Update target temperature marker position
        if (this.targetTempMarkerElement && targetTemp !== undefined) {
            // Position marker based on target temperature (assuming 0-100°C range)
            const angle = this.mapRange(targetTemp, 0, 100, 0, 360);
            const radius = 75; // Gauge radius in px

            // Calculate position on the circle
            const radians = (angle - 90) * (Math.PI / 180); // -90 to align with CSS conic gradient start
            const x = radius * Math.cos(radians);
            const y = radius * Math.sin(radians);

            // Position marker
            this.targetTempMarkerElement.style.transform = `translate(${x}px, ${y}px)`;
        }
    }

    /**
     * Update energy usage displays
     */
    updateEnergyUsage(deviceState, telemetry) {
        const currentEnergy = deviceState.current_energy_usage;
        const efficiency = deviceState.efficiency || 0;

        // Calculate daily average from telemetry
        let dailyAverage = 0;
        if (telemetry && telemetry.readings && telemetry.readings.length > 0) {
            const today = new Date().setHours(0, 0, 0, 0);
            const todayReadings = telemetry.readings.filter(reading => {
                const readingDate = new Date(reading.timestamp).setHours(0, 0, 0, 0);
                return readingDate === today;
            });

            if (todayReadings.length > 0) {
                const energySum = todayReadings.reduce((sum, reading) => sum + (reading.energy_usage || 0), 0);
                dailyAverage = energySum / todayReadings.length;
            }
        }

        // Update energy gauge height (0-3000W range)
        if (this.energyGaugeValueElement && currentEnergy !== undefined) {
            const heightPercentage = this.mapRange(currentEnergy, 0, 3000, 0, 100);
            this.energyGaugeValueElement.style.height = `${heightPercentage}%`;
        }

        // Update current energy text
        if (this.currentEnergyElement && currentEnergy !== undefined) {
            this.currentEnergyElement.textContent = Math.round(currentEnergy);
        }

        // Update daily average
        if (this.dailyEnergyAvgElement) {
            this.dailyEnergyAvgElement.textContent = `${Math.round(dailyAverage)} W`;
        }

        // Update efficiency
        if (this.energyEfficiencyElement) {
            this.energyEfficiencyElement.textContent = `${Math.round(efficiency * 100)}%`;
        }
    }

    /**
     * Update heating cycle information
     */
    updateHeatingCycle(deviceState, telemetry) {
        // Get latest cycle duration
        let lastCycleDuration = deviceState.last_heating_cycle_duration || 0;
        let todayCycles = 0;
        let avgCycleDuration = 0;

        // Calculate cycle statistics from telemetry
        if (telemetry && telemetry.readings && telemetry.readings.length > 0) {
            const today = new Date().setHours(0, 0, 0, 0);
            const todayReadings = telemetry.readings.filter(reading => {
                const readingDate = new Date(reading.timestamp).setHours(0, 0, 0, 0);
                return readingDate === today;
            });

            // Get heating cycle completions
            const cycleCompletions = todayReadings.filter(reading =>
                reading.heating_cycle_completion && reading.heating_cycle_completion === true
            );

            todayCycles = cycleCompletions.length;

            // Calculate average cycle duration
            if (cycleCompletions.length > 0) {
                const durationSum = cycleCompletions.reduce((sum, reading) =>
                    sum + (reading.heating_cycle_duration || 0), 0
                );
                avgCycleDuration = durationSum / cycleCompletions.length;
            }
        }

        // Update cycle progress visualization
        if (this.cycleProgressElement) {
            // Set progress as percentage of average cycle time
            const averageTime = avgCycleDuration > 0 ? avgCycleDuration : 600; // Default to 10 min
            const progress = lastCycleDuration / averageTime * 100;
            this.cycleProgressElement.style.setProperty('--progress', `${Math.min(100, progress)}%`);
        }

        // Update cycle time text
        if (this.cycleTimeElement) {
            const minutes = Math.floor(lastCycleDuration / 60);
            const seconds = Math.floor(lastCycleDuration % 60);
            this.cycleTimeElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }

        // Update average cycle time
        if (this.avgCycleTimeElement) {
            const minutes = Math.floor(avgCycleDuration / 60);
            const seconds = Math.floor(avgCycleDuration % 60);
            this.avgCycleTimeElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }

        // Update cycles today
        if (this.cyclesTodayElement) {
            this.cyclesTodayElement.textContent = todayCycles;
        }
    }

    /**
     * Update last update time
     */
    updateLastUpdateTime() {
        const now = new Date();

        if (this.lastUpdateTimeElement) {
            this.lastUpdateTimeElement.textContent = this.formatTime(now);
        }

        this.lastUpdate = now;
    }

    /**
     * Update historical data arrays
     */
    updateHistoricalData(deviceState, telemetry) {
        // Add current temperature to history (limit to last 100 readings)
        if (deviceState.current_temperature !== undefined) {
            this.temperatureHistory.push({
                timestamp: new Date(),
                value: deviceState.current_temperature
            });

            if (this.temperatureHistory.length > 100) {
                this.temperatureHistory.shift();
            }
        }

        // Add current energy usage to history
        if (deviceState.current_energy_usage !== undefined) {
            this.energyHistory.push({
                timestamp: new Date(),
                value: deviceState.current_energy_usage
            });

            if (this.energyHistory.length > 100) {
                this.energyHistory.shift();
            }
        }

        // Add cycle data to history if available
        if (deviceState.is_heating !== undefined) {
            const isHeating = deviceState.is_heating;
            const lastCycleItem = this.cycleHistory[this.cycleHistory.length - 1];

            // If state changed from not heating to heating, add new cycle start
            if (isHeating && (!lastCycleItem || !lastCycleItem.isHeating)) {
                this.cycleHistory.push({
                    startTime: new Date(),
                    isHeating: true
                });
            }
            // If state changed from heating to not heating, update the end time
            else if (!isHeating && lastCycleItem && lastCycleItem.isHeating && !lastCycleItem.endTime) {
                lastCycleItem.endTime = new Date();
                lastCycleItem.duration = (lastCycleItem.endTime - lastCycleItem.startTime) / 1000;
            }

            // Limit history to last 20 cycles
            if (this.cycleHistory.length > 20) {
                this.cycleHistory.shift();
            }
        }
    }

    /**
     * Format mode string for display
     */
    formatMode(mode) {
        switch (mode.toLowerCase()) {
            case 'eco':
            case 'economy':
                return 'Economy';
            case 'boost':
            case 'high':
                return 'Boost';
            case 'vacation':
                return 'Vacation';
            case 'standby':
                return 'Standby';
            case 'off':
                return 'Off';
            default:
                return mode.charAt(0).toUpperCase() + mode.slice(1);
        }
    }

    /**
     * Format time for display
     */
    formatTime(date) {
        const now = new Date();
        const diffMs = now - date;

        if (diffMs < 60000) {
            return 'Just now';
        } else if (diffMs < 3600000) {
            const minutes = Math.floor(diffMs / 60000);
            return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else {
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
    }

    /**
     * Map a value from one range to another
     */
    mapRange(value, inMin, inMax, outMin, outMax) {
        return (value - inMin) * (outMax - outMin) / (inMax - inMin) + outMin;
    }
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Get device ID from URL or data attribute
    const deviceIdElement = document.getElementById('device-id');
    const deviceId = deviceIdElement ? deviceIdElement.dataset.deviceId : null;

    if (deviceId) {
        window.waterHeaterDashboard = new WaterHeaterDashboard(deviceId);
    } else {
        console.error('Device ID not found for dashboard');
    }
});
