/**
 * Water Heater Details Page - Simplified
 *
 * This script handles ONLY current shadow information for the details page,
 * with NO temperature history chart or history API calls.
 */

(function() {
    // Execute when DOM is ready
    document.addEventListener('DOMContentLoaded', initializeDetailsPage);

    function initializeDetailsPage() {
        console.log('Initializing water heater details page (current shadow only)');

        // Extract device ID from the page
        const deviceIdElement = document.getElementById('water-heater-detail');
        if (!deviceIdElement) {
            console.error('Could not find water heater detail element');
            return;
        }

        const deviceId = deviceIdElement.dataset.deviceId;
        if (!deviceId) {
            console.error('No device ID found in data attribute');
            return;
        }

        console.log(`Initializing shadow data for device ${deviceId}`);

        // Initialize API client
        const api = new ApiClient();

        // Elements for shadow data display
        const elements = {
            temperatureValue: document.querySelector('.temperature-value'),
            statusValue: document.querySelector('.device-status-value'),
            modeValue: document.querySelector('.device-mode-value'),
            heaterStatusValue: document.querySelector('.heater-status-value'),
            lastUpdatedValue: document.querySelector('.last-updated-value'),
            lastUpdateTime: document.getElementById('last-update-time'),
            connectionStatus: document.getElementById('realtime-connection-status'),
            errorContainer: document.querySelector('.shadow-document-error')
        };

        // Setup shadow document handler
        if (window.DeviceShadowHandler) {
            const shadowHandler = new DeviceShadowHandler(deviceId);

            // Handle shadow updates
            shadowHandler.onUpdate(function(shadow) {
                updateShadowDisplay(shadow, elements);
            });

            // Handle shadow errors
            shadowHandler.onError(function(error) {
                showError(error, elements.errorContainer);
            });

            // Start polling for shadow updates
            shadowHandler.startPolling(5000); // Poll every 5 seconds
        } else {
            console.error('DeviceShadowHandler not available');
            showError('Shadow document handler not available', elements.errorContainer);
        }

        // Initial shadow fetch
        fetchCurrentShadow(deviceId, api, elements);
    }

    function fetchCurrentShadow(deviceId, api, elements) {
        console.log(`Fetching current shadow for device ${deviceId}`);

        // Use device shadow API to get current state only (no history)
        api.get(`/api/device-shadows/${deviceId}`)
            .then(response => {
                if (!response || !response.reported) {
                    throw new Error('Invalid shadow document response');
                }

                // Update UI with shadow data
                updateShadowDisplay(response, elements);
            })
            .catch(error => {
                console.error('Error fetching shadow document:', error);
                showError(error.message || 'Failed to load device data', elements.errorContainer);
            });
    }

    function updateShadowDisplay(shadow, elements) {
        if (!shadow || !shadow.reported) {
            console.warn('Invalid shadow data received');
            return;
        }

        const reported = shadow.reported;

        // Update temperature display
        if (elements.temperatureValue && reported.temperature) {
            elements.temperatureValue.textContent = `${reported.temperature}°C`;
            elements.temperatureValue.classList.add('active');
        }

        // Update status display
        if (elements.statusValue && reported.status) {
            elements.statusValue.textContent = reported.status;
            elements.statusValue.className = 'device-status-value'; // Reset classes
            elements.statusValue.classList.add(reported.status.toLowerCase());
        }

        // Update mode display
        if (elements.modeValue && reported.mode) {
            elements.modeValue.textContent = reported.mode;
        }

        // Update heater status display
        if (elements.heaterStatusValue && reported.heater_status) {
            elements.heaterStatusValue.textContent = reported.heater_status;
        }

        // Update last update time
        if (elements.lastUpdateTime && shadow.timestamp) {
            const timestamp = new Date(shadow.timestamp);
            elements.lastUpdateTime.textContent = timestamp.toLocaleString();
        }

        if (elements.lastUpdatedValue && shadow.timestamp) {
            const timestamp = new Date(shadow.timestamp);
            elements.lastUpdatedValue.textContent = timestamp.toLocaleTimeString();
        }

        // Update connection status indicator
        if (elements.connectionStatus) {
            if (reported.connection_status === 'ONLINE') {
                elements.connectionStatus.className = 'status-indicator connected';
            } else {
                elements.connectionStatus.className = 'status-indicator disconnected';
            }
        }

        // Hide error container if we have valid data
        if (elements.errorContainer) {
            elements.errorContainer.style.display = 'none';
        }
    }

    function showError(message, errorContainer) {
        console.error('Shadow error:', message);

        if (errorContainer) {
            errorContainer.textContent = message;
            errorContainer.style.display = 'block';
        }
    }
})();
