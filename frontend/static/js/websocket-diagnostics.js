/**
 * WebSocket and API Diagnostics Tool
 *
 * This utility helps diagnose issues with WebSocket connections and API responses
 * for the IoTSphere application.
 */

class WebSocketDiagnostics {
    constructor() {
        this.results = {
            websocketChecks: [],
            apiChecks: [],
            uiChecks: []
        };
        this.deviceId = this.getDeviceIdFromUrl();
        console.log(`Diagnostics initialized for device ID: ${this.deviceId}`);
    }

    /**
     * Extract device ID from the current URL
     */
    getDeviceIdFromUrl() {
        const pathParts = window.location.pathname.split('/');
        const deviceIdIndex = pathParts.indexOf('water-heaters') + 1;
        return pathParts[deviceIdIndex] || 'unknown';
    }

    /**
     * Run all diagnostic tests
     */
    async runAllTests() {
        console.log('Starting WebSocket and API diagnostics...');

        // Clear previous results
        this.results = {
            websocketChecks: [],
            apiChecks: [],
            uiChecks: []
        };

        // Check token availability
        this.checkTokenAvailability();

        // Test WebSocket endpoints
        await this.testDeviceStateWebSocket();
        await this.testTelemetryWebSocket();

        // Test API endpoints
        await this.testHistoryEndpoints();

        // Check UI elements
        this.checkUIElements();

        // Display results
        this.displayResults();
    }

    /**
     * Check if auth token is available
     */
    checkTokenAvailability() {
        try {
            const token = window.authTokenProvider ? window.authTokenProvider.getToken() : null;
            const hasToken = !!token;

            this.results.websocketChecks.push({
                name: 'Auth Token Available',
                success: hasToken,
                details: hasToken ?
                    `Token is available ${token.substring(0, 15)}...` :
                    'No authentication token found'
            });

            console.log(`Auth token available: ${hasToken}`);
        } catch (error) {
            this.results.websocketChecks.push({
                name: 'Auth Token Available',
                success: false,
                details: `Error checking token: ${error.message}`
            });
        }
    }

    /**
     * Test device state WebSocket
     */
    async testDeviceStateWebSocket() {
        return new Promise(resolve => {
            // Create a temporary WebSocket
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const token = window.authTokenProvider ? window.authTokenProvider.getToken() : null;

            // Build URL with token
            const url = new URL(`${protocol}//${window.location.host}/ws/devices/${this.deviceId}/state`);
            if (token) {
                url.searchParams.append('token', token);
            }

            console.log(`Testing state WebSocket: ${url.toString()}`);

            // Create WebSocket and set timeout
            const socket = new WebSocket(url);
            let messageReceived = false;
            let connectionSuccessful = false;

            // Set a timeout to abort the test
            const timeout = setTimeout(() => {
                if (socket.readyState === WebSocket.OPEN) {
                    socket.close();
                }

                this.results.websocketChecks.push({
                    name: 'Device State WebSocket',
                    success: connectionSuccessful,
                    details: connectionSuccessful ?
                        (messageReceived ? 'Connected and received state message' : 'Connected but no state message received') :
                        'Failed to establish connection or timed out'
                });

                resolve();
            }, 5000);

            // Connection opened
            socket.addEventListener('open', event => {
                connectionSuccessful = true;
                console.log('State WebSocket connection established');

                // Request state
                socket.send(JSON.stringify({
                    type: 'get_state'
                }));
            });

            // Listen for messages
            socket.addEventListener('message', event => {
                messageReceived = true;
                console.log('State message received:', event.data);

                // If we got a message, we can resolve early
                clearTimeout(timeout);

                this.results.websocketChecks.push({
                    name: 'Device State WebSocket',
                    success: true,
                    details: `Connected and received message: ${event.data.substring(0, 50)}...`
                });

                socket.close();
                resolve();
            });

            // Connection closed or error
            socket.addEventListener('close', event => {
                if (!connectionSuccessful) {
                    console.log(`State WebSocket connection closed with code: ${event.code}`);

                    if (!messageReceived) {
                        this.results.websocketChecks.push({
                            name: 'Device State WebSocket',
                            success: false,
                            details: `Connection closed with code: ${event.code}`
                        });

                        clearTimeout(timeout);
                        resolve();
                    }
                }
            });

            // Connection error
            socket.addEventListener('error', error => {
                console.error('State WebSocket error:', error);
            });
        });
    }

    /**
     * Test telemetry WebSocket
     */
    async testTelemetryWebSocket() {
        return new Promise(resolve => {
            // Create a temporary WebSocket
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const token = window.authTokenProvider ? window.authTokenProvider.getToken() : null;

            // Build URL with token and simulate flag
            const url = new URL(`${protocol}//${window.location.host}/ws/devices/${this.deviceId}/telemetry`);
            if (token) {
                url.searchParams.append('token', token);
            }
            url.searchParams.append('simulate', 'true');

            console.log(`Testing telemetry WebSocket: ${url.toString()}`);

            // Create WebSocket and set timeout
            const socket = new WebSocket(url);
            let messageReceived = false;
            let connectionSuccessful = false;

            // Set a timeout to abort the test
            const timeout = setTimeout(() => {
                if (socket.readyState === WebSocket.OPEN) {
                    socket.close();
                }

                this.results.websocketChecks.push({
                    name: 'Telemetry WebSocket',
                    success: connectionSuccessful,
                    details: connectionSuccessful ?
                        (messageReceived ? 'Connected and received telemetry message' : 'Connected but no telemetry message received') :
                        'Failed to establish connection or timed out'
                });

                resolve();
            }, 5000);

            // Connection opened
            socket.addEventListener('open', event => {
                connectionSuccessful = true;
                console.log('Telemetry WebSocket connection established');
            });

            // Listen for messages
            socket.addEventListener('message', event => {
                messageReceived = true;
                console.log('Telemetry message received:', event.data);

                // If we got a message, we can resolve early
                clearTimeout(timeout);

                this.results.websocketChecks.push({
                    name: 'Telemetry WebSocket',
                    success: true,
                    details: `Connected and received message: ${event.data.substring(0, 50)}...`
                });

                socket.close();
                resolve();
            });

            // Connection closed or error
            socket.addEventListener('close', event => {
                if (!connectionSuccessful) {
                    console.log(`Telemetry WebSocket connection closed with code: ${event.code}`);

                    if (!messageReceived) {
                        this.results.websocketChecks.push({
                            name: 'Telemetry WebSocket',
                            success: false,
                            details: `Connection closed with code: ${event.code}`
                        });

                        clearTimeout(timeout);
                        resolve();
                    }
                }
            });

            // Connection error
            socket.addEventListener('error', error => {
                console.error('Telemetry WebSocket error:', error);
            });
        });
    }

    /**
     * Test history API endpoints
     */
    async testHistoryEndpoints() {
        const endpoints = [
            `/api/manufacturer/water-heaters/${this.deviceId}/history?days=7`,
            `/api/manufacturer/water-heaters/${this.deviceId}/history/temperature?days=7`,
            `/api/manufacturer/water-heaters/${this.deviceId}/history/energy-usage?days=7`,
            `/api/manufacturer/water-heaters/${this.deviceId}/history/pressure-flow?days=7`,
            `/api/manufacturer/water-heaters/${this.deviceId}/history/dashboard?days=7`
        ];

        const results = await Promise.all(endpoints.map(async endpoint => {
            try {
                const response = await fetch(`${endpoint}&_t=${Date.now()}`);
                const success = response.ok;
                let details = `Status: ${response.status}`;

                if (success) {
                    try {
                        const data = await response.json();
                        const hasData = !!data;
                        details += ` | Data received: ${hasData ? 'Yes' : 'No'}`;

                        if (hasData) {
                            if (endpoint.includes('temperature')) {
                                // Check temperature data format
                                const hasLabels = Array.isArray(data.labels);
                                const hasValues = Array.isArray(data.values);
                                details += ` | Has labels: ${hasLabels} | Has values: ${hasValues}`;
                            }
                        }

                        return {
                            name: `History API: ${endpoint.split('/').pop().split('?')[0]}`,
                            success,
                            details,
                            data: hasData ? data : null
                        };
                    } catch (parseError) {
                        return {
                            name: `History API: ${endpoint.split('/').pop().split('?')[0]}`,
                            success: false,
                            details: `Error parsing JSON: ${parseError.message}`
                        };
                    }
                } else {
                    return {
                        name: `History API: ${endpoint.split('/').pop().split('?')[0]}`,
                        success: false,
                        details
                    };
                }
            } catch (error) {
                return {
                    name: `History API: ${endpoint.split('/').pop().split('?')[0]}`,
                    success: false,
                    details: `Network error: ${error.message}`
                };
            }
        }));

        this.results.apiChecks.push(...results);
    }

    /**
     * Check UI elements related to WebSocket and history data
     */
    checkUIElements() {
        // Check connection status indicator
        const statusElement = document.getElementById('realtime-connection-status');
        if (statusElement) {
            const statusClass = statusElement.className;
            const isConnected = statusClass.includes('connected');
            const isDisconnected = statusClass.includes('disconnected');
            const statusText = statusElement.textContent.trim();

            this.results.uiChecks.push({
                name: 'Connection Status Element',
                success: true,
                details: `Element found | Class: "${statusClass}" | Text: "${statusText}" | Connected: ${isConnected} | Disconnected: ${isDisconnected}`
            });
        } else {
            this.results.uiChecks.push({
                name: 'Connection Status Element',
                success: false,
                details: 'Element not found in DOM'
            });
        }

        // Check temperature history element
        const tempHistoryElement = document.querySelector('.temperature-history-chart');
        if (tempHistoryElement) {
            const hasCanvas = !!tempHistoryElement.querySelector('canvas');
            const hasNoData = !!tempHistoryElement.querySelector('.no-data');
            const isEmpty = tempHistoryElement.innerHTML.trim() === '';

            this.results.uiChecks.push({
                name: 'Temperature History Element',
                success: true,
                details: `Element found | Has canvas: ${hasCanvas} | Has no-data message: ${hasNoData} | Is empty: ${isEmpty}`
            });
        } else {
            this.results.uiChecks.push({
                name: 'Temperature History Element',
                success: false,
                details: 'Element not found in DOM'
            });
        }
    }

    /**
     * Display diagnostic results
     */
    displayResults() {
        console.log('Diagnostic Results:', this.results);

        // Create results container if it doesn't exist
        let resultsContainer = document.getElementById('diagnostics-results');
        if (!resultsContainer) {
            resultsContainer = document.createElement('div');
            resultsContainer.id = 'diagnostics-results';
            resultsContainer.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                width: 400px;
                max-height: 80vh;
                overflow-y: auto;
                background: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 15px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                z-index: 10000;
                font-family: monospace;
                font-size: 12px;
            `;
            document.body.appendChild(resultsContainer);
        }

        // Generate HTML for results
        const html = `
            <h2 style="margin-top: 0;">IoTSphere Diagnostics</h2>
            <p>Device ID: ${this.deviceId}</p>
            <p>Time: ${new Date().toLocaleTimeString()}</p>

            <h3>WebSocket Checks</h3>
            <ul style="padding-left: 20px;">
                ${this.results.websocketChecks.map(check => `
                    <li style="margin-bottom: 10px;">
                        <div style="color: ${check.success ? 'green' : 'red'}">
                            <strong>${check.name}:</strong> ${check.success ? 'Success' : 'Failed'}
                        </div>
                        <div style="font-size: 11px; color: #666;">${check.details}</div>
                    </li>
                `).join('')}
            </ul>

            <h3>API Checks</h3>
            <ul style="padding-left: 20px;">
                ${this.results.apiChecks.map(check => `
                    <li style="margin-bottom: 10px;">
                        <div style="color: ${check.success ? 'green' : 'red'}">
                            <strong>${check.name}:</strong> ${check.success ? 'Success' : 'Failed'}
                        </div>
                        <div style="font-size: 11px; color: #666;">${check.details}</div>
                    </li>
                `).join('')}
            </ul>

            <h3>UI Element Checks</h3>
            <ul style="padding-left: 20px;">
                ${this.results.uiChecks.map(check => `
                    <li style="margin-bottom: 10px;">
                        <div style="color: ${check.success ? 'green' : 'red'}">
                            <strong>${check.name}:</strong> ${check.success ? 'Found' : 'Not Found'}
                        </div>
                        <div style="font-size: 11px; color: #666;">${check.details}</div>
                    </li>
                `).join('')}
            </ul>

            <button id="close-diagnostics" style="
                padding: 5px 10px;
                background: #f3f3f3;
                border: 1px solid #ccc;
                border-radius: 3px;
                cursor: pointer;
                margin-top: 10px;
            ">Close</button>
        `;

        resultsContainer.innerHTML = html;

        // Add close button handler
        document.getElementById('close-diagnostics').addEventListener('click', () => {
            resultsContainer.remove();
        });
    }
}

// Initialize the diagnostics tool
window.webSocketDiagnostics = new WebSocketDiagnostics();

// Add a button to run the diagnostics
function addDiagnosticsButton() {
    const button = document.createElement('button');
    button.textContent = 'Run Diagnostics';
    button.id = 'run-diagnostics-button';
    button.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 8px 15px;
        background: #007bff;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        z-index: 10000;
        font-family: sans-serif;
        font-size: 14px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    `;
    button.addEventListener('click', () => {
        window.webSocketDiagnostics.runAllTests();
    });

    document.body.appendChild(button);
}

// Auto-run diagnostics on page load after 2 seconds
setTimeout(() => {
    addDiagnosticsButton();
    // Uncomment to auto-run diagnostics
    // window.webSocketDiagnostics.runAllTests();
}, 2000);
