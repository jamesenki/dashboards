import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { WebSocketService, TelemetryMessage, EventMessage } from '../../services/websocket.service';
import { environment } from '../../../environments/environment';
import { Subscription } from 'rxjs';

/**
 * DeviceDetailsComponent
 * 
 * Comprehensive device details page that integrates all visualization components.
 * Shows real-time status, historical data, and performance metrics for a single device.
 */
@Component({
  selector: 'app-device-details',
  templateUrl: './device-details.component.html',
  styleUrls: ['./device-details.component.scss']
})
export class DeviceDetailsComponent implements OnInit, OnDestroy {
  // Device details
  public deviceId: string = '';
  public device: any = null;
  public isLoading: boolean = true;
  public error: string | null = null;
  
  // View state
  public activeTab: 'overview' | 'performance' | 'history' | 'maintenance' = 'overview';
  public temperatureUnit: 'F' | 'C' = 'F';
  public timeRange: '24h' | '7d' | '30d' = '24h';
  
  // Selected metrics for charts
  public selectedMetrics: string[] = ['temperature_current', 'temperature_setpoint'];
  
  // Recent events log
  public recentEvents: EventMessage[] = [];
  
  // Subscriptions
  private routeSubscription: Subscription | null = null;
  private telemetrySubscription: Subscription | null = null;
  private eventSubscription: Subscription | null = null;
  
  constructor(
    private route: ActivatedRoute,
    private http: HttpClient,
    private websocketService: WebSocketService
  ) {}
  
  ngOnInit(): void {
    // Get device ID from route parameters
    this.routeSubscription = this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.deviceId = id;
        this.loadDeviceDetails();
      }
    });
    
    // Subscribe to real-time telemetry
    this.telemetrySubscription = this.websocketService.telemetry$.subscribe(
      (telemetry: TelemetryMessage) => {
        if (telemetry.device_id === this.deviceId) {
          this.updateDeviceStateFromTelemetry(telemetry);
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
  }
  
  ngOnDestroy(): void {
    // Clean up subscriptions
    if (this.routeSubscription) {
      this.routeSubscription.unsubscribe();
    }
    
    if (this.telemetrySubscription) {
      this.telemetrySubscription.unsubscribe();
    }
    
    if (this.eventSubscription) {
      this.eventSubscription.unsubscribe();
    }
    
    // Unsubscribe from device updates
    if (this.deviceId) {
      this.websocketService.unsubscribeFromDevice(this.deviceId);
    }
  }
  
  /**
   * Load device details from API
   */
  loadDeviceDetails(): void {
    this.isLoading = true;
    this.error = null;
    
    const apiUrl = `${environment.apiUrl}/api/devices/water-heaters/${this.deviceId}`;
    
    this.http.get(apiUrl).subscribe({
      next: (data: any) => {
        this.device = data;
        this.isLoading = false;
        
        // Subscribe to device updates
        this.websocketService.subscribeToDevice(this.deviceId);
      },
      error: (err) => {
        this.error = `Failed to load device details: ${err.message}`;
        this.isLoading = false;
      }
    });
  }
  
  /**
   * Update device state from real-time telemetry
   */
  private updateDeviceStateFromTelemetry(telemetry: TelemetryMessage): void {
    if (!this.device || !telemetry.data) return;
    
    // Update device state with telemetry data
    if (!this.device.state) {
      this.device.state = {};
    }
    
    // Merge telemetry data into device state
    Object.assign(this.device.state, telemetry.data);
    
    // Update last updated timestamp
    this.device.last_updated = telemetry.timestamp;
  }
  
  /**
   * Handle device event
   */
  private handleDeviceEvent(event: EventMessage): void {
    if (!this.device) return;
    
    // Add to recent events (limit to 10)
    this.recentEvents.unshift(event);
    if (this.recentEvents.length > 10) {
      this.recentEvents.pop();
    }
    
    // Update device state based on event type
    switch (event.event_type) {
      case 'connection_status_changed':
        this.device.connection_status = event.details?.status || this.device.connection_status;
        break;
        
      case 'mode_changed':
        if (!this.device.state) {
          this.device.state = {};
        }
        this.device.state.mode = event.details?.mode || this.device.state.mode;
        break;
        
      case 'error_occurred':
        if (!this.device.state) {
          this.device.state = {};
        }
        this.device.state.error_code = event.details?.error_code || 'unknown';
        break;
        
      case 'error_cleared':
        if (this.device.state) {
          this.device.state.error_code = null;
        }
        break;
    }
  }
  
  /**
   * Set active tab
   */
  setActiveTab(tab: 'overview' | 'performance' | 'history' | 'maintenance'): void {
    this.activeTab = tab;
  }
  
  /**
   * Toggle temperature unit
   */
  toggleTemperatureUnit(): void {
    this.temperatureUnit = this.temperatureUnit === 'F' ? 'C' : 'F';
  }
  
  /**
   * Change time range for charts and metrics
   */
  changeTimeRange(range: '24h' | '7d' | '30d'): void {
    this.timeRange = range;
  }
  
  /**
   * Update selected metrics for charts
   */
  updateSelectedMetrics(metrics: string[]): void {
    this.selectedMetrics = metrics;
  }
  
  /**
   * Send command to device
   */
  sendCommand(command: string, parameters?: any): void {
    this.websocketService.sendCommand(this.deviceId, command, parameters);
  }
  
  /**
   * Get device display name
   */
  getDeviceDisplayName(): string {
    if (!this.device) return this.deviceId;
    
    return this.device.display_name || 
      `${this.device.manufacturer} ${this.device.model} (${this.device.device_id.substring(0, 8)})`;
  }
  
  /**
   * Get device image URL
   */
  getDeviceImageUrl(): string {
    if (!this.device) return '';
    
    return this.device.image_url || 
      `${environment.baseUrl}/assets/images/water-heaters/${this.device.manufacturer.toLowerCase()}-${this.device.model.toLowerCase()}.png`;
  }
  
  /**
   * Refresh device data
   */
  refreshData(): void {
    this.loadDeviceDetails();
  }
  
  /**
   * Get severity class for event display
   */
  getEventSeverityClass(severity: string): string {
    switch (severity) {
      case 'error':
        return 'severity-error';
      case 'warning':
        return 'severity-warning';
      case 'info':
      default:
        return 'severity-info';
    }
  }
  
  /**
   * Format event timestamp for display
   */
  formatEventTime(timestamp: string): string {
    const eventTime = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - eventTime.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    
    if (diffMin < 1) {
      return 'Just now';
    } else if (diffMin < 60) {
      return `${diffMin} min ago`;
    } else if (diffMin < 1440) {
      return `${Math.floor(diffMin / 60)} hr ago`;
    } else {
      return eventTime.toLocaleDateString();
    }
  }
}
