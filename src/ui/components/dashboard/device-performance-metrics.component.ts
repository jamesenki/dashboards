import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Subscription } from 'rxjs';
import { WebSocketService, TelemetryMessage } from '../../services/websocket.service';
import { environment } from '../../../environments/environment';

/**
 * Interface for performance metric
 */
interface PerformanceMetric {
  name: string;
  value: number | null;
  unit: string;
  trend: 'up' | 'down' | 'stable' | 'unknown';
  trendValue: number | null;
  status: 'normal' | 'warning' | 'critical' | 'unknown';
  icon: string;
  description: string;
}

/**
 * DevicePerformanceMetrics Component
 * 
 * Displays key performance metrics for a device with real-time updates
 * and status indicators. Supports both real-time and historical trends.
 */
@Component({
  selector: 'app-device-performance-metrics',
  templateUrl: './device-performance-metrics.component.html',
  styleUrls: ['./device-performance-metrics.component.scss']
})
export class DevicePerformanceMetricsComponent implements OnInit, OnDestroy {
  @Input() deviceId: string = '';
  @Input() timeRange: '24h' | '7d' | '30d' = '24h';
  @Input() temperatureUnit: 'F' | 'C' = 'F';

  // Metrics data
  public metrics: PerformanceMetric[] = [];
  public isLoading: boolean = true;
  public error: string | null = null;
  public lastUpdated: Date | null = null;
  
  // Anomaly detection
  public anomaliesDetected: number = 0;
  public showAnomalies: boolean = false;
  
  // Efficiency rating
  public efficiencyScore: number = 0;
  public efficiencyRating: 'A+' | 'A' | 'B' | 'C' | 'D' | 'F' = 'C';
  
  // Subscription for real-time updates
  private telemetrySubscription: Subscription | null = null;
  private refreshInterval: any = null;

  constructor(
    private http: HttpClient,
    private websocketService: WebSocketService
  ) {}

  ngOnInit(): void {
    // Load initial performance metrics
    this.loadPerformanceMetrics();
    
    // Subscribe to real-time telemetry updates
    this.telemetrySubscription = this.websocketService.telemetry$.subscribe(
      (telemetry: TelemetryMessage) => {
        if (telemetry.device_id === this.deviceId) {
          this.updateMetricsWithRealtimeData(telemetry);
        }
      }
    );
    
    // Set up periodic refresh (every 10 minutes)
    this.refreshInterval = setInterval(() => {
      this.loadPerformanceMetrics();
    }, 600000); // 10 minutes
  }

  ngOnDestroy(): void {
    // Clean up subscriptions
    if (this.telemetrySubscription) {
      this.telemetrySubscription.unsubscribe();
    }
    
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  }

  /**
   * Load performance metrics from API
   */
  loadPerformanceMetrics(): void {
    this.isLoading = true;
    this.error = null;
    
    const apiUrl = `${environment.apiUrl}/api/devices/${this.deviceId}/performance`;
    
    this.http.get(apiUrl, {
      params: {
        time_range: this.timeRange
      }
    }).subscribe({
      next: (data: any) => {
        this.processPerformanceData(data);
        this.isLoading = false;
        this.lastUpdated = new Date();
      },
      error: (err) => {
        this.error = `Failed to load performance metrics: ${err.message}`;
        this.isLoading = false;
      }
    });
  }

  /**
   * Process performance data from API
   */
  private processPerformanceData(data: any): void {
    if (!data) {
      this.error = 'Invalid data format received from server';
      return;
    }
    
    try {
      // Process efficiency rating
      if (data.efficiency) {
        this.efficiencyScore = data.efficiency.score || 0;
        this.efficiencyRating = data.efficiency.rating || 'C';
      }
      
      // Process anomalies
      if (data.anomalies) {
        this.anomaliesDetected = data.anomalies.count || 0;
      }
      
      // Process metrics
      this.metrics = [];
      
      // Energy consumption
      if (data.energy_consumption) {
        this.metrics.push({
          name: 'Energy Consumption',
          value: data.energy_consumption.current,
          unit: 'kWh',
          trend: data.energy_consumption.trend || 'unknown',
          trendValue: data.energy_consumption.trend_value,
          status: this.getMetricStatus(data.energy_consumption.status),
          icon: 'energy',
          description: 'Total energy consumed in the selected period'
        });
      }
      
      // Water usage
      if (data.water_usage) {
        this.metrics.push({
          name: 'Water Usage',
          value: data.water_usage.current,
          unit: 'Gal',
          trend: data.water_usage.trend || 'unknown',
          trendValue: data.water_usage.trend_value,
          status: this.getMetricStatus(data.water_usage.status),
          icon: 'water',
          description: 'Total water used in the selected period'
        });
      }
      
      // Heating cycles
      if (data.heating_cycles) {
        this.metrics.push({
          name: 'Heating Cycles',
          value: data.heating_cycles.current,
          unit: 'cycles',
          trend: data.heating_cycles.trend || 'unknown',
          trendValue: data.heating_cycles.trend_value,
          status: this.getMetricStatus(data.heating_cycles.status),
          icon: 'cycle',
          description: 'Number of heating cycles in the selected period'
        });
      }
      
      // Average temperature
      if (data.average_temperature) {
        let tempValue = data.average_temperature.current;
        let tempUnit = '°F';
        
        // Convert to Celsius if needed
        if (this.temperatureUnit === 'C') {
          tempValue = this.convertFahrenheitToCelsius(tempValue);
          tempUnit = '°C';
        }
        
        this.metrics.push({
          name: 'Average Temperature',
          value: tempValue,
          unit: tempUnit,
          trend: data.average_temperature.trend || 'unknown',
          trendValue: data.average_temperature.trend_value,
          status: this.getMetricStatus(data.average_temperature.status),
          icon: 'temperature',
          description: 'Average water temperature in the selected period'
        });
      }
      
      // Recovery rate
      if (data.recovery_rate) {
        this.metrics.push({
          name: 'Recovery Rate',
          value: data.recovery_rate.current,
          unit: '°F/min',
          trend: data.recovery_rate.trend || 'unknown',
          trendValue: data.recovery_rate.trend_value,
          status: this.getMetricStatus(data.recovery_rate.status),
          icon: 'recovery',
          description: 'Average temperature recovery rate'
        });
      }
    } catch (err: any) {
      this.error = `Error processing performance data: ${err.message}`;
    }
  }

  /**
   * Update metrics with real-time telemetry data
   */
  private updateMetricsWithRealtimeData(telemetry: TelemetryMessage): void {
    if (!telemetry.data) return;
    
    // We'll only update certain metrics in real-time
    // Others require aggregation over time and will be updated with periodic refresh
    
    this.lastUpdated = new Date();
  }

  /**
   * Get normalized status from API response
   */
  private getMetricStatus(status: string): 'normal' | 'warning' | 'critical' | 'unknown' {
    switch (status?.toLowerCase()) {
      case 'normal':
      case 'good':
      case 'ok':
        return 'normal';
      case 'warning':
      case 'attention':
        return 'warning';
      case 'critical':
      case 'alert':
      case 'bad':
        return 'critical';
      default:
        return 'unknown';
    }
  }

  /**
   * Convert Fahrenheit to Celsius
   */
  private convertFahrenheitToCelsius(fahrenheit: number): number {
    return Math.round((fahrenheit - 32) * 5/9 * 10) / 10;
  }

  /**
   * Get CSS class for metric status
   */
  getStatusClass(status: string): string {
    return `status-${status}`;
  }

  /**
   * Get CSS class for trend direction
   */
  getTrendClass(trend: string): string {
    return `trend-${trend}`;
  }

  /**
   * Get trend icon based on direction
   */
  getTrendIcon(trend: string): string {
    switch (trend) {
      case 'up':
        return '↑';
      case 'down':
        return '↓';
      case 'stable':
        return '→';
      default:
        return '-';
    }
  }

  /**
   * Get formatted trend text
   */
  getTrendText(metric: PerformanceMetric): string {
    if (metric.trendValue === null) return 'No trend data';
    
    const direction = metric.trend === 'up' ? 'increase' : 
                     (metric.trend === 'down' ? 'decrease' : 'change');
    
    return `${Math.abs(metric.trendValue)}% ${direction} from previous period`;
  }

  /**
   * Refresh metrics data manually
   */
  refreshData(): void {
    this.loadPerformanceMetrics();
  }

  /**
   * Change time range for metrics
   */
  changeTimeRange(range: '24h' | '7d' | '30d'): void {
    this.timeRange = range;
    this.loadPerformanceMetrics();
  }

  /**
   * Toggle anomalies view
   */
  toggleAnomalies(): void {
    this.showAnomalies = !this.showAnomalies;
  }
}
