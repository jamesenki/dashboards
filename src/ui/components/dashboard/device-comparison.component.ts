import { Component, OnInit, OnDestroy, Input } from '@angular/core';
import { FormBuilder, FormGroup, FormArray, FormControl } from '@angular/forms';
import { DeviceService } from '../../../services/device.service';
import { Observable, Subscription, forkJoin } from 'rxjs';
import { map, switchMap } from 'rxjs/operators';

/**
 * Device Comparison Component
 *
 * Provides comparative analysis of multiple devices based on key performance metrics
 * Following device-agnostic design principles to support future device types
 */
@Component({
  selector: 'app-device-comparison',
  templateUrl: './device-comparison.component.html',
  styleUrls: ['./device-comparison.component.scss']
})
export class DeviceComparisonComponent implements OnInit, OnDestroy {
  @Input() deviceType: string = 'water-heater';
  @Input() initialDeviceIds: string[] = [];
  @Input() temperatureUnit: string = 'F';
  @Input() timeRange: string = '24h';

  devices: any[] = [];
  availableDevices: any[] = [];
  selectedDevices: any[] = [];
  comparisonMetrics: any[] = [];
  comparisonForm: FormGroup;

  isLoading: boolean = true;
  error: string = null;

  // Chart configuration
  chartData: any = null;
  chartOptions: any = null;

  private subscriptions: Subscription = new Subscription();

  // Define available metrics by device type
  private metricsByDeviceType = {
    'water-heater': [
      { id: 'efficiency', name: 'Efficiency Rating', unit: '%' },
      { id: 'energy_consumption', name: 'Energy Consumption', unit: 'kWh' },
      { id: 'water_usage', name: 'Water Usage', unit: 'gal' },
      { id: 'heating_cycles', name: 'Heating Cycles', unit: 'cycles' },
      { id: 'average_temperature', name: 'Average Temperature', unit: '°' },
      { id: 'recovery_rate', name: 'Recovery Rate', unit: '°/min' },
      { id: 'anomalies', name: 'Anomalies Detected', unit: 'count' }
    ]
  };

  constructor(
    private deviceService: DeviceService,
    private fb: FormBuilder
  ) {
    this.comparisonForm = this.fb.group({
      deviceIds: this.fb.array([]),
      metrics: this.fb.array([])
    });
  }

  ngOnInit(): void {
    // Load available devices for the selected type
    this.loadAvailableDevices();

    // Initialize selected metrics based on device type
    this.initializeMetrics();

    // If initial device IDs were provided, select them
    if (this.initialDeviceIds.length > 0) {
      this.selectInitialDevices();
    }
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  /**
   * Initialize metrics based on device type
   */
  initializeMetrics(): void {
    this.comparisonMetrics = this.metricsByDeviceType[this.deviceType] || [];

    // Create form controls for each metric
    const metricsArray = this.comparisonForm.get('metrics') as FormArray;

    // Select default metrics
    const defaultMetrics = ['efficiency', 'energy_consumption', 'average_temperature'];

    this.comparisonMetrics.forEach(metric => {
      metricsArray.push(new FormControl(defaultMetrics.includes(metric.id)));
    });
  }

  /**
   * Load available devices for comparison
   */
  loadAvailableDevices(): void {
    this.isLoading = true;
    this.error = null;

    const subscription = this.deviceService.getDevicesByType(this.deviceType)
      .subscribe(
        (devices) => {
          this.availableDevices = devices;
          this.isLoading = false;
        },
        (error) => {
          console.error('Error loading devices:', error);
          this.error = 'Failed to load devices for comparison. Please try again later.';
          this.isLoading = false;
        }
      );

    this.subscriptions.add(subscription);
  }

  /**
   * Select initial devices if provided
   */
  selectInitialDevices(): void {
    const deviceIdsArray = this.comparisonForm.get('deviceIds') as FormArray;

    // Clear existing selections
    while (deviceIdsArray.length) {
      deviceIdsArray.removeAt(0);
    }

    // Add initial device IDs
    this.initialDeviceIds.forEach(id => {
      deviceIdsArray.push(new FormControl(id));
    });

    // Trigger comparison update
    this.updateComparison();
  }

  /**
   * Get metrics form array
   */
  get metricsFormArray(): FormArray {
    return this.comparisonForm.get('metrics') as FormArray;
  }

  /**
   * Get device IDs form array
   */
  get deviceIdsFormArray(): FormArray {
    return this.comparisonForm.get('deviceIds') as FormArray;
  }

  /**
   * Toggle device selection
   */
  toggleDeviceSelection(deviceId: string): void {
    const deviceIdsArray = this.comparisonForm.get('deviceIds') as FormArray;
    const index = deviceIdsArray.controls.findIndex(control => control.value === deviceId);

    if (index === -1) {
      // Add device if not already selected
      deviceIdsArray.push(new FormControl(deviceId));
    } else {
      // Remove device if already selected
      deviceIdsArray.removeAt(index);
    }

    this.updateComparison();
  }

  /**
   * Check if a device is selected
   */
  isDeviceSelected(deviceId: string): boolean {
    const deviceIdsArray = this.comparisonForm.get('deviceIds') as FormArray;
    return deviceIdsArray.controls.some(control => control.value === deviceId);
  }

  /**
   * Get selected metric IDs
   */
  getSelectedMetricIds(): string[] {
    const selectedMetrics = [];
    const metricsArray = this.comparisonForm.get('metrics') as FormArray;

    metricsArray.controls.forEach((control, index) => {
      if (control.value) {
        selectedMetrics.push(this.comparisonMetrics[index].id);
      }
    });

    return selectedMetrics;
  }

  /**
   * Update comparison when selection changes
   */
  updateComparison(): void {
    const deviceIds = (this.comparisonForm.get('deviceIds') as FormArray).value;

    if (deviceIds.length === 0) {
      this.selectedDevices = [];
      this.chartData = null;
      return;
    }

    this.isLoading = true;
    this.error = null;

    // Load performance data for all selected devices
    const observables = deviceIds.map(deviceId =>
      this.deviceService.getDevicePerformanceData(deviceId, this.timeRange)
    );

    const subscription = forkJoin(observables)
      .pipe(
        switchMap(performanceDataArray => {
          // Store performance data
          const deviceDataMap = {};
          performanceDataArray.forEach((data, index) => {
            deviceDataMap[deviceIds[index]] = data;
          });

          // Load device details
          return forkJoin(deviceIds.map(deviceId => this.deviceService.getDeviceById(deviceId)))
            .pipe(
              map(devices => {
                // Combine device details with performance data
                return devices.map((device, index) => ({
                  ...device,
                  performance: deviceDataMap[deviceIds[index]]
                }));
              })
            );
        })
      )
      .subscribe(
        (devices) => {
          this.selectedDevices = devices;
          this.prepareChartData();
          this.isLoading = false;
        },
        (error) => {
          console.error('Error loading comparison data:', error);
          this.error = 'Failed to load comparison data. Please try again later.';
          this.isLoading = false;
        }
      );

    this.subscriptions.add(subscription);
  }

  /**
   * Prepare chart data for visualization
   */
  prepareChartData(): void {
    if (this.selectedDevices.length === 0) {
      this.chartData = null;
      return;
    }

    const selectedMetricIds = this.getSelectedMetricIds();

    // Prepare data series for each selected metric
    const datasets = [];
    const labels = this.selectedDevices.map(device => device.display_name || `${device.manufacturer} ${device.model}`);

    selectedMetricIds.forEach(metricId => {
      const metric = this.comparisonMetrics.find(m => m.id === metricId);
      const data = this.selectedDevices.map(device => {
        // Handle different metric paths in the data structure
        if (metricId === 'efficiency') {
          return device.performance?.efficiency?.score || 0;
        } else if (metricId === 'anomalies') {
          return device.performance?.anomalies?.count || 0;
        } else {
          return device.performance?.[metricId]?.current || 0;
        }
      });

      datasets.push({
        label: metric.name,
        data,
        unit: metric.unit
      });
    });

    this.chartData = {
      labels,
      datasets
    };

    this.prepareChartOptions();
  }

  /**
   * Prepare chart options
   */
  prepareChartOptions(): void {
    this.chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true
        }
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: (context) => {
              const dataset = context.dataset;
              const value = context.raw;
              return `${dataset.label}: ${value} ${dataset.unit}`;
            }
          }
        }
      }
    };
  }

  /**
   * Handle metric selection change
   */
  onMetricSelectionChange(): void {
    this.updateComparison();
  }

  /**
   * Convert temperature based on selected unit
   */
  convertTemperature(value: number, sourceUnit: string = 'F'): number {
    if (this.temperatureUnit === sourceUnit) {
      return value;
    }

    return this.temperatureUnit === 'C'
      ? (value - 32) * 5/9  // F to C
      : value * 9/5 + 32;   // C to F
  }

  /**
   * Get CSS class for metric comparison
   * Based on whether a higher or lower value is better for this metric
   */
  getComparisonClass(metricId: string, value: number, bestValue: number): string {
    // Define metrics where higher is better
    const higherIsBetter = ['efficiency', 'recovery_rate'];

    // Define metrics where lower is better
    const lowerIsBetter = ['energy_consumption', 'water_usage', 'heating_cycles', 'anomalies'];

    // Define threshold for significant difference (%)
    const threshold = 0.05;

    if (value === bestValue) {
      return 'best-value';
    }

    const percentDifference = Math.abs((value - bestValue) / bestValue);

    if (percentDifference < threshold) {
      return 'similar-value';
    }

    if (higherIsBetter.includes(metricId)) {
      return value > bestValue * (1 - threshold) ? 'good-value' : 'poor-value';
    }

    if (lowerIsBetter.includes(metricId)) {
      return value < bestValue * (1 + threshold) ? 'good-value' : 'poor-value';
    }

    return '';
  }

  /**
   * Get best value for a metric across all devices
   */
  getBestValueForMetric(metricId: string): number {
    // Define metrics where higher is better
    const higherIsBetter = ['efficiency', 'recovery_rate'];

    // Define metrics where lower is better
    const lowerIsBetter = ['energy_consumption', 'water_usage', 'heating_cycles', 'anomalies'];

    const values = this.selectedDevices.map(device => {
      if (metricId === 'efficiency') {
        return device.performance?.efficiency?.score || 0;
      } else if (metricId === 'anomalies') {
        return device.performance?.anomalies?.count || 0;
      } else {
        return device.performance?.[metricId]?.current || 0;
      }
    });

    if (higherIsBetter.includes(metricId)) {
      return Math.max(...values);
    }

    if (lowerIsBetter.includes(metricId)) {
      return Math.min(...values);
    }

    return 0;
  }
}
