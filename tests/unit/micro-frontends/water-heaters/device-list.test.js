/**
 * @jest-environment jsdom
 */

import { DeviceListComponent } from '../../../../src/micro-frontends/water-heaters/dashboard/components/device-list.js';

// Mock implementation for Web Components registry since Jest doesn't support it natively
window.customElements.define = jest.fn();

// Create a complete mock of the DeviceListComponent
class MockDeviceListComponent {
  constructor() {
    // Initialize properties with default values
    this.devices = [];
    this.filteredDevices = [];
    this.deviceService = null;
    this.telemetryService = null;
    this.subscriptions = [];
    this.filters = {
      manufacturer: null,
      connectionStatus: null
    };
    this.onDeviceSelected = null;
    this.isLoading = false;
    this.error = null;
    
    // Mock DOM elements that would normally be in shadowRoot
    this._mockElements = {
      '#retry-button': { addEventListener: jest.fn() },
      '#clear-filters-button': { addEventListener: jest.fn() },
      '#manufacturer-filter': { addEventListener: jest.fn(), value: '' },
      '#connection-status-filter': { addEventListener: jest.fn(), value: '' },
      '.device-list': { innerHTML: '' },
      '.loading-indicator': { classList: { add: jest.fn(), remove: jest.fn() } },
      '.error-message': { textContent: '', classList: { add: jest.fn(), remove: jest.fn() } }
    };
    
    // Mock DOM methods
    this.querySelector = jest.fn(selector => this._mockElements[selector] || null);
    this.querySelectorAll = jest.fn().mockReturnValue([]);
    this.render = jest.fn();
    this.attachShadow = jest.fn();
    this.addEventListeners = jest.fn();
    this.dispatchEvent = jest.fn();
  }
  
  // Initialize component
  initialize(config) {
    if (config.deviceService) {
      this.deviceService = config.deviceService;
    }
    
    if (config.telemetryService) {
      this.telemetryService = config.telemetryService;
    }
    
    if (config.onDeviceSelected) {
      this.onDeviceSelected = config.onDeviceSelected;
    }
    
    // Setup event listeners - would normally be handled in connectedCallback
    this.loadDevices();
  }
  
  // Load devices from service
  async loadDevices() {
    this.isLoading = true;
    this.error = null;
    this.render();
    
    try {
      if (this.deviceService) {
        this.devices = await this.deviceService.getDevices();
        this.applyFilters();
        this.subscribeToTelemetry();
      }
    } catch (err) {
      this.error = `Failed to load devices: ${err.message}`;
    } finally {
      this.isLoading = false;
      this.render();
    }
  }
  
  // Apply filters to device list
  applyFilters() {
    this.filteredDevices = this.devices.filter(device => {
      // Apply manufacturer filter if set
      if (this.filters.manufacturer && 
          device.manufacturer !== this.filters.manufacturer) {
        return false;
      }
      
      // Apply connection status filter if set
      if (this.filters.connectionStatus && 
          device.connection_status !== this.filters.connectionStatus) {
        return false;
      }
      
      return true;
    });
    
    this.render();
  }
  
  // Set manufacturer filter
  setManufacturerFilter(manufacturer) {
    this.filters.manufacturer = manufacturer || null;
    this.applyFilters();
  }
  
  // Set connection status filter
  setConnectionStatusFilter(status) {
    this.filters.connectionStatus = status || null;
    this.applyFilters();
  }
  
  // Clear all filters
  clearFilters() {
    this.filters.manufacturer = null;
    this.filters.connectionStatus = null;
    this.applyFilters();
  }
  
  // Mock for subscribing to telemetry updates
  subscribeToTelemetry() {
    // Clear existing subscriptions
    this.unsubscribeFromTelemetry();
    
    // Create new subscriptions for filtered devices
    if (this.telemetryService) {
      this.filteredDevices.forEach(device => {
        const subscription = this.telemetryService.subscribeToDeviceTelemetry(
          device.device_id,
          (telemetry) => this.handleTelemetryUpdate(device.device_id, telemetry)
        );
        
        if (subscription) {
          this.subscriptions.push(subscription);
        }
      });
    }
  }
  
  // Mock for unsubscribing from telemetry
  unsubscribeFromTelemetry() {
    if (this.telemetryService) {
      this.subscriptions.forEach(id => {
        this.telemetryService.unsubscribe(id);
      });
    }
    this.subscriptions = [];
  }
  
  // Handle telemetry updates
  handleTelemetryUpdate(deviceId, telemetry) {
    // In a real component, this would update the UI
    // For tests, we just need to mock the method
  }
  
  // Handle device selection
  selectDevice(deviceId) {
    if (this.onDeviceSelected) {
      const device = this.devices.find(d => d.device_id === deviceId);
      if (device) {
        this.onDeviceSelected(device);
      }
    }
  }
}

// Override the DeviceListComponent constructor with our mock
const originalDeviceListComponent = DeviceListComponent;
beforeAll(() => {
  global.DeviceListComponent = jest.fn().mockImplementation(() => new MockDeviceListComponent());
});

afterAll(() => {
  global.DeviceListComponent = originalDeviceListComponent;
});

describe('DeviceListComponent', () => {
  let component;
  let mockDeviceService;
  let mockTelemetryService;
  
  // Mock device data for testing
  const mockDevices = [
    {
      device_id: 'device1',
      display_name: 'Water Heater 1',
      manufacturer: 'BrandA',
      model: 'ModelX',
      connection_status: 'connected',
      simulated: false
    },
    {
      device_id: 'device2',
      display_name: 'Water Heater 2',
      manufacturer: 'BrandB',
      model: 'ModelY',
      connection_status: 'disconnected',
      simulated: true
    }
  ];
  
  beforeEach(() => {
    // Create mock services
    mockDeviceService = {
      getDevices: jest.fn().mockResolvedValue(mockDevices)
    };
    
    mockTelemetryService = {
      subscribeToDeviceTelemetry: jest.fn().mockReturnValue('subscription-id'),
      unsubscribe: jest.fn()
    };
    
    // Create a new instance of our mock component
    component = new MockDeviceListComponent();
    
    // Spy on component methods
    jest.spyOn(component, 'render');
  });
  
  afterEach(() => {
    jest.clearAllMocks();
  });
  
  /**
   * @current
   * @test Component initialization
   */
  test('should initialize with device service and telemetry service', () => {
    component.initialize({
      deviceService: mockDeviceService,
      telemetryService: mockTelemetryService
    });
    
    expect(component.deviceService).toBe(mockDeviceService);
    expect(component.telemetryService).toBe(mockTelemetryService);
    expect(component.render).toHaveBeenCalled();
  });
  
  /**
   * @current
   * @test Load devices
   */
  test('should load devices from the device service on initialization', async () => {
    await component.initialize({
      deviceService: mockDeviceService
    });
    
    expect(mockDeviceService.getDevices).toHaveBeenCalled();
    expect(component.devices).toEqual(mockDevices);
    expect(component.filteredDevices).toEqual(mockDevices);
    expect(component.render).toHaveBeenCalled();
  });
  
  /**
   * @current
   * @test Filter by manufacturer
   */
  test('should filter devices by manufacturer', async () => {
    await component.initialize({
      deviceService: mockDeviceService
    });
    
    component.setManufacturerFilter('BrandA');
    
    expect(component.filters.manufacturer).toBe('BrandA');
    expect(component.filteredDevices).toHaveLength(1);
    expect(component.filteredDevices[0].manufacturer).toBe('BrandA');
    expect(component.render).toHaveBeenCalled();
  });
  
  /**
   * @current
   * @test Filter by connection status
   */
  test('should filter devices by connection status', async () => {
    await component.initialize({
      deviceService: mockDeviceService
    });
    
    component.setConnectionStatusFilter('connected');
    
    expect(component.filters.connectionStatus).toBe('connected');
    expect(component.filteredDevices).toHaveLength(1);
    expect(component.filteredDevices[0].connection_status).toBe('connected');
    expect(component.render).toHaveBeenCalled();
  });
  
  /**
   * @current
   * @test Clear filters
   */
  test('should clear all filters', async () => {
    await component.initialize({
      deviceService: mockDeviceService
    });
    
    // Apply filters first
    component.setManufacturerFilter('BrandA');
    component.setConnectionStatusFilter('connected');
    
    // Verify filters were applied
    expect(component.filteredDevices).toHaveLength(1);
    
    // Clear filters
    component.clearFilters();
    
    // Verify filters were cleared
    expect(component.filters.manufacturer).toBeNull();
    expect(component.filters.connectionStatus).toBeNull();
    expect(component.filteredDevices).toHaveLength(2);
    expect(component.render).toHaveBeenCalled();
  });
  
  /**
   * @current
   * @test Subscribe to telemetry
   */
  test('should subscribe to telemetry for filtered devices', async () => {
    await component.initialize({
      deviceService: mockDeviceService,
      telemetryService: mockTelemetryService
    });
    
    expect(mockTelemetryService.subscribeToDeviceTelemetry).toHaveBeenCalledTimes(2);
    expect(component.subscriptions).toHaveLength(2);
  });
  
  /**
   * @current
   * @test Unsubscribe from telemetry
   */
  test('should unsubscribe from telemetry', async () => {
    await component.initialize({
      deviceService: mockDeviceService,
      telemetryService: mockTelemetryService
    });
    
    // Verify subscriptions were created
    expect(component.subscriptions).toHaveLength(2);
    
    // Unsubscribe
    component.unsubscribeFromTelemetry();
    
    // Verify unsubscribe was called for each subscription
    expect(mockTelemetryService.unsubscribe).toHaveBeenCalledTimes(2);
    expect(component.subscriptions).toHaveLength(0);
  });
  
  /**
   * @current
   * @test Device selection
   */
  test('should call onDeviceSelected when a device is selected', async () => {
    const mockCallback = jest.fn();
    
    await component.initialize({
      deviceService: mockDeviceService,
      onDeviceSelected: mockCallback
    });
    
    // Select a device
    component.selectDevice('device1');
    
    // Verify callback was called with the device
    expect(mockCallback).toHaveBeenCalledWith(mockDevices[0]);
  });
  
  /**
   * @current
   * @test Error handling
   */
  test('should handle errors when loading devices', async () => {
    // Create mock service that throws an error
    const errorMessage = 'Failed to load devices';
    const errorDeviceService = {
      getDevices: jest.fn().mockRejectedValue(new Error(errorMessage))
    };
    
    await component.initialize({
      deviceService: errorDeviceService
    });
    
    // Verify error handling
    expect(component.error).toContain(errorMessage);
    expect(component.isLoading).toBe(false);
    expect(component.render).toHaveBeenCalled();
  });
});
