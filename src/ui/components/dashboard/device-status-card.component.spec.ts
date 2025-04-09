import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DeviceStatusCardComponent } from './device-status-card.component';
import { WebSocketService } from '../../services/websocket.service';
import { of } from 'rxjs';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('DeviceStatusCardComponent', () => {
  let component: DeviceStatusCardComponent;
  let fixture: ComponentFixture<DeviceStatusCardComponent>;
  let mockWebSocketService: jasmine.SpyObj<WebSocketService>;

  beforeEach(async () => {
    // Create a mock WebSocketService
    mockWebSocketService = jasmine.createSpyObj('WebSocketService', [
      'subscribeToDevice',
      'unsubscribeFromDevice',
      'sendCommand'
    ]);

    // Configure the telemetry$ and events$ observables
    mockWebSocketService.telemetry$ = of();
    mockWebSocketService.events$ = of();

    await TestBed.configureTestingModule({
      declarations: [ DeviceStatusCardComponent ],
      providers: [
        { provide: WebSocketService, useValue: mockWebSocketService }
      ],
      schemas: [NO_ERRORS_SCHEMA] // Ignore unknown elements to avoid template errors
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DeviceStatusCardComponent);
    component = fixture.componentInstance;
    // Set required input properties
    component.deviceId = 'test-device-1';
    component.deviceName = 'Test Water Heater';
    component.deviceModel = 'Pro 2000';
    component.deviceManufacturer = 'AquaTech';
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should subscribe to device telemetry on init', () => {
    expect(mockWebSocketService.subscribeToDevice).toHaveBeenCalledWith('test-device-1');
  });

  it('should unsubscribe from device telemetry on destroy', () => {
    component.ngOnDestroy();
    expect(mockWebSocketService.unsubscribeFromDevice).toHaveBeenCalledWith('test-device-1');
  });

  it('should update state from telemetry messages', () => {
    // Arrange
    const telemetryData = {
      device_id: 'test-device-1',
      timestamp: new Date().toISOString(),
      data: {
        temperature_current: 125,
        temperature_setpoint: 130,
        heating_status: true,
        power_consumption_watts: 1200,
        water_flow_gpm: 2.5,
        mode: 'heating'
      },
      simulated: true
    };

    // Act
    component['updateFromTelemetry'](telemetryData);

    // Assert
    expect(component.currentTemperature).toBe(125);
    expect(component.targetTemperature).toBe(130);
    expect(component.heatingStatus).toBe(true);
    expect(component.powerConsumption).toBe(1200);
    expect(component.waterFlow).toBe(2.5);
    expect(component.mode).toBe('heating');
    expect(component.isSimulated).toBe(true);
    expect(component.connectionStatus).toBe('connected');
  });

  it('should handle device error events', () => {
    // Arrange
    const errorEvent = {
      device_id: 'test-device-1',
      event_type: 'error_occurred',
      timestamp: new Date().toISOString(),
      details: {
        error_code: 'E101'
      },
      simulated: true
    };

    // Act
    component['handleDeviceEvent'](errorEvent);

    // Assert
    expect(component.errorCode).toBe('E101');
    expect(component.isSimulated).toBe(true);
  });

  it('should handle error cleared events', () => {
    // Set initial error state
    component.errorCode = 'E101';

    // Arrange
    const errorClearedEvent = {
      device_id: 'test-device-1',
      event_type: 'error_cleared',
      timestamp: new Date().toISOString(),
      details: {},
      simulated: true
    };

    // Act
    component['handleDeviceEvent'](errorClearedEvent);

    // Assert
    expect(component.errorCode).toBeNull();
  });

  it('should send correct commands when controlling the device', () => {
    // Test temperature control
    component.setTemperature(135);
    expect(mockWebSocketService.sendCommand).toHaveBeenCalledWith(
      'test-device-1',
      'set_temperature',
      { setpoint: 135 }
    );

    // Test mode control
    component.setMode('eco');
    expect(mockWebSocketService.sendCommand).toHaveBeenCalledWith(
      'test-device-1',
      'set_mode',
      { mode: 'eco' }
    );

    // Test power toggle
    component.togglePower();
    expect(mockWebSocketService.sendCommand).toHaveBeenCalledWith(
      'test-device-1',
      'power_toggle'
    );
  });

  it('should convert temperatures between units', () => {
    // Test Fahrenheit (default)
    component.currentTemperature = 100;
    expect(component.getTemperatureInSelectedUnit(100)).toBe(100);

    // Test Celsius conversion
    component.temperatureUnit = 'C';
    expect(component.getTemperatureInSelectedUnit(100)).toBeCloseTo(37.78, 1);
  });

  it('should return appropriate CSS classes for status indicators', () => {
    // Heating status
    component.heatingStatus = true;
    expect(component.getHeatingStatusClass()).toBe('heating-active');

    component.heatingStatus = false;
    expect(component.getHeatingStatusClass()).toBe('heating-inactive');

    // Error status
    component.errorCode = 'E101';
    expect(component.getErrorStatusClass()).toBe('error-active');

    component.errorCode = null;
    expect(component.getErrorStatusClass()).toBe('');

    // Connection status
    component.connectionStatus = 'connected';
    expect(component.getConnectionStatusClass()).toBe('connected');

    component.connectionStatus = 'disconnected';
    expect(component.getConnectionStatusClass()).toBe('disconnected');
  });
});
