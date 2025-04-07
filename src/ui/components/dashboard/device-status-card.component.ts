import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { Subscription } from 'rxjs';
import { WebSocketService, TelemetryMessage, EventMessage } from '../../services/websocket.service';

/**
 * DeviceStatusCard Component
 * 
 * Displays real-time status information for a single water heater device,
 * including temperature, heating status, and other key metrics.
 */
@Component({
  selector: 'app-device-status-card',
  templateUrl: './device-status-card.component.html',
  styleUrls: ['./device-status-card.component.scss']
})
export class DeviceStatusCardComponent implements OnInit, OnDestroy {
  @Input() deviceId: string = '';
  @Input() deviceName: string = '';
  @Input() deviceModel: string = '';
  @Input() deviceManufacturer: string = '';
  @Input() initialState: any = {};

  // Device state
  public currentTemperature: number | null = null;
  public targetTemperature: number | null = null;
  public heatingStatus: boolean = false;
  public powerConsumption: number | null = null;
  public waterFlow: number | null = null;
  public mode: string = 'unknown';
  public errorCode: string | null = null;
  public connectionStatus: 'connected' | 'disconnected' = 'disconnected';
  public lastUpdated: Date | null = null;
  public isSimulated: boolean = false;

  // Dashboard display settings
  public temperatureUnit: 'F' | 'C' = 'F';
  public showPowerConsumption: boolean = true;
  public showWaterFlow: boolean = true;

  // Subscriptions
  private telemetrySubscription: Subscription | null = null;
  private eventSubscription: Subscription | null = null;

  constructor(private websocketService: WebSocketService) {}

  ngOnInit(): void {
    // Initialize with any provided initial state
    if (this.initialState) {
      this.updateState(this.initialState);
    }

    // Subscribe to real-time telemetry for this device
    this.telemetrySubscription = this.websocketService.telemetry$.subscribe(
      (telemetry: TelemetryMessage) => {
        if (telemetry.device_id === this.deviceId) {
          this.updateFromTelemetry(telemetry);
        }
      }
    );

    // Subscribe to device events
    this.eventSubscription = this.websocketService.events$.subscribe(
      (event: EventMessage) => {
        if (event.device_id === this.deviceId) {
          this.handleDeviceEvent(event);
        }
      }
    );

    // Subscribe to this device's updates
    this.websocketService.subscribeToDevice(this.deviceId);
  }

  ngOnDestroy(): void {
    // Unsubscribe to prevent memory leaks
    if (this.telemetrySubscription) {
      this.telemetrySubscription.unsubscribe();
    }
    
    if (this.eventSubscription) {
      this.eventSubscription.unsubscribe();
    }

    // Unsubscribe from device updates
    this.websocketService.unsubscribeFromDevice(this.deviceId);
  }

  /**
   * Update component state from telemetry message
   */
  private updateFromTelemetry(telemetry: TelemetryMessage): void {
    if (telemetry.data) {
      // Update state properties from telemetry data
      if (telemetry.data.temperature_current !== undefined) {
        this.currentTemperature = telemetry.data.temperature_current;
      }
      
      if (telemetry.data.temperature_setpoint !== undefined) {
        this.targetTemperature = telemetry.data.temperature_setpoint;
      }
      
      if (telemetry.data.heating_status !== undefined) {
        this.heatingStatus = telemetry.data.heating_status;
      }
      
      if (telemetry.data.power_consumption_watts !== undefined) {
        this.powerConsumption = telemetry.data.power_consumption_watts;
      }
      
      if (telemetry.data.water_flow_gpm !== undefined) {
        this.waterFlow = telemetry.data.water_flow_gpm;
      }
      
      if (telemetry.data.mode !== undefined) {
        this.mode = telemetry.data.mode;
      }
      
      if (telemetry.data.error_code !== undefined) {
        this.errorCode = telemetry.data.error_code;
      }
      
      // Update connection status and timestamp
      this.connectionStatus = 'connected';
      this.lastUpdated = new Date();
      
      // Track if data is simulated
      this.isSimulated = telemetry.simulated;
    }
  }

  /**
   * Handle device events (errors, mode changes, etc.)
   */
  private handleDeviceEvent(event: EventMessage): void {
    // Handle different event types
    switch (event.event_type) {
      case 'error_occurred':
        this.errorCode = event.details?.error_code || 'unknown';
        break;
        
      case 'error_cleared':
        this.errorCode = null;
        break;
        
      case 'mode_changed':
        this.mode = event.details?.mode || this.mode;
        break;
        
      case 'connection_status_changed':
        this.connectionStatus = event.details?.status === 'connected' ? 'connected' : 'disconnected';
        break;
    }
    
    // Track if event is from simulated device
    this.isSimulated = event.simulated;
  }

  /**
   * Update component state from an object
   */
  updateState(state: any): void {
    if (!state) return;
    
    if (state.temperature_current !== undefined) {
      this.currentTemperature = state.temperature_current;
    }
    
    if (state.temperature_setpoint !== undefined) {
      this.targetTemperature = state.temperature_setpoint;
    }
    
    if (state.heating_status !== undefined) {
      this.heatingStatus = state.heating_status;
    }
    
    if (state.power_consumption_watts !== undefined) {
      this.powerConsumption = state.power_consumption_watts;
    }
    
    if (state.water_flow_gpm !== undefined) {
      this.waterFlow = state.water_flow_gpm;
    }
    
    if (state.mode !== undefined) {
      this.mode = state.mode;
    }
    
    if (state.error_code !== undefined) {
      this.errorCode = state.error_code;
    }
    
    if (state.simulated !== undefined) {
      this.isSimulated = state.simulated;
    }
  }

  /**
   * Calculate temperature in selected units
   */
  getTemperatureInSelectedUnit(temp: number | null): number | null {
    if (temp === null) return null;
    return this.temperatureUnit === 'C' ? (temp - 32) * 5/9 : temp;
  }

  /**
   * Get CSS class for heating status
   */
  getHeatingStatusClass(): string {
    return this.heatingStatus ? 'heating-active' : 'heating-inactive';
  }

  /**
   * Get error status display class
   */
  getErrorStatusClass(): string {
    return this.errorCode ? 'error-active' : '';
  }

  /**
   * Get connection status display class
   */
  getConnectionStatusClass(): string {
    return this.connectionStatus === 'connected' ? 'connected' : 'disconnected';
  }

  /**
   * Send temperature setpoint command
   */
  setTemperature(temperature: number): void {
    this.websocketService.sendCommand(
      this.deviceId,
      'set_temperature',
      { setpoint: temperature }
    );
  }

  /**
   * Send mode change command
   */
  setMode(mode: string): void {
    this.websocketService.sendCommand(
      this.deviceId,
      'set_mode',
      { mode }
    );
  }

  /**
   * Toggle power state
   */
  togglePower(): void {
    this.websocketService.sendCommand(
      this.deviceId,
      'power_toggle'
    );
  }
}
