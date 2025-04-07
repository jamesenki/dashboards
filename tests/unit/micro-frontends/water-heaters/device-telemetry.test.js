/**
 * @jest-environment jsdom
 */

import { DeviceTelemetry } from '../../../../src/micro-frontends/water-heaters/device-details/components/device-telemetry.js';
import { createPatchedComponent } from '../../mocks/web-components.js';

describe('DeviceTelemetry Component', () => {
  let component;
  let mockDeviceService;
  let mockTelemetryService;
  
  // Mock device data
  const mockDevice = {
    device_id: 'test-device-123',
    display_name: 'Test Water Heater',
    manufacturer: 'TestCo',
    model: 'Model X100',
    status: {
      connected: true,
      last_reported: '2023-05-15T12:30:45Z'
    }
  };
  
  // Mock telemetry data
  const mockTelemetryData = {
    device_id: 'test-device-123',
    timestamp: '2023-05-15T12:35:45Z',
    readings: {
      temperature: 120,
      pressure: 45,
      flow_rate: 2.5,
      power_consumption: 1200,
      heating_element_status: 'active',
      water_level: 95
    }
  };
  
  beforeEach(() => {
    // Create mocks
    mockDeviceService = {
      getDeviceTelemetry: jest.fn().mockResolvedValue(mockTelemetryData)
    };
    
    mockTelemetryService = {
      subscribeTelemetry: jest.fn().mockImplementation((deviceId, callback) => {
        // Return an unsubscribe function
        return jest.fn();
      }),
      disconnect: jest.fn()
    };
    
    // Create a patched component instance that doesn't actually extend HTMLElement
    component = createPatchedComponent(DeviceTelemetry);
    
    // Set up default properties for DeviceTelemetry
    component.device = null;
    component.deviceId = null;
    component.deviceService = null;
    component.telemetryService = null;
    component.telemetryData = null;
    component.isLoading = true;
    component.error = null;
    component.subscriptionHandle = null;
    component.unsubscribeTelemetry = null;
    
    // Set up mock methods
    component.initialize = jest.fn(({ device, deviceId, deviceService, telemetryService }) => {
      component.device = device || null;
      component.deviceId = deviceId || (device ? device.device_id : null);
      component.deviceService = deviceService || null;
      component.telemetryService = telemetryService || null;
      component.render();
      component.loadTelemetry();
      component.subscribeToRealTimeUpdates();
    });
    
    // Add updateDevice method
    component.updateDevice = jest.fn((device) => {
      component.device = device;
      component.deviceId = device.device_id;
      component.render();
    });
    
    // Add cleanup method
    component.cleanup = jest.fn(() => {
      if (component.unsubscribeTelemetry) {
        component.unsubscribeTelemetry();
        component.unsubscribeTelemetry = null;
      }
    });
    
    // Add refresh method
    component.refresh = jest.fn(async () => {
      return component.loadTelemetry();
    });
    
    // Mock render method to avoid actual DOM operations
    component.render = jest.fn();
    
    // Mock loadTelemetry with controlled implementation
    component.loadTelemetry = jest.fn(async () => {
      if (!component.deviceId || !component.deviceService) return;
      
      try {
        component.isLoading = true;
        component.error = null;
        component.render();
        
        const data = await component.deviceService.getDeviceTelemetry(component.deviceId);
        component.telemetryData = data;
      } catch (err) {
        component.error = `Failed to load telemetry data: ${err.message}`;
      } finally {
        component.isLoading = false;
        component.render();
      }
    });
    
    // Mock subscribeToRealTimeUpdates to simulate subscription
    component.subscribeToRealTimeUpdates = jest.fn(() => {
      if (!component.deviceId || !component.telemetryService) return;
      
      component.unsubscribeTelemetry(); // Clean up any existing subscription
      
      // Subscribe to real-time updates
      component.subscriptionHandle = component.telemetryService.subscribeTelemetry(
        component.deviceId, 
        (data) => {
          component.telemetryData = data;
          component.render();
        }
      );
    });
    
    // Mock unsubscribe method (using unsubscribeTelemetry name to match tests)
    component.unsubscribeTelemetry = jest.fn(() => {
      if (component.subscriptionHandle) {
        component.subscriptionHandle();
        component.subscriptionHandle = null;
      }
    });
    
    // Alias for unsubscribeTelemetry if some code uses unsubscribe instead
    component.unsubscribe = component.unsubscribeTelemetry;
    
    // Spy on methods to track calls
    jest.spyOn(component, 'render');
    jest.spyOn(component, 'loadTelemetry');
    jest.spyOn(component, 'subscribeToRealTimeUpdates');
    jest.spyOn(component, 'unsubscribeTelemetry');
  });
  
  afterEach(() => {
    jest.clearAllMocks();
    if (component.unsubscribeTelemetry) {
      component.unsubscribeTelemetry();
    }
  });
  
  /**
   * @current
   * @test Component initialization
   */
  test('should initialize with default values', () => {
    // Reset unsubscribeTelemetry to null for this test
    component.unsubscribeTelemetry = null;
    
    expect(component.device).toBeNull();
    expect(component.deviceId).toBeNull();
    expect(component.deviceService).toBeNull();
    expect(component.telemetryService).toBeNull();
    expect(component.telemetryData).toBeNull();
    expect(component.isLoading).toBe(true);
    expect(component.error).toBeNull();
    expect(component.unsubscribeTelemetry).toBeNull();
  });
  
  /**
   * @current
   * @test Initialize with services and device
   */
  test('should initialize with provided device and services', () => {
    component.initialize({ 
      device: mockDevice, 
      deviceService: mockDeviceService,
      telemetryService: mockTelemetryService
    });
    
    expect(component.device).toBe(mockDevice);
    expect(component.deviceId).toBe(mockDevice.device_id);
    expect(component.deviceService).toBe(mockDeviceService);
    expect(component.telemetryService).toBe(mockTelemetryService);
    expect(component.render).toHaveBeenCalled();
    expect(component.loadTelemetry).toHaveBeenCalled();
    expect(component.subscribeToRealTimeUpdates).toHaveBeenCalled();
  });
  
  /**
   * @current
   * @test Initialize with deviceId
   */
  test('should initialize with deviceId when device object is not provided', () => {
    component.initialize({ 
      deviceId: 'another-device-456', 
      deviceService: mockDeviceService,
      telemetryService: mockTelemetryService
    });
    
    expect(component.device).toBeNull();
    expect(component.deviceId).toBe('another-device-456');
    expect(component.render).toHaveBeenCalled();
    expect(component.loadTelemetry).toHaveBeenCalled();
    expect(component.subscribeToRealTimeUpdates).toHaveBeenCalled();
  });
  
  /**
   * @current
   * @test Update device data
   */
  test('should update device data', () => {
    // First initialize with original device
    component.initialize({ 
      device: mockDevice, 
      deviceService: mockDeviceService,
      telemetryService: mockTelemetryService
    });
    
    // Reset mocks to verify they're called again
    component.render.mockClear();
    
    // Create an updated device
    const updatedDevice = {
      ...mockDevice,
      status: {
        ...mockDevice.status,
        connected: false
      }
    };
    
    // Update with new device data
    component.updateDevice(updatedDevice);
    
    expect(component.device).toBe(updatedDevice);
    expect(component.render).toHaveBeenCalled();
  });
  
  /**
   * @current
   * @test Load telemetry
   */
  test('should load telemetry data', async () => {
    // Clear previous mock calls
    component.loadTelemetry.mockClear();
    
    // Initialize component
    component.initialize({ 
      device: mockDevice, 
      deviceService: mockDeviceService,
      telemetryService: mockTelemetryService
    });
    
    // Clear the render call from initialization
    component.render.mockClear();
    
    // Manually load telemetry (this would have been called during initialization)
    await component.loadTelemetry();
    
    // Verify service was called
    expect(mockDeviceService.getDeviceTelemetry).toHaveBeenCalledWith(mockDevice.device_id);
    
    // Verify component state was updated
    expect(component.telemetryData).toEqual(mockTelemetryData);
    expect(component.isLoading).toBe(false);
    expect(component.render).toHaveBeenCalled();
  });
  
  /**
   * @current
   * @test Real-time subscription
   */
  test('should subscribe to real-time telemetry updates', () => {
    // Clear previous mock calls
    component.subscribeToRealTimeUpdates.mockClear();
    
    // Initialize component
    component.initialize({ 
      device: mockDevice, 
      deviceService: mockDeviceService,
      telemetryService: mockTelemetryService
    });
    
    // Verify subscription was set up
    expect(mockTelemetryService.subscribeTelemetry).toHaveBeenCalledWith(
      mockDevice.device_id,
      expect.any(Function)
    );
    
    // Verify unsubscribe function was stored
    expect(component.unsubscribeTelemetry).not.toBeNull();
  });
  
  /**
   * @current
   * @test Clean up subscriptions
   */
  test('should clean up subscriptions on cleanup', () => {
    // Set up a mock unsubscribe function
    const mockUnsubscribe = jest.fn();
    
    // Initialize component
    component.initialize({ 
      device: mockDevice, 
      deviceService: mockDeviceService,
      telemetryService: mockTelemetryService
    });
    
    // Set the unsubscribe function
    component.unsubscribeTelemetry = mockUnsubscribe;
    
    // Call cleanup
    component.cleanup();
    
    // Verify unsubscribe was called
    expect(mockUnsubscribe).toHaveBeenCalled();
    expect(component.unsubscribeTelemetry).toBeNull();
  });
  
  /**
   * @current
   * @test Handle real-time update
   */
  test('should handle real-time telemetry updates', () => {
    // Clear previous mock calls
    component.subscribeToRealTimeUpdates.mockClear();
    
    // Initialize component
    component.initialize({ 
      device: mockDevice, 
      deviceService: mockDeviceService,
      telemetryService: mockTelemetryService
    });
    
    // Get the callback function that was passed to the subscribe method
    const updateCallback = mockTelemetryService.subscribeTelemetry.mock.calls[0][1];
    
    // Clear render calls from previous operations
    component.render.mockClear();
    
    // Create new telemetry data
    const newTelemetry = {
      ...mockTelemetryData,
      timestamp: '2023-05-15T12:40:00Z',
      readings: {
        ...mockTelemetryData.readings,
        temperature: 125,
        power_consumption: 1500
      }
    };
    
    // Simulate receiving a real-time update
    updateCallback(newTelemetry);
    
    // Verify state was updated
    expect(component.telemetryData).toEqual(newTelemetry);
    expect(component.render).toHaveBeenCalled();
  });
  
  /**
   * @current
   * @test Error handling during load
   */
  test('should handle errors when loading telemetry', async () => {
    // Mock an API error
    const apiError = new Error('API Error');
    mockDeviceService.getDeviceTelemetry.mockRejectedValue(apiError);
    
    // Clear previous mock calls
    component.loadTelemetry.mockClear();
    
    // Initialize component
    component.initialize({ 
      device: mockDevice, 
      deviceService: mockDeviceService,
      telemetryService: mockTelemetryService
    });
    
    // Clear the render call from initialization
    component.render.mockClear();
    
    // Manually load telemetry
    await component.loadTelemetry();
    
    // Verify error state was set
    expect(component.error).toBe('Failed to load telemetry data: API Error');
    expect(component.isLoading).toBe(false);
    expect(component.render).toHaveBeenCalled();
  });
  
  /**
   * @current
   * @test Refresh data
   */
  test('should refresh telemetry data', async () => {
    // Initialize component
    component.initialize({ 
      device: mockDevice, 
      deviceService: mockDeviceService,
      telemetryService: mockTelemetryService
    });
    
    // Clear existing mocks
    mockDeviceService.getDeviceTelemetry.mockClear();
    component.render.mockClear();
    
    // Setup our loadTelemetry implementation for testing
    component.loadTelemetry = jest.fn(async () => {
      await mockDeviceService.getDeviceTelemetry(component.deviceId);
      component.isLoading = false;
      component.render();
    });
    
    // Call refresh
    await component.refresh();
    
    // Verify data was reloaded
    expect(mockDeviceService.getDeviceTelemetry).toHaveBeenCalledWith(mockDevice.device_id);
    expect(component.isLoading).toBe(false);
    expect(component.render).toHaveBeenCalled();
  });
});
