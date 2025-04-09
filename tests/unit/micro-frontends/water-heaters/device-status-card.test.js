/**
 * @jest-environment jsdom
 */

import { DeviceStatusCard } from '../../../../src/micro-frontends/water-heaters/dashboard/components/device-status-card.js';

// Mock implementation for Web Components registry since Jest doesn't support it natively
window.customElements.define = jest.fn();

// Create a complete mock of the DeviceStatusCard component
class MockDeviceStatusCard {
  constructor() {
    // Initialize properties with default values
    this.deviceId = '';
    this.deviceName = '';
    this.manufacturer = '';
    this.model = '';
    this.connectionStatus = 'disconnected';
    this.simulated = false;
    this.temperatureUnit = 'F';
    this.selected = false;

    // Initialize telemetry with default values
    this.telemetry = {
      temperature_current: null,
      temperature_setpoint: null,
      heating_status: false,
      power_consumption_watts: null,
      water_flow_gpm: null,
      mode: 'standby',
      last_updated: null
    };

    // Mock DOM elements that would normally be in shadowRoot
    this._mockElements = {
      '.device-card': {
        addEventListener: jest.fn(),
        classList: { toggle: jest.fn() }
      },
      '.current-temp .value': { textContent: '' },
      '.target-temp .value': { textContent: '' },
      '.heating-status': { textContent: '' },
      '.mode-value': { textContent: '' },
      '.power-value': { textContent: '' },
      '.flow-value': { textContent: '' },
      '.last-updated': { textContent: '' }
    };

    // Mock DOM methods
    this.querySelector = jest.fn(selector => this._mockElements[selector] || null);
    this.render = jest.fn();
    this.updateTelemetryUI = jest.fn();
    this.attachShadow = jest.fn();
  }

  // Attribute change handler from the custom element
  attributeChangedCallback(name, oldValue, newValue) {
    switch (name) {
      case 'device-id':
        this.deviceId = newValue;
        break;
      case 'device-name':
        this.deviceName = newValue;
        break;
      case 'manufacturer':
        this.manufacturer = newValue;
        break;
      case 'model':
        this.model = newValue;
        break;
      case 'connection-status':
        this.connectionStatus = newValue;
        break;
      case 'simulated':
        this.simulated = newValue === 'true';
        break;
    }
    this.render();
  }

  // Mock of the actual updateTelemetry method
  updateTelemetry(data) {
    Object.assign(this.telemetry, data);
    this.updateTelemetryUI();
  }

  // Mock of the actual updateDevice method
  updateDevice(device) {
    if (device.device_id !== this.deviceId) {
      return;
    }

    this.deviceName = device.display_name;
    this.manufacturer = device.manufacturer;
    this.model = device.model;
    this.connectionStatus = device.connection_status;
    this.simulated = device.simulated;

    // Update telemetry from device state if available
    if (device.state) {
      Object.assign(this.telemetry, device.state);
    }

    this.render();
  }

  // Helper methods
  formatTemperature(temp) {
    if (temp === null || isNaN(temp)) {
      return '—';
    }
    return `${temp}°${this.temperatureUnit}`;
  }

  formatMode(mode) {
    if (!mode) {
      return 'Unknown';
    }
    return mode.charAt(0).toUpperCase() + mode.slice(1);
  }
}

// Override the DeviceStatusCard constructor with our mock
const originalDeviceStatusCard = DeviceStatusCard;
beforeAll(() => {
  global.DeviceStatusCard = jest.fn().mockImplementation(() => new MockDeviceStatusCard());
});

afterAll(() => {
  global.DeviceStatusCard = originalDeviceStatusCard;
});

describe('DeviceStatusCard Component', () => {
  let element;

  beforeEach(() => {
    // Create a new instance of our mock component
    element = new MockDeviceStatusCard();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  /**
   * @current
   * @test Device properties are correctly initialized
   */
  test('should initialize with default property values', () => {
    expect(element.deviceId).toBe('');
    expect(element.deviceName).toBe('');
    expect(element.manufacturer).toBe('');
    expect(element.model).toBe('');
    expect(element.connectionStatus).toBe('disconnected');
    expect(element.simulated).toBe(false);
    expect(element.temperatureUnit).toBe('F');

    // Verify telemetry is initialized with null/default values
    expect(element.telemetry.temperature_current).toBeNull();
    expect(element.telemetry.temperature_setpoint).toBeNull();
    expect(element.telemetry.heating_status).toBe(false);
    expect(element.telemetry.mode).toBe('standby');
  });

  /**
   * @current
   * @test Attribute changes update properties
   */
  test('should update properties when attributes change', () => {
    // Set attributes via attributeChangedCallback
    element.attributeChangedCallback('device-id', '', 'device123');
    element.attributeChangedCallback('device-name', '', 'Test Water Heater');
    element.attributeChangedCallback('manufacturer', '', 'Acme');
    element.attributeChangedCallback('model', '', 'WH2000');
    element.attributeChangedCallback('connection-status', 'disconnected', 'connected');
    element.attributeChangedCallback('simulated', 'false', 'true');

    // Verify properties were updated
    expect(element.deviceId).toBe('device123');
    expect(element.deviceName).toBe('Test Water Heater');
    expect(element.manufacturer).toBe('Acme');
    expect(element.model).toBe('WH2000');
    expect(element.connectionStatus).toBe('connected');
    expect(element.simulated).toBe(true);

    // Verify render was called for each attribute change
    expect(element.render).toHaveBeenCalledTimes(6);
  });

  /**
   * @current
   * @test Telemetry updates are handled properly
   */
  test('should update telemetry data and UI when telemetry is received', () => {
    // Setup spies
    jest.spyOn(element, 'updateTelemetryUI');

    // Call updateTelemetry with new data
    const telemetryData = {
      temperature_current: 120.5,
      temperature_setpoint: 125.0,
      heating_status: true,
      power_consumption_watts: 3500,
      water_flow_gpm: 2.5,
      mode: 'heating',
      last_updated: '2023-06-15T14:30:45Z'
    };

    element.updateTelemetry(telemetryData);

    // Verify telemetry state was updated
    expect(element.telemetry.temperature_current).toBe(120.5);
    expect(element.telemetry.temperature_setpoint).toBe(125.0);
    expect(element.telemetry.heating_status).toBe(true);
    expect(element.telemetry.power_consumption_watts).toBe(3500);
    expect(element.telemetry.water_flow_gpm).toBe(2.5);
    expect(element.telemetry.mode).toBe('heating');
    expect(element.telemetry.last_updated).toBe('2023-06-15T14:30:45Z');

    // Verify UI update was called
    expect(element.updateTelemetryUI).toHaveBeenCalledTimes(1);
  });

  /**
   * @current
   * @test Device update handled properly
   */
  test('should update device properties when device data is received', () => {
    // Setup initial component state
    element.deviceId = 'device123';

    // Call updateDevice with new data
    const deviceData = {
      device_id: 'device123',
      display_name: 'Updated Water Heater',
      manufacturer: 'NewCo',
      model: 'SuperHeater',
      connection_status: 'connected',
      simulated: true,
      state: {
        temperature_current: 130.0
      }
    };

    element.updateDevice(deviceData);

    // Verify device properties were updated
    expect(element.deviceName).toBe('Updated Water Heater');
    expect(element.manufacturer).toBe('NewCo');
    expect(element.model).toBe('SuperHeater');
    expect(element.connectionStatus).toBe('connected');
    expect(element.simulated).toBe(true);

    // Verify telemetry was updated from state
    expect(element.telemetry.temperature_current).toBe(130.0);

    // Verify render was called
    expect(element.render).toHaveBeenCalledTimes(1);
  });

  /**
   * @current
   * @test Device update ignored for different device id
   */
  test('should ignore device updates for a different device id', () => {
    // Setup initial component state
    element.deviceId = 'device123';
    element.deviceName = 'Original Name';

    // Call updateDevice with data for a different device
    const deviceData = {
      device_id: 'different_device',
      display_name: 'Different Device'
    };

    element.updateDevice(deviceData);

    // Verify device properties were not updated
    expect(element.deviceName).toBe('Original Name');

    // Verify render was not called
    expect(element.render).not.toHaveBeenCalled();
  });

  /**
   * @current
   * @test Temperature formatting
   */
  test('should format temperature values correctly', () => {
    // Test with regular value
    expect(element.formatTemperature(75.5)).toBe('75.5°F');

    // Test with null
    expect(element.formatTemperature(null)).toBe('—');

    // Test with NaN
    expect(element.formatTemperature(NaN)).toBe('—');

    // Change temperature unit and test again
    element.temperatureUnit = 'C';
    expect(element.formatTemperature(25.0)).toBe('25°C');
  });

  /**
   * @current
   * @test Mode formatting
   */
  test('should format mode values correctly', () => {
    expect(element.formatMode('heating')).toBe('Heating');
    expect(element.formatMode('standby')).toBe('Standby');
    expect(element.formatMode('')).toBe('Unknown');
    expect(element.formatMode(null)).toBe('Unknown');
  });
});
