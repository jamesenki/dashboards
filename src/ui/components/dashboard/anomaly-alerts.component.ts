import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { Observable, Subscription, interval } from 'rxjs';
import { map, switchMap, startWith } from 'rxjs/operators';
import { WebSocketService } from '../../../services/websocket.service';
import { DeviceService } from '../../../services/device.service';
import { environment } from '../../../environments/environment';

/**
 * Component for displaying real-time anomaly alerts from device telemetry
 * 
 * This component is designed to be device-agnostic and will work with any
 * IoT device type that implements the standard anomaly detection interfaces
 */
@Component({
  selector: 'app-anomaly-alerts',
  templateUrl: './anomaly-alerts.component.html',
  styleUrls: ['./anomaly-alerts.component.scss']
})
export class AnomalyAlertsComponent implements OnInit, OnDestroy {
  /** Device ID to monitor for anomalies */
  @Input() deviceId: string;
  
  /** Optional limit to number of alerts shown */
  @Input() limit: number = 5;
  
  /** Specify whether to show all alerts or only unacknowledged ones */
  @Input() showOnlyUnacknowledged: boolean = false;
  
  /** List of detected anomalies */
  anomalies: any[] = [];
  
  /** Loading state */
  isLoading: boolean = true;
  
  /** Error state */
  error: string = null;
  
  /** WebSocket subscription for real-time alerts */
  private wsSubscription: Subscription;
  
  /** Polling subscription for fallback to REST API */
  private pollingSubscription: Subscription;
  
  constructor(
    private deviceService: DeviceService,
    private wsService: WebSocketService
  ) { }

  ngOnInit(): void {
    this.loadAnomalies();
    this.subscribeToRealtimeAlerts();
  }

  ngOnDestroy(): void {
    if (this.wsSubscription) {
      this.wsSubscription.unsubscribe();
    }
    
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
    }
  }

  /**
   * Initial load of anomalies from API
   */
  loadAnomalies(): void {
    this.isLoading = true;
    this.error = null;
    
    this.deviceService.getDeviceAnomalies(this.deviceId)
      .subscribe(
        (data) => {
          this.processAnomalies(data);
          this.isLoading = false;
        },
        (err) => {
          console.error('Error loading anomalies:', err);
          this.error = 'Failed to load anomalies. Please try again later.';
          this.isLoading = false;
        }
      );
  }

  /**
   * Subscribe to real-time anomaly alerts via WebSocket
   * Falls back to polling if WebSockets are not available
   */
  subscribeToRealtimeAlerts(): void {
    const wsUrl = `${environment.wsUrl}/devices/${this.deviceId}/anomalies`;
    
    // First try WebSocket connection
    this.wsSubscription = this.wsService.connect(wsUrl)
      .subscribe(
        (message) => {
          if (message.type === 'anomaly_detected') {
            this.addNewAnomaly(message.data);
          } else if (message.type === 'anomaly_resolved') {
            this.markAnomalyResolved(message.data.anomalyId);
          }
        },
        (error) => {
          console.warn('WebSocket error, falling back to polling:', error);
          // Fallback to polling if WebSocket fails
          this.setupPolling();
        }
      );
  }

  /**
   * Fallback to polling REST API if WebSockets are unavailable
   */
  setupPolling(): void {
    // Poll for updates every 30 seconds
    this.pollingSubscription = interval(30000)
      .pipe(
        startWith(0),
        switchMap(() => this.deviceService.getDeviceAnomalies(this.deviceId))
      )
      .subscribe(
        (data) => {
          this.processAnomalies(data);
        },
        (error) => {
          console.error('Polling error:', error);
        }
      );
  }

  /**
   * Process anomalies data received from API
   */
  processAnomalies(data: any): void {
    if (data && data.items) {
      // Filter only unacknowledged if necessary
      let filteredAnomalies = this.showOnlyUnacknowledged 
        ? data.items.filter(a => !a.acknowledged)
        : data.items;
      
      // Sort by timestamp (newest first)
      filteredAnomalies.sort((a, b) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );
      
      // Apply limit if specified
      if (this.limit > 0) {
        filteredAnomalies = filteredAnomalies.slice(0, this.limit);
      }
      
      this.anomalies = filteredAnomalies;
    }
  }

  /**
   * Add a new anomaly to the list
   */
  addNewAnomaly(anomaly: any): void {
    // Only add if it doesn't already exist
    if (!this.anomalies.some(a => a.id === anomaly.id)) {
      this.anomalies.unshift(anomaly);
      
      // Maintain limit
      if (this.limit > 0 && this.anomalies.length > this.limit) {
        this.anomalies = this.anomalies.slice(0, this.limit);
      }
    }
  }

  /**
   * Mark an anomaly as resolved
   */
  markAnomalyResolved(anomalyId: string): void {
    const index = this.anomalies.findIndex(a => a.id === anomalyId);
    if (index !== -1) {
      this.anomalies[index].resolved = true;
    }
  }

  /**
   * Acknowledge an anomaly
   */
  acknowledgeAnomaly(anomalyId: string): void {
    this.deviceService.acknowledgeAnomaly(this.deviceId, anomalyId)
      .subscribe(
        () => {
          const index = this.anomalies.findIndex(a => a.id === anomalyId);
          if (index !== -1) {
            this.anomalies[index].acknowledged = true;
            
            // Remove from view if only showing unacknowledged
            if (this.showOnlyUnacknowledged) {
              this.anomalies = this.anomalies.filter(a => !a.acknowledged);
            }
          }
        },
        (error) => {
          console.error('Error acknowledging anomaly:', error);
        }
      );
  }

  /**
   * Get CSS class based on anomaly severity
   */
  getSeverityClass(severity: string): string {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'severity-critical';
      case 'error':
        return 'severity-error';
      case 'warning':
        return 'severity-warning';
      default:
        return 'severity-info';
    }
  }

  /**
   * Format relative time from timestamp
   */
  getRelativeTime(timestamp: string): string {
    const now = new Date().getTime();
    const time = new Date(timestamp).getTime();
    const diff = now - time;
    
    // Convert to appropriate unit
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) {
      return `${days}d ago`;
    } else if (hours > 0) {
      return `${hours}h ago`;
    } else if (minutes > 0) {
      return `${minutes}m ago`;
    } else {
      return `${seconds}s ago`;
    }
  }
}
