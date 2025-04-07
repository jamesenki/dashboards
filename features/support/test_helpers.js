/**
 * Helper utilities for BDD testing in IoTSphere
 * Following TDD principles - helpers to make test setup more robust
 */

// Create fallback elements when needed for testing
const ensureElementExists = async (page, selector, fallbackCreator) => {
  const element = await page.$(selector);
  if (!element && fallbackCreator) {
    await page.evaluate(fallbackCreator);
    return await page.$(selector);
  }
  return element;
};

// Mock shadow document data for testing
const mockShadowDocument = (deviceId, data = {}) => ({
  deviceId,
  state: {
    reported: {
      temperature: data.temperature || 135,
      temperatureUnit: data.temperatureUnit || "F",
      status: data.status || "online",
      heatingElement: data.heatingElement || "active",
      timestamp: data.timestamp || new Date().toISOString(),
      temperatureHistory: data.temperatureHistory || [
        { timestamp: new Date(Date.now() - 3600000).toISOString(), value: 132 },
        { timestamp: new Date(Date.now() - 2700000).toISOString(), value: 133 },
        { timestamp: new Date(Date.now() - 1800000).toISOString(), value: 134 },
        { timestamp: new Date(Date.now() - 900000).toISOString(), value: 135 },
        { timestamp: new Date().toISOString(), value: 135 },
      ],
    },
  },
});

// Mock metadata for testing
const mockDeviceMetadata = (deviceId, data = {}) => ({
  id: deviceId,
  deviceType: data.deviceType || "waterHeater",
  manufacturer: data.manufacturer || "Test Manufacturer",
  model: data.model || "Test Model",
  firmwareVersion: data.firmwareVersion || "1.0.0",
  location: data.location || "Test Location",
  installDate: data.installDate || new Date().toISOString().split("T")[0],
  capabilities: data.capabilities || ["temperature", "heating"],
});

// Helper to handle both shadow document and metadata mocking
const setupTestDevice = async (page, deviceId, options = {}) => {
  await page.evaluate(
    ({ deviceId, shadowData, metadataData }) => {
      // Store mock data in window object for test use
      window.testData = window.testData || {};
      window.testData[deviceId] = {
        shadowDocument: shadowData,
        metadata: metadataData,
      };

      // Setup handlers if they don't exist
      if (!window.shadowDocumentHandler) {
        window.shadowDocumentHandler = {
          ws: {
            onmessage: (event) => {
              const data = JSON.parse(event.data);
              console.log("Mock WebSocket received:", data);
              // Dispatch shadow update event
              document.dispatchEvent(
                new CustomEvent("shadow-update", {
                  detail: data.data?.state?.reported || {},
                })
              );
            },
            onclose: () => {
              console.log("Mock WebSocket connection closed");
              document.dispatchEvent(new CustomEvent("ws-disconnect"));
            },
            onopen: () => {
              console.log("Mock WebSocket connection opened");
              document.dispatchEvent(new CustomEvent("ws-connect"));
            },
          },
        };
      }
    },
    {
      deviceId,
      shadowData: options.shadowData || mockShadowDocument(deviceId, options.shadowOptions || {}),
      metadataData:
        options.metadataData || mockDeviceMetadata(deviceId, options.metadataOptions || {}),
    }
  );
};

// Setup real-time monitoring test environment
const setupRealTimeMonitoring = async (page, deviceId) => {
  // Use the integration test adapter that connects to the real WebSocket server
  const RealTimeTestAdapterIntegration = require("./realtime_test_adapter_integration");

  // Initialize the integration test adapter
  const adapter = new RealTimeTestAdapterIntegration(page);
  await adapter.initialize(deviceId);

  // Add test adapter to the page context
  page.realTimeAdapter = adapter;

  // The adapter now handles UI element creation through the actual RealTimeMonitor implementation
  console.log("Real-time monitoring integration test environment setup complete");

  return adapter;
};

module.exports = {
  ensureElementExists,
  mockShadowDocument,
  mockDeviceMetadata,
  setupTestDevice,
  setupRealTimeMonitoring,
};
