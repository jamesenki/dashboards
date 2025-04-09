import { Component, Input, OnInit, OnDestroy, ElementRef, ViewChild } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Subscription } from 'rxjs';
import { WebSocketService, TelemetryMessage } from '../../services/websocket.service';
import { environment } from '../../../environments/environment';

/**
 * TelemetryHistoryChart Component
 *
 * Displays historical time-series data for device telemetry, supporting multiple
 * metrics and configurable time ranges. Supports real-time updates via WebSocket.
 */
@Component({
  selector: 'app-telemetry-history-chart',
  templateUrl: './telemetry-history-chart.component.html',
  styleUrls: ['./telemetry-history-chart.component.scss']
})
export class TelemetryHistoryChartComponent implements OnInit, OnDestroy {
  @ViewChild('chartContainer') chartContainer: ElementRef;

  @Input() deviceId: string = '';
  @Input() metrics: string[] = ['temperature_current'];
  @Input() timeRange: '1h' | '6h' | '24h' | '7d' | '30d' = '24h';
  @Input() chartTitle: string = 'Temperature History';
  @Input() chartType: 'line' | 'bar' | 'area' = 'line';
  @Input() height: number = 300;
  @Input() showLegend: boolean = true;
  @Input() temperatureUnit: 'F' | 'C' = 'F';
  @Input() autoRefresh: boolean = true;
  @Input() aggregationType: 'raw' | 'avg' | 'min' | 'max' = 'raw';

  // Chart data
  public chartOptions: any;
  public chartInstance: any;
  public chartData: any[] = [];
  public isLoading: boolean = true;
  public error: string | null = null;
  public lastUpdated: Date | null = null;

  // Chart Y-axis display units
  public displayUnits: {[key: string]: string} = {
    'temperature_current': '°F',
    'temperature_setpoint': '°F',
    'power_consumption_watts': 'W',
    'water_flow_gpm': 'GPM',
    'pressure_psi': 'PSI',
    'energy_usage_kwh': 'kWh',
    'water_usage_gallons': 'Gal'
  };

  // Chart colors for different metrics
  public metricColors: {[key: string]: string} = {
    'temperature_current': '#F44336',
    'temperature_setpoint': '#FF9800',
    'power_consumption_watts': '#4CAF50',
    'water_flow_gpm': '#2196F3',
    'pressure_psi': '#9C27B0',
    'energy_usage_kwh': '#795548',
    'water_usage_gallons': '#00BCD4'
  };

  // Display names for metrics
  public metricDisplayNames: {[key: string]: string} = {
    'temperature_current': 'Current Temperature',
    'temperature_setpoint': 'Target Temperature',
    'power_consumption_watts': 'Power Consumption',
    'water_flow_gpm': 'Water Flow',
    'pressure_psi': 'Pressure',
    'energy_usage_kwh': 'Energy Usage',
    'water_usage_gallons': 'Water Usage'
  };

  // Subscriptions
  private telemetrySubscription: Subscription | null = null;
  private refreshInterval: any = null;

  constructor(
    private http: HttpClient,
    private websocketService: WebSocketService
  ) {}

  ngOnInit(): void {
    // Load initial historical data
    this.loadHistoricalData();

    // Set up real-time updates if auto-refresh is enabled
    if (this.autoRefresh) {
      // Subscribe to telemetry for this device
      this.telemetrySubscription = this.websocketService.telemetry$.subscribe(
        (telemetry: TelemetryMessage) => {
          if (telemetry.device_id === this.deviceId) {
            this.updateChartWithRealtimeData(telemetry);
          }
        }
      );

      // Set up periodic refresh of historical data (every 5 minutes)
      this.refreshInterval = setInterval(() => {
        this.loadHistoricalData();
      }, 300000); // 5 minutes
    }
  }

  ngOnDestroy(): void {
    // Clean up subscriptions
    if (this.telemetrySubscription) {
      this.telemetrySubscription.unsubscribe();
    }

    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }

    // Destroy chart instance if it exists
    if (this.chartInstance) {
      this.chartInstance.destroy();
    }
  }

  /**
   * Load historical telemetry data from API
   */
  loadHistoricalData(): void {
    this.isLoading = true;
    this.error = null;

    const apiUrl = `${environment.apiUrl}/api/telemetry/history/${this.deviceId}`;

    this.http.get(apiUrl, {
      params: {
        metrics: this.metrics.join(','),
        time_range: this.timeRange,
        aggregation: this.aggregationType
      }
    }).subscribe({
      next: (data: any) => {
        this.processHistoricalData(data);
        this.isLoading = false;
        this.lastUpdated = new Date();
      },
      error: (err) => {
        this.error = `Failed to load historical data: ${err.message}`;
        this.isLoading = false;
      }
    });
  }

  /**
   * Process historical data and initialize chart
   */
  private processHistoricalData(data: any): void {
    if (!data || !data.series) {
      this.error = 'Invalid data format received from server';
      return;
    }

    try {
      // Prepare chart series data
      this.chartData = this.metrics.map(metric => {
        const metricData = data.series[metric] || [];

        return {
          name: this.metricDisplayNames[metric] || metric,
          data: metricData.map((point: any) => {
            // Convert temperature if needed
            let value = point.value;
            if ((metric === 'temperature_current' || metric === 'temperature_setpoint')
                && this.temperatureUnit === 'C') {
              value = this.convertFahrenheitToCelsius(value);
            }

            return {
              x: new Date(point.timestamp).getTime(),
              y: value
            };
          }),
          color: this.metricColors[metric] || '#607D8B'
        };
      });

      // Initialize or update chart
      this.initializeChart();
    } catch (err: any) {
      this.error = `Error processing chart data: ${err.message}`;
    }
  }

  /**
   * Initialize chart with ApexCharts
   */
  private initializeChart(): void {
    if (!this.chartContainer) return;

    // Prepare Y-axis labels
    const yAxisLabels = this.metrics.map(metric => {
      let unit = this.displayUnits[metric] || '';

      // Adjust temperature unit
      if ((metric === 'temperature_current' || metric === 'temperature_setpoint')
          && this.temperatureUnit === 'C') {
        unit = '°C';
      }

      return unit;
    });

    // Configure chart options
    this.chartOptions = {
      series: this.chartData,
      chart: {
        type: this.chartType,
        height: this.height,
        animations: {
          enabled: true,
          dynamicAnimation: {
            speed: 1000
          }
        },
        toolbar: {
          show: true,
          tools: {
            download: true,
            selection: true,
            zoom: true,
            zoomin: true,
            zoomout: true,
            pan: true,
            reset: true
          }
        },
        zoom: {
          enabled: true
        }
      },
      dataLabels: {
        enabled: false
      },
      stroke: {
        curve: 'smooth',
        width: 2
      },
      title: {
        text: this.chartTitle,
        align: 'left'
      },
      grid: {
        borderColor: '#e0e0e0',
        row: {
          colors: ['#f5f5f5', 'transparent'],
          opacity: 0.5
        }
      },
      xaxis: {
        type: 'datetime',
        labels: {
          datetimeUTC: false,
          format: this.getDateTimeFormat()
        },
        title: {
          text: 'Time'
        }
      },
      yaxis: {
        title: {
          text: this.metrics.map(m => this.metricDisplayNames[m] || m).join(' / ')
        },
        labels: {
          formatter: (value: number) => `${value.toFixed(1)} ${yAxisLabels[0]}`
        }
      },
      legend: {
        show: this.showLegend,
        position: 'top'
      },
      tooltip: {
        x: {
          format: 'dd MMM yyyy HH:mm'
        }
      }
    };

    // Render the chart
    if (typeof ApexCharts !== 'undefined') {
      if (this.chartInstance) {
        this.chartInstance.updateOptions(this.chartOptions);
      } else {
        this.chartInstance = new ApexCharts(
          this.chartContainer.nativeElement,
          this.chartOptions
        );
        this.chartInstance.render();
      }
    } else {
      console.error('ApexCharts is not loaded. Please include the library.');
    }
  }

  /**
   * Update chart with real-time telemetry data
   */
  private updateChartWithRealtimeData(telemetry: TelemetryMessage): void {
    if (!this.chartInstance || !telemetry.data) return;

    const timestamp = new Date(telemetry.timestamp).getTime();

    // Update each metric in the chart if it has new data
    this.metrics.forEach((metric, index) => {
      if (telemetry.data[metric] !== undefined) {
        let value = telemetry.data[metric];

        // Convert temperature if needed
        if ((metric === 'temperature_current' || metric === 'temperature_setpoint')
            && this.temperatureUnit === 'C') {
          value = this.convertFahrenheitToCelsius(value);
        }

        // Add new data point
        const newData = { x: timestamp, y: value };
        this.chartInstance.appendData([{
          name: this.metricDisplayNames[metric] || metric,
          data: [newData]
        }]);

        // Update component data
        if (this.chartData[index]) {
          this.chartData[index].data.push(newData);

          // Trim array to avoid memory issues (keep last 1000 points)
          if (this.chartData[index].data.length > 1000) {
            this.chartData[index].data.shift();
          }
        }
      }
    });

    this.lastUpdated = new Date();
  }

  /**
   * Get appropriate date format based on time range
   */
  private getDateTimeFormat(): string {
    switch (this.timeRange) {
      case '1h':
      case '6h':
        return 'HH:mm';
      case '24h':
        return 'HH:mm';
      case '7d':
        return 'dd MMM, HH:mm';
      case '30d':
        return 'dd MMM';
      default:
        return 'dd MMM, HH:mm';
    }
  }

  /**
   * Convert Fahrenheit to Celsius
   */
  private convertFahrenheitToCelsius(fahrenheit: number): number {
    return (fahrenheit - 32) * 5/9;
  }

  /**
   * Refresh chart data manually
   */
  refreshData(): void {
    this.loadHistoricalData();
  }

  /**
   * Change time range
   */
  changeTimeRange(range: '1h' | '6h' | '24h' | '7d' | '30d'): void {
    this.timeRange = range;
    this.loadHistoricalData();
  }

  /**
   * Change chart type
   */
  changeChartType(type: 'line' | 'bar' | 'area'): void {
    this.chartType = type;

    if (this.chartInstance) {
      this.chartInstance.updateOptions({
        chart: {
          type: type
        }
      });
    }
  }
}
