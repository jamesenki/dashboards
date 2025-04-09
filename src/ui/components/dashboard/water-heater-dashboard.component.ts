import { Component, OnInit, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { WebSocketService } from '../../services/websocket.service';
import { environment } from '../../../environments/environment';
import { Subscription } from 'rxjs';

/**
 * Interface for water heater device information
 */
interface WaterHeater {
  device_id: string;
  manufacturer: string;
  model: string;
  serial_number?: string;
  connection_status: string;
  simulated: boolean;
  state?: any;
  display_name?: string;
}

/**
 * Water Heater Dashboard Component
 *
 * Main dashboard for water heater monitoring and control,
 * displaying multiple device status cards and handling device filtering.
 */
@Component({
  selector: 'app-water-heater-dashboard',
  templateUrl: './water-heater-dashboard.component.html',
  styleUrls: ['./water-heater-dashboard.component.scss']
})
export class WaterHeaterDashboardComponent implements OnInit, OnDestroy {
  // Device data
  public waterHeaters: WaterHeater[] = [];
  public filteredWaterHeaters: WaterHeater[] = [];

  // Filter options
  public manufacturers: string[] = [];
  public connectionStatuses: string[] = ['connected', 'disconnected'];

  // Active filters
  public selectedManufacturer: string = '';
  public selectedStatus: string = '';
  public showSimulatedOnly: boolean = false;

  // Dashboard state
  public isLoading: boolean = true;
  public error: string | null = null;
  public lastRefreshed: Date | null = null;

  // WebSocket connection status
  public realTimeActive: boolean = false;

  // Subscription for websocket connection status
  private connectionSubscription: Subscription | null = null;

  constructor(
    private http: HttpClient,
    private websocketService: WebSocketService
  ) { }

  ngOnInit(): void {
    // Monitor WebSocket connection status
    this.connectionSubscription = this.websocketService.connectionStatus$.subscribe(
      (connected: boolean) => {
        this.realTimeActive = connected;
      }
    );

    // Load devices
    this.loadWaterHeaters();
  }

  ngOnDestroy(): void {
    // Clean up subscriptions
    if (this.connectionSubscription) {
      this.connectionSubscription.unsubscribe();
    }
  }

  /**
   * Load water heaters from API
   */
  loadWaterHeaters(): void {
    this.isLoading = true;
    this.error = null;

    const apiUrl = `${environment.apiUrl}/api/devices/water-heaters`;

    this.http.get<WaterHeater[]>(apiUrl).subscribe({
      next: (data) => {
        this.waterHeaters = data;
        this.lastRefreshed = new Date();

        // Extract unique manufacturers for filtering
        this.manufacturers = [...new Set(data.map(wh => wh.manufacturer))];

        // Apply filters
        this.applyFilters();

        this.isLoading = false;
      },
      error: (err) => {
        this.error = `Failed to load water heaters: ${err.message}`;
        this.isLoading = false;
      }
    });
  }

  /**
   * Apply filters to water heaters
   */
  applyFilters(): void {
    let filtered = this.waterHeaters;

    // Filter by manufacturer
    if (this.selectedManufacturer) {
      filtered = filtered.filter(wh => wh.manufacturer === this.selectedManufacturer);
    }

    // Filter by connection status
    if (this.selectedStatus) {
      filtered = filtered.filter(wh => wh.connection_status === this.selectedStatus);
    }

    // Filter by simulation status
    if (this.showSimulatedOnly) {
      filtered = filtered.filter(wh => wh.simulated);
    }

    this.filteredWaterHeaters = filtered;
  }

  /**
   * Handle manufacturer filter change
   */
  onManufacturerChange(manufacturer: string): void {
    this.selectedManufacturer = manufacturer;
    this.applyFilters();
  }

  /**
   * Handle status filter change
   */
  onStatusChange(status: string): void {
    this.selectedStatus = status;
    this.applyFilters();
  }

  /**
   * Toggle simulated device filter
   */
  toggleSimulatedFilter(): void {
    this.showSimulatedOnly = !this.showSimulatedOnly;
    this.applyFilters();
  }

  /**
   * Clear all filters
   */
  clearFilters(): void {
    this.selectedManufacturer = '';
    this.selectedStatus = '';
    this.showSimulatedOnly = false;
    this.applyFilters();
  }

  /**
   * Refresh device data
   */
  refresh(): void {
    this.loadWaterHeaters();
  }

  /**
   * Get device display name
   */
  getDeviceDisplayName(device: WaterHeater): string {
    return device.display_name ||
      `${device.manufacturer} ${device.model} (${device.device_id.substring(0, 8)})`;
  }

  /**
   * Get count of devices by status
   */
  getDeviceCountByStatus(status: string): number {
    return this.waterHeaters.filter(wh => wh.connection_status === status).length;
  }

  /**
   * Get count of simulated devices
   */
  getSimulatedDeviceCount(): number {
    return this.waterHeaters.filter(wh => wh.simulated).length;
  }
}
