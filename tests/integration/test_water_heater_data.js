/**
 * Integration test for the water heater data architecture
 *
 * Tests the separation between device metadata in Asset DB and
 * device state in shadow documents, with proper event handling
 * for metadata changes
 */
const { expect } = require('chai');
const sinon = require('sinon');
const { JSDOM } = require('jsdom');

// Create a DOM environment for testing
const dom = new JSDOM(`
<!DOCTYPE html>
<html>
<body>
  <div id="deviceMetadata">
    <div id="deviceManufacturer"></div>
    <div id="deviceModel"></div>
    <div id="deviceSerialNumber"></div>
    <div id="deviceInstallationDate"></div>
    <div id="deviceLocation"></div>
    <div id="deviceSpecifications"></div>
  </div>
  <div id="deviceState">
    <div class="temperature-value"></div>
    <div class="pressure-value"></div>
    <div class="water-level-value"></div>
    <div class="heating-element-status"></div>
    <div id="realtime-connection-status"></div>
  </div>
</body>
</html>
`);

// Set up global window and document
global.window = dom.window;
global.document = dom.window.document;

// Import our handlers
const ShadowDocumentHandler = require('../../frontend/static/js/shadow-document-handler');
const DeviceMetadataHandler = require('../../frontend/static/js/device-metadata-handler');

// Mock WebSocket
global.WebSocket = class MockWebSocket {
  constructor() {
    this.onopen = null;
    this.onmessage = null;
    this.onclose = null;
    this.onerror = null;
    this.send = sinon.spy();
    this.close = sinon.spy();

    // Auto-trigger onopen to simulate connection
    setTimeout(() => {
      if (this.onopen) this.onopen();
    }, 10);
  }
};

describe('Water Heater Data Integration', () => {
  let shadowHandler;
  let metadataHandler;
  let fetchStub;
  let eventSpy;

  beforeEach(() => {
    // Mock fetch API
    fetchStub = sinon.stub(global, 'fetch');

    // Spy on custom events
    eventSpy = sinon.spy();
    document.addEventListener('deviceDataChanged', eventSpy);

    // Reset handlers
    window.shadowDocumentHandler = null;
    window.deviceMetadataHandler = null;
  });

  afterEach(() => {
    // Clean up
    fetchStub.restore();
    document.removeEventListener('deviceDataChanged', eventSpy);
  });

  it('should properly separate device metadata from state data', async () => {
    // Mock asset DB API response with metadata
    fetchStub.withArgs('/api/devices/wh-test-001/metadata')
      .resolves({
        ok: true,
        json: async () => ({
          device_id: 'wh-test-001',
          manufacturer: 'AquaTech',
          model: 'HeatMaster 5000',
          serial_number: 'AT-HM5K-12345',
          installation_date: '2024-01-15T12:00:00Z',
          location: {
            building: 'Main Campus',
            floor: '3',
            room: '304B'
          },
          specifications: {
            capacity: '80',
            voltage: '240',
            wattage: '4500'
          }
        })
      });

    // Mock shadow document API response with state data
    fetchStub.withArgs('/api/device/wh-test-001/shadow')
      .resolves({
        ok: true,
        json: async () => ({
          state: {
            reported: {
              temperature: '140',
              temperature_unit: 'F',
              pressure: '45',
              pressure_unit: 'PSI',
              heating_element: 'active',
              water_level: '75',
              water_level_unit: '%',
              status: 'online'
            }
          }
        })
      });

    // Initialize metadata handler
    metadataHandler = new DeviceMetadataHandler('wh-test-001');

    // Wait for metadata to be fetched
    await new Promise(resolve => setTimeout(resolve, 50));

    // Initialize shadow document handler
    shadowHandler = new ShadowDocumentHandler('wh-test-001');

    // Wait for shadow document to be fetched
    await new Promise(resolve => setTimeout(resolve, 50));

    // Verify metadata is displayed correctly
    expect(document.getElementById('deviceManufacturer').textContent).to.include('AquaTech');
    expect(document.getElementById('deviceModel').textContent).to.include('HeatMaster 5000');
    expect(document.getElementById('deviceLocation').textContent).to.include('Main Campus');

    // Verify state data is displayed correctly
    expect(document.querySelector('.temperature-value').textContent).to.include('140');

    // Simulate metadata change event (e.g., location update)
    const metadataEvent = {
      device_id: 'wh-test-001',
      change_type: 'location_update',
      new_value: {
        building: 'Main Campus',
        floor: '4',
        room: '401A'
      }
    };

    // Find the WebSocket onmessage handler for metadata and trigger it
    if (metadataHandler.ws && metadataHandler.ws.onmessage) {
      metadataHandler.ws.onmessage({ data: JSON.stringify(metadataEvent) });
    }

    // Wait for event processing
    await new Promise(resolve => setTimeout(resolve, 50));

    // Verify location was updated
    expect(document.getElementById('deviceLocation').textContent).to.include('401A');

    // Simulate shadow update event (e.g., temperature change)
    const shadowEvent = {
      type: 'shadow_update',
      data: {
        state: {
          reported: {
            temperature: '145',
            temperature_unit: 'F',
            heating_element: 'active'
          }
        }
      }
    };

    // Find the WebSocket onmessage handler for shadow and trigger it
    if (shadowHandler.ws && shadowHandler.ws.onmessage) {
      shadowHandler.ws.onmessage({ data: JSON.stringify(shadowEvent) });
    }

    // Wait for event processing
    await new Promise(resolve => setTimeout(resolve, 50));

    // Verify temperature was updated
    expect(document.querySelector('.temperature-value').textContent).to.include('145');

    // Verify metadata was not affected by state change
    expect(document.getElementById('deviceLocation').textContent).to.include('401A');
    expect(document.getElementById('deviceManufacturer').textContent).to.include('AquaTech');
  });

  it('should trigger appropriate events when metadata changes', async () => {
    // Set up the handlers
    metadataHandler = new DeviceMetadataHandler('wh-test-002');
    shadowHandler = new ShadowDocumentHandler('wh-test-002');

    // Mock API responses
    fetchStub.resolves({
      ok: true,
      json: async () => ({})
    });

    // Wait for initialization
    await new Promise(resolve => setTimeout(resolve, 50));

    // Create a specific event spy for deviceDataChanged
    const dataChangedSpy = sinon.spy();
    document.addEventListener('deviceDataChanged', dataChangedSpy);

    // Manually trigger a metadata change notification
    document.dispatchEvent(new CustomEvent('deviceMetadataChanged', {
      detail: {
        deviceId: 'wh-test-002',
        metadata: {
          manufacturer: 'ThermalTech',
          model: 'WaterMax 300',
          firmware_version: '2.1.0'
        },
        changeType: 'firmware_update'
      }
    }));

    // Wait for event propagation
    await new Promise(resolve => setTimeout(resolve, 50));

    // Verify the deviceDataChanged event was dispatched with the combined data
    expect(dataChangedSpy.called).to.be.true;

    // Clean up
    document.removeEventListener('deviceDataChanged', dataChangedSpy);
  });
});
