/**
 * Water Heater Dashboard Micro-Frontend
 * 
 * Entry point for the Water Heater Dashboard micro-frontend
 * Part of the device-agnostic IoTSphere platform
 */

import { DeviceListComponent } from './components/device-list.js';
import { DeviceStatusCard } from './components/device-status-card.js';
import { DashboardSummary } from './components/dashboard-summary.js';
import { DeviceFilters } from './components/device-filters.js';
import { TelemetryService } from '../../shared/services/telemetry-service.js';
import { DeviceService } from '../../shared/services/device-service.js';

// Register all custom elements
customElements.define('device-list', DeviceListComponent);
customElements.define('device-status-card', DeviceStatusCard);
customElements.define('dashboard-summary', DashboardSummary);
customElements.define('device-filters', DeviceFilters);

/**
 * Mount the Water Heater Dashboard micro-frontend
 * 
 * @param {HTMLElement} mountPoint - DOM element to mount the micro-frontend
 * @param {Object} context - Context provided by the shell application
 * @returns {Object} - Interface for controlling the mounted micro-frontend
 */
export async function mount(mountPoint, context) {
  // Extract context
  const { deviceType, auth, eventBus } = context;
  
  // Create services with dependency injection
  const deviceService = new DeviceService({ 
    endpoint: '/api/devices',
    deviceType: 'water-heater',
    auth
  });
  
  const telemetryService = new TelemetryService({
    endpoint: '/api/telemetry',
    wsEndpoint: 'ws://localhost:8000/ws/telemetry',
    auth
  });
  
  // Create the micro-frontend structure
  mountPoint.innerHTML = `
    <div class="water-heater-dashboard">
      <div class="dashboard-header">
        <h1>Water Heater Dashboard</h1>
        <div class="dashboard-actions">
          <button class="btn-refresh" id="refresh-dashboard">
            <span class="icon-refresh"></span> Refresh
          </button>
          <button class="btn-add" id="add-device">
            <span class="icon-plus"></span> Add Device
          </button>
        </div>
      </div>
      
      <!-- Dashboard summary metrics -->
      <dashboard-summary id="dashboard-summary"></dashboard-summary>
      
      <!-- Device filters -->
      <device-filters id="device-filters"></device-filters>
      
      <!-- Device list -->
      <device-list id="device-list"></device-list>
    </div>
  `;
  
  // Get references to the custom elements
  const dashboardSummary = mountPoint.querySelector('#dashboard-summary');
  const deviceFilters = mountPoint.querySelector('#device-filters');
  const deviceList = mountPoint.querySelector('#device-list');
  const refreshButton = mountPoint.querySelector('#refresh-dashboard');
  
  // Initialize components with services and event handlers
  dashboardSummary.initialize({ deviceService });
  deviceFilters.initialize({ 
    deviceService,
    onFilterChange: (filters) => {
      deviceList.applyFilters(filters);
    }
  });
  
  deviceList.initialize({ 
    deviceService, 
    telemetryService,
    onDeviceSelected: (deviceId) => {
      // Navigate to device details when a device is selected
      window.location.hash = `#/dashboard/water-heaters/${deviceId}`;
    }
  });
  
  // Event listeners
  refreshButton.addEventListener('click', () => {
    dashboardSummary.refresh();
    deviceList.refresh();
  });
  
  // Initial data loading
  await Promise.all([
    dashboardSummary.refresh(),
    deviceList.refresh()
  ]);
  
  // Subscribe to real-time updates via EventBus
  const deviceUpdateSubscription = eventBus.subscribe('device:updated', (updatedDevice) => {
    deviceList.updateDevice(updatedDevice);
  });
  
  // Return interface for controlling the micro-frontend
  return {
    /**
     * Unmount the micro-frontend and clean up resources
     */
    unmount: () => {
      // Unsubscribe from EventBus
      deviceUpdateSubscription();
      
      // Clean up services
      telemetryService.disconnect();
      
      // Clear the mount point
      mountPoint.innerHTML = '';
    },
    
    /**
     * Refresh the micro-frontend data
     */
    refresh: async () => {
      await Promise.all([
        dashboardSummary.refresh(),
        deviceList.refresh()
      ]);
    }
  };
}
