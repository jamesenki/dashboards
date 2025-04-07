/**
 * Unit tests for the device metadata handler component
 * Following TDD principles, we define expected behavior before implementation
 */
const { expect } = require('chai');
const sinon = require('sinon');
const { JSDOM } = require('jsdom');

// Create a mock DOM environment for testing
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
    <div id="deviceTemperature"></div>
    <div id="devicePressure"></div>
    <div id="deviceStatus"></div>
  </div>
</body>
</html>
`);

// Mock the global window and document objects
global.window = dom.window;
global.document = dom.window.document;

// Import the handler (will be implemented later)
const DeviceMetadataHandler = require('../../../frontend/static/js/device-metadata-handler');

describe('DeviceMetadataHandler', () => {
  let handler;
  let fetchStub;
  let socketStub;
  
  beforeEach(() => {
    // Mock the fetch API
    fetchStub = sinon.stub(global, 'fetch');
    
    // Mock WebSocket
    global.WebSocket = class MockWebSocket {
      constructor() {
        this.addEventListener = sinon.spy();
        this.send = sinon.spy();
        this.close = sinon.spy();
      }
    };
    
    socketStub = {
      onopen: null,
      onmessage: null,
      onclose: null,
      onerror: null,
      send: sinon.spy(),
      close: sinon.spy()
    };
    
    global.WebSocket = function() {
      return socketStub;
    };
    
    // Create a new handler instance
    handler = new DeviceMetadataHandler('wh-test-001');
  });
  
  afterEach(() => {
    // Clean up stubs
    fetchStub.restore();
    if (global.WebSocket.restore) {
      global.WebSocket.restore();
    }
  });
  
  describe('initialization', () => {
    it('should initialize with the provided device ID', () => {
      expect(handler.deviceId).to.equal('wh-test-001');
    });
    
    it('should fetch device metadata on initialization', async () => {
      const metadata = {
        device_id: 'wh-test-001',
        manufacturer: 'AquaTech',
        model: 'HeatMaster 5000',
        serial_number: 'AT-HM5K-12345',
        installation_date: '2024-01-15T12:00:00Z',
        location: {
          building: 'Main Campus',
          floor: '3',
          room: '304B'
        }
      };
      
      fetchStub.resolves({
        ok: true,
        json: async () => metadata
      });
      
      await handler.fetchMetadata();
      
      expect(fetchStub.calledOnce).to.be.true;
      expect(fetchStub.firstCall.args[0]).to.include('/api/devices/wh-test-001/metadata');
    });
  });
  
  describe('display metadata', () => {
    it('should update the UI with device metadata', async () => {
      const metadata = {
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
      };
      
      fetchStub.resolves({
        ok: true,
        json: async () => metadata
      });
      
      await handler.fetchMetadata();
      handler.updateMetadataDisplay();
      
      expect(document.getElementById('deviceManufacturer').textContent).to.include('AquaTech');
      expect(document.getElementById('deviceModel').textContent).to.include('HeatMaster 5000');
      expect(document.getElementById('deviceSerialNumber').textContent).to.include('AT-HM5K-12345');
      expect(document.getElementById('deviceLocation').textContent).to.include('Main Campus');
      expect(document.getElementById('deviceSpecifications').textContent).to.include('80');
    });
    
    it('should handle missing metadata gracefully', async () => {
      fetchStub.resolves({
        ok: false,
        status: 404,
        json: async () => ({ error: 'Device metadata not found' })
      });
      
      await handler.fetchMetadata();
      handler.updateMetadataDisplay();
      
      expect(document.getElementById('deviceManufacturer').textContent).to.include('Not available');
    });
  });
  
  describe('metadata change events', () => {
    it('should subscribe to metadata change events', () => {
      handler.subscribeToMetadataChanges();
      
      expect(global.WebSocket).to.have.been.calledOnce;
      expect(global.WebSocket.firstCall.args[0]).to.include('/api/events/device/wh-test-001/metadata');
    });
    
    it('should update UI when metadata changes are received', () => {
      // Mock an event message
      const event = {
        device_id: 'wh-test-001',
        change_type: 'location_update',
        new_value: {
          building: 'Main Campus',
          floor: '4',
          room: '401A'
        }
      };
      
      handler.metadata = {
        device_id: 'wh-test-001',
        manufacturer: 'AquaTech',
        model: 'HeatMaster 5000',
        location: {
          building: 'Main Campus',
          floor: '3',
          room: '304B'
        }
      };
      
      // Subscribe to metadata changes
      handler.subscribeToMetadataChanges();
      
      // Simulate receiving an event
      socketStub.onmessage({ data: JSON.stringify(event) });
      
      // Check that the metadata was updated
      expect(handler.metadata.location.room).to.equal('401A');
      expect(handler.metadata.location.floor).to.equal('4');
      
      // Check that the UI was updated
      handler.updateMetadataDisplay();
      expect(document.getElementById('deviceLocation').textContent).to.include('401A');
    });
  });
});
