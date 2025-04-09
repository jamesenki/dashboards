/**
 * Water Heater Device Details Micro-Frontend
 *
 * Entry point for the Water Heater Device Details micro-frontend
 * Part of the device-agnostic IoTSphere platform
 */

import { DeviceHeader } from './components/device-header.js';
import { DeviceControls } from './components/device-controls.js';
import { DeviceTelemetry } from './components/device-telemetry.js';
import { DevicePerformance } from './components/device-performance.js';
import { DeviceEvents } from './components/device-events.js';
import { AnomalyAlerts } from './components/anomaly-alerts.js';
import { DeviceService } from '../../../shared/services/device-service.js';
import { TelemetryService } from '../../../shared/services/telemetry-service.js';

// Register all custom elements
customElements.define('device-header', DeviceHeader);
customElements.define('device-controls', DeviceControls);
customElements.define('device-telemetry', DeviceTelemetry);
customElements.define('device-performance', DevicePerformance);
customElements.define('device-events', DeviceEvents);
customElements.define('anomaly-alerts', AnomalyAlerts);

/**
 * Mount the Water Heater Device Details micro-frontend
 *
 * @param {HTMLElement} mountPoint - DOM element to mount the micro-frontend
 * @param {Object} context - Context provided by the shell application
 * @returns {Object} - Interface for controlling the mounted micro-frontend
 */
export async function mount(mountPoint, context) {
  // Extract context
  const { deviceId, deviceType, auth, eventBus } = context;

  if (!deviceId) {
    mountPoint.innerHTML = `<div class="error-container">No device ID provided</div>`;
    return { unmount: () => { mountPoint.innerHTML = ''; } };
  }

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

  // Set loading state
  mountPoint.innerHTML = `
    <div class="water-heater-device-details loading">
      <div class="loading-indicator">
        <div class="loading-spinner"></div>
        <div class="loading-text">Loading device information...</div>
      </div>
    </div>
  `;

  try {
    // Load device data
    const device = await deviceService.getDevice(deviceId);

    // Set up the micro-frontend structure
    mountPoint.innerHTML = `
      <div class="water-heater-device-details">
        <!-- Header with basic device info -->
        <device-header id="device-header"></device-header>

        <!-- Main content with tabs -->
        <div class="device-content">
          <div class="device-tabs">
            <button class="tab-button active" data-tab="overview">Overview</button>
            <button class="tab-button" data-tab="performance">Performance</button>
            <button class="tab-button" data-tab="events">Events</button>
            <button class="tab-button" data-tab="settings">Settings</button>
          </div>

          <div class="tab-content">
            <!-- Overview tab (default view) -->
            <div class="tab-pane active" id="overview-tab">
              <div class="device-overview-layout">
                <div class="main-column">
                  <device-telemetry id="device-telemetry"></device-telemetry>
                  <device-controls id="device-controls"></device-controls>
                </div>
                <div class="side-column">
                  <anomaly-alerts id="anomaly-alerts"></anomaly-alerts>
                </div>
              </div>
            </div>

            <!-- Performance tab -->
            <div class="tab-pane" id="performance-tab">
              <device-performance id="device-performance"></device-performance>
            </div>

            <!-- Events tab -->
            <div class="tab-pane" id="events-tab">
              <device-events id="device-events"></device-events>
            </div>

            <!-- Settings tab -->
            <div class="tab-pane" id="settings-tab">
              <div class="settings-container">
                <h3>Device Settings</h3>
                <p>Device configuration options will be displayed here.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    // Get references to the custom elements
    const deviceHeader = mountPoint.querySelector('#device-header');
    const deviceTelemetry = mountPoint.querySelector('#device-telemetry');
    const deviceControls = mountPoint.querySelector('#device-controls');
    const devicePerformance = mountPoint.querySelector('#device-performance');
    const deviceEvents = mountPoint.querySelector('#device-events');
    const anomalyAlerts = mountPoint.querySelector('#anomaly-alerts');

    // Initialize tab navigation
    initializeTabs(mountPoint);

    // Initialize components with device data and services
    deviceHeader.initialize({ device, deviceService });
    deviceTelemetry.initialize({ device, deviceService, telemetryService });
    deviceControls.initialize({
      device,
      deviceService,
      onDeviceControlChange: (controlType, value) => {
        // Publish event when device controls change
        eventBus.publish('device:control-change', {
          deviceId: device.device_id,
          controlType,
          value
        });
      }
    });

    devicePerformance.initialize({ device, deviceId, telemetryService });
    deviceEvents.initialize({ device, deviceId });
    anomalyAlerts.initialize({ device, deviceId });

    // Subscribe to real-time updates
    const deviceUpdateSubscription = eventBus.subscribe('device:updated', (updatedDevice) => {
      if (updatedDevice.device_id === deviceId) {
        // Update components with new device data
        deviceHeader.updateDevice(updatedDevice);
        deviceTelemetry.updateDevice(updatedDevice);
        deviceControls.updateDevice(updatedDevice);
      }
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
        if (deviceTelemetry) deviceTelemetry.cleanup();
        if (telemetryService) telemetryService.disconnect();

        // Clear the mount point
        mountPoint.innerHTML = '';
      },

      /**
       * Refresh the micro-frontend data
       */
      refresh: async () => {
        const refreshedDevice = await deviceService.getDevice(deviceId);

        deviceHeader.updateDevice(refreshedDevice);
        deviceTelemetry.updateDevice(refreshedDevice);
        deviceControls.updateDevice(refreshedDevice);
        devicePerformance.refresh();
        deviceEvents.refresh();
        anomalyAlerts.refresh();
      }
    };
  } catch (error) {
    console.error(`Error loading device details for ${deviceId}:`, error);

    // Display error state
    mountPoint.innerHTML = `
      <div class="water-heater-device-details error">
        <div class="error-container">
          <h3>Error Loading Device</h3>
          <p>${error.message || 'Failed to load device details'}</p>
          <button id="retry-button">Retry</button>
        </div>
      </div>
    `;

    // Add retry button handler
    const retryButton = mountPoint.querySelector('#retry-button');
    if (retryButton) {
      retryButton.addEventListener('click', () => {
        // Re-mount the micro-frontend
        mount(mountPoint, context);
      });
    }

    return {
      unmount: () => {
        mountPoint.innerHTML = '';
      },
      refresh: async () => {
        // Re-mount the micro-frontend
        mount(mountPoint, context);
      }
    };
  }
}

/**
 * Initialize tab navigation
 */
function initializeTabs(container) {
  const tabButtons = container.querySelectorAll('.tab-button');
  const tabPanes = container.querySelectorAll('.tab-pane');

  tabButtons.forEach(button => {
    button.addEventListener('click', () => {
      const targetTab = button.getAttribute('data-tab');

      // Deactivate all tabs
      tabButtons.forEach(btn => btn.classList.remove('active'));
      tabPanes.forEach(pane => pane.classList.remove('active'));

      // Activate target tab
      button.classList.add('active');
      container.querySelector(`#${targetTab}-tab`).classList.add('active');
    });
  });
}
