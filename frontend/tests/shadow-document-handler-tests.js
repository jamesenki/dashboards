/**
 * Shadow Document Handler Test Suite
 *
 * Tests the shadow document handler functionality, including:
 * - JavaScript syntax and structure
 * - Chart initialization and rendering
 * - Shadow document data processing
 * - Error handling and display
 *
 * This test suite follows TDD principles.
 */

// Mock dependencies for testing
class MockChartJS {
    constructor(ctx, config) {
        this.ctx = ctx;
        this.config = config;
        this.destroyed = false;
        MockChartJS.instances.push(this);
    }

    destroy() {
        this.destroyed = true;
    }

    update() {
        // Simulate chart update
    }

    static instances = [];
    static resetInstances() {
        MockChartJS.instances = [];
    }
}

// Test utilities
const TestUtils = {
    /**
     * Create a DOM fixture with necessary elements for testing
     */
    createDOMFixture() {
        // Clean up any previous fixture
        const existingFixture = document.getElementById('test-fixture');
        if (existingFixture) {
            document.body.removeChild(existingFixture);
        }

        // Create new fixture
        const fixture = document.createElement('div');
        fixture.id = 'test-fixture';

        // Add temperature chart container
        const chartContainer = document.createElement('div');
        chartContainer.id = 'temp-chart';
        chartContainer.className = 'chart-container';

        // Add canvas for chart
        const canvas = document.createElement('canvas');
        canvas.id = 'temperature-chart';
        chartContainer.appendChild(canvas);

        // Add history container
        const historyContainer = document.createElement('div');
        historyContainer.id = 'history-container';

        const historyChart = document.createElement('canvas');
        historyChart.id = 'history-temperature-chart';
        historyContainer.appendChild(historyChart);

        // Add error message container
        const errorContainer = document.createElement('div');
        errorContainer.id = 'chart-error-message';
        errorContainer.style.display = 'none';

        // Add shadow info container
        const shadowInfo = document.createElement('div');
        shadowInfo.id = 'shadow-info';

        // Assemble fixture
        fixture.appendChild(chartContainer);
        fixture.appendChild(historyContainer);
        fixture.appendChild(errorContainer);
        fixture.appendChild(shadowInfo);
        document.body.appendChild(fixture);

        return fixture;
    },

    /**
     * Create sample shadow document data for testing
     */
    createSampleShadowData(withHistory = true) {
        const now = new Date();

        let shadow = {
            device_id: 'test-wh-001',
            reported: {
                temperature: 120.5,
                pressure: 60.0,
                flow_rate: 3.2,
                energy_usage: 450.0,
                status: 'ONLINE',
                timestamp: now.toISOString()
            },
            desired: {
                temperature: 125.0
            },
            metadata: {
                last_updated: now.toISOString()
            }
        };

        if (withHistory) {
            shadow.history = [];

            // Generate 24 hours of data
            for (let i = 0; i < 24; i++) {
                const time = new Date(now);
                time.setHours(now.getHours() - i);

                shadow.history.push({
                    temperature: 120 + Math.sin(i * 0.5) * 5,
                    pressure: 60 + Math.cos(i * 0.3) * 3,
                    flow_rate: 3 + Math.sin(i * 0.2) * 0.5,
                    energy_usage: 450 + Math.cos(i * 0.1) * 50,
                    timestamp: time.toISOString()
                });
            }
        }

        return shadow;
    },

    /**
     * Simulate API response
     */
    simulateAPIResponse(shadow) {
        return {
            json: () => Promise.resolve(shadow),
            ok: true,
            status: 200
        };
    },

    /**
     * Simulate failed API response
     */
    simulateAPIError(status, message) {
        return {
            json: () => Promise.resolve({ error: message }),
            ok: false,
            status: status,
            text: () => Promise.resolve(message)
        };
    }
};

/**
 * Test Suite for ShadowDocumentHandler
 */
describe('ShadowDocumentHandler', () => {
    let originalChart;
    let fixture;
    let handler;

    beforeEach(() => {
        // Save the original Chart constructor
        originalChart = window.Chart;
        window.Chart = MockChartJS;
        MockChartJS.resetInstances();

        // Setup DOM fixture
        fixture = TestUtils.createDOMFixture();

        // Mock fetch
        global.fetch = jest.fn();
    });

    afterEach(() => {
        // Restore original Chart constructor
        window.Chart = originalChart;

        // Clean up
        if (handler) {
            handler.cleanup();
        }
    });

    /**
     * Test ShadowDocumentHandler initialization
     */
    test('should initialize properly', () => {
        // Arrange
        const deviceId = 'test-wh-001';

        // Act
        handler = new ShadowDocumentHandler(deviceId);

        // Assert
        expect(handler.deviceId).toBe(deviceId);
        expect(handler.temperatureChart).toBeNull();
        expect(handler.initialized).toBe(false);
    });

    /**
     * Test loading shadow data
     */
    test('should load shadow data successfully', async () => {
        // Arrange
        const deviceId = 'test-wh-001';
        const sampleShadow = TestUtils.createSampleShadowData();
        global.fetch.mockResolvedValueOnce(TestUtils.simulateAPIResponse(sampleShadow));

        // Act
        handler = new ShadowDocumentHandler(deviceId);
        await handler.loadShadowData();

        // Assert
        expect(handler.shadowData).toEqual(sampleShadow);
        expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining(`/api/shadows/${deviceId}`));
        expect(handler.initialized).toBe(true);
    });

    /**
     * Test handling API errors
     */
    test('should handle API errors gracefully', async () => {
        // Arrange
        const deviceId = 'test-wh-001';
        global.fetch.mockResolvedValueOnce(TestUtils.simulateAPIError(404, 'Shadow not found'));

        // Act
        handler = new ShadowDocumentHandler(deviceId);
        await handler.loadShadowData();

        // Assert
        expect(handler.shadowData).toBeNull();
        expect(handler.error).toBe('Shadow not found');
        expect(document.getElementById('chart-error-message').style.display).not.toBe('none');
    });

    /**
     * Test initializing temperature chart
     */
    test('should initialize temperature chart with shadow data', async () => {
        // Arrange
        const deviceId = 'test-wh-001';
        const sampleShadow = TestUtils.createSampleShadowData();
        global.fetch.mockResolvedValueOnce(TestUtils.simulateAPIResponse(sampleShadow));

        // Act
        handler = new ShadowDocumentHandler(deviceId);
        await handler.loadShadowData();
        handler.initializeTemperatureChart();

        // Assert
        expect(handler.temperatureChart).not.toBeNull();
        expect(MockChartJS.instances.length).toBe(1);
        expect(MockChartJS.instances[0].config.data.datasets.length).toBeGreaterThan(0);
    });

    /**
     * Test handling missing history data
     */
    test('should handle missing history data', async () => {
        // Arrange
        const deviceId = 'test-wh-001';
        const sampleShadow = TestUtils.createSampleShadowData(false); // No history
        global.fetch.mockResolvedValueOnce(TestUtils.simulateAPIResponse(sampleShadow));

        // Act
        handler = new ShadowDocumentHandler(deviceId);
        await handler.loadShadowData();
        handler.initializeTemperatureChart();

        // Assert
        expect(handler.temperatureChart).not.toBeNull();
        expect(MockChartJS.instances.length).toBe(1);
        // Should still create chart even without history, just with less data
        expect(MockChartJS.instances[0].config.data.datasets[0].data.length).toBeLessThanOrEqual(1);
    });

    /**
     * Test properly cleaning up chart resources
     */
    test('should clean up chart resources before reinitializing', async () => {
        // Arrange
        const deviceId = 'test-wh-001';
        const sampleShadow = TestUtils.createSampleShadowData();
        global.fetch.mockResolvedValueOnce(TestUtils.simulateAPIResponse(sampleShadow));

        // Act - First initialization
        handler = new ShadowDocumentHandler(deviceId);
        await handler.loadShadowData();
        handler.initializeTemperatureChart();

        // Initial state
        const firstChart = handler.temperatureChart;
        expect(firstChart).not.toBeNull();

        // Act - Second initialization
        handler.initializeTemperatureChart();

        // Assert
        expect(firstChart.destroyed).toBe(true);
        expect(handler.temperatureChart).not.toBe(firstChart);
    });

    /**
     * Test updating chart with new data
     */
    test('should update chart with new shadow data', async () => {
        // Arrange
        const deviceId = 'test-wh-001';
        const initialShadow = TestUtils.createSampleShadowData();
        const updatedShadow = {...initialShadow};

        // Modify the updated shadow
        updatedShadow.reported.temperature = 130.0;
        if (updatedShadow.history && updatedShadow.history.length > 0) {
            updatedShadow.history[0].temperature = 130.0;
        }

        global.fetch.mockResolvedValueOnce(TestUtils.simulateAPIResponse(initialShadow));

        // Act - Initial setup
        handler = new ShadowDocumentHandler(deviceId);
        await handler.loadShadowData();
        handler.initializeTemperatureChart();

        // Get initial chart data
        const initialData = handler.temperatureChart.config.data.datasets[0].data.slice();

        // Act - Update shadow
        handler.updateShadowData(updatedShadow);

        // Assert
        expect(handler.shadowData).toEqual(updatedShadow);
        // Check that the chart data has been updated
        expect(handler.temperatureChart.config.data.datasets[0].data).not.toEqual(initialData);
    });
});

/**
 * Test Suite for history chart functionality
 */
describe('Temperature History Chart', () => {
    let originalChart;
    let fixture;
    let historyManager;

    beforeEach(() => {
        // Save the original Chart constructor
        originalChart = window.Chart;
        window.Chart = MockChartJS;
        MockChartJS.resetInstances();

        // Setup DOM fixture
        fixture = TestUtils.createDOMFixture();

        // Mock fetch
        global.fetch = jest.fn();
    });

    afterEach(() => {
        // Restore original Chart constructor
        window.Chart = originalChart;

        // Clean up
        if (historyManager && historyManager.cleanup) {
            historyManager.cleanup();
        }
    });

    /**
     * Test loading history data from the history API
     */
    test('should load history data from the correct API endpoint', async () => {
        // Arrange
        const deviceId = 'test-wh-001';
        const historyData = {
            temperature: Array(24).fill().map((_, i) => ({
                timestamp: new Date(Date.now() - i * 3600000).toISOString(),
                value: 120 + Math.sin(i) * 5
            })),
            pressure: Array(24).fill().map((_, i) => ({
                timestamp: new Date(Date.now() - i * 3600000).toISOString(),
                value: 60 + Math.cos(i) * 3
            })),
            flow_rate: Array(24).fill().map((_, i) => ({
                timestamp: new Date(Date.now() - i * 3600000).toISOString(),
                value: 3 + Math.sin(i) * 0.5
            })),
            energy_usage: Array(24).fill().map((_, i) => ({
                timestamp: new Date(Date.now() - i * 3600000).toISOString(),
                value: 450 + Math.cos(i) * 50
            }))
        };

        global.fetch.mockResolvedValueOnce(TestUtils.simulateAPIResponse(historyData));

        // Create a simple history manager for testing
        class HistoryManager {
            constructor(deviceId) {
                this.deviceId = deviceId;
                this.historyData = null;
                this.tempChart = null;
            }

            async loadHistoryData(days = 7) {
                try {
                    const response = await fetch(`/api/manufacturer/water-heaters/${this.deviceId}/history?days=${days}`);
                    if (!response.ok) {
                        throw new Error(`Failed to load history: ${response.status}`);
                    }

                    this.historyData = await response.json();
                    this.initializeChart();
                    return this.historyData;
                } catch (error) {
                    console.error('Error loading history:', error);
                    document.getElementById('chart-error-message').textContent = error.message;
                    document.getElementById('chart-error-message').style.display = 'block';
                    return null;
                }
            }

            initializeChart() {
                const canvas = document.getElementById('history-temperature-chart');
                if (!canvas) {
                    console.error('History chart canvas not found');
                    return;
                }

                if (this.tempChart) {
                    this.tempChart.destroy();
                }

                // Create chart config from history data
                const config = {
                    type: 'line',
                    data: {
                        datasets: [{
                            label: 'Temperature',
                            data: this.historyData.temperature.map(point => ({
                                x: new Date(point.timestamp),
                                y: point.value
                            }))
                        }]
                    }
                };

                this.tempChart = new Chart(canvas, config);
            }

            cleanup() {
                if (this.tempChart) {
                    this.tempChart.destroy();
                }
            }
        }

        // Act
        historyManager = new HistoryManager(deviceId);
        await historyManager.loadHistoryData();

        // Assert
        expect(global.fetch).toHaveBeenCalledWith(
            expect.stringContaining(`/api/manufacturer/water-heaters/${deviceId}/history?days=7`)
        );
        expect(historyManager.historyData).toEqual(historyData);
        expect(MockChartJS.instances.length).toBe(1);
    });

    /**
     * Test handling missing canvas
     */
    test('should handle missing chart canvas gracefully', async () => {
        // Arrange
        const deviceId = 'test-wh-001';
        const historyData = {
            temperature: []
        };

        global.fetch.mockResolvedValueOnce(TestUtils.simulateAPIResponse(historyData));

        // Remove canvas from DOM
        const canvas = document.getElementById('history-temperature-chart');
        canvas.parentNode.removeChild(canvas);

        // Create a simple history manager for testing
        class HistoryManager {
            constructor(deviceId) {
                this.deviceId = deviceId;
                this.historyData = null;
                this.tempChart = null;
                this.error = null;
            }

            async loadHistoryData() {
                try {
                    const response = await fetch(`/api/manufacturer/water-heaters/${this.deviceId}/history?days=7`);
                    if (!response.ok) {
                        throw new Error(`Failed to load history: ${response.status}`);
                    }

                    this.historyData = await response.json();
                    this.initializeChart();
                    return this.historyData;
                } catch (error) {
                    this.error = error.message;
                    console.error('Error loading history:', error);
                    return null;
                }
            }

            initializeChart() {
                const canvas = document.getElementById('history-temperature-chart');
                if (!canvas) {
                    this.error = 'History chart canvas not found';
                    console.error(this.error);
                    return;
                }

                // Create chart...
            }
        }

        // Act
        historyManager = new HistoryManager(deviceId);
        await historyManager.loadHistoryData();

        // Assert
        expect(historyManager.error).toBe('History chart canvas not found');
    });
});

// Run the tests
if (typeof jest !== 'undefined') {
    // Tests will be executed by Jest
    console.log('Tests ready to be executed by Jest');
} else {
    // Manual test execution in browser
    console.log('To run these tests, you need Jest installed. These are unit test specifications.');
}
